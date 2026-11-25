// lab: repartir 100.000 claves entre servidores de tres formas, y medir qué pasa al añadir o
// quitar uno. Solo cálculo: no hay red ni disco.
//
//	módulo       servidor = hash(clave) % N
//	anillo       hashing consistente: cada servidor, V puntos en un anillo; la clave va al siguiente
//	rendezvous   la clave va al servidor con el hash(clave, servidor) más alto
package main

import (
	"fmt"
	"hash/fnv"
	"math"
	"sort"
	"strconv"
	"time"
)

const CLAVES = 100_000

// h: FNV-1a de 64 bits + el mezclador de splitmix64, para que claves parecidas caigan lejos.
func h(s string) uint64 {
	f := fnv.New64a()
	f.Write([]byte(s))
	x := f.Sum64()
	x ^= x >> 30
	x *= 0xbf58476d1ce4e5b9
	x ^= x >> 27
	x *= 0x94d049bb133111eb
	return x ^ (x >> 31)
}

func claves() []string {
	c := make([]string, CLAVES)
	for i := range c {
		c[i] = "usuario:" + strconv.Itoa(i)
	}
	return c
}

func servidores(n int) []string {
	s := make([]string, n)
	for i := range s {
		s[i] = "cache-" + strconv.Itoa(i)
	}
	return s
}

// hCrudo: FNV-1a de 64 bits SIN el mezclador, para ver qué pasa con un hash flojo.
func hCrudo(s string) uint64 {
	f := fnv.New64a()
	f.Write([]byte(s))
	return f.Sum64()
}

// anilloCrudo: el mismo anillo, pero con hCrudo para los puntos y para las claves.
func anilloCrudo(srv []string, v int) func(string) string {
	var puntos []uint64
	dueño := map[uint64]string{}
	for _, s := range srv {
		for i := 0; i < v; i++ {
			p := hCrudo(s + "#" + strconv.Itoa(i))
			puntos = append(puntos, p)
			dueño[p] = s
		}
	}
	sort.Slice(puntos, func(i, j int) bool { return puntos[i] < puntos[j] })
	return func(k string) string {
		x := hCrudo(k)
		i := sort.Search(len(puntos), func(i int) bool { return puntos[i] >= x })
		if i == len(puntos) {
			i = 0
		}
		return dueño[puntos[i]]
	}
}

// ── módulo
func modulo(srv []string) func(string) string {
	return func(k string) string { return srv[h(k)%uint64(len(srv))] }
}

// ── anillo con V nodos virtuales por servidor
type anillo struct {
	puntos []uint64
	dueño  map[uint64]string
}

func nuevoAnillo(srv []string, v int) *anillo {
	a := &anillo{dueño: map[uint64]string{}}
	for _, s := range srv {
		for i := 0; i < v; i++ {
			p := h(s + "#" + strconv.Itoa(i))
			a.puntos = append(a.puntos, p)
			a.dueño[p] = s
		}
	}
	sort.Slice(a.puntos, func(i, j int) bool { return a.puntos[i] < a.puntos[j] })
	return a
}

func (a *anillo) buscar(k string) string {
	x := h(k)
	i := sort.Search(len(a.puntos), func(i int) bool { return a.puntos[i] >= x })
	if i == len(a.puntos) {
		i = 0 // da la vuelta
	}
	return a.dueño[a.puntos[i]]
}

// ── rendezvous (el hash más alto)
func rendezvous(srv []string) func(string) string {
	return func(k string) string {
		mejor, quien := uint64(0), ""
		for _, s := range srv {
			if x := h(k + "|" + s); x >= mejor {
				mejor, quien = x, s
			}
		}
		return quien
	}
}

// ── jump consistent hash (Lamping y Veach, Google, 2014): sin anillo y sin memoria. Solo sirve si los
// servidores se numeran de 0 a N-1 y solo se añaden o quitan por el final.
func jump(key uint64, n int) int {
	var b, j int64 = -1, 0
	for j < int64(n) {
		b = j
		key = key*2862933555777941757 + 1
		j = int64(float64(b+1) * (float64(int64(1)<<31) / float64((key>>33)+1)))
	}
	return int(b)
}

func jumpDe(srv []string) func(string) string {
	return func(k string) string { return srv[jump(h(k), len(srv))] }
}

func movidas(cs []string, antes, despues func(string) string) float64 {
	m := 0
	for _, k := range cs {
		if antes(k) != despues(k) {
			m++
		}
	}
	return 100 * float64(m) / float64(len(cs))
}

func reparto(cs []string, f func(string) string, srv []string) string {
	cuenta := map[string]int{}
	for _, k := range cs {
		cuenta[f(k)]++
	}
	min, max := math.MaxInt, 0
	for _, s := range srv {
		min, max = minI(min, cuenta[s]), maxI(max, cuenta[s])
	}
	ideal := len(cs) / len(srv)
	return fmt.Sprintf("el que menos %6d · el que más %6d · el más cargado lleva %.2f veces lo justo",
		min, max, float64(max)/float64(ideal))
}

func minI(a, b int) int {
	if a < b {
		return a
	}
	return b
}
func maxI(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func main() {
	cs := claves()
	s4, s5 := servidores(4), servidores(5)
	sin2 := []string{"cache-0", "cache-1", "cache-3"} // cache-2 se cae

	fmt.Println("== 1 · De 4 a 5 servidores: ¿qué parte de las 100.000 claves cambia de servidor? ==")
	fmt.Printf("  módulo                      %5.1f %%\n", movidas(cs, modulo(s4), modulo(s5)))
	for _, v := range []int{1, 100} {
		a4, a5 := nuevoAnillo(s4, v), nuevoAnillo(s5, v)
		fmt.Printf("  anillo, %3d nodos virtuales %5.1f %%\n", v, movidas(cs, a4.buscar, a5.buscar))
	}
	fmt.Printf("  rendezvous                  %5.1f %%   (lo justo: 1 de cada 5 = 20 %%)\n",
		movidas(cs, rendezvous(s4), rendezvous(s5)))

	fmt.Println()
	fmt.Println("== 2 · Se cae cache-2 (de 4 a 3) ==")
	fmt.Printf("  módulo                      %5.1f %%\n", movidas(cs, modulo(s4), modulo(sin2)))
	a4, a3 := nuevoAnillo(s4, 100), nuevoAnillo(sin2, 100)
	fmt.Printf("  anillo, 100 nodos virtuales %5.1f %%   (lo justo: las de cache-2, 1 de cada 4 = 25 %%)\n",
		movidas(cs, a4.buscar, a3.buscar))
	// ¿a dónde van las claves de cache-2?
	destino := map[string]int{}
	for _, k := range cs {
		if a4.buscar(k) == "cache-2" {
			destino[a3.buscar(k)]++
		}
	}
	fmt.Printf("  sus claves se reparten entre: cache-0 %d · cache-1 %d · cache-3 %d\n",
		destino["cache-0"], destino["cache-1"], destino["cache-3"])
	a4v1, a3v1 := nuevoAnillo(s4, 1), nuevoAnillo(sin2, 1)
	destino = map[string]int{}
	for _, k := range cs {
		if a4v1.buscar(k) == "cache-2" {
			destino[a3v1.buscar(k)]++
		}
	}
	fmt.Printf("  sin nodos virtuales, van a:   cache-0 %d · cache-1 %d · cache-3 %d\n",
		destino["cache-0"], destino["cache-1"], destino["cache-3"])

	fmt.Println()
	fmt.Println("== 3 · ¿Cómo de justo es el reparto? 100.000 claves entre 4 servidores ==")
	fmt.Printf("  módulo                       %s\n", reparto(cs, modulo(s4), s4))
	for _, v := range []int{1, 10, 100, 1000} {
		fmt.Printf("  anillo, %4d nodos virtuales %s\n", v, reparto(cs, nuevoAnillo(s4, v).buscar, s4))
	}
	fmt.Printf("  rendezvous                   %s\n", reparto(cs, rendezvous(s4), s4))

	fmt.Println()
	fmt.Println("== 4 · Lo que cuesta buscar una clave (100.000 búsquedas) ==")
	for _, n := range []int{4, 50} {
		srv := servidores(n)
		a := nuevoAnillo(srv, 100)
		r := rendezvous(srv)
		m := modulo(srv)
		for _, caso := range []struct {
			nombre string
			f      func(string) string
		}{{"módulo", m}, {"anillo (100 virtuales)", a.buscar}, {"rendezvous", r}} {
			t := time.Now()
			for _, k := range cs {
				caso.f(k)
			}
			fmt.Printf("  %2d servidores · %-22s %6.0f ns por clave\n", n, caso.nombre,
				float64(time.Since(t).Nanoseconds())/CLAVES)
		}
	}
	fmt.Println()
	fmt.Println("== 5 · Jump consistent hash: sin anillo y sin memoria ==")
	fmt.Printf("  de 4 a 5 servidores:          %5.1f %%\n", movidas(cs, jumpDe(s4), jumpDe(s5)))
	fmt.Printf("  reparto entre 4:              %s\n", reparto(cs, jumpDe(s4), s4))
	t0 := time.Now()
	j50 := jumpDe(servidores(50))
	for _, k := range cs {
		j50(k)
	}
	fmt.Printf("  buscar, 50 servidores:        %6.0f ns por clave\n", float64(time.Since(t0).Nanoseconds())/CLAVES)

	fmt.Println()
	fmt.Println("== 6 · Un servidor el doble de grande: el doble de nodos virtuales ==")
	pesos := &anillo{dueño: map[uint64]string{}}
	for _, s := range s4 {
		v := 100
		if s == "cache-0" {
			v = 200
		}
		for i := 0; i < v; i++ {
			pt := h(s + "#" + strconv.Itoa(i))
			pesos.puntos = append(pesos.puntos, pt)
			pesos.dueño[pt] = s
		}
	}
	sort.Slice(pesos.puntos, func(i, j int) bool { return pesos.puntos[i] < pesos.puntos[j] })
	cuenta := map[string]int{}
	for _, k := range cs {
		cuenta[pesos.buscar(k)]++
	}
	fmt.Printf("  cache-0 con 200 nodos, el resto con 100: cache-0 %d · cache-1 %d · cache-2 %d · cache-3 %d\n",
		cuenta["cache-0"], cuenta["cache-1"], cuenta["cache-2"], cuenta["cache-3"])
	fmt.Println("  (lo justo con pesos 2:1:1:1 → cache-0 40.000, los demás 20.000)")

	fmt.Println()
	fmt.Println("== 7 · Cada clave en 3 servidores: los 3 siguientes distintos del anillo (como Dynamo) ==")
	a100 := nuevoAnillo(s4, 100)
	copias := map[string]int{}
	for _, k := range cs {
		x := h(k)
		i := sort.Search(len(a100.puntos), func(i int) bool { return a100.puntos[i] >= x })
		vistos := map[string]bool{}
		for len(vistos) < 3 {
			s := a100.dueño[a100.puntos[i%len(a100.puntos)]]
			if !vistos[s] {
				vistos[s] = true
				copias[s]++
			}
			i++
		}
	}
	fmt.Printf("  copias por servidor (300.000 en total): cache-0 %d · cache-1 %d · cache-2 %d · cache-3 %d\n",
		copias["cache-0"], copias["cache-1"], copias["cache-2"], copias["cache-3"])

	fmt.Println()
	fmt.Println("== 8 · ¿Importa la función de hash? El anillo con FNV-1a a secas, sin mezclador ==")
	for _, v := range []int{100, 1000} {
		fmt.Printf("  FNV a secas, %4d virtuales  %s\n", v, reparto(cs, anilloCrudo(s4, v), s4))
		fmt.Printf("  FNV + mezcla, %4d virtuales %s\n", v, reparto(cs, nuevoAnillo(s4, v).buscar, s4))
	}
}
