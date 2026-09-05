import * as THREE from 'three';

// A decorative celestial object in scene space, with depth and a sunlit surface.
export function createLunarBackdrop(scene,renderer){
 const group=new THREE.Group();group.name='Lunar backdrop · dark studio';scene.add(group);
 const loader=new THREE.TextureLoader();
 const color=loader.load('assets/moon/lroc-color.jpg');color.colorSpace=THREE.SRGBColorSpace;color.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
 const height=loader.load('assets/moon/lola-height.jpg');height.colorSpace=THREE.NoColorSpace;
 const material=new THREE.MeshStandardMaterial({map:color,bumpMap:height,bumpScale:.00010,color:0xdadee1,metalness:0,roughness:1,envMapIntensity:0});
 material.onBeforeCompile=shader=>{
  // A separate distant sunlight direction illuminates the Moon without changing the jewellery lights.
  shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`
   vec3 lunarNormal=inverseTransformDirection(normal,viewMatrix);
   float lunarSun=max(dot(lunarNormal,normalize(vec3(-.62,.38,1.))),0.);
   outgoingLight=diffuseColor.rgb*(.035+1.45*lunarSun);
   #include <opaque_fragment>`);
 };
 material.customProgramCacheKey=()=> 'rosan-lunar-sun-1';
 const moon=new THREE.Mesh(new THREE.SphereGeometry(.044,128,96),material);moon.name='Moon · NASA LROC / LOLA';moon.rotation.set(.10,Math.PI*.54,-.15);group.add(moon);
 // Sparse fixed stars provide depth cues; they are never attached to the camera.
 let seed=4137;function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
 const points=[];for(let i=0;i<130;i++){const y=rand()*2-1,a=rand()*Math.PI*2,r=Math.sqrt(1-y*y);points.push(.64*r*Math.cos(a),.64*y,.64*r*Math.sin(a));}
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
 const stars=new THREE.Points(geo,new THREE.PointsMaterial({color:0xdadee1,size:.00065,transparent:true,opacity:.22,depthWrite:false,toneMapped:false}));stars.name='Quiet stellar field';group.add(stars);
 function update(angle=0){
  // The shallow, continuous 3D arc is coupled to the card's accumulated spin.
  // It is a presentation motion, not a simulated astronomical orbit.
  const phase=angle*.45;moon.position.set(.055+.027*Math.cos(phase),.043+.016*Math.sin(phase),-.35+.018*Math.sin(phase*.8));
 }
 update();return {group,moon,update};
}
