# -*- coding: utf-8 -*-
"""Las 20 apps típicas del vídeo 711 (5 Node, 5 Python, 5 Go, 5 Java). Fijadas el 2026-10-29 antes de generar ningún Dockerfile.
Todas escuchan en el puerto 8080 y responden «ok» en /. Los lockfiles (package-lock.json, go.sum) se generan con
`python crear_apps.py --locks` en contenedores desechables; después quedan fijos.

  python crear_apps.py          # escribe apps/
  python crear_apps.py --locks  # genera package-lock.json y go.sum (necesita red)
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

NODE_SRV = """const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('ok'));
app.listen(8080, () => console.log('escuchando en 8080'));
"""

POM_BASE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.ejemplo</groupId>
  <artifactId>{art}</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
{deps}
  <build>
    <plugins>
{plugins}
    </plugins>
  </build>
</project>
"""

JAR_PLUGIN = """      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.4.2</version>
        <configuration>
          <archive><manifest><mainClass>app.Main</mainClass></manifest></archive>
        </configuration>
      </plugin>"""

SHADE_PLUGIN = """      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.6.0</version>
        <executions>
          <execution>
            <phase>package</phase>
            <goals><goal>shade</goal></goals>
            <configuration>
              <transformers>
                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                  <mainClass>app.Main</mainClass>
                </transformer>
              </transformers>
            </configuration>
          </execution>
        </executions>
      </plugin>"""

JAVA_HTTP = """package app;

import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class Main {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", ex -> {
            byte[] b = "ok".getBytes();
            ex.sendResponseHeaders(200, b.length);
            try (OutputStream os = ex.getResponseBody()) { os.write(b); }
        });
        server.start();
        System.out.println("escuchando en 8080");
    }
}
"""

APPS = {
    # ───────── Node ─────────
    "n1-express": {
        "package.json": json.dumps({"name": "api-express", "version": "1.0.0", "main": "server.js",
                                    "scripts": {"start": "node server.js"}, "dependencies": {"express": "^4.21.2"}}, indent=2) + "\n",
        "server.js": NODE_SRV,
    },
    "n2-http-sin-dependencias": {
        "package.json": json.dumps({"name": "http-simple", "version": "1.0.0", "main": "index.js",
                                    "scripts": {"start": "node index.js"}}, indent=2) + "\n",
        "index.js": "const http = require('http');\nhttp.createServer((req, res) => { res.end('ok'); })"
                    ".listen(8080, () => console.log('escuchando en 8080'));\n",
    },
    "n3-fastify": {
        "package.json": json.dumps({"name": "api-fastify", "version": "1.0.0", "main": "app.js", "type": "module",
                                    "scripts": {"start": "node app.js"}, "dependencies": {"fastify": "^5.2.1"}}, indent=2) + "\n",
        "app.js": "import Fastify from 'fastify';\nconst app = Fastify({ logger: true });\napp.get('/', async () => 'ok');\n"
                  "await app.listen({ port: 8080, host: '0.0.0.0' });\n",
    },
    "n4-typescript": {
        "package.json": json.dumps({"name": "api-ts", "version": "1.0.0", "main": "dist/server.js",
                                    "scripts": {"build": "tsc", "start": "node dist/server.js"},
                                    "dependencies": {"express": "^4.21.2"},
                                    "devDependencies": {"typescript": "^5.7.3", "@types/express": "^4.17.21",
                                                        "@types/node": "^22.10.5"}}, indent=2) + "\n",
        "tsconfig.json": json.dumps({"compilerOptions": {"target": "ES2022", "module": "commonjs", "outDir": "dist",
                                                         "rootDir": "src", "strict": True, "esModuleInterop": True}}, indent=2) + "\n",
        "src/server.ts": "import express from 'express';\nconst app = express();\napp.get('/', (_req, res) => { res.send('ok'); });\n"
                         "app.listen(8080, () => console.log('escuchando en 8080'));\n",
    },
    "n5-koa": {
        "package.json": json.dumps({"name": "api-koa", "version": "1.0.0", "main": "server.js",
                                    "scripts": {"start": "node server.js"}, "dependencies": {"koa": "^2.15.3"}}, indent=2) + "\n",
        "server.js": "const Koa = require('koa');\nconst app = new Koa();\napp.use(ctx => { ctx.body = 'ok'; });\n"
                     "app.listen(8080, () => console.log('escuchando en 8080'));\n",
    },
    # ───────── Python ─────────
    "p1-flask-gunicorn": {
        "requirements.txt": "flask==3.1.0\ngunicorn==23.0.0\n",
        "app.py": "from flask import Flask\n\napp = Flask(__name__)\n\n\n@app.get('/')\ndef inicio():\n    return 'ok'\n",
        "README.md": "En producción: gunicorn -b 0.0.0.0:8080 app:app\n",
    },
    "p2-fastapi": {
        "requirements.txt": "fastapi==0.115.6\nuvicorn==0.34.0\n",
        "main.py": "from fastapi import FastAPI\nfrom fastapi.responses import PlainTextResponse\n\napp = FastAPI()\n\n\n"
                   "@app.get('/', response_class=PlainTextResponse)\ndef inicio():\n    return 'ok'\n",
        "README.md": "Arranque: uvicorn main:app --host 0.0.0.0 --port 8080\n",
    },
    "p3-sin-dependencias": {
        "server.py": "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n\nclass H(BaseHTTPRequestHandler):\n"
                     "    def do_GET(self):\n        self.send_response(200)\n        self.end_headers()\n        self.wfile.write(b'ok')\n\n\n"
                     "HTTPServer(('0.0.0.0', 8080), H).serve_forever()\n",
    },
    "p4-pyproject": {
        "pyproject.toml": "[build-system]\nrequires = [\"setuptools>=75\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\n"
                          "name = \"servicio\"\nversion = \"1.0.0\"\nrequires-python = \">=3.11\"\ndependencies = [\"flask==3.1.0\", "
                          "\"waitress==3.0.2\"]\n\n[project.scripts]\nservicio = \"servicio.main:run\"\n",
        "src/servicio/__init__.py": "",
        "src/servicio/main.py": "from flask import Flask\nfrom waitress import serve\n\napp = Flask(__name__)\n\n\n@app.get('/')\n"
                                "def inicio():\n    return 'ok'\n\n\ndef run():\n    serve(app, host='0.0.0.0', port=8080)\n",
    },
    "p5-aiohttp": {
        "requirements.txt": "aiohttp==3.11.11\n",
        "app.py": "from aiohttp import web\n\n\nasync def inicio(request):\n    return web.Response(text='ok')\n\n\napp = web.Application()\n"
                  "app.add_routes([web.get('/', inicio)])\n\nif __name__ == '__main__':\n    web.run_app(app, host='0.0.0.0', port=8080)\n",
    },
    # ───────── Go ─────────
    "g1-net-http": {
        "go.mod": "module ejemplo.com/servidor\n\ngo 1.24\n",
        "main.go": "package main\n\nimport (\n\t\"log\"\n\t\"net/http\"\n)\n\nfunc main() {\n\thttp.HandleFunc(\"/\", func(w http.ResponseWriter, "
                   "r *http.Request) { w.Write([]byte(\"ok\")) })\n\tlog.Fatal(http.ListenAndServe(\":8080\", nil))\n}\n",
    },
    "g2-gin": {
        "go.mod": "module ejemplo.com/api-gin\n\ngo 1.24\n\nrequire github.com/gin-gonic/gin v1.10.0\n",
        "main.go": "package main\n\nimport \"github.com/gin-gonic/gin\"\n\nfunc main() {\n\tr := gin.Default()\n\tr.GET(\"/\", func(c *gin.Context) "
                   "{ c.String(200, \"ok\") })\n\tr.Run(\":8080\")\n}\n",
    },
    "g3-chi": {
        "go.mod": "module ejemplo.com/api-chi\n\ngo 1.24\n\nrequire github.com/go-chi/chi/v5 v5.2.0\n",
        "main.go": "package main\n\nimport (\n\t\"net/http\"\n\n\t\"github.com/go-chi/chi/v5\"\n)\n\nfunc main() {\n\tr := chi.NewRouter()\n"
                   "\tr.Get(\"/\", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte(\"ok\")) })\n\thttp.ListenAndServe(\":8080\", r)\n}\n",
    },
    "g4-cmd-internal": {
        "go.mod": "module ejemplo.com/servicio\n\ngo 1.24\n",
        "cmd/servidor/main.go": "package main\n\nimport (\n\t\"log\"\n\t\"net/http\"\n\n\t\"ejemplo.com/servicio/internal/saludo\"\n)\n\n"
                                "func main() {\n\thttp.HandleFunc(\"/\", saludo.Handler)\n\tlog.Fatal(http.ListenAndServe(\":8080\", nil))\n}\n",
        "internal/saludo/saludo.go": "package saludo\n\nimport \"net/http\"\n\nfunc Handler(w http.ResponseWriter, r *http.Request) "
                                     "{ w.Write([]byte(\"ok\")) }\n",
    },
    "g5-embed": {
        "go.mod": "module ejemplo.com/web\n\ngo 1.24\n",
        "main.go": "package main\n\nimport (\n\t\"embed\"\n\t\"io/fs\"\n\t\"log\"\n\t\"net/http\"\n)\n\n//go:embed static\nvar static embed.FS\n\n"
                   "func main() {\n\tsub, _ := fs.Sub(static, \"static\")\n\thttp.Handle(\"/\", http.FileServer(http.FS(sub)))\n"
                   "\tlog.Fatal(http.ListenAndServe(\":8080\", nil))\n}\n",
        "static/index.html": "ok\n",
    },
    # ───────── Java ─────────
    "j1-maven-sin-dependencias": {
        "pom.xml": POM_BASE.format(art="servidor", deps="", plugins=JAR_PLUGIN),
        "src/main/java/app/Main.java": JAVA_HTTP,
    },
    "j2-spring-boot": {
        "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.1</version>
  </parent>
  <groupId>com.ejemplo</groupId>
  <artifactId>api-spring</artifactId>
  <version>1.0.0</version>
  <properties>
    <java.version>21</java.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
""",
        "src/main/java/com/ejemplo/Aplicacion.java": """package com.ejemplo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class Aplicacion {
    @GetMapping("/")
    public String inicio() { return "ok"; }

    public static void main(String[] args) { SpringApplication.run(Aplicacion.class, args); }
}
""",
        "src/main/resources/application.properties": "server.port=8080\n",
    },
    "j3-un-archivo": {
        "App.java": JAVA_HTTP.replace("package app;\n\n", "").replace("public class Main", "public class App"),
        "README.md": "Una sola clase, sin Maven ni Gradle: javac App.java && java App\n",
    },
    "j4-maven-gson-shade": {
        "pom.xml": POM_BASE.format(art="api-gson", deps="""  <dependencies>
    <dependency>
      <groupId>com.google.code.gson</groupId>
      <artifactId>gson</artifactId>
      <version>2.11.0</version>
    </dependency>
  </dependencies>""", plugins=SHADE_PLUGIN),
        "src/main/java/app/Main.java": JAVA_HTTP.replace('"ok".getBytes()', 'new com.google.gson.Gson().toJson("ok").replace("\\"", "").getBytes()'),
    },
    "j5-javalin": {
        "pom.xml": POM_BASE.format(art="api-javalin", deps="""  <dependencies>
    <dependency>
      <groupId>io.javalin</groupId>
      <artifactId>javalin</artifactId>
      <version>6.4.0</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-simple</artifactId>
      <version>2.0.16</version>
    </dependency>
  </dependencies>""", plugins=SHADE_PLUGIN),
        "src/main/java/app/Main.java": "package app;\n\nimport io.javalin.Javalin;\n\npublic class Main {\n    public static void main(String[] args) {\n"
                                       "        Javalin.create().get(\"/\", ctx -> ctx.result(\"ok\")).start(8080);\n    }\n}\n",
    },
}


def escribir():
    for app, archivos in APPS.items():
        for rel, txt in archivos.items():
            p = os.path.join(AQUI, "apps", app, rel)
            if rel == "go.mod" and os.path.exists(os.path.join(AQUI, "apps", app, "go.sum")):
                continue  # `go mod tidy` ya lo completó (requires indirectos): no se pisa
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(txt)
    print(len(APPS), "apps escritas")


def locks():
    for app in APPS:
        d = os.path.join(AQUI, "apps", app)
        if app.startswith("n") and "dependencies" in APPS[app]["package.json"]:
            cmd = ["node:22.12.0-bookworm-slim", "npm", "install", "--package-lock-only", "--no-audit", "--no-fund"]
        elif app.startswith("g") and "require" in APPS[app]["go.mod"]:
            cmd = ["golang:1.27.2", "go", "mod", "tidy"]
        else:
            continue
        r = subprocess.run(["docker", "run", "--rm", "--name", f"v711-lock-{app}", "-v", f"{d}:/app", "-w", "/app"] + cmd,
                           capture_output=True, text=True)
        print(app, r.returncode, r.stderr[-300:])


if __name__ == "__main__":
    escribir()
    if "--locks" in sys.argv:
        locks()
