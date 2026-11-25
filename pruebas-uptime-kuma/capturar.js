// Captura el panel de Uptime Kuma (publicado en localhost:3001).
//   node capturar.js <salida.png> [ruta]
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
(async () => {
  const [out, ruta] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  await pg.goto("http://localhost:3001/dashboard");
  await pg.waitForTimeout(2500);
  if (await pg.locator("input[type=password]").count()) {
    await pg.locator("input[autocomplete=username]").first().fill("admin");
    await pg.locator("input[type=password]").first().fill("Clave-de-prueba-123");
    await pg.locator("button[type=submit]").first().click();
    await pg.waitForTimeout(3000);
  }
  if (ruta) { await pg.goto("http://localhost:3001" + ruta); }
  await pg.waitForTimeout(4000);
  await pg.screenshot({ path: out });
  await b.close();
  console.log("ok", out);
})();
