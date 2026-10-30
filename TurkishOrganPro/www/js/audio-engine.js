// Turkish Organ Pro — Audio Engine v1
// Web Audio, low-latency, Redmi 13 optimized (48kHz, look-ahead scheduler)
// Provides: init, master controls, instrument voice creation, rhythm scheduler

export const AudioEngine = {
  ctx: null,
  master: null,
  limiter:null,
  reverb:null,
  reverbGain:null,
  convolver:null,
  masterEQ:{bass:null,mid:null,treble:null},
  voices: new Map(), // midiNote -> nodes[]
  rhythmTimer: null,
  isRhythmPlaying:false,
  tempo:120,
  swing:0,
  rhythmGain:null,
  metronomeGain:null,
  pitchBend:0, // semitones
  octave:0,
  transpose:0,
  masterTune:440,
  reverbWet:0.18,
  chorusDepth:0,
  _reverbIRBuffer:null,
  _chorusNodes:null,

  async init() {
    if(this.ctx) return;
    this.ctx = new (window.AudioContext||window.webkitAudioContext)({latencyHint:'interactive', sampleRate:48000});
    // Master chain: voices -> limiter? -> reverb send -> master EQ -> master -> destination
    this.master = this.ctx.createGain(); this.master.gain.value=0.9;
    this.rhythmGain = this.ctx.createGain(); this.rhythmGain.gain.value=0.85;
    this.metronomeGain = this.ctx.createGain(); this.metronomeGain.gain.value=0.0;

    // EQ
    this.masterEQ.bass = this.ctx.createBiquadFilter(); this.masterEQ.bass.type='lowshelf'; this.masterEQ.bass.frequency.value=180; this.masterEQ.bass.gain.value=0;
    this.masterEQ.mid = this.ctx.createBiquadFilter(); this.masterEQ.mid.type='peaking'; this.masterEQ.mid.frequency.value=1000; this.masterEQ.mid.Q.value=0.9; this.masterEQ.mid.gain.value=0;
    this.masterEQ.treble = this.ctx.createBiquadFilter(); this.masterEQ.treble.type='highshelf'; this.masterEQ.treble.frequency.value=5200; this.masterEQ.treble.gain.value=0;

    // Reverb (generated impulse, no external file)
    this.convolver = this.ctx.createConvolver();
    this.reverbGain = this.ctx.createGain(); this.reverbGain.gain.value=this.reverbWet;
    this._makeImpulse(2.2, 2.0); // seconds, decay
    this.reverb = this.convolver;

    // Dynamics
    this.limiter = this.ctx.createDynamicsCompressor();
    this.limiter.threshold.value=-6; this.limiter.ratio.value=12; this.limiter.attack.value=0.003; this.limiter.release.value=0.22;

    // Wiring
    this.master.connect(this.masterEQ.bass);
    this.masterEQ.bass.connect(this.masterEQ.mid);
    this.masterEQ.mid.connect(this.masterEQ.treble);
    this.masterEQ.treble.connect(this.limiter);
    this.limiter.connect(this.ctx.destination);

    // Reverb send wiring: each voice connects also to convolver via reverbGain path — handled per voice
    // Rhythm / metronome direct to master
    this.rhythmGain.connect(this.master);
    this.metronomeGain.connect(this.master);

    // Resume on interaction if suspended
    if(this.ctx.state==='suspended') await this.ctx.resume();
  },

  _makeImpulse(seconds, decay){
    const rate=this.ctx.sampleRate, len=Math.floor(rate*seconds);
    const buf=this.ctx.createBuffer(2,len,rate);
    for(let ch=0; ch<2; ch++){
      const data=buf.getChannelData(ch);
      for(let i=0;i<len;i++){
        data[i]=(Math.random()*2-1)*Math.pow(1 - i/len, decay) * 0.6;
      }
    }
    this.convolver.buffer=buf;
    // connect convolver -> reverbGain -> masterEQ
    try{ this.convolver.disconnect(); }catch{}
    try{ this.reverbGain.disconnect(); }catch{}
    this.convolver.connect(this.reverbGain);
    this.reverbGain.connect(this.masterEQ.bass);
  },

  ensure(){
    if(!this.ctx) throw new Error('Audio not initialized — call init() on user gesture');
    if(this.ctx.state==='suspended') this.ctx.resume();
  },

  noteFreq(midi){
    // midi 69 = A4. Use masterTune as A4 reference
    const a4=this.masterTune;
    return a4 * Math.pow(2,(midi-69)/12);
  },

  // Create a voice for a given midi note and instrument definition
  playNote(midi, velocity=100, inst, centsDetune=0){
    this.ensure();
    const freq = this.noteFreq(midi + this.octave*12 + this.transpose) * Math.pow(2, centsDetune/1200) * Math.pow(2, this.pitchBend/12);
    const vel = Math.max(0,Math.min(127,velocity))/127;
    const now=this.ctx.currentTime;
    const nodes = this._buildInstrumentVoice(inst, freq, vel, now);
    this.voices.set(midi, nodes);
    return nodes;
  },

  stopNote(midi){
    const nodes=this.voices.get(midi);
    if(!nodes) return;
    const now=this.ctx.currentTime;
    nodes.forEach(n=>{
      try{
        if(n.gain){
          const rel = n.release || 0.18;
          n.gain.gain.cancelScheduledValues(now);
          n.gain.gain.setValueAtTime(n.gain.gain.value, now);
          n.gain.gain.linearRampToValueAtTime(0.0001, now + rel);
        }
        if(n.osc){
          n.osc.forEach(o=>{ try{o.stop(now + (n.release||0.2)+0.05);}catch{} });
        } else if(n.src) {
          try{n.src.stop(now + (n.release||0.2)+0.05);}catch{}
        }
      }catch{}
    });
    setTimeout(()=>{ this.voices.delete(midi); nodes.forEach(n=>{ try{n.gain.disconnect();}catch{} try{n.filter&&n.filter.disconnect();}catch{} }); }, 600);
  },

  allNotesOff(){
    for(const k of this.voices.keys()) this.stopNote(k);
  },

  _buildInstrumentVoice(inst, freq, vel, now){
    // Returns array of node groups {osc, gain, filter, release}
    // Each instrument defines: type, oscTypes, filter, envelope, detune, chorus
    const def = inst;
    const outGain=this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();
    filter.type = def.filterType || 'lowpass';
    filter.frequency.value = def.filterFreq || 2400;
    filter.Q.value = def.filterQ || 0.8;

    // Envelope
    const env = def.env || {a:0.008,d:0.12,s:0.7,r:0.22};
    const peak = (def.peakGain||0.55) * (0.6 + vel*0.7);
    outGain.gain.setValueAtTime(0.0001, now);
    outGain.gain.linearRampToValueAtTime(peak, now+env.a);
    outGain.gain.linearRampToValueAtTime(peak*env.s, now+env.a+env.d);

    let oscs=[];
    // Primary oscillators
    const types = def.oscTypes || ['triangle'];
    types.forEach((t,i)=>{
      const o=this.ctx.createOscillator();
      o.type=t;
      o.frequency.value = freq * (def.detunes?.[i] || 1);
      if(def.detuneCents) o.detune.value = def.detuneCents[i]||0;
      // breath noise for Ney etc handled separately
      o.connect(filter);
      o.start(now);
      oscs.push(o);
    });

    // Breath / noise layer
    let noiseNode=null;
    if(def.noise){
      const bufSize = this.ctx.sampleRate * 0.6;
      const buf=this.ctx.createBuffer(1, bufSize, this.ctx.sampleRate);
      const ch=buf.getChannelData(0);
      for(let i=0;i<bufSize;i++) ch[i]=(Math.random()*2-1)*0.5;
      const src=this.ctx.createBufferSource(); src.buffer=buf; src.loop=true;
      const bp=this.ctx.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value=def.noiseFreq||1800; bp.Q.value=1.1;
      const ng=this.ctx.createGain(); ng.gain.value = (def.noiseGain||0.12)*vel;
      src.connect(bp); bp.connect(ng); ng.connect(filter);
      src.start(now);
      // reuse release handling
      oscs.push(src);
      noiseNode=src;
    }

    // Metallic resonator for Cümbüş
    let resonator=null;
    if(def.resonator){
      const delay=this.ctx.createDelay(0.02); delay.delayTime.value= def.resonatorDelay||0.006;
      const fb=this.ctx.createGain(); fb.gain.value=def.resonatorFB||0.35;
      const ap=this.ctx.createBiquadFilter(); ap.type='allpass'; ap.frequency.value=2500; ap.Q.value=2;
      filter.connect(delay); delay.connect(ap); ap.connect(fb); fb.connect(filter);
      resonator={delay,fb,ap};
    }

    // Pluck transient — short click
    if(def.pluck){
      const click=this.ctx.createOscillator(); click.type='square'; click.frequency.value=freq*2;
      const cg=this.ctx.createGain(); cg.gain.value=0.25*vel;
      cg.gain.setValueAtTime(0.25*vel, now);
      cg.gain.exponentialRampToValueAtTime(0.0001, now+0.02);
      click.connect(cg); cg.connect(filter);
      click.start(now); click.stop(now+0.025);
    }

    // vibrato LFO (for Kemençe, Ney)
    if(def.vibrato){
      const lfo=this.ctx.createOscillator(); lfo.type='sine'; lfo.frequency.value=def.vibrato.rate||5.5;
      const lfoGain=this.ctx.createGain(); lfoGain.gain.value=def.vibrato.depth||6; // cents
      lfo.connect(lfoGain);
      oscs.forEach(o=>{ if(o.detune) lfoGain.connect(o.detune); });
      lfo.start(now);
    }

    filter.connect(outGain);
    outGain.connect(this.master);
    // reverb send
    const send=this.ctx.createGain(); send.gain.value = this.reverbWet * (def.reverbSend||0.7);
    filter.connect(send); send.connect(this.convolver);

    return [{osc:oscs, gain:outGain, filter, release:env.r, send, resonator, noise:noiseNode}];
  },

  // --- Rhythm engine ---
  // Simple look-ahead scheduler: schedule next 0.4s every 25ms
  _rhythmPattern:null,
  _rhythmNextTime:0,
  _rhythmStep:0,
  _scheduler:null,

  playRhythm(pattern){ // pattern: {name, meter, bpm, steps:[{t, type, vel}]}
    this.ensure();
    this._rhythmPattern=pattern;
    this.tempo=pattern.bpm || 120;
    this._rhythmStep=0;
    this._rhythmNextTime=this.ctx.currentTime+0.05;
    this.isRhythmPlaying=true;
    if(this._scheduler) clearInterval(this._scheduler);
    this._scheduler=setInterval(()=>this._schedulerTick(), 25);
    this._schedulerTick();
  },
  stopRhythm(){
    this.isRhythmPlaying=false;
    if(this._scheduler) clearInterval(this._scheduler);
    this._scheduler=null;
  },
  setTempo(bpm){
    this.tempo=Math.max(40, Math.min(220, bpm));
    if(this._rhythmPattern) this._rhythmPattern.bpm=this.tempo;
  },

  _schedulerTick(){
    if(!this.isRhythmPlaying || !this._rhythmPattern) return;
    const lookAhead=0.45;
    while(this._rhythmNextTime < this.ctx.currentTime + lookAhead){
      const pat=this._rhythmPattern;
      const step = pat.steps[this._rhythmStep % pat.steps.length];
      this._triggerPerc(step, this._rhythmNextTime);
      // advance
      const stepsPerBeat = pat.resolution || 4; // steps per beat
      const secPerBeat = 60/this.tempo;
      const stepDur = secPerBeat / (stepsPerBeat/4) * (step.len||1) ; // crude
      // Actually use pattern step Duration precomputed: pat.stepSec
      const dur = pat.stepSec || (secPerBeat/2);
      this._rhythmNextTime += dur;
      this._rhythmStep++;
    }
  },

  _triggerPerc(step, when){
    if(!step || step.type==='-') return;
    const t=step.type; // D,T,k,S
    let f1=80, f2=55, noise=0;
    let gain=0.7* (step.vel||1);
    if(t==='D'){ f1=95; f2=52; gain*=1.0; }
    if(t==='T'){ f1=165; f2=110; gain*=0.78; }
    if(t==='k'){ f1=210; f2=140; gain*=0.52; }
    if(t==='S'){ f1=120; noise=0.22; }
    if(t==='R'){ // Riq jingle
      const buf=this.ctx.createBuffer(1, Math.floor(this.ctx.sampleRate*0.08), this.ctx.sampleRate);
      const d=buf.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*Math.exp(-i/d.length*28)*0.8;
      const src=this.ctx.createBufferSource(); src.buffer=buf;
      const hp=this.ctx.createBiquadFilter(); hp.type='highpass'; hp.frequency.value=4200;
      const g=this.ctx.createGain(); g.gain.value=gain*0.6;
      g.gain.setValueAtTime(gain*0.6, when);
      g.gain.exponentialRampToValueAtTime(0.0001, when+0.18);
      src.connect(hp); hp.connect(g); g.connect(this.rhythmGain);
      src.start(when); src.stop(when+0.2);
      return;
    }
    // membrane synth: sine sweep + slap
    const osc=this.ctx.createOscillator(); osc.type='sine'; osc.frequency.setValueAtTime(f1, when); osc.frequency.exponentialRampToValueAtTime(f2, when+0.06);
    const amp=this.ctx.createGain(); amp.gain.setValueAtTime(0, when); amp.gain.linearRampToValueAtTime(gain, when+0.002); amp.gain.exponentialRampToValueAtTime(0.0001, when+0.22);
    const filt=this.ctx.createBiquadFilter(); filt.type='bandpass'; filt.frequency.value=900; filt.Q.value=0.7;
    osc.connect(filt); filt.connect(amp); amp.connect(this.rhythmGain);
    osc.start(when); osc.stop(when+0.25);
    // slap click
    if(noise>0 || t==='T' || t==='k'){
      const b=this.ctx.createBuffer(1, Math.floor(this.ctx.sampleRate*0.015), this.ctx.sampleRate);
      const d=b.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*Math.exp(-i/d.length*40);
      const s=this.ctx.createBufferSource(); s.buffer=b;
      const bp=this.ctx.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value=2800; bp.Q.value=1;
      const ng=this.ctx.createGain(); ng.gain.value= gain* (t==='k'?0.22:0.14);
      ng.gain.setValueAtTime(ng.gain.value, when);
      ng.gain.exponentialRampToValueAtTime(0.0001, when+0.04);
      s.connect(bp); bp.connect(ng); ng.connect(this.rhythmGain);
      s.start(when);
    }
    // click visual callback if present
    if(this.onRhythmStep) this.onRhythmStep(this._rhythmStep, t);
  },

  // Live controls
  setReverb(v){ this.reverbWet=Math.max(0,Math.min(1,v)); if(this.reverbGain) this.reverbGain.gain.value=this.reverbWet; },
  setMasterVolume(v){ if(this.master) this.master.gain.value=Math.max(0,Math.min(1.2,v)); },
  setRhythmVolume(v){ if(this.rhythmGain) this.rhythmGain.gain.value=Math.max(0,Math.min(1.2,v)); },
  setEQ(b,m,t){ if(this.masterEQ.bass) this.masterEQ.bass.gain.value=b; if(this.masterEQ.mid) this.masterEQ.mid.gain.value=m; if(this.masterEQ.treble) this.masterEQ.treble.gain.value=t; },
  setPitchBend(semi){ this.pitchBend=Math.max(-12,Math.min(12,semi)); // applied on next notes; for held notes we could glide — simplified: pitch bend handled via detune on active voices
  },
  setMasterTune(hz){ this.masterTune=Math.max(392,Math.min(452,hz)); },
};
