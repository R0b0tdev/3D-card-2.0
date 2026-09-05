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
 // A closed, inward-facing backdrop surrounds every permitted camera position.
 // Lighting for the jewellery remains independent of the decorative background.
 const uniforms={pastelLow:{value:new THREE.Color()},pastelHigh:{value:new THREE.Color()},composition:{value:1},compositionStrength:{value:.18},textureStrength:{value:.4}};
 const material=new THREE.MeshBasicMaterial({side:THREE.BackSide,depthWrite:false,toneMapped:false});
 material.onBeforeCompile=shader=>{
  Object.assign(shader.uniforms,uniforms);
  shader.vertexShader='varying vec3 studioPosition;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nstudioPosition=(modelMatrix*vec4(position,1.)).xyz;');
  shader.fragmentShader='varying vec3 studioPosition;uniform vec3 pastelLow;uniform vec3 pastelHigh;uniform float composition;uniform float compositionStrength;uniform float textureStrength;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('void main() {',`
   float stoneHash(vec3 p){p=fract(p*.1031);p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z);}
   float stoneNoise(vec3 p){
    vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
    return mix(mix(mix(stoneHash(i),stoneHash(i+vec3(1,0,0)),f.x),mix(stoneHash(i+vec3(0,1,0)),stoneHash(i+vec3(1,1,0)),f.x),f.y),mix(mix(stoneHash(i+vec3(0,0,1)),stoneHash(i+vec3(1,0,1)),f.x),mix(stoneHash(i+vec3(0,1,1)),stoneHash(i+vec3(1,1,1)),f.x),f.y),f.z);
   }
   float stoneFbm(vec3 p){return .57*stoneNoise(p)+.28*stoneNoise(p*2.03+7.1)+.15*stoneNoise(p*4.11+13.7);}
   void main() {`);
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
   vec3 d=normalize(studioPosition);
   float wash=.5+.24*d.y+.12*d.x+.10*d.z;
   diffuseColor.rgb=mix(pastelLow,pastelHigh,smoothstep(0.,1.,wash));
   vec2 p=studioPosition.xy*2.0;
   float halo=exp(-dot(p*vec2(1.7,1.05),p*vec2(1.7,1.05))*5.);
   float accent=0.;
   if(composition>.5&&composition<1.5){accent=.075*halo-.020*(1.-halo);}
   if(composition>1.5&&composition<2.5){
    float r=length((p-vec2(-.34,-.22))*vec2(.9,1.));
    float arcs=exp(-pow((r-.52)/.065,2.))+ .55*exp(-pow((r-.72)/.10,2.));
    accent=.06*halo-.038*arcs*(1.-halo*.7);
   }
   if(composition>2.5){
    float fold=sin(p.x*8.+p.y*2.+sin(p.y*3.)*.7);
    accent=.065*halo+.024*fold*(1.-halo*.85);
   }
   diffuseColor.rgb=clamp(diffuseColor.rgb+vec3(accent*compositionStrength),0.,1.);
   // Continuous 3D coordinates: no UV seam, screen-space mapping or time offset.
   // Broad mineral clouds, thin flowing veins and fine satin grain share one surface.
   vec3 q=studioPosition;
   float clouds=stoneFbm(q*19.);
   float flow=dot(q,vec3(72.,39.,55.))+stoneFbm(q*13.)*9.+stoneNoise(q*38.)*1.2;
   float wave=abs(sin(flow*1.7));
   float aa=max(fwidth(wave),.008);
   float veins=1.-smoothstep(.055-aa,.15+aa,wave);
   float grain=stoneNoise(q*420.)-.5;
   float relief=(clouds-.5)*.34-veins*.14+grain*.24;
   diffuseColor.rgb=clamp(diffuseColor.rgb*(.94+relief*textureStrength),0.,1.);
  `);
 };
 const backdrop=new THREE.Mesh(new THREE.SphereGeometry(.75,128,80),material);
 backdrop.name='Stationary textured studio surround';backdrop.renderOrder=-10;scene.add(backdrop);
 // Only the real cast shadow is visible; there is no opaque floor edge or horizon.
 const shadowMaterial=new THREE.ShadowMaterial({color:0x514953,opacity:.20,depthWrite:false});
 shadowMaterial.onBeforeCompile=shader=>{
  shader.vertexShader='varying vec2 shadowGround;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nshadowGround=position.xy;');
  shader.fragmentShader='varying vec2 shadowGround;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <fog_fragment>',`#include <fog_fragment>
   gl_FragColor.a*=1.-smoothstep(.18,.48,length(shadowGround));
  `);
 };
 const ground=new THREE.Mesh(new THREE.PlaneGeometry(2,2),shadowMaterial);
 ground.name='Transparent studio shadow receiver';ground.rotation.x=-Math.PI/2;ground.position.y=-.056;ground.receiveShadow=true;scene.add(ground);
 const themes={dark:['#161d27','#263049'],sand:['#e9e3d8','#fffaf1'],light:['#efd0da','#fff0f5']};
 function setTheme(name){const t=themes[name]||themes.dark;uniforms.pastelLow.value.set(t[0]);uniforms.pastelHigh.value.set(t[1]);scene.background.set(t[0]);uniforms.compositionStrength.value=name==='dark'?.12:1;uniforms.textureStrength.value=name==='dark'?.38:.85;}
 function setComposition(value){uniforms.composition.value=Number(value);}
 function update(){renderer.shadowMap.needsUpdate=true;}
 setTheme('dark');return {setTheme,setComposition,update,key,backdrop,ground};
}
