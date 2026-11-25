package demo

// Suma devuelve la suma de los valores.
func Suma(xs []float64) float64 {
    total := 0.0
    for _, x := range xs {
        total += x
    }
    return total
}

// Maximo devuelve el mayor valor; ok es false si el slice está vacío.
func Maximo(xs []int) (m int, ok bool) {
	if len(xs)==0 { return 0, false }
	m = xs[0]
	for _, x := range xs[1:] {
		if x > m { m = x }
	}
	return m, true
}
