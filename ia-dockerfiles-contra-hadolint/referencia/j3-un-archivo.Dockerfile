FROM eclipse-temurin:21.0.5_11-jdk AS build
WORKDIR /src
COPY App.java .
RUN javac App.java

FROM eclipse-temurin:21.0.5_11-jre
WORKDIR /app
COPY --from=build /src/App.class .
USER 1000
EXPOSE 8080
CMD ["java", "App"]
