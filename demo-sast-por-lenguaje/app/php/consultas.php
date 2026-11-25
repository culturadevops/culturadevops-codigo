<?php
// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.

function buscar_productos(PDO $db, string $texto): array
{
    // V3: el SQL se arma aquí, lejos de donde entra el dato
    $sql = "SELECT nombre FROM productos WHERE nombre LIKE '%" . $texto . "%'";
    return $db->query($sql)->fetchAll();
}
