#!/usr/bin/env python3
"""Nay_WakaWaka.py
One-minute hyper-produced arrangement of Shakira's Waka Waka (This Time
for Africa) with the LEAD played exclusively from recorded grains of
Nay1.m4a (resampled / looped — never a synthetic nay).
128 BPM, D major, exactly 60.000 s, 48 kHz stereo.
"""
from __future__ import annotations

import math
import os
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from numpy.typing import NDArray
from scipy.signal import butter, resample_poly, sosfilt, sosfiltfilt

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
ROOT = Path("/home/user/Music_unmixing")
WORK = Path("/home/user/work")
SRC_WAV = WORK / "nay1_48k.wav"
OUT_WAV = WORK / "Nay_WakaWaka.wav"
OUT_M4A = ROOT / "Nay_WakaWaka.m4a"
FFMPEG = Path(
    "/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/"
    "ffmpeg-linux-x86_64-v7.0.2"
)

SR = 48000
BPM = 128.0
BEAT = 60.0 / BPM          # 0.46875 s
BAR = 4.0 * BEAT           # 1.875 s
N_BARS = 32
DUR = N_BARS * BAR         # 60.000 s
N = int(round(DUR * SR))
assert abs(N / SR - 60.0) < 1e-9

A4 = 440.0
rng = np.random.default_rng(2010)


def midi_hz(m: float) -> float:
    return A4 * 2.0 ** ((m - 69.0) / 12.0)


def db(x: float) -> float:
    return 10.0 ** (x / 20.0)


def clamp(a: NDArray, p: float = 0.97) -> NDArray:
    return np.clip(a, -p, p)


# ---------------------------------------------------------------------------
# Measured grains from Nay1.m4a (README_ANALYSIS.md)
# idx, t0, t1, midi, freq_hz, vel
# ---------------------------------------------------------------------------
GRAIN_TABLE = [
    (1, 1.519, 1.861, 67, 380.18, 79),
    (2, 1.864, 2.156, 65, 338.31, 81),
    (3, 2.159, 2.300, 67, 381.94, 82),
    (4, 2.397, 2.600, 62, 287.79, 99),
    (5, 2.665, 2.937, 62, 290.46, 85),
    (6, 2.940, 2.979, 65, 305.96, 89),
    (7, 2.981, 3.219, 63, 305.96, 83),
    (8, 3.221, 3.291, 62, 290.12, 75),
    (9, 3.293, 3.430, 60, 253.74, 82),
    (10, 3.925, 4.195, 67, 383.26, 97),
    (11, 4.197, 4.365, 65, 342.63, 84),
    (12, 4.368, 4.550, 67, 385.04, 89),
    (13, 4.613, 4.780, 62, 289.45, 90),
    (14, 4.871, 5.457, 63, 303.84, 85),
    (15, 5.460, 6.165, 67, 385.04, 79),
    (16, 6.170, 6.252, 60, 257.28, 96),
    (17, 6.345, 6.565, 67, 384.14, 84),
    (18, 6.571, 6.830, 65, 345.02, 82),
    (19, 6.856, 7.036, 67, 388.16, 82),
    (20, 7.120, 7.224, 62, 289.79, 105),
    (21, 7.236, 7.350, 65, 345.02, 91),
    (22, 7.364, 7.676, 62, 290.79, 82),
    (23, 7.684, 7.836, 63, 306.67, 94),
    (24, 7.844, 7.908, 62, 289.45, 74),
    (25, 7.916, 8.125, 60, 256.69, 74),
    (26, 8.416, 8.492, 67, 351.86, 52),
    (27, 8.496, 8.560, 65, 338.31, 111),
    (28, 8.564, 8.608, 63, 303.49, 92),
    (29, 8.628, 9.265, 65, 343.03, 90),
    (30, 9.272, 9.467, 67, 389.06, 95),
    (31, 9.523, 9.664, 63, 306.67, 87),
    (32, 9.667, 9.795, 65, 343.82, 81),
    (33, 9.798, 9.900, 62, 290.46, 73),
    (34, 9.916, 10.028, 63, 308.80, 81),
    (35, 10.036, 10.100, 62, 293.83, 82),
    (36, 10.108, 10.420, 60, 258.47, 74),
]


# ---------------------------------------------------------------------------
# DSP helpers
# ---------------------------------------------------------------------------
def hp(x: NDArray, fc: float, order: int = 2) -> NDArray:
    sos = butter(order, fc / (SR * 0.5), btype="highpass", output="sos")
    return sosfiltfilt(sos, x).astype(np.float64)


def lp(x: NDArray, fc: float, order: int = 2) -> NDArray:
    sos = butter(order, min(fc / (SR * 0.5), 0.99), btype="lowpass", output="sos")
    return sosfiltfilt(sos, x).astype(np.float64)


def bp(x: NDArray, lo: float, hi: float, order: int = 2) -> NDArray:
    sos = butter(order, [lo / (SR * 0.5), hi / (SR * 0.5)], btype="bandpass", output="sos")
    return sosfiltfilt(sos, x).astype(np.float64)


def fade(x: NDArray, tin: float, tout: float) -> NDArray:
    y = x.copy()
    ni = int(tin * SR)
    no = int(tout * SR)
    if ni > 0:
        n = min(ni, len(y))
        y[:n] *= np.linspace(0.0, 1.0, n)
    if no > 0:
        n = min(no, len(y))
        y[-n:] *= np.linspace(1.0, 0.0, n)
    return y


def env_adsr(n: int, a: float, d: float, s: float, r: float) -> NDArray:
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na, nd, nr = max(na, 1), max(nd, 1), max(nr, 1)
    ns = max(n - na - nd - nr, 0)
    parts = [
        np.linspace(0.0, 1.0, na),
        np.linspace(1.0, s, nd),
        np.full(ns, s),
        np.linspace(s, 0.0, nr),
    ]
    e = np.concatenate(parts)
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def tanh_sat(x: NDArray, drive: float = 1.4) -> NDArray:
    return np.tanh(x * drive) / np.tanh(drive)


def pan_stereo(mono: NDArray, pan: float) -> NDArray:
    """pan -1 L .. +1 R, constant-power."""
    ang = (pan + 1.0) * 0.25 * math.pi
    left = mono * math.cos(ang)
    right = mono * math.sin(ang)
    return np.stack([left, right], axis=1)


def add_at(buf: NDArray, sig: NDArray, t: float, gain: float = 1.0) -> None:
    i0 = int(round(t * SR))
    if sig.ndim == 1:
        if buf.ndim == 2:
            sig = pan_stereo(sig, 0.0)
        else:
            sl = min(len(sig), len(buf) - i0)
            if sl > 0 and i0 < len(buf):
                if i0 < 0:
                    sig = sig[-i0:]
                    sl = min(len(sig), len(buf))
                    i0 = 0
                buf[i0 : i0 + sl] += gain * sig[:sl]
            return
    sl = min(len(sig), len(buf) - i0)
    if sl <= 0 or i0 >= len(buf):
        return
    if i0 < 0:
        sig = sig[-i0:]
        sl = min(len(sig), len(buf))
        i0 = 0
        if sl <= 0:
            return
    buf[i0 : i0 + sl] += gain * sig[:sl]


def rms(x: NDArray) -> float:
    return float(np.sqrt(np.mean(np.square(x)) + 1e-16))


def norm_peak(x: NDArray, peak: float = 0.92) -> NDArray:
    m = float(np.max(np.abs(x)))
    if m < 1e-12:
        return x
    return x * (peak / m)


# ---------------------------------------------------------------------------
# Nay grain bank — ONLY audio from Nay1.m4a
# ---------------------------------------------------------------------------
class NayBank:
    def __init__(self, wav: NDArray):
        self.raw = wav.astype(np.float64)
        self.grains = []
        pad = int(0.008 * SR)
        for idx, t0, t1, midi, freq, vel in GRAIN_TABLE:
            a = max(0, int(t0 * SR) - pad)
            b = min(len(wav), int(t1 * SR) + pad)
            g = wav[a:b].astype(np.float64)
            # strip DC, light HP (keep chiff)
            g = g - np.mean(g)
            g = hp(g, 70.0, 1)
            g = fade(g, 0.003, 0.006)
            peak = float(np.max(np.abs(g)) + 1e-12)
            g = g / peak
            self.grains.append(
                dict(idx=idx, midi=midi, freq=freq, vel=vel, audio=g, dur=(t1 - t0))
            )
        # round-robin cursors
        self.rr: dict[int, int] = {}

    def pick(self, target_midi: int, want_dur: float) -> dict:
        """Closest pitch, prefer longer grains when we need sustain."""
        scored = []
        for g in self.grains:
            dmidi = abs(g["midi"] - target_midi)
            # skip the glitchy very-short / wildly-detuned grains
            if g["dur"] < 0.05 or g["idx"] in (6, 26):
                continue
            length_pen = 0.0
            if want_dur > g["dur"] + 0.05:
                length_pen = (want_dur - g["dur"]) * 0.4
            scored.append((dmidi + 0.15 * abs(dmidi) ** 2 + length_pen, -g["dur"], g))
        scored.sort(key=lambda z: (z[0], z[1]))
        # round-robin among the best 3 of the same pitch class
        top = [s[2] for s in scored[:4]]
        key = int(target_midi)
        k = self.rr.get(key, 0)
        self.rr[key] = k + 1
        return top[k % len(top)]

    def render_note(self, midi: float, dur: float, vel: float = 0.9) -> NDArray:
        g = self.pick(int(round(midi)), dur)
        target_f = midi_hz(midi)
        ratio = target_f / g["freq"]
        # keep ratio sane (formant preservation by choosing close grains)
        ratio = float(np.clip(ratio, 0.78, 1.28))
        x = g["audio"]
        # resample_poly pitch shift
        # length *= 1/ratio  (higher pitch => shorter)
        shifted = resample_poly(x, 1000, int(round(1000 * ratio))).astype(np.float64)
        shifted = hp(shifted, 80.0, 1)
        n_out = int(round(dur * SR))
        y = self._fit_length(shifted, n_out)
        # nay-like amp envelope: fast chiff in, natural decay tail
        att = min(int(0.008 * SR), n_out // 8)
        rel = min(int(0.055 * SR), n_out // 3)
        e = np.ones(n_out)
        if att > 0:
            e[:att] = np.linspace(0.0, 1.0, att)
        if rel > 0:
            e[-rel:] = np.linspace(1.0, 0.0, rel)
        # slight recorded-style amplitude flutter
        t = np.arange(n_out) / SR
        flutter = 1.0 + 0.035 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
        y = y * e * flutter * vel
        # match grain loudness-ish
        r = rms(y)
        if r > 1e-8:
            y = y * (0.18 / r) * vel
        return y

    def _fit_length(self, x: NDArray, n_out: int) -> NDArray:
        if len(x) >= n_out:
            y = x[:n_out].copy()
            return y
        # attack + crossfade-looped sustain
        att = min(int(0.04 * SR), len(x) // 4)
        rel = min(int(0.05 * SR), len(x) // 5)
        core = x[att : len(x) - rel] if len(x) > att + rel + 64 else x
        if len(core) < 64:
            # just pad with fade
            y = np.zeros(n_out)
            y[: len(x)] = x
            return y
        fade_n = min(int(0.028 * SR), len(core) // 3)
        hop = len(core) - fade_n
        y = np.zeros(n_out)
        # write attack
        y[:att] = x[:att]
        pos = att
        win_in = np.sin(np.linspace(0, np.pi / 2, fade_n)) ** 2
        win_out = 1.0 - win_in
        first = True
        guard = 0
        while pos < n_out - rel and guard < 400:
            guard += 1
            if first:
                take = min(len(core), n_out - rel - pos)
                y[pos : pos + take] += core[:take]
                pos += hop
                first = False
            else:
                # crossfade in
                ov = min(fade_n, n_out - rel - pos)
                y[pos : pos + ov] = y[pos : pos + ov] * win_out[:ov] + core[:ov] * win_in[:ov]
                rest = core[ov:]
                sl = min(len(rest), n_out - rel - pos - ov)
                if sl > 0:
                    y[pos + ov : pos + ov + sl] += rest[:sl]
                pos += hop
        # original release colour if we have room
        tail = x[-rel:]
        end = min(n_out, pos + rel)
        sl = end - (n_out - rel) if False else min(len(tail), n_out - (n_out - rel))
        y[n_out - rel : n_out - rel + sl] += tail[:sl] * np.linspace(0.4, 0.0, sl)
        # safety fade
        y = fade(y, 0.0, 0.01)
        return y


# ---------------------------------------------------------------------------
# Reverb (unit-energy noise IR)
# ---------------------------------------------------------------------------
def make_ir(t60: float, stereo: bool = True, hp_fc: float = 120.0, pre: float = 0.018) -> NDArray:
    n = int((t60 * 2.2 + pre) * SR)
    t = np.arange(n) / SR
    decay = np.exp(-t * (3.0 / max(t60, 1e-3)))  # ~T60
    pre_n = int(pre * SR)
    decay[:pre_n] = 0.0
    if stereo:
        ir = rng.normal(0.0, 1.0, size=(n, 2))
        ir *= decay[:, None]
        ir[:, 0] = hp(ir[:, 0], hp_fc, 1)
        ir[:, 1] = hp(ir[:, 1], hp_fc, 1)
        ir /= np.sqrt(np.sum(ir ** 2) + 1e-16)
    else:
        ir = rng.normal(0.0, 1.0, size=n) * decay
        ir = hp(ir, hp_fc, 1)
        ir /= np.sqrt(np.sum(ir ** 2) + 1e-16)
    return ir


def conv_reverb(mono: NDArray, ir: NDArray, wet: float) -> NDArray:
    """IR is (N,2). Returns stereo wet only."""
    # FFT convolution
    n = len(mono) + len(ir) - 1
    nfft = 1 << int(math.ceil(math.log2(n)))
    M = np.fft.rfft(mono, nfft)
    L = np.fft.rfft(ir[:, 0], nfft)
    R = np.fft.rfft(ir[:, 1], nfft)
    yL = np.fft.irfft(M * L, nfft)[: len(mono)]
    yR = np.fft.irfft(M * R, nfft)[: len(mono)]
    y = np.stack([yL, yR], axis=1) * wet
    return y


# ---------------------------------------------------------------------------
# Synthetic accompaniment (NOT the nay)
# ---------------------------------------------------------------------------
def synth_kick(dur: float = 0.42) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    # pitch sweep
    f = 148.0 * np.exp(-t * 18.0) + 38.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 9.5)
    click = hp(rng.normal(0, 1, n) * np.exp(-t * 180.0), 1500, 2) * 0.35
    thump = np.sin(2 * np.pi * 55.0 * t) * np.exp(-t * 14.0) * 0.4
    y = body + click + thump
    y = fade(y, 0.0004, 0.02)
    return norm_peak(y, 0.95)


def synth_snare(dur: float = 0.28) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = hp(rng.normal(0, 1, n), 800, 2)
    noise = lp(noise, 7500, 2) * np.exp(-t * 22.0)
    tone = (np.sin(2 * np.pi * 190 * t) + 0.4 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t * 18)
    y = 0.78 * noise + 0.35 * tone
    y = fade(y, 0.0003, 0.03)
    return norm_peak(y, 0.9)


def synth_clap(dur: float = 0.32) -> NDArray:
    n = int(dur * SR)
    y = np.zeros(n)
    delays = [0.0, 0.012, 0.021, 0.031, 0.045]
    gains = [1.0, 0.7, 0.55, 0.4, 0.28]
    for d, g in zip(delays, gains):
        i = int(d * SR)
        m = n - i
        if m <= 0:
            continue
        t = np.arange(m) / SR
        burst = hp(rng.normal(0, 1, m), 900, 2) * np.exp(-t * 35.0) * g
        y[i : i + m] += burst
    y = lp(y, 6000, 2)
    return norm_peak(y, 0.85)


def synth_hat(open_: bool = False) -> NDArray:
    dur = 0.18 if not open_ else 0.32
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = rng.normal(0, 1, n)
    y = hp(y, 6000, 3)
    y = lp(y, 14000, 2)
    dec = 28.0 if not open_ else 12.0
    y *= np.exp(-t * dec)
    return norm_peak(y, 0.7)


def synth_shaker_tick() -> NDArray:
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    y = hp(rng.normal(0, 1, n), 4000, 2) * np.exp(-t * 90.0)
    y = lp(y, 12000, 1)
    return norm_peak(y, 0.6)


def synth_conga(f: float, dur: float = 0.28) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * t) * np.exp(-t * 14.0)
    body += 0.35 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t * 22.0)
    slap = hp(rng.normal(0, 1, n), 1200, 2) * np.exp(-t * 70.0) * 0.25
    y = body + slap
    y = fade(y, 0.0005, 0.02)
    return norm_peak(y, 0.85)


def synth_bass_note(midi: int, dur: float, vel: float = 1.0) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(midi)
    # slight pitch drop at attack (african bass punch)
    f_env = f * (1.0 + 0.06 * np.exp(-t * 60.0))
    phase = 2 * np.pi * np.cumsum(f_env) / SR
    sig = 0.85 * np.sin(phase)
    sig += 0.22 * np.sin(2 * phase) * np.exp(-t * 8.0)
    sig += 0.08 * np.tanh(np.sin(phase) * 2.5)
    e = env_adsr(n, 0.006, 0.07, 0.72, min(0.08, dur * 0.3))
    y = sig * e * vel
    y = lp(y, 2800, 2)
    return y * 0.9


def karplus_note(midi: int, dur: float, brightness: float = 0.988, vel: float = 0.8) -> NDArray:
    n = int(dur * SR)
    f = midi_hz(midi)
    per = max(int(SR / f), 2)
    buf = rng.normal(0, 1, per)
    buf = hp(buf, 80, 1)
    out = np.zeros(n)
    idx = 0
    prev = 0.0
    for i in range(n):
        cur = buf[idx]
        mixed = 0.5 * (cur + prev) * brightness
        buf[idx] = mixed
        out[i] = mixed
        prev = cur
        idx += 1
        if idx >= per:
            idx = 0
    out = fade(out, 0.001, 0.02) * vel
    return out


def guitar_chord(midis: list[int], dur: float, vel: float = 0.75) -> NDArray:
    acc = np.zeros(int(dur * SR))
    for k, m in enumerate(midis):
        delay = int((0.004 + 0.003 * k) * SR)  # strum
        note = karplus_note(m, dur, brightness=0.985 - 0.004 * k, vel=vel * (0.9 + 0.05 * rng.random()))
        if delay < len(acc):
            sl = min(len(note), len(acc) - delay)
            acc[delay : delay + sl] += note[:sl]
    acc = lp(acc, 5200, 2)
    r = rms(acc)
    if r > 1e-8:
        acc *= 0.16 / r
    return acc


def synth_pad_chord(midis: list[int], dur: float) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    yL = np.zeros(n)
    yR = np.zeros(n)
    for i, m in enumerate(midis):
        f = midi_hz(m)
        det = 1.0 + (0.004 if i % 2 == 0 else -0.004)
        sig = 0.5 * np.sin(2 * np.pi * f * t)
        sig += 0.25 * np.sin(2 * np.pi * f * 2 * t * det)
        sig += 0.12 * np.sin(2 * np.pi * f * 3 * t)
        if i % 2 == 0:
            yL += sig
        else:
            yR += sig
        yL += 0.35 * sig
        yR += 0.35 * sig
    e = env_adsr(n, 0.12, 0.15, 0.7, 0.25)
    yL = lp(yL * e, 2400, 2)
    yR = lp(yR * e, 2400, 2)
    st = np.stack([yL, yR], axis=1)
    r = rms(st)
    if r > 1e-8:
        st *= 0.10 / r
    return st


def synth_brass_stab(midis: list[int], dur: float = 0.22) -> NDArray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for m in midis:
        f = midi_hz(m)
        s = np.sin(2 * np.pi * f * t)
        s += 0.4 * np.sin(2 * np.pi * 2 * f * t)
        s += 0.18 * np.sin(2 * np.pi * 3 * f * t)
        s = np.tanh(s * 1.8)
        y += s
    e = env_adsr(n, 0.008, 0.06, 0.35, 0.12)
    y = lp(y * e, 3200, 2)
    r = rms(y)
    if r > 1e-8:
        y *= 0.14 / r
    return y


# ---------------------------------------------------------------------------
# Arrangement data  (bars 0..31), D major / B minor, 128 BPM
# Chords cycle: D | A | Bm | G
# MIDI: B3=59 C#4=61 D4=62 E4=64 F#4=66 A4=69  (nay-comfortable)
# ---------------------------------------------------------------------------
CHORDS = {
    "D":  [50, 57, 62, 66],      # D3 A3 D4 F#4
    "A":  [45, 52, 57, 61],      # A2 E3 A3 C#4
    "Bm": [47, 54, 59, 62],      # B2 F#3 B3 D4
    "G":  [43, 50, 55, 59],      # G2 D3 G3 B3
}
CHORD_ROOT = {"D": 38, "A": 33, "Bm": 35, "G": 31}  # bass MIDI (D2, A1, B1, G1)
PROG = (["D", "A", "Bm", "G"] * 8)  # 32 bars

# nay melody: list of (bar, start_beat 0-4, dur_beats, midi, vel)
# Rhythms follow Shakira / Freshlyground syllable timing.
def M(bar, beat, dur, midi, vel=0.92):
    return (bar, beat, dur, midi, vel)


NAY_MELODY = [
    # ---- INTRO pickup + call (bars 1-3) ----
    M(1, 2.00, 0.70, 66, 0.78),  # F# pickup
    M(1, 3.00, 0.90, 62, 0.84),  # D
    M(2, 0.00, 0.45, 66, 0.82),  # F#
    M(2, 0.50, 0.45, 62, 0.78),  # D
    M(2, 1.00, 0.45, 69, 0.85),  # A
    M(2, 1.50, 0.45, 66, 0.80),
    M(2, 2.00, 0.70, 64, 0.84),  # E
    M(2, 3.00, 0.90, 62, 0.88),  # D
    M(3, 0.00, 0.45, 62, 0.80),
    M(3, 0.50, 0.45, 64, 0.82),
    M(3, 1.00, 0.45, 66, 0.86),
    M(3, 1.50, 0.45, 69, 0.84),
    M(3, 2.00, 0.70, 66, 0.82),
    M(3, 3.00, 0.95, 62, 0.90),

    # ---- VERSE 1 (4-11) "You're a good soldier..." ----
    # bar4 D  You're a good soldier   D D D E D
    M(4, 0.00, 0.45, 62, 0.88),
    M(4, 0.50, 0.45, 62, 0.84),
    M(4, 1.00, 0.70, 62, 0.86),
    M(4, 2.00, 0.70, 64, 0.90),
    M(4, 3.00, 0.90, 62, 0.88),
    # bar5 A  Choosing your battles   C# C# C# D C#
    M(5, 0.00, 0.45, 61, 0.86),
    M(5, 0.50, 0.45, 61, 0.82),
    M(5, 1.00, 0.70, 61, 0.84),
    M(5, 2.00, 0.70, 62, 0.88),
    M(5, 3.00, 0.90, 61, 0.86),
    # bar6 Bm Pick yourself up / dust yourself off   D D C# B  B D
    M(6, 0.00, 0.45, 62, 0.88),
    M(6, 0.50, 0.45, 62, 0.84),
    M(6, 1.00, 0.45, 61, 0.82),
    M(6, 1.50, 0.70, 59, 0.86),
    M(6, 2.50, 0.45, 59, 0.80),
    M(6, 3.00, 0.90, 62, 0.88),
    # bar7 G  And back in the saddle   B D D D E B
    M(7, 0.00, 0.45, 59, 0.84),
    M(7, 0.50, 0.45, 62, 0.86),
    M(7, 1.00, 0.45, 62, 0.84),
    M(7, 1.50, 0.45, 62, 0.86),
    M(7, 2.00, 0.70, 64, 0.90),
    M(7, 3.00, 0.90, 59, 0.88),
    # bar8 D  You're on the front line  D D D E F#
    M(8, 0.00, 0.45, 62, 0.88),
    M(8, 0.50, 0.45, 62, 0.84),
    M(8, 1.00, 0.70, 62, 0.86),
    M(8, 2.00, 0.70, 64, 0.90),
    M(8, 3.00, 0.90, 66, 0.92),
    # bar9 A  Everyone's watching  C# C# C# D E
    M(9, 0.00, 0.45, 61, 0.86),
    M(9, 0.50, 0.45, 61, 0.82),
    M(9, 1.00, 0.70, 61, 0.84),
    M(9, 2.00, 0.70, 62, 0.86),
    M(9, 3.00, 0.90, 64, 0.90),
    # bar10 Bm You know it's serious  D D C# B
    M(10, 0.00, 0.45, 62, 0.88),
    M(10, 0.50, 0.45, 62, 0.84),
    M(10, 1.00, 0.70, 61, 0.84),
    M(10, 2.00, 1.80, 59, 0.90),
    # bar11 G  This isn't over  D D E B D
    M(11, 0.00, 0.45, 62, 0.86),
    M(11, 0.50, 0.45, 62, 0.84),
    M(11, 1.00, 0.70, 64, 0.88),
    M(11, 2.00, 0.70, 59, 0.86),
    M(11, 3.00, 0.95, 62, 0.92),

    # ---- PRE-CHORUS (12-15) ----
    # bar12 D  When you fall get up oh oh   D D D D D E D
    M(12, 0.00, 0.45, 62, 0.90),
    M(12, 0.50, 0.45, 62, 0.86),
    M(12, 1.00, 0.45, 62, 0.88),
    M(12, 1.50, 0.45, 62, 0.86),
    M(12, 2.00, 0.70, 62, 0.90),
    M(12, 3.00, 0.45, 64, 0.94),
    M(12, 3.50, 0.45, 62, 0.88),
    # bar13 A  And if you fall get up eh eh  E E E E E F# D E
    M(13, 0.00, 0.45, 64, 0.90),
    M(13, 0.50, 0.45, 64, 0.86),
    M(13, 1.00, 0.45, 64, 0.88),
    M(13, 1.50, 0.45, 64, 0.86),
    M(13, 2.00, 0.45, 64, 0.90),
    M(13, 2.50, 0.45, 66, 0.94),
    M(13, 3.00, 0.45, 62, 0.88),
    M(13, 3.50, 0.45, 64, 0.90),
    # bar14 Bm Tsamina mina zangalewa  F# F# F# D D B B B A
    M(14, 0.00, 0.45, 66, 0.94),
    M(14, 0.50, 0.45, 66, 0.90),
    M(14, 1.00, 0.45, 66, 0.92),
    M(14, 1.50, 0.45, 62, 0.88),
    M(14, 2.00, 0.45, 62, 0.86),
    M(14, 2.50, 0.45, 59, 0.88),
    M(14, 3.00, 0.45, 59, 0.86),
    M(14, 3.50, 0.45, 59, 0.84),
    # bar15 G  'Cause this is Africa  A | F# D D B D D
    M(15, 0.00, 0.45, 69, 0.92),
    M(15, 0.50, 0.45, 66, 0.90),
    M(15, 1.00, 0.45, 62, 0.88),
    M(15, 1.50, 0.45, 62, 0.86),
    M(15, 2.00, 0.70, 59, 0.88),
    M(15, 3.00, 0.95, 62, 0.94),

    # ---- CHORUS (16-23)  two cycles ----
    # 16 D  Tsamina mina eh eh
    M(16, 0.00, 0.45, 62, 0.96),
    M(16, 0.50, 0.45, 62, 0.90),
    M(16, 1.00, 0.45, 62, 0.92),
    M(16, 1.50, 0.45, 62, 0.90),
    M(16, 2.00, 0.70, 62, 0.94),
    M(16, 3.00, 0.45, 64, 0.98),
    M(16, 3.50, 0.45, 62, 0.92),
    # 17 A  Waka waka eh eh
    M(17, 0.00, 0.45, 64, 0.96),
    M(17, 0.50, 0.45, 64, 0.90),
    M(17, 1.00, 0.45, 64, 0.92),
    M(17, 1.50, 0.45, 64, 0.90),
    M(17, 2.00, 0.70, 66, 0.98),
    M(17, 3.00, 0.45, 62, 0.90),
    M(17, 3.50, 0.45, 64, 0.94),
    # 18 Bm Tsamina mina zangalewa
    M(18, 0.00, 0.45, 66, 0.98),
    M(18, 0.50, 0.45, 66, 0.92),
    M(18, 1.00, 0.45, 66, 0.94),
    M(18, 1.50, 0.45, 62, 0.90),
    M(18, 2.00, 0.45, 62, 0.88),
    M(18, 2.50, 0.45, 59, 0.90),
    M(18, 3.00, 0.45, 59, 0.88),
    M(18, 3.50, 0.45, 59, 0.86),
    # 19 G  This time for Africa
    M(19, 0.00, 0.45, 69, 0.96),
    M(19, 0.50, 0.45, 66, 0.92),
    M(19, 1.00, 0.45, 62, 0.90),
    M(19, 1.50, 0.45, 62, 0.88),
    M(19, 2.00, 0.70, 59, 0.90),
    M(19, 3.00, 0.95, 62, 0.98),
    # 20-23 repeat chorus, last bar "Anawa a a" then cadence
    M(20, 0.00, 0.45, 62, 0.98),
    M(20, 0.50, 0.45, 62, 0.92),
    M(20, 1.00, 0.45, 62, 0.94),
    M(20, 1.50, 0.45, 62, 0.90),
    M(20, 2.00, 0.70, 62, 0.94),
    M(20, 3.00, 0.45, 64, 1.00),
    M(20, 3.50, 0.45, 62, 0.92),
    M(21, 0.00, 0.45, 64, 0.98),
    M(21, 0.50, 0.45, 64, 0.92),
    M(21, 1.00, 0.45, 64, 0.94),
    M(21, 1.50, 0.45, 64, 0.90),
    M(21, 2.00, 0.70, 66, 1.00),
    M(21, 3.00, 0.45, 62, 0.90),
    M(21, 3.50, 0.45, 64, 0.94),
    M(22, 0.00, 0.45, 66, 1.00),
    M(22, 0.50, 0.45, 66, 0.94),
    M(22, 1.00, 0.45, 66, 0.96),
    M(22, 1.50, 0.45, 62, 0.90),
    M(22, 2.00, 0.45, 62, 0.88),
    M(22, 2.50, 0.45, 59, 0.90),
    M(22, 3.00, 0.45, 59, 0.88),
    M(22, 3.50, 0.45, 59, 0.86),
    M(23, 0.00, 0.90, 69, 0.98),  # Anawa
    M(23, 1.00, 0.90, 66, 0.92),
    M(23, 2.00, 0.90, 62, 0.90),
    M(23, 3.00, 0.95, 62, 0.96),

    # ---- FINAL CHORUS lift (24-27) ----
    M(24, 0.00, 0.45, 62, 1.00),
    M(24, 0.50, 0.45, 62, 0.94),
    M(24, 1.00, 0.45, 62, 0.96),
    M(24, 1.50, 0.45, 62, 0.92),
    M(24, 2.00, 0.70, 62, 0.96),
    M(24, 3.00, 0.45, 64, 1.00),
    M(24, 3.50, 0.45, 62, 0.94),
    M(25, 0.00, 0.45, 64, 1.00),
    M(25, 0.50, 0.45, 64, 0.94),
    M(25, 1.00, 0.45, 64, 0.96),
    M(25, 1.50, 0.45, 64, 0.92),
    M(25, 2.00, 0.70, 66, 1.00),
    M(25, 3.00, 0.45, 62, 0.92),
    M(25, 3.50, 0.45, 64, 0.96),
    M(26, 0.00, 0.45, 66, 1.00),
    M(26, 0.50, 0.45, 66, 0.94),
    M(26, 1.00, 0.45, 66, 0.96),
    M(26, 1.50, 0.45, 62, 0.90),
    M(26, 2.00, 0.45, 62, 0.88),
    M(26, 2.50, 0.45, 59, 0.90),
    M(26, 3.00, 0.45, 59, 0.88),
    M(26, 3.50, 0.45, 59, 0.86),
    M(27, 0.00, 0.70, 69, 1.00),  # This time
    M(27, 1.00, 0.70, 66, 0.96),
    M(27, 2.00, 0.70, 64, 0.94),
    M(27, 3.00, 1.80, 62, 1.00),  # Africa — held into outro

    # ---- OUTRO (28-31) nay cadence ----
    M(28, 0.00, 0.90, 66, 0.90),
    M(28, 1.00, 0.90, 64, 0.86),
    M(28, 2.00, 0.90, 62, 0.88),
    M(28, 3.00, 0.90, 59, 0.84),
    M(29, 0.00, 1.80, 62, 0.88),
    M(29, 2.00, 0.90, 66, 0.86),
    M(29, 3.00, 0.90, 64, 0.84),
    M(30, 0.00, 1.80, 62, 0.90),
    M(30, 2.00, 1.80, 59, 0.82),
    M(31, 0.00, 3.70, 62, 0.92),  # final D, long
]


def bar_time(bar: float, beat: float = 0.0) -> float:
    return (bar * 4.0 + beat) * BEAT


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build():
    print("loading nay source…")
    wav, sr = sf.read(str(SRC_WAV), always_2d=False)
    assert sr == SR
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    bank = NayBank(wav)

    mix = np.zeros((N, 2), dtype=np.float64)
    nay_bus = np.zeros(N, dtype=np.float64)
    nay_dbl = np.zeros(N, dtype=np.float64)
    drum_bus = np.zeros((N, 2), dtype=np.float64)
    bass_bus = np.zeros(N, dtype=np.float64)
    gtr_bus = np.zeros((N, 2), dtype=np.float64)
    pad_bus = np.zeros((N, 2), dtype=np.float64)
    perc_bus = np.zeros((N, 2), dtype=np.float64)
    brass_bus = np.zeros((N, 2), dtype=np.float64)

    print("pre-rendering one-shots…")
    kick = synth_kick()
    snare = synth_snare()
    clap = synth_clap()
    hat_c = synth_hat(False)
    hat_o = synth_hat(True)
    shak = synth_shaker_tick()
    conga_l = synth_conga(180.0, 0.30)
    conga_m = synth_conga(220.0, 0.26)
    conga_h = synth_conga(280.0, 0.22)

    # energy by section
    def sect_gain(bar: int) -> dict:
        if bar < 2:
            return dict(k=0.82, s=0.45, h=0.7, sh=0.85, c=0.55, b=0.45, g=0.25, p=0.4, cl=0.0, br=0.0)
        if bar < 4:
            return dict(k=0.9, s=0.8, h=0.78, sh=0.9, c=0.7, b=0.8, g=0.55, p=0.55, cl=0.1, br=0.0)
        if bar < 12:
            return dict(k=0.9, s=0.85, h=0.75, sh=0.85, c=0.7, b=0.9, g=0.7, p=0.55, cl=0.15, br=0.0)
        if bar < 16:
            return dict(k=0.95, s=0.9, h=0.8, sh=0.9, c=0.8, b=0.95, g=0.8, p=0.65, cl=0.45, br=0.35)
        if bar < 24:
            return dict(k=1.0, s=1.0, h=0.85, sh=1.0, c=0.95, b=1.0, g=0.95, p=0.75, cl=0.85, br=0.7)
        if bar < 28:
            return dict(k=1.0, s=1.0, h=0.9, sh=1.0, c=1.0, b=1.0, g=1.0, p=0.85, cl=1.0, br=0.85)
        if bar < 30:
            return dict(k=0.75, s=0.55, h=0.5, sh=0.6, c=0.5, b=0.7, g=0.4, p=0.55, cl=0.2, br=0.0)
        return dict(k=0.45, s=0.0, h=0.25, sh=0.3, c=0.2, b=0.45, g=0.2, p=0.4, cl=0.0, br=0.0)

    print("drums / bass / guitar / pad…")
    for bar in range(N_BARS):
        g = sect_gain(bar)
        ch = PROG[bar]
        roots = CHORD_ROOT[ch]
        t0 = bar_time(bar)

        # kick four-on-the-floor + extra on 4& in chorus
        for bt in (0.0, 1.0, 2.0, 3.0):
            add_at(drum_bus, pan_stereo(kick, 0.0), t0 + bt * BEAT, g["k"] * 0.95)
        if bar >= 16 and bar < 28:
            add_at(drum_bus, pan_stereo(kick * 0.55, 0.0), t0 + 3.5 * BEAT, g["k"] * 0.5)

        # snare / clap 2 and 4
        for bt in (1.0, 3.0):
            add_at(drum_bus, pan_stereo(snare, 0.02), t0 + bt * BEAT, g["s"] * 0.72)
            add_at(drum_bus, pan_stereo(clap, 0.08), t0 + bt * BEAT + 0.004, g["cl"] * 0.55)

        # hats: 8ths closed, open on 2& 4& in later sections
        for k in range(8):
            bt = k * 0.5
            vel = 0.45 if k % 2 else 0.7
            add_at(drum_bus, pan_stereo(hat_c, 0.15), t0 + bt * BEAT, g["h"] * vel * 0.33)
        if bar >= 4:
            add_at(drum_bus, pan_stereo(hat_o, 0.2), t0 + 1.5 * BEAT, g["h"] * 0.28)
            add_at(drum_bus, pan_stereo(hat_o, 0.2), t0 + 3.5 * BEAT, g["h"] * 0.28)

        # shaker 16ths with 3+3+2 african accent
        accents = {0: 1.0, 3: 0.85, 6: 0.95, 8: 0.7, 12: 0.9}
        for s in range(16):
            vel = accents.get(s, 0.45 + 0.15 * (s % 2))
            jitter = rng.uniform(-0.003, 0.003)
            add_at(
                perc_bus,
                pan_stereo(shak, 0.35 + 0.1 * rng.uniform(-1, 1)),
                t0 + s * 0.25 * BEAT + jitter,
                g["sh"] * vel * 0.28,
            )

        # congas afro pattern
        cpat = [(0.0, conga_l, -0.35, 0.8), (0.75, conga_h, -0.15, 0.55),
                (1.5, conga_m, -0.25, 0.65), (2.25, conga_h, -0.1, 0.5),
                (3.0, conga_l, -0.3, 0.7), (3.5, conga_m, -0.2, 0.6)]
        if bar >= 2:
            for bt, snd, p, v in cpat:
                add_at(perc_bus, pan_stereo(snd, p), t0 + bt * BEAT, g["c"] * v * 0.42)

        # tom fill into chorus / final
        if bar in (15, 23):
            for i, (bt, f) in enumerate([(2.0, 160), (2.5, 140), (3.0, 120), (3.5, 95)]):
                tom = synth_conga(f, 0.28)
                add_at(drum_bus, pan_stereo(tom, -0.2 + 0.1 * i), t0 + bt * BEAT, 0.7)

        # bass
        if g["b"] > 0:
            # 1 root, 2 root, 3 fifth, 4 root, 4& octave
            fifth = roots + 7
            octv = roots + 12
            pattern = [(0.0, 1.0, roots, 1.0),
                       (1.0, 0.9, roots, 0.85),
                       (2.0, 0.7, fifth, 0.9),
                       (3.0, 0.45, roots, 0.88),
                       (3.5, 0.45, octv, 0.8)]
            if bar % 4 == 3:  # G bar walk
                pattern = [(0.0, 1.0, roots, 1.0),
                           (1.0, 0.9, roots, 0.85),
                           (2.0, 0.45, roots + 2, 0.85),  # A
                           (2.5, 0.45, roots + 4, 0.85),  # B
                           (3.0, 0.45, roots, 0.9),
                           (3.5, 0.45, octv, 0.8)]
            for bt, dur_bt, midi, vel in pattern:
                note = synth_bass_note(midi, dur_bt * BEAT + 0.03, vel)
                add_at(bass_bus, note, t0 + bt * BEAT, g["b"] * 0.95)

        # guitar 8ths
        if g["g"] > 0:
            voicing = CHORDS[ch]
            for k in range(8):
                bt = k * 0.5
                vel = (0.85 if k % 2 == 0 else 0.5) * (0.92 + 0.08 * rng.random())
                if k in (2, 6):  # ska-ish accent on 2 and 4
                    vel *= 1.15
                chrd = guitar_chord(voicing, 0.42, vel)
                pan = -0.25 if k % 2 == 0 else 0.28
                add_at(gtr_bus, pan_stereo(chrd, pan), t0 + bt * BEAT, g["g"] * 0.55)

        # pad whole bar
        if g["p"] > 0:
            pad = synth_pad_chord(CHORDS[ch], BAR + 0.12)
            add_at(pad_bus, pad, t0, g["p"] * 0.85)

        # brass stabs on chorus downbeats of D and Bm
        if g["br"] > 0 and bar % 4 in (0, 2) and bar >= 16:
            stab = synth_brass_stab(CHORDS[ch][1:], 0.20)
            add_at(brass_bus, pan_stereo(stab, 0.1), t0, g["br"] * 0.7)
            add_at(brass_bus, pan_stereo(stab * 0.6, -0.1), t0 + 0.5 * BEAT, g["br"] * 0.35)

    print("nay lead from recorded grains…")
    for bar, beat, dur_bt, midi, vel in NAY_MELODY:
        t = bar_time(bar, beat)
        dur = dur_bt * BEAT * 0.92  # slight gap like a blown instrument
        if bar == 31:
            dur = dur_bt * BEAT * 0.98
        # humanize 1–6 ms
        t += rng.uniform(0.001, 0.006)
        note = bank.render_note(midi, dur, vel)
        add_at(nay_bus, note, t, 1.0)
        # double-track: different grain, tiny delay + cents via extra resample
        note2 = bank.render_note(midi + rng.uniform(-0.08, 0.08), dur * rng.uniform(0.96, 1.02), vel * 0.72)
        add_at(nay_dbl, note2, t + rng.uniform(0.012, 0.022), 0.7)

    print("reverb / mix…")
    ir_nay = make_ir(1.85, stereo=True, hp_fc=180.0, pre=0.022)
    ir_drm = make_ir(0.70, stereo=True, hp_fc=400.0, pre=0.008)
    ir_hall = make_ir(2.4, stereo=True, hp_fc=150.0, pre=0.028)

    nay_hp = hp(nay_bus, 120.0, 1)
    nay_lp = lp(nay_hp, 10000.0, 2)
    # presence bell (nay formant / attack chiff)
    nay_lp = nay_lp + bp(nay_lp, 900.0, 2800.0, 2) * 0.28
    dbl_hp = hp(nay_dbl, 140.0, 1)

    nay_st = pan_stereo(nay_lp, 0.0)
    dbl_st = pan_stereo(dbl_hp, 0.0)
    # width: delay one side of double
    dly = int(0.014 * SR)
    dbl_w = np.zeros_like(nay_st)
    dbl_w[dly:, 0] = dbl_st[:-dly, 0] * 0.85
    dbl_w[:, 1] = dbl_st[:, 1] * 0.85

    nay_wet = conv_reverb(nay_lp, ir_nay, wet=0.28)
    nay_hall = conv_reverb(nay_lp, ir_hall, wet=0.10)

    drums_mono = drum_bus.mean(axis=1)
    drm_wet = conv_reverb(drums_mono, ir_drm, wet=0.16)
    perc_wet = conv_reverb(perc_bus.mean(axis=1), ir_drm, wet=0.12)
    gtr_wet = conv_reverb(gtr_bus.mean(axis=1), ir_nay, wet=0.10)
    brass_wet = conv_reverb(brass_bus.mean(axis=1), ir_nay, wet=0.18)

    bass_st = pan_stereo(lp(hp(bass_bus, 30.0, 1), 4200.0, 2), 0.0)

    # light sidechain-ish duck of bass on kick transients
    kick_env = np.abs(drum_bus.mean(axis=1))
    # smooth
    win = int(0.03 * SR)
    kernel = np.hanning(win)
    kernel /= kernel.sum()
    duck = np.convolve(kick_env, kernel, mode="same")
    duck = np.clip(duck / (np.percentile(duck, 95) + 1e-9), 0, 1)
    bass_st *= (1.0 - 0.28 * duck)[:, None]

    # assemble
    mix += nay_st * 1.38
    mix += dbl_w * 0.62
    mix += nay_wet * 1.05
    mix += nay_hall * 0.62
    mix += drum_bus * 0.66
    mix += drm_wet * 0.48
    mix += perc_bus * 0.70
    mix += perc_wet * 0.42
    mix += bass_st * 0.66
    mix += gtr_bus * 0.34
    mix += gtr_wet * 0.28
    mix += pad_bus * 0.32
    mix += brass_bus * 0.24
    mix += brass_wet * 0.20
    # air / stadium sheen
    air = np.stack([hp(mix[:, 0], 6500.0, 1), hp(mix[:, 1], 6500.0, 1)], axis=1)
    mix += air * 0.18

    # master: HP rumble, gentle tilt, saturate, limiter
    mix[:, 0] = hp(mix[:, 0], 28.0, 1)
    mix[:, 1] = hp(mix[:, 1], 28.0, 1)
    mix = tanh_sat(mix, drive=1.15)

    # 10 ms fade in, 80 ms fade out
    fade_in = int(0.012 * SR)
    fade_out = int(0.10 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]

    # true-peak-ish limiter
    peak = float(np.max(np.abs(mix)))
    print(f"pre-lim peak={peak:.3f} rms={rms(mix):.4f}")
    target = db(-0.7)  # -0.7 dBFS
    mix = mix * (target / max(peak, 1e-9))
    mix = np.clip(mix, -0.99, 0.99)
    if len(mix) != N:
        # exact length
        if len(mix) > N:
            mix = mix[:N]
        else:
            mix = np.pad(mix, ((0, N - len(mix)), (0, 0)))

    print(f"final peak={np.max(np.abs(mix)):.4f} rms={rms(mix):.4f} dur={len(mix)/SR:.6f}s")
    sf.write(str(OUT_WAV), mix, SR, subtype="FLOAT")
    print("encoding m4a…")
    cmd = [
        str(FFMPEG), "-y",
        "-i", str(OUT_WAV),
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        str(OUT_M4A),
    ]
    subprocess.check_call(cmd)
    print("wrote", OUT_M4A, "bytes", OUT_M4A.stat().st_size)


if __name__ == "__main__":
    build()
