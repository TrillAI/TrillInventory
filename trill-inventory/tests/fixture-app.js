// Legacy UI regression fixtures, test-only. The shipped app must start with no seed catalog.
const fixture=require('./catalog-fixture.json');
module.exports=html=>html.replace("var EXTRA = lsGet('hs.catalog', []);", "var EXTRA = lsGet('hs.catalog', " + JSON.stringify(fixture) + ");").replace('boot();\n\n})();',"window.confirm=function(){return true;};S.autoPhotos=false;boot();\n\n})();");
