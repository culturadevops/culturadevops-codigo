FROM openjdk:17-alpine

COPY App.java /App.java

RUN javac /App.java

CMD ["java", "-cp", ".", "App"]
