// lab: cache-aside con Valkey delante de Postgres. Cada orden es una medición del vídeo 346.
//
//	lab preparar                 1.000 productos en Postgres
//	lab sincache  -n 2000        todas las lecturas a la base de datos
//	lab concache  -n 2000        cache-aside: primero Valkey, si falla la BD y se guarda (TTL 60 s)
//	lab vieja                    actualizar el precio sin borrar la caché, y borrándola
//	lab estampida -modo X        100 peticiones a la vez cuando expira la clave más pedida
//	lab expiracion -jitter       1.000 claves con el mismo TTL, leídas sin parar: consultas por segundo
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"math/rand/v2"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
	"golang.org/x/sync/singleflight"
)

var (
	ctx       = context.Background()
	db        *pgxpool.Pool
	rdb       *redis.Client
	consultas atomic.Int64 // cuántas veces se fue a la base de datos
)

type producto struct {
	Nombre string
	Precio int
}

// deBD es la consulta «cara»: 20 ms de pg_sleep para simular una consulta lenta, siempre igual.
func deBD(id int) (producto, error) {
	consultas.Add(1)
	var p producto
	err := db.QueryRow(ctx, "SELECT nombre, precio FROM productos, pg_sleep($2) WHERE id = $1", id, coste).
		Scan(&p.Nombre, &p.Precio)
	return p, err
}

// coste de la consulta, en segundos: 0,02 por defecto; la estampida usa 0,2 (la clave caliente
// suele ser cara de reconstruir: un agregado, un informe).
var coste = 0.02

func clave(id int) string { return "producto:" + strconv.Itoa(id) }

// leer es cache-aside: Valkey primero; si no está, la base de datos, y se guarda con su TTL.
func leer(id int, ttl time.Duration) (producto, bool, error) {
	if v, err := rdb.HGetAll(ctx, clave(id)).Result(); err == nil && len(v) > 0 {
		precio, _ := strconv.Atoi(v["precio"])
		return producto{v["nombre"], precio}, true, nil
	}
	p, err := deBD(id)
	if err != nil {
		return p, false, err
	}
	if grande {
		rdb.HSet(ctx, clave(id), "nombre", p.Nombre, "precio", p.Precio, "descripcion", strings.Repeat("x", 2000))
	} else {
		rdb.HSet(ctx, clave(id), "nombre", p.Nombre, "precio", p.Precio)
	}
	rdb.Expire(ctx, clave(id), ttl)
	return p, false, nil
}

// popular: unos pocos productos se piden mucho (distribución de Zipf sobre 1.000).
func popular(r *rand.Rand, z *rand.Zipf) int { return int(z.Uint64()) + 1 }

func medir(n, c int, una func(id int) bool) {
	var mu sync.Mutex
	var lat []time.Duration
	aciertos := 0
	cola := make(chan int, n)
	r := rand.New(rand.NewPCG(1, 2))
	z := rand.NewZipf(r, 1.2, 1, 999)
	for i := 0; i < n; i++ {
		cola <- popular(r, z)
	}
	close(cola)
	t0 := time.Now()
	var wg sync.WaitGroup
	for w := 0; w < c; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for id := range cola {
				ini := time.Now()
				ok := una(id)
				d := time.Since(ini)
				mu.Lock()
				lat = append(lat, d)
				if ok {
					aciertos++
				}
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	sort.Slice(lat, func(i, j int) bool { return lat[i] < lat[j] })
	q := func(p float64) time.Duration { return lat[int(float64(len(lat)-1)*p)].Round(10 * time.Microsecond) }
	fmt.Printf("  %d lecturas en %v · p50 %v · p99 %v\n", n, time.Since(t0).Round(10*time.Millisecond), q(.5), q(.99))
	fmt.Printf("  aciertos de caché: %d (%.1f %%) · consultas a la BD: %d\n",
		aciertos, 100*float64(aciertos)/float64(n), consultas.Load())
}

func main() {
	var err error
	db, err = pgxpool.New(ctx, "postgres://postgres:lab@sd-pg:5432/tienda?pool_max_conns=50")
	if err != nil {
		panic(err)
	}
	// Timeouts de 200 ms (los de serie son 5 s para conectar y 3 s para leer): con una caché caída,
	// cada lectura espera ese tiempo antes de ir a la base de datos.
	rdb = redis.NewClient(&redis.Options{Addr: "sd-valkey:6379", PoolSize: 200,
		DialTimeout: 200 * time.Millisecond, ReadTimeout: 200 * time.Millisecond})
	orden := os.Args[1]
	fs := flag.NewFlagSet(orden, flag.ExitOnError)
	n := fs.Int("n", 2000, "lecturas")
	modo := fs.String("modo", "nada", "estampida: nada, singleflight, cerrojo")
	jitter := fs.Bool("jitter", false, "expiración: TTL con ±30 % de azar")
	ttlFlag := fs.Duration("ttl", 5*time.Second, "ttl: la caducidad que se prueba")
	fs.Parse(os.Args[2:])

	switch orden {
	case "preparar":
		db.Exec(ctx, "DROP TABLE IF EXISTS productos")
		db.Exec(ctx, "CREATE TABLE productos (id int PRIMARY KEY, nombre text, precio int)")
		db.Exec(ctx, "INSERT INTO productos SELECT g, 'producto ' || g, 100 FROM generate_series(1, 1000) g")
		rdb.FlushAll(ctx)
		fmt.Println("  1000 productos en Postgres · Valkey vacío")

	case "sincache":
		medir(*n, 20, func(id int) bool { deBD(id); return false })

	case "concache":
		rdb.FlushAll(ctx)
		medir(*n, 20, func(id int) bool { _, hit, _ := leer(id, 60*time.Second); return hit })

	case "vieja":
		rdb.FlushAll(ctx)
		p, _, _ := leer(1, 60*time.Second)
		fmt.Printf("  leo el producto 1: %d €  (ahora está en caché)\n", p.Precio)
		db.Exec(ctx, "UPDATE productos SET precio = 120 WHERE id = 1")
		p, hit, _ := leer(1, 60*time.Second)
		fmt.Printf("  UPDATE precio = 120 en la BD · leo otra vez: %d €  (de la caché: %v)\n", p.Precio, hit)
		db.Exec(ctx, "UPDATE productos SET precio = 130 WHERE id = 1")
		rdb.Del(ctx, clave(1))
		p, hit, _ = leer(1, 60*time.Second)
		fmt.Printf("  UPDATE precio = 130 y DEL de la clave · leo: %d €  (de la caché: %v)\n", p.Precio, hit)
		db.Exec(ctx, "UPDATE productos SET precio = 100 WHERE id = 1")

	case "estampida":
		coste = 0.2 // la clave caliente es cara de reconstruir
		rdb.FlushAll(ctx)
		leer(1, time.Second) // la clave más pedida, con 1 s de vida
		time.Sleep(1100 * time.Millisecond)
		consultas.Store(0)
		var g singleflight.Group
		var grupos [4]singleflight.Group // 4 instancias de la app, cada una con su singleflight
		var wg sync.WaitGroup
		inicio := make(chan struct{})
		var lat [100]time.Duration
		for i := 0; i < 100; i++ {
			wg.Add(1)
			go func(i int) {
				defer wg.Done()
				<-inicio
				t := time.Now()
				switch *modo {
				case "nada":
					leer(1, time.Minute)
				case "singleflight":
					g.Do("1", func() (any, error) { p, _, err := leer(1, time.Minute); return p, err })
				case "instancias":
					grupos[i%4].Do("1", func() (any, error) { p, _, err := leer(1, time.Minute); return p, err })
				case "cerrojo":
					leerConCerrojo(1)
				}
				lat[i] = time.Since(t)
			}(i)
		}
		close(inicio)
		wg.Wait()
		peor := time.Duration(0)
		for _, d := range lat {
			peor = max(peor, d)
		}
		fmt.Printf("  %-12s 100 peticiones a la vez · consultas a la BD: %3d · la más lenta: %v\n",
			*modo, consultas.Load(), peor.Round(time.Millisecond))

	case "ttl":
		// 20 lectores durante 6 s; cuanto más corto el TTL, más fallos y más consultas.
		rdb.FlushAll(ctx)
		var lecturas, aciertos atomic.Int64
		t0 := time.Now()
		var wg sync.WaitGroup
		for w := 0; w < 20; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				r := rand.New(rand.NewPCG(uint64(w), 7))
				z := rand.NewZipf(r, 1.2, 1, 999)
				for time.Since(t0) < 6*time.Second {
					_, hit, _ := leer(popular(r, z), *ttlFlag)
					lecturas.Add(1)
					if hit {
						aciertos.Add(1)
					}
					time.Sleep(2 * time.Millisecond)
				}
			}(w)
		}
		wg.Wait()
		fmt.Printf("  TTL %-4v %6d lecturas · aciertos %5.1f %% · consultas a la BD: %d\n", *ttlFlag,
			lecturas.Load(), 100*float64(aciertos.Load())/float64(lecturas.Load()), consultas.Load())

	case "llena":
		// Una caché más pequeña que los datos: maxmemory = lo que ya usa + 1 MB, y desalojo LRU.
		// Cada producto ocupa ~2 KB (una descripción larga): 1.000 productos no caben.
		rdb.FlushAll(ctx)
		base := memoria("used_memory")
		rdb.ConfigSet(ctx, "maxmemory", strconv.FormatInt(base+1<<20, 10))
		rdb.ConfigSet(ctx, "maxmemory-policy", "allkeys-lru")
		grande = true
		medir(*n, 20, func(id int) bool { _, hit, _ := leer(id, 60*time.Second); return hit })
		fmt.Printf("  claves expulsadas por falta de memoria (evicted_keys): %d\n", memoria("evicted_keys"))
		rdb.ConfigSet(ctx, "maxmemory", "0")

	case "caida":
		// Valkey está parado (lo para correr.py): cada lectura espera el timeout y va a la BD.
		medir(*n, 20, func(id int) bool { _, hit, _ := leer(id, 60*time.Second); return hit })

	case "inexistente":
		// 100 peticiones del producto 5000, que no existe: no hay nada que guardar en la caché.
		rdb.FlushAll(ctx)
		for _, negativa := range []bool{false, true} {
			consultas.Store(0)
			var wg sync.WaitGroup
			for i := 0; i < 100; i++ {
				wg.Add(1)
				go func() { defer wg.Done(); leerNegativo(5000, negativa) }()
				time.Sleep(time.Millisecond)
			}
			wg.Wait()
			fmt.Printf("  caché negativa %-5v 100 peticiones del producto 5000 (no existe) · consultas a la BD: %d\n",
				negativa, consultas.Load())
		}

	case "expiracion":
		// Las 1.000 claves se cargan DE GOLPE (un pipeline), como un calentamiento de caché o un
		// arranque: todas nacen en el mismo instante. Sin jitter, mueren en el mismo instante.
		rdb.FlushAll(ctx)
		r := rand.New(rand.NewPCG(3, 4))
		pipe := rdb.Pipeline()
		for id := 1; id <= 1000; id++ {
			ttl := 5 * time.Second
			if *jitter {
				ttl = time.Duration(float64(ttl) * (0.7 + 0.6*r.Float64()))
			}
			pipe.HSet(ctx, clave(id), "nombre", "producto "+strconv.Itoa(id), "precio", 100)
			pipe.Expire(ctx, clave(id), ttl)
		}
		if _, err := pipe.Exec(ctx); err != nil {
			panic(err)
		}
		consultas.Store(0)
		t0 := time.Now()
		var wg sync.WaitGroup
		for w := 0; w < 50; w++ { // 50 lectores a la vez, cada uno con productos al azar
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				rw := rand.New(rand.NewPCG(uint64(w), 9))
				for time.Since(t0) < 9*time.Second {
					leer(rw.IntN(1000)+1, 5*time.Second)
					time.Sleep(20 * time.Millisecond)
				}
			}(w)
		}
		previas := int64(0)
		for s := 0; s < 9; s++ {
			time.Sleep(time.Until(t0.Add(time.Duration(s+1) * time.Second)))
			ahora := consultas.Load()
			fmt.Printf("  segundo %d: %4d consultas a la BD\n", s, ahora-previas)
			previas = ahora
		}
		wg.Wait()
	}
}

// grande: en «llena», cada producto se guarda con una descripción de 2 KB.
var grande bool

func memoria(campo string) int64 {
	info, _ := rdb.Info(ctx, "memory", "stats").Result()
	for _, l := range strings.Split(info, "\n") {
		if v, ok := strings.CutPrefix(l, campo+":"); ok {
			n, _ := strconv.ParseInt(strings.TrimSpace(v), 10, 64) // INFO separa con \r\n
			return n
		}
	}
	return 0
}

// leerNegativo: como leer, pero si el producto NO existe guarda esa respuesta («nada») 30 s.
func leerNegativo(id int, negativa bool) {
	if v, err := rdb.HGetAll(ctx, clave(id)).Result(); err == nil && len(v) > 0 {
		return // acierto, aunque sea un «no existe»
	}
	if _, err := deBD(id); errors.Is(err, pgx.ErrNoRows) && negativa {
		rdb.HSet(ctx, clave(id), "nada", 1)
		rdb.Expire(ctx, clave(id), 30*time.Second)
	}
}

// leerConCerrojo: si no está en caché, solo UNA petición (la que consigue el cerrojo en Valkey)
// va a la base de datos; las demás esperan a que aparezca la clave. Vale entre instancias.
func leerConCerrojo(id int) producto {
	for {
		if v, err := rdb.HGetAll(ctx, clave(id)).Result(); err == nil && len(v) > 0 {
			precio, _ := strconv.Atoi(v["precio"])
			return producto{v["nombre"], precio}
		}
		ok, err := rdb.SetNX(ctx, "cerrojo:"+clave(id), "1", 5*time.Second).Result()
		if err != nil && !errors.Is(err, redis.Nil) {
			panic(err)
		}
		if ok {
			p, _, _ := leer(id, time.Minute)
			rdb.Del(ctx, "cerrojo:"+clave(id))
			return p
		}
		time.Sleep(5 * time.Millisecond)
	}
}
