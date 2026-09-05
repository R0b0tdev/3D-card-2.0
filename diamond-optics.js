import * as THREE from 'three';

// Trace refraction and internal reflections against the actual convex cut.
// This shader is scoped to the 25 central stones; the rest of the model is untouched.
export function applyBrilliantOptics(mesh,material){
 const planes=JSON.parse(mesh.userData.optical_planes||'[]');
 const records=JSON.parse(mesh.userData.registration||'[]');
 if(!planes.length||!records.length)return;
 const centers=records.map(r=>({x:(r.u-.5)*.05398,y:(r.v-.5)*.08560,z:r.base_mm/1000,r:r.radius_mm/1000}));
 const pos=mesh.geometry.attributes.position,local=new Float32Array(pos.count*3);
 for(let i=0;i<pos.count;i++){
  const x=pos.getX(i),y=-pos.getZ(i),h=-pos.getY(i);
  let nearest=centers[0],distance=Infinity;
  for(const c of centers){const d=(x-c.x)**2+(y-c.y)**2;if(d<distance){distance=d;nearest=c;}}
  local.set([(x-nearest.x)/nearest.r,(y-nearest.y)/nearest.r,(h-nearest.z)/nearest.r],i*3);
 }
 mesh.geometry.setAttribute('diamondLocal',new THREE.BufferAttribute(local,3));
 // Browser optical paths are calculated below, avoiding an opaque-looking diffuse disk.
 material.transmission=0;material.metalness=0;material.clearcoat=0;
 material.onBeforeCompile=shader=>{
  shader.uniforms.diamondPlanes={value:planes.map(p=>new THREE.Vector4(...p))};
  shader.vertexShader='attribute vec3 diamondLocal; varying vec3 vDiamondLocal; varying vec3 vDiamondX; varying vec3 vDiamondY; varying vec3 vDiamondZ;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
   vDiamondLocal=diamondLocal;
   vDiamondX=normalize(normalMatrix*vec3(1,0,0));
   vDiamondY=normalize(normalMatrix*vec3(0,0,-1));
   vDiamondZ=normalize(normalMatrix*vec3(0,-1,0));`);
  shader.fragmentShader=`uniform vec4 diamondPlanes[${planes.length}]; varying vec3 vDiamondLocal; varying vec3 vDiamondX; varying vec3 vDiamondY; varying vec3 vDiamondZ;\n`+shader.fragmentShader;
  const functions=`
   vec3 diamondEnvironment(vec3 direction){
    vec3 viewDirection=normalize(vDiamondX*direction.x+vDiamondY*direction.y+vDiamondZ*direction.z);
    vec3 worldDirection=inverseTransformDirection(viewDirection,viewMatrix);
    return textureCubeUV(envMap,envMapRotation*worldDirection,.035).rgb*envMapIntensity;
   }
   vec3 traceDiamond(vec3 start,vec3 incoming,vec3 surfaceNormal){
    const float ior=2.417;
    const float f0=.17195;
    float frontF=f0+(1.0-f0)*pow(1.0-clamp(dot(-incoming,surfaceNormal),0.0,1.0),5.0);
    vec3 result=frontF*diamondEnvironment(reflect(incoming,surfaceNormal));
    vec3 direction=refract(incoming,surfaceNormal,1.0/ior);
    vec3 origin=start-surfaceNormal*.002;
    float weight=1.0-frontF;
    for(int bounce=0;bounce<5;bounce++){
     float nearest=1.e8;vec3 hitNormal=vec3(0,0,1);
     for(int plane=0;plane<${planes.length};plane++){
      vec4 p=diamondPlanes[plane];float den=dot(p.xyz,direction);
      if(den>1.e-5){float t=(p.w-dot(p.xyz,origin))/den;if(t>.00001&&t<nearest){nearest=t;hitNormal=p.xyz;}}
     }
     if(nearest>1.e7)break;
     origin+=direction*nearest;
     vec3 escape=refract(direction,-hitNormal,ior);
     if(dot(escape,escape)>.001){
      float cosine=clamp(dot(direction,hitNormal),0.0,1.0);
      float fresnel=f0+(1.0-f0)*pow(1.0-cosine,5.0);
      result+=weight*(1.0-fresnel)*diamondEnvironment(escape);
      weight*=fresnel;
     }
     direction=reflect(direction,hitNormal);origin+=direction*.001;
    }
    result+=weight*diamondEnvironment(direction)*.55;
    return result;
   }
  `;
  shader.fragmentShader=shader.fragmentShader.replace('void main() {',functions+'\nvoid main() {');
  shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`
   vec3 diamondIncoming=normalize(vec3(dot(-normalize(vViewPosition),vDiamondX),dot(-normalize(vViewPosition),vDiamondY),dot(-normalize(vViewPosition),vDiamondZ)));
   vec3 diamondNormal=normalize(vec3(dot(normal,vDiamondX),dot(normal,vDiamondY),dot(normal,vDiamondZ)));
   outgoingLight=traceDiamond(vDiamondLocal,diamondIncoming,diamondNormal);
   #include <opaque_fragment>`);
 };
 material.customProgramCacheKey=()=> 'round-brilliant-ray-paths-'+planes.length;
 material.needsUpdate=true;
}
