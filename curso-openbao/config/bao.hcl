# El servidor de las lecciones 2 a 6: almacenamiento integrado (raft) en un volumen, y sin TLS.
# ⚠️ tls_disable SOLO en el laboratorio: en una máquina de verdad, el listener va con TLS.
# (OpenBao 2.7 ya no tiene el almacenamiento «file»: responde «unknown storage type file».)
storage "raft" {
  path    = "/openbao/file"
  node_id = "nodo-1"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

api_addr      = "http://127.0.0.1:8200"
cluster_addr  = "http://127.0.0.1:8201"
