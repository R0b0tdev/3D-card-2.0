from pathlib import Path
import hashlib,json
p=Path('/home/vetal/projects/3D_CARDS/exhibition')
proof=json.loads((p/'output/rim-cleanup-protected-assets.json').read_text())
changed=[name for name,digest in proof.items() if hashlib.sha256((p/name).read_bytes()).hexdigest()!=digest]
assert not changed,changed
m=json.loads((p/'output/metrics.json').read_text())
assert m['shell_nonmanifold_edges']==0
r=p/'README.md';s=r.read_text(encoding='utf-8-sig').replace('22 отверстия занимают приблизительно 2,83% площади карты.','24 отверстия занимают приблизительно 4,68% площади карты.').replace('все 22 выреза','все вырезы')
s+='\n## Очистка остатков белого фона\n\nПо новой разметке пользователя уточнены только центральные отверстия. Границы доведены до оправ и сглажены периодическими кривыми; удалены белые колпачки, узкие светлые полосы и два малых остатка фона внутри орнамента. Проверены обе стороны. Исходные текстуры всех материалов и файл камней побайтно сохранены (11 защищённых файлов); корпус остаётся замкнутым. Исходное состояние геометрии сохранено в output/before-rim-cleanup. Для воспроизведения этой правки после prepare.py запустите clean_cutout_rims.py и rebuild_clean_cutouts.py, затем build_blender.py.\n'
r.write_text(s)
print({'protected_files_unchanged':len(proof),'cutouts':m['cutout_count'],'nonmanifold_edges':m['shell_nonmanifold_edges']})
