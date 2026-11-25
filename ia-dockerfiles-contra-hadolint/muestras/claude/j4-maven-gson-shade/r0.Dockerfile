# syntax=docker/dockerfile:1

# ---------- Etapa de construcción ----------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

# Cachear dependencias
COPY pom.xml .
RUN --mount=type=cache,target=/root/.m2 mvn -B -q dependency:go-offline

# Compilar y empaquetar (fat jar con maven-shade-plugin)
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B -q -DskipTests package \
 && cp target/api-gson-1.0.0.jar /build/app.jar

# ---------- Etapa de ejecución ----------
FROM eclipse-temurin:21-jre

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=build --chown=app:app /build/app.jar /app/app.jar

USER 10001:10001

ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError"

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
