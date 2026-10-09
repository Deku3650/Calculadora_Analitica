"""
pages/9_Calculo.py
==================
PROTOTIPO del módulo de Cálculo, hecho SOLO para probar el teclado matemático.
Qué hace: captura una función con el teclado, la interpreta con SymPy y muestra
sus variables, el gradiente y la matriz Hessiana. Todavía no es el módulo final.

Requiere: streamlit >= 1.51, sympy, y teclado_matematico.py en la raíz del repo
(junto a utils.py).
"""
import streamlit as st
import sympy as sp

from teclado_matematico import (
    ErrorLatex,
    ErrorNoSoportado,
    latex_a_sympy,
    teclado_matematico,
)

st.set_page_config(page_title="Cálculo · prototipo del teclado", page_icon="∑", layout="wide")

st.title("∑ Cálculo — prototipo del teclado")
st.caption(
    "Escribe una función con el teclado de abajo y pulsa **↵**. "
    "La app muestra qué entendió y calcula su gradiente y su Hessiana."
)

# ------------------------------------------------------------------ opciones
with st.sidebar:
    st.header("Opciones de prueba")
    acoplado = st.toggle(
        "Teclado acoplado abajo",
        value=False,
        help="Estilo móvil: el teclado se desliza desde el borde inferior al tocar el campo.",
    )
    en_vivo = st.toggle(
        "Actualizar mientras escribo",
        value=False,
        help="Si está apagado, la app solo se actualiza al pulsar ↵ o salir del campo.",
    )
    i_imaginaria = st.toggle(
        "La letra «i» (pestaña abc) es √−1",
        value=False,
        help="La tecla «i» de la pestaña f(x) siempre es la unidad imaginaria.",
    )


# ------------------------------------------------------------------ análisis
def mostrar_analisis(expr: sp.Basic) -> None:
    """Variables, gradiente y Hessiana de una función f: ℝⁿ → ℝ."""
    if not isinstance(expr, sp.Expr):
        st.info(
            "Esto es una relación (ecuación o desigualdad), no una función. "
            "Escríbela sin «=», «<» o «>» para analizarla como f(x, y, …)."
        )
        return

    variables = sorted(expr.free_symbols, key=lambda s: s.name)
    n = len(variables)
    if n == 0:
        st.success("Es una constante.")
        st.latex(sp.latex(expr) + r" \approx " + sp.latex(sp.N(expr, 12)))
        return

    nombres = ", ".join(f"`{v}`" for v in variables)
    st.markdown(f"**Variables:** {nombres}  →  f : ℝ^{n} → ℝ")
    try:
        gradiente = sp.Matrix([sp.diff(expr, v) for v in variables])
        st.latex(r"\nabla f = " + sp.latex(gradiente))
        if n <= 3:
            st.latex(r"H_f = " + sp.latex(sp.hessian(expr, variables)))
        else:
            st.caption("La Hessiana se omite con más de 3 variables en este prototipo.")
    except Exception as e:  # noqa: BLE001  (prototipo: mostrar el problema, no tumbar la página)
        st.warning(f"No pude derivar esta expresión: {e}")


# ------------------------------------------------------------------ interfaz
col_in, col_out = st.columns([1.15, 1], gap="large")

with col_in:
    st.subheader("1 · Escribe")
    try:
        latex = teclado_matematico("calculo_f", acoplado=acoplado, en_vivo=en_vivo)
    except RuntimeError as e:  # Streamlit demasiado viejo
        st.error(str(e))
        st.stop()

    with st.expander("¿Qué puedo probar?"):
        st.markdown(
            """
- **123:** `3x²+1`, una fracción `(x²−1)/(x+1)`, `√(x²+y²)`, `|x−1|`
- **f(x):** `ln(x)`, `log₂(8)`, una función **por trozos**, `n!`, `⌊x⌋`
- **sin cos tan:** `sin²(x)`, `cos⁻¹(x)`, `sech(x)`, `30°`
- **abc / #&\\*:** variables `x₁`, `x₂` (con la tecla de subíndice) para funciones de ℝⁿ

Las teclas **∫, Σ, lím, d/dx** ya escriben, pero el intérprete todavía no las evalúa:
la app te avisará en lugar de fallar.
            """
        )

with col_out:
    st.subheader("2 · Lo que entendió la app")
    if not latex:
        st.info("Aún no hay nada confirmado. Escribe algo y pulsa **↵**.")
    else:
        st.markdown("**LaTeX capturado**")
        st.code(latex, language="latex")
        try:
            expr = latex_a_sympy(latex, i_imaginaria=i_imaginaria)
        except ErrorNoSoportado as e:
            st.warning(str(e))
        except ErrorLatex as e:
            st.error(str(e))
        else:
            st.markdown("**Expresión interpretada**")
            st.latex(sp.latex(expr))
            st.markdown("**Análisis**")
            mostrar_analisis(expr)
