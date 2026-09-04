from pathlib import Path
import numpy as np,cv2,json,hashlib
from PIL import Image
from scipy.interpolate import splprep,splev,LinearNDInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import contains_xy
import triangle
P=Path(__file__).parent;W,H=1280,2040;BW,BH=53.98,85.6
backup=P/'output/before-rim-cleanup';old=np.load(backup/'geometry.npz')
mask=np.array(Image.open(P/'output/cutout-mask-proposed.png'))>0
contours,hierarchy=cv2.findContours(mask.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
def smooth_ring(c):
 pts=cv2.approxPolyDP(c,.5,True)[:,0,:].astype(float)
 if len(pts)>=6:
  tck,u=splprep(pts.T,s=len(pts)*.8,per=True)
  length=cv2.arcLength(pts.astype(np.float32),True)
  pts=np.array(splev(np.linspace(0,1,max(32,int(length/1.4)),endpoint=False),tck)).T
 return np.column_stack([pts[:,0]/W*BW-BW/2,BH/2-pts[:,1]/H*BH])
holes=[]
for i,c in enumerate(contours):
 if hierarchy[0,i,3]!=-1 or cv2.contourArea(c)<100:continue
 inn=[];child=hierarchy[0,i,2]
 while child!=-1:
  if cv2.contourArea(contours[child])>10:inn.append(smooth_ring(contours[child]))
  child=hierarchy[0,child,0]
 q=Polygon(smooth_ring(c),inn).buffer(0)
 if not q.is_empty:holes.append(q)
radius=3.18
outer=box(-BW/2+radius,-BH/2+radius,BW/2-radius,BH/2-radius).buffer(radius,quad_segs=32)
body=outer.difference(unary_union(holes)).buffer(0)
if body.geom_type!='Polygon':raise RuntimeError('Cleanup detached an ornament; do not alter it or add supports')
metrics=json.loads((backup/'metrics.json').read_text())
if len(body.interiors)<metrics['cutout_count']:raise RuntimeError('Cleanup merged openings and could remove an ornamental rib')
print('Opening areas',sorted(round(Polygon(r).area,4) for r in body.interiors),flush=True)
vertices=[];segments=[];seeds=[]
def ring(coords):
 pts=list(coords)[:-1];off=len(vertices);vertices.extend(pts);segments.extend([(off+i,off+(i+1)%len(pts)) for i in range(len(pts))])
ring(body.exterior.coords)
for ring0 in body.interiors:
 ring(ring0.coords);p=Polygon(ring0).representative_point();seeds.append([p.x,p.y])
# Retain the previous surface sampling everywhere outside the edited rim.
xy=old['vertices'];keep=contains_xy(body,xy[:,0],xy[:,1]);vertices.extend(xy[keep].tolist())
mesh=triangle.triangulate(dict(vertices=vertices,segments=segments,holes=seeds),'pq24a0.035')
v=mesh['vertices'];tri=mesh['triangles'];seg=mesh['segments']
a=v[tri[:,1]]-v[tri[:,0]];b=v[tri[:,2]]-v[tri[:,0]];flip=a[:,0]*b[:,1]-a[:,1]*b[:,0]<0;tri[flip]=tri[flip,::-1]
heights=[]
for key in ['front_height','back_height']:
 interp=LinearNDInterpolator(xy,old[key]);z=interp(v)
 bad=~np.isfinite(z)
 if bad.any():z[bad]=old[key][cKDTree(xy).query(v[bad])[1]]
 z[np.unique(seg)]=.04;heights.append(z.astype(np.float32))
np.savez_compressed(P/'output/geometry.npz',vertices=v,triangles=tri,segments=seg,front_height=heights[0],back_height=heights[1])
Image.fromarray(mask.astype(np.uint8)*255).save(P/'output/cutout-mask.png')
metrics['cutout_count']=len(body.interiors)
metrics['cutout_area_percent']=round((outer.area-body.area)/outer.area*100,2);metrics['surface_triangles_per_side']=len(tri)
metrics['rim_cleanup']={'cutouts':len(body.interiors),'smooth_contours':True,'texture_maps_unchanged':True,'gemstones_unchanged':True}
(P/'output/metrics.json').write_text(json.dumps(metrics,indent=2))
# Record protected assets so their byte-for-byte preservation can be checked after the rebuild.
protected=[P/'output/gems.json']+sorted((P/'textures').glob('*'))
proof={str(x.relative_to(P)):hashlib.sha256(x.read_bytes()).hexdigest() for x in protected if x.is_file()}
(P/'output/rim-cleanup-protected-assets.json').write_text(json.dumps(proof,indent=2))
print({'openings':len(body.interiors),'cutout_area_percent':metrics['cutout_area_percent'],'triangles':len(tri),'protected_assets':len(proof)},flush=True)


