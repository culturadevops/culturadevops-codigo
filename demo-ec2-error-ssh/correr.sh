#!/bin/bash
# Demo de «AWS: error establishing SSH connection to your instance» (cultura-devops, 2026-10-23). Lo llama ejecutar.sh.
# «instancia» = Debian + OpenSSH con el usuario ubuntu (como una AMI de Ubuntu). «pc» = tu computadora (usuaria ana).
# «moto» = un AWS de mentira para el grupo de seguridad. Lo único que sale a internet es la descarga de ip-ranges.json (público).
set -u
I() { docker exec instancia "$@" 2>&1; }
SSH="ssh -o BatchMode=yes -o ConnectTimeout=5"
PC() { docker exec -u ana -w /home/ana pc "$@" 2>&1; }
AWS() { docker run --rm --network demo-ec2 -e AWS_ACCESS_KEY_ID=prueba -e AWS_SECRET_ACCESS_KEY=prueba -e AWS_DEFAULT_REGION=us-east-1 \
          amazon/aws-cli:2.38.5 --endpoint-url http://moto:5000 "$@" 2>&1; }
sshd_log() { I tail -n "${1:-1}" /var/log/sshd.log | sed -E 's/^.*sshd(-session)?\[[0-9]+\]: //'; }

echo "### 1 · La llave y la conexión buena"
echo "pc\$ ls -l mi-llave.pem"
PC ls -l mi-llave.pem
echo "pc\$ ssh -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -o StrictHostKeyChecking=accept-new -i mi-llave.pem ubuntu@instancia hostname

echo
echo "### 2 · El usuario equivocado (la AMI es de Ubuntu, no de Amazon Linux)"
echo "pc\$ ssh -i mi-llave.pem ec2-user@instancia hostname"
PC $SSH -i mi-llave.pem ec2-user@instancia hostname
echo "instancia\$ tail -n 2 /var/log/sshd.log"
sshd_log 2
echo "pc\$ ssh -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -i mi-llave.pem ubuntu@instancia hostname

echo
echo "### 3 · Permisos de la llave demasiado abiertos"
PC chmod 644 mi-llave.pem
echo "pc\$ chmod 644 mi-llave.pem; ls -l mi-llave.pem"
PC ls -l mi-llave.pem
echo "pc\$ ssh -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -i mi-llave.pem ubuntu@instancia hostname
echo "pc\$ chmod 400 mi-llave.pem"
PC chmod 400 mi-llave.pem
echo "pc\$ ssh -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -i mi-llave.pem ubuntu@instancia hostname

echo
echo "### 4 · La llave equivocada"
echo "pc\$ ssh -i otra-llave.pem ubuntu@instancia hostname"
PC $SSH -i otra-llave.pem ubuntu@instancia hostname
echo "pc\$ ssh -v -i otra-llave.pem ubuntu@instancia hostname 2>&1 | grep -E 'Authentications that can continue|denied'"
PC sh -c "$SSH -v -i otra-llave.pem ubuntu@instancia hostname 2>&1 | grep -E 'Authentications that can continue|denied' | sed -E 's/SHA256:[A-Za-z0-9+\/]+/SHA256:…/'"
echo "pc\$ ssh-keygen -y -f mi-llave.pem | cut -c1-40 ; instancia\$ cut -c1-40 ~ubuntu/.ssh/authorized_keys"
PC sh -c "ssh-keygen -y -f mi-llave.pem | cut -c1-40"
I cut -c1-40 /home/ubuntu/.ssh/authorized_keys

echo
echo "### 5 · El grupo de seguridad no deja pasar el 22: «timed out», no «refused»"
echo "(en la instancia simulo el grupo de seguridad: descarta todo lo que llega al 22)"
I iptables -A INPUT -p tcp --dport 22 -j DROP
echo "pc\$ time ssh -o ConnectTimeout=5 -i mi-llave.pem ubuntu@instancia hostname"
inicio=$(date +%s)
PC $SSH -i mi-llave.pem ubuntu@instancia hostname
echo "(tardó $(( $(date +%s) - inicio )) s)"
I iptables -F INPUT

echo
echo "### 6 · El grupo de seguridad, en la API de AWS (moto)"
VPC=$(AWS ec2 describe-vpcs --query 'Vpcs[0].VpcId' --output text)
SG=$(AWS ec2 create-security-group --group-name web --description "servidor web" --vpc-id "$VPC" --query GroupId --output text)
AWS ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 443 --cidr 0.0.0.0/0 >/dev/null
echo "\$ aws ec2 describe-security-groups --group-ids $SG --query 'SecurityGroups[0].IpPermissions[].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' --output text"
AWS ec2 describe-security-groups --group-ids "$SG" --query 'SecurityGroups[0].IpPermissions[].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' --output text
echo "(no hay regla para el 22: desde afuera, «timed out»)"
echo "\$ aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 22 --cidr 203.0.113.25/32   # tu IP pública, /32"
AWS ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 22 --cidr 203.0.113.25/32 --query Return --output text
echo "\$ aws ec2 describe-security-groups ... (otra vez)"
AWS ec2 describe-security-groups --group-ids "$SG" --query 'SecurityGroups[0].IpPermissions[].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' --output text

echo
echo "### 7 · EC2 Instance Connect (el botón «Conectar» de la consola): sus IP no son las tuyas"
echo "\$ curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq -r '.syncToken, .createDate'"
I sh -c "curl -s https://ip-ranges.amazonaws.com/ip-ranges.json -o /tmp/ip-ranges.json && jq -r '.syncToken, .createDate' /tmp/ip-ranges.json"
echo "\$ jq -r '.prefixes[] | select(.service==\"EC2_INSTANCE_CONNECT\" and .region==\"us-east-1\") | .ip_prefix' ip-ranges.json"
I jq -r '.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT" and .region=="us-east-1") | .ip_prefix' /tmp/ip-ranges.json
echo "\$ jq '[.prefixes[] | select(.service==\"EC2_INSTANCE_CONNECT\")] | length' ip-ranges.json   # rangos de Instance Connect en todo el mundo"
I jq '[.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT")] | length' /tmp/ip-ranges.json
CIDR=$(I jq -r '.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT" and .region=="us-east-1") | .ip_prefix' /tmp/ip-ranges.json | head -1 | tr -d '\r')
echo "\$ aws ec2 authorize-security-group-ingress --group-id $SG --protocol tcp --port 22 --cidr $CIDR"
AWS ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 22 --cidr "$CIDR" --query Return --output text
echo "\$ aws ec2 describe-security-groups ... --query '...[?FromPort==\`22\`].IpRanges[].CidrIp'"
AWS ec2 describe-security-groups --group-ids "$SG" --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`].IpRanges[].CidrIp' --output text

echo
echo "### 8 · La instancia cambió por dentro (misma IP, otra máquina)"
I sh -c "rm -f /etc/ssh/ssh_host_* && ssh-keygen -A >/dev/null && pkill -x sshd; sleep 1; /usr/sbin/sshd -E /var/log/sshd.log"
sleep 1
echo "pc\$ ssh -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -i mi-llave.pem ubuntu@instancia hostname | grep -vE "^@ +@$|^Someone could be|^It is also possible|^Please contact|^To get rid|^Add correct host key|^Offending|^  remove with|^Password authentication|^Agent forwarding|^Port forwarding|^X11 forwarding|^UpdateHostkeys|^Keyboard-interactive|^Challenge/response" | sed -E 's/SHA256:[A-Za-z0-9+\/]+/SHA256:…/'
echo "pc\$ ssh-keygen -R instancia"
PC ssh-keygen -R instancia
echo "pc\$ ssh -o StrictHostKeyChecking=accept-new -i mi-llave.pem ubuntu@instancia hostname"
PC $SSH -o StrictHostKeyChecking=accept-new -i mi-llave.pem ubuntu@instancia hostname
