#!/usr/bin/env python3
"""Render a one-minute instrumental orchestral arrangement in A major.

Uses the existing Waka Waka transcription in ../Nay_WakaWaka.py and the CC0
VSCO 2 Community Edition SFZ instrument maps.  Sample libraries and temporary
WAVs stay outside the repository.  See README.md for setup and rights notes.
"""
from __future__ import annotations

import argparse
import ast
import ctypes as ct
import json
import math
import random
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import mido
import numpy as np
import soundfile as sf
from pedalboard import Reverb
from scipy.signal import butter, sosfilt

SR = 48_000
BPM = 128
BEAT_SAMPLES = SR * 60 // BPM  # 22,500 samples per beat, exactly
TOTAL_BEATS = 128
TOTAL_SAMPLES = TOTAL_BEATS * BEAT_SAMPLES
BLOCK = 1024
TPQ = 960
ROOT = Path(__file__).resolve().parent


@dataclass
class Part:
    name: str
    patch: str
    program: int
    channel: int
    pan: float
    target_db: float
    highpass: float
    hall_send: float
    notes: list[tuple[float, float, int, int]] = field(default_factory=list)


def create_parts() -> list[Part]:
    # One SFZ patch per part. Values are conservative mix targets, not claims
    # about the source samples' original resolution.
    return [
        Part('Flute lead', 'FluteSusVib', 73, 0, -0.04, -23.0, 145, .28),
        Part('Violins sustain', 'ViolinEnsSusVib', 48, 1, -.40, -26.2, 130, .33),
        Part('Violas sustain', 'ViolaEnsSusVib', 48, 2, -.15, -28.8, 105, .32),
        Part('Cellos sustain', 'CelloEnsSusVib', 48, 3, .27, -28.7, 55, .27),
        Part('Contrabass pizzicato', 'ContrabassPizz', 43, 4, .02, -28.2, 32, .09),
        Part('Violins spiccato', 'ViolinEnsSpic', 48, 5, -.35, -30.0, 150, .24),
        Part('Cellos spiccato', 'CelloEnsSpic', 42, 6, .23, -30.4, 75, .20),
        Part('French horn sustain', 'FHornSus', 60, 7, .34, -31.0, 90, .34),
        Part('Trumpet accents', 'TrumpetStac', 56, 8, .29, -33.5, 180, .31),
        Part('Harp', 'Harp', 46, 10, -.30, -31.0, 125, .27),
        Part('Marimba', 'Marimba', 12, 11, -.20, -32.5, 130, .16),
        Part('Glockenspiel', 'Glockenspiel', 9, 12, .40, -35.0, 500, .32),
        Part('Timpani', 'Timpani', 47, 13, .24, -34.0, 35, .24),
        Part('Violins melody double', 'ViolinEnsSusVib', 48, 14, -.20, -28.0, 165, .30),
        Part('Orchestral percussion', 'GM-StylePerc', 0, 9, .10, -30.0, 45, .17),
    ]


def read_existing_melody() -> list[tuple[int, float, float, int, float]]:
    """Read the note transcription already present in this repository.

    Parse only literal calls to M rather than executing that audio-rendering
    script or relying on its (machine-specific) dependencies and paths.
    """
    source = ast.parse((ROOT.parent / 'Nay_WakaWaka.py').read_text(encoding='utf-8'))
    for node in source.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == 'NAY_MELODY' for t in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            raise ValueError('NAY_MELODY is not a list')
        result = []
        for call in node.value.elts:
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != 'M':
                raise ValueError('Unexpected melody entry')
            args = [ast.literal_eval(a) for a in call.args]
            if len(args) == 4:
                args.append(.92)
            if len(args) != 5:
                raise ValueError('Invalid melody entry')
            result.append(tuple(args))
        if not result:
            raise ValueError('The transcription is empty')
        return result
    raise ValueError('NAY_MELODY was not found')


def arrange() -> list[Part]:
    rng = random.Random(2010)
    parts = create_parts()
    by_name = {p.name: p for p in parts}

    def add(name: str, beat: float, duration: float, pitch: int, velocity: float, jitter: bool = True):
        beat += rng.uniform(-.008, .008) if jitter else 0.0
        beat = max(0.0, beat)
        duration = min(duration, TOTAL_BEATS - beat - .01)
        if duration <= 0 or not 0 <= pitch <= 127:
            return
        vel = round(max(1, min(127, velocity + rng.uniform(-2.5, 2.5))))
        by_name[name].notes.append((beat, duration, pitch, vel))

    # D major -> A major, transposed up a fifth for a comfortable flute range.
    # The existing transcription already includes the verse and chorus.
    for bar, beat, duration, pitch, velocity in read_existing_melody():
        if bar == 27 and beat == 3.0:
            duration = .86  # avoid a flute overlap at the start of the outro
        start = bar * 4 + beat
        pitch += 7
        vel = velocity * (94 if bar < 16 else 105)
        add('Flute lead', start, duration * .90, pitch, vel)
        if 16 <= bar < 28:
            add('Violins melody double', start + .025, duration * .82, pitch, vel * .68)

    # Chords in A major: I–V–vi–IV, with a final I cadence.
    chords = ['A', 'E', 'F#m', 'D'] * 7 + ['A', 'E', 'D', 'A']
    voicings = {
        'A':   dict(violin=[69, 73, 76], viola=[57, 61, 64], cello=[45, 52], bass=33, arp=[57, 61, 64, 69, 73], timp=45),
        'E':   dict(violin=[68, 71, 76], viola=[56, 59, 64], cello=[40, 47], bass=28, arp=[56, 59, 64, 68, 71], timp=40),
        'F#m': dict(violin=[69, 73, 78], viola=[57, 61, 66], cello=[42, 49], bass=30, arp=[54, 57, 61, 66, 69], timp=42),
        'D':   dict(violin=[69, 74, 78], viola=[57, 62, 66], cello=[38, 45], bass=38, arp=[57, 62, 66, 69, 74], timp=38),
    }

    for bar, chord in enumerate(chords):
        d = voicings[chord]
        start = bar * 4.0
        if bar < 4:
            dyn = 50 + bar * 2
        elif bar < 12:
            dyn = 59
        elif bar < 16:
            dyn = 65
        elif bar < 28:
            dyn = 75
        elif bar < 31:
            dyn = 60 - (bar - 28) * 4
        else:
            dyn = 62

        # Bowed string sections: staggered starts and short overlaps in the
        # releases make the harmony breathe rather than hard-cut each bar.
        for i, pitch in enumerate(d['violin']):
            add('Violins sustain', start + .035 * i, 3.64, pitch, dyn - i * 2)
        for i, pitch in enumerate(d['viola'][:2]):
            add('Violas sustain', start + .06 + .04 * i, 3.60, pitch, dyn - 4)
        for i, pitch in enumerate(d['cello']):
            add('Cellos sustain', start + .03 + .035 * i, 3.62, pitch, dyn - 5)

        # A sampled harp provides moving inner voices without obscuring the lead.
        if bar < 30:
            order = [0, 2, 3, 1, 2, 4]
            timing = [0.0, .75, 1.5, 2.25, 3.0, 3.5]
            for i, (bt, k) in enumerate(zip(timing, order)):
                if bar < 4 and i in (1, 4):
                    continue
                add('Harp', start + bt, .65, d['arp'][k], dyn - 4 + (4 if i in (0, 3) else 0))

        if 2 <= bar < 30:
            bass_pattern = [(0, d['bass']), (1.5, d['bass'] + 7), (2.0, d['bass'] + 12), (3.0, d['bass'])]
            for i, (bt, pitch) in enumerate(bass_pattern):
                add('Contrabass pizzicato', start + bt, .7 if i != 3 else .5, pitch, dyn + (7 if i == 0 else 0))

        if 4 <= bar < 30:
            for i, bt in enumerate((.5, 1.5, 2.5, 3.5)):
                add('Violins spiccato', start + bt, .30, d['violin'][i % 3], dyn - 6 + (4 if i % 2 else 0))
            for i, bt in enumerate((0, .75, 1.5, 2.25, 3.0, 3.5)):
                pitch = d['cello'][i % 2] + (12 if i == 3 else 0)
                add('Cellos spiccato', start + bt, .28, pitch, dyn - 7 + (4 if i in (0, 4) else 0))

        if 6 <= bar < 30:
            horn_notes = d['viola'][1:] if bar >= 16 else d['viola'][1:2]
            for i, pitch in enumerate(horn_notes):
                add('French horn sustain', start + .08 * i, 3.45, pitch, dyn - 8)

        if 16 <= bar < 28 and bar % 4 in (0, 2):
            for bt in (0.0, 2.5):
                for i, pitch in enumerate(d['violin'][1:]):
                    add('Trumpet accents', start + bt + i * .025, .32, pitch, dyn - 8)

        if 4 <= bar < 30:
            # 3+3+2-inspired pulse, played on real marimba and hand percussion.
            for i, bt in enumerate((0, .75, 1.5, 2.25, 3.0, 3.5)):
                add('Marimba', start + bt, .25, d['arp'][[0, 2, 1, 3, 2, 1][i]], dyn - 10 + (5 if i in (0, 3) else 0))

        if bar in (3, 11, 15, 19, 23, 27, 30):
            for i, pitch in enumerate(d['violin'][1:]):
                add('Glockenspiel', start + 3.0 + .25 * i, .45, min(pitch + 12, 96), dyn - 10)
        if bar in (0, 4, 8, 12, 15, 16, 20, 24, 27, 30, 31):
            add('Timpani', start, 1.0, d['timp'], dyn + (8 if bar in (16, 24, 31) else 0))

        if 2 <= bar < 30:
            # GM-style percussion maps in VSCO: orchestral bass drum, conga,
            # tambourine, claves and snare. Keep it a supportive acoustic pulse.
            for bt in ((0.0, 2.0) if bar < 16 else (0.0, 1.5, 2.0, 3.5)):
                add('Orchestral percussion', start + bt, .18, 36, dyn - 2)
            for bt, note, offset in ((0.75, 61, -12), (1.5, 63, -7), (2.25, 62, -10), (3.0, 65, -5), (3.5, 63, -10)):
                add('Orchestral percussion', start + bt, .16, note, dyn + offset)
            if bar >= 4:
                for bt in (1.0, 3.0):
                    add('Orchestral percussion', start + bt, .16, 38, dyn - 8)
                for bt in (.5, 1.5, 2.5, 3.5):
                    add('Orchestral percussion', start + bt, .10, 53, dyn - 13)
            if bar >= 12 and bar % 4 == 3:
                add('Orchestral percussion', start + 3.5, .18, 75, dyn - 3)
            if bar in (16, 24):
                add('Orchestral percussion', start, .40, 49, dyn - 5)

    for part in parts:
        if not part.notes:
            raise ValueError(f'Empty part: {part.name}')
    return parts


def write_midi(parts: list[Part], path: Path) -> None:
    midi = mido.MidiFile(type=1, ticks_per_beat=TPQ)
    meta = mido.MidiTrack()
    midi.tracks.append(meta)
    meta.append(mido.MetaMessage('track_name', name='Waka Waka - A major - 128 BPM', time=0))
    meta.append(mido.MetaMessage('set_tempo', tempo=468750, time=0))
    meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    meta.append(mido.MetaMessage('key_signature', key='A', time=0))
    meta.append(mido.MetaMessage('end_of_track', time=TOTAL_BEATS * TPQ))
    for part in parts:
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.MetaMessage('track_name', name=f'{part.name} - VSCO {part.patch}', time=0))
        if part.channel != 9:
            track.append(mido.Message('program_change', channel=part.channel, program=part.program, time=0))
        events = []
        for start, duration, pitch, velocity in part.notes:
            events.append((round(start * TPQ), 1, pitch, velocity))
            events.append((round((start + duration) * TPQ), 0, pitch, 0))
        events.sort()  # note-offs before note-ons at the same tick
        previous = 0
        for tick, on, pitch, vel in events:
            track.append(mido.Message('note_on' if on else 'note_off', channel=part.channel,
                                      note=pitch, velocity=vel, time=tick - previous))
            previous = tick
        track.append(mido.MetaMessage('end_of_track', time=max(0, TOTAL_BEATS * TPQ - previous)))
    midi.save(path)


class Sfizz:
    def __init__(self, lib_path: Path):
        self.lib = ct.CDLL(str(lib_path))
        p, i = ct.c_void_p, ct.c_int
        float_ptr = ct.POINTER(ct.c_float)
        self.lib.sfizz_create_synth.argtypes = []
        self.lib.sfizz_create_synth.restype = p
        self.lib.sfizz_free.argtypes = [p]
        self.lib.sfizz_load_file.argtypes = [p, ct.c_char_p]
        self.lib.sfizz_load_file.restype = ct.c_bool
        self.lib.sfizz_set_samples_per_block.argtypes = [p, i]
        self.lib.sfizz_set_sample_rate.argtypes = [p, ct.c_float]
        self.lib.sfizz_set_sample_quality.argtypes = [p, i, i]
        self.lib.sfizz_set_num_voices.argtypes = [p, i]
        self.lib.sfizz_enable_freewheeling.argtypes = [p]
        self.lib.sfizz_send_note_on.argtypes = [p, i, i, i]
        self.lib.sfizz_send_note_off.argtypes = [p, i, i, i]
        self.lib.sfizz_render_block.argtypes = [p, ct.POINTER(float_ptr), i, i]

    def render(self, part: Part, vsco: Path) -> np.ndarray:
        patch = vsco / (part.patch + '.sfz')
        if not patch.is_file():
            raise FileNotFoundError(patch)
        synth = self.lib.sfizz_create_synth()
        if not synth:
            raise RuntimeError('Could not create sfizz synth')
        try:
            self.lib.sfizz_set_samples_per_block(synth, BLOCK)
            self.lib.sfizz_set_sample_rate(synth, SR)
            self.lib.sfizz_set_num_voices(synth, 128)
            self.lib.sfizz_set_sample_quality(synth, 1, 7)  # freewheeling/offline
            self.lib.sfizz_enable_freewheeling(synth)
            if not self.lib.sfizz_load_file(synth, str(patch).encode()):
                raise RuntimeError(f'Could not load {patch}')
            events = []
            for start, duration, pitch, velocity in part.notes:
                events.append((round(start * BEAT_SAMPLES), 1, pitch, velocity))
                events.append((round((start + duration) * BEAT_SAMPLES), 0, pitch, 0))
            events.sort()
            out = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
            left = np.zeros(BLOCK, dtype=np.float32)
            right = np.zeros(BLOCK, dtype=np.float32)
            ptrs = (ct.POINTER(ct.c_float) * 2)(left.ctypes.data_as(ct.POINTER(ct.c_float)),
                                                right.ctypes.data_as(ct.POINTER(ct.c_float)))
            ei = 0
            for start in range(0, TOTAL_SAMPLES, BLOCK):
                n = min(BLOCK, TOTAL_SAMPLES - start)
                while ei < len(events) and events[ei][0] < start + n:
                    frame, on, pitch, vel = events[ei]
                    if frame >= start:
                        sender = self.lib.sfizz_send_note_on if on else self.lib.sfizz_send_note_off
                        sender(synth, frame - start, pitch, vel)
                    ei += 1
                self.lib.sfizz_render_block(synth, ptrs, 2, n)
                out[start:start+n, 0] = left[:n]
                out[start:start+n, 1] = right[:n]
            if not np.isfinite(out).all() or float(np.max(np.abs(out))) < 1e-6:
                raise RuntimeError(f'No valid sound rendered for {part.name}; check sample paths')
            return out
        finally:
            self.lib.sfizz_free(synth)


def pan_stereo(x: np.ndarray, amount: float) -> np.ndarray:
    # Stereo-preserving balance: avoid losing the original stereo samples.
    angle = (amount + 1.0) * math.pi / 4.0
    middle = (x[:, 0] + x[:, 1]) * .5
    side = (x[:, 0] - x[:, 1]) * .5
    left = middle * (math.cos(angle) * math.sqrt(2)) + side * .8
    right = middle * (math.sin(angle) * math.sqrt(2)) - side * .8
    return np.column_stack((left, right)).astype(np.float32)


def mix_parts(parts: list[Part], synth: Sfizz, vsco: Path, work: Path) -> Path:
    mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
    hall = np.zeros_like(mix)
    for part in parts:
        print(f'Rendering: {part.name} ({len(part.notes)} notes)', flush=True)
        x = synth.render(part, vsco)
        sos = butter(2, part.highpass, btype='highpass', fs=SR, output='sos')
        x = sosfilt(sos, x, axis=0).astype(np.float32)
        x = pan_stereo(x, part.pan)
        # Normalise once per instrument, not per note: velocities and section
        # dynamics remain intact. Use upper active-window RMS to avoid boosting
        # quiet tails; cap transients conservatively before summing.
        window = SR // 5
        powers = np.mean(x[:(len(x)//window)*window].reshape(-1, window, 2) ** 2, axis=(1, 2))
        rms = np.sqrt(powers)
        active = rms[rms > max(float(np.max(rms)) * .025, 1e-8)]
        reference = float(np.percentile(active, 75))
        peak = float(np.max(np.abs(x)))
        gain = min(10 ** (part.target_db / 20) / max(reference, 1e-9), .46 / max(peak, 1e-9))
        print(f'  reference={reference:.5f}, peak={peak:.4f}, gain={gain:.2f}', flush=True)
        x *= gain
        mix += x
        hall += x * part.hall_send
        del x

    # A single shared stereo hall places the acoustic instruments together.
    reverb = Reverb(room_size=.64, damping=.58, wet_level=1.0, dry_level=0.0, width=.95)
    wet = reverb(hall.T.copy(), SR).T
    mix += wet * .36
    del hall, wet
    mix = sosfilt(butter(2, 25, btype='highpass', fs=SR, output='sos'), mix, axis=0).astype(np.float32)
    # No hard clipping. Fade out the last chord gracefully inside exactly 60 s.
    fi, fo = int(.08 * SR), int(.65 * SR)
    mix[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    if not np.isfinite(mix).all():
        raise RuntimeError('Non-finite samples in mix')
    out = work / 'orchestral_premaster_float.wav'
    sf.write(out, mix, SR, subtype='FLOAT')
    print(f'Premaster peak={np.max(np.abs(mix)):.4f}, rms={np.sqrt(np.mean(mix**2)):.5f}', flush=True)
    return out


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def export(premaster: Path, ffmpeg: Path, work: Path, output: Path) -> None:
    # Two-pass EBU R128: preserve dynamics and leave headroom for AAC.
    measure = run([str(ffmpeg), '-hide_banner', '-nostats', '-i', str(premaster),
                   '-af', 'loudnorm=I=-15.5:TP=-1.8:LRA=11:print_format=json',
                   '-f', 'null', '-'], capture=True)
    matches = re.findall(r'\{\s*"input_i".*?\}', measure.stderr, re.S)
    if not matches:
        raise RuntimeError('Could not read loudness measurements')
    m = json.loads(matches[-1])
    measured = [m[k] for k in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset')]
    if not all(math.isfinite(float(v)) for v in measured):
        raise RuntimeError('Invalid loudness measurement')
    print('Loudness measurement:', json.dumps(m), flush=True)
    filt = (f'loudnorm=I=-15.5:TP=-1.8:LRA=11:measured_I={measured[0]}:'
            f'measured_TP={measured[1]}:measured_LRA={measured[2]}:'
            f'measured_thresh={measured[3]}:offset={measured[4]}:linear=true,'
            'aresample=48000:resampler=soxr:precision=28:dither_method=triangular,'
            'atrim=end_sample=2880000,asetpts=N/SR/TB')
    master = work / 'orchestral_master_24bit.wav'
    run([str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(premaster),
         '-af', filt, '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s24le', str(master)])
    common = [str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(master),
              '-map_metadata', '-1', '-metadata', 'title=Waka Waka - Orchestral Arrangement in A Major',
              '-metadata', 'artist=Instrumental orchestral arrangement',
              '-metadata', 'comment=VSCO 2 Community Edition samples; instrumental cover',
              '-movflags', '+faststart']
    lossless = output / 'WakaWaka_Orchestral_A_Lossless.m4a'
    compatible = output / 'WakaWaka_Orchestral_A_AAC.m4a'
    run(common + ['-c:a', 'alac', '-sample_fmt', 's32p', '-bits_per_raw_sample', '24', str(lossless)])
    run(common + ['-c:a', 'aac', '-b:a', '320k', '-ar', str(SR), str(compatible)])
    print('Wrote', lossless, 'and', compatible, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vsco', type=Path, required=True, help='VSCO 2 CE SFZ directory including samples')
    parser.add_argument('--libsfizz', type=Path, required=True, help='Path to libsfizz shared library')
    parser.add_argument('--ffmpeg', type=Path, required=True, help='Path to ffmpeg executable')
    parser.add_argument('--work', type=Path, required=True, help='Scratch directory for WAV files')
    parser.add_argument('--output', type=Path, default=ROOT, help='Output directory')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    parts = arrange()
    midi = args.output / 'WakaWaka_Orchestral_A.mid'
    write_midi(parts, midi)
    premaster = mix_parts(parts, Sfizz(args.libsfizz), args.vsco, args.work)
    export(premaster, args.ffmpeg, args.work, args.output)
    print(f'Arrangement: {len(parts)} instruments, {sum(len(p.notes) for p in parts)} notes; '
          f'{TOTAL_SAMPLES/SR:.3f} s at {SR} Hz; MIDI: {midi}', flush=True)


if __name__ == '__main__':
    main()
