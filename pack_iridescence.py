from pathlib import Path
import struct,json
p=Path(__file__).parent
f=p/'output/jewellery-card.glb'
data=f.read_bytes();jl=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+jl]);bo=20+jl;bl=struct.unpack_from('<I',data,bo)[0];binary=bytearray(data[bo+8:bo+8+bl])
if 'KHR_materials_iridescence' not in doc.get('extensionsUsed',[]):
 doc.setdefault('extensionsUsed',[]).append('KHR_materials_iridescence')
 for side in [1,2]:
  blob=(p/f'textures/side{side}-pearl.png').read_bytes()
  while len(binary)%4:binary.append(0)
  start=len(binary);binary.extend(blob)
  bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(blob)})
  im=len(doc['images']);doc['images'].append({'name':f'Nacre mask {side}','bufferView':bv,'mimeType':'image/png'})
  ti=len(doc['textures']);doc['textures'].append({'source':im})
  mat=next(m for m in doc['materials'] if m['name'].startswith(f'Side {side}'))
  mat.setdefault('extensions',{})['KHR_materials_iridescence']={'iridescenceFactor':.52,'iridescenceIor':1.34,'iridescenceTexture':{'index':ti},'iridescenceThicknessMinimum':210,'iridescenceThicknessMaximum':420}
 doc['buffers'][0]['byteLength']=len(binary)
 while len(binary)%4:binary.append(0)
 j=json.dumps(doc,separators=(',',':')).encode()
 j+=b' '*((-len(j))%4)
 total=12+8+len(j)+8+len(binary)
 f.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
 metric=p/'output/metrics.json'
 if metric.exists():
  d=json.loads(metric.read_text());d['glb_bytes']=total;metric.write_text(json.dumps(d,indent=2))
 print('Packed portable nacre materials',total)
