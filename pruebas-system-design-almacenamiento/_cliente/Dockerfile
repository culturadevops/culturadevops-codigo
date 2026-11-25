FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends nfs-common e2fsprogs && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir boto3==1.35.36
