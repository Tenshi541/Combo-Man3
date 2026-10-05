'use strict';
const $ = id => document.getElementById(id);
const overlay = location.pathname === '/overlay';
if (overlay) document.body.classList.add('overlay');
let packet = {time:0, devices:[], active:{}, events:[]}, events = [], selected = '', frozen = null, clearedAt = 0;
let config;
try { config = JSON.parse(localStorage.getItem('combo-config') || '{}'); } catch { config = {}; }
$('fps').value = config.fps || 60; $('window').value = config.window || 120;
const params = new URLSearchParams(location.search);
if(params.has('fps')) $('fps').value = params.get('fps');
if(params.has('device')) selected = params.get('device');
function number(id, fallback, min, max){const v=Number($(id).value);return Number.isFinite(v)?Math.max(min,Math.min(max,v)):fallback;}
const fps = () => number('fps',60,1,360);
const windowFrames = () => number('window',120,30,600);
const device = () => packet.devices.find(d => String(d.id) === selected);
function labels(){try{return JSON.parse(localStorage.getItem('combo-labels-'+(device()?.guid || 'unknown')) || '{}');}catch{return {};}}
function label(control){return labels()[control] || control;}
function saveConfig(){localStorage.setItem('combo-config', JSON.stringify({fps:fps(),window:windowFrames()}));updateOverlay();render();}
function updateOverlay(){$('overlay').href = `/overlay?fps=${fps()}&device=${encodeURIComponent(selected)}`;}
$('fps').onchange = saveConfig; $('window').onchange = saveConfig;
$('device').onchange = () => { selected=$('device').value; frozen=null; $('pause').textContent='Freeze view'; buildMapping();updateOverlay();render(); };
$('pause').onclick = () => {frozen=frozen?null:JSON.parse(JSON.stringify({packet,events}));$('pause').textContent=frozen?'Resume view':'Freeze view';render();};
$('clear').onclick=()=>{events=[];clearedAt=packet.sequence || 0;frozen=null;$('pause').textContent='Freeze view';render();};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({version:1,fps:fps(),timing:'collector clock; not game synchronized',device:device(),labels:labels(),events:events.filter(e=>String(e.device)===selected)},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='combo-man3-session.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function buildMapping(){const root=$('mapping');root.replaceChildren();const d=device();if(!d)return;const saved=labels();for(let i=0;i<d.buttons;i++){const control='B'+i;const wrap=document.createElement('label');wrap.append(control);const input=document.createElement('input');input.value=saved[control]||'';input.placeholder=control;input.maxLength=24;input.onchange=()=>{saved[control]=input.value.trim();localStorage.setItem('combo-labels-'+d.guid,JSON.stringify(saved));render();};wrap.append(input);root.append(wrap);}}
const source = new EventSource('/events');
source.onopen = () => {$('connection').textContent='● CAPTURE LIVE';};
source.onerror = () => {$('connection').textContent='● Reconnecting to collector…';};
source.onmessage = event => {
  const next=JSON.parse(event.data);
  if(next.sequence < (packet.sequence || 0)){events=[];clearedAt=0;frozen=null;}
  const last=events.at(-1)?.seq || clearedAt;
  events.push(...next.events.filter(e=>e.seq>last));
  if(events.length>20000)events.splice(0,events.length-20000);
  const signature=JSON.stringify(next.devices.map(d=>[d.id,d.guid,d.buttons,d.hats,d.axes.length]));
  const old=JSON.stringify(packet.devices.map(d=>[d.id,d.guid,d.buttons,d.hats,d.axes.length]));
  packet=next;
  if(signature!==old){
    if(!packet.devices.some(d=>String(d.id)===selected))selected=String(packet.devices[0]?.id ?? '');
    $('device').replaceChildren();
    for(const d of packet.devices){const o=document.createElement('option');o.value=String(d.id);o.textContent=d.name+' · '+d.id;$('device').append(o);}
    if(!packet.devices.length){const o=document.createElement('option');o.textContent='Plug in a controller';o.value='';$('device').append(o);}
    $('device').value=selected;buildMapping();updateOverlay();
  }
  if(!frozen)render();
};
function render(){
  const state=frozen || {packet,events};const p=state.packet;const d=p.devices.find(x=>String(x.id)===selected);
  const active=p.active[selected]||[];const history=state.events.filter(e=>String(e.device)===selected);
  $('clock').textContent='FRAME '+Math.floor(p.time*fps());$('empty').hidden=Boolean(d);
  $('sample').textContent=d?.guid==='demo'?'DEMO INPUTS · no hardware connected':'Timestamped input observations · bounded history';
  $('buttons').replaceChildren();
  const controls=d?Array.from({length:d.buttons},(_,i)=>'B'+i):[];
  for(const control of active)if(!controls.includes(control))controls.push(control);
  for(const control of controls){const node=document.createElement('div');node.className='button'+(active.includes(control)?' active':'');node.textContent=label(control);$('buttons').append(node);}
  $('axes').textContent=d?d.axes.map((v,i)=>`Axis ${i}: ${v.toFixed(2)}`).join('   '):'';
  $('history').replaceChildren();
  for(const e of history.slice(-30).reverse()){
    const row=document.createElement('div');row.className='history-row '+(e.down?'down':'up');
    const previous=history.findLast(x=>x.seq<e.seq && x.control===e.control && x.down);
    const duration=!e.down&&previous?Math.floor(e.time*fps())-Math.floor(previous.time*fps()):null;
    for(const value of [Math.floor(e.time*fps()),label(e.control),e.down?'PRESS':'RELEASE',duration===null?'':duration+' frames']){const span=document.createElement('span');span.textContent=value;row.append(span);}
    $('history').append(row);
  }
  draw(p,history,controls);
}
function draw(p,history,controls){
  const canvas=$('timeline');const ratio=window.devicePixelRatio||1;const width=canvas.getBoundingClientRect().width;const height=300;
  canvas.width=width*ratio;canvas.height=height*ratio;const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
  const end=Math.floor(p.time*fps()),start=Math.max(0,end-windowFrames()),span=windowFrames(),left=112,right=width-12;
  const x=frame=>left+(frame-start)/span*(right-left);
  ctx.font='11px monospace';ctx.strokeStyle='#28364b';ctx.fillStyle='#8fa5c0';
  const step=span>240?30:span>120?15:10;
  for(let frame=Math.ceil(start/step)*step;frame<=start+span;frame+=step){ctx.beginPath();ctx.moveTo(x(frame),24);ctx.lineTo(x(frame),height);ctx.stroke();ctx.fillText(String(frame),x(frame)+2,14);}
  const lanes=[...new Set([...controls,...history.filter(e=>e.time*fps()>=start).map(e=>e.control)])].slice(0,16);
  const rowHeight=Math.min(30,(height-30)/Math.max(1,lanes.length));
  for(let i=0;i<lanes.length;i++){
    const control=lanes[i],y=30+i*rowHeight;ctx.fillStyle='#bdcce0';ctx.fillText(label(control).slice(0,14),4,y+12);
    let down=null;
    for(const e of history.filter(e=>e.control===control)){
      if(e.down)down=e.time;
      else if(down!==null){bar(down,e.time);down=null;}
    }
    if(down!==null)bar(down,p.time);
    else if((p.active[selected]||[]).includes(control)){ctx.fillStyle='#95ed5877';ctx.fillRect(x(start),y,right-left,rowHeight-4);}
    function bar(a,b){const begin=Math.max(start,Math.floor(a*fps()));const finish=Math.min(end,Math.floor(b*fps()));if(finish<start)return;ctx.fillStyle='#95ed58';ctx.fillRect(x(begin),y,Math.max(2,x(finish)-x(begin)),rowHeight-4);}
  }
  ctx.strokeStyle='#f3f7ff';ctx.beginPath();ctx.moveTo(x(end),22);ctx.lineTo(x(end),height);ctx.stroke();
}
window.addEventListener('resize',render);
updateOverlay();render();
