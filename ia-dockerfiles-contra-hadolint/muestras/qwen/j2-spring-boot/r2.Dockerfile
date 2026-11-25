# Use la imagen base de OpenJDK 21
FROM openjdk:21-jdk-slim

# Establece el trabajo actual como directorio de trabajo
WORKDIR /app

# Copia el archivo pom.xml al directorio de trabajo
COPY pom.xml /app/

# Instala las dependencias Maven
RUN apt-get update && \
    apt-get install -y maven=3.8.4-1 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copia todos los archivos del proyecto al directorio de trabajo
COPY . /app

# Construye la aplicación
RUN mvn clean package -DskipTests

# Establece el trabajo actual como directorio de la aplicación
WORKDIR /app/target

# Copia la aplicación compilada al directorio de trabajo
COPY target/api-spring-1.0.0.jar /app/api-spring.jar

# Establece los puertos de la aplicación
EXPOSE 8080

# Ejecuta la aplicación
CMD ["java", "-jar", "api-spring.jar"]
