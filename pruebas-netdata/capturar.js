// Captura el panel local de Netdata (http://localhost:19999).
//   node capturar.js <salida.png> <ruta>
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
(async () => {
  const [out, ruta, clic] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  await pg.goto("http://localhost:19999" + ruta);
  await pg.waitForTimeout(9000);
  // si sale el aviso de iniciar sesión en Netdata Cloud, se descarta
  for (const t of ["Skip and use the dashboard anonymously", "Skip", "Use the dashboard anonymously", "Later"]) {
    const l = pg.getByText(t, { exact: false });
    if (await l.count()) { try { await l.first().click(); await pg.waitForTimeout(3000); } catch (e) {} }
  }
  if (clic) { try { await pg.getByText(clic, { exact: true }).first().click(); await pg.waitForTimeout(5000); } catch (e) {} }
  await pg.waitForTimeout(3000);
  await pg.screenshot({ path: out });
  await b.close();
  console.log("ok", out);
})();
