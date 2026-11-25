mock_provider "docker" {}
mock_provider "http" {
  mock_data "http" {
    defaults = { status_code = 200 }
  }
}

run "sin_docker_el_nombre_sigue_bien" {
  command = apply
  assert {
    condition     = docker_container.web.name == "pruebas-web"
    error_message = "El contenedor no se llama como debe."
  }
}
