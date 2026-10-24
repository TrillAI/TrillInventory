from pathlib import Path
import base64
r=Path('/home/user/trill-inventory')
font=base64.b64encode((r/'android/vendor/Manrope.ttf').read_bytes()).decode()
terrain='''<path d="M0 236V280H900V236" fill="#342349"/><path d="M0 237H900" stroke="#c187ff" stroke-width="3"/><path d="M0 265H900M30 238V265M90 265V280M150 238V265M210 265V280M270 238V265M330 265V280M390 238V265M450 265V280M510 238V265M570 265V280M630 238V265M690 265V280M750 238V265M810 265V280M870 238V265" stroke="#654280" stroke-width="2"/>
<path d="M300 236V192H350V236M294 192V180H356V192Z M600 236V192H650V236M594 192V180H656V192Z" fill="#628753" stroke="#b6dc89" stroke-width="2"/>
<path d="M30 235Q100 96 175 235M390 235Q470 105 550 235M710 235Q770 130 840 235" fill="#32234e"/>
<g fill="#fac86b" stroke="#ffefac" stroke-width="2"><ellipse cx="305" cy="105" rx="7" ry="11"/><ellipse cx="335" cy="98" rx="7" ry="11"/><ellipse cx="605" cy="105" rx="7" ry="11"/><ellipse cx="635" cy="98" rx="7" ry="11"/></g><path d="M895 235V73" stroke="#cab0ec" stroke-width="4"/><path d="M893 76L851 88L893 100Z" fill="#c49aff"/><circle cx="895" cy="70" r="5" fill="#f6ce79"/>
<g fill="#aa8bc3" opacity=".4"><path d="M45 70Q47 51 63 57Q73 33 93 53Q116 50 117 70Z"/><path d="M425 58Q427 39 443 45Q453 21 473 41Q496 38 497 58Z"/><path d="M760 100Q762 81 778 87Q788 63 808 83Q831 80 832 100Z"/></g>'''
scene='''<div class="level-scene" aria-hidden="true"><svg viewBox="0 0 900 280" preserveAspectRatio="xMidYMax slice"><g class="level-world">'''+terrain+'<g transform="translate(900 0)">'+terrain+'''</g></g><g transform="translate(160 190)"><g class="level-runner"><path d="M8 13Q5 0 20 0Q34 0 34 12H39V17H6V13" fill="#ef4d5b"/><circle cx="22" cy="8" r="6" fill="#fff0df"/><text x="18" y="11" font-size="8" font-family="sans-serif" font-weight="bold" fill="#da3248">M</text><path d="M10 17H31V31H12Z" fill="#efb48d"/><path d="M8 17H15V25H10M23 25H36V29H23" fill="#452739"/><circle cx="28" cy="20" r="2" fill="#241628"/><path d="M30 20H38V25H30" fill="#efb48d"/><path d="M10 31H31V41H10Z" fill="#ef4d5b"/><path d="M14 30V39H27V30M13 38H29V48H12Z" fill="#5785cc" stroke="#5785cc" stroke-width="3"/><g class="runner-feet" fill="#4c3040"><path d="M10 46H20V53H5V50Z"/><path d="M24 46H33V52H39V55H24Z"/></g><circle cx="12" cy="36" r="4" fill="#fff0df"/><circle cx="32" cy="36" r="4" fill="#fff0df"/></g></g></svg><div class="level-win">★ LEVEL CLEAR! ★</div></div>'''
css='''
@font-face{font-family:Manrope;src:url(data:font/ttf;base64,'''+font+''') format('truetype');font-weight:200 800;font-display:swap}
body,input,select,textarea,button{font-family:Manrope,system-ui,sans-serif}
.level-scene{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:0;background:radial-gradient(ellipse at 70% 60%,#33134d 0%,#08070f 75%)}.level-scene svg{position:absolute;bottom:0;width:100%;height:min(45vh,380px);opacity:.32}.level-world{animation:levelTravel 12s linear infinite}.level-runner{animation:levelJump 12s linear infinite}.runner-feet{animation:levelFeet .22s steps(2,end) infinite;transform-origin:20px 48px}.level-win{position:absolute;bottom:28vh;right:8%;font-weight:800;font-size:clamp(12px,2vw,24px);letter-spacing:.15em;color:#f8d492;opacity:0;animation:levelWin 12s infinite;text-shadow:0 0 22px #e1a641}
@keyframes levelTravel{to{transform:translateX(-900px)}}@keyframes levelJump{0%,8%,26%,41%,59%,75%,96%,100%{transform:translateY(0)}12%,22%,45%,55%{transform:translateY(-90px)}82%,88%{transform:translateY(-45px)}}@keyframes levelFeet{to{transform:skewX(-18deg)}}@keyframes levelWin{0%,77%,98%,100%{opacity:0;transform:translateY(10px) scale(.97)}81%,94%{opacity:.85;transform:none}}
.no-motion .level-scene *,.motion-off .level-scene *{animation:none!important}.no-motion .level-win,.motion-off .level-win{display:none}
@media(prefers-reduced-motion:reduce){.level-scene *{animation:none!important}.level-win{display:none}}
'''
for f in ['index.html','android/vendor/remote.html']:
 p=r/f;s=p.read_text();s=s.replace('</style>',css+'</style>',1)
 if f=='index.html':
  s=s.replace('<div id="stage">','<div id="stage">'+scene,1)
  # Background also appears through overlay surfaces; camera view is never covered.
  s=s.replace('<div id="app" data-drawer="none">',scene+'<div id="app" data-drawer="none">',1)
  s=s.replace('function renderHud(){','function renderHud(){\n  document.body.classList.toggle("camera-live",!!camOn);',1)
  s=s.replace('</style>','''
.camera-live #stage .level-scene{display:none}#stage>.level-scene{z-index:0}#stage video{position:relative;z-index:1}.drawer,.sheet{background:linear-gradient(150deg,#171025f5,#0e0b17f5);backdrop-filter:blur(22px)}.pair-qr{max-width:260px;margin:18px auto;background:white;padding:10px;border-radius:20px}.pair-qr svg{display:block;width:100%;height:auto}.cigarette-box{border-color:#8261a5;background:linear-gradient(135deg,#30203d,#1a1226)}.splash-credit{font-family:Manrope,system-ui,sans-serif!important;letter-spacing:.08em!important}.splash .level-scene{opacity:.55}#splash .level-scene{z-index:0;opacity:.7}#splash>.level-scene~*{position:relative}#splash::before{content:'';position:absolute;inset:-50%;background:conic-gradient(from 0deg,transparent,#ab72eb12,transparent,#e7b7ff0b,transparent);animation:splashOrbit 20s linear infinite;pointer-events:none}@keyframes splashOrbit{to{transform:rotate(360deg)}}
</style>''',1)
  # Place scene inside splash without changing its layout roles.
  import re
  s=re.sub(r'(<div[^>]*id="splash"[^>]*>)',lambda m:m[0]+scene,s,count=1)
 else:s=s.replace('</style><main>','</style>'+scene+'<main>',1)
 p.write_text(s)
(r/'android/vendor/level-scene.html').write_text(scene)
