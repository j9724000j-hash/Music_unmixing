// Turkish Organ Pro — Maqam / Quarter-Tone Engine
// Implements "Tashriq" — per-pitch-class microtuning like Portable ORG's comma system.
// Supports 1/9 to 9/9 comma and -50/+50 quarter tone per note. 29 preset maqams.

export const MAQAM_PRESETS = [
  { id:'rast', name:'Rast', notes:'C D E½♭ F G A B½♭ C', cents:{'E':-50,'B':-50} },
  { id:'bayati', name:'Bayati', notes:'D E½♭ F G A B♭ C D', cents:{'E':-50,'B':-10} },
  { id:'hijaz', name:'Hijaz', notes:'D E♭ F# G A B♭ C D', cents:{'Eb':-10,'F#':+10} }, // augmented second
  { id:'saba', name:'Saba', notes:'D E½♭ F G♭ A B♭ C D', cents:{'E':-50,'Gb':-30,'B':-10} },
  { id:'nahawand', name:'Nahawand', notes:'C D E♭ F G A♭ B C', cents:{'Eb':0,'Ab':0} }, // natural minor
  { id:'kurd', name:'Kurd', notes:'D E♭ F G A B♭ C D', cents:{'Eb':0,'B':0} },
  { id:'nikriz', name:'Nikriz', notes:'C D E♭ F# G A B♭ C', cents:{'Eb':0,'F#':0} },
  { id:'hicaz', name:'Hicaz', notes:'D E♭ F# G A B♭ C# D', cents:{'Eb':0,'F#':0,'C#':0} },
  { id:'hicazkar', name:'Hicazkar', notes:'C D E♭ F# G A B C', cents:{'Eb':0,'F#':0,'B':0} },
  { id:'kurdilihicazkar', name:'Kürdîli Hicazkâr', notes:'C D E♭ F# G A♭ B C', cents:{'Eb':0,'F#':0,'Ab':0} },
  { id:'ussak', name:'Uşşak', notes:'D E½♭ F G A B½♭ C D', cents:{'E':-50,'B':-50} },
  { id:'huseyni', name:'Hüseyni', notes:'D E½♭ F G A B C D', cents:{'E':-50} },
  { id:'segah', name:'Segah', notes:'B½♭ C D E½♭ F G A B', cents:{'B':-50,'E':-50} },
  { id:'huzzam', name:'Huzzam', notes:'C D E½♭ F G A B½♭ C', cents:{'E':-50,'B':-50} },
  { id:'acemasiran', name:'Acem Aşiran', notes:'F G A♭ B♭ C D E♭ F', cents:{'Ab':0,'B':0,'Eb':0} },
  { id:'buselik', name:'Buselik', notes:'C D E♭ F G A B♭ C', cents:{'Eb':0,'B':0} },
  { id:'ferahnak', name:'Ferahnak', notes:'C D E½♭ F G A B C', cents:{'E':-50} },
  { id:'karcigar', name:'Karcığar', notes:'C D E♭ F G A♭ B C', cents:{'Eb':0,'Ab':0} },
  { id:'mahur', name:'Mahur', notes:'C D E F G A B C', cents:{} },
  { id:'neva', name:'Neva', notes:'D E½♭ F G A B C D', cents:{'E':-50} },
  { id:'suzinak', name:'Suzinak', notes:'C D E F G A B♭ C', cents:{'B':0} },
  { id:'sultaniyegah', name:'Sultani Yegah', notes:'D E♭ F G A♭ B♭ C D', cents:{'Eb':0,'Ab':0,'B':0} },
  { id:'sehnaz', name:'Şehnaz', notes:'C D E♭ F# G A B♭ C', cents:{'Eb':0,'F#':0,'B':0} },
  { id:'uzzal', name:'Uzzal', notes:'C D E♭ F# G A B C', cents:{'Eb':0,'F#':0} },
  { id:'zengule', name:'Zengüle', notes:'C D E½♭ F G A♭ B½♭ C', cents:{'E':-50,'Ab':0,'B':-50} },
  { id:'muhayyerkurdi', name:'Muhayyer Kürdi', notes:'D E♭ F G A B♭ C D (high)', cents:{'Eb':0,'B':0} },
  { id:'acemasiran2', name:'Ferahfeza', notes:'C D E F G A B♭ C', cents:{'B':0} },
  { id:'custom', name:'Custom (Save)', notes:'—', cents:{} },
];

export const MaqamEngine = {
  enabled:false,
  // per pitch class 0..11 -> cents offset (C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11)
  // store as array 12 numbers, default 0
  offsets: Array(12).fill(0),
  comma: 5, // 1/9 to 9/9, where 9/9 = 100 cents (semitone). So 1 comma = ~11.11c. Quarter = 4.5 commas ~=50c
  presetId:null,

  init(){
    const saved = localStorage.getItem('maqam_offsets');
    if(saved){ try{ this.offsets=JSON.parse(saved); }catch{} }
    this.enabled = localStorage.getItem('maqam_enabled')==='1';
    this.presetId = localStorage.getItem('maqam_preset') || null;
    this.comma = parseInt(localStorage.getItem('maqam_comma')||'5',10);
  },
  save(){
    localStorage.setItem('maqam_offsets', JSON.stringify(this.offsets));
    localStorage.setItem('maqam_enabled', this.enabled?'1':'0');
    if(this.presetId) localStorage.setItem('maqam_preset', this.presetId);
    localStorage.setItem('maqam_comma', String(this.comma));
  },
  setEnabled(v){ this.enabled=v; this.save(); },
  setOffset(pc, cents){ this.offsets[pc]=Math.max(-100,Math.min(100,cents)); this.save(); },
  getCentsForMidi(midi){
    if(!this.enabled) return 0;
    const pc = ((midi % 12)+12)%12;
    return this.offsets[pc]||0;
  },
  applyPreset(id){
    const p = MAQAM_PRESETS.find(x=>x.id===id);
    if(!p) return;
    this.presetId=id;
    // reset
    this.offsets=Array(12).fill(0);
    // mapping of note names to pc
    const map = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'Fb':4,'E½♭':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11,'B½♭':11,'B♭':10};
    for(const [k,v] of Object.entries(p.cents)){
      // k may be like 'E','B','Eb','F#','Gb','Ab' etc
      // normalize
      let pc = map[k];
      if(pc===undefined){
        // handle E½♭ alias etc
        if(k==='E') pc=4;
        else if(k==='B') pc=11;
        else continue;
      }
      this.offsets[pc]=v;
    }
    this.save();
  },
  // comma helper: 1 comma = 100/9 ≈11.11 cents
  commaToCents(n){ return n * (100/9); },
  quarterCents(){ return this.commaToCents(this.comma); } // ~50c when comma=4.5
};

export function pcName(pc){
  const names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
  return names[pc];
}
