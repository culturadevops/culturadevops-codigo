# pruebas-lenguajes-vs

Código de estos vídeos del canal Cultura DevOps:

- [¿Python o Java? Lo medí: Java atiende 7 veces más, pero gasta más memoria](https://youtu.be/526ZT0cC9eQ)
- [¿Python o Rust? Lo medí: Rust atiende 5,6 veces más con 15 veces menos memoria](https://youtu.be/CrMzGrF6w88)
- [¿Python o PHP? Lo medí: empatan a tope, pero PHP usa 3 veces menos memoria](https://youtu.be/NlODEQkn0VM)
- [¿Node o Bun? Lo medí: Bun usa 4 veces menos memoria, pero Node calcula más rápido](https://youtu.be/mI-24QFExLg)
- [¿Node o Deno? Lo medí: con 2 núcleos Deno atiende más con 44 % menos memoria](https://youtu.be/MeeVcHu9HUU)
- [¿Node o PHP? Lo medí: Node atiende 2,5 veces más, pero PHP gana en cálculo puro](https://youtu.be/UECxKM1mz7s)
- [¿PHP o Rust? Lo medí: Rust atiende 5 veces más con la sexta parte de memoria](https://youtu.be/bwDC0SvwHmA)
- [¿PHP o Java? Lo medí: Java atiende casi 7 veces más, pero PHP gasta 4 veces menos memoria](https://youtu.be/roBpEnD54fk)
- [¿Java o Rust? Lo medí: Java atiende un 33 % más con objetos, pero Rust gasta 29 veces menos memoria](https://youtu.be/C1Zhjr7-QZA)
- [¿Node o Rust? Lo medí: Rust atiende 10 veces más en cálculo y el doble con 25 veces menos memoria](https://youtu.be/PpXW8vu9rtM)
- [¿Node o Java? Lo medí: Java atiende 3 veces más con objetos y casi la misma memoria](https://youtu.be/PCqXN_TpySE)
- [¿Para qué sirve Python y para qué NO? La lista honesta (2026)](https://youtu.be/hD_Z-VkHTSg)
- [¿Deno o Bun? Lo medí: Deno atiende un 18 % más, Bun gasta un 58 % menos de memoria](https://youtu.be/nz1KkP_USe4)
- [¿Python o Deno? Lo medí: Deno atiende 3 veces más que FastAPI y con menos memoria](https://youtu.be/3awYGa20k7U)
- [¿Deno o PHP? Lo medí: PHP gana en cálculo, Deno atiende 3 veces más con objetos](https://youtu.be/Qn8g_txhokg)
- [¿Deno o Java? Lo medí: Java atiende el doble con objetos, pero gasta el doble de memoria](https://youtu.be/F4ANBJW6Lpo)
- [¿Deno o Rust? Lo medí: Rust ×10 en cálculo y 12 veces menos memoria con objetos](https://youtu.be/mcg6_IPd6TE)

## Qué es

El código, los scripts de medición y los resultados (`SALIDA*.md`) que se ejecutaron para el vídeo. Las cifras del vídeo salen de estas ejecuciones.

## Cómo ejecutarlo

```bash
python correr.py
```

Casi todo corre dentro de Docker para que el resultado no dependa de tu máquina. Algunos scripts se escribieron para la estructura de carpetas original (rutas como `<repo>` o `<proyecto>`): ajústalas a la tuya.

## Resultados

Los resultados de la ejecución que sale en el vídeo están en los archivos `SALIDA*.md`.
