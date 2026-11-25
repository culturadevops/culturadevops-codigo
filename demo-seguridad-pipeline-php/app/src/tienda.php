<?php
// Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops). No la despliegues.
declare(strict_types=1);

// Fallo 4: una clave pegada en el código
const STRIPE_API_KEY = 'CLAVE_STRIPE_FALSA_DE_EJEMPLO';

function producto(PDO $db): array
{
    $nombre = $_GET['nombre'] ?? '';
    // Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
    $res = $db->query("SELECT id, nombre, precio FROM productos WHERE nombre = '$nombre'");
    return $res === false ? [] : $res->fetchAll();
}

function ping(): string
{
    $host = $_GET['host'] ?? 'localhost';
    // Fallo 2: inyección de comandos
    return (string) shell_exec('ping -c 1 ' . $host);
}

function factura(): string
{
    $archivo = $_GET['archivo'] ?? '';
    // Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
    return (string) file_get_contents('/srv/facturas/' . $archivo);
}

function saludo(): void
{
    // Extra: XSS (el nombre se imprime sin escapar)
    echo '<h1>Hola, ' . ($_GET['quien'] ?? '') . '</h1>';
}
