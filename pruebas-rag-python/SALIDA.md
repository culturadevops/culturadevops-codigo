# SALIDA — RAG en Python sin framework (cultura-devops 797)

Corrida del 2026-11-05 con `bash ejecutar_todo.sh` (literal abajo, copiada de corrida.txt). Contenedores con `--rm --cpus 1`.
Ollama en el HOST (Windows, versión 0.40.14). Modelos: nomic-embed-text 274 MB · bge-m3 1.2 GB (bajado para esta demo) · qwen2.5:7b 4.7 GB (ollama list).
Una sola dependencia de Python: psycopg 3.2.10. Ollama se llama con urllib (biblioteca estándar). El vector va a Postgres como texto '[0.1,...]'::vector.

⚠️ Sin cronómetro: en la máquina corre un banco de Deno. Ningún tiempo de esta demo va al vídeo.

## Hallazgos
1. nomic-embed-text (el de la tanda 471-472) NO recupera «copias de seguridad»: el top 3 son trozos de guardias
   (0.303 · 0.319 · 0.355); respaldos#2, el bueno, sale 8.º de 15 a 0.389 (corrida suelta con K=15, antes de esta, mismo índice).
   Con la palabra del documento («respaldos») sí sale (0.283 · 0.306 · 0.331).
2. Ese fallo es SILENCIOSO: el modelo, con el contexto equivocado, contesta «No está en los documentos.» — parece honestidad y es
   un fallo de recuperación.
3. Quitar los prefijos search_document/search_query de nomic NO lo arregla (corrida suelta: guardias#3 0.292 · guardias#1 0.323 ·
   despliegues#4 0.333).
4. bge-m3 (multilingüe, 1024 números) lo arregla: respaldos#2 a 0.390 y responde «35 días ... un año [respaldos#2]».
5. Con bge-m3 la pregunta sin respuesta queda lejos: mejor trozo a 0.596 frente a 0.278-0.390 de las que sí tienen respuesta.
   El modelo dice «No está en los documentos.»; con UMBRAL=0.5 ni se llama al modelo. ⚠️ El 0.5 lo elegí mirando ESTAS cuatro
   preguntas: con otros documentos hay que medirlo otra vez. Con nomic (primera corrida exploratoria, mismos prefijos) la
   pregunta del presupuesto quedaba a 0.366 · 0.367 · 0.383 (accesos#2, accesos#1, accesos#3): casi como una buena (0.334).
6. La cita no siempre llega: la respuesta del viernes no cita [despliegues#1] aunque el sistema lo pide.
7. HNSW: el índice existe, pero con 15 filas Postgres prefiere leerlo todo (Seq Scan + Sort). Con enable_seqscan=off usa
   trozos_emb_idx. Con 15 trozos no hace falta; el índice importa con miles.
8. Tamaño: rag.py 96 líneas · tabla 272 kB con 15 trozos · imagen de la demo 209 MB.

## Corrida literal
```
=== versiones
python 3.13.17 · psycopg 3.2.10
CREATE EXTENSION
postgres 17.11 (Debian 17.11-1.pgdg12+2) · pgvector 0.8.7
{"version":"0.40.14"}

=== A · nomic-embed-text (768), con los prefijos search_document/search_query
$ EMB=nomic-embed-text python rag.py indexar 
indexados 15 trozos de 4 documentos · 768 números por trozo

$ EMB=nomic-embed-text python rag.py buscar "¿Puedo desplegar un viernes?"
  0.334  [despliegues#1] Despliegues a producción. Se despliega a producción de lunes a jueves,...
  0.354  [despliegues#2] Despliegues a producción. Todo despliegue pasa primero por el entorno ...
  0.354  [despliegues#4] Despliegues a producción. Durante la semana de cierre de mes, del día ...

$ EMB=nomic-embed-text python rag.py buscar "¿Qué pasa si la guardia no contesta una alerta?"
  0.260  [guardias#1] Guardias del equipo de plataforma. La guardia dura una semana y empiez...
  0.260  [guardias#2] Guardias del equipo de plataforma. Si la persona de guardia no respond...
  0.267  [guardias#3] Guardias del equipo de plataforma. Cada guardia termina con una nota d...

$ EMB=nomic-embed-text python rag.py buscar "¿Cuánto tiempo se guardan las copias de seguridad?"
  0.303  [guardias#3] Guardias del equipo de plataforma. Cada guardia termina con una nota d...
  0.319  [guardias#1] Guardias del equipo de plataforma. La guardia dura una semana y empiez...
  0.355  [guardias#4] Guardias del equipo de plataforma. Las horas de guardia fuera del hora...

$ EMB=nomic-embed-text python rag.py buscar "¿Cuánto tiempo se guardan los respaldos?"
  0.283  [respaldos#4] Respaldos de las bases de datos. Si el respaldo de la noche falla, la ...
  0.306  [respaldos#2] Respaldos de las bases de datos. Los respaldos diarios se guardan 35 d...
  0.331  [respaldos#3] Respaldos de las bases de datos. Una vez al mes se restaura el último ...

$ EMB=nomic-embed-text python rag.py preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"
  [guardias#3] distancia 0.303
  [guardias#1] distancia 0.319
  [guardias#4] distancia 0.355
respuesta: No está en los documentos.

=== B · bge-m3 (1024, multilingüe)
$ EMB=bge-m3 python rag.py indexar 
indexados 15 trozos de 4 documentos · 1024 números por trozo

$ EMB=bge-m3 python rag.py buscar "¿Puedo desplegar un viernes?"
  0.337  [despliegues#1] Despliegues a producción. Se despliega a producción de lunes a jueves,...
  0.467  [despliegues#4] Despliegues a producción. Durante la semana de cierre de mes, del día ...
  0.511  [despliegues#3] Despliegues a producción. Para revertir un despliegue se usa el comand...

$ EMB=bge-m3 python rag.py buscar "¿Qué pasa si la guardia no contesta una alerta?"
  0.278  [guardias#2] Guardias del equipo de plataforma. Si la persona de guardia no respond...
  0.363  [guardias#1] Guardias del equipo de plataforma. La guardia dura una semana y empiez...
  0.374  [respaldos#4] Respaldos de las bases de datos. Si el respaldo de la noche falla, la ...

$ EMB=bge-m3 python rag.py buscar "¿Cuánto tiempo se guardan las copias de seguridad?"
  0.390  [respaldos#2] Respaldos de las bases de datos. Los respaldos diarios se guardan 35 d...
  0.494  [guardias#1] Guardias del equipo de plataforma. La guardia dura una semana y empiez...
  0.519  [accesos#1] Accesos a servidores y a la nube. Nadie entra a los servidores de prod...

$ EMB=bge-m3 python rag.py buscar "¿Cuál es el presupuesto de la nube para 2027?"
  0.596  [accesos#2] Accesos a servidores y a la nube. Los permisos de administrador en la ...
  0.609  [accesos#1] Accesos a servidores y a la nube. Nadie entra a los servidores de prod...
  0.627  [respaldos#1] Respaldos de las bases de datos. La base de datos de clientes se respa...

$ EMB=bge-m3 python rag.py preguntar "¿Puedo desplegar un viernes?"
  [despliegues#1] distancia 0.337
  [despliegues#4] distancia 0.467
  [despliegues#3] distancia 0.511
respuesta: No, generalmente no se despliega un viernes a menos que haya un arreglo urgente aprobado por la guardia.

$ EMB=bge-m3 python rag.py preguntar "¿Qué pasa si la guardia no contesta una alerta?"
  [guardias#2] distancia 0.278
  [guardias#1] distancia 0.363
  [respaldos#4] distancia 0.374
respuesta: Si la persona de guardia no responde en 15 minutos, la alerta escala sola a la segunda guardia. Si nadie responde en 30 minutos, escala a la jefa del equipo. [guardias#2]

$ EMB=bge-m3 python rag.py preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"
  [respaldos#2] distancia 0.390
  [guardias#1] distancia 0.494
  [accesos#1] distancia 0.519
respuesta: Se guardan los respaldos diarios durante 35 días. Adicionalmente, el respaldo del primer día de cada mes se guarda un año. [respaldos#2]

=== C · la pregunta sin respuesta
$ EMB=bge-m3 python rag.py preguntar "¿Cuál es el presupuesto de la nube para 2027?"
  [accesos#2] distancia 0.596
  [accesos#1] distancia 0.609
  [respaldos#1] distancia 0.627
respuesta: No está en los documentos.

$ EMB=bge-m3 UMBRAL=0.5 python rag.py preguntar "¿Cuál es el presupuesto de la nube para 2027?"
  [accesos#2] distancia 0.596
  [accesos#1] distancia 0.609
  [respaldos#1] distancia 0.627
respuesta: no lo encuentro en los documentos (el más cercano está a 0.596 > 0.5)

$ EMB=bge-m3 UMBRAL=0.5 python rag.py preguntar "¿Cuánto tiempo se guardan las copias de seguridad?"
  [respaldos#2] distancia 0.390
  [guardias#1] distancia 0.494
  [accesos#1] distancia 0.519
respuesta: Se guardan los respaldos diarios durante 35 días. Adicionalmente, el respaldo del primer día de cada mes se guarda un año. [respaldos#2]

=== D · ¿usa el índice HNSW?
$ psql -c "EXPLAIN SELECT ... ORDER BY emb <=> ... LIMIT 3"
    "trozos_emb_idx" hnsw (emb vector_cosine_ops)
                       QUERY PLAN                       
--------------------------------------------------------
 Limit
   InitPlan 1
     ->  Seq Scan on trozos trozos_1
           Filter: (id = 1)
   ->  Sort
         Sort Key: ((trozos.emb <=> (InitPlan 1).col1))
         ->  Seq Scan on trozos
(7 rows)

SET
                       QUERY PLAN                        
---------------------------------------------------------
 Limit
   InitPlan 1
     ->  Index Scan using trozos_pkey on trozos trozos_1
           Index Cond: (id = 1)
   ->  Index Scan using trozos_emb_idx on trozos
         Order By: (emb <=> (InitPlan 1).col1)
(6 rows)

=== E · el tamaño
15 trozos · tabla 272 kB
96 rag.py
imagen 209MB
```
