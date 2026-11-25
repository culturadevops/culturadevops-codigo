"""Operador de PaginaWeb con kopf: un ConfigMap con el HTML, un Deployment de nginx y un Service.
VIGILAR_HIJOS=1 añade la vigilancia de los Deployment que crea (la deriva)."""
import os

import kopf
import kubernetes
from kubernetes.client.rest import ApiException

kubernetes.config.load_kube_config()
core = kubernetes.client.CoreV1Api()
apps = kubernetes.client.AppsV1Api()
GRUPO, VERSION, PLURAL = "web.culturadevops.dev", "v1", "paginawebs"


def objetos(nombre, spec):
    html = f"<h1>{spec['mensaje']}</h1>\n"
    etiquetas = {"app": nombre, "gestionado-por": "paginaweb-kopf"}
    cm = {"metadata": {"name": nombre, "labels": etiquetas}, "data": {"index.html": html}}
    dep = {"metadata": {"name": nombre, "labels": etiquetas},
           "spec": {"replicas": spec.get("replicas", 1), "selector": {"matchLabels": {"app": nombre}},
                    "template": {"metadata": {"labels": {"app": nombre}},
                                 "spec": {"containers": [{"name": "nginx", "image": "nginx:1.29-alpine",
                                                          "volumeMounts": [{"name": "html", "mountPath": "/usr/share/nginx/html"}]}],
                                          "volumes": [{"name": "html", "configMap": {"name": nombre}}]}}}}
    svc = {"metadata": {"name": nombre, "labels": etiquetas},
           "spec": {"selector": {"app": nombre}, "ports": [{"port": 80}]}}
    return cm, dep, svc


def crear_o_actualizar(leer, crear, parchear, ns, cuerpo):
    try:
        leer(cuerpo["metadata"]["name"], ns)
        parchear(cuerpo["metadata"]["name"], ns, cuerpo)
        return "actualizado"
    except ApiException as e:
        if e.status != 404:
            raise
        crear(ns, cuerpo)
        return "creado"


@kopf.on.create(GRUPO, VERSION, PLURAL)
@kopf.on.update(GRUPO, VERSION, PLURAL)
@kopf.on.resume(GRUPO, VERSION, PLURAL)
def reconciliar(spec, name, namespace, body, logger, **_):
    cm, dep, svc = objetos(name, spec)
    for o in (cm, dep, svc):
        kopf.adopt(o, owner=body)          # ownerReferences: la PaginaWeb es la dueña
    r = [crear_o_actualizar(core.read_namespaced_config_map, core.create_namespaced_config_map,
                            core.patch_namespaced_config_map, namespace, cm),
         crear_o_actualizar(apps.read_namespaced_deployment, apps.create_namespaced_deployment,
                            apps.patch_namespaced_deployment, namespace, dep),
         crear_o_actualizar(core.read_namespaced_service, core.create_namespaced_service,
                            core.patch_namespaced_service, namespace, svc)]
    logger.info(f"configmap {r[0]} · deployment {r[1]} · service {r[2]}")


if os.environ.get("VIGILAR_HIJOS") == "1":
    @kopf.on.event("apps", "v1", "deployments", labels={"gestionado-por": "paginaweb-kopf"})
    def vigilar_deployment(event, body, namespace, logger, **_):
        duenos = [o for o in body["metadata"].get("ownerReferences", []) if o["kind"] == "PaginaWeb"]
        if not duenos:
            return
        nombre = duenos[0]["name"]
        crd = kubernetes.client.CustomObjectsApi()
        try:
            pagina = crd.get_namespaced_custom_object(GRUPO, VERSION, namespace, PLURAL, nombre)
        except ApiException as e:
            if e.status == 404:
                return                      # la dueña ya no existe: el borrado en cascada está en marcha
            raise
        if event["type"] == "DELETED":
            logger.info(f"alguien borró el deployment {body['metadata']['name']}: lo vuelvo a crear")
            reconciliar(pagina["spec"], nombre, namespace, pagina, logger)
            return
        listas = body.get("status", {}).get("readyReplicas", 0) or 0
        if pagina.get("status", {}).get("listas") != listas:
            crd.patch_namespaced_custom_object_status(GRUPO, VERSION, namespace, PLURAL, nombre,
                                                      {"status": {"listas": listas}})
