from pathlib import Path
import numpy as np, cv2, json
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, distance_transform_edt
P=Path(__file__).parent
W,H=1280,2040
ims=[]
for side in [1,2]:
 im=np.array(Image.open(P/f'source/side_{side}.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS))
 ims.append(im)
a=ims[0]; b=ims[1][::-1]
# Register the reverse photograph after a flip around the horizontal axis.
sift=cv2.SIFT_create(nfeatures=6000)
k1,d1=sift.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_RGB2GRAY),None)
k2,d2=sift.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_RGB2GRAY),None)
matches=cv2.BFMatcher().knnMatch(d2,d1,k=2)
good=[m for m,n in matches if m.distance<.69*n.distance]
src=np.float32([k2[m.queryIdx].pt for m in good]); dst=np.float32([k1[m.trainIdx].pt for m in good])
M,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=4)
print('Registration',len(good),int(inliers.sum()),M,flush=True)
# Preserve the nearly identical outer frame; only accept small alignment corrections.
if M is None or np.linalg.norm(M[:,:2]-np.eye(2))>.08: M=np.array([[1,0,0],[0,1,0]],float)
b=cv2.warpAffine(b,M,(W,H),borderMode=cv2.BORDER_REPLICATE)
np.save(P/'output/back_alignment.npy',M)
# Corrected from the user's red annotation: ONLY the diagonal ivory fan / scroll band.
# The neutral floral mineral fields outside this band are solid stone.
env=np.zeros((H,W),np.uint8)
polys=[[(.050,.392),(.125,.320),(.210,.277),(.302,.272),(.333,.348),(.350,.383),(.407,.451),(.495,.511),(.602,.602),(.709,.625),(.676,.653),(.575,.708),(.459,.716),(.411,.672),(.368,.574),(.307,.521),(.218,.469),(.131,.425)]]
for poly in polys: cv2.fillPoly(env,[np.array([(x*W,y*H) for x,y in poly],np.int32)],255)
af=a.astype(float)/255; bf=b.astype(float)/255
sa=(af.max(2)-af.min(2))/(af.max(2)+.001)
ga=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(float)/255
gb=cv2.cvtColor(b,cv2.COLOR_RGB2GRAY).astype(float)/255
va=np.sqrt(np.maximum(0,gaussian_filter(ga*ga,1.7)-gaussian_filter(ga,1.7)**2))
# Pale interiors are cut; shaded rims, ornamental metalwork and stone settings stay solid.
mask=(env>0)&(sa<.19)&(ga>.64)&(gb>.48)&(va<.045)
mask=cv2.morphologyEx(mask.astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,labels,stats,cents=cv2.connectedComponentsWithStats(mask,8)
mask=np.isin(labels,[i for i in range(1,n) if stats[i,4]>180]).astype('uint8')
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
mask=cv2.erode(mask,np.ones((3,3),np.uint8))
assert not np.any(mask[env==0]), 'Cutouts must stay inside user-marked diagonal band'
Image.fromarray(mask*255).save(P/'output/cutout-mask.png')
over=a.copy(); over[mask>0]=(over[mask>0]*.25+np.array([0,210,240])*.75).astype('uint8')
out=Image.fromarray(over).resize((640,1020)); draw=ImageDraw.Draw(out)
out.save(P/'output/mask-review.jpg')
Image.fromarray(b).resize((640,1020)).save(P/'output/back-aligned.jpg')
print('Hole pixels',int(mask.sum()),'fraction',float(mask.mean()),flush=True)

# Produce PBR maps, microrelief, and gemstone candidates from the originals.
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, nearest_points
import triangle
from scipy.ndimage import map_coordinates
TW,TH=2048,3264
BW,BH=53.98,85.60
heights=[]; gemsets=[]
for si in [1,2]:
 im=np.array(Image.open(P/f'source/side_{si}.png').convert('RGB').resize((TW,TH),Image.Resampling.LANCZOS))
 rgb=im.astype(np.float32)/255
 r,g,bl=rgb.transpose(2,0,1); val=rgb.max(2); sat=(val-rgb.min(2))/(val+.001)
 gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY).astype(np.float32)/255
 # Warm metal traces get real metalness; high-key ivory remains dielectric.
 warm=np.clip((r-bl-.025)*8,0,1)*np.clip((g-bl)*14,0,1)
 fine=np.maximum(0,gray-gaussian_filter(gray,5))
 gold=np.clip(warm*.85+np.clip(fine*9,0,.85)*(sat<.27),0,1)
 gold*=np.clip((val-.22)*3,0,1)
 yy,xx=np.mgrid[:TH,:TW]; u=xx/TW; v=yy/TH
 border=(u<.028)|(u>.974)|(v<.018)|(v>.983)
 gold[border]=np.maximum(gold[border],.72)
 if si==2:
  plaque=(u>.588)&(u<.973)&(v>.839)&(v<.979)
  gold[plaque & (val>.2)]=.98
 pink=(r>g*1.16)&(bl>g*1.05)&(r>.27)&(val<.9)
 gold[pink]*=.15
 # Subtle cleanup of captured photographic shading; preserve stone pattern and inscriptions.
 base=rgb.copy()
 target=np.stack([np.clip(gray*1.10+.10,0,1),np.clip(gray*.83+.065,0,1),np.clip(gray*.42+.025,0,1)],2)
 base=base*(1-gold[...,None]*.48)+target*gold[...,None]*.48
 rough=np.clip(.34-gold*.15, .17,.4)
 rough[pink]=.20
 pearl=((sat<.20)&(val>.58)&(~border)).astype(np.float32)
 # Iridescence is local to pale nacre, never applied to the complete card.
 pearl=gaussian_filter(pearl,1)*.33*(1-gold)
 Image.fromarray(np.uint8(np.clip(base,0,1)*255)).save(P/f'textures/side{si}-base.jpg',quality=96,subsampling=0)
 Image.fromarray(np.uint8(gold*255)).save(P/f'textures/side{si}-metal.png')
 Image.fromarray(np.uint8(rough*255)).save(P/f'textures/side{si}-rough.png')
 Image.fromarray(np.uint8(pearl*255)).save(P/f'textures/side{si}-pearl.png')
 normal=Image.open(P/f'source/side_{si}_3d.png').convert('RGB').resize((TW,TH),Image.Resampling.LANCZOS)
 normal.save(P/f'textures/side{si}-normal.png')
 # Recover only high-frequency relief from the supplied tangent-space normal field.
 nn=np.array(normal.resize((W,H)),dtype=float)/127.5-1
 px=-nn[:,:,0]/np.maximum(nn[:,:,2],.3); py=nn[:,:,1]/np.maximum(nn[:,:,2],.3)
 ky=2*np.pi*np.fft.fftfreq(H)[:,None]; kx=2*np.pi*np.fft.fftfreq(W)[None,:]
 den=kx*kx+ky*ky; den[0,0]=1
 z=np.fft.ifft2((-1j*kx*np.fft.fft2(px)-1j*ky*np.fft.fft2(py))/den).real
 z=z-gaussian_filter(z,18)
 z=np.clip(z/np.percentile(np.abs(z),97),-1,1)
 gm=cv2.resize(gold,(W,H)); pm=cv2.resize(pink.astype(float),(W,H))
 height=.04+.10*gm+.055*z+.035*gaussian_filter(pm,2)
 heights.append(np.clip(height,.012,.22).astype(np.float32))
 # Round settings: conservative color/contrast filtering after Hough detection.
 small=cv2.resize(im,(W,H)); gray8=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
 circles=cv2.HoughCircles(cv2.GaussianBlur(gray8,(3,3),.6),cv2.HOUGH_GRADIENT,1.2,13,param1=85,param2=22,minRadius=6,maxRadius=19)
 gems=[]
 localmask=mask if si==1 else mask[::-1]
 if circles is not None:
  for x,y,rad in circles[0]:
   x,y=int(x),int(y)
   if not(32<x<W-32 and 32<y<H-32):continue
   patch=small[max(0,y-3):y+4,max(0,x-3):x+4].astype(float)/255
   cr,cg,cb=np.median(patch.reshape(-1,3),axis=0)
   disc=gray8[max(0,y-int(rad)):y+int(rad)+1,max(0,x-int(rad)):x+int(rad)+1]
   is_pink=cr>cg*1.1 and cb>cg*1.01 and cr>.3
   is_diamond=(max(cr,cg,cb)-min(cr,cg,cb)<.14 and disc.std()>40 and np.percentile(disc,85)>195)
   if is_diamond:
    ux=x/W;vy=y/H
    rows = ((ux<.34 and vy<.109) or (ux>.45 and vy>.81 and vy>(1.10-.30*ux))) if si==1 else ((ux>.47 and vy<.18 and vy<(.31-.19*ux)) or (ux<.34 and vy>.872))
    is_diamond=rows and rad<12
   if localmask[y,x] or not(is_pink or is_diamond):continue
   gems.append([x/W,y/H,rad/W*BW*.78, 'ruby' if is_pink else 'diamond'])
 gemsets.append(gems)
 print('Side',si,'gems',len(gems),flush=True)
 # Save an evidence overlay for visual verification of placement.
 ov=small.copy()
 for x,y,rad,kind in gems:cv2.circle(ov,(int(x*W),int(y*H)),int(rad/BW*W),(255,40,130) if kind=='ruby' else (0,225,255),1)
 Image.fromarray(ov).resize((640,1020)).save(P/f'output/gems-side{si}.jpg')

# Create one common perforated body, including preserved islands in the cutouts.
contours,hierarchy=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
def polycoords(c):
 c=cv2.approxPolyDP(c,.9,True)[:,0,:]
 return [(float(x)/W*BW-BW/2,BH/2-float(y)/H*BH) for x,y in c]
holes=[]
for i,c in enumerate(contours):
 if hierarchy[0,i,3]!=-1 or cv2.contourArea(c)<160:continue
 inn=[]; child=hierarchy[0,i,2]
 while child!=-1:
  if len(contours[child])>=3:inn.append(polycoords(contours[child]))
  child=hierarchy[0,child,0]
 p=Polygon(polycoords(c),inn).buffer(0)
 if not p.is_empty:holes.append(p)
radius=3.18
outer=box(-BW/2+radius,-BH/2+radius,BW/2-radius,BH/2-radius).buffer(radius,quad_segs=32)
body=outer.difference(unary_union(holes)).buffer(0)
# Tiny photographed islands receive narrow gold supports rather than floating in space.
support_count=0
if body.geom_type=='MultiPolygon':
 parts=sorted(body.geoms,key=lambda p:p.area,reverse=True); main=parts[0]
 for part in parts[1:]:
  if part.area<.008:continue
  p1,p2=nearest_points(main,part)
  bridge=LineString([p1,p2]).buffer(.045,cap_style=1)
  main=unary_union([main,part,bridge]).buffer(.0001)
  support_count+=1
 body=main
if body.geom_type!='Polygon':raise RuntimeError('Body must be connected')
verts=[];segments=[];seeds=[]
def ring(coords):
 pts=list(coords)[:-1]; off=len(verts); verts.extend(pts)
 segments.extend([(off+i,off+(i+1)%len(pts)) for i in range(len(pts))])
ring(body.exterior.coords)
for inner in body.interiors:
 ring(inner.coords);pt=Polygon(inner).representative_point();seeds.append((pt.x,pt.y))
mesh=triangle.triangulate(dict(vertices=verts,segments=segments,holes=seeds),'pq24a0.035')
v=mesh['vertices']; tris=mesh['triangles']; seg=mesh['segments']
# Consistent CCW triangles in physical XY.
tri=v[tris]; e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];cross=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];tris[cross<0]=tris[cross<0,::-1]
ix=(v[:,0]/BW+.5)*W; iy=(.5-v[:,1]/BH)*H
zf=map_coordinates(heights[0],[iy,ix],order=1,mode='nearest')
zb=map_coordinates(heights[1],[H-1-iy,ix],order=1,mode='nearest')
# Smooth the face height into the continuous gold sidewalls at all boundaries.
bound=np.unique(seg);zf[bound]=.04;zb[bound]=.04
np.savez_compressed(P/'output/geometry.npz',vertices=v,triangles=tris,segments=seg,front_height=zf,back_height=zb)
(P/'output/gems.json').write_text(json.dumps(gemsets,default=float))
metrics={'width_mm':BW,'height_mm':BH,'corner_radius_mm':radius,'core_thickness_mm':.76,'cutout_count':len(body.interiors),'support_bridges':support_count,'cutout_area_percent':round((outer.area-body.area)/outer.area*100,2),'surface_triangles_per_side':len(tris),'gemstones_per_side':[len(x) for x in gemsets], 'reconstruction':'Photographic interpretation; material species and relief depths are not measured.'}
(P/'output/metrics.json').write_text(json.dumps(metrics,indent=2))
print(metrics,flush=True)



