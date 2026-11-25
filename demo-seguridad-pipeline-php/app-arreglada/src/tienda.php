<?php
// La misma tienda, con los fallos arreglados (demo de cultura-devops).
declare(strict_types=1);

/** Lee un parámetro de la URL y garantiza que es texto. */
function param(string $clave, string $porDefecto = ''): string
{
    $v = $_GET[$clave] ?? $porDefecto;
    return is_string($v) ? $v : $porDefecto;
}

function stripeKey(): string
{
    // Arreglo 4: la clave viene del entorno (en el pipeline, de un gestor de secretos)
    $k = getenv('STRIPE_API_KEY');
    return $k === false ? '' : $k;
}

/** @return list<mixed> */
function producto(PDO $db): array
{
    // Arreglo 1: consulta preparada con parámetros
    $st = $db->prepare('SELECT id, nombre, precio FROM productos WHERE nombre = ?');
    $st->execute([param('nombre')]);
    return array_values($st->fetchAll(PDO::FETCH_ASSOC));
}

function ping(): string
{
    $host = param('host', '127.0.0.1');
    // Arreglo 2: solo se acepta una IP, y además se escapa el argumento
    if (filter_var($host, FILTER_VALIDATE_IP) === false) {
        return 'IP no válida';
    }
    return (string) shell_exec('ping -c 1 ' . escapeshellarg($host));
}

function factura(): string
{
    // Arreglo 3: basename quita las carpetas, y además se comprueba la ruta final
    $base = '/srv/facturas';
    $ruta = realpath($base . '/' . basename(param('archivo')));
    if ($ruta === false || !str_starts_with($ruta, $base . '/')) {
        return 'no existe';
    }
    return (string) file_get_contents($ruta);
}

function saludo(): void
{
    echo '<h1>Hola, ' . htmlspecialchars(param('quien'), ENT_QUOTES) . '</h1>';
}
