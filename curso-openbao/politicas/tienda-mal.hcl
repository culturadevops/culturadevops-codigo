# La trampa: un comodín demasiado ancho. Lee los secretos de la tienda... y los de todos.
path "secret/*" {
  capabilities = ["read"]
}
