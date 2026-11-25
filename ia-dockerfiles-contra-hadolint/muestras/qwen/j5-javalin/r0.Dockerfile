FROM openjdk:21-jdk-alpine
EXPOSE 8080
COPY target/api-javalin-1.0.0.jar app.jar
ENTRYPOINT ["java","-jar","/app.jar"]
