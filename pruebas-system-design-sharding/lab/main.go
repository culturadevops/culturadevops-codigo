// lab: sharding a mano. Cuatro Postgres (s0..s3) y uno con todo (mono), y este programa hace de
// router. Tres formas de repartir los mismos pedidos:
//
//	hash por cliente   shard = hash(cliente_id) % 4
//	rango por cliente  shard = (cliente_id - 1) / 2500
//	hash por pedido    shard = hash(pedido_id) % 4
//
//	lab cargar · lab reparto · lab consultas · lab top · lab mover
package main

import (
	"context"
	"fmt"
	"hash/fnv"
	"math/rand/v2"
	"os"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ctx = context.Background()

const (
	N        = 1_000_000 // pedidos
	CLIENTES = 10_000
	GRANDE   = 777 // un cliente que hace el 20 % de los pedidos
)

type pedido struct {
	id, cliente int64
	total       int64 // céntimos
	dia         int   // 0..29
}

func h(x int64) uint32 {
	f := fnv.New32a()
	fmt.Fprint(f, x)
	return f.Sum32()
}

var estrategias = map[string]func(p pedido, n int) int{
	"hash_cliente":  func(p pedido, n int) int { return int(h(p.cliente) % uint32(n)) },
	"rango_cliente": func(p pedido, n int) int { return min(int((p.cliente-1)/(CLIENTES/int64(n))), n-1) },
	"hash_pedido":   func(p pedido, n int) int { return int(h(p.id) % uint32(n)) },
}
var orden = []string{"hash_cliente", "rango_cliente", "hash_pedido"}

func pedidos() []pedido {
	r := rand.New(rand.NewPCG(42, 1))
	ps := make([]pedido, N)
	for i := range ps {
		c := int64(r.IntN(CLIENTES) + 1)
		if r.Float64() < 0.20 {
			c = GRANDE
		}
		ps[i] = pedido{int64(i + 1), c, int64(r.IntN(20000) + 500), r.IntN(30)}
	}
	return ps
}

func conectar(nombre string) *pgxpool.Pool {
	pool, err := pgxpool.New(ctx, "postgres://postgres:lab@"+nombre+":5432/tienda")
	if err != nil {
		panic(err)
	}
	return pool
}

func shards() []*pgxpool.Pool {
	s := make([]*pgxpool.Pool, 4)
	for i := range s {
		s[i] = conectar(fmt.Sprintf("s%d", i))
	}
	return s
}

func main() {
	switch os.Args[1] {
	case "cargar":
		ps := pedidos()
		ss := shards()
		mono := conectar("mono")
		t0 := time.Now()
		for _, e := range orden {
			porShard := make([][][]any, 4)
			for _, p := range ps {
				i := estrategias[e](p, 4)
				porShard[i] = append(porShard[i], []any{p.id, p.cliente, p.total, p.dia})
			}
			for i, s := range ss {
				s.Exec(ctx, "DROP TABLE IF EXISTS "+e)
				s.Exec(ctx, "CREATE TABLE "+e+" (id bigint PRIMARY KEY, cliente bigint, total bigint, dia int)")
				if _, err := s.CopyFrom(ctx, pgx.Identifier{e}, []string{"id", "cliente", "total", "dia"},
					pgx.CopyFromRows(porShard[i])); err != nil {
					panic(err)
				}
				s.Exec(ctx, "CREATE INDEX ON "+e+" (cliente)")
				s.Exec(ctx, "ANALYZE "+e)
			}
		}
		filas := make([][]any, len(ps))
		for i, p := range ps {
			filas[i] = []any{p.id, p.cliente, p.total, p.dia}
		}
		mono.Exec(ctx, "DROP TABLE IF EXISTS pedidos")
		mono.Exec(ctx, "CREATE TABLE pedidos (id bigint PRIMARY KEY, cliente bigint, total bigint, dia int)")
		mono.CopyFrom(ctx, pgx.Identifier{"pedidos"}, []string{"id", "cliente", "total", "dia"}, pgx.CopyFromRows(filas))
		mono.Exec(ctx, "CREATE INDEX ON pedidos (cliente)")
		mono.Exec(ctx, "ANALYZE pedidos")
		fmt.Printf("  %d pedidos de %d clientes (el %d hace el 20 %%) · 3 formas × 4 shards + 1 monolito · %v\n",
			N, CLIENTES, GRANDE, time.Since(t0).Round(time.Second))

	case "reparto":
		ss := shards()
		for _, e := range orden {
			var linea []string
			total := 0
			cuenta := make([]int, 4)
			for i, s := range ss {
				s.QueryRow(ctx, "SELECT count(*) FROM "+e).Scan(&cuenta[i])
				total += cuenta[i]
			}
			for i, c := range cuenta {
				linea = append(linea, fmt.Sprintf("s%d %6d (%2.0f %%)", i, c, 100*float64(c)/float64(total)))
			}
			fmt.Printf("  %-14s %s\n", e, strings.Join(linea, " · "))
		}

	case "consultas":
		ss := shards()
		mono := conectar("mono")
		cliente := int64(42)
		e := "hash_cliente"
		i := estrategias[e](pedido{cliente: cliente}, 4)
		// Calentar: la primera consulta de cada pool paga abrir la conexión (medido: 41 ms a un
		// shard frente a 17 ms a cuatro, al revés de lo esperado). Se mide la segunda vuelta.
		for _, s := range append(ss, mono) {
			s.Exec(ctx, "SELECT 1")
			s.Exec(ctx, "SELECT count(*) FROM hash_pedido WHERE cliente = 1")
		}
		// 1) los pedidos de UN cliente: con la clave de reparto, a un solo shard
		t := time.Now()
		var n int
		ss[i].QueryRow(ctx, "SELECT count(*) FROM "+e+" WHERE cliente = $1", cliente).Scan(&n)
		fmt.Printf("  pedidos del cliente 42 · hash_cliente: 1 shard (s%d) · %d pedidos · %v\n", i, n, time.Since(t).Round(time.Microsecond))
		t = time.Now()
		total := 0
		var wg sync.WaitGroup
		var mu sync.Mutex
		for _, s := range ss {
			wg.Add(1)
			go func(s *pgxpool.Pool) {
				defer wg.Done()
				var c int
				s.QueryRow(ctx, "SELECT count(*) FROM hash_pedido WHERE cliente = $1", cliente).Scan(&c)
				mu.Lock()
				total += c
				mu.Unlock()
			}(s)
		}
		wg.Wait()
		fmt.Printf("  pedidos del cliente 42 · hash_pedido:  4 shards · %d pedidos · %v\n", total, time.Since(t).Round(time.Microsecond))
		// 2) un total de todo (scatter-gather) frente al monolito
		for _, intento := range []int{1, 2} {
			t = time.Now()
			var suma int64
			for _, s := range ss {
				wg.Add(1)
				go func(s *pgxpool.Pool) {
					defer wg.Done()
					var x int64
					s.QueryRow(ctx, "SELECT coalesce(sum(total), 0) FROM "+e+" WHERE dia = 7").Scan(&x)
					mu.Lock()
					suma += x
					mu.Unlock()
				}(s)
			}
			wg.Wait()
			dShards := time.Since(t)
			t = time.Now()
			var y int64
			mono.QueryRow(ctx, "SELECT sum(total) FROM pedidos WHERE dia = 7").Scan(&y)
			dMono := time.Since(t)
			if intento == 2 { // la primera calienta las cachés
				fmt.Printf("  ventas del día 7 · 4 shards en paralelo: %d · %v  |  monolito: %d · %v\n",
					suma, dShards.Round(time.Millisecond), y, dMono.Round(time.Millisecond))
			}
		}

	case "top":
		ss := shards()
		mono := conectar("mono")
		top := func(rows pgx.Rows) []string {
			var r []string
			for rows.Next() {
				var c, s int64
				rows.Scan(&c, &s)
				r = append(r, fmt.Sprintf("%d", c))
			}
			return r
		}
		q := "SELECT cliente, sum(total) s FROM %s GROUP BY cliente ORDER BY s DESC LIMIT 5"
		rows, _ := mono.Query(ctx, fmt.Sprintf(q, "pedidos"))
		bueno := top(rows)
		fmt.Printf("  top 5 clientes · monolito (la respuesta correcta): %s\n", strings.Join(bueno, ", "))
		for _, e := range []string{"hash_cliente", "hash_pedido"} {
			// lo ingenuo: el top 5 de cada shard, y luego el top 5 de esos 20
			type par struct {
				c, s int64
			}
			var todos []par
			for _, s := range ss {
				rows, _ := s.Query(ctx, fmt.Sprintf(q, e))
				for rows.Next() {
					var p par
					rows.Scan(&p.c, &p.s)
					todos = append(todos, p)
				}
			}
			sort.Slice(todos, func(i, j int) bool { return todos[i].s > todos[j].s })
			var r []string
			vistos := map[int64]bool{}
			for _, p := range todos {
				if !vistos[p.c] && len(r) < 5 {
					r = append(r, fmt.Sprintf("%d", p.c))
					vistos[p.c] = true
				}
			}
			ok := strings.Join(r, ", ") == strings.Join(bueno, ", ")
			fmt.Printf("  top 5 clientes · %-12s top 5 de cada shard y mezclar: %s  (¿correcto?: %v)\n", e, strings.Join(r, ", "), ok)
		}

	case "extra":
		ss := shards()
		e := "hash_cliente"
		for _, s := range ss {
			s.Exec(ctx, "SELECT 1") // calentar
		}
		// 1) el cliente grande, consultado: su shard trabaja por todos
		for _, c := range []int64{42, GRANDE} {
			i := estrategias[e](pedido{cliente: c}, 4)
			for vuelta := 0; vuelta < 2; vuelta++ {
				t := time.Now()
				var n, suma int64
				ss[i].QueryRow(ctx, "SELECT count(*), sum(total) FROM "+e+" WHERE cliente = $1", c).Scan(&n, &suma)
				if vuelta == 1 {
					fmt.Printf("  gasto del cliente %4d · shard s%d · %6d pedidos · %v\n", c, i, n, time.Since(t).Round(100*time.Microsecond))
				}
			}
		}
		// 2) buscar un pedido por su número cuando se reparte por cliente: ¿en qué shard está?
		var donde []string
		t := time.Now()
		for i, s := range ss {
			var c int64
			if err := s.QueryRow(ctx, "SELECT cliente FROM "+e+" WHERE id = 123456").Scan(&c); err == nil {
				donde = append(donde, fmt.Sprintf("s%d (cliente %d)", i, c))
			}
		}
		fmt.Printf("  el pedido 123456 · repartido por cliente: pregunto a los 4 shards · está en %s · %v\n",
			strings.Join(donde, ""), time.Since(t).Round(100*time.Microsecond))
		// 3) una restricción UNIQUE solo vale dentro de cada shard
		for _, s := range ss {
			s.Exec(ctx, "DROP TABLE IF EXISTS usuarios")
			s.Exec(ctx, "CREATE TABLE usuarios (id bigint PRIMARY KEY, email text UNIQUE)")
		}
		_, err1 := ss[estrategias[e](pedido{cliente: 1}, 4)].Exec(ctx, "INSERT INTO usuarios VALUES (1, 'ana@ejemplo.com')")
		_, err2 := ss[estrategias[e](pedido{cliente: 2}, 4)].Exec(ctx, "INSERT INTO usuarios VALUES (2, 'ana@ejemplo.com')")
		fmt.Printf("  usuario 1 con ana@ejemplo.com en s%d: %v · usuario 2 con el MISMO email en s%d: %v\n",
			estrategias[e](pedido{cliente: 1}, 4), err1, estrategias[e](pedido{cliente: 2}, 4), err2)

	case "mover":
		ps := pedidos()
		for _, e := range orden {
			movidas := 0
			for _, p := range ps {
				if estrategias[e](p, 4) != estrategias[e](p, 5) {
					movidas++
				}
			}
			fmt.Printf("  %-14s de 4 a 5 shards: hay que mover %7d de %d filas (%2.0f %%)\n", e, movidas, N, 100*float64(movidas)/N)
		}
		// Rango, pero partiendo SOLO el shard más lleno (s0): los clientes 1251-2500 pasan al nuevo s4.
		movidas := 0
		for _, p := range ps {
			if p.cliente >= 1251 && p.cliente <= 2500 {
				movidas++
			}
		}
		fmt.Printf("  %-14s partir solo s0 (1251-2500 → s4): hay que mover %7d de %d filas (%2.0f %%)\n",
			"rango_cliente", movidas, N, 100*float64(movidas)/N)
	}
}
