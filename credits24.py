from pathlib import Path
r=Path('/home/user/trill-inventory');p=r/'index.html';s=p.read_text()
s=s.replace("bg:'#050208', s1:'#0e0916', s2:'#170e24', s3:'#26143c', line:'#39204f'", "bg:'#08070f', s1:'#12101f', s2:'#1a1730', s3:'#241f42', line:'#2f2952'")
s=s.replace('--bg:#050208; --surface:#0e0916; --surface-2:#170e24; --surface-3:#26143c;', '--bg:#08070f; --surface:#12101f; --surface-2:#1a1730; --surface-3:#241f42;')
s=s.replace('--line:#26303f; --text:#e8edf6; --muted:#8b98ad;', '--line:#2f2952; --text:#efeaff; --muted:#9a93bd;')
s=s.replace('content="#050208"','content="#08070f"').replace("--intro-purple:#b65bff", "--intro-purple:#a855f7")
s=s.replace('background:#030105;transition:opacity', 'background:#08070f;transition:opacity')
s=s.replace('stop-color="#bb69ff"','stop-color="#a855f7"')
# favicon uses the same icon palette, including dark T against purple
s=s.replace("fill='%230b0e14'", "fill='%23a855f7'").replace("fill='%23f5a524'", "fill='%23150a24'")
pos=s.index('/* Motion polish:')
s=s[:pos]+'''/* Opening credits play before the existing T-building movie. */
.splash-credits{position:absolute;inset:0;z-index:8;display:flex;align-items:center;justify-content:center;background:#08070f;pointer-events:none}
.credit-card{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:36px;text-align:center;opacity:0}
.credit-card p{margin:0;color:#dcb7ff;font-size:clamp(25px,6.8vw,38px);font-weight:550;letter-spacing:.035em;line-height:1.4;max-width:620px;text-shadow:0 0 35px #a855f733}
#creditProduction p{font-size:clamp(22px,6vw,34px);font-weight:700}
#splash.credit-author #creditAuthor{animation:creditFade 2.4s ease both}
#splash.credit-production #creditProduction{animation:creditFade 2.4s ease both}
@keyframes creditFade{0%{opacity:0}25%,72%{opacity:1}100%{opacity:0}}
#splash:not(.draw) .splash-scene,#splash:not(.draw) .splash-word,#splash:not(.draw) .splash-sub,#splash:not(.draw) .movie-caption{visibility:hidden}
#splash.draw .splash-credits{display:none}
#splash .movie-footer{z-index:10}
.no-anim #splash.credit-author #creditAuthor,.no-anim #splash.credit-production #creditProduction{opacity:1}
#splash.draw .movie-footer .movie-progress i{animation-duration:5.74s}

''' +s[pos:]
s=s.replace('<div id="splash" role="dialog" aria-label="Trill Inventory startup movie">', '<div id="splash" role="dialog" aria-modal="true" aria-label="Trill Inventory opening credits and startup movie">\n  <div class="splash-credits"><div class="credit-card" id="creditAuthor"><p>By Brian Cross</p></div><div class="credit-card" id="creditProduction"><p>A Trill Tech Production!</p></div></div>')
a=s.index('  if(!motionAllowed()){',s.index('function runSplash()'));b=s.index('\n}\nfunction hideSplash()',a)
s=s[:a]+'''  var creditDuration=motionAllowed()?2400:800;
  sp.classList.add('credit-author');
  later(function(){sp.classList.remove('credit-author');sp.classList.add('credit-production');},creditDuration);
  later(function(){
    sp.classList.remove('credit-production');sp.classList.add('draw');
    if(!motionAllowed()){sp.classList.add('shine');later(hideSplash,420);return;}
    later(function(){sp.classList.add('shine');},3590);
    later(hideSplash,5740);
  },creditDuration*2);
''' +s[b:]
s=s.replace("label:'Version 1.11.0'", "label:'Version 1.12.0'")
p.write_text(s)
p=r/'android/res/values/styles.xml';s=p.read_text().replace('#030105','#08070f');p.write_text(s)
p=r/'android/src/com/harrys/scan/MainActivity.java';s=p.read_text().replace('web.setBackgroundColor(0xFF030105)','web.setBackgroundColor(0xFF08070F)');p.write_text(s)
p=r/'android/vendor/remote.html';s=p.read_text().replace('--bg:#0c0b12;--card:#17151f;--line:#302c3d;--muted:#a9a2b8;--accent:#bd8bff','--bg:#08070f;--card:#12101f;--line:#2f2952;--muted:#9a93bd;--accent:#a855f7').replace('#bd8bff','#a855f7');p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=r/f;s=p.read_text().replace('1.11.0','1.12.0').replace('--version-code 14','--version-code 15').replace('versionCode="14"','versionCode="15"');p.write_text(s)
