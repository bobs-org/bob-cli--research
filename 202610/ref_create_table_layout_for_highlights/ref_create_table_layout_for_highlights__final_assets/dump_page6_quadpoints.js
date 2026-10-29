var doc = Document.openDocument(scriptArgs[0]);
var page = doc.loadPage(5);
var pobj = page.getObject();
var annots = pobj.get("Annots");
print("Annots count: "+annots.length);
for (var i=0;i<annots.length;i++){
  var a = annots.get(i);
  var st = a.get("Subtype");
  var qp = a.get("QuadPoints"); var r = a.get("Rect");
  var s=""; for (var k=0;k<qp.length;k++){ s+= (Math.round(qp.get(k).valueOf()*10)/10)+" "; }
  var rs=""; for (var k=0;k<r.length;k++){ rs+= (Math.round(r.get(k).valueOf()*10)/10)+" "; }
  print(i+" "+st+" M="+a.get("M")+" Rect=["+rs+"] QP=["+s.substring(0,120)+"]");
}
