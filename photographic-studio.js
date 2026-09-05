import * as THREE from 'three';

export function createStudio(scene,renderer,software){
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;
 renderer.shadowMap.autoUpdate=false;
 const key=new THREE.SpotLight(0xfff3df,.11,1,Math.PI*.30,.8,2);
 key.name='Upper right photographic softbox';key.position.set(.095,.145,.12);key.target.position.set(0,-.01,0);
 key.castShadow=true;key.shadow.mapSize.set(software?1024:2048,software?1024:2048);
 key.shadow.camera.near=.025;key.shadow.camera.far=.45;key.shadow.bias=-.00002;key.shadow.normalBias=.000045;
 key.shadow.radius=3.5;key.shadow.focus=.8;scene.add(key,key.target);
 const fill=new THREE.DirectionalLight(0xdce9ff,.14);fill.position.set(-.12,.04,.08);scene.add(fill);
 // A continuous cyclorama: actual horizontal floor, rolled corner and rear wall.
 const floorY=-.056,width=.8;
 const path=[[.4,floorY],[-.065,floorY]];
 const radius=.10;
 for(let i=1;i<=48;i++){const a=i/48*Math.PI/2;path.push([-.065-radius*Math.sin(a),floorY+radius*(1-Math.cos(a))]);}
 path.push([-.165,.55]);
 const vertices=[],indices=[];
 path.forEach(([z,y])=>vertices.push(-width/2,y,z,width/2,y,z));
 for(let i=0;i<path.length-1;i++){const a=i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.setIndex(indices);geometry.computeVertexNormals();
 const material=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.91,metalness:.025,side:THREE.FrontSide});
 const uniforms={studioBase:{value:new THREE.Color('#0d1015')},studioVein:{value:new THREE.Color('#494238')},studioStyle:{value:0}};
 material.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,uniforms);
  shader.vertexShader='varying vec3 vStudioPosition;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvStudioPosition=position;');
  shader.fragmentShader='varying vec3 vStudioPosition;uniform vec3 studioBase;uniform vec3 studioVein;uniform float studioStyle;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
   vec2 p=vStudioPosition.xy*22.0+vStudioPosition.xz*vec2(7.0,11.0);
   float folds=sin(p.x*2.8+p.y*.5+sin(p.y*.9)*.7)*.5+.5;
   float veins=pow(.5+.5*sin(p.x*4.0+p.y*2.3+sin(p.y*3.7)*1.6+sin(p.x*2.1)*.9),22.0);
   float grain=fract(sin(dot(vStudioPosition.xz*1900.0+vStudioPosition.xy*2400.0,vec2(12.9898,78.233)))*43758.5453)-.5;
   float stoneBands=.5+.5*sin(p.y*52.0+sin(p.x*1.2)*.18);
   float pattern=folds*.10;
   if(studioStyle>.5)pattern=stoneBands*.023+veins*.017;
   if(studioStyle>1.5)pattern=veins*.08;
   float upperGlow=exp(-pow((vStudioPosition.x-.095)*8.0,2.0)-pow((vStudioPosition.y-.13)*6.0,2.0));
   diffuseColor.rgb=mix(studioBase,studioVein,pattern)+studioBase*(upperGlow*.25+grain*.018);
  `);
 };
 const backdrop=new THREE.Mesh(geometry,material);backdrop.name='Curved studio floor and backdrop';backdrop.receiveShadow=true;scene.add(backdrop);
 const themes={dark:['#0d1015','#24282d',0],sand:['#97816b','#d3c0a2',1],light:['#c7c5bc','#787e7b',2]};
 function setTheme(name){const t=themes[name]||themes.dark;uniforms.studioBase.value.set(t[0]);uniforms.studioVein.value.set(t[1]);uniforms.studioStyle.value=t[2];scene.background.set(t[0]);}
 function update(){renderer.shadowMap.needsUpdate=true;}
 setTheme('dark');return {setTheme,update,key,backdrop};
}
