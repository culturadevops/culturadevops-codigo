$ ollama --version
ollama version is 0.40.5
$ ollama list | grep qwen2.5-coder
qwen2.5-coder:7b 4.7 GB
qwen2.5-coder:3b 1.9 GB
qwen2.5-coder:1.5b 986 MB
$ nvidia-smi --query-gpu=name --format=csv,noheader
NVIDIA GeForce RTX 5070 Ti

$ ls app && cat app/requirements.txt
app.py
requirements.txt
flask==3.0.3
psycopg2==2.9.10
gunicorn==23.0.0

$ python dockerfile_ia.py app --modelo qwen2.5-coder:7b --errores cola
== intento 1 (3.1 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
      1.130 note: This is an issue with the package mentioned above, not pip.
      1.130 hint: See above for details.
      1.185 
      1.185 [notice] A new release of pip is available: 23.0.1 -> 26.2.1
      1.185 [notice] To update, run: pip install --upgrade pip
      ------
      Dockerfile:12
      --------------------
        10 |     # Copy dependencies
        11 |     COPY requirements.txt /app/
        12 | >>> RUN pip install --no-cache-dir -r requirements.txt
        13 |     
        14 |     # Copy app
      --------------------
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
== intento 2 (2.9 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir pip && \
   |     pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
      1.369 
      1.369 note: This is an issue with the package mentioned above, not pip.
      1.369 hint: See above for details.
      1.425 
      1.425 [notice] A new release of pip is available: 23.0.1 -> 26.2.1
      1.425 [notice] To update, run: pip install --upgrade pip
      ------
      Dockerfile:12
      --------------------
        11 |     COPY requirements.txt /app/
        12 | >>> RUN pip install --no-cache-dir pip && \
        13 | >>>     pip install --no-cache-dir -r requirements.txt
        14 |     
      --------------------
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir pip &&     pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
== intento 3 (3.0 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir pip && \
   |     pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
      1.419 
      1.419 note: This is an issue with the package mentioned above, not pip.
      1.419 hint: See above for details.
      1.473 
      1.473 [notice] A new release of pip is available: 23.0.1 -> 26.2.1
      1.473 [notice] To update, run: pip install --upgrade pip
      ------
      Dockerfile:12
      --------------------
        11 |     COPY requirements.txt /app/
        12 | >>> RUN pip install --no-cache-dir pip && \
        13 | >>>     pip install --no-cache-dir -r requirements.txt
        14 |     
      --------------------
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir pip &&     pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
== intento 4 (2.6 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
      1.120 note: This is an issue with the package mentioned above, not pip.
      1.120 hint: See above for details.
      1.174 
      1.174 [notice] A new release of pip is available: 23.0.1 -> 26.2.1
      1.174 [notice] To update, run: pip install --upgrade pip
      ------
      Dockerfile:12
      --------------------
        10 |     # Copy dependencies
        11 |     COPY requirements.txt /app/
        12 | >>> RUN pip install --no-cache-dir -r requirements.txt
        13 |     
        14 |     # Copy app
      --------------------
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1

RESULTADO: no funcionó en 4 intentos · 11.6 s · modelo qwen2.5-coder:7b
(código de salida: 1)

$ python dockerfile_ia.py app --modelo qwen2.5-coder:7b --errores relevantes
== intento 1 (2.6 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
        Preparing metadata (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            Error: pg_config executable not found.
        note: This error originates from a subprocess, and is likely not a problem with pip.
      error: metadata-generation-failed
      × Encountered error while generating package metadata.
      #8 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.164 error: metadata-generation-failed
      1.164 × Encountered error while generating package metadata.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        12 | >>> RUN pip install --no-cache-dir -r requirements.txt
        13 |     
        14 |     # Copy app
      --------------------
== intento 2 (3.4 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Install PostgreSQL client
   | RUN apt-get update && apt-get install -y libpq-dev
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> docker build falló:
        Building wheel for psycopg2 (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            copying lib/errorcodes.py -> build/lib.linux-x86_64-cpython-310/psycopg2
            copying lib/errors.py -> build/lib.linux-x86_64-cpython-310/psycopg2
            It appears you are missing some prerequisite to build the package from source.
            error: command 'gcc' failed: No such file or directory
        note: This error originates from a subprocess, and is likely not a problem with pip.
        ERROR: Failed building wheel for psycopg2
      Failed to build psycopg2
        Running setup.py install for psycopg2: finished with status 'error'
      error: legacy-install-failure
      × Encountered error while trying to install package.
      #9 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.798 error: legacy-install-failure
      1.798 × Encountered error while trying to install package.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        15 | >>> RUN pip install --no-cache-dir -r requirements.txt
        16 |     
        17 |     # Copy app
      --------------------
== intento 3 (4.6 s)
   | # Dockerfile
   | FROM python:3.10-slim
   | 
   | # Set environment variables
   | ENV PYTHONUNBUFFERED=1
   | 
   | # Install PostgreSQL client and build-essential
   | RUN apt-get update && apt-get install -y libpq-dev build-essential
   | 
   | # Create app directory
   | WORKDIR /app
   | 
   | # Copy dependencies
   | COPY requirements.txt /app/
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Copy app
   | COPY app.py /app/
   | 
   | # Expose port
   | EXPOSE 8080
   | 
   | # Command to run the app
   | CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
   -> GET /salud -> 200 {"driver":"2.9.10","estado":"ok"}

RESULTADO: funciona en el intento 3 · 10.7 s en total · imagen de 188 MB · modelo qwen2.5-coder:7b
(código de salida: 0)

$ python dockerfile_ia.py app --modelo qwen2.5-coder:1.5b --errores relevantes
== intento 1 (2.1 s)
   | # Use an official Python runtime as a parent image
   | FROM python:3.9-slim
   | 
   | # Set the working directory in the container to /app
   | WORKDIR /app
   | 
   | # Copy the current directory contents into the container at /app
   | COPY . /app
   | 
   | # Install any needed packages specified in requirements.txt
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Make port 8080 available to the world outside this container
   | EXPOSE 8080
   | 
   | # Define environment variable
   | ENV PORT 8080
   | 
   | # Run app.py when the container launches
   | CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
   -> docker build falló:
        Preparing metadata (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            Error: pg_config executable not found.
        note: This error originates from a subprocess, and is likely not a problem with pip.
      error: metadata-generation-failed
      × Encountered error while generating package metadata.
      #8 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.172 error: metadata-generation-failed
      1.172 × Encountered error while generating package metadata.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        11 | >>> RUN pip install --no-cache-dir -r requirements.txt
        12 |     
        13 |     # Make port 8080 available to the world outside this container
      --------------------
== intento 2 (2.1 s)
   | # Use an official Python runtime as a parent image
   | FROM python:3.9-slim
   | 
   | # Set the working directory in the container to /app
   | WORKDIR /app
   | 
   | # Copy the current directory contents into the container at /app
   | COPY . /app
   | 
   | # Install any needed packages specified in requirements.txt
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Make port 8080 available to the world outside this container
   | EXPOSE 8080
   | 
   | # Define environment variable
   | ENV PORT 8080
   | 
   | # Install the PostgreSQL development libraries
   | RUN apt-get update && apt-get install -y postgresql-dev
   | 
   | # Run app.py when the container launches
   | CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
   -> docker build falló:
        Preparing metadata (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            Error: pg_config executable not found.
        note: This error originates from a subprocess, and is likely not a problem with pip.
      error: metadata-generation-failed
      × Encountered error while generating package metadata.
      #8 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.186 error: metadata-generation-failed
      1.186 × Encountered error while generating package metadata.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        11 | >>> RUN pip install --no-cache-dir -r requirements.txt
        12 |     
        13 |     # Make port 8080 available to the world outside this container
      --------------------
== intento 3 (2.1 s)
   | # Use an official Python runtime as a parent image
   | FROM python:3.9-slim
   | 
   | # Set the working directory in the container to /app
   | WORKDIR /app
   | 
   | # Copy the current directory contents into the container at /app
   | COPY . /app
   | 
   | # Install any needed packages specified in requirements.txt
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Make port 8080 available to the world outside this container
   | EXPOSE 8080
   | 
   | # Define environment variable
   | ENV PORT 8080
   | 
   | # Install the PostgreSQL development libraries
   | RUN apt-get update && apt-get install -y postgresql-dev
   | 
   | # Install the libpq-dev package which is required for psycopg2
   | RUN apt-get install -y libpq-dev
   | 
   | # Run app.py when the container launches
   | CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
   -> docker build falló:
        Preparing metadata (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            Error: pg_config executable not found.
        note: This error originates from a subprocess, and is likely not a problem with pip.
      error: metadata-generation-failed
      × Encountered error while generating package metadata.
      #8 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.168 error: metadata-generation-failed
      1.168 × Encountered error while generating package metadata.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        11 | >>> RUN pip install --no-cache-dir -r requirements.txt
        12 |     
        13 |     # Make port 8080 available to the world outside this container
      --------------------
== intento 4 (2.2 s)
   | # Use an official Python runtime as a parent image
   | FROM python:3.9-slim
   | 
   | # Set the working directory in the container to /app
   | WORKDIR /app
   | 
   | # Copy the current directory contents into the container at /app
   | COPY . /app
   | 
   | # Install any needed packages specified in requirements.txt
   | RUN pip install --no-cache-dir -r requirements.txt
   | 
   | # Make port 8080 available to the world outside this container
   | EXPOSE 8080
   | 
   | # Define environment variable
   | ENV PORT 8080
   | 
   | # Install the PostgreSQL development libraries
   | RUN apt-get update && apt-get install -y postgresql-dev
   | 
   | # Install the libpq-dev package which is required for psycopg2
   | RUN apt-get install -y libpq-dev
   | 
   | # Install the libpq-dev package which is required for psycopg2
   | RUN apt-get install -y libpq-dev
   | 
   | # Run app.py when the container launches
   | CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
   -> docker build falló:
        Preparing metadata (setup.py): finished with status 'error'
        error: subprocess-exited-with-error
            Error: pg_config executable not found.
        note: This error originates from a subprocess, and is likely not a problem with pip.
      error: metadata-generation-failed
      × Encountered error while generating package metadata.
      #8 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
      1.195 error: metadata-generation-failed
      1.195 × Encountered error while generating package metadata.
      ERROR: failed to build: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
        11 | >>> RUN pip install --no-cache-dir -r requirements.txt
        12 |     
        13 |     # Make port 8080 available to the world outside this container
      --------------------

RESULTADO: no funcionó en 4 intentos · 8.5 s · modelo qwen2.5-coder:1.5b
(código de salida: 1)

$ # la versión del modelo, revisada por una persona (Dockerfile.revisado)
$ docker build -t ia-demo:revisado app && docker run -d -p 18080:8080 ia-demo:revisado && curl /salud
  build: ok
  GET /salud -> {"driver":"2.9.10","estado":"ok"}
  usuario dentro del contenedor: app
  ¿hay gcc en la imagen final?: no
  imagen: 48 MB

