from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text();pos=s.index('</style>');s=s[:pos]+'''
/* Motion polish: short, interruptible feedback; no scan or save is delayed. */
@keyframes menuGlide{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:none}}
#app[data-drawer="left"] .nav-item{animation:menuGlide .32s ease-out both;animation-delay:calc(var(--nav-order,0) * 18ms)}
.btn,.icon-btn,.step-btn,.qbtn{transition:transform .17s ease,background-color .2s ease,box-shadow .2s ease}
.btn:active,.icon-btn:active,.step-btn:active,.qbtn:active{transform:scale(.96)}
@media(hover:hover){.btn:hover,.qbtn:hover{transform:translateY(-2px);box-shadow:0 5px 16px #0002}}
input,select{transition:border-color .2s,box-shadow .2s,background-color .2s}
input:focus,select:focus{box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 18%,transparent)}
.bar i{transform-origin:left center}
.pimg{transition:box-shadow .25s ease}
#toast{overflow:hidden}
#toast.good::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;background:var(--ok);transform-origin:left;animation:toastTimer 2.1s linear both}
@keyframes toastTimer{from{transform:scaleX(1)}to{transform:scaleX(0)}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
body.motion-paused *,body.motion-paused *::before,body.motion-paused *::after{animation-play-state:paused!important}
''' +s[pos:]
pos=s.index('/* tactile ripple on any tappable control */');s=s[:pos]+'''/* Motion helpers preserve exact values and never gate application logic. */
function motionAllowed(){return !!S.animate && !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);}
function motionPlay(el,frames,options){
  if(!el || !motionAllowed() || document.hidden || typeof el.animate!=='function')return;
  if(el._trillMotion)try{el._trillMotion.cancel();}catch(e){}
  el._trillMotion=el.animate(frames,Object.assign({duration:360,easing:'cubic-bezier(.2,.8,.2,1)'},options || {}));
}
function motionNumber(el){motionPlay(el,[{transform:'translateY(5px) scale(.94)',opacity:.55},{transform:'translateY(-2px) scale(1.06)',opacity:1,offset:.55},{transform:'none',opacity:1}],{duration:340});}
function animateSheetDetails(){
  motionPlay($('sheetTitle'),[{opacity:.4,transform:'translateX(10px)'},{opacity:1,transform:'none'}],{duration:260});
  document.querySelectorAll('#sheetBody .stat').forEach(function(el,i){if(i<8)motionPlay(el,[{transform:'translateY(10px)',opacity:.3},{transform:'none',opacity:1}],{delay:i*35,duration:330});});
  document.querySelectorAll('#sheetBody .bar i').forEach(function(el){motionPlay(el,[{transform:'scaleX(0)'},{transform:'scaleX(1)'}],{duration:540});});
  motionPlay(document.querySelector('#sheetBody .pimg'),[{transform:'scale(.92) rotate(-2deg)',opacity:.5},{transform:'scale(1)',opacity:1}],{duration:400});
}
function syncMotionPreference(){
  document.body.classList.toggle('no-anim',!motionAllowed());
  if(!motionAllowed() && document.getAnimations)document.getAnimations().forEach(function(a){a.cancel();});
}
function wireExtraMotion(){
  document.querySelectorAll('.nav-item').forEach(function(el,i){el.style.setProperty('--nav-order',Math.min(i,10));});
  document.addEventListener('toggle',function(e){
    if(e.target.tagName==='DETAILS' && e.target.open){
      var body=e.target.querySelector('.setgroup-body');
      motionPlay(body,[{opacity:0,transform:'translateY(-5px)'},{opacity:1,transform:'none'}],{duration:260});
    }
  },true);
  document.addEventListener('visibilitychange',function(){document.body.classList.toggle('motion-paused',document.hidden);});
  var media=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  if(media){if(media.addEventListener)media.addEventListener('change',syncMotionPreference);else if(media.addListener)media.addListener(syncMotionPreference);}
  syncMotionPreference();
}

''' +s[pos:]
s=s.replace("  $('sheetBody').scrollTop = 0;\n}","  $('sheetBody').scrollTop = 0;\n  animateSheetDetails();\n}")
s=s.replace("function refreshQtyVal(){\n  var el = $('qtyVal');\n  if(el) el.textContent = pendingQty;", "function refreshQtyVal(){\n  var el = $('qtyVal');\n  if(el){var changed=el.textContent!==String(pendingQty);el.textContent=pendingQty;if(changed)motionNumber(el);}")
s=s.replace("function renderHud(){\n  var chips", "function renderHud(){\n  var oldNumbers=Array.prototype.map.call(document.querySelectorAll('#hudChips b'),function(el){return el.textContent;});\n  var chips")
s=s.replace("  $('hudChips').innerHTML = chips.join('');", "  $('hudChips').innerHTML = chips.join('');\n  document.querySelectorAll('#hudChips b').forEach(function(el,i){if(oldNumbers[i]!==el.textContent)motionNumber(el);});")
s=s.replace("  document.body.classList.toggle('no-anim', !S.animate);", "  syncMotionPreference();")
s=s.replace("if(!S.animate)","if(!motionAllowed())")
s=s.replace("  if(source === 'added' && S.animate){", "  if(source === 'price' || source === 'browser'){\n    motionPlay(document.querySelector('#sheetBody .statgrid'),[{outline:'2px solid var(--accent)',outlineOffset:'0px'},{outline:'2px solid transparent',outlineOffset:'5px'}],{duration:650});\n  }\n  if(source === 'added' && motionAllowed()){")
s=s.replace("  wire();\n  runSplash();", "  wire();\n  wireExtraMotion();\n  runSplash();")
s=s.replace("label:'Animations', d:'Transitions and the scanning line.'", "label:'Animations', d:'Screen entrances, counters, button feedback and scanning line. Respects system reduced motion.'")
p.write_text(s)
p=r/'android/vendor/remote.html';s=p.read_text();s=s.replace('</style>', '''
@keyframes dashboardEnter{from{opacity:0;transform:translateY(15px)}to{opacity:1;transform:none}}
@keyframes dialogEnter{from{opacity:0;transform:translateY(20px) scale(.96)}to{opacity:1;transform:none}}
@keyframes onlineBreathe{0%,100%{opacity:.45}50%{opacity:1}}
#dashboard:not([hidden]),.login{animation:dashboardEnter .45s ease-out both}
.stats .card{animation:dashboardEnter .45s ease-out both}.stats .card:nth-child(2){animation-delay:60ms}.stats .card:nth-child(3){animation-delay:120ms}
dialog[open]{animation:dialogEnter .3s cubic-bezier(.2,.85,.2,1)}dialog[open]::backdrop{animation:dashboardEnter .2s ease-out}
button{transition:transform .16s ease,background-color .2s,box-shadow .2s}button:active{transform:scale(.96)}
@media(hover:hover){button:not(:disabled):hover{transform:translateY(-2px);box-shadow:0 5px 18px #0004}tbody tr:hover{background:#ffffff05}}
input,select{transition:border-color .2s,box-shadow .2s}input:focus{box-shadow:0 0 0 3px #bd8bff22}
.status:not(.error):not(:empty)::before{content:'';display:inline-block;width:7px;height:7px;background:#8bdfbb;border-radius:50%;margin-right:9px;animation:onlineBreathe 2.6s ease-in-out infinite}
.stats b{display:block;transform-origin:left center}
.no-motion *,.no-motion *::before,.no-motion *::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>''')
s=s.replace('<button id="disconnect" hidden>', '<button id="motionToggle" aria-pressed="true" title="Toggle dashboard animations">Motion on</button><button id="disconnect" hidden>')
a=s.index('function render(){');b=s.index('\nasync function refresh()',a)
s=s[:a]+'''let motionEnabled=true;try{motionEnabled=localStorage.getItem('trill.dashboardMotion')!=='off';}catch(e){}
function canAnimate(){return motionEnabled && !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);}
function play(el,frames,options={}){if(!el||!canAnimate()||document.hidden||!el.animate)return;if(el._motion)el._motion.cancel();el._motion=el.animate(frames,{duration:360,easing:'cubic-bezier(.2,.8,.2,1)',...options});}
function setCounter(id,value){const el=$(id),changed=el.textContent!==String(value);el.textContent=value;if(changed)play(el,[{transform:'translateY(7px) scale(.95)',opacity:.55},{transform:'none',opacity:1}]);}
function updateMotion(){document.body.classList.toggle('no-motion',!canAnimate());$('motionToggle').textContent=canAnimate()?'Motion on':'Motion off';$('motionToggle').setAttribute('aria-pressed',String(canAnimate()));if(!canAnimate()&&document.getAnimations)document.getAnimations().forEach(a=>a.cancel());}
$('motionToggle').onclick=()=>{motionEnabled=!motionEnabled;try{localStorage.setItem('trill.dashboardMotion',motionEnabled?'on':'off');}catch(e){}updateMotion();};
const motionMedia=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)');if(motionMedia&&motionMedia.addEventListener)motionMedia.addEventListener('change',updateMotion);updateMotion();
function render(){
 const q=$('search').value.toLowerCase(),low=$('filter').value==='low';setCounter('products',rows.length);setCounter('units',rows.reduce((s,r)=>s+r.qty,0));setCounter('low',rows.filter(r=>r.qty<=r.rp).length);
 const view=rows.filter(r=>(r.name+' '+r.brand+' '+r.upc).toLowerCase().includes(q)&&(!low||r.qty<=r.rp)),existing=new Map(Array.from($('rows').children).map(el=>[el.dataset.upc,el])),keep=new Set(view.map(r=>r.upc));
 existing.forEach((el,key)=>{if(!keep.has(key))el.remove();});
 view.forEach((r,index)=>{
  let tr=existing.get(r.upc),fresh=!tr;
  if(fresh){tr=document.createElement('tr');tr.dataset.upc=r.upc;const name=document.createElement('td');name.append(document.createElement('b'),document.createElement('small'));tr.append(name);for(let i=0;i<5;i++)tr.append(document.createElement('td'));const button=document.createElement('button');button.textContent='Edit';tr.children[5].append(button);}
  const signature=JSON.stringify(r),changed=tr.dataset.signature&&tr.dataset.signature!==signature;
  tr.children[0].querySelector('b').textContent=r.name;tr.children[0].querySelector('small').textContent=r.upc+' · '+(r.size||'Unit size not set');
  [r.qty,money(r.price),money(r.cost),r.reorder].forEach((value,i)=>{const td=tr.children[i+1],diff=td.textContent!==String(value);td.textContent=value;td.className=i===0&&r.qty<=r.rp?'low':'';if(changed&&diff)play(td,[{color:'#bd8bff',opacity:.45},{color:'inherit',opacity:1}],{duration:650});});
  tr.children[5].querySelector('button').onclick=()=>openEditor(r);tr.dataset.signature=signature;
  if($('rows').children[index]!==tr)$('rows').insertBefore(tr,$('rows').children[index]||null);
  if(fresh&&index<20)play(tr,[{opacity:0,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{delay:Math.min(index*22,180)});
  else if(changed)play(tr,[{backgroundColor:'#bd8bff22'},{backgroundColor:'transparent'}],{duration:800});
 });
 $('empty').hidden=view.length>0;$('empty').textContent=rows.length?'No products match this filter.':'No saved products yet. Scan and save an item on the phone first.';
}
''' +s[b:];p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.9.0','1.10.0').replace('--version-code 11','--version-code 12').replace('versionCode="11"','versionCode="12"');p.write_text(s)
