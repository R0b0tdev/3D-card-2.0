from pathlib import Path
import numpy as np, cv2, json, shutil, hashlib
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
from skimage.segmentation import inverse_gaussian_gradient, morphological_geodesic_active_contour
from scipy.interpolate import splprep,splev
P=Path(__file__).parent;W,H=1280,2040
backup=P/'output/before-rim-cleanup';backup.mkdir(exist_ok=True)
for name in ['geometry.npz','cutout-mask.png','metrics.json']:
 dst=backup/name
 if not dst.exists():shutil.copy2(P/'output'/name,dst)
old=np.array(Image.open(backup/'cutout-mask.png'))>0
im=np.array(Image.open(P/'source/side_1.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS))
gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY).astype(float)/255
count,lab,stats,cents=cv2.connectedComponentsWithStats(old.astype(np.uint8),8)
new=np.zeros_like(old)
# Start from each existing opening and follow the photographic rim locally.
# No new regions may be cut elsewhere in the card.
for k in range(1,count):
 x,y,w,h,area=stats[k]
 if area<60:continue
 margin=36;x0=max(0,x-margin);x1=min(W,x+w+margin);y0=max(0,y-margin);y1=min(H,y+h+margin)
 seed=lab[y0:y1,x0:x1]==k
 crop=gray[y0:y1,x0:x1]
 edge=inverse_gaussian_gradient(crop,alpha=650,sigma=1.2)
 domain=distance_transform_edt(~seed)<28
 occupied=(lab[y0:y1,x0:x1]>0)&(~seed)
 domain[cv2.dilate(occupied.astype(np.uint8),np.ones((5,5),np.uint8))>0]=False
 def limit(level):level[~domain]=0
 evolved=morphological_geodesic_active_contour(edge,60,init_level_set=seed,smoothing=2,threshold=.30,balloon=1,iter_callback=limit)>0
 evolved|=seed
 # Smoothing only the cutout contour, leaving the surrounding texture and gemstones untouched.
 cs,_=cv2.findContours(evolved.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
 if not cs:continue
 c=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
 c=cv2.approxPolyDP(c.astype(np.float32),.45,True)[:,0,:].astype(float)
 if len(c)>5:
  try:
   tck,u=splprep(c.T,s=len(c)*.65,per=True)
   per=cv2.arcLength(c.astype(np.float32),True)
   c=np.array(splev(np.linspace(0,1,max(40,int(per*2)),endpoint=False),tck)).T
  except ValueError:pass
 sm=np.zeros_like(seed,dtype=np.uint8);cv2.fillPoly(sm,[np.int32(np.round(c))],1)
 sm[~domain]=0
 new[y0:y1,x0:x1]|=sm>0
# Keep components separated by at least a narrow gold bridge.
Image.fromarray(new.astype(np.uint8)*255).save(P/'output/cutout-mask-proposed.png')
over=im.copy();over[new]=(over[new]*.25+np.array([0,205,240])*.75).astype(np.uint8)
Image.fromarray(over).resize((640,1020)).save(P/'output/clean-cutout-review.jpg')
added=new&~old
print({'old_pixels':int(old.sum()),'new_pixels':int(new.sum()),'added_pixels':int(added.sum()),'max_growth_px':float(distance_transform_edt(~old)[added].max())},flush=True)

