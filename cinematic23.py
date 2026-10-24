from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text();a=s.index('#splash{');b=s.index('/* Motion polish:',a)
s=s[:a]+'''#splash{
  --intro-purple:#b65bff;--intro-bright:#e9ceff;
  position:fixed;inset:0;z-index:200;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:24px;overflow:hidden;isolation:isolate;
  color:#f4eaff;background:#030105;transition:opacity .5s ease,transform .5s ease;
}
#splash.gone{opacity:0;transform:scale(1.055);pointer-events:none}
.movie-aura{position:absolute;inset:0;z-index:-2;background:radial-gradient(ellipse at 50% 43%,#7423b940 0%,#290a481c 33%,transparent 65%);opacity:0}
.movie-grid{position:absolute;inset:45% -60% -45%;z-index:-1;background-image:linear-gradient(#a855f717 1px,transparent 1px),linear-gradient(90deg,#a855f717 1px,transparent 1px);background-size:54px 54px;transform:perspective(400px) rotateX(63deg) translateY(120px);opacity:0;mask-image:linear-gradient(transparent,#000,transparent);-webkit-mask-image:linear-gradient(transparent,#000,transparent)}
.movie-top{position:absolute;top:calc(env(safe-area-inset-top,0px) + 40px);font-size:9px;letter-spacing:.42em;color:#b59cc9;opacity:0}
.splash-scene{position:relative;width:min(72vw,310px);height:min(72vw,310px);display:flex;align-items:center;justify-content:center;margin-top:-28px}
.splash-svg{width:78%;height:auto;overflow:visible;position:relative;z-index:3}
.movie-halo{position:absolute;width:96%;height:96%;border:1px solid #a855f733;border-radius:50%;opacity:0;transform:scale(.6)}
.movie-orbit{position:absolute;width:112%;height:112%;border:1px solid transparent;border-top-color:#c275ff80;border-bottom-color:#67319660;border-radius:50%;opacity:0;transform:rotate(-70deg) scale(.7)}
.movie-orbit::after{content:'';position:absolute;width:5px;height:5px;border-radius:50%;background:#deb2ff;top:15%;left:14%;box-shadow:0 0 14px #b65bff}
.movie-impact{position:absolute;inset:16%;border:1px solid #c989ff;border-radius:50%;opacity:0;pointer-events:none}
.movie-particles{position:absolute;inset:0;pointer-events:none}
.movie-particles i{position:absolute;top:50%;left:50%;width:3px;height:3px;background:#d6a2ff;box-shadow:0 0 8px #ab45ff;border-radius:50%;opacity:0}
.splash-svg .sp-frame,.splash-svg .sp-stroke,.splash-svg .sp-line{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}
.splash-svg .sp-frame{stroke:#a855f7;stroke-width:1.2;opacity:.65}
.splash-svg .sp-stroke{stroke:#e8c9ff;stroke-width:.8;opacity:.6}
.splash-svg .sp-line{stroke:#b65bff;stroke-width:1.3;opacity:.65}
.splash-svg .sp-fill{fill:url(#introMetal);opacity:0;transform-origin:70px 70px}
.splash-svg .sp-dot{fill:#e1b8ff;opacity:0}
.t-piece{fill:url(#introMetal);opacity:0;transform-box:fill-box;transform-origin:center}
.t-cap-left{--from-x:-170px;--from-y:-80px;--from-turn:-45deg;--arrive:1s}
.t-cap-right{--from-x:170px;--from-y:-80px;--from-turn:45deg;--arrive:1.16s}
.t-stem-top{--from-x:-110px;--from-y:100px;--from-turn:-90deg;--arrive:1.52s}
.t-stem-mid{--from-x:110px;--from-y:130px;--from-turn:90deg;--arrive:1.78s}
.t-stem-base{--from-x:0px;--from-y:190px;--from-turn:180deg;--arrive:2.02s}
#splash.draw .movie-aura{animation:auraAwake 5.7s ease both}
#splash.draw .movie-grid{animation:floorRise 5.7s ease both}
#splash.draw .movie-top{animation:riseIn .9s ease .4s both}
#splash.draw .movie-halo{animation:haloBuild 3.8s ease .3s both}
#splash.draw .movie-orbit{animation:orbitBuild 3.7s cubic-bezier(.25,.6,.25,1) .15s both}
#splash.draw .movie-particles i{animation:fragmentGather 1.35s cubic-bezier(.6,0,.3,1) var(--delay) both}
#splash.draw .t-piece{animation:pieceArrive 1s cubic-bezier(.16,.85,.25,1) var(--arrive) both}
#splash.draw .sp-frame{animation:draw 1.1s ease 2.65s forwards}
#splash.draw .sp-bar{animation:draw .45s ease 2.8s forwards}
#splash.draw .sp-stem{animation:draw .5s ease 3s forwards}
#splash.draw .sp-line{animation:draw .6s ease 3.45s forwards}
#splash.draw .sp-fill{animation:logoSeal .8s ease 2.9s forwards}
#splash.draw .sp-dot{animation:logoSeal .6s ease 3.85s forwards}
#splash.draw .movie-impact{animation:sealWave 1.15s ease-out 3s both}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes pieceArrive{0%{opacity:0;transform:translate(var(--from-x),var(--from-y)) rotate(var(--from-turn)) scale(.4)}20%{opacity:.9}78%{opacity:1;transform:translate(0,-1px) rotate(0) scale(1.02)}100%{opacity:1;transform:none}}
@keyframes fragmentGather{0%{opacity:0;transform:translate(var(--x),var(--y)) scale(.3)}25%{opacity:.8}80%{opacity:.8}100%{opacity:0;transform:translate(0,0) scale(.3)}}
@keyframes auraAwake{0%{opacity:0;transform:scale(.7)}35%{opacity:.6}65%,100%{opacity:1;transform:scale(1)}}
@keyframes floorRise{0%{opacity:0;transform:perspective(400px) rotateX(63deg) translateY(120px)}45%,100%{opacity:.8;transform:perspective(400px) rotateX(63deg) translateY(0)}}
@keyframes haloBuild{0%{opacity:0;transform:scale(.4)}45%{opacity:.9;transform:scale(1)}100%{opacity:.32;transform:scale(1.03)}}
@keyframes orbitBuild{0%{opacity:0;transform:rotate(-100deg) scale(.65)}25%{opacity:.8}70%{opacity:.65}100%{opacity:.18;transform:rotate(160deg) scale(1)}}
@keyframes sealWave{0%{opacity:0;transform:scale(.6)}15%{opacity:.65}100%{opacity:0;transform:scale(2)}}
@keyframes logoSeal{from{opacity:0}to{opacity:1}}
.splash-word{display:flex;gap:.32em;justify-content:center;position:relative;margin-top:-17px;z-index:4}
.splash-word span{font-size:clamp(25px,6.5vw,34px);font-weight:850;letter-spacing:.26em;color:#f4eaff;opacity:0;transform:translateY(14px)}
#splash.draw .splash-word span{animation:titleResolve .7s cubic-bezier(.2,.8,.2,1) both}
#splash.draw .splash-word span:nth-child(1){animation-delay:3.52s}
#splash.draw .splash-word span:nth-child(2){animation-delay:3.62s}
#splash.draw .splash-word span:nth-child(3){animation-delay:3.72s}
#splash.draw .splash-word span:nth-child(4){animation-delay:3.82s}
#splash.draw .splash-word span:nth-child(5){animation-delay:3.92s}
@keyframes titleResolve{from{opacity:0;transform:translateY(14px) scale(.9);filter:blur(4px)}to{opacity:1;transform:none;filter:blur(0)}}
.splash-sub{font-size:10px;letter-spacing:.62em;text-transform:uppercase;color:#ba8fd8;opacity:0;margin-top:-10px;padding-left:.62em;z-index:4}
#splash.draw .splash-sub{animation:riseIn .75s ease 4.15s both}
.movie-caption{position:relative;font-size:9px;letter-spacing:.25em;color:#8b759e;margin-top:2px;opacity:0;text-transform:uppercase}
#splash.draw .movie-caption{animation:riseIn .7s ease 4.5s both}
.splash-shine{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:5}
.splash-shine::after{content:'';position:absolute;top:0;bottom:0;left:-50%;width:40%;background:linear-gradient(105deg,transparent,#bb78ff0b,transparent);opacity:0}
#splash.draw.shine .splash-shine::after{animation:introSweep 1.2s ease both}
@keyframes introSweep{0%{opacity:0;transform:translateX(0)}25%{opacity:1}100%{opacity:0;transform:translateX(400%)}}
.movie-footer{position:absolute;bottom:calc(env(safe-area-inset-bottom,0px) + 26px);width:min(68vw,280px);display:flex;align-items:center;justify-content:space-between;gap:20px}
.movie-progress{height:1px;flex:1;background:#47245b;overflow:hidden}
.movie-progress i{display:block;height:100%;background:#ba6bff;transform:scaleX(0);transform-origin:left}
#splash.draw .movie-progress i{animation:introProgress 5.74s linear forwards}
@keyframes introProgress{to{transform:scaleX(1)}}
.splash-skip{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#c7a8dc;padding:14px 0 14px 14px;white-space:nowrap;min-height:44px}
.splash-skip:focus-visible{outline:1px solid #ba6bff;outline-offset:5px;border-radius:6px}
#splash.gone .movie-footer{display:none}
.no-anim #splash{transition:none}
.no-anim #splash .sp-frame,.no-anim #splash .sp-stroke,.no-anim #splash .sp-line{stroke-dashoffset:0}
.no-anim #splash .sp-fill,.no-anim #splash .sp-dot,.no-anim #splash .movie-aura,.no-anim #splash .splash-word span,.no-anim #splash .splash-sub,.no-anim #splash .movie-caption{opacity:1;transform:none;filter:none}
.no-anim #splash .movie-progress i{transform:scaleX(1)}
.no-anim #splash .movie-particles,.no-anim #splash .t-piece,.no-anim #splash .movie-impact{display:none}
@media(max-height:560px){.splash-scene{width:190px;height:190px;margin-top:0}.movie-top{top:20px}.movie-caption{display:none}#splash{gap:15px}.movie-footer{bottom:8px}}

''' +s[b:]
a=s.index('<div id="splash">');b=s.index('\n<div id="app"',a)
particles=''.join('<i style="--x:%spx;--y:%spx;--delay:%ss"></i>'%(x,y,delay) for x,y,delay in [(-160,-200,.2),(180,-120,.35),(-210,70,.46),(130,190,.6),(-80,210,.3),(220,-30,.7),(-180,-80,.65),(90,-220,.5),(180,130,.3),(-230,-20,.8),(40,240,.7),(-140,180,.55),(230,50,.9),(-20,-250,.72),(150,-200,.84),(-200,140,.95)])
s=s[:a]+'''<div id="splash" role="dialog" aria-label="Trill Inventory startup movie">
  <div class="movie-aura"></div><div class="movie-grid"></div>
  <div class="movie-top" aria-hidden="true">BUILT FOR INVENTORY</div>
  <div class="splash-shine"></div>
  <div class="splash-scene">
    <div class="movie-halo"></div><div class="movie-orbit"></div><div class="movie-impact"></div>
    <div class="movie-particles" aria-hidden="true">'''+particles+'''</div>
    <svg class="splash-svg" viewBox="0 0 140 140" role="img" aria-label="Fragments assemble into the Trill T">
      <defs><linearGradient id="introMetal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#edceff"/><stop offset=".42" stop-color="#bb69ff"/><stop offset="1" stop-color="#7425c5"/></linearGradient></defs>
      <rect class="sp-frame" x="8" y="8" width="124" height="124" rx="30" pathLength="1"/>
      <g aria-hidden="true"><rect class="t-piece t-cap-left" x="42" y="40" width="28" height="15"/><rect class="t-piece t-cap-right" x="70" y="40" width="28" height="15"/><rect class="t-piece t-stem-top" x="60.5" y="55" width="19" height="15"/><rect class="t-piece t-stem-mid" x="60.5" y="70" width="19" height="15"/><rect class="t-piece t-stem-base" x="60.5" y="85" width="19" height="15"/></g>
      <path class="sp-fill" d="M42 40 H98 V55 H79.5 V100 H60.5 V55 H42 Z"/>
      <path class="sp-stroke sp-bar" d="M42 40 H98" pathLength="1"/>
      <path class="sp-stroke sp-stem" d="M79.5 55 V100" pathLength="1"/>
      <path class="sp-line" d="M46 112 H94" pathLength="1"/>
      <circle class="sp-dot" cx="70" cy="112" r="2"/>
    </svg>
  </div>
  <div class="splash-word" aria-label="Trill"><span>T</span><span>R</span><span>I</span><span>L</span><span>L</span></div>
  <div class="splash-sub">Inventory</div>
  <div class="movie-caption">Every item. Accounted for.</div>
  <div class="movie-footer"><div class="movie-progress" aria-hidden="true"><i></i></div><button class="splash-skip" id="splashSkip">Skip intro ↗</button></div>
</div>
''' +s[b:]
a=s.index('var splashDone = false;');b=s.index('\n/* =========================================================\n   BOOT',a)
s=s[:a]+'''var splashDone = false, splashTimers=[];
function runSplash(){
  var sp=$('splash');if(!sp){splashDone=true;return;}
  var appRoot=$('app');if(appRoot)appRoot.inert=true;
  function later(fn,ms){splashTimers.push(setTimeout(function(){if(!splashDone)fn();},ms));}
  sp.addEventListener('click',hideSplash);
  sp.addEventListener('keydown',function(e){if(e.key==='Escape'){e.preventDefault();hideSplash();}});
  if(!motionAllowed()){
    sp.classList.add('draw','shine');later(hideSplash,420);return;
  }
  later(function(){sp.classList.add('draw');},60);
  later(function(){sp.classList.add('shine');},3650);
  later(hideSplash,5800);
}
function hideSplash(){
  var sp=$('splash');if(!sp || splashDone)return;
  splashDone=true;splashTimers.forEach(clearTimeout);splashTimers=[];
  if($('app'))$('app').inert=false;
  var restore=sp.contains(document.activeElement);
  sp.classList.add('gone');document.body.classList.add('splashed');
  setTimeout(function(){if(sp.parentNode)sp.parentNode.removeChild(sp);if(restore){var button=!ONBOARDED?$('obNext'):$('btnScan');if(button)button.focus();}},motionAllowed()?560:0);
}
''' +s[b:]
s=s.replace("bg:'#08070f', s1:'#12101f', s2:'#1a1730', s3:'#241f42', line:'#2f2952'", "bg:'#050208', s1:'#0e0916', s2:'#170e24', s3:'#26143c', line:'#39204f'")
s=s.replace("--bg:#0b0e14; --surface:#121722; --surface-2:#1a2130; --surface-3:#222b3c;", "--bg:#050208; --surface:#0e0916; --surface-2:#170e24; --surface-3:#26143c;")
s=s.replace("--accent:#f5a524; --accent-ink:#1a1205;", "--accent:#a855f7; --accent-ink:#150a24;")
s=s.replace('content="#0b0e14"','content="#050208"').replace("label:'Version 1.10.1'", "label:'Version 1.11.0'")
p.write_text(s)
p=r/'android/res/values/styles.xml';s=p.read_text().replace('#08070f','#030105');p.write_text(s)
p=r/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text().replace('web.setBackgroundColor(0xFF0B0E14)','web.setBackgroundColor(0xFF030105)');p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.10.1','1.11.0').replace('--version-code 13','--version-code 14').replace('versionCode="13"','versionCode="14"');p.write_text(s)
