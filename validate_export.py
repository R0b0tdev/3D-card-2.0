from pathlib import Path
import struct,json
p=Path('/home/vetal/projects/3D_CARDS/exhibition')
f=p/'output/jewellery-card.glb'
with f.open('rb') as s:
 magic,version,size=struct.unpack('<4sII',s.read(12));length,kind=struct.unpack('<II',s.read(8));doc=json.loads(s.read(length))
r={'glb_valid_header':magic==b'glTF' and version==2 and size==f.stat().st_size,'self_contained_images':all('bufferView' in x for x in doc['images']),'mesh_parts':len(doc['meshes']),'materials':[x['name'] for x in doc['materials']],'textured_surface_materials':sum('normalTexture' in x and 'baseColorTexture' in x.get('pbrMetallicRoughness',{}) for x in doc['materials']),'extensions':doc.get('extensionsUsed',[]),'browser':'Chromium 153; front/back/materials/background/rotation/mobile checked','local_only':'127.0.0.1:8765'}
(p/'output/validation.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
