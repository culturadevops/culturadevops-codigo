# SALIDA — AWS: error establishing SSH connection to your instance (cultura-devops)

> Corrida del 2026-10-23 13:10. «instancia» y «pc»: Debian trixie, OpenSSH_10.0p2 Debian-7+deb13u4, OpenSSL 3.5.7 9 Jun 2026. AWS simulado con moto 5.2.4.dev y aws-cli 2.38.5.
> ip-ranges.json es el archivo público y oficial de AWS, descargado en esta corrida.

```
### 1 · La llave y la conexión buena
pc$ ls -l mi-llave.pem
-r-------- 1 ana ana 1675 Oct 23 18:10 mi-llave.pem
pc$ ssh -i mi-llave.pem ubuntu@instancia hostname
Warning: Permanently added 'instancia' (ED25519) to the list of known hosts.
instancia

### 2 · El usuario equivocado (la AMI es de Ubuntu, no de Amazon Linux)
pc$ ssh -i mi-llave.pem ec2-user@instancia hostname
ec2-user@instancia: Permission denied (publickey).
instancia$ tail -n 2 /var/log/sshd.log
Invalid user ec2-user from 192.168.192.3 port 40110
Connection closed by invalid user ec2-user 192.168.192.3 port 40110 [preauth]
pc$ ssh -i mi-llave.pem ubuntu@instancia hostname
instancia

### 3 · Permisos de la llave demasiado abiertos
pc$ chmod 644 mi-llave.pem; ls -l mi-llave.pem
-rw-r--r-- 1 ana ana 1675 Oct 23 18:10 mi-llave.pem
pc$ ssh -i mi-llave.pem ubuntu@instancia hostname
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'mi-llave.pem' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "mi-llave.pem": bad permissions
ubuntu@instancia: Permission denied (publickey).
pc$ chmod 400 mi-llave.pem
pc$ ssh -i mi-llave.pem ubuntu@instancia hostname
instancia

### 4 · La llave equivocada
pc$ ssh -i otra-llave.pem ubuntu@instancia hostname
ubuntu@instancia: Permission denied (publickey).
pc$ ssh -v -i otra-llave.pem ubuntu@instancia hostname 2>&1 | grep -E 'Authentications that can continue|denied'
debug1: Authentications that can continue: publickey
debug1: Authentications that can continue: publickey
ubuntu@instancia: Permission denied (publickey).
pc$ ssh-keygen -y -f mi-llave.pem | cut -c1-40 ; instancia$ cut -c1-40 ~ubuntu/.ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCe
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCe

### 5 · El grupo de seguridad no deja pasar el 22: «timed out», no «refused»
(en la instancia simulo el grupo de seguridad: descarta todo lo que llega al 22)
pc$ time ssh -o ConnectTimeout=5 -i mi-llave.pem ubuntu@instancia hostname
ssh: connect to host instancia port 22: Connection timed out
(tardó 5 s)

### 6 · El grupo de seguridad, en la API de AWS (moto)
$ aws ec2 describe-security-groups --group-ids sg-425c6ad74ada4d888 --query 'SecurityGroups[0].IpPermissions[].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' --output text
tcp	443	443	0.0.0.0/0
(no hay regla para el 22: desde afuera, «timed out»)
$ aws ec2 authorize-security-group-ingress --group-id sg-425c6ad74ada4d888 --protocol tcp --port 22 --cidr 203.0.113.25/32   # tu IP pública, /32
True
$ aws ec2 describe-security-groups ... (otra vez)
tcp	443	443	0.0.0.0/0
tcp	22	22	203.0.113.25/32

### 7 · EC2 Instance Connect (el botón «Conectar» de la consola): sus IP no son las tuyas
$ curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq -r '.syncToken, .createDate'
1792738625
2026-10-23-06-57-05
$ jq -r '.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT" and .region=="us-east-1") | .ip_prefix' ip-ranges.json
18.206.107.24/29
$ jq '[.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT")] | length' ip-ranges.json   # rangos de Instance Connect en todo el mundo
37
$ aws ec2 authorize-security-group-ingress --group-id sg-425c6ad74ada4d888 --protocol tcp --port 22 --cidr 18.206.107.24/29
True
$ aws ec2 describe-security-groups ... --query '...[?FromPort==`22`].IpRanges[].CidrIp'
203.0.113.25/32	18.206.107.24/29

### 8 · La instancia cambió por dentro (misma IP, otra máquina)
pc$ ssh -i mi-llave.pem ubuntu@instancia hostname
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
The fingerprint for the ED25519 key sent by the remote host is
SHA256:….
  ssh-keygen -f '/home/ana/.ssh/known_hosts' -R 'instancia'
Host key for instancia has changed and you have requested strict checking.
Host key verification failed.
pc$ ssh-keygen -R instancia
# Host instancia found: line 1
# Host instancia found: line 2
# Host instancia found: line 3
/home/ana/.ssh/known_hosts updated.
Original contents retained as /home/ana/.ssh/known_hosts.old
pc$ ssh -o StrictHostKeyChecking=accept-new -i mi-llave.pem ubuntu@instancia hostname
Warning: Permanently added 'instancia' (ED25519) to the list of known hosts.
instancia
```
