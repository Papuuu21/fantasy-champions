import json
import random
import threading
import webbrowser
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ─────────────────────────────────────────────────────────
#  FANTASY CHAMPIONS · SORTEOS (grupos, enfrentamientos, calendario)
#  Ejecuta este script y se abrirá el navegador solo.
# ─────────────────────────────────────────────────────────

PARTICIPANTES = ["Palop", "Fale", "Lope", "Tony", "Ruso", "Kero","Coquina", "Papu", "Kike", "Gonzo", "Puche", "Armada"]

JORNADAS_LIGA = list(range(8, 18))   # J1 Champions = J8 Liga ... J10 = J17
PUERTO = 8000

rng = random.SystemRandom()
ESTADO = {"grupos": None, "numeros": None, "calendario": None}
ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sorteo_fantasy.json")

def guardar():
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(ESTADO, f, ensure_ascii=False, indent=2)


def cargar():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            ESTADO.update(json.load(f))

def berger(p):
    """Rondas de una liga a una vuelta entre 6 (método del círculo)."""
    n = len(p)
    rondas = []
    for r in range(n - 1):
        a, b = p[n - 1], p[r]
        partidos = [(a, b) if r % 2 == 0 else (b, a)]
        for i in range(1, n // 2):
            partidos.append((p[(r + i) % (n - 1)], p[(r - i) % (n - 1)]))
        rondas.append(partidos)
    return rondas


def sortear_grupos():
    nombres = PARTICIPANTES[:]
    rng.shuffle(nombres)
    bolas = ["A"] * 6 + ["B"] * 6
    rng.shuffle(bolas)
    pasos = [{"nombre": n, "grupo": g} for n, g in zip(nombres, bolas)]
    grupos = {"A": [], "B": []}
    for p in pasos:
        grupos[p["grupo"]].append(p["nombre"])
    ESTADO.update(grupos=grupos, numeros=None, calendario=None)
    return {"participantes": PARTICIPANTES, "pasos": pasos, "grupos": grupos}


def sortear_numeros():
    grupos = ESTADO["grupos"]
    if not grupos:
        raise ValueError("Primero hay que sortear los grupos")
    pasos, orden, enf = {}, {}, {}
    for k in "AB":
        nombres = grupos[k][:]
        rng.shuffle(nombres)
        nums = list(range(1, 7))
        rng.shuffle(nums)
        pasos[k] = [{"nombre": n, "numero": m} for n, m in zip(nombres, nums)]
        o = [None] * 6
        for p in pasos[k]:
            o[p["numero"] - 1] = p["nombre"]
        orden[k] = o
        enf[k] = [[o[i], o[j]] for i in range(6) for j in range(i + 1, 6)]
    ESTADO["numeros"] = {"orden": orden, "enfrentamientos": enf}
    ESTADO["calendario"] = None
    return {"grupos": grupos, "pasos": pasos, "enfrentamientos": enf}


def sortear_calendario():
    if not ESTADO["numeros"]:
        raise ValueError("Primero hay que sortear los enfrentamientos")
    rondas = {k: berger(ESTADO["numeros"]["orden"][k]) for k in "AB"}
    ordenes = {k: {"ida": rng.sample(range(5), 5), "vuelta": rng.sample(range(5), 5)}
                for k in "AB"}
    cal = []
    for j in range(10):
        fase = "ida" if j < 5 else "vuelta"
        fila = {"cl": j + 1, "liga": JORNADAS_LIGA[j], "fase": fase}
        for k in "AB":
            r = ordenes[k][fase][j % 5]
            partidos = [list(p) for p in rondas[k][r]]
            if fase == "vuelta":
                partidos = [[v, l] for l, v in partidos]
            fila[k] = {"bola": ("I" if fase == "ida" else "V") + str(r + 1),
                        "partidos": partidos}
        cal.append(fila)
    ESTADO["calendario"] = cal
    return {"calendario": cal}


PAGINA = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fantasy Champions · Sorteos</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',Arial,sans-serif;color:#fff;min-height:100vh;
background:radial-gradient(circle at 50% 0,#14327a 0,#071230 55%,#030814 100%)}
header{text-align:center;padding:14px 10px 4px}
h1{margin:0;font-size:26px;letter-spacing:3px;color:#f5c518;text-shadow:0 0 18px #f5c51866}
#pills{margin-top:10px}
.pill{display:inline-block;margin:0 4px;padding:6px 16px;border-radius:20px;background:#ffffff14;
border:1px solid #ffffff30;cursor:pointer;font-size:14px}
.pill.active{background:#f5c518;color:#111;font-weight:700}
.pill.done:not(.active){border-color:#27ae60;color:#7dffb0}
main{display:flex;flex-wrap:wrap;gap:18px;padding:12px 18px;justify-content:center;align-items:flex-start}
#stage{flex:0 0 auto;width:100%;max-width:800px;text-align:center}
#caption{font-size:28px;font-weight:800;min-height:38px;color:#fff;text-shadow:0 2px 10px #000}
#sub{font-size:15px;color:#9fb3e8;min-height:22px;margin-bottom:6px}
canvas{width:100%;max-width:800px;height:auto;border-radius:16px;border:2px solid #ffffff25;
box-shadow:0 10px 40px #000a}
button{font-size:18px;font-weight:800;border:0;border-radius:30px;padding:14px 34px;margin:14px 6px 0;
cursor:pointer;color:#111;background:linear-gradient(#ffd84d,#f2a900);box-shadow:0 0 22px #f5c51888;
animation:pulso 1.6s infinite}
button#reset{font-size:12px;padding:6px 14px;background:#ffffff18;color:#ccc;box-shadow:none;animation:none}
@keyframes pulso{50%{transform:scale(1.05)}}
#panel{flex:1 1 380px;max-width:640px;max-height:640px;overflow:auto;padding-right:4px}
.res{display:none}
.cols{display:flex;gap:12px;flex-wrap:wrap}
.card{flex:1 1 220px;border-radius:12px;padding:10px 14px;background:#ffffff0f;border-top:4px solid #888}
.card.A{border-color:#2f80ed}.card.B{border-color:#eb5757}
.card h3{margin:2px 0 8px;letter-spacing:2px}.card h4{margin:12px 0 4px;color:#f5c518;font-size:13px}
.slot{padding:6px 8px;margin:3px 0;border-radius:6px;background:#ffffff12;font-size:15px}
.slot.empty{opacity:.35}.slot.new{background:#27ae60;animation:pop .8s}
.vs{font-size:13px;padding:2px 6px;color:#cfd9f5}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f5c51822;color:#f5c518;padding:6px}
td{padding:5px 8px;border-bottom:1px solid #ffffff18;vertical-align:top}
tr.sep td{background:#ffffff14;text-align:center;font-weight:700;letter-spacing:2px;color:#f5c518}
tr.ida td:first-child{border-left:4px solid #2f80ed}tr.vuelta td:first-child{border-left:4px solid #f2994a}
tr.new td{background:#27ae6044}
.dim{color:#7f8fb8}
@keyframes pop{0%{transform:scale(1.15)}100%{transform:scale(1)}}
</style></head><body>
<header><h1>🏆 FANTASY CHAMPIONS LEAGUE</h1>
<div id="pills">
<span class="pill" data-t="1">① Grupos</span>
<span class="pill" data-t="2">② Enfrentamientos</span>
<span class="pill" data-t="3">③ Calendario</span></div></header>
<main>
<section id="stage">
<div id="caption">Bienvenidos al sorteo</div><div id="sub">Pulsa el botón para comenzar</div>
<canvas id="cv" width="800" height="460"></canvas><br>
<button id="go">▶ COMENZAR</button><button id="reset">↺ Reiniciar todo</button>
</section>
<section id="panel"><div class="res" id="r1"></div><div class="res" id="r2"></div><div class="res" id="r3"></div></section>
</main>
<script>
const $=s=>document.querySelector(s);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
const COL={A:'#2f80ed',B:'#eb5757',gold:'#f5c518',ida:'#2f80ed',vuelta:'#f2994a'};
const cv=$('#cv'),ctx=cv.getContext('2d'),W=800,H=460,R=135,DY=190,TY=405;
let drums=[],conf=[],ST={f1:false,f2:false,f3:false},busy=false;

/* ───────── utilidades ───────── */
const say=(t,s='')=>{$('#caption').textContent=t;$('#sub').textContent=s;};
const post=async u=>{const r=await fetch(u,{method:'POST'});const j=await r.json();
  if(!r.ok)throw new Error(j.error||'Error');return j;};
function anim(ms,fn){return new Promise(res=>{const t0=performance.now();
  (function f(now){const t=Math.min(1,(now-t0)/ms);fn(t);t<1?requestAnimationFrame(f):res();})(t0);});}
function confeti(n){for(let i=0;i<n;i++)conf.push({x:W/2+(Math.random()-.5)*300,y:H/2,
  vx:(Math.random()-.5)*700,vy:-Math.random()*650-100,c:`hsl(${Math.random()*360},90%,60%)`,
  s:4+Math.random()*5,rot:Math.random()*6,life:3});}

/* ───────── bombos y bolas ───────── */
function makeDrum(x,title,items){
  const d={x,y:DY,R,title,rot:0,mixing:false,balls:[]};
  const br=items.length>8?26:(items.length>4?30:34);
  items.forEach(it=>{const a=Math.random()*6.28,rr=Math.random()*(R-br-12);
    d.balls.push({label:it.label,color:it.color,tc:it.tc||'#111',x:x+Math.cos(a)*rr,
      y:DY+Math.sin(a)*rr+20,vx:(Math.random()-.5)*100,vy:0,r:br,out:false,dead:false,hide:false,a:1});});
  return d;
}
function physics(dt){
  for(const d of drums){
    d.rot+=(d.mixing?7:.4)*dt;
    const bs=d.balls.filter(b=>!b.out&&!b.dead);
    for(const b of bs){
      if(d.mixing){const dx=b.x-d.x,dy=b.y-d.y;
        b.vx+=(-dy*6+(Math.random()-.5)*4500)*dt;
        b.vy+=(dx*6+(Math.random()-.5)*4500-500)*dt;
      }else{b.vy+=900*dt;b.vx*=(1-.6*dt);}
      const sp=Math.hypot(b.vx,b.vy),mx=d.mixing?680:900;
      if(sp>mx){b.vx*=mx/sp;b.vy*=mx/sp;}
      b.x+=b.vx*dt;b.y+=b.vy*dt;
      const dx=b.x-d.x,dy=b.y-d.y,dist=Math.hypot(dx,dy),lim=d.R-b.r-4;
      if(dist>lim){const nx=dx/dist,ny=dy/dist;b.x=d.x+nx*lim;b.y=d.y+ny*lim;
        const vn=b.vx*nx+b.vy*ny;if(vn>0){b.vx-=1.7*vn*nx;b.vy-=1.7*vn*ny;}}
    }
    for(let i=0;i<bs.length;i++)for(let j=i+1;j<bs.length;j++){
      const a=bs[i],b=bs[j];const dx=b.x-a.x,dy=b.y-a.y,dist=Math.hypot(dx,dy)||.01,min=a.r+b.r;
      if(dist<min){const nx=dx/dist,ny=dy/dist,ov=(min-dist)/2;
        a.x-=nx*ov;a.y-=ny*ov;b.x+=nx*ov;b.y+=ny*ov;
        const rel=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;
        if(rel<0){const imp=-rel*.9;a.vx-=imp*nx;a.vy-=imp*ny;b.vx+=imp*nx;b.vy+=imp*ny;}}
    }
  }
  conf.forEach(p=>{p.vy+=700*dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.rot+=dt*8;p.life-=dt;});
  conf=conf.filter(p=>p.life>0&&p.y<H+20);
}
function drawDrum(d){
  ctx.save();
  ctx.beginPath();ctx.arc(d.x,TY,50,0,7);ctx.setLineDash([6,6]);
  ctx.strokeStyle='rgba(245,197,24,.4)';ctx.lineWidth=2;ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#1b2a52';ctx.fillRect(d.x-26,d.y+d.R-2,52,42);
  ctx.strokeStyle='#8fa6d8';ctx.lineWidth=3;ctx.strokeRect(d.x-26,d.y+d.R-2,52,42);
  const g=ctx.createRadialGradient(d.x-40,d.y-40,20,d.x,d.y,d.R);
  g.addColorStop(0,'rgba(255,255,255,.2)');g.addColorStop(1,'rgba(120,160,255,.07)');
  ctx.beginPath();ctx.arc(d.x,d.y,d.R,0,7);ctx.fillStyle=g;ctx.fill();
  ctx.lineWidth=8;ctx.strokeStyle='#c9d6f5';ctx.stroke();
  ctx.translate(d.x,d.y);ctx.rotate(d.rot);ctx.strokeStyle='rgba(201,214,245,.3)';ctx.lineWidth=2;
  for(let i=0;i<8;i++){ctx.rotate(Math.PI/4);ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(d.R-4,0);ctx.stroke();}
  ctx.restore();
  ctx.fillStyle='#f5c518';ctx.font='bold 15px Segoe UI,sans-serif';ctx.textAlign='center';
  ctx.fillText(d.title,d.x,d.y-d.R-16);
}
function drawBall(b){
  if(b.dead)return;
  ctx.save();ctx.globalAlpha=b.a;
  ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,7);ctx.fillStyle=b.color;ctx.fill();
  const g=ctx.createRadialGradient(b.x-b.r*.4,b.y-b.r*.4,b.r*.1,b.x,b.y,b.r);
  g.addColorStop(0,'rgba(255,255,255,.75)');g.addColorStop(.45,'rgba(255,255,255,0)');
  g.addColorStop(1,'rgba(0,0,0,.4)');ctx.fillStyle=g;ctx.fill();
  const t=b.hide?'?':b.label;let fs=b.r*.7;ctx.font=`bold ${fs}px Segoe UI,sans-serif`;
  while(ctx.measureText(t).width>b.r*1.7&&fs>6){fs--;ctx.font=`bold ${fs}px Segoe UI,sans-serif`;}
  ctx.fillStyle=b.tc;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(t,b.x,b.y+1);
  ctx.restore();
}
function draw(){
  const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#10285a');g.addColorStop(1,'#060d24');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  if(!drums.length){ctx.font='150px serif';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillStyle='#fff';ctx.fillText('🏆',W/2,H/2);}
  drums.forEach(drawDrum);
  drums.forEach(d=>d.balls.filter(b=>!b.out).forEach(drawBall));
  drums.forEach(d=>d.balls.filter(b=>b.out).forEach(drawBall));
  conf.forEach(p=>{ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.rot);ctx.fillStyle=p.c;
    ctx.fillRect(-p.s/2,-p.s/2,p.s,p.s*.6);ctx.restore();});
}
let last=performance.now();
(function loop(now){const dt=Math.min(.033,(now-last)/1000);last=now;physics(dt);draw();
  requestAnimationFrame(loop);})(last);

/* ───────── acciones del bombo ───────── */
async function mezclar(d,ms){drums.forEach(x=>x.mixing=false);d.mixing=true;await sleep(ms);}
async function extraer(d,label){
  const c=d.balls.filter(b=>!b.out&&!b.dead&&b.label===label);
  const b=c[Math.floor(Math.random()*c.length)];
  d.mixing=false;b.out=true;b.hide=true;
  const sx=b.x,sy=b.y,r0=b.r,ex=d.x,ey=d.y+d.R-r0-6;
  await anim(700,t=>{const e=ease(t);b.x=sx+(ex-sx)*e;b.y=sy+(ey-sy)*e;});
  await anim(1000,t=>{const e=1-Math.pow(1-t,3);b.y=ey+(TY-ey)*e;b.r=r0+(44-r0)*e;});
  return b;
}
async function sacar(d,label,tit,sub){
  say(tit,sub);await mezclar(d,1900);
  const b=await extraer(d,label);
  say('Y la bola es…',sub);await sleep(1300);
  b.hide=false;await anim(500,t=>{b.r=44+12*Math.sin(Math.PI*t);});b.r=44;
  return b;
}
async function retirar(b){await anim(400,t=>{b.a=1-t;});b.dead=true;}

/* ───────── paneles de resultados ───────── */
function renderGrupos(gr,nuevo){
  let h='<div class="cols">';
  for(const k of ['A','B']){h+=`<div class="card ${k}"><h3>GRUPO ${k}</h3>`;
    for(let i=0;i<6;i++){const n=gr[k][i];
      h+=n?`<div class="slot ${n===nuevo?'new':''}">${i+1}. ${n}</div>`:`<div class="slot empty">${i+1}. ···</div>`;}
    h+='</div>';}
  $('#r1').innerHTML=h+'</div>';
}
function renderNums(nums,enf,nuevo){
  let h='<div class="cols">';
  for(const k of ['A','B']){h+=`<div class="card ${k}"><h3>GRUPO ${k}</h3>`;
    for(let i=0;i<6;i++){const n=nums[k][i];
      h+=`<div class="slot ${n?'':'empty'} ${n&&n===nuevo?'new':''}"><b>Nº ${i+1}</b> &nbsp;${n||'···'}</div>`;}
    if(enf[k].length){h+='<h4>ENFRENTAMIENTOS (IDA Y VUELTA)</h4>';
      enf[k].forEach(p=>h+=`<div class="vs">${p[0]} ⇄ ${p[1]}</div>`);}
    h+='</div>';}
  $('#r2').innerHTML=h+'</div>';
}
function renderCal(rows,nuevo){
  let h='<table><tr><th>Champions</th><th>Liga</th><th>Grupo A</th><th>Grupo B</th></tr>';
  rows.forEach((f,i)=>{
    if(i===0||i===5)h+=`<tr class="sep"><td colspan="4">${i?'FASE DE VUELTA':'FASE DE IDA'}</td></tr>`;
    const cell=k=>f[k]?f[k].partidos.map(p=>`<div>${p[0]} – ${p[1]}</div>`).join(''):'<span class="dim">· · ·</span>';
    h+=`<tr class="${f.fase} ${i===nuevo?'new':''}"><td><b>J${f.cl}</b></td><td>Liga J${f.liga}</td><td>${cell('A')}</td><td>${cell('B')}</td></tr>`;});
  $('#r3').innerHTML=h+'</table><p class="dim">Formato: Local – Visitante</p>';
  const n=$('#r3 .new');if(n)n.scrollIntoView({block:'nearest',behavior:'smooth'});
}
function showTab(n){[1,2,3].forEach(i=>{$('#r'+i).style.display=i===n?'block':'none';
  document.querySelector(`.pill[data-t="${i}"]`).classList.toggle('active',i===n);});}
function refreshUI(){
  const next=!ST.f1?1:!ST.f2?2:!ST.f3?3:0;
  $('#go').style.display=(next&&!busy)?'inline-block':'none';
  if(next)$('#go').textContent='▶ COMENZAR SORTEO DE '+['','GRUPOS','ENFRENTAMIENTOS','CALENDARIO'][next];
  document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('done',ST['f'+p.dataset.t]));
}

/* ───────── SORTEO 1: GRUPOS ───────── */
async function fase1(){
  const r=await post('/api/sorteo/1');const gr={A:[],B:[]};renderGrupos(gr);
  drums=[makeDrum(210,'PARTICIPANTES',r.participantes.map(n=>({label:n,color:COL.gold,tc:'#111'}))),
    makeDrum(590,'GRUPOS',['A','A','A','A','A','A','B','B','B','B','B','B'].map(g=>({label:g,color:COL[g],tc:'#fff'})))];
  say('¡Bienvenidos al sorteo de la fase de grupos!','12 participantes · 2 grupos de 6 · pasan los 4 primeros');
  await sleep(3500);
  for(let i=0;i<r.pasos.length;i++){const p=r.pasos[i];
    const b1=await sacar(drums[0],p.nombre,'Se remueve el bombo de participantes…',`Bola ${i+1} de 12`);
    say(p.nombre.toUpperCase(),'¿En qué grupo jugará?');await sleep(1500);
    const b2=await sacar(drums[1],p.grupo,'Se remueve el bombo de grupos…',p.nombre);
    say(`${p.nombre} → GRUPO ${p.grupo}`,`Bola ${i+1} de 12`);
    gr[p.grupo].push(p.nombre);renderGrupos(gr,p.nombre);confeti(40);
    await sleep(2200);await Promise.all([retirar(b1),retirar(b2)]);}
  drums=[];say('¡SORTEO DE GRUPOS COMPLETADO!','Ya puedes pasar al sorteo de enfrentamientos');confeti(250);
}

/* ───────── SORTEO 2: ENFRENTAMIENTOS ───────── */
async function fase2(){
  const r=await post('/api/sorteo/2');
  const nums={A:Array(6).fill(null),B:Array(6).fill(null)},enf={A:[],B:[]};renderNums(nums,enf);
  say('SORTEO DE ENFRENTAMIENTOS','Cada jugador saca su número en el grupo: ese número fija sus rivales y su campo');
  await sleep(4500);
  for(const k of ['A','B']){
    drums=[makeDrum(210,`GRUPO ${k} · JUGADORES`,r.grupos[k].map(n=>({label:n,color:COL[k],tc:'#fff'}))),
      makeDrum(590,'NÚMEROS',[1,2,3,4,5,6].map(n=>({label:String(n),color:COL.gold,tc:'#111'})))];
    say(`GRUPO ${k}`,'Comienza el sorteo de este grupo');await sleep(2200);
    for(const p of r.pasos[k]){
      const b1=await sacar(drums[0],p.nombre,'Se remueve el bombo de jugadores…',`Grupo ${k}`);
      say(p.nombre.toUpperCase(),'¿Qué número tendrá?');await sleep(1400);
      const b2=await sacar(drums[1],String(p.numero),'Se remueve el bombo de números…',p.nombre);
      say(`${p.nombre} será el nº ${p.numero}`,`Grupo ${k}`);
      nums[k][p.numero-1]=p.nombre;renderNums(nums,enf,p.nombre);confeti(40);
      await sleep(2000);await Promise.all([retirar(b1),retirar(b2)]);}
  }
  drums=[];say('Números definidos…','Se desvelan los enfrentamientos (todos a ida y vuelta)');await sleep(2500);
  for(let i=0;i<15;i++)for(const k of ['A','B']){enf[k].push(r.enfrentamientos[k][i]);renderNums(nums,enf);await sleep(150);}
  say('¡ENFRENTAMIENTOS DEFINIDOS!','Ya puedes pasar al sorteo del calendario');confeti(250);
}

/* ───────── SORTEO 3: CALENDARIO ───────── */
async function fase3(){
  const r=await post('/api/sorteo/3'),cal=r.calendario;
  const rows=cal.map(f=>({cl:f.cl,liga:f.liga,fase:f.fase,A:null,B:null}));renderCal(rows,-1);
  say('SORTEO DEL CALENDARIO','La jornada 1 de Champions es la jornada 8 de Liga · primero ida, luego vuelta');
  await sleep(5000);
  for(let i=0;i<cal.length;i++){const f=cal[i],ida=f.fase==='ida';
    if(i===0||i===5){
      drums=['A','B'].map((k,j)=>makeDrum(j?590:210,`GRUPO ${k} · ${ida?'IDA':'VUELTA'}`,
        [1,2,3,4,5].map(n=>({label:(ida?'I':'V')+n,color:ida?COL.ida:COL.vuelta,tc:'#fff'}))));
      say(ida?'FASE DE IDA':'FASE DE VUELTA',ida?'Jornadas 1 a 5':'Jornadas 6 a 10');await sleep(2500);}
    const tit=`JORNADA ${f.cl} · LIGA J${f.liga}`,bs=[];
    for(let j=0;j<2;j++){const k=['A','B'][j];
      const b=await sacar(drums[j],f[k].bola,tit,`Sorteo del grupo ${k}`);
      rows[i][k]=f[k];renderCal(rows,i);bs.push(b);confeti(30);await sleep(1200);}
    await sleep(1200);await Promise.all(bs.map(retirar));}
  drums=[];say('¡CALENDARIO COMPLETO!','¡Que gane el mejor!');confeti(300);
}

/* ───────── control ───────── */
$('#go').onclick=async()=>{
  if(busy)return;busy=true;const n=!ST.f1?1:!ST.f2?2:3;refreshUI();showTab(n);
  try{await [null,fase1,fase2,fase3][n]();ST['f'+n]=true;}catch(e){say('Error',String(e));}
  busy=false;refreshUI();};
$('#reset').onclick=async()=>{if(busy||!confirm('¿Borrar todos los sorteos y empezar de cero?'))return;
  await post('/api/reset');location.reload();};
document.querySelectorAll('.pill').forEach(p=>p.onclick=()=>{
  const n=+p.dataset.t;if(ST['f'+n]||busy)showTab(n);});
(async()=>{
  const e=await (await fetch('/api/estado')).json();
  if(e.grupos){ST.f1=true;renderGrupos(e.grupos);}
  if(e.numeros){ST.f2=true;renderNums(e.numeros.orden,e.numeros.enfrentamientos);}
  if(e.calendario){ST.f3=true;renderCal(e.calendario,-1);}
  if(!ST.f1)drums=[makeDrum(400,'PARTICIPANTES',e.participantes.map(n=>({label:n,color:COL.gold,tc:'#111'})))];
  showTab(ST.f3?3:ST.f2?2:1);
  say(ST.f3?'¡Todos los sorteos completados!':'Bienvenidos al sorteo',
      ST.f3?'Revisa las pestañas de arriba':'Pulsa el botón para comenzar');
  refreshUI();
})();
</script></body></html>
"""


class Manejador(BaseHTTPRequestHandler):
    def _enviar(self, cuerpo, tipo="application/json", codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, obj, codigo=200):
        self._enviar(json.dumps(obj).encode("utf-8"), codigo=codigo)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._enviar(PAGINA.encode("utf-8"), "text/html")
        elif self.path == "/api/estado":
            self._json({**ESTADO, "participantes": PARTICIPANTES})
        else:
            self._json({"error": "No encontrado"}, 404)

    def do_POST(self):
        try:
            if self.path == "/api/sorteo/1":
                r = sortear_grupos()
            elif self.path == "/api/sorteo/2":
                r = sortear_numeros()
            elif self.path == "/api/sorteo/3":
                r = sortear_calendario()
            elif self.path == "/api/reset":
                ESTADO.update(grupos=None, numeros=None, calendario=None)
                r = {"ok": True}
            else:
                self._json({"error": "No encontrado"}, 404)
                return
            guardar()
            self._json(r)
        except ValueError as e:
            self._json({"error": str(e)}, 400)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    cargar()
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    url = f"http://localhost:{PUERTO}"
    print(f"\n🏆 Sorteo listo en {url}  (Ctrl+C para cerrar)\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")