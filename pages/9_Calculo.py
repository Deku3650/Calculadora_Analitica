"""
pages/9_Calculo.py
==================
Módulo de Cálculo: se escribe una expresión con el teclado matemático y la app

  1. la INTERPRETA y dice, en español, qué entendió (tipo, lectura en palabras, variables);
  2. COMPRUEBA si tiene sentido (avisos y errores: dominios, límites invertidos, etc.);
  3. ofrece el análisis que corresponde: dominio, derivadas, límites, continuidad, extremos,
     integrales, series y sucesiones, Taylor, conjuntos de nivel y gráficas.

Archivos que usa (todos en la raíz del repo, junto a utils.py):
  teclado_matematico.py · interprete_latex.py · calculo_motor.py · calculo_graficas.py
Requiere: streamlit >= 1.51, sympy, numpy, matplotlib, mpmath, scipy.
"""
import itertools
import re
import threading
from collections import OrderedDict

import streamlit as st

st.set_page_config(page_title="Cálculo", page_icon="∑", layout="wide")

import sympy as sp  # noqa: E402

import calculo_graficas as G  # noqa: E402
import calculo_motor as M  # noqa: E402
from interprete_latex import (  # noqa: E402
    ErrorLatex, ErrorNoSoportado, ascii_a_sympy, ascii_lista, clasificar_entrada,
    diagnosticar, latex_a_sympy, leer_en_espanol,
)
from teclado_matematico import teclado_matematico  # noqa: E402


# ==============================================================================
# Ayudas generales
# ==============================================================================
@st.cache_resource
def _calentar():
    """Levanta el proceso trabajador una sola vez (así el primer cálculo no espera el arranque)."""
    return M.precalentar()


@st.cache_resource
def _almacen():
    return {"lock": threading.Lock(), "d": OrderedDict()}


def _clave(o) -> str:
    if isinstance(o, sp.Basic):
        return sp.srepr(o)
    if isinstance(o, (list, tuple)):
        return "[" + ",".join(_clave(i) for i in o) + "]"
    if isinstance(o, dict):
        return "{" + ",".join(f"{_clave(k)}:{_clave(v)}" for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))) + "}"
    return repr(o)


def calcular(nombre, *args, timeout=25, **kwargs):
    """Ejecuta una operación del motor en el proceso aislado y guarda el resultado (menos timeouts)."""
    _calentar()
    clave = f"{nombre}|{_clave(args)}|{_clave(kwargs)}"
    alm = _almacen()
    with alm["lock"]:
        if clave in alm["d"]:
            alm["d"].move_to_end(clave)
            return alm["d"][clave]
    with st.spinner("Calculando…"):
        r = M.ejecutar_seguro(nombre, *args, timeout=timeout, **kwargs)
    if not (r["datos"].get("timeout") or r["datos"].get("ocupado")):
        with alm["lock"]:
            alm["d"][clave] = r
            while len(alm["d"]) > 300:
                alm["d"].popitem(last=False)
    return r


def _celda(txt: str) -> str:
    """Una celda de tabla Markdown: las barras | rompen la tabla, se protegen."""
    partes = re.split(r"(\$[^$]*\$)", str(txt))
    return "".join(p.replace("|", "\\vert ") if p.startswith("$") else p.replace("|", "&#124;") for p in partes)


def mostrar(r):
    """Dibuja los bloques que devuelve el motor."""
    for bl in r["bloques"]:
        k = bl[0]
        if k == "h":
            st.markdown(f"##### {bl[1]}")
        elif k == "md":
            st.markdown(bl[1])
        elif k == "latex":
            st.latex(bl[1])
        elif k == "ok":
            st.success(bl[1])
        elif k == "aviso":
            st.warning(bl[1])
        elif k == "error":
            st.error(bl[1])
        elif k == "info":
            st.info(bl[1])
        elif k == "tabla":
            cols, filas = bl[1], bl[2]
            md = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
            md += "\n".join("| " + " | ".join(_celda(c) for c in f) + " |" for f in filas)
            st.markdown(md)


def figura(f):
    st.pyplot(f)


def hay_error(*rs) -> bool:
    return any(b[0] == "error" for r in rs for b in r["bloques"])


def leer_numero(texto, que="valor"):
    """Número (o ±oo) escrito como texto -> (sympy, None) o (None, mensaje)."""
    try:
        v = ascii_a_sympy(texto)
    except ErrorLatex as e:
        return None, f"{que}: {e}"
    if v.free_symbols:
        return None, f"{que}: debe ser un número (puedes usar pi, e, oo, sqrt(2)…)."
    return v, None


def leer_punto(texto, n_, que="El punto"):
    try:
        vals = ascii_lista(texto)
    except ErrorLatex as e:
        return None, f"{que}: {e}"
    if len(vals) != n_:
        return None, f"{que} debe tener {n_} coordenada(s) separadas por comas (escribiste {len(vals)})."
    if any(v.free_symbols or v.has(sp.oo, -sp.oo, sp.zoo) for v in vals):
        return None, f"{que} debe ser numérico y finito."
    return vals, None


def ventana_1d(clave, a0=-6.0, b0=6.0):
    with st.expander("🔧 Ventana de la gráfica"):
        c1, c2 = st.columns(2)
        with c1:
            a = st.number_input("x mínimo", value=float(a0), key=f"{clave}_a_{a0}_{b0}")
        with c2:
            b = st.number_input("x máximo", value=float(b0), key=f"{clave}_b_{a0}_{b0}")
    if a >= b:
        st.warning("El mínimo debe ser menor que el máximo; se usa la ventana por defecto.")
        return (a0, b0)
    return (a, b)


def ventana_2d(clave, r0=3.0, centro=(0.0, 0.0)):
    x0, y0 = centro
    with st.expander("🔧 Ventana de la gráfica"):
        c = st.columns(4)
        vals = []
        for i, (et, v0) in enumerate((("x mín", x0 - r0), ("x máx", x0 + r0), ("y mín", y0 - r0), ("y máx", y0 + r0))):
            with c[i]:
                vals.append(st.number_input(et, value=float(v0), key=f"{clave}_{et}_{r0}_{x0}_{y0}"))
    if vals[0] >= vals[1] or vals[2] >= vals[3]:
        st.warning("Los mínimos deben ser menores que los máximos; se usa la ventana por defecto.")
        return (x0 - r0, x0 + r0, y0 - r0, y0 + r0)
    return tuple(vals)


def _discontinuidades(r, tipos):
    """Abscisas de las discontinuidades de ciertos tipos (según continuidad_1d)."""
    return [d[0] for d in r["datos"].get("discontinuidades", [])
            if isinstance(d, tuple) and len(d) == 2 and d[1] in tipos]


# ==============================================================================
# Encabezado, opciones y teclado
# ==============================================================================
st.title("∑ Cálculo")
st.caption("Escribe con el teclado y pulsa **↵**. La app te dice **qué entendió**, comprueba que **tenga sentido** "
           "y te ofrece el análisis que corresponde.")

with st.expander("⚙️ Opciones", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        acoplado = st.toggle("Teclado acoplado abajo", value=False,
                             help="Estilo móvil: el teclado sube desde el borde inferior al tocar el campo.")
    with c2:
        en_vivo = st.toggle("Actualizar mientras escribo", value=False,
                            help="Si está apagado, la app se actualiza al pulsar ↵ o al salir del campo.")
    with c3:
        i_imag = st.toggle("La letra «i» (pestaña abc) es √−1", value=False,
                           help="La tecla «i» de la pestaña f(x) siempre es la unidad imaginaria.")

with st.expander("📖 Qué puedes escribir (guía rápida)"):
    st.markdown(
        """
**Una función** (la app te ofrece su análisis completo):
`x³ − 3x`, `(x²−1)/(x−1)`, `ln(x)/x`, `x²y + sin(y)`, una función **por trozos** (pestaña f(x)).

**Una operación** (la app la calcula y explica los pasos):
- Límite: tecla `lím` → `x → 0`; para laterales escribe `0⁺` o `0⁻` (con la tecla xⁿ). Varias variables: `(x,y) → (0,0)`.
- Integral: tecla `∫` (indefinida) o `∫ₐᵇ` (definida, impropias con `∞`). Dobles: una `∫` dentro de otra.
- Series: tecla `Σ` con `n = 1` abajo y `∞` arriba.
- Derivadas: teclas `d/dx` y `∂/∂x`. Gradiente: `∇`.

**Una ecuación o desigualdad**: `x² − 5x + 6 = 0`, `x² + y² ≤ 1`.

💡 Si dudas de cómo la leyó la app, mira el recuadro **«Lo que entendí»**: ahí aparece la frase en español.
        """
    )

latex = teclado_matematico("calculo_f", acoplado=acoplado, en_vivo=en_vivo)

if not latex:
    st.info("Aún no hay nada confirmado. Escribe una expresión y pulsa **↵**.")
    st.stop()

# ==============================================================================
# 1 · Interpretar, explicar y comprobar
# ==============================================================================
try:
    obj = latex_a_sympy(latex, i_imaginaria=i_imag)
except ErrorNoSoportado as e:
    st.warning(f"⚠️ {e}")
    st.stop()
except ErrorLatex as e:
    st.error(f"❌ No pude interpretar lo que escribiste: {e}")
    with st.expander("Ver el LaTeX capturado"):
        st.code(latex, language="latex")
    st.stop()

info = clasificar_entrada(obj)
diag = diagnosticar(obj, latex)
vs = info["variables"]
n = info["n"]

st.subheader("1 · Lo que entendí")
with st.container(border=True):
    st.markdown(f"**Tipo:** {info['etiqueta']}" + (f" — {info['detalle']}" if info.get("detalle") else ""))
    st.markdown(f"**Entiendo:** {leer_en_espanol(obj)}")
    try:
        st.latex(sp.latex(obj))
    except Exception:  # noqa: BLE001
        pass
    if vs and info["tipo"] not in ("serie", "suma_finita", "producto"):
        st.caption("Variables: " + ", ".join(f"`{v}`" for v in vs))

for d in diag:
    {"error": st.error, "aviso": st.warning, "info": st.info}[d["nivel"]](
        {"error": "⛔ ", "aviso": "⚠️ ", "info": "ℹ️ "}[d["nivel"]] + d["texto"])
if not diag:
    st.success("✅ La expresión tiene sentido (no encontré problemas).")
with st.expander("Ver el LaTeX capturado"):
    st.code(latex, language="latex")
if any(d["nivel"] == "error" for d in diag):
    st.error("Corrige lo señalado con ⛔ para poder continuar: con esos problemas el análisis no tendría sentido.")
    st.stop()

st.divider()


# ==============================================================================
# 2 · Secciones para funciones
# ==============================================================================
def sec_resumen(f, vs_):
    x = vs_[0] if len(vs_) == 1 else None
    r = calcular("dominio", f)
    mostrar(r)
    if x is not None:
        mostrar(calcular("ceros_cortes", f, x))
        mostrar(calcular("simetria_periodo", f, x))
        figura(G.fig_funcion_1d(f, x, ventana_1d("res")))
    elif len(vs_) == 2:
        conds = r["datos"].get("condiciones", [])
        if conds:
            st.markdown("##### Región del dominio (ℝ²)")
            figura(G.fig_region(sp.And(*conds) if len(conds) > 1 else conds[0], vs_[0], vs_[1], ventana_2d("resdom")))


def sec_analisis_1d(f, x):
    pasos = [("dominio", (f,)), ("ceros_cortes", (f, x)), ("simetria_periodo", (f, x)), ("continuidad_1d", (f, x)),
             ("asintotas", (f, x)), ("monotonia_extremos", (f, x)), ("concavidad", (f, x))]
    R, barra = {}, st.progress(0.0, text="Analizando la función…")
    for i, (nom, a) in enumerate(pasos):
        R[nom] = calcular(nom, *a)
        barra.progress((i + 1) / len(pasos), text=f"Analizando… ({i + 1}/{len(pasos)})")
    barra.empty()

    d_cero, d_mon = R["ceros_cortes"]["datos"], R["monotonia_extremos"]["datos"]
    d_conc, d_as = R["concavidad"]["datos"], R["asintotas"]["datos"]
    pts = [(p, 0, "cero", G.AZUL) for p in d_cero.get("ceros", [])]
    pts += [(c, fc, ("máx" if "máx" in t else "mín" if "mín" in t else "crít."), G.VERDE if "mín" in t else G.ROJO)
            for c, fc, t in d_mon.get("extremos", [])]
    pts += [(c, fc, "infl.", G.NARANJA) for c, fc in d_conc.get("inflexion", [])]
    xs = [M._flt(p[0]) for p in pts if M._flt(p[0]) is not None] + \
         [M._flt(v) for v in d_as.get("verticales", []) if M._flt(v) is not None]
    a0, b0 = (min(xs) - 2.5, max(xs) + 2.5) if xs else (-6.0, 6.0)
    a0, b0 = max(a0, -60.0), min(b0, 60.0)
    if b0 - a0 < 4:
        a0, b0 = a0 - 2, b0 + 2
    figura(G.fig_funcion_1d(f, x, ventana_1d("an1d", round(a0, 1), round(b0, 1)),
                            verticales=d_as.get("verticales", []), horizontales=d_as.get("horizontales", []),
                            oblicuas=d_as.get("oblicuas", []), puntos=pts,
                            cortes=_discontinuidades(R["continuidad_1d"], ("salto",))))
    st.caption("Rojo punteado: asíntotas · puntos azules: ceros · rojo/verde: máximos/mínimos locales · naranja: inflexiones.")
    tabs = st.tabs(["Dominio y rango", "Cortes y simetría", "Continuidad", "Asíntotas", "Crecimiento y extremos", "Concavidad"])
    grupos = (["dominio"], ["ceros_cortes", "simetria_periodo"], ["continuidad_1d"], ["asintotas"],
              ["monotonia_extremos"], ["concavidad"])
    for tab, claves in zip(tabs, grupos):
        with tab:
            for k in claves:
                mostrar(R[k])


def sec_derivadas(f, vs_):
    modos = ["Derivada", "Gradiente y Hessiana", "Recta / plano tangente"] + (["Derivada direccional"] if n >= 2 else [])
    modo = st.radio("Calcular", modos, horizontal=True, key=f"calc_der_{n}")
    nombres = ", ".join(str(v) for v in vs_)
    if modo == "Derivada":
        if n == 1:
            orden = st.slider("Orden de la derivada", 1, 6, 1, key="calc_der_orden")
            variables = [(vs_[0], orden)]
        else:
            st.caption("Elige cuántas veces derivar respecto de cada variable (0 = no derivar).")
            cols = st.columns(min(n, 4))
            variables = []
            for i, v in enumerate(vs_[:4]):
                with cols[i]:
                    k = st.number_input(f"veces en {v}", 0, 4, 1 if i == 0 else 0, key=f"calc_derv_{v}")
                if k:
                    variables.append((v, int(k)))
            if not variables:
                st.info("Elige al menos una derivada.")
                return
        punto = None
        if st.checkbox("Evaluar en un punto", key="calc_der_usarpunto"):
            pt, err = leer_punto(st.text_input(f"Punto ({nombres})", ",".join(["1"] * n), key="calc_der_punto"), n)
            if err:
                st.error(err)
                return
            punto = dict(zip(vs_, pt))
        r = calcular("derivar", f, variables, punto)
        mostrar(r)
        if n == 1 and not hay_error(r):
            figura(G.fig_funcion_1d(f, vs_[0], ventana_1d("der"),
                                    derivada=r["datos"].get("derivada") if variables[0][1] == 1 else None))
    elif modo == "Gradiente y Hessiana":
        t = st.text_input(f"Punto ({nombres}) — opcional", "", key="calc_gh_punto", help="Déjalo vacío para ver solo las fórmulas.")
        punto = None
        if t.strip():
            punto, err = leer_punto(t, n)
            if err:
                st.error(err)
                return
        mostrar(calcular("gradiente_hessiana", f, vs_, punto))
        if n == 2:
            figura(G.fig_niveles(f, vs_[0], vs_[1], ventana_2d("gh"), gradiente=True, punto=punto))
    elif modo == "Recta / plano tangente":
        pt, err = leer_punto(st.text_input(f"Punto ({nombres})", ",".join(["1"] * n), key="calc_tg_punto"), n)
        if err:
            st.error(err)
            return
        r = calcular("tangente", f, vs_, pt)
        mostrar(r)
        if not hay_error(r):
            L_ = r["datos"]["tangente"]
            if n == 1:
                figura(G.fig_funcion_1d(f, vs_[0], ventana_1d("tg", float(pt[0]) - 4, float(pt[0]) + 4), tangente=L_,
                                        puntos=[(pt[0], r["datos"]["f_p"], "p", G.ROJO)]))
            elif n == 2:
                figura(G.fig_superficie(f, vs_[0], vs_[1], ventana_2d("tg2", 2.0), plano=L_, punto=pt))
    else:
        pt, err = leer_punto(st.text_input(f"Punto ({nombres})", ",".join(["1"] * n), key="calc_dd_punto"), n)
        dv, err2 = leer_punto(st.text_input("Dirección v (no hace falta que sea unitaria)",
                                            ",".join(["1"] + ["0"] * (n - 1)), key="calc_dd_dir"), n, "La dirección")
        if err or err2:
            st.error(err or err2)
            return
        r = calcular("derivada_direccional", f, vs_, pt, dv)
        mostrar(r)
        if n == 2 and not hay_error(r):
            figura(G.fig_niveles(f, vs_[0], vs_[1], ventana_2d("dd"), gradiente=True, punto=pt))


def sec_limites(f, vs_):
    if n == 1:
        x = vs_[0]
        c1, c2 = st.columns([2, 3])
        with c1:
            t = st.text_input(f"{x} tiende a", "0", key="calc_lim_punto", help="Puedes escribir números, pi, oo (infinito) o -oo.")
        with c2:
            lado = st.radio("Desde", ["los dos lados", "la izquierda", "la derecha"], horizontal=True, key="calc_lim_lado")
        a, err = leer_numero(t, "El punto")
        if err:
            st.error(err)
            return
        d = {"los dos lados": "+-", "la izquierda": "-", "la derecha": "+"}[lado]
        r = calcular("limite_1d", f, x, a, d)
        mostrar(r)
        af = M._flt(a)
        if af is not None:
            v0 = (af - 4, af + 4)
        else:
            v0 = (0.0, 40.0) if a == sp.oo else (-40.0, 0.0)
        L_ = r["datos"].get("limite")
        finito = L_ is not None and M._clase(L_) == "fin"
        figura(G.fig_funcion_1d(
            f, x, ventana_1d("lim", round(v0[0], 2), round(v0[1], 2)),
            horizontales=[L_] if (finito and af is None) else [],
            puntos=[(a, L_, "límite", G.ROJO)] if (finito and af is not None) else []))
    else:
        pt, err = leer_punto(st.text_input(f"({', '.join(str(v) for v in vs_)}) tiende a", ",".join(["0"] * n), key="calc_limm_punto"), n)
        if err:
            st.error(err)
            return
        r = calcular("limite_multi", f, vs_, pt, timeout=40)
        mostrar(r)
        if n == 2 and not hay_error(r):
            p0, p1 = M._flt(pt[0]) or 0.0, M._flt(pt[1]) or 0.0
            figura(G.fig_niveles(f, vs_[0], vs_[1], ventana_2d("limm", 1.5, (p0, p1)), punto=pt))
            st.caption("Curvas de nivel cerca del punto (punto rojo). Si varias curvas de nivel **llegan al punto** con valores "
                       "distintos, el límite no existe.")


def sec_continuidad(f, vs_):
    if n == 1:
        x = vs_[0]
        r = calcular("continuidad_1d", f, x)
        mostrar(r)
        figura(G.fig_funcion_1d(f, x, ventana_1d("cont"), cortes=_discontinuidades(r, ("salto",)),
                                verticales=_discontinuidades(r, ("infinita",))))
    else:
        pt, err = leer_punto(st.text_input(f"Punto ({', '.join(str(v) for v in vs_)})", ",".join(["0"] * n), key="calc_cm_punto"), n)
        if err:
            st.error(err)
            return
        mostrar(calcular("continuidad_multi", f, vs_, pt, timeout=40))


def _leer_restriccion(latex_r, i_imag_):
    """Restricción escrita con el teclado -> (g que debe valer 0, mensaje)."""
    try:
        g = latex_a_sympy(latex_r, i_imaginaria=i_imag_)
    except ErrorLatex as e:
        return None, str(e)
    if isinstance(g, sp.Eq):
        return g.lhs - g.rhs, None
    if g in (sp.true, sp.false):
        return None, "Esa igualdad se simplificó por completo (siempre verdadera o falsa): no es una restricción útil."
    if isinstance(g, sp.Expr) and g.free_symbols:
        return g, "(Sin signo «=»: se tomó la expresión igual a 0.)"
    return None, "Escribe una igualdad con las variables, por ejemplo x² + y² = 1."


def sec_extremos(f, vs_):
    if n == 1:
        x = vs_[0]
        mostrar(calcular("monotonia_extremos", f, x))
        st.markdown("##### Máximo y mínimo **absolutos** en un intervalo cerrado")
        c1, c2 = st.columns(2)
        with c1:
            ta = st.text_input("a (extremo izquierdo)", "-2", key="calc_abs_a")
        with c2:
            tb = st.text_input("b (extremo derecho)", "2", key="calc_abs_b")
        a, e1 = leer_numero(ta, "a")
        b, e2 = leer_numero(tb, "b")
        if e1 or e2:
            st.error(e1 or e2)
            return
        r = calcular("extremos_absolutos", f, x, a, b)
        mostrar(r)
        if not hay_error(r) and r["datos"].get("maximo"):
            (xm, fm), (xn, fn) = r["datos"]["maximo"], r["datos"]["minimo"]
            figura(G.fig_funcion_1d(f, x, ventana_1d("abs", float(a) - 1, float(b) + 1),
                                    puntos=[(xm, fm, "máx abs", G.ROJO), (xn, fn, "mín abs", G.VERDE)]))
        return
    r = calcular("extremos_multi", f, vs_, timeout=40)
    mostrar(r)
    cand = [tuple(pt) for pt, _, _ in r["datos"].get("criticos", [])]
    if n == 2:
        figura(G.fig_niveles(f, vs_[0], vs_[1], ventana_2d("ext", 3.0), candidatos=cand))
        st.caption("Estrellas naranja: puntos críticos. Un mínimo/máximo se ve como curvas de nivel cerradas alrededor del punto; "
                   "una silla, como curvas que se cruzan.")
    st.divider()
    st.markdown("##### Extremos con restricción (multiplicadores de Lagrange)")
    st.caption("Escribe la restricción con el teclado, por ejemplo `x² + y² = 1`.")
    lr = teclado_matematico("calculo_restriccion", acoplado=acoplado, placeholder="g(x, y) = c")
    if not lr:
        return
    g1, msg = _leer_restriccion(lr, i_imag)
    if g1 is None:
        st.error(msg)
        return
    if msg:
        st.caption(msg)
    gs = [g1]
    if st.checkbox("Agregar una segunda restricción", key="calc_lag_2"):
        lr2 = teclado_matematico("calculo_restriccion2", acoplado=acoplado, placeholder="segunda restricción")
        if lr2:
            g2, msg2 = _leer_restriccion(lr2, i_imag)
            if g2 is None:
                st.error(msg2)
                return
            gs.append(g2)
    extra = set().union(*[g.free_symbols for g in gs]) - set(vs_)
    if extra:
        st.error("La restricción usa variables que no están en la función: " + ", ".join(str(s_) for s_ in extra))
        return
    rl = calcular("lagrange", f, vs_, gs, timeout=40)
    mostrar(rl)
    if n == 2 and len(gs) == 1 and not hay_error(rl):
        cl = [tuple(pt) for pt, _ in rl["datos"].get("candidatos", [])]
        figura(G.fig_niveles(f, vs_[0], vs_[1], ventana_2d("lag", 3.0), restriccion=gs[0], candidatos=cl))
        st.caption("Rojo: la restricción. Estrellas: candidatos. Los extremos están donde una curva de nivel **toca tangente** a la restricción.")


def _limites_texto(clave, nombre_var, defecto_a, defecto_b):
    c1, c2 = st.columns(2)
    with c1:
        ta = st.text_input(f"{nombre_var}: desde", defecto_a, key=f"{clave}_a")
    with c2:
        tb = st.text_input(f"{nombre_var}: hasta", defecto_b, key=f"{clave}_b")
    return ta, tb


def sec_integrales(f, vs_):
    if n == 1:
        x = vs_[0]
        modo = st.radio("Tipo", ["Definida (o impropia)", "Indefinida (primitiva)"], horizontal=True, key="calc_int_modo")
        if modo.startswith("Indef"):
            mostrar(calcular("integral_indefinida", f, x))
            return
        ta, tb = _limites_texto("calc_int", str(x), "0", "1")
        a, e1 = leer_numero(ta, "Límite inferior")
        b, e2 = leer_numero(tb, "Límite superior")
        if e1 or e2:
            st.error(e1 or e2)
            return
        r = calcular("integral_definida", f, x, a, b, timeout=40)
        mostrar(r)
        fa, fb = M._flt(a), M._flt(b)
        if fa is not None and fb is not None:
            lo, hi = min(fa, fb), max(fa, fb)
            figura(G.fig_funcion_1d(f, x, ventana_1d("intd", round(lo - 1, 2), round(hi + 1, 2)), sombrear=(lo, hi)))
        else:
            fin = fa if fa is not None else fb if fb is not None else 0.0
            figura(G.fig_funcion_1d(f, x, ventana_1d("intd", round(fin - 6, 2), round(fin + 12, 2)),
                                    sombrear=(fin, fin + 12) if b == sp.oo else (fin - 12, fin) if a == -sp.oo else None))
    elif n in (2, 3):
        st.caption("Se integra **de adentro hacia afuera**. Los límites pueden depender de las variables de las integrales de afuera "
                   "(por ejemplo `0` a `x`). Escribe con `pi`, `sqrt()`, `^`, `*`.")
        ordenes = list(itertools.permutations(vs_))
        etiquetas = ["  ".join(f"d{v}" for v in o) for o in ordenes]
        et = st.selectbox("Orden de integración (de adentro hacia afuera)", etiquetas, key=f"calc_im_orden_{n}")
        orden = ordenes[etiquetas.index(et)]
        lims = []
        for i, v in enumerate(orden):
            rol = "interna" if i == 0 else ("externa" if i == n - 1 else "intermedia")
            ta, tb = _limites_texto(f"calc_im_{n}_{et}_{v}", f"{v} ({rol})", "0", "1")
            try:
                a, b = ascii_a_sympy(ta), ascii_a_sympy(tb)
            except ErrorLatex as e:
                st.error(f"Límites de {v}: {e}")
                return
            permitidas = set(orden[i + 1:])
            mal = (a.free_symbols | b.free_symbols) - permitidas
            if mal:
                st.error(f"Los límites de {v} solo pueden depender de variables de integrales **exteriores** "
                         f"({', '.join(map(str, orden[i + 1:])) or 'ninguna'}); aparece: {', '.join(map(str, mal))}.")
                return
            lims.append((v, a, b))
        mostrar(calcular("integral_multiple", f, lims, timeout=40))
    else:
        st.info("Las integrales múltiples de más de 3 variables no están disponibles en este módulo.")


def sec_series(f, vs_):
    nom = [v for v in vs_ if v.name == "n"]
    nv = st.selectbox("Variable índice (n)", vs_, index=vs_.index(nom[0]) if nom else 0, format_func=str,
                      key="calc_ser_var") if len(vs_) > 1 else vs_[0]
    modo = st.radio("Estudiar como", ["Sucesión aₙ", "Serie Σ aₙ", "Serie de potencias"], horizontal=True, key="calc_ser_modo")
    n0 = int(st.number_input("Primer valor de n", value=0 if modo == "Serie de potencias" else 1, step=1, key=f"calc_ser_n0_{modo}"))
    if modo.startswith("Suc"):
        r = calcular("sucesion", f, nv, n0)
        mostrar(r)
        if not hay_error(r):
            figura(G.fig_sucesion(r["datos"].get("valores", []), n0, r["datos"].get("limite")))
    elif modo.startswith("Serie Σ"):
        r = calcular("serie", f, nv, n0, timeout=40)
        mostrar(r)
        if not hay_error(r) and r["datos"].get("sumas"):
            figura(G.fig_sumas_parciales(r["datos"]["sumas"], r["datos"].get("suma")))
    else:
        otras = [v for v in vs_ if v != nv]
        if not otras:
            st.info("Una serie de potencias necesita la variable índice **n** y otra variable **x** (por ejemplo xⁿ/n).")
            return
        xv = otras[0] if len(otras) == 1 else st.selectbox("Variable de la serie (x)", otras, format_func=str, key="calc_ser_x")
        c, err = leer_numero(st.text_input("Centro de la serie", "0", key="calc_ser_c"), "El centro")
        if err:
            st.error(err)
            return
        mostrar(calcular("serie_potencias", f, nv, xv, c, n0, timeout=40))


def sec_taylor(f, vs_):
    if n == 1:
        x = vs_[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            tc = st.text_input("Centro a", "0", key="calc_tay_c")
        with c2:
            orden = st.slider("Orden", 1, 12, 4, key="calc_tay_o")
        with c3:
            te = st.text_input("Evaluar en x = (opcional)", "", key="calc_tay_e")
        a, err = leer_numero(tc, "El centro")
        if err:
            st.error(err)
            return
        xe = None
        if te.strip():
            xe, err = leer_numero(te, "x")
            if err:
                st.error(err)
                return
        r = calcular("taylor", f, x, a, orden, xe)
        mostrar(r)
        if not hay_error(r):
            figura(G.fig_taylor(f, x, a, r["datos"]["polinomios"]))
    elif n in (2, 3):
        c1, c2 = st.columns(2)
        with c1:
            t = st.text_input(f"Punto ({', '.join(str(v) for v in vs_)})", ",".join(["0"] * n), key="calc_taym_p")
        with c2:
            orden = st.slider("Orden", 1, 3, 2, key="calc_taym_o")
        pt, err = leer_punto(t, n)
        if err:
            st.error(err)
            return
        r = calcular("taylor_multi", f, vs_, pt, orden)
        mostrar(r)
        if n == 2 and not hay_error(r):
            figura(G.fig_superficie(f, vs_[0], vs_[1], ventana_2d("taym", 2.0), plano=r["datos"]["polinomio"], punto=pt))
            st.caption("Naranja: el polinomio de Taylor. Cerca del punto rojo se pega a la superficie.")
    else:
        st.info("Taylor está disponible para funciones de 1 a 3 variables.")


def _niveles_de_texto(txt):
    out = []
    for t in txt.split(","):
        if t.strip():
            v, err = leer_numero(t, "Nivel")
            if err:
                return None, err
            out.append(v)
    return out, None


def sec_niveles(f, vs_):
    if n == 1:
        figura(G.fig_funcion_1d(f, vs_[0], ventana_1d("niv1")))
        cs, err = _niveles_de_texto(st.text_input("Niveles c (separados por comas)", "0", key="calc_niv1"))
        if err:
            st.error(err)
            return
        mostrar(calcular("niveles", f, vs_, cs))
    elif n == 2:
        vent = ventana_2d("niv2")
        auto = G.niveles_automaticos(f, vs_[0], vs_[1], vent)
        txt = st.text_input("Niveles c (separados por comas; vacío = automático)", "", key="calc_niv2", help="Ejemplo: 1, 4, 9")
        cs, err = _niveles_de_texto(txt) if txt.strip() else ([], None)
        if err:
            st.error(err)
            return
        c1, c2 = st.columns(2)
        with c1:
            grad = st.checkbox("Mostrar el campo de gradiente", value=True, key="calc_niv2_g")
        with c2:
            usar_p = st.checkbox("Marcar un punto", key="calc_niv2_up")
        punto = None
        if usar_p:
            punto, err = leer_punto(st.text_input("Punto (x, y)", "1,1", key="calc_niv2_p"), 2)
            if err:
                st.error(err)
                return
        t1, t2, t3 = st.tabs(["Curvas de nivel", "Superficie 3D", "Ecuaciones de los niveles"])
        with t1:
            figura(G.fig_niveles(f, vs_[0], vs_[1], vent, niveles=[float(M._flt(c)) for c in cs] if cs else None,
                                 gradiente=grad, punto=punto))
            st.caption("Las flechas naranja son el gradiente: **perpendiculares** a las curvas de nivel y apuntan hacia donde f crece más.")
        with t2:
            figura(G.fig_superficie(f, vs_[0], vs_[1], vent, punto=punto))
        with t3:
            niv = cs if cs else [sp.nsimplify(round(v, 3)) for v in auto[:5]]
            mostrar(calcular("niveles", f, vs_, niv))
    elif n == 3:
        vent = ventana_2d("niv3")
        c1, c2 = st.columns(2)
        with c1:
            txt = st.text_input("Niveles c (separados por comas)", "1", key="calc_niv3")
        with c2:
            tz = st.text_input("Cortes en z = (separados por comas)", "-1, 0, 1", key="calc_niv3z")
        cs, err = _niveles_de_texto(txt)
        zs, err2 = _niveles_de_texto(tz)
        if err or err2:
            st.error(err or err2)
            return
        mostrar(calcular("niveles", f, vs_, cs))
        for c in cs[:3]:
            st.markdown(f"##### Cortes de la superficie $f={sp.latex(c)}$")
            figura(G.fig_cortes(f, tuple(vs_), float(M._flt(c)), [float(M._flt(z)) for z in zs[:6]], vent))
    else:
        st.info("Los conjuntos de nivel se dibujan para funciones de 1 a 3 variables.")


# ==============================================================================
# 3 · Otras entradas: relaciones y operaciones escritas directamente
# ==============================================================================
def sec_relacion(rel, vs_):
    mostrar(calcular("resolver_relacion", rel))
    if len(vs_) == 2:
        figura(G.fig_region(rel, vs_[0], vs_[1], ventana_2d("rel")))
    elif len(vs_) == 1 and isinstance(rel, sp.core.relational.Relational):
        figura(G.fig_funcion_1d(rel.lhs - rel.rhs, vs_[0], ventana_1d("rel1"),
                                titulo="g(x) = (lado izquierdo) − (lado derecho): el eje x marca g = 0"))


def seccion_operacion(obj_, tipo_):
    r = calcular("evaluar_operacion", obj_, timeout=40)
    mostrar(r)
    if hay_error(r):
        return
    try:
        if tipo_ == "limite" and isinstance(obj_, sp.Limit):
            f, x, a = obj_.args[0], obj_.args[1], obj_.args[2]
            af = M._flt(a)
            v0 = (af - 4, af + 4) if af is not None else ((0.0, 40.0) if a == sp.oo else (-40.0, 0.0))
            if f.free_symbols == {x}:
                figura(G.fig_funcion_1d(f, x, ventana_1d("op_lim", round(v0[0], 2), round(v0[1], 2))))
        elif tipo_ == "integral" and isinstance(obj_, sp.Integral) and len(obj_.limits) == 1 and len(obj_.limits[0]) == 3:
            x, a, b = obj_.limits[0]
            fa, fb = M._flt(a), M._flt(b)
            if fa is not None and fb is not None and obj_.function.free_symbols == {x}:
                lo, hi = min(fa, fb), max(fa, fb)
                figura(G.fig_funcion_1d(obj_.function, x, ventana_1d("op_int", round(lo - 1, 2), round(hi + 1, 2)), sombrear=(lo, hi)))
        elif tipo_ == "serie" and r["datos"].get("sumas"):
            figura(G.fig_sumas_parciales(r["datos"]["sumas"], r["datos"].get("suma")))
        elif tipo_ == "derivada" and isinstance(obj_, sp.Derivative) and len(obj_.expr.free_symbols) == 1 \
                and len(obj_.variable_count) == 1:
            x = obj_.variable_count[0][0]
            figura(G.fig_funcion_1d(obj_.expr, x, ventana_1d("op_der"),
                                    derivada=r["datos"].get("derivada") if obj_.variable_count[0][1] == 1 else None))
    except Exception:  # noqa: BLE001
        pass  # la gráfica es un extra: si falla, el resultado de arriba sigue siendo válido


# ==============================================================================
# 4 · Despacho según el tipo de entrada
# ==============================================================================
tipo = info["tipo"]
st.subheader("2 · Análisis")

if tipo == "constante" and isinstance(obj, sp.Expr):
    st.latex(sp.latex(obj) + (r"\approx " + sp.latex(sp.N(obj, 12)) if not (obj.is_Integer or obj.is_Float) else ""))
    st.info("Es un número. Para estudiar sucesiones o series escribe una expresión con la variable **n** "
            "(por ejemplo `1/n²`), o una función con **x** para analizarla.")
elif tipo == "relacion":
    sec_relacion(obj, vs)
elif tipo == "funcion":
    if n > 4:
        st.warning("Con más de 4 variables solo se ofrecen derivadas, gradiente y extremos; las gráficas no están disponibles.")
    opciones = ["📋 Resumen y dominio"] + (["📈 Análisis completo"] if n == 1 else []) + [
        "∂ Derivadas", "→ Límites", "🔗 Continuidad", "⛰️ Extremos", "∫ Integrales", "Σ Series y sucesiones",
        "🧮 Taylor", "🗺️ Niveles y gráficas"]
    sec = st.radio("¿Qué quieres estudiar?", opciones, horizontal=True, key=f"calc_sec_{n}")
    st.divider()
    if sec.startswith("📋"):
        sec_resumen(obj, vs)
    elif sec.startswith("📈"):
        sec_analisis_1d(obj, vs[0])
    elif sec.startswith("∂"):
        sec_derivadas(obj, vs)
    elif sec.startswith("→"):
        sec_limites(obj, vs)
    elif sec.startswith("🔗"):
        sec_continuidad(obj, vs)
    elif sec.startswith("⛰️"):
        sec_extremos(obj, vs)
    elif sec.startswith("∫"):
        sec_integrales(obj, vs)
    elif sec.startswith("Σ"):
        sec_series(obj, vs)
    elif sec.startswith("🧮"):
        sec_taylor(obj, vs)
    else:
        sec_niveles(obj, vs)
else:       # límite, integral, serie, suma, producto, derivada, gradiente, expresión compuesta
    seccion_operacion(obj, tipo)
