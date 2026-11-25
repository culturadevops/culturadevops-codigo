FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B package -DskipTests && find target -maxdepth 1 -name '*.jar' ! -name 'original-*' -exec cp {} /app.jar \;

FROM eclipse-temurin:21.0.5_11-jre
COPY --from=build /app.jar /app.jar
USER 1000
EXPOSE 8080
CMD ["java", "-jar", "/app.jar"]
