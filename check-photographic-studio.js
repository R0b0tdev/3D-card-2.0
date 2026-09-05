async page => {
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.setViewportSize({width:1440,height:1000});await page.reload();await page.waitForFunction(()=>window.viewerReady,null,{timeout:90000});
 await page.screenshot({path:'output/playwright/studio-dark.png',timeout:60000});
 await page.locator('[data-bg="sand"]').click();await page.screenshot({path:'output/playwright/studio-sand.png',timeout:60000});
 await page.evaluate(()=>{viewerPivot.rotation.y+=.85;viewerStudio.update();viewerRenderer.render(viewerScene,viewerCamera);});
 await page.screenshot({path:'output/playwright/studio-shadow-turned.png',timeout:60000});
 await page.locator('[data-bg="light"]').click();await page.screenshot({path:'output/playwright/studio-marble.png',timeout:60000});
 return {errors,shadow:await page.evaluate(()=>({casters:viewerModel.children.length,enabled:viewerRenderer.shadowMap.enabled,floorY:-.056,key:viewerStudio.key.position.toArray()}))};
}
