package demo;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/** Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops). No la despliegues. */
public class Tienda {
    // Fallo 4: una clave pegada en el código
    static final String STRIPE_API_KEY = "CLAVE_STRIPE_FALSA_DE_EJEMPLO";

    Connection conectar() throws SQLException {
        // Fallo 4b: usuario y contraseña de la base pegados en el código
        return DriverManager.getConnection("jdbc:postgresql://db/tienda", "admin", "admin123");
    }

    // Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
    String producto(Connection db, String nombre) throws SQLException {
        Statement st = db.createStatement();
        ResultSet rs = st.executeQuery("SELECT nombre, precio FROM productos WHERE nombre = '" + nombre + "'");
        return rs.next() ? rs.getString(1) : "";
    }

    // Fallo 2: inyección de comandos
    Process ping(String host) throws IOException {
        return Runtime.getRuntime().exec(new String[] {"sh", "-c", "ping -c 1 " + host});
    }

    // Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
    String factura(String archivo) throws IOException {
        return Files.readString(new File("/srv/facturas", archivo).toPath());
    }
}
