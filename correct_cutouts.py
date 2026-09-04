from pathlib import Path
p=Path('/home/vetal/projects/3D_CARDS/exhibition/prepare.py')
s=p.read_text(encoding='utf-8-sig')
a=s.index('# User-specified milky background areas:');b=s.index('Image.fromarray(mask*255)',a)
s=s[:a]+'''# Corrected from the user's red annotation: ONLY the diagonal ivory fan / scroll band.
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
''' +s[b:]
p.write_text(s)
# Fast mask-only review before the heavy rebuild.
exec(compile(s[:s.index('# Produce PBR maps')],str(p),'exec'),{'__file__':str(p)})
