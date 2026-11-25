// Captura el portal de Harbor (publicado en http://localhost:8088).
//   node capturar.js <salida.png> <ruta> <clave_admin>
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
(async () => {
  const [out, ruta, clave] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  await pg.goto("http://localhost:8088/account/sign-in");
  await pg.waitForTimeout(3000);
  await pg.locator("#login_username").fill("admin");
  await pg.locator("#login_password").fill(clave);
  await pg.locator("#log_in").click();
  await pg.waitForTimeout(3000);
  await pg.goto("http://localhost:8088" + ruta);
  await pg.waitForTimeout(5000);
  await pg.screenshot({ path: out });
  await b.close();
  console.log("ok", out);
})();
