async page => {
 await page.setViewportSize({width:1200,height:1000});
 await page.reload();
 await page.waitForFunction(()=>window.viewerReady,null,{timeout:90000});
 const materials=await page.evaluate(()=>{viewerPivot.rotation.set(.08,1.42,-.03);viewerPivot.position.set(0,0,0);viewerCamera.position.set(0,0,.064);viewerRenderer.render(viewerScene,viewerCamera);let a=[];viewerModel.traverse(o=>{if(o.isMesh)for(const m of(Array.isArray(o.material)?o.material:[o.material]))if(m.name.startsWith('Au'))a.push({name:m.name,roughness:m.roughness,light:m.envMapIntensity});});return a;});
 await page.screenshot({path:'output/soft-rims-grazing.png',timeout:60000});
 return materials;
}
