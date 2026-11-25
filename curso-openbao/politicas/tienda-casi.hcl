# La que parece bien: la ruta que escribes con `bao kv get`. Pero el KV v2 guarda en secret/data/.
path "secret/tienda/*" {
  capabilities = ["read"]
}
