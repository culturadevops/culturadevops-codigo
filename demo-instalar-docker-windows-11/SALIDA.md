# SALIDA · demo-instalar-docker-windows-11 (2026-10-23, PC del canal, Windows 11 Pro build 26200)

SOLO LECTURA: wsl --version/--status/-l -v, systeminfo, docker version, docker run --rm hello-world, Win32_Processor. No se instaló ni cambió nada.
(«ó»: wsl.exe escribe UTF-16 y PowerShell lo mostró como «�»; es «Versión».)

```
### 1 · wsl --version
Versión de WSL: 2.7.11.0
Versión de kernel: 6.18.33.2-2
Versión de WSLg: 1.0.73.2
Versión de MSRDC: 1.2.7214
Versión de Direct3D: 1.611.1-81528511
Versión de DXCore: 10.0.26100.1-240331-1435.ge-release
Versión de Windows: 10.0.26200.9711
### 2 · wsl --status
Distribución predeterminada: docker-desktop
Versión predeterminada: 2
### 3 · wsl -l -v
  NAME                      STATE           VERSION
* docker-desktop            Running         2
  podman-machine-default    Stopped         2
### 4 · systeminfo (líneas de Hyper-V)
>                                                  Integridad del código reforzada por el hipervisor
                                             Services Running:
>                                                  Integridad del código reforzada por el hipervisor
                                             App Control for Business policy: Forzado
                                             App Control for Business user mode policy: Desactivado
                                             Características de seguridad habilitadas:
> Requisitos Hyper-V:                        Se detectó un hipervisor. No se mostrarán las características necesarias 
para Hyper-V.
### 5 · docker version
Client:
 Version:           29.6.2
 API version:       1.55
 Go version:        go1.26.5
 Git commit:        dfc4efb
 Built:             Thu Jul 16 16:14:59 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux
Server: Docker Desktop 4.84.0 (234817)
 Engine:
  Version:          29.6.2
  API version:      1.55 (minimum version 1.40)
  Go version:       go1.26.5
  Git commit:       3d80467
  Built:            Thu Jul 16 16:12:20 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.5
  GitCommit:        e53c7c1516c3b2bff98eb76f1f4117477e6f4e66
 runc:
  Version:          1.3.6
  GitCommit:        v1.3.6-0-g491b69ba
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
### 6 · docker run --rm hello-world
docker : Unable to find image 'hello-world:latest' locally
En línea: 1 Carácter: 967
+ ... un --rm hello-world"; $o += (docker run --rm hello-world 2>&1 | Out-S ...
+                                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Unable to find ...latest' locally:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
latest: Pulling from library/hello-world
4f55086f7dd0: Pulling fs layer
d5e71e642bf5: Download complete
4f55086f7dd0: Download complete
4f55086f7dd0: Pull complete
Digest: sha256:11a3eb1597e864c51b3f56733cb2e8a90bf0c284bfc05f9444d81c558bc848aa
Status: Downloaded newer image for hello-world:latest
Hello from Docker!
This message shows that your installation appears to be working correctly.
To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.
To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash
Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/
For more examples and ideas, visit:
 https://docs.docker.com/get-started/
### 7 · Get-CimInstance Win32_Processor VirtualizationFirmwareEnabled
Name                                    : Intel(R) Core(TM) Ultra 7 270K Plus
VirtualizationFirmwareEnabled           : False
SecondLevelAddressTranslationExtensions : False
### 8 · versión de Windows
Caption     : Microsoft Windows 11 Pro
Version     : 10.0.26200
BuildNumber : 26200

```

## Mensajes de error que NO se reproducen (citados de la documentación oficial)
- Docker Desktop (docs.docker.com, troubleshoot topics): «Docker Desktop - Unexpected WSL error» con `Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED` o `.../ERROR_NOT_SUPPORTED`. Causa: virtualización desactivada en la BIOS o faltan Hyper-V/WSL 2.
- WSL (learn.microsoft.com, troubleshooting): «Error: 0x80370102 The virtual machine could not be started because a required feature is not installed.» → activar Virtual Machine Platform y la virtualización en la BIOS.
- Docker Desktop (windows-install): si `wsl --version` no muestra versiones, es el WSL de bandeja (inbox) y hay que actualizar: `wsl --update` (o `wsl --install`).
- systeminfo con virtualización activa: «Hyper-V Requirements: A hypervisor has been detected.» (docs.docker.com).
- Hipervisor apagado al arrancar: `bcdedit /set hypervisorlaunchtype auto` y reiniciar (docs.docker.com).
