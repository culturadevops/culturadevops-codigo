FROM openjdk:17-jdk-alpine

COPY target/servidor-1.0.0.jar /app/servidor.jar

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "servidor.jar"]
