import bpy, numpy as np, math, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='CYCLES';scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.view_settings.view_transform='AgX'

def basic(name,col,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*col,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 return m,s

gold,gs=basic('Au • polished yellow gold',(.83,.53,.16),1,.135)
gs.inputs['Coat Weight'].default_value=.08
gs.inputs['Coat Roughness'].default_value=.09
ruby,rs=basic('Rose pink gemstone • interpreted material',(.23,.032,.07),0,.19)
rs.inputs['IOR'].default_value=1.76;rs.inputs['Transmission Weight'].default_value=.22;rs.inputs['Coat Weight'].default_value=.5
rs.inputs['Coat Roughness'].default_value=.1
diamond,ds=basic('Diamond • faceted optical material',(.88,.94,1),0,.065)
ds.inputs['IOR'].default_value=2.417;ds.inputs['Transmission Weight'].default_value=.65

def textured(si):
 m,s=basic(f'Side {si} • gold / nacre / mineral inlay',(.8,.7,.5),0,.3)
 n=m.node_tree.nodes;l=m.node_tree.links
 def tex(suffix,noncolor=True):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/f'textures/side{si}-{suffix}'),check_existing=True)
  if noncolor:t.image.colorspace_settings.name='Non-Color'
  return t
 l.new(tex('base.jpg',False).outputs['Color'],s.inputs['Base Color'])
 l.new(tex('metal.png').outputs['Color'],s.inputs['Metallic'])
 l.new(tex('rough.png').outputs['Color'],s.inputs['Roughness'])
 no=n.new('ShaderNodeNormalMap');no.inputs['Strength'].default_value=.62;l.new(tex('normal.png').outputs['Color'],no.inputs['Color']);l.new(no.outputs['Normal'],s.inputs['Normal'])
 s.inputs['Coat Weight'].default_value=.23;s.inputs['Coat Roughness'].default_value=.21
 film=n.new('ShaderNodeMath');film.operation='MULTIPLY';film.inputs[1].default_value=1100;l.new(tex('pearl.png').outputs['Color'],film.inputs[0]);l.new(film.outputs[0],s.inputs['Thin Film Thickness']);s.inputs['Thin Film IOR'].default_value=1.36
 # Keep a named mask for richer per-pixel nacre in the web viewer.
 m['nacre_mask']=f'textures/side{si}-pearl.png'
 return m
edge_gold,edge_shader=basic('Au edge • softly polished yellow gold',(.83,.53,.16),1,.30)
edge_shader.inputs['Coat Weight'].default_value=0
mats=[textured(1),textured(2),edge_gold]
g=np.load(P/'output/geometry.npz');xy=g['vertices'];tri=g['triangles'];N=len(xy)
zf=.38+g['front_height'];zb=-.38-g['back_height']
verts=np.concatenate([np.column_stack([xy,zf]),np.column_stack([xy,zb])])/1000
faces=tri.tolist()+(tri[:,::-1]+N).tolist()
# Recover oriented boundary edges from the triangulation for a watertight shell.
all_edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);keys=np.sort(all_edges,axis=1)
_,ids,counts=np.unique(keys,axis=0,return_index=True,return_counts=True)
edge=all_edges[ids[counts==1]]
faces.extend([[int(b),int(a),int(a+N),int(b+N)] for a,b in edge])
me=bpy.data.meshes.new('Watertight rounded perforated card shell');me.from_pydata(verts.tolist(),[],faces);me.update()
ob=bpy.data.objects.new('01 • jewellery card | 53.98 × 85.60 mm',me);scene.collection.objects.link(ob)
for m in mats:me.materials.append(m)
nt=len(tri)
material_ids=np.concatenate([np.zeros(nt,dtype=int),np.ones(nt,dtype=int),np.full(len(edge),2)])
me.polygons.foreach_set('material_index',material_ids)
uv=me.uv_layers.new(name='Photograph UV')
loops=np.array([l.vertex_index for l in me.loops]);coords=verts[loops]*1000
uvs=np.column_stack([coords[:,0]/53.98+.5,coords[:,1]/85.6+.5])
uvs[loops>=N,1]=1-uvs[loops>=N,1]
uv.data.foreach_set('uv',uvs.ravel())
# Analytic constant-radius shoulders with a smooth relief transition.
import bmesh
from mathutils.kdtree import KDTree
samples=[]
segments=[]
for a,b in edge:
 pa,pb=xy[a]/1000,xy[b]/1000
 outer=int(abs(pa[0])>.024 or abs(pa[1])>.039)
 segments.append((pa,pb,outer))
 count=max(2,int(np.linalg.norm(pb-pa)/.000012)+1)
 for t in np.linspace(0,1,count):
  q=pa*(1-t)+pb*t;samples.append((float(q[0]),float(q[1]),len(segments)-1))
kd=KDTree(len(samples))
for i,(x,y,seg) in enumerate(samples):kd.insert((x,y,0),i)
kd.balance()
def proximity(v):
 # Project onto the actual segment: distance must not ripple between samples.
 q,ix,d=kd.find((v.co.x,v.co.y,0))
 pa,pb,outer=segments[samples[ix][2]]
 dx,dy=pb-pa;vx=v.co.x-pa[0];vy=v.co.y-pa[1]
 t=max(0.,min(1.,(vx*dx+vy*dy)/(dx*dx+dy*dy)))
 return math.hypot(vx-t*dx,vy-t*dy),outer
bm=bmesh.new();bm.from_mesh(me)
near={v:proximity(v)[0] for v in bm.verts}
refine=[e for e in bm.edges if (e.verts[0].co.z*e.verts[1].co.z>0 and min(near[e.verts[0]],near[e.verts[1]])<.00065) or abs(e.verts[0].co.z-e.verts[1].co.z)>.0006]
bmesh.ops.subdivide_edges(bm,edges=refine,cuts=5,use_grid_fill=True)
rolled=0;rim_vertices=set()
for v in bm.verts:
 d,is_outer=proximity(v)
 radius=.00030 if is_outer else .00018
 transition=.00065 if is_outer else .00030
 oldz=abs(v.co.z);sign=1 if v.co.z>=0 else -1
 if d<transition:
  if d<1e-9:
   # Sidewall points retain their order along the thickness.
   z=oldz*(.00042-radius)/.00042
  elif d<radius:
   z=.00042-radius+math.sqrt(max(0,radius*radius-(radius-d)**2))
  else:
   t=min(1.,(d-radius)/(transition-radius))
   blend=t*t*t*(10+t*(-15+6*t))
   z=.00042+(oldz-.00042)*blend
  v.co.z=sign*z;rolled+=1
 if d<radius:rim_vertices.add(v)
for face in bm.faces:
 if all(v in rim_vertices for v in face.verts):face.material_index=2
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for face in bm.faces:face.smooth=True
bm.to_mesh(me);bm.free();me.update()
ob['outer_roll_radius_mm']=.30;ob['cutout_roll_radius_mm']=.18
ob['rounded_rim_vertices']=rolled
print('ROUNDED_RIMS',rolled,'vertices',len(me.vertices),flush=True)
ob['core_thickness_mm']=.76;ob['corner_radius_mm']=3.18;ob['reverse_orientation']='180 degrees around horizontal X axis'
ob['note']='Photo-derived presentation reconstruction. Cutouts share a common physical boundary on both sides.'

# Batch gemstone and bezel geometry for efficient browser rendering.
gemsets=json.loads((P/'output/gems.json').read_text())
batches={k:([],[]) for k in ['ruby','diamond','bezels']}
def append(name,v,f):
 vv,ff=batches[name];off=len(vv);vv.extend(v);ff.extend([[off+i for i in face] for face in f])
for side,gems in enumerate(gemsets):
 sign=1 if side==0 else -1
 for u,v,r,kind in gems:
  x=(u-.5)*53.98;y=(.5-v)*85.6*sign
  z=sign*.49
  n=16 if kind=='ruby' else 8
  # A closed faceted stone: pavilion, girdle, crown, and table.
  rings=[(.18,-.09),(.93,0),(1,.045),(.66,.22),(.36,.28)] if kind=='ruby' else [(.05,-.22),(.99,0),(1,.025),(.46,.22)]
  vv=[]
  for rr,zz in rings:
   for j in range(n):
    a=2*math.pi*j/n
    vv.append(((x+r*rr*math.cos(a))/1000,(y+r*rr*math.sin(a))/1000,(z+sign*zz)/1000))
  ff=[]
  ff.append(tuple(range(n-1,-1,-1)))
  for k in range(len(rings)-1):
   for j in range(n):
    a=k*n+j;b=k*n+(j+1)%n;c=b+n;d=a+n
    if kind=='ruby':ff.extend([(a,b,c),(a,c,d)])
    else:ff.append((a,b,c,d))
  ff.append(tuple(range((len(rings)-1)*n,len(rings)*n)))
  if sign<0:ff=[tuple(reversed(f)) for f in ff]
  append(kind,vv,ff)
  vv=[];ff=[];ns,ms=20,6;tube=.035
  for j in range(ns):
   a=2*math.pi*j/ns
   for k in range(ms):
    b=2*math.pi*k/ms;rad=r*1.02+tube*math.cos(b)
    vv.append(((x+rad*math.cos(a))/1000,(y+rad*math.sin(a))/1000,(z+sign*(.025+tube*math.sin(b)))/1000))
  for j in range(ns):
   for k in range(ms):ff.append((j*ms+k,((j+1)%ns)*ms+k,((j+1)%ns)*ms+(k+1)%ms,j*ms+(k+1)%ms))
  if sign<0:ff=[tuple(reversed(f)) for f in ff]
  append('bezels',vv,ff)
for name,(vv,ff) in batches.items():
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vv,[],ff);mesh.materials.append({'ruby':ruby,'diamond':diamond,'bezels':gold}[name]);mesh.update()
 obj=bpy.data.objects.new('02 • '+name,mesh);scene.collection.objects.link(obj)
 for f in mesh.polygons:f.use_smooth=name=='bezels'

exec(compile((P/'central_diamonds.py').read_text(encoding='utf-8-sig'),'central_diamonds.py','exec'),{'__file__':str(P/'central_diamonds.py')})

# Camera and an actual studio lighting rig for editing/rendering in Blender.
world=bpy.data.worlds.new('Warm charcoal studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35

def aim(obj,p=(0,0,0)):obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,sy):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='RECTANGLE';data.size=size;data.size_y=sy
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;aim(obj)
area('Softbox • ivory key',(-.075,.065,.12),.48,(1,.9,.76),.09,.15)
area('Softbox • cool edge',(.065,.025,.06),.24,(.72,.84,1),.022,.15)
area('Softbox • top highlight',(0,.12,.02),.36,(1,.98,.91),.12,.012)
area('Softbox • back',(-.07,-.02,-.09),.36,(1,.86,.64),.08,.15)
camd=bpy.data.cameras.new('Presentation camera');cam=bpy.data.objects.new('Presentation camera',camd);scene.collection.objects.link(cam);cam.location=(.062,.027,.18);camd.type='ORTHO';camd.ortho_scale=.115;cam.rotation_euler=(.13,-.29,0);cam.location=cam.rotation_euler.to_matrix() @ Vector((0,0,.19));scene.camera=cam
scene.render.resolution_x=1350;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
# Save self-contained master with the photographic maps packed inside.
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH':o.select_set(True)
bpy.context.view_layer.objects.active=ob
bpy.ops.wm.save_as_mainfile(filepath=str(P/'output/jewellery-card.blend'))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'output/jewellery-card.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'output/jewellery-card.glb'),export_format='GLB',use_selection=True,export_yup=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_extras=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_texcoord_quantization=14)
exec(compile((P/'pack_iridescence.py').read_text(encoding='utf-8-sig'),str(P/'pack_iridescence.py'),'exec'),{'__file__':str(P/'pack_iridescence.py'),'__name__':'__main__'})
# Shell manifold and material evidence.
import bmesh
bm=bmesh.new();bm.from_mesh(me)
report=json.loads((P/'output/metrics.json').read_text());report['shell_nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges);report['blender_version']=bpy.app.version_string
report['outer_roll_radius_mm']=.30;report['cutout_roll_radius_mm']=.18;report['rounded_rim_vertices']=rolled
report['total_mesh_vertices']=sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH');report['glb_bytes']=(P/'output/jewellery-card.glb').stat().st_size
(P/'output/metrics.json').write_text(json.dumps(report,indent=2));bm.free()
print('BUILD_COMPLETE',report,flush=True)
scene.render.filepath=str(P/'output/studio-front.png')
bpy.ops.render.render(write_still=True)





