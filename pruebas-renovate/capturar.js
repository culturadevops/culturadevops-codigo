// Captura una página de Gitea (localhost:3000) con la sesión del usuario dev.
//   node capturar.js <salida.png> <ruta>
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
(async () => {
  const [out, ruta] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  await pg.goto("http://localhost:3000/user/login");
  await pg.locator("#user_name").fill("dev");
  await pg.locator("#password").fill("Clave-de-prueba-123");
  await pg.locator("form button.ui.primary").first().click();
  await pg.waitForTimeout(2000);
  await pg.goto("http://localhost:3000" + ruta);
  await pg.waitForTimeout(2500);
  await pg.screenshot({ path: out });
  await b.close();
  console.log("ok", out);
})();
