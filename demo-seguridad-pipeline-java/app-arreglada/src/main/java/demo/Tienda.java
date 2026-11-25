package demo;

import java.io.IOException;
import java.net.InetAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/** La misma tienda, con los fallos arreglados (demo de cultura-devops). */
public class Tienda {
    private static final Path FACTURAS = Path.of("/srv/facturas").toAbsolutePath().normalize();

    // Arreglo 4: las claves vienen del entorno (en el pipeline, de un gestor de secretos)
    static String stripeKey() {
        return System.getenv("STRIPE_API_KEY");
    }

    Connection conectar() throws SQLException {
        return DriverManager.getConnection(System.getenv("DB_URL"), System.getenv("DB_USER"), System.getenv("DB_PASS"));
    }

    // Arreglo 1: consulta preparada con parámetros
    String producto(Connection db, String nombre) throws SQLException {
        try (PreparedStatement st = db.prepareStatement("SELECT nombre, precio FROM productos WHERE nombre = ?")) {
            st.setString(1, nombre);
            try (ResultSet rs = st.executeQuery()) {
                return rs.next() ? rs.getString(1) : "";
            }
        }
    }

    // Arreglo 2: solo IPs literales, y sin shell
    boolean ping(String host) throws IOException {
        if (!host.matches("[0-9.]{7,15}")) {
            throw new IllegalArgumentException("IP no válida");
        }
        return InetAddress.getByName(host).isReachable(2000);
    }

    // Arreglo 3: la ruta final tiene que quedar dentro de FACTURAS
    String factura(String archivo) throws IOException {
        Path ruta = FACTURAS.resolve(archivo).normalize();
        if (!ruta.startsWith(FACTURAS)) {
            throw new IllegalArgumentException("ruta fuera de facturas");
        }
        return Files.readString(ruta);
    }
}
