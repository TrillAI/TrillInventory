from pathlib import Path
p=Path('/home/user/trill-inventory/index.html');s=p.read_text()
s='\n'.join(x for x in s.split('\n') if 'data-nav="store"' not in x and 'var shifted = {};' not in x)
a=s.index('function viewStore(){');b=s.index('/* =========================================================',a);s=s[:a]+s[b:]
s=s.replace("  $('sheet').classList.add('on');", "  app.setAttribute('data-drawer','none');\n  $('sheet').classList.add('on');",1).replace("  sheetOpen = true;\n", "  sheetOpen = true;\n  syncNavigationState();\n",1)
a=s.index('function closeSheet(){');b=s.index('\nfunction showResult',a)
s=s[:a]+'''function closeSheet(){
  closeSheetSilent();
  syncNavigationState();
  renderHud();
}
'''+s[b:]
a=s.index('function openDrawer(side){');b=s.index('function isDrawerOpen()',a)
s=s[:a]+'''function syncNavigationState(){
  var side=app.getAttribute('data-drawer'), guide=!$('onboard').classList.contains('off');
  scanPaused=sheetOpen || side!=='none' || guide;
  $('scrim').classList.toggle('on',sheetOpen || side!=='none');
  $('stage').inert=scanPaused;
  [['drawerLeft',side==='left'],['drawerRight',side==='right'],['sheet',sheetOpen]].forEach(function(pair){
    var el=$(pair[0]);
    if(!pair[1] && el.contains(document.activeElement))document.activeElement.blur();
    el.inert=!pair[1];el.setAttribute('aria-hidden',String(!pair[1]));
  });
  $('btnMenu').setAttribute('aria-expanded',String(side==='left'));
  $('btnSettings').setAttribute('aria-expanded',String(side==='right'));
  setTimeout(syncTorch,60);
}
function openDrawer(side){
  closeSheetSilent();
  app.setAttribute('data-drawer',side);
  $('drawerLeft').style.transform='';$('drawerRight').style.transform='';
  if(side==='right')renderSettings();
  syncNavigationState();
}
function closeSheetSilent(){
  stopPhotoCapture();photoGeneration++;unknownRequest++;
  $('sheet').classList.remove('on');
  sheetOpen=false;currentUpc=null;onlineLoading=false;
}
function closeDrawers(){
  app.setAttribute('data-drawer','none');
  $('drawerLeft').style.transform='';$('drawerRight').style.transform='';
  syncNavigationState();
}
'''+s[b:]
a=s.index('/* swipe */');b=s.index('/* =========================================================\n   ONBOARDING',a)
s=s[:a]+'''/* A pointer-down is only a candidate: taps and vertical scrolling must
   retain their native click/scroll behavior. */
var drag=null, EDGE=30, suppressSwipeClick=false;
function onDown(e){
  suppressSwipeClick=false;
  if(drag || sheetOpen || e.isPrimary===false || (e.pointerType==='mouse' && e.button!==0))return;
  if(e.target.closest('input,select,textarea,[contenteditable="true"],.switch'))return;
  var side=app.getAttribute('data-drawer'), opened=side!=='none';
  if(!opened){side=e.clientX<=EDGE?'left':e.clientX>=window.innerWidth-EDGE?'right':null;}
  if(!side)return;
  drag={side:side,open:opened,x0:e.clientX,y0:e.clientY,id:e.pointerId,active:false,p:opened?1:0};
  window.addEventListener('pointermove',onMove,{passive:false});
  window.addEventListener('pointerup',onUp);
  window.addEventListener('pointercancel',onUp);
}
function onMove(e){
  if(!drag || e.pointerId!==drag.id)return;
  var dx=e.clientX-drag.x0,dy=e.clientY-drag.y0;
  if(!drag.active){
    if(Math.abs(dy)>10 && Math.abs(dy)>=Math.abs(dx)){onUp({pointerId:drag.id,type:'pointercancel'});return;}
    if(Math.abs(dx)<12 || Math.abs(dx)<=Math.abs(dy))return;
    drag.active=true;$(drag.side==='left'?'drawerLeft':'drawerRight').classList.add('dragging');
  }
  if(e.cancelable)e.preventDefault();
  var el=$(drag.side==='left'?'drawerLeft':'drawerRight'),w=el.offsetWidth;
  var amount=drag.side==='left'?dx:-dx;
  drag.p=Math.max(0,Math.min(1,(drag.open?1:0)+amount/w));
  el.style.transform='translateX('+((drag.side==='left'?-1:1)*(1-drag.p)*w)+'px)';
  $('scrim').classList.add('on');
}
function onUp(e){
  if(!drag || (e && e.pointerId!==drag.id))return;
  var d=drag;drag=null;
  window.removeEventListener('pointermove',onMove);window.removeEventListener('pointerup',onUp);window.removeEventListener('pointercancel',onUp);
  var el=$(d.side==='left'?'drawerLeft':'drawerRight');el.classList.remove('dragging');el.style.transform='';
  if(!d.active)return;
  suppressSwipeClick=true;
  if(e && e.type==='pointercancel'){syncNavigationState();return;}
  if(d.p>(d.open?0.6:0.35))openDrawer(d.side);else closeDrawers();
}

'''+s[b:]
s=s.replace("  setObStep(0);\n}","  setObStep(0);\n  syncNavigationState();\n}",1)
s=s.replace("  $('onboard').classList.add('off');\n  renderHud();","  $('onboard').classList.add('off');\n  syncNavigationState();\n  renderHud();",1)
s=s.replace("  var raw = String(upc == null", "  if(source==='camera' && (sheetOpen || isDrawerOpen() || !$('onboard').classList.contains('off')))return;\n  var raw = String(upc == null",1)
s=s.replace("    setTimeout(function(){\n      if(what === 'scan')", "    closeSheetSilent();syncNavigationState();\n      if(what === 'scan')",1)
s=s.replace("      else if(what === 'store') viewStore();\n",'')
s=s.replace("else if(what === 'guide'){ $('onboard').classList.remove('off'); setObStep(0); }\n    }, 180);", "else if(what === 'guide') showOb();")
a=s.index("  $('drawerLeft').addEventListener('pointerdown', function(e)");b=s.index('\n',a)
s=s[:a]+"  $('drawerLeft').addEventListener('pointerdown',onDown);\n  $('drawerRight').addEventListener('pointerdown',onDown);\n  document.addEventListener('pointerdown',function(){suppressSwipeClick=false;},true);\n  document.addEventListener('click',function(e){if(suppressSwipeClick){e.preventDefault();e.stopImmediatePropagation();suppressSwipeClick=false;}},true);"+s[b:]
s=s.replace("if(e.key === 'Escape'){ closeSheet(); closeDrawers(); }", "if(e.key === 'Escape' && !e.defaultPrevented){if(window.__hsHandleBack())e.preventDefault();}")
s=s.replace("    if(!$('onboard').classList.contains('off')) return true;", "    if(!$('onboard').classList.contains('off')){\n      if(ONBOARDED){$('onboard').classList.add('off');syncNavigationState();}\n      else if(obStep>0)setObStep(obStep-1);\n      return true;\n    }")
s=s.replace("else if(a === 'viewImport') { closeDrawers(); setTimeout(viewImport, 160); }", "else if(a === 'viewImport') { closeDrawers(); viewImport(); }")
s=s.replace("else if(a === 'guide'){ closeDrawers(); setTimeout(function(){ $('onboard').classList.remove('off'); setObStep(0); }, 180); }", "else if(a === 'guide'){ closeDrawers();closeSheetSilent();showOb(); }")
s=s.replace("  else { $('onboard').classList.add('off'); }\n}","  else { $('onboard').classList.add('off'); }\n  syncNavigationState();\n}")
s=s.replace('</style>','\n.drawer{touch-action:pan-y}\n.drawer-body{overscroll-behavior:contain;min-height:0}\n</style>',1)
p.write_text(s)
for f in ['android/build.sh','android/AndroidManifest.xml']:
 p=Path('/home/user/trill-inventory')/f;t=p.read_text().replace('1.14.0','1.15.0').replace('versionCode="17"','versionCode="18"');p.write_text(t)
