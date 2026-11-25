// Captura la interfaz de Argo CD (port-forward publicado en https://localhost:8443).
//   node capturar.js <salida.png> <ruta> <clave_admin>
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
(async () => {
  const [out, ruta, clave] = process.argv.slice(2);
  const b = await chromium.launch();
  const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  const pg = await ctx.newPage();
  await pg.goto("https://localhost:8443/login");
  await pg.waitForTimeout(2500);
  await pg.locator("input[name=username], #username").first().fill("admin");
  await pg.locator("input[type=password]").first().fill(clave);
  await pg.locator("button[type=submit], button:has-text('Sign In')").first().click();
  await pg.waitForTimeout(3000);
  await pg.goto("https://localhost:8443" + ruta);
  await pg.waitForTimeout(6000);
  await pg.screenshot({ path: out });
  await b.close();
  console.log("ok", out);
})();
