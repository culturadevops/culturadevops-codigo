# -*- coding: utf-8 -*-
"""Cliente mínimo de la API REST de Jenkins para el banco (877 y 878). Sin dependencias: urllib + cookies.
Jenkins va sin seguridad (JCasC: securityRealm none), pero la protección CSRF sigue activa: se pide el crumb con la
misma sesión (cookie) y se manda en cada POST."""
import http.cookiejar
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape


class Jenkins:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.crumb = None

    def _req(self, metodo, ruta, datos=None, tipo=None):
        url = ruta if ruta.startswith("http") else self.base + ruta
        r = urllib.request.Request(url, data=datos, method=metodo)
        if tipo:
            r.add_header("Content-Type", tipo)
        if metodo == "POST":
            if not self.crumb:
                c = json.loads(self.op.open(self.base + "/crumbIssuer/api/json", timeout=30).read())
                self.crumb = (c["crumbRequestField"], c["crumb"])
            r.add_header(*self.crumb)
        return self.op.open(r, timeout=60)

    def get(self, ruta):
        return self._req("GET", ruta).read().decode("utf-8", "replace")

    def json(self, ruta):
        return json.loads(self.get(ruta))

    def esperar_listo(self, tope=300):
        t0 = time.time()
        while time.time() - t0 < tope:
            try:
                d = self.json("/api/json")
                if "jobs" in d:
                    return time.time() - t0
            except Exception:
                pass
            time.sleep(1)
        raise SystemExit("Jenkins no arrancó")

    def crear_pipeline(self, nombre, script):
        xml = ("<?xml version='1.1' encoding='UTF-8'?><flow-definition plugin='workflow-job'>"
               "<keepDependencies>false</keepDependencies><properties/>"
               "<definition class='org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition' plugin='workflow-cps'>"
               f"<script>{escape(script)}</script><sandbox>true</sandbox></definition>"
               "<disabled>false</disabled></flow-definition>").encode("utf-8")
        try:
            self._req("POST", "/createItem?name=" + urllib.parse.quote(nombre), xml, "application/xml")
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            self._req("POST", f"/job/{nombre}/config.xml", xml, "application/xml")

    def crear_pipeline_scm(self, nombre, url_repo, rama, ruta_jenkinsfile, ligero=True):
        """Job «Pipeline script from SCM»: Jenkins lee el Jenkinsfile del repo (como en la vida real)."""
        xml = ("<?xml version='1.1' encoding='UTF-8'?><flow-definition plugin='workflow-job'>"
               "<keepDependencies>false</keepDependencies><properties/>"
               "<definition class='org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition' plugin='workflow-cps'>"
               "<scm class='hudson.plugins.git.GitSCM' plugin='git'><configVersion>2</configVersion>"
               f"<userRemoteConfigs><hudson.plugins.git.UserRemoteConfig><url>{escape(url_repo)}</url>"
               "</hudson.plugins.git.UserRemoteConfig></userRemoteConfigs>"
               f"<branches><hudson.plugins.git.BranchSpec><name>{escape(rama)}</name></hudson.plugins.git.BranchSpec></branches>"
               "<doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations><submoduleCfg class='empty-list'/>"
               "<extensions/></scm>"
               f"<scriptPath>{escape(ruta_jenkinsfile)}</scriptPath><lightweight>{'true' if ligero else 'false'}</lightweight>"
               "</definition><disabled>false</disabled></flow-definition>").encode("utf-8")
        try:
            self._req("POST", "/createItem?name=" + urllib.parse.quote(nombre), xml, "application/xml")
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            self._req("POST", f"/job/{nombre}/config.xml", xml, "application/xml")

    def lanzar(self, nombre):
        """Lanza un build y devuelve su número (espera a que salga de la cola)."""
        r = self._req("POST", f"/job/{nombre}/build?delay=0sec")
        cola = r.headers["Location"].rstrip("/") + "/api/json"
        while True:
            q = json.loads(self._req("GET", cola).read())
            if q.get("executable"):
                return q["executable"]["number"]
            if q.get("cancelled"):
                raise SystemExit(f"{nombre}: cancelado en la cola")
            time.sleep(0.2)

    def esperar(self, nombre, n, tope=3600):
        t0 = time.time()
        while time.time() - t0 < tope:
            b = self.json(f"/job/{nombre}/{n}/api/json?tree=building,result,duration,timestamp")
            if not b["building"] and b["result"]:
                return b
            time.sleep(1)
        raise SystemExit(f"{nombre} #{n} no terminó en {tope} s")

    def consola(self, nombre, n):
        return self.get(f"/job/{nombre}/{n}/consoleText")

    def etapas(self, nombre, n):
        """Etapas y su duración (plugin pipeline-stage-view, /wfapi/describe)."""
        d = self.json(f"/job/{nombre}/{n}/wfapi/describe")
        return [(s["name"], s["durationMillis"] / 1000, s["status"]) for s in d.get("stages", [])]

    def abortar(self, nombre, n):
        self._req("POST", f"/job/{nombre}/{n}/stop")
