// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
package tienda;

import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;

public class TiendaServlet extends HttpServlet {

    private Connection db() throws SQLException {
        return DriverManager.getConnection("jdbc:sqlite:tienda.db");
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException {
        try {
            switch (req.getPathInfo()) {
                case "/usuario" -> {
                    // V1: inyección SQL
                    String id = req.getParameter("id");
                    db().createStatement().executeQuery("SELECT nombre FROM usuarios WHERE id = " + id);
                }
                case "/ping" -> {
                    // V2: inyección de comandos
                    String host = req.getParameter("host");
                    Runtime.getRuntime().exec(new String[] {"sh", "-c", "ping -c 1 " + host});
                }
                case "/buscar" ->
                    // V3: inyección SQL a través de otro archivo
                    Consultas.buscarProductos(db(), req.getParameter("q"));
                case "/usuario_seguro" -> {
                    // S1: consulta con parámetros: segura
                    PreparedStatement st = db().prepareStatement("SELECT nombre FROM usuarios WHERE id = ?");
                    st.setString(1, req.getParameter("id"));
                    st.executeQuery();
                }
                case "/pedido" -> {
                    // S2: el id se convierte a entero: seguro
                    int id = Integer.parseInt(req.getParameter("id"));
                    db().createStatement().executeQuery("SELECT total FROM pedidos WHERE id = " + id);
                }
                default -> res.sendError(404);
            }
        } catch (SQLException e) {
            res.sendError(500);
        }
    }
}
