<?php
// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
require __DIR__ . '/consultas.php';

$db = new PDO('sqlite:tienda.db');
$ruta = $_GET['ruta'] ?? '';

if ($ruta === 'usuario') {
    // V1: inyección SQL
    $id = $_GET['id'];
    echo json_encode($db->query("SELECT nombre FROM usuarios WHERE id = " . $id)->fetchAll());
} elseif ($ruta === 'ping') {
    // V2: inyección de comandos
    $host = $_GET['host'];
    echo shell_exec("ping -c 1 " . $host);
} elseif ($ruta === 'buscar') {
    // V3: inyección SQL a través de otro archivo
    echo json_encode(buscar_productos($db, $_GET['q']));
} elseif ($ruta === 'usuario_seguro') {
    // S1: consulta con parámetros: segura
    $st = $db->prepare("SELECT nombre FROM usuarios WHERE id = ?");
    $st->execute([$_GET['id']]);
    echo json_encode($st->fetchAll());
} elseif ($ruta === 'pedido') {
    // S2: el id se convierte a entero: seguro
    $id = (int) $_GET['id'];
    echo json_encode($db->query("SELECT total FROM pedidos WHERE id = " . $id)->fetchAll());
}
