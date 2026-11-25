$ docker run --rm debian:12 dpkg-query -W liblzma5
liblzma5:amd64	5.4.1-1+deb12u2
  ingenuo:  5.4.1 -> no afectada
  mejor:    5.4.1 -> no afectada

$ docker run --rm ubuntu:24.04 dpkg-query -W liblzma5
liblzma5:amd64	5.6.1+really5.4.5-1ubuntu0.3
  ingenuo:  5.6.1 -> AFECTADA
  mejor:    5.4.5 -> no afectada

$ docker run --rm alpine:3.20 apk info -v 2>/dev/null | grep '^xz-libs'
(nada)
  ingenuo:  no instalada
  mejor:    no instalada

$ docker run --rm fedora:41 rpm -q xz-libs
xz-libs-5.8.1-2.fc41.x86_64
  ingenuo:  5.8.1 -> no afectada
  mejor:    5.8.1 -> no afectada

$ # los dos comprobadores, contra las versiones afectadas (solo texto)
  versión: 5.6.0-0.2
  ingenuo:  5.6.0 -> AFECTADA
  mejor:    5.6.0 -> AFECTADA
  versión: 5.6.1-1
  ingenuo:  5.6.1 -> AFECTADA
  mejor:    5.6.1 -> AFECTADA
  versión: 5.6.1+really5.4.5-1
  ingenuo:  5.6.1 -> AFECTADA
  mejor:    5.4.5 -> no afectada
  versión: 5.6.2-1
  ingenuo:  5.6.2 -> no afectada
  mejor:    5.6.2 -> no afectada

$ git ls-remote --tags https://github.com/tukaani-project/xz | grep -E "v5\.6\.[0-9]+$" | sed "s|.*/||"
v5.6.0
v5.6.1
v5.6.2
v5.6.3
v5.6.4
