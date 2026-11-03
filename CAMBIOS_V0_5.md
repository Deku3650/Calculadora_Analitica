# Mathesis v0.5 — cambios respecto de v0.3

## Cálculo vectorial e integrales (Cálculo 3 y 4)
- **Integrales dobles y triples sobre regiones** (`calculo_integrales_multiples.py`): `∬_D f dA`, `∭_E f dV`, con la región como conjunto
  `{(x,y) ∣ …}`, producto de intervalos `[0,1]×[0,2]`, bola `B_r(p)` o desigualdades separadas por comas. Deduce los límites de integración
  (cartesianas con varios órdenes, **polares, cilíndricas, esféricas**, incluso con el centro trasladado), muestra el procedimiento con el jacobiano y da
  área/volumen, valor promedio y centro de masa. Cada resultado exacto se **contrasta con Monte Carlo** (SymPy a veces integra mal con raíces cuadradas).
- **Operadores**: `∇·F`, `∇×F`, `∇²f` (y `div`, `rot`, `lap`), con fórmula, términos e interpretación.
- **Campos vectoriales** (`calculo_vectorial.py`): jacobiano, divergencia, rotacional, ¿conservativo?, **función potencial** y la advertencia del
  dominio con huecos (campo del remolino: rotacional 0 pero NO conservativo, comprobado con la circulación). Figuras con líneas de flujo y curvas de nivel.
- **Integrales de línea**: `∫ f ds`, `∫ F·dr` (trabajo/circulación) y flujo plano, con comprobación por función potencial y por el teorema de Green.
- **Superficies paramétricas** (`calculo_superficies.py`): normal, plano tangente, formas fundamentales, curvaturas de Gauss y media, reconocimiento
  de plano/esfera/cilindro/cono, área, **integral de superficie y flujo**.
- **Teoremas de Green, Stokes y Gauss**: se calculan los dos lados y se comprueba que coinciden.
- **Derivación implícita** (`F(x,y)=0` → dy/dx, d²y/dx², recta tangente; `F(x,y,z)=0` → ∂z/∂x, ∂z/∂y, plano tangente) y **regla de la cadena**.

## Curvas, sumas y estructuras
- **Curvas paramétricas** (`calculo_curvas.py`): suavidad (y dónde falla), tangente, normal, binormal, curvatura, torsión, Frenet–Serret, longitud,
  evoluta, planos osculador/normal/rectificante, circunferencia osculadora; figuras 2D y 3D. «Curvatura de la gráfica» para y = f(x).
- **Sumas con subíndices** (`calculo_sumas.py`): `x_i`, `x_{i-1}`, `a_{n+1}`, `a_{ij}` son elementos de una lista; telescopado explicado, linealidad,
  reindexado, sumas dobles, evaluación con datos (x̄ = promedio) y **teorema del binomio**.
- Conjuntos, topología, lógica, cuantificadores, argumentos y congruencias (`estructuras.py`, `calculo_conjuntos.py`) e intérprete ampliado.

## Guía de uso (nueva)
- `pages/9_Calculo_Guia.py`: cómo empezar, **78 ejemplos con botón «▶ Probar»** que los carga ya escritos en el teclado, **notación de conjuntos y lógica
  explicada**, preguntas frecuentes y lo que aún no hace. Los ejemplos están en `guia_ejemplos.py` y `test_guia.py` pasa todos por la página real.
- Teclado: pestaña **ℝⁿ** (puntos, vectores, bolas, topología, conjuntos, cuantificadores) con una fila de `∬ ∭ ∇· ∇× ∇²`, plantillas de curva y
  superficie y x̄. Enlaces a la guía desde Inicio y desde la calculadora.

## Errores corregidos (varios eran resultados falsos en silencio)
- `\frac{dy}{dx}` se leía como `y/x`; `\frac{d(x²)}{dx}` como `x`. Ahora se deriva bien o se explica qué falta.
- `x_{i-1}` se leía como un símbolo `x_i1` (se perdía el signo).
- Con raíces cuadradas, SymPy daba un **0 falso** en integrales triples de bolas desplazadas: cada método exacto se valida con Monte Carlo y, si no concuerda, se descarta.
- El orden de los parámetros de una superficie (alfabético) invertía la normal (flujo −4π); ahora sigue el orden de las condiciones y se avisa la orientación.
- La **caché de la página** usaba `repr()` para curvas y superficies: dos curvas con distinto intervalo podían compartir resultado. Ahora la clave sale del contenido.
- `x!` = Γ(x+1) es válido para todo real salvo los enteros negativos (dominio, comprobaciones y gráficas).

## Pruebas
`python3 correr_pruebas.py RUTA/AL/REPO` (en `pruebas_v0_5.zip`) corre 19 baterías, incluidos 191 casos de la página y los 78 ejemplos de la guía.
Cobertura medida con ~54 expresiones típicas de Cálculo 1–4: 52 de 54 (antes 43/56). Las dos restantes: `∂²u/∂x²` con `u` sin definir (se rechaza
explicando por qué) y una suma que no tiene forma cerrada.

## Lo que aún no hace
Series de Fourier y EDP; integrales sobre uniones de regiones o regiones no acotadas; Green/Stokes/Gauss automáticos para dominios que no sean
círculo, rectángulo o bola; variable compleja; resolver recurrencias; conjuntos de ℝⁿ con n ≥ 4 (se analizan, no se dibujan).

## Notas técnicas
- `requirements.txt` no cambia (ya incluía scipy y mpmath).
- Los archivos que en tu v0.3 usaban saltos de línea CRLF conservan CRLF; el resto, LF.
