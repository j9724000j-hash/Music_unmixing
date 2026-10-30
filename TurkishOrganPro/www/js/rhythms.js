// Turkish Organ Pro — 10 Turkish Rhythms
// Step-based patterns for AudioEngine rhythm scheduler.
// Types: D = Dum (low center), T = Tek (high rim), k = Ka (soft), R = Riq jingle, - = rest
// stepSec computed from tempo & meter. Patterns tuned against Portable ORG & real Turkish percussion.

export const RHYTHMS = [
  {
    id:'duyek', name:'Düyek', meter:'8/8', bpm:120, icon:'◐',
    desc:'Pop arabesque classic — 3+3+2',
    steps:[
      {type:'D',len:1,vel:1},{type:'-',len:1},{type:'k',len:1,vel:0.6},{type:'-',len:1},
      {type:'T',len:1,vel:0.9},{type:'-',len:1},{type:'k',len:1,vel:0.55},{type:'-',len:1},
      {type:'T',len:1,vel:0.8},{type:'k',len:1,vel:0.5},{type:'D',len:1,vel:0.95},{type:'-',len:1},
    ],
    resolution:8, stepSec:0.25
  },
  {
    id:'curcuna', name:'Curcuna', meter:'10/8', bpm:150, icon:'◑',
    desc:'Fast folk — 3+3+2+2',
    steps:[
      {type:'D',len:1,vel:1},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.85},{type:'k',len:1,vel:0.5},
      {type:'D',len:1,vel:0.95},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.85},{type:'k',len:1,vel:0.5},
      {type:'T',len:1,vel:0.7},{type:'k',len:1,vel:0.5},
    ],
    resolution:8, stepSec:0.20
  },
  {
    id:'karsilama', name:'Karşılama', meter:'9/8', bpm:155, icon:'◎',
    desc:'Wedding 9/8 — 2+2+2+3',
    steps:[
      {type:'D',len:1,vel:1},{type:'-',len:1},{type:'k',len:1,vel:0.6},{type:'T',len:1,vel:0.85},{type:'-',len:1},
      {type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.8},{type:'-',len:1},{type:'k',len:1,vel:0.5},{type:'-',len:1},{type:'D',len:1,vel:0.9},
    ],
    resolution:8, stepSec:0.193
  },
  {
    id:'roman', name:'Roman 9/8', meter:'9/8', bpm:160, icon:'▣',
    desc:'Turkish Romani gypsy',
    steps:[
      {type:'D',len:1,vel:1},{type:'T',len:1,vel:0.85},{type:'k',len:1,vel:0.6},{type:'T',len:1,vel:0.8},{type:'k',len:1,vel:0.5},
      {type:'D',len:1,vel:0.92},{type:'-',len:1},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.75},{type:'-',len:1},
    ],
    resolution:8, stepSec:0.187
  },
  {
    id:'sofyan', name:'Aksak / Sofyan', meter:'7/8', bpm:132, icon:'⬔',
    desc:'Limping 7 — 3+2+2',
    steps:[
      {type:'D',len:1,vel:1},{type:'-',len:1},{type:'k',len:1,vel:0.55},{type:'-',len:1},
      {type:'T',len:1,vel:0.85},{type:'-',len:1},{type:'k',len:1,vel:0.55},{type:'D',len:1,vel:0.9},
    ],
    resolution:8, stepSec:0.227
  },
  {
    id:'ciftetelli', name:'Çiftetelli', meter:'8/4', bpm:92, icon:'⬣',
    desc:'Belly dance slow 8',
    steps:[
      {type:'D',len:1,vel:1},{type:'k',len:1,vel:0.6},{type:'-',len:1},{type:'-',len:1},
      {type:'T',len:1,vel:0.85},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.75},{type:'k',len:1,vel:0.5},
      {type:'D',len:1,vel:0.92},{type:'-',len:1},{type:'T',len:1,vel:0.8},{type:'k',len:1,vel:0.5},
    ],
    resolution:8, stepSec:0.326
  },
  {
    id:'halay', name:'Halay / Dabke', meter:'4/4', bpm:122, icon:'⬢',
    desc:'Line dance Anatolian',
    steps:[
      {type:'D',len:1,vel:1},{type:'-',len:1},{type:'-',len:1},{type:'T',len:1,vel:0.85},{type:'-',len:1},{type:'-',len:1},
      {type:'D',len:1,vel:0.92},{type:'-',len:1},
    ],
    resolution:4, stepSec:0.245
  },
  {
    id:'zeybek', name:'Zeybek', meter:'9/4', bpm:78, icon:'⬔',
    desc:'Aegean eagle — slow heavy 9',
    steps:[
      {type:'D',len:1,vel:1},{type:'-',len:1},{type:'-',len:1},{type:'-',len:1},{type:'-',len:1},{type:'-',len:1},
      {type:'T',len:1,vel:0.8},{type:'-',len:1},{type:'k',len:1,vel:0.5},{type:'-',len:1},
    ],
    resolution:4, stepSec:0.384
  },
  {
    id:'horon', name:'Horon', meter:'7/16', bpm:176, icon:'◆',
    desc:'Black Sea tight 7/16',
    steps:[
      {type:'D',len:1,vel:1},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.85},{type:'k',len:1,vel:0.5},
      {type:'D',len:1,vel:0.9},{type:'k',len:1,vel:0.5},{type:'T',len:1,vel:0.8},
    ],
    resolution:8, stepSec:0.17
  },
  {
    id:'nimsofyan', name:'Nim Sofyan', meter:'6/8', bpm:110, icon:'⬣',
    desc:'Light 6/8 folk waltz',
    steps:[
      {type:'D',len:1,vel:1},{type:'k',len:1,vel:0.55},{type:'T',len:1,vel:0.8},{type:'-',len:1},
      {type:'D',len:1,vel:0.9},{type:'k',len:1,vel:0.55},{type:'T',len:1,vel:0.75},{type:'-',len:1},
    ],
    resolution:8, stepSec:0.272
  },
];

export function getRhythm(id){ return RHYTHMS.find(r=>r.id===id) || RHYTHMS[0]; }

// Map meter string to UI badge
export function meterColor(m){
  if(m.includes('9/8')) return '#e6c66a';
  if(m.includes('7/8')||m.includes('7/16')) return '#ff8c2e';
  if(m.includes('10/8')) return '#2ec4b6';
  if(m.includes('8/8')||m.includes('8/4')) return '#7ad3ff';
  return '#a8a6b0';
}
