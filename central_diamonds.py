"""Add hand-registered round brilliant geometry on photo side 2 only."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent
# Centres/radii measured on a 675 x 840 review crop of side_2:
# full reference 1247 x 1990, crop origin (260,690), review scale 1.5.
GROUPS={
 'upper_fan':[(587,59,18),(629,39,18),(625,85,18)],
 'upper_chain':[(423,129,13),(480,144,12),(541,129,18),(573,153,18),(534,174,13),(575,215,13),(605,267,13)],
 'upper_scroll':[(448,283,20),(421,319,17)],
 'flower':[(334,438,19)],
 'lower_scroll':[(253,556,17),(225,590,21)],
 'lower_chain':[(56,582,12),(83,634,12),(123,679,12),(123,729,18),(171,715,13),(223,741,12),(279,755,12)],
 'lower_fan':[(60,778,17),(53,819,17),(95,804,17)]}
for ob in list(bpy.data.objects):
 if ob.name.startswith('03 • central brilliants'):bpy.data.objects.remove(ob,do_unlink=True)
mat=bpy.data.materials.get('Central brilliant • colourless diamond')
if mat is None:mat=bpy.data.materials.new('Central brilliant • colourless diamond')
mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.94,.97,1,1)
bs.inputs['Metallic'].default_value=0
bs.inputs['Roughness'].default_value=.035
bs.inputs['IOR'].default_value=2.417
bs.inputs['Transmission Weight'].default_value=.88
bs.inputs['Coat Weight'].default_value=.10
bs.inputs['Coat Roughness'].default_value=.025
shell=next(o for o in bpy.context.scene.objects if o.name.startswith('01 •'))
vv=[];ff=[];records=[]
for group,points in GROUPS.items():
 for cx,cy,rad in points:
  u=(260+cx/1.5)/1247;v=(690+cy/1.5)/1990
  x=(u-.5)*.05398;y=(v-.5)*.08560;r=rad/1.5/1247*.05398
  # Seat each girdle on the existing local relief without altering the gold.
  heights=[]
  for j in range(9):
   a=j*math.tau/8;rr=0 if j==8 else r*.7
   hit,loc,n,idx=shell.ray_cast(Vector((x+rr*math.cos(a),y+rr*math.sin(a),-.004)),Vector((0,0,1)))
   if hit:heights.append(-loc.z)
  base=max(heights,default=.00049)+.000008
  crown=min(.00028,max(.00018,r*.48))
  off=len(vv);N=64
  # Round 64-sided girdle; sixteen optical sectors, star/lower-crown facets.
  rings=[(.06,-r*.50),(1,0),(1,.000025),(.80,crown*.48),(.48,crown)]
  for k,(rr,h) in enumerate(rings):
   for j in range(N):
    a=j*math.tau/N
    if k>=3:
     sector=j//4;t=(j%4)/4
     a0=sector*math.tau/16;a1=(sector+1)*math.tau/16
     px=(1-t)*math.cos(a0)+t*math.cos(a1);py=(1-t)*math.sin(a0)+t*math.sin(a1)
     if k==3:hlocal=h*(1.12 if j%4==0 else .94)
     else:hlocal=h
    else:px=math.cos(a);py=math.sin(a);hlocal=h
    vv.append((x+r*rr*px,y+r*rr*py,-base-hlocal))
  local=[tuple(range(N-1,-1,-1))]
  for k in range(len(rings)-1):
   for j in range(N):
    a=k*N+j;b=k*N+(j+1)%N;c=b+N;d=a+N
    if k>=2:local.extend([(a,b,c),(a,c,d)])
    else:local.append((a,b,c,d))
  local.append(tuple(range((len(rings)-1)*N,len(rings)*N)))
  ff.extend([tuple(off+i for i in reversed(face)) for face in local])
  records.append({'group':group,'u':u,'v':v,'radius_mm':r*1000,'crown_mm':crown*1000,'base_mm':base*1000})
mesh=bpy.data.meshes.new('25 round central brilliants • side 2');mesh.from_pydata(vv,[],ff);mesh.materials.append(mat);mesh.update()
uv=mesh.uv_layers.new(name='Brilliant optical coordinates')
for loop in mesh.loops:
 rec=records[loop.vertex_index//320];co=mesh.vertices[loop.vertex_index].co
 cx=(rec['u']-.5)*.05398;cy=(rec['v']-.5)*.08560;radius=rec['radius_mm']/1000
 uv.data[loop.index].uv=((co.x-cx)/radius*.5+.5,(co.y-cy)/radius*.5+.5)
obj=bpy.data.objects.new('03 • central brilliants | logo side only',mesh);bpy.context.scene.collection.objects.link(obj)
obj['stone_count']=len(records);obj['photo_side']=2;obj['registration']=json.dumps(records)
(P/'output/central-diamonds.json').write_text(json.dumps(records,indent=2))
print('CENTRAL_DIAMONDS',len(records),flush=True)
