import {createStudio} from './photographic-studio.js?v=studio-23';
import {applyBrilliantOptics} from './diamond-optics.js?v=brilliant-recut-21';
import * as THREE from 'three';
import {TrackballControls} from 'three/addons/controls/TrackballControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=id=>document.getElementById(id);
const scene=new THREE.Scene();scene.background=new THREE.Color('#101311');
const camera=new THREE.PerspectiveCamera(31,innerWidth/innerHeight,.001,10);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.35;
const gl=renderer.getContext();const dbg=gl.getExtension('WEBGL_debug_renderer_info');const software=dbg&&/swiftshader|llvmpipe|software/i.test(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL));if(software)renderer.setPixelRatio(.85);
renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').appendChild(renderer.domElement);
const pmrem=new THREE.PMREMGenerator(renderer);const room=new RoomEnvironment();
// Narrow studio strips produce moving, shaped highlights on the rolled gold rims.
for(const [x,y,z,w,h,strength] of [[-3,0,2,.26,5,3.2],[3,1,-2,.4,5,2.6],[0,4,1,5,.18,2.2]]){
 const strip=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(1,.96,.88).multiplyScalar(strength),side:THREE.DoubleSide}));
 strip.position.set(x,y,z);strip.lookAt(0,0,0);room.add(strip);
}
scene.environment=pmrem.fromScene(room,.03).texture;room.dispose();
// High-contrast jewellery reflection cards keep the metal lively without bleaching the inlays.
const goldStudio=new THREE.Scene();goldStudio.background=new THREE.Color(.075,.07,.06);
for(const [x,y,z,w,h,power] of [[-3,1,2,1.3,7,2.6],[3,0,1,.45,7,4],[0,0,4,3.8,5,.85],[1,1,-4,2.8,6,1.7],[0,4,0,5,.5,3]]){
 const card=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(1,.98,.94).multiplyScalar(power),side:THREE.DoubleSide}));
 card.position.set(x,y,z);card.lookAt(0,0,0);goldStudio.add(card);
}
const goldEnvironment=pmrem.fromScene(goldStudio,.015).texture;
// Broad feathered reflections on the rolled rim prevent a narrow strip reading as a seam.
// Keep the original jewellery environment on all face ornaments and settings.
const edgeEnvironment=pmrem.fromScene(goldStudio,.16).texture;
const diamondStudio=new THREE.Scene();diamondStudio.background=new THREE.Color(.18,.18,.18);
for(const [x,y,z,w,h,power] of [[-3,2,2,1.5,4,5],[3,0,2,.65,4,7],[0,3,-2,3,1.1,4],[0,-3,1,1.7,1.4,2],[0,0,4,1.2,1.2,3]]){
 const panel=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(power,power,power),side:THREE.DoubleSide}));
 panel.position.set(x,y,z);panel.lookAt(0,0,0);diamondStudio.add(panel);
}
const centralDiamondEnvironment=pmrem.fromScene(diamondStudio,.005).texture;
const goldMaterials=new Set();
const studio=createStudio(scene,renderer,software);window.viewerStudio=studio;
const controls=new TrackballControls(camera,renderer.domElement);controls.noPan=true;controls.minDistance=.064;controls.maxDistance=.45;controls.rotateSpeed=2.5;controls.zoomSpeed=1.05;controls.staticMoving=true;
const pivot=new THREE.Group();scene.add(pivot);
let loaded=false,rotating=false,clay=false,target=null,zoomed=false,dirty=true; THREE.DefaultLoadingManager.onLoad=()=>dirty=true;
const original=new Map();const clayMat=new THREE.MeshStandardMaterial({color:'#c6b69a',metalness:.22,roughness:.48});
function home(){controls.reset();camera.position.set(0,0,innerWidth<650?.28:.215);controls.target.set(0,0,0);pivot.rotation.set(Math.PI+.075,-.19,Math.PI-.035);zoomed=false;target=null;controls.update();}
home();
const draco=new DRACOLoader();draco.setDecoderPath('./node_modules/three/examples/jsm/libs/draco/gltf/');
new GLTFLoader().setDRACOLoader(draco).load('output/jewellery-card.glb?v=brilliant-recut-21',gltf=>{
 const root=gltf.scene;root.rotation.x=Math.PI/2;root.rotateOnWorldAxis(new THREE.Vector3(0,0,1),Math.PI);pivot.add(root);
 root.traverse(o=>{if(!o.isMesh)return;o.frustumCulled=false;o.castShadow=true;const mats=Array.isArray(o.material)?o.material:[o.material];
 for(let m of mats){m.envMapIntensity=1.35;if(m.map)m.map.anisotropy=renderer.capabilities.getMaxAnisotropy();if(m.normalMap)m.normalMap.anisotropy=8;
 if(m.name.startsWith('Au')){m.envMap=goldEnvironment;m.envMapIntensity=1.65;m.roughness=.115;if(m.name.startsWith('Au edge')){m.envMap=edgeEnvironment;m.roughness=.34;m.envMapIntensity=1.1;m.clearcoat=0;}goldMaterials.add(m);}
 if(m.name.startsWith('Central brilliant')){m.color.setRGB(.94,.97,1);m.metalness=0;m.roughness=.035;m.ior=2.417;m.transmission=.88;m.thickness=.0004;m.dispersion=.045;m.envMap=centralDiamondEnvironment;m.envMapIntensity=1.5;m.clearcoat=.10;m.clearcoatRoughness=.025;goldMaterials.add(m);}
 if(m.name.includes('Diamond')){m.ior=2.417;m.transmission=.46;m.thickness=.00025;m.dispersion=.15;m.envMapIntensity=1.9;}
 if(m.name.includes('Rose pink')){m.color.setRGB(.23,.032,.07);m.transmission=.12;m.thickness=.00025;m.envMapIntensity=1.4;}
 if(m.name.startsWith('Side')){if(!m.isMeshPhysicalMaterial){const p=new THREE.MeshPhysicalMaterial();THREE.MeshStandardMaterial.prototype.copy.call(p,m);m=p;}m.iridescence=.52;m.iridescenceIOR=1.34;m.iridescenceThicknessRange=[210,420];if(!m.iridescenceMap)m.iridescenceMap=new THREE.TextureLoader().load(m.name.includes('Side 1')?'textures/side1-pearl.png':'textures/side2-pearl.png');m.clearcoat=.18;m.clearcoatRoughness=.23;}
 if(software&&m.isMeshPhysicalMaterial){m.transmission=0;m.dispersion=0;}
 if(m.name.startsWith('Central brilliant')){applyBrilliantOptics(o,m);}

 const idx=mats.findIndex(x=>x.name===m.name);if(idx>=0)mats[idx]=m;
 }
 o.material=Array.isArray(o.material)?mats:mats[0];original.set(o,o.material);
 });
 loaded=true;$('loading').style.display='none';window.viewerReady=true;window.viewerModel=root;window.viewerScene=scene;window.viewerCamera=camera;window.viewerRenderer=renderer;window.viewerPivot=pivot;
},e=>{$('progress').textContent=e.total?`Загрузка объекта · ${Math.round(e.loaded/e.total*100)}%`:'Загрузка ювелирного объекта…';},error=>{$('loading').style.display='none';$('error').hidden=false;$('error').textContent='Не удалось загрузить модель. Запустите локальный сервер через start-viewer.cmd и откройте http://localhost:8765. '+error.message;console.error(error);});
function stop(){rotating=false;$('rotate').classList.remove('active');$('rotate').setAttribute('aria-pressed','false');}
function preset(back){stop();controls.reset();camera.position.set(0,0,innerWidth<650?.28:.215);controls.target.set(0,0,0);target=new THREE.Quaternion().setFromEuler(back?new THREE.Euler(0,0,0):new THREE.Euler(Math.PI,0,Math.PI));controls.update();}
$('front').onclick=()=>preset(false);$('back').onclick=()=>preset(true);
$('rotate').onclick=()=>{rotating=!rotating;target=null;if(rotating){autoSpinPhase=0;secondarySpinDirection=1;}$('rotate').classList.toggle('active',rotating);$('rotate').setAttribute('aria-pressed',String(rotating));};
$('reset').onclick=()=>{stop();home();};
$('zoom').onclick=()=>{zoomed=!zoomed;camera.position.multiplyScalar((zoomed?.115:.215)/camera.position.length());controls.update();};
$('light').oninput=e=>renderer.toneMappingExposure=Number(e.target.value);
$('light-angle').oninput=e=>{scene.environmentRotation.y=Number(e.target.value)*Math.PI/180;goldMaterials.forEach(m=>m.envMapRotation.copy(scene.environmentRotation));dirty=true;};
$('edge').onclick=()=>{stop();controls.reset();camera.position.set(0,0,innerWidth<650?.28:.18);controls.target.set(0,0,0);target=new THREE.Quaternion().setFromEuler(new THREE.Euler(.10,1.20,-.06));controls.update();};
$('clay').onclick=()=>{clay=!clay;original.forEach((m,o)=>o.material=clay?clayMat:m);$('clay').textContent=clay?'Вернуть материалы':'Посмотреть форму';};
document.querySelectorAll('[data-bg]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-bg]').forEach(x=>x.classList.remove('active'));b.classList.add('active');const type=b.dataset.bg;studio.setTheme(type);document.body.classList.toggle('pale',type!=='dark');});
$('fullscreen').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen();};
$('capture').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.href=renderer.domElement.toDataURL('image/png');a.download='MIR-SUPREME-view.png';a.click();};
controls.addEventListener('start',()=>{stop();target=null;});
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);controls.handleResize();});
controls.addEventListener('change',()=>dirty=true);document.addEventListener('click',()=>dirty=true);document.addEventListener('input',()=>dirty=true);addEventListener('resize',()=>dirty=true);
const previousCameraPosition=new THREE.Vector3();const previousCameraQuaternion=new THREE.Quaternion();
const autoSpinSpeed=.24,secondarySpinRatio=.10,fullTurn=Math.PI*2;let autoSpinPhase=0,secondarySpinDirection=1,last=performance.now();function advanceAutoSpin(step){pivot.rotation.y+=step;while(step>0){const part=Math.min(step,fullTurn-autoSpinPhase);pivot.rotation.x+=part*secondarySpinRatio*secondarySpinDirection;autoSpinPhase+=part;step-=part;if(autoSpinPhase>=fullTurn-1e-9){autoSpinPhase=0;secondarySpinDirection*=-1;}}}function tick(now){const dt=Math.min((now-last)/1000,.5);last=now;if(loaded){if(rotating){advanceAutoSpin(dt*autoSpinSpeed);dirty=true;}if(target){pivot.quaternion.slerp(target,1-Math.exp(-dt*7));dirty=true;if(pivot.quaternion.angleTo(target)<.001)target=null;}}controls.update();if(previousCameraPosition.distanceToSquared(camera.position)>1e-14 || 1-Math.abs(previousCameraQuaternion.dot(camera.quaternion))>1e-12){dirty=true;previousCameraPosition.copy(camera.position);previousCameraQuaternion.copy(camera.quaternion);}if(dirty){studio.update();renderer.render(scene,camera);dirty=false;}requestAnimationFrame(tick);}requestAnimationFrame(tick);












