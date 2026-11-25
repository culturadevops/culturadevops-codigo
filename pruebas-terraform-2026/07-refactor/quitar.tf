removed {
  from = docker_container.a_mano
  lifecycle {
    destroy = false
  }
}
