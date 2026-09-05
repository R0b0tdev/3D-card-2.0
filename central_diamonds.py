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
# Build one convex round brilliant in radius-normalized optical coordinates.
import bmesh,numpy as np
bm=bmesh.new()
N=48
for z in [0,-.025]:
 for j in range(N):
  a=j*math.tau/N;bm.verts.new((math.cos(a),math.sin(a),z))
for j in range(8):
 a=j*math.tau/8
 bm.verts.new((.53*math.cos(a),.53*math.sin(a),.32))
 a+=math.pi/8
 star_z=.32/(1-.53)*(1-.78*math.cos(math.pi/8))
 bm.verts.new((.78*math.cos(a),.78*math.sin(a),star_z))
 bm.verts.new((.72*math.cos(a),.72*math.sin(a),-.30))
 bm.verts.new((.008*math.cos(a),.008*math.sin(a),-.86))
bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.verts.ensure_lookup_table();bm.verts.index_update()
unit=[tuple(v.co) for v in bm.verts];unitfaces=[tuple(v.index for v in f.verts) for f in bm.faces]
planes=[]
for f in bm.faces:
 n=f.normal;d=n.dot(f.verts[0].co)
 q=np.array([*n,d])
 if not any(np.linalg.norm(q-np.array(v))<1e-4 for v in planes):planes.append(q.tolist())
bm.free()
for ob in list(bpy.data.objects):
 if ob.name.startswith('03 • central brilliants'):bpy.data.objects.remove(ob,do_unlink=True)
mat=bpy.data.materials.get('Central brilliant • colourless diamond') or bpy.data.materials.new('Central brilliant • colourless diamond')
mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.985,.99,1,1)
bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.025
bs.inputs['IOR'].default_value=2.417;bs.inputs['Transmission Weight'].default_value=1
bs.inputs['Coat Weight'].default_value=0
shell=next(o for o in bpy.context.scene.objects if o.name.startswith('01 •'))
vv=[];ff=[];records=[];localuv=[]
for group,points in GROUPS.items():
 for cx,cy,rad in points:
  u=(260+cx/1.5)/1247;v=(690+cy/1.5)/1990
  x=(u-.5)*.05398;y=(v-.5)*.08560;r=rad/1.5/1247*.05398
  heights=[]
  for j in range(16):
   a=j*math.tau/16
   hit,loc,n,idx=shell.ray_cast(Vector((x+r*.94*math.cos(a),y+r*.94*math.sin(a),-.004)),Vector((0,0,1)))
   if hit:heights.append(-loc.z)
  base=max(heights,default=.00049)+.000002
  off=len(vv)
  for px,py,pz in unit:vv.append((x+r*px,y+r*py,-base-r*pz));localuv.append((px*.5+.5,py*.5+.5))
  ff.extend([tuple(off+i for i in reversed(face)) for face in unitfaces])
  records.append({'group':group,'u':u,'v':v,'radius_mm':r*1000,'crown_mm':r*.32*1000,'base_mm':base*1000})
mesh=bpy.data.meshes.new('25 recut round brilliants • thin girdle');mesh.from_pydata(vv,[],ff);mesh.materials.append(mat);mesh.update()
uv=mesh.uv_layers.new(name='Brilliant optical coordinates')
for loop in mesh.loops:uv.data[loop.index].uv=localuv[loop.vertex_index]
obj=bpy.data.objects.new('03 • central brilliants | logo side only',mesh);bpy.context.scene.collection.objects.link(obj)
obj['stone_count']=len(records);obj['photo_side']=2;obj['registration']=json.dumps(records);obj['optical_planes']=json.dumps(planes)
obj['cut']='Round brilliant: table, star facets, crown, thin girdle and pavilion'
(P/'output/central-diamonds.json').write_text(json.dumps(records,indent=2))
print('RECUT_BRILLIANTS',len(records),'optical planes',len(planes),'unit vertices',len(unit),flush=True)
