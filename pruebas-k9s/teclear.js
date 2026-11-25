// Abre la terminal web (ttyd en localhost:7681), arranca k9s y teclea los atajos.
// Una captura por paso en <carpeta>.   node teclear.js <carpeta>
const path = require("path");
const PW = ["<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright", "playwright"];
let chromium = null;
for (const p of PW) { try { chromium = require(p).chromium; break; } catch (e) {} }
const dir = process.argv[2];
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  await pg.goto("http://localhost:7681");
  await espera(2500);
  await pg.locator(".xterm").click();
  const foto = async (n, ms = 2500) => { await espera(ms); await pg.screenshot({ path: path.join(dir, n + ".png") }); console.log("ok", n); };
  const tecla = async (k) => { await pg.keyboard.press(k); };
  const escribe = async (t) => { await pg.keyboard.type(t, { delay: 60 }); };

  await escribe("k9s -n tienda\n");
  await foto("01-pods", 6000);                       // pods del namespace tienda
  await escribe(":deploy\n");
  await foto("02-deploy");
  await escribe(":pods\n");
  await espera(2000);
  await escribe("/pagos\n");                         // filtro
  await foto("03-filtro-pagos");
  await tecla("l");                                   // logs
  await foto("04-logs-pagos", 4000);
  await tecla("p");                                   // logs del contenedor anterior
  await foto("05-logs-previos", 4000);
  await tecla("Escape"); await espera(800); await tecla("Escape"); await espera(800);
  await escribe("/web\n");
  await espera(1500);
  await tecla("d");                                   // describe
  await foto("06-describe");
  await tecla("Escape"); await espera(800);
  await tecla("s");                                   // shell
  await espera(3000);
  await escribe("nginx -v; hostname\n");
  await foto("07-shell", 3000);
  await escribe("exit\n");
  await espera(3000);
  await tecla("Control+d");                           // borrar pod
  await espera(1200);
  await foto("08-confirmar-borrar", 500);
  await tecla("Tab");                                 // el foco empieza en Cancel
  await foto("08a-ok", 800);
  await tecla("Enter");                               // OK
  await foto("08b-recreado", 6000);
  await escribe(":deploy\n");
  await espera(2000);
  await escribe("/web\n");
  await espera(1500);
  await tecla("s");                                   // escalar
  await espera(1500);
  for (let i = 0; i < 4; i++) await tecla("Backspace");
  await escribe("5"); await espera(500);
  await foto("10-escalar", 500);
  await tecla("Enter");
  await foto("11-escalado", 6000);
  await escribe(":xray deploy tienda\n");
  await foto("12-xray", 4000);
  await escribe(":q\n");
  await espera(1500);
  await escribe("clear; k9s -n tienda --readonly\n");
  await espera(6000);
  await tecla("Control+d");
  await foto("09-readonly", 2000);
  await escribe(":q\n");
  await b.close();
})();
