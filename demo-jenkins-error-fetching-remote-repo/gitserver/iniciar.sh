#!/bin/sh
# Crea los dos repos con un commit, y arranca sshd, fcgiwrap (como el usuario git) y nginx.
set -e
crear() {
  mkdir -p "$(dirname "$1")"
  git init -q --bare -b main "$1"
  tmp=$(mktemp -d)
  git -C "$tmp" init -q -b main
  echo "# $2" > "$tmp/README.md"
  git -C "$tmp" add README.md
  git -C "$tmp" -c user.name=demo -c user.email=demo@example.com commit -q -m "primer commit"
  git -C "$tmp" push -q "$1" main
  rm -rf "$tmp"
}
crear /srv/git/tienda.git tienda
crear /srv/git/privado/api.git api
chown -R git:git /srv/git
mkdir -p /home/git/.ssh && touch /home/git/.ssh/authorized_keys && chown -R git:git /home/git/.ssh && chmod 700 /home/git/.ssh
/usr/sbin/sshd
spawn-fcgi -s /run/fcgiwrap.sock -u git -g git -M 766 -- /usr/bin/fcgiwrap >/dev/null
exec nginx -g 'daemon off;'
