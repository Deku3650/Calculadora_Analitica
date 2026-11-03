"""
pages/9_Calculo_Guia.py
=======================
Guía de uso del módulo de Cálculo: qué se puede hacer, cómo escribirlo con el teclado, qué significa cada notación
(sobre todo conjuntos y lógica) y qué hacer cuando algo no sale.

Los ejemplos están en guia_ejemplos.py (se prueban automáticamente con la app real). El botón «Probar» manda el ejemplo
a la página de Cálculo, que lo carga ya escrito en el teclado.
"""
import streamlit as st

st.set_page_config(page_title="Guía de Cálculo", page_icon="📖", layout="wide")

from guia_ejemplos import EJEMPLOS, TEMAS  # noqa: E402

st.title("📖 Guía de uso — Cálculo, conjuntos y lógica")
st.caption("Cómo escribir lo que quieres calcular, qué obtienes y qué hacer si algo no sale. Cada ejemplo tiene un botón **▶ Probar** que lo abre ya escrito.")


def _probar(latex: str, clave: str):
    if st.button("▶ Probar", key=clave, use_container_width=True):
        st.session_state["calculo_ejemplo"] = latex
        st.switch_page("pages/9_Calculo.py")


t_empezar, t_ejemplos, t_notacion, t_faq, t_limites = st.tabs(
    ["🚀 Empezar", "📚 Qué puedes hacer (ejemplos)", "🧩 Conjuntos y lógica, explicados", "❓ Preguntas y errores comunes", "⚠️ Lo que aún no hace"])

# ------------------------------------------------------------------------------------------------------------------
with t_empezar:
    st.markdown("""
### Cómo funciona, en tres pasos
1. **Escribe** con el teclado matemático (o con el teclado de tu equipo) y pulsa **↵** para confirmar.
2. **Revisa «Entiendo:»**: la app te dice *en español* qué leyó (por ejemplo «la derivada de x al cuadrado por seno de x»). Si no es lo que querías, corrige: **es la mejor forma de no recibir una respuesta a otra pregunta**.
3. **Elige el análisis**: según lo que escribiste, la app ofrece lo que corresponde (para una función: dominio, límites, derivadas, integrales, series, Taylor…).

### Los avisos
| Aviso | Significa |
|---|---|
| ⛔ **Error** | Lo escrito no tiene sentido matemático (por ejemplo ln(−2), o un intervalo [3, 1]). No se calcula hasta corregirlo. |
| ⚠️ **Aviso** | Tiene sentido, pero probablemente no es lo que querías (por ejemplo una letra que no se usa). |
| ℹ️ **Información** | Una aclaración útil (por ejemplo «ℕ se toma como {1, 2, 3, …}»). |

### ¿Qué tan seguro es cada resultado?
Cuando hay incertidumbre, la app lo dice con una etiqueta:
- **exacto**: cálculo simbólico (un teorema o una cuenta exacta).
- **criterio**: se aplicó un criterio suficiente (por ejemplo «todas las desigualdades son ≤, luego es cerrado»).
- **contraejemplo**: se encontró un caso concreto que refuta la afirmación, y se verificó con cuentas exactas.
- **evidencia**: se probó numéricamente (muestreo). **No es una demostración.**

### Mapa del teclado
| Pestaña | Qué tiene |
|---|---|
| **123** | números, x, y, π, e, potencias, fracciones, raíces, valor absoluto, paréntesis |
| **f(x)** | ln, log, exponenciales, factorial, funciones por trozos, **Σ, Π, límite, integral (definida e indefinida), d/dx, ∂/∂x, ∇**, combinaciones, máx, mín |
| **sin cos tan** | trigonométricas, hiperbólicas y sus inversas |
| **abc** | letras y letras griegas, con subíndice |
| **#&\\*** | corchetes y llaves, ⟨ ⟩, ‖ ‖, **∈ ∉ ⊂ ⊆ ∪ ∩ ∖**, ∅ ℝ ℕ ℤ ℚ ℂ, ≤ ≥ ≠ ≈ ≡ ±, → ↦ ∘, **∧ ∨ ¬ ⇒ ⇔ ∀ ∃ ∄ ∴** |
| **ℝⁿ** | puntos y vectores, ‖v‖, u·v, u×v, d(p,q), **bolas**, int/cl/Fr/diam, {x ∣ condición}, intervalos, A×B, Aᶜ, ∀/∃, ↦, ∘, congruencias, y en la última fila: **∬, ∭, ∇·, ∇×, ∇², plantillas de curva y de superficie, x̄** |

> 💡 En el teléfono, escribe con el teclado de la app (no el del sistema): evita errores de símbolos.
""")

# ------------------------------------------------------------------------------------------------------------------
with t_ejemplos:
    st.markdown("Cada tema tiene ejemplos listos. Pulsa **▶ Probar** para abrirlos en la calculadora.")
    for ti, tema in enumerate(TEMAS):
        with st.expander(f"**{tema}**  ·  {len(EJEMPLOS[tema])} ejemplos", expanded=(ti == 0)):
            for k, ej in enumerate(EJEMPLOS[tema]):
                c1, c2, c3 = st.columns([5, 4, 1.2])
                with c1:
                    st.markdown(f"**{ej['titulo']}**")
                    st.markdown(ej["que_hace"])
                    st.caption("⌨️ " + ej["como"])
                with c2:
                    st.latex(ej["latex"])
                with c3:
                    _probar(ej["latex"], f"ej_{ti}_{k}")
                st.divider()

# ------------------------------------------------------------------------------------------------------------------
with t_notacion:
    st.markdown("""
### Lo que significa cada forma de escribir
La notación de conjuntos es la parte que más confunde. Esta tabla dice **cómo lee la app** lo que escribes.

| Escribes | Se lee como | Ejemplo |
|---|---|---|
| `( a, b )` con **dos números** | un **punto** de ℝ²; pero **dentro de ∪, ∩, ∖, ∈, ∀x∈ …** es el **intervalo abierto** de a a b | `(1,2)` es un punto; `(0,1) ∪ (2,3]` son intervalos |
| `[ a, b ]`, `[ a, b )`, `( a, b ]` | intervalos (cerrado, semiabierto) | `[0, 1)` |
| `( a, b, c )` con **tres números o más** | un punto de ℝⁿ | `(1, 2, 3)` |
| `⟨ a, b ⟩` | un **vector** (con flechas) | `⟨1, 2⟩ + ⟨3, 4⟩` |
| `[ a, b, c ]` o `a, b, c` | una **lista** (el orden y las repeticiones importan) | `1, 3, …, 21` |
| `{ a, b, c }` | un **conjunto finito** (el orden y las repeticiones no importan) | `{1, 2, 3}` |
| `{ x ∣ condición }` | el **conjunto de los x que cumplen** la condición | `{x ∣ x² < 4}` es el intervalo (−2, 2) |
| `{ (x,y) ∣ condición }` | una **región del plano** | `{(x,y) ∣ x² + y² ≤ 1}` es el disco |
| `{ x ∈ ℕ ∣ condición }` | como arriba, pero solo con naturales | `{x ∈ ℕ ∣ x < 5}` = {1, 2, 3, 4} |
| `{ 2n ∣ n ∈ ℤ }` | el conjunto de los **valores** que toma 2n | los pares |
| `B_r(p)` | **bola abierta** de radio r y centro p (en ℝ² es un disco) | `B_1(0,0)` |
| `B̄_r(p)` | bola **cerrada** (incluye el borde) | `B̄_2(1,2,3)` |
| `S_r(p)` | la **esfera** (solo el borde) | `S_1(0,0,0)` |
| `A ∪ B`, `A ∩ B`, `A ∖ B`, `Aᶜ` | unión, intersección, diferencia, complemento | `[0,3] ∖ (1,2)` |
| `A × B` | producto de conjuntos (rectángulos, cajas) | `[0,1] × [2,3]` |
| `a ∈ A`, `a ∉ A` | pertenencia | `3 ∈ [0,5]` es verdadero |
| `A ⊂ B`, `A ⊆ B` | A está contenido en B (⊂: y además son distintos) | `[0,1] ⊂ [0,2]` |
| `int(A)`, `cl(A)`, `Fr(A)` o `∂A`, `diam(A)` | interior, cerradura, frontera, diámetro | `∂B_1(0,0)` |
| `ℝ, ℕ, ℤ, ℚ, ℂ, ℝⁿ, ℝ⁺` | los conjuntos numéricos | **ℕ = {1, 2, 3, …}** (se puede cambiar) |

### Lógica
| Escribes | Significa |
|---|---|
| `p ∧ q`, `p ∨ q`, `¬p` | y, o, no |
| `p ⇒ q`, `p ⇔ q` | implica, si y solo si |
| `∀x ∈ A : …`, `∃x ∈ A : …`, `∄x ∈ A : …` | para todo, existe, no existe |
| `p ⇒ q, p ∴ q` | un **argumento**: premisas separadas por comas, y **∴** antes de la conclusión |
| `a ≡ b (mod n)`, `a ∣ b` | congruencia, divisibilidad |
| `x ↦ x²`, `f ∘ g` | una función, composición |

> Una **letra suelta** (p, q) dentro de ∧ ∨ ¬ ⇒ es una **proposición**. Con desigualdades (x > 0) la lógica se evalúa sobre los números reales.

### Subíndices: etiqueta o elemento
- `x_1`, `x_{12}`, `v_0`, `x_max` → son **nombres** distintos (etiquetas).
- Dentro de Σ o Π, `x_i`, `x_{i-1}`, `a_{n+1}`, `a_{ij}` → son **elementos de una lista** (el i-ésimo valor). Así la app reconoce sumas telescópicas y puede reindexar.

### Parametrizar curvas y superficies
- Un vector con **un** parámetro libre es una **curva**: `⟨cos t, sin t, t⟩, 0 ≤ t ≤ 4π`. El intervalo va después de una coma.
- Con **dos** parámetros y tres componentes es una **superficie**: `⟨u cos v, u sin v, u²⟩, 0 ≤ u ≤ 1, 0 ≤ v ≤ 2π`.
- El **orden de los parámetros** es el de las condiciones, y fija la orientación (la normal es r_u × r_v). Para una esfera, escribe `0 ≤ φ ≤ π, 0 ≤ θ ≤ 2π` y la normal apunta hacia afuera.
- También puedes escribir `r(t) = ⟨…⟩` o `r(u, v) = ⟨…⟩`.
""")

# ------------------------------------------------------------------------------------------------------------------
with t_faq:
    faqs = [
        ("«Entiendo:» dice algo distinto de lo que quise",
         "Corrige antes de seguir. Las causas comunes: falta un paréntesis (`sen x + 1` ≠ `sen(x + 1)`), una letra que se leyó como variable, o un `(a, b)` que se leyó como punto en vez de intervalo."),
        ("`(0,1)` ¿es un punto o un intervalo?",
         "Solo, es un punto de ℝ². Dentro de una unión, intersección, diferencia, `∈` o un cuantificador, es el intervalo abierto. Si quieres un punto en un conjunto de puntos, ponlo entre llaves: `{(0,1), (2,3)}`."),
        ("`dy/dx` me dice que «y es solo una letra»",
         "A propósito: no sé de qué depende `y`. Escribe la función (`d/dx (x² + 1)`) o una ecuación (`x² + y² = 25`) y elige **Derivación implícita**."),
        ("¿Cómo hago una integral de línea o de superficie?",
         "Primero escribe la **curva** (o la **superficie**) con su parametrización e intervalo. En su análisis hay una caja «Integral de línea» (o «de superficie»). Si escribes `∫_C` sin definir C, la app te lo recuerda."),
        ("El flujo me sale con el signo contrario",
         "La orientación es la de N = r_u × r_v, y depende del **orden de los parámetros**. Invierte el orden en las condiciones, o cambia el signo del resultado. La app dice si la normal apunta hacia afuera o hacia adentro."),
        ("¿Por qué mi vector `⟨x, 0⟩` se volvió una curva?",
         "Una vector con un único parámetro libre se lee como curva. Si es un **campo**, escríbelo dentro de las cajas de campo (integral de línea, flujo, teoremas), donde siempre se lee como campo."),
        ("Tres componentes y dos variables: ¿campo o superficie?",
         "Es ambiguo, así que la app te pregunta. Si las letras se llaman `u, v, s, t, θ, φ` supone **superficie**; si son `x, y`, te deja elegir."),
        ("Rotacional cero pero dice que NO es conservativo",
         "Correcto: si el dominio tiene un **hueco** (por ejemplo el campo del remolino, no definido en el origen), rotacional cero no basta. La app lo comprueba con la circulación alrededor del hueco."),
        ("¿Qué pasa con los resultados que dicen «evidencia»?",
         "Son numéricos (muestreo). Úsalos como pista, no como demostración. Los «exactos» sí lo son."),
        ("Tarda mucho o se corta",
         "Cada cálculo tiene un tiempo límite (entre 25 y 90 segundos según la operación) y corre aparte, así que no se cuelga la página. Prueba con una región más sencilla o con coordenadas que simplifiquen (polares, esféricas)."),
        ("¿ℕ incluye el 0?",
         "Por defecto no (ℕ = {1, 2, 3, …}). En **⚙️ Opciones** hay un interruptor «ℕ incluye el 0»."),
        ("¿Se puede integrar sobre una unión de regiones?",
         "Divide en regiones **disjuntas** e integra cada una por separado (la app lo avisa)."),
    ]
    for q, a in faqs:
        with st.expander(q):
            st.markdown(a)

# ------------------------------------------------------------------------------------------------------------------
with t_limites:
    st.markdown("""
### Lo que esta versión **todavía no** hace
- **Series de Fourier** y ecuaciones en derivadas parciales (para ecuaciones diferenciales ordinarias está el módulo 7).
- **Integrales sobre una unión** de regiones o regiones **no acotadas** (impropias de varias variables).
- Verificación automática de **Stokes** para dominios no rectangulares; de **Gauss** para regiones que no son bolas; de **Green** para regiones que no son círculos o rectángulos. (Las integrales mismas sí se calculan con cualquier región.)
- **Variable compleja** (funciones analíticas, residuos).
- Recurrencias como `aₙ₊₁ = 2aₙ + 1` (resolverlas) y cambio de variable con jacobiano **definido por el usuario** (polares, cilíndricas y esféricas sí están).
- Conjuntos de ℝⁿ con **n ≥ 4**: se analizan, pero no se dibujan.

### Si encuentras un error
Si un resultado te parece incorrecto, revisa primero «Entiendo:» y las etiquetas de rigor. Si aun así hay algo mal, anota la expresión exacta que escribiste: con eso se puede reproducir y arreglar.
""")
