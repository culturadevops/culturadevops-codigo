// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
package tienda;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;

public final class Consultas {

    private Consultas() {
    }

    public static ResultSet buscarProductos(Connection db, String texto) throws SQLException {
        // V3: el SQL se arma aquí, lejos de donde entra el dato
        String sql = "SELECT nombre FROM productos WHERE nombre LIKE '%" + texto + "%'";
        return db.createStatement().executeQuery(sql);
    }
}
