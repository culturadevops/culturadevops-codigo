CREATE TABLE productos (id serial PRIMARY KEY, nombre text NOT NULL, precio numeric(10,2));
INSERT INTO productos (nombre, precio) VALUES ('teclado', 25.00), ('mouse', 12.50), ('monitor', 180.00);
