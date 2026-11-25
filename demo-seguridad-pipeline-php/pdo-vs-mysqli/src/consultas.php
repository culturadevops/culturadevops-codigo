<?php
// La misma inyección SQL, con PDO y con mysqli: ¿la ve psalm --taint-analysis?
declare(strict_types=1);
function conPdo(PDO $db): void { $db->query('SELECT * FROM productos WHERE nombre = ' . $_GET['n']); }
function conPdoExec(PDO $db): void { $db->exec('DELETE FROM productos WHERE nombre = ' . $_GET['n']); }
function conMysqli(mysqli $m): void { $m->query('SELECT * FROM productos WHERE nombre = ' . $_GET['n']); }
