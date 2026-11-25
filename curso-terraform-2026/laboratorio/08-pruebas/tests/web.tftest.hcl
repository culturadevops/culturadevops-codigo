run "el_puerto_por_omision_es_8120" {
  command = plan
  # En plan la web todavía no existe: el check tiene que fallar, y lo decimos.
  expect_failures = [check.la_web_responde]
  assert {
    condition     = docker_container.web.ports[0].external == 8120
    error_message = "El puerto publicado no es el esperado."
  }
}

run "crea_el_contenedor_de_verdad" {
  command = apply
  variables {
    puerto = 8121
  }
  assert {
    condition     = output.url == "http://localhost:8121"
    error_message = "La URL no apunta al puerto que pedí."
  }
  assert {
    condition     = docker_container.web.name == "pruebas-web"
    error_message = "El contenedor no se llama como debe."
  }
}
