package app;

import io.javalin.Javalin;

public class Main {
    public static void main(String[] args) {
        Javalin.create().get("/", ctx -> ctx.result("ok")).start(8080);
    }
}
