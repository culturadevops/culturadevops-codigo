// Dokploy de principio a fin desde el navegador (sesión real) + capturas.
// La API REST acepta la cookie de sesión, así que las llamadas van con fetch desde la página.
//   node flujo.js <carpeta_capturas>
const path = require("path");
const { chromium } = require("<proyecto>/canales/cartasdeldiablo/recursos/node_modules/playwright");
const dir = process.argv[2];
const URL = "http://localhost:3300";
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const sec = (t) => console.log(`\n### ${t}`);

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
  const foto = async (n) => { await espera(2500); await pg.screenshot({ path: path.join(dir, n + ".png") }); };
  const api = async (ruta, cuerpo) => pg.evaluate(async ([r, c]) => {
    const res = await fetch("/api/" + r, c === undefined ? {} : {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(c) });
    const t = await res.text();
    try { return { status: res.status, json: JSON.parse(t) }; } catch (e) { return { status: res.status, text: t.slice(0, 500) }; }
  }, [ruta, cuerpo]);

  // 1 · registro del primer usuario (el administrador)
  await pg.goto(URL + "/register");
  await espera(3000);
  await foto("01-registro");
  await pg.fill("input[placeholder=John]", "Dev");
  await pg.fill("input[placeholder=Doe]", "Ops");
  await pg.fill("input[placeholder='email@dokploy.com']", "dev@ejemplo.test");
  const pw = pg.locator("input[type=password]");
  await pw.nth(0).fill("Clave-de-prueba-123");
  await pw.nth(1).fill("Clave-de-prueba-123");
  await pg.click("button:has-text('Register')");
  await espera(6000);
  sec("registro");
  console.log("tras registrarse:", pg.url());
  await foto("02-bienvenida");
  for (const t of ["SKIP ALL", "Skip all"]) { const l = pg.getByText(t, { exact: false }); if (await l.count()) { try { await l.first().click(); await espera(2000); } catch (e) {} break; } }

  // 2 · proyecto y aplicación
  sec("crear proyecto");
  const pj = await api("project.create", { name: "tienda", description: "banco de pruebas" });
  console.log(JSON.stringify(pj).slice(0, 600));
  const proyectos = await api("project.all");
  const proyecto = proyectos.json.find((p) => p.name === "tienda");
  const envId = proyecto.environments[0].environmentId;
  console.log("entornos del proyecto:", proyecto.environments.map((e) => e.name).join(", "));

  sec("crear aplicación");
  const ap = await api("application.create", { name: "web", environmentId: envId });
  const appId = ap.json.applicationId;
  console.log("status", ap.status, "applicationId", appId, "appName", ap.json.appName);

  sec("origen: Git");
  const g = await api("application.saveGitProvider", {
    applicationId: appId, customGitUrl: "https://github.com/Dokploy/examples.git",
    customGitBranch: "main", customGitBuildPath: "/go-fiber", watchPaths: [] });
  console.log("saveGitProvider", g.status);
  const bt = await api("application.saveBuildType", {
    applicationId: appId, buildType: "nixpacks", dockerfile: null, dockerContextPath: null,
    dockerBuildStage: null, herokuVersion: null, railpackVersion: null });
  console.log("saveBuildType nixpacks", bt.status);
  await api("application.update", { applicationId: appId, sourceType: "git" });

  // 3 · desplegar
  sec("desplegar");
  const t0 = Date.now();
  const dp = await api("application.deploy", { applicationId: appId });
  console.log("deploy", dp.status);
  let ultimo = null;
  for (let i = 0; i < 180; i++) {
    await espera(5000);
    const ds = await api(`deployment.all?applicationId=${appId}`);
    if (ds.json && ds.json.length) {
      ultimo = ds.json[0];
      if (["done", "error"].includes(ultimo.status)) break;
    }
  }
  console.log(`estado: ${ultimo && ultimo.status} · ${((Date.now() - t0) / 1000).toFixed(0)} s desde el deploy`);
  console.log("título:", ultimo && ultimo.title, "· log:", ultimo && ultimo.logPath);
  const una = await api(`application.one?applicationId=${appId}`);
  console.log("applicationStatus:", una.json.applicationStatus, "· appName:", una.json.appName);
  await pg.goto(`${URL}/dashboard/project/${proyecto.projectId}/environment/${envId}/services/application/${appId}?tab=deployments`);
  await foto("03-despliegues");
  await pg.goto(`${URL}/dashboard/project/${proyecto.projectId}/environment/${envId}`);
  await foto("04-proyecto");

  // 4 · dominio
  sec("dominio sin HTTPS");
  const dm = await api("domain.create", { host: "tienda.localhost", port: 3000, https: false,
    applicationId: appId, certificateType: "none", domainType: "application", path: "/" });
  console.log("domain.create", dm.status, JSON.stringify(dm.json || dm.text).slice(0, 300));
  sec("dominio con HTTPS (Let's Encrypt)");
  const dm2 = await api("domain.create", { host: "tienda.ejemplo.test", port: 3000, https: true,
    applicationId: appId, certificateType: "letsencrypt", domainType: "application", path: "/" });
  console.log("domain.create", dm2.status, JSON.stringify(dm2.json || dm2.text).slice(0, 300));
  await pg.goto(`${URL}/dashboard/project/${proyecto.projectId}/environment/${envId}/services/application/${appId}?tab=domains`);
  await foto("05-dominios");
  console.log("APPNAME=" + una.json.appName);
  await b.close();
})();
