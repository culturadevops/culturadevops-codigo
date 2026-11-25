# Lo correcto: la ruta real del KV v2 (secret/data/...) y solo la de la tienda.
path "secret/data/tienda/*" {
  capabilities = ["read"]
}
