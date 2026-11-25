FROM eclipse-temurin:25-jdk AS build
WORKDIR /src
COPY Servidor.java /src/
RUN javac -d /tmp/c Servidor.java && jar --create --file /servidor.jar --main-class Servidor -C /tmp/c .
FROM eclipse-temurin:25-jre
COPY --from=build /servidor.jar /app/servidor.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/servidor.jar"]
