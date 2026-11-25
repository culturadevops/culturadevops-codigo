# -*- coding: utf-8 -*-
"""correr.py — «¿Postgres o MySQL? Lo medí» (cultura-devops 839, pedido del dueño 2026-11-05).

    python correr.py              → SALIDA.md
    python correr.py --preparar   → solo construye/baja imágenes (sin candado, sin medir)

Montaje (igual para los dos):
  · imágenes OFICIALES fijadas (postgres:18.6, mysql:9.7.4), 2 CPU y 1 GiB, datos en un volumen con nombre que se BORRA al final;
  · configuración de producción razonable e igualada: 256 MB de caché propia (shared_buffers / innodb_buffer_pool_size),
    100 conexiones máx., durabilidad de fábrica (fsync en cada commit en los dos; MySQL con su binlog de fábrica), SIN TLS en
    los dos (la imagen de PostgreSQL no lo trae activado; a MySQL se le quita con --tls-version=);
  · la carga: sysbench 1.0.20 (los MISMOS scripts OLTP contra los dos) desde OTRO contenedor de la misma red, 4 CPU;
  · LOS MISMOS DATOS: 8 tablas × 100.000 filas que genera sysbench UNA vez y se exportan a CSV; cada base crea el esquema de
    sysbench (tabla + índice en k) y carga ese CSV (\\copy en PostgreSQL, LOAD DATA LOCAL en MySQL; esa carga se cronometra).
    Se generan una vez porque sysbench con la misma semilla NO da las mismas filas en las dos bases (comprobado: 2026-11-05).
    Antes de medir se comprueba tabla por tabla que las dos tienen lo mismo. Si no, exit 1.
"""
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun as K  # noqa: E402
from comun import w, sh, ok, num  # noqa: E402

SB = "hvs-sysbench:1"
CSV = "hvs-csv"
TABLAS, FILAS = 8, 100_000
SEG, SEG_CAL, REPES = 30, 10, 3
PRUEBAS = [("oltp_point_select", 16, "Lecturas por clave (SELECT … WHERE id = ?)"),
           ("oltp_read_only", 8, "Solo lectura: 14 consultas por transacción (claves, rangos, SUM, ORDER BY, DISTINCT)"),
           ("oltp_read_write", 8, "Lectura y escritura: las de arriba + 2 UPDATE, 1 DELETE y 1 INSERT por transacción, con COMMIT")]

D = {
    "postgres": dict(nombre="PostgreSQL", img="postgres:18.6", vol="hvs-pgdata", dest="/var/lib/postgresql",
                     datos="/var/lib/postgresql/18/docker",
                     env={"POSTGRES_USER": "sbtest", "POSTGRES_PASSWORD": "banco", "POSTGRES_DB": "sbtest"},
                     cmd=["-c", "shared_buffers=256MB", "-c", "effective_cache_size=512MB", "-c", "max_connections=100"],
                     listo=["pg_isready", "-h", "127.0.0.1", "-U", "sbtest", "-d", "sbtest"],
                     sb=["--db-driver=pgsql", "--pgsql-host=db", "--pgsql-user=sbtest", "--pgsql-password=banco", "--pgsql-db=sbtest"],
                     sql=lambda q: ["psql", "-v", "ON_ERROR_STOP=1", "-h", "db", "-U", "sbtest", "-d", "sbtest", "-At", "-F", "|", "-c", q],
                     senv=["-e", "PGPASSWORD=banco"],
                     cargar=lambda i: f"\\copy sbtest{i} (id, k, c, pad) FROM '/csv/sbtest{i}.csv' CSV",
                     analizar=lambda i: f"ANALYZE sbtest{i}"),
    "mysql": dict(nombre="MySQL", img="mysql:9.7.4", vol="hvs-mydata", dest="/var/lib/mysql", datos="/var/lib/mysql",
                  env={"MYSQL_ROOT_PASSWORD": "banco", "MYSQL_DATABASE": "sbtest", "MYSQL_USER": "sbtest", "MYSQL_PASSWORD": "banco"},
                  # --tls-version= deja la base SIN TLS, como la imagen oficial de PostgreSQL: las dos van en claro, en igualdad.
                  # --local-infile=1 solo para cargar el CSV (LOAD DATA LOCAL), el equivalente de \copy de psql.
                  cmd=["--innodb-buffer-pool-size=256M", "--max-connections=100", "--tls-version=", "--local-infile=1"],
                  # sin TLS, caching_sha2_password necesita la clave pública del servidor (o la contraseña ya en caché)
                  listo=["mysqladmin", "-h127.0.0.1", "--protocol=tcp", "-usbtest", "-pbanco", "--get-server-public-key", "ping"],
                  sb=["--db-driver=mysql", "--mysql-host=db", "--mysql-user=sbtest", "--mysql-password=banco", "--mysql-db=sbtest"],
                  sql=lambda q: ["mysql", "-h", "db", "-usbtest", "-pbanco", "--local-infile=1", "-N", "-B", "sbtest", "-e", q],
                  senv=[],
                  cargar=lambda i: (f"LOAD DATA LOCAL INFILE '/csv/sbtest{i}.csv' INTO TABLE sbtest{i} FIELDS TERMINATED BY ',' "
                                    "OPTIONALLY ENCLOSED BY '\"' (id, k, c, pad)"),
                  analizar=lambda i: f"ANALYZE TABLE sbtest{i}"),
}


def arrancar(k, nuevo=False):
    d = D[k]
    K.rm("db")
    if nuevo:
        sh(["docker", "volume", "rm", "-f", d["vol"]])
    args = ["docker", "run", "-d", "--rm", "--name", "db", "--network", K.RED, "--cpus", K.CPUS, "--memory", K.MEM,
            "-v", f"{d['vol']}:{d['dest']}"]
    for e, v in d["env"].items():
        args += ["-e", f"{e}={v}"]
    t0 = time.perf_counter()
    ok(args + [d["img"]] + d["cmd"])
    return t0


def esperar(k, t0, limite=300):
    while True:
        r = sh(["docker", "exec", "db"] + D[k]["listo"])
        if r.returncode == 0:
            seg = time.perf_counter() - t0
            if k == "mysql":
                # caching_sha2_password sin TLS: una conexión por el socket local deja la contraseña en caché y desde ahí
                # los clientes por TCP en claro entran (sin esto, «Authentication requires secure connection»). No cuenta en el tiempo.
                for _ in range(100):
                    if sh(["docker", "exec", "db", "mysql", "-usbtest", "-pbanco", "-e", "SELECT 1"]).returncode == 0:
                        break
                    time.sleep(0.1)
            return seg
        if time.perf_counter() - t0 > limite:
            logs = sh(["docker", "logs", "db"])
            raise SystemExit(f"⛔ {k} no arrancó:\n{logs.stdout[-1500:]}\n{logs.stderr[-1500:]}")
        time.sleep(0.05)


def parar():
    t0 = time.perf_counter()
    ok(["docker", "stop", "-t", "120", "db"])
    while sh(["docker", "inspect", "db"]).returncode == 0:
        time.sleep(0.1)
    return time.perf_counter() - t0


def sql(k, q):
    r = ok(["docker", "run", "--rm", "--network", K.RED, "-v", f"{CSV}:/csv"] + D[k]["senv"] + [SB] + D[k]["sql"](q))
    return r.stdout.strip()


def sysbench(k, prueba, hilos, seg, accion="run", filas=FILAS):
    args = ["docker", "run", "--rm", "--network", K.RED, "--cpus", "4", SB, "sysbench", prueba] + D[k]["sb"] + [
        f"--tables={TABLAS}", f"--table-size={filas}", f"--threads={hilos}", "--rand-seed=1"]
    if accion == "run":
        args += [f"--time={seg}", "--report-interval=0", "--percentile=99", "--histogram=on"]
    r = sh(args + [accion])
    if r.returncode != 0:
        raise SystemExit(f"⛔ sysbench {prueba} {accion} contra {k}:\n{r.stdout[-2500:]}\n{r.stderr[-2500:]}")
    return r.stdout


def leer(t):
    tps = float(re.search(r"transactions:\s+\d+\s+\(([\d.]+) per sec", t).group(1))
    qps = float(re.search(r"queries:\s+\d+\s+\(([\d.]+) per sec", t).group(1))
    p99 = float(re.search(r"99th percentile:\s+([\d.]+)", t).group(1))
    errores = int(re.search(r"ignored errors:\s+(\d+)", t).group(1))
    hist = [(float(v), int(c)) for v, c in re.findall(r"^\s+([\d.]+) \|[* ]*\s(\d+)\s*$", t, re.M)]
    total, acum, p50 = sum(c for _, c in hist), 0, float("nan")
    for v, c in hist:
        acum += c
        if acum >= total / 2:
            p50 = v
            break
    return dict(tps=tps, qps=qps, p50=p50, p99=p99, errores=errores)


def generar_csv():
    """Los datos, UNA vez: sysbench prepare en un PostgreSQL de paso, y cada tabla a /csv/sbtestN.csv (volumen hvs-csv)."""
    sh(["docker", "volume", "rm", "-f", CSV])
    ok(["docker", "volume", "create", CSV])
    arrancar("postgres", nuevo=True)
    esperar("postgres", time.perf_counter())
    sysbench("postgres", "oltp_read_write", 8, 0, accion="prepare")
    for i in range(1, TABLAS + 1):
        sql("postgres", f"\\copy (SELECT id, k, c, pad FROM sbtest{i} ORDER BY id) TO '/csv/sbtest{i}.csv' CSV")
    K.rm("db")
    ok(["docker", "volume", "rm", "-f", D["postgres"]["vol"]])
    r = ok(["docker", "run", "--rm", "-v", f"{CSV}:/csv", "--entrypoint", "sh", SB, "-c", "wc -l /csv/*.csv | tail -1; du -cb /csv/*.csv | tail -1"])
    filas, bytes_ = r.stdout.split()[0], r.stdout.split()[2]
    return int(filas), int(bytes_) / 1048576


def cargar(k):
    """Esquema de sysbench (tabla + índice secundario en k, vacías) y la carga del MISMO CSV, una tabla tras otra. Se cronometra la carga."""
    sysbench(k, "oltp_read_write", 1, 0, accion="prepare", filas=0)
    t0 = time.perf_counter()
    for i in range(1, TABLAS + 1):
        sql(k, D[k]["cargar"](i))
    seg = time.perf_counter() - t0
    for i in range(1, TABLAS + 1):
        sql(k, D[k]["analizar"](i))
    return seg


def huella(k):
    """Lo que de verdad hay en cada base: filas, suma de k, largo total de c y de pad, y dos filas sueltas, tabla por tabla."""
    filas = []
    for i in range(1, TABLAS + 1):
        a = sql(k, f"SELECT COUNT(*), SUM(k), SUM(LENGTH(c)), SUM(LENGTH(pad)) FROM sbtest{i}")
        b = sql(k, f"SELECT id, k, c FROM sbtest{i} WHERE id IN (1, {FILAS}) ORDER BY id")
        filas.append(re.sub(r"[\t|]", " ", a) + " · " + re.sub(r"\s+", " ", re.sub(r"[\t|]", " ", b)))
    return filas


def huella_csv():
    """La misma huella, calculada sobre el CSV (sin pasar por ninguna base): es la referencia contra la que se compara cada una."""
    prog = ("{n++; k+=$2; c=$3; sub(/ +$/,\"\",c); p=$4; sub(/ +$/,\"\",p); lc+=length(c); lp+=length(p); "
            "if ($1==1) r1=$1\" \"$2\" \"c; if ($1==%d) rn=$1\" \"$2\" \"c} "
            "END {printf \"%%.0f %%.0f %%.0f %%.0f · %%s %%s\\n\", n, k, lc, lp, r1, rn}") % FILAS
    filas = []
    for i in range(1, TABLAS + 1):
        r = ok(["docker", "run", "--rm", "-v", f"{CSV}:/csv", "--entrypoint", "awk", SB, "-F,", prog, f"/csv/sbtest{i}.csv"])
        filas.append(r.stdout.strip())
    return filas


def disco(k):
    d = D[k]
    total = int(ok(["docker", "exec", "db", "du", "-sb", d["datos"]]).stdout.split()[0]) / 1048576
    if k == "postgres":
        tablas = float(sql(k, "SELECT SUM(pg_total_relation_size(c.oid)) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                              "WHERE n.nspname = 'public' AND c.relkind = 'r'")) / 1048576
        extra = "WAL " + num(int(ok(["docker", "exec", "db", "du", "-sb", d["datos"] + "/pg_wal"]).stdout.split()[0]) / 1048576) + " MiB"
    else:
        tablas = float(sql(k, "SELECT SUM(data_length + index_length) FROM information_schema.tables WHERE table_schema = 'sbtest'")) / 1048576
        bl = ok(["docker", "exec", "db", "sh", "-c", f"du -cb {d['datos']}/binlog.0* | tail -1"]).stdout.split()[0]
        extra = "binlog " + num(int(bl) / 1048576) + " MiB"
    return tablas, total, extra


def main():
    K.red()
    ok(["docker", "build", "-q", "-f", str(AQUI.parent / "_comun" / "Dockerfile.sysbench"), "-t", SB, str(AQUI.parent / "_comun")])
    for k in D:
        if sh(["docker", "image", "inspect", D[k]["img"]]).returncode != 0:
            ok(["docker", "pull", "-q", D[k]["img"]])
    if "--preparar" in sys.argv:
        print("[ok] imágenes listas")
        return
    K.OUT.clear()
    res = {k: {} for k in D}
    with K.candado("postgres-mysql"):
        w("# SALIDA — ¿Postgres o MySQL? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)\n")
        w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}, bajo el candado _logs/banco.lock. Regenerable con `python correr.py`. "
          "⛔ Ninguna cifra de blog: todo salió de aquí.\n")
        w(f"- PostgreSQL: `{ok(['docker', 'run', '--rm', D['postgres']['img'], 'postgres', '--version']).stdout.strip()}` — imagen oficial `postgres:18.6`")
        w(f"- MySQL: `{ok(['docker', 'run', '--rm', D['mysql']['img'], 'mysqld', '--version']).stdout.strip()}` — imagen oficial `mysql:9.7.4`")
        w(f"- Carga: `{ok(['docker', 'run', '--rm', SB, 'sysbench', '--version']).stdout.strip()}` (Ubuntu 24.04) desde otro contenedor con 4 CPU.")
        w(f"- Docker `{sh(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip()}` (Docker Desktop, Windows 11, 24 hilos); "
          f"base con {K.CPUS} CPU y {K.MEM}; datos en un volumen de Docker (disco de la VM de WSL2, el mismo para las dos).")
        w("- Config: PostgreSQL `shared_buffers=256MB effective_cache_size=512MB max_connections=100`; MySQL "
          "`innodb_buffer_pool_size=256M max_connections=100 tls-version=(vacío)`. Lo demás, de fábrica (commit con fsync en las dos; "
          "MySQL con binlog). Sin TLS en ninguna de las dos.")
        filas, mib = generar_csv()
        w(f"- Datos: {TABLAS} tablas × {num(FILAS, 0)} filas generadas UNA vez por sysbench (--rand-seed=1) y exportadas a CSV "
          f"({num(filas, 0)} líneas, {num(mib)} MiB); las dos bases cargan ESE archivo.\n")

        ref = huella_csv()
        w("## 1 · Lo que despliegas\n")
        w("| base | imagen | tamaño en disco |")
        w("|---|---|---|")
        for k in D:
            w(f"| {D[k]['nombre']} | `{D[k]['img']}` | {num(K.tam_imagen(D[k]['img']))} MiB |")
        w()

        for k in D:
            ini = []
            for i in range(REPES):
                t0 = arrancar(k, nuevo=True)
                ini.append(esperar(k, t0))
                if i < REPES - 1:
                    parar()
            res[k]["init"] = K.mediana(ini)
            time.sleep(10)
            res[k]["reposo"] = K.stats("db")[0]
            res[k]["carga"] = cargar(k)
            res[k]["huella"] = huella(k)
            if res[k]["huella"] != ref:  # ⛔ antes de medir nada de carga
                for a, b in zip(ref, res[k]["huella"]):
                    w(f"- CSV `{a[:110]}`")
                    w(f"- {k} `{b[:110]}`")
                K.rm("db")
                K.guardar(AQUI / "SALIDA-NO-COMPARABLE.md")
                raise SystemExit(f"{k} no tiene los datos del CSV: no se compara")
            res[k]["disco"] = disco(k)
            for prueba, hilos, _ in PRUEBAS:
                sysbench(k, prueba, hilos, SEG_CAL)
                with K.Muestreo("db") as m:
                    r = leer(sysbench(k, prueba, hilos, SEG))
                r.update(mem=m.mem_max, cpu=m.cpu_media)
                res[k][prueba] = r
            if k == "mysql":
                res[k]["ssl"] = sql(k, "SHOW GLOBAL STATUS LIKE 'Ssl_accepts'").split()[-1]
            else:
                res[k]["ssl"] = sql(k, "SELECT COUNT(*) FILTER (WHERE ssl) || ' de ' || COUNT(*) FROM pg_stat_ssl")
            stops, reinicios = [], []
            for _ in range(REPES):
                stops.append(parar())
                t0 = arrancar(k)
                reinicios.append(esperar(k, t0))
            res[k]["stop"], res[k]["reinicio"] = K.mediana(stops), K.mediana(reinicios)
            K.rm("db")
            ok(["docker", "volume", "rm", "-f", D[k]["vol"]])

        w("## 0 · ¿Tienen los mismos datos? (después de cargar, antes de medir)\n")
        w(f"Por tabla: filas · suma de k · largo total de c · largo total de pad · filas id=1 e id={FILAS} (id, k, c). Referencia = "
          "la misma cuenta hecha con awk sobre el CSV; cada base se comprobó contra ella justo después de cargar y ANTES de medir.\n")
        iguales = True
        for i in range(TABLAS):
            a, b, c = ref[i], res["postgres"]["huella"][i], res["mysql"]["huella"][i]
            igual = a == b == c
            iguales &= igual
            w(f"- sbtest{i + 1}: CSV = PostgreSQL = MySQL → {'igual' if igual else '⛔ DISTINTO'} — `{a[:100]}…`")
        w(f"\nTLS: MySQL `Ssl_accepts` al terminar = {res['mysql']['ssl']}; PostgreSQL, conexiones con TLS = {res['postgres']['ssl']}. "
          "Las dos van en claro.\n")
        if not iguales:
            K.guardar(AQUI / "SALIDA-NO-COMPARABLE.md")
            raise SystemExit("las dos bases no tienen los mismos datos: no se compara")

        w("## 2 · Arranque, carga del CSV, disco y memoria en reposo\n")
        w("Arranque = `docker run` hasta que la base acepta conexiones TCP (sonda con `docker exec`, resolución ~0,1 s; mediana de "
          f"{REPES}). «Primera vez» incluye crear la base vacía (initdb / --initialize). Carga = las 8 tablas desde el CSV, una tras otra, "
          "con el índice en k ya creado.\n")
        w("| base | primera vez (volumen vacío) | reinicio con datos | parada limpia | cargar 800.000 filas | tablas + índices | carpeta de datos | memoria en reposo |")
        w("|---|---|---|---|---|---|---|---|")
        for k in D:
            r = res[k]
            t, tot, extra = r["disco"]
            w(f"| {D[k]['nombre']} | {num(r['init'])} s | {num(r['reinicio'])} s | {num(r['stop'])} s | {num(r['carga'])} s | "
              f"{num(t)} MiB | {num(tot)} MiB ({extra}) | {num(r['reposo'])} MiB |")
        w()
        w(f"## 3 · Carga OLTP (sysbench, {SEG} s tras {SEG_CAL} s de calentamiento)\n")
        w("Memoria = máximo de `docker stats` durante la carga (con 1 GiB de límite); CPU = media (200 % = las 2 CPU llenas). "
          "p50 sale del histograma de sysbench; p99, de su percentil. «Errores» = los que sysbench ignora y reintenta (choques entre "
          "transacciones).\n")
        for prueba, hilos, desc in PRUEBAS:
            w(f"### {prueba} · {hilos} hilos — {desc}\n")
            w("| base | transacciones/s | consultas/s | p50 | p99 | memoria máx. | CPU media | errores |")
            w("|---|---|---|---|---|---|---|---|")
            for k in D:
                r = res[k][prueba]
                w(f"| {D[k]['nombre']} | {num(r['tps'], 0)} | {num(r['qps'], 0)} | {num(r['p50'], 2)} ms | {num(r['p99'], 2)} ms | "
                  f"{num(r['mem'])} MiB | {num(r['cpu'], 0)} % | {r['errores']} |")
            w()
        for k in D:
            sh(["docker", "volume", "rm", "-f", D[k]["vol"]])
        sh(["docker", "volume", "rm", "-f", CSV])
    K.guardar(AQUI / "SALIDA.md")


if __name__ == "__main__":
    main()
