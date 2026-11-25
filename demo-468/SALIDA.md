$ kubectl version | grep Server
Server Version: v1.34.0

# 1) RBAC
$ kubectl -n tienda create role leer-pods --verb=get,list,watch --resource=pods
$ kubectl -n tienda create rolebinding lector-lee --role=leer-pods --serviceaccount=tienda:lector
$ kubectl auth can-i get pods -n tienda --as=system:serviceaccount:tienda:lector
yes
$ kubectl auth can-i delete pods -n tienda --as=system:serviceaccount:tienda:lector
no
$ kubectl auth can-i get secrets -n tienda --as=system:serviceaccount:tienda:lector
no
$ kubectl auth can-i get pods -n kube-system --as=system:serviceaccount:tienda:lector
no

# 2) Pod Security Admission
$ kubectl label namespace tienda pod-security.kubernetes.io/enforce=restricted
namespace/tienda labeled
$ kubectl -n tienda apply -f privilegiado.yaml
Error from server (Forbidden): error when creating "privilegiado.yaml": pods "privilegiado" is forbidden: 
violates PodSecurity "restricted:latest": privileged (container "app" must not set 
securityContext.privileged=true), allowPrivilegeEscalation != false (container "app" must set 
securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "app" must set 
securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "app" must set 
securityContext.runAsNonRoot=true), seccompProfile (pod or container "app" must set 
securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
$ kubectl -n tienda apply -f correcto.yaml
pod/correcto created

# 3) NetworkPolicy
$ # sin políticas
  cliente -> servidor: responde
  otro -> servidor: responde
$ kubectl -n red apply -f denegar.yaml
networkpolicy.networking.k8s.io/denegar-todo created
  cliente -> servidor: sin respuesta (3 s)
  otro -> servidor: sin respuesta (3 s)
$ kubectl -n red apply -f permitir.yaml
networkpolicy.networking.k8s.io/cliente-a-servidor created
  cliente -> servidor: responde
  otro -> servidor: sin respuesta (3 s)

$ kind delete cluster   # clúster borrado
$ kind version
kind v0.30.0 go1.26.5 windows/amd64
