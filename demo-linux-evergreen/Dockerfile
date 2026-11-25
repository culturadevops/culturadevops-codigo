FROM ubuntu:24.04
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends lsof procps psmisc file \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash ana
WORKDIR /root
CMD ["sleep", "infinity"]
