// Turkish Organ Pro — 10 Turkish Instruments Definitions
// Each definition drives AudioEngine._buildInstrumentVoice
// Values tuned by ear against DSK World Stringz, TAQSIM references and real Turkish timbres.
// No copyrighted samples included — all DSP.

export const INSTRUMENTS = [
  {
    id:'saz', name:'Saz / Bağlama', tr:'Bağlama', icon:'🪕', tag:'Folk Lead',
    desc:'Long-neck lute, metallic triple-course chorus',
    oscTypes:['triangle','sawtooth'], detunes:[1,1.007],
    filterType:'lowpass', filterFreq:3200, filterQ:0.9,
    env:{a:0.004,d:0.08,s:0.55,r:0.22}, peakGain:0.62,
    pluck:true, detuneCents:[0,7], reverbSend:0.55,
  },
  {
    id:'oud', name:'Oud (Ud)', tr:'Ud', icon:'🎸', tag:'Warm',
    desc:'Fretless deep lute, warm body resonance',
    oscTypes:['triangle','sine'], detunes:[1,1.003],
    filterType:'lowpass', filterFreq:2100, filterQ:0.85,
    env:{a:0.006,d:0.14,s:0.62,r:0.26}, peakGain:0.58,
    pluck:true, reverbSend:0.6,
  },
  {
    id:'ney', name:'Ney', tr:'Ney', icon:'🎐', tag:'Breathy',
    desc:'End-blown flute, airy Sufi voice',
    oscTypes:['sine'], detunes:[1],
    filterType:'lowpass', filterFreq:2400, filterQ:0.7,
    env:{a:0.05,d:0.18,s:0.82,r:0.32}, peakGain:0.5,
    noise:true, noiseGain:0.11, noiseFreq:1800,
    vibrato:{rate:5.2, depth:12}, reverbSend:0.75,
  },
  {
    id:'kanun', name:'Kanun / Qanun', tr:'Kanun', icon:'🎹', tag:'Shimmer',
    desc:'Zither with mandal levers, bright & ornate',
    oscTypes:['sawtooth','square'], detunes:[1,2.002],
    filterType:'highpass', filterFreq:260, filterQ:0.6, // + lowpass via second stage simulated by EQ
    // We'll boost presence via filterFreq; shimmer via second osc
    env:{a:0.002,d:0.09,s:0.4,r:0.3}, peakGain:0.6,
    pluck:true, detuneCents:[0,2], reverbSend:0.62,
  },
  {
    id:'darbuka', name:'Darbuka', tr:'Darbuka', icon:'🥁', tag:'Percussion',
    desc:'Goblet drum — use rhythm panel for patterns (tap keys for hits)',
    oscTypes:['sine'], detunes:[1],
    filterType:'bandpass', filterFreq:900, filterQ:0.8,
    env:{a:0.001,d:0.05,s:0.0,r:0.12}, peakGain:0.9,
    pluck:false, reverbSend:0.35,
  },
  {
    id:'bendir', name:'Bendir / Def', tr:'Bendir', icon:'🪘', tag:'Frame',
    desc:'Frame drum with jingles, Sufi pulse',
    oscTypes:['sine','triangle'], detunes:[1,1.01],
    filterType:'lowpass', filterFreq:1200, filterQ:0.6,
    env:{a:0.002,d:0.14,s:0.15,r:0.35}, peakGain:0.68,
    reverbSend:0.5,
  },
  {
    id:'kemence', name:'Kemençe', tr:'Kemençe', icon:'🎻', tag:'Bowed',
    desc:'Black Sea fiddle, lyrical bow',
    oscTypes:['sawtooth','triangle'], detunes:[1,1.004],
    filterType:'lowpass', filterFreq:2600, filterQ:1.1,
    env:{a:0.07,d:0.2,s:0.85,r:0.28}, peakGain:0.52,
    vibrato:{rate:5.7, depth:14}, reverbSend:0.62,
  },
  {
    id:'zurna', name:'Zurna', tr:'Zurna', icon:'📯', tag:'Nasal Reed',
    desc:'Double-reed, powerful folk oboe',
    oscTypes:['square','sawtooth'], detunes:[1,1.01],
    filterType:'bandpass', filterFreq:1100, filterQ:1.8,
    env:{a:0.02,d:0.12,s:0.9,r:0.18}, peakGain:0.58,
    reverbSend:0.4,
  },
  {
    id:'clarinet', name:'Turkish Clarinet', tr:'Klarnet (G)', icon:'🎷', tag:'Gypsy Glide',
    desc:'G-Clarinet, weepy portamento king',
    oscTypes:['square','triangle'], detunes:[1,1.002],
    filterType:'lowpass', filterFreq:2800, filterQ:0.9,
    env:{a:0.015,d:0.1,s:0.88,r:0.2}, peakGain:0.54,
    vibrato:{rate:4.8, depth:10}, reverbSend:0.55,
  },
  {
    id:'cumbus', name:'Cümbüş', tr:'Cümbüş', icon:'🪕', tag:'Metallic',
    desc:'Metal-body oud, bright resonator',
    oscTypes:['triangle','sawtooth'], detunes:[1,1.008],
    filterType:'lowpass', filterFreq:3000, filterQ:1.0,
    env:{a:0.003,d:0.1,s:0.5,r:0.32}, peakGain:0.6,
    pluck:true, resonator:true, resonatorDelay:0.0055, resonatorFB:0.32, reverbSend:0.52,
  },
];

export function getInstrument(id){ return INSTRUMENTS.find(i=>i.id===id) || INSTRUMENTS[0]; }
