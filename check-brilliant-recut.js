async page => {
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.setViewportSize({width:1200,height:1000});await page.reload();await page.waitForFunction(()=>window.viewerReady,null,{timeout:90000});
 await page.evaluate(()=>{viewerPivot.rotation.set(Math.PI,0,Math.PI);viewerPivot.position.set(.0055,0,0);viewerCamera.position.set(0,0,.064);viewerCamera.zoom=1.6;viewerCamera.updateProjectionMatrix();viewerRenderer.render(viewerScene,viewerCamera);});
 await page.screenshot({path:'output/playwright/brilliant-recut-front.png',timeout:60000});
 await page.evaluate(()=>{viewerPivot.rotation.set(Math.PI+.22,.27,Math.PI);viewerRenderer.render(viewerScene,viewerCamera);});
 await page.screenshot({path:'output/playwright/brilliant-recut-angled.png',timeout:60000});
 return {errors};
}
