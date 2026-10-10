"""
teclado_matematico.py
=====================
Teclado matemático interactivo (estilo Photomath / GeoGebra) para Streamlit.

Contiene dos piezas:

1. LAYOUTS ......... definición (en Python) de las pestañas y teclas de cada módulo.
                     Hoy solo existe el layout "calculo"; agregar otro módulo es
                     agregar una entrada a LAYOUTS (ver sección 1).
2. COMPONENTE ...... `teclado_matematico(key, ...)`: campo de escritura matemática
                     (MathLive) + teclado propio. Devuelve el LaTeX escrito.
                     Usa Streamlit Custom Components v2 (requiere Streamlit >= 1.51).

El intérprete que convierte ese LaTeX en SymPy (sin eval) está en interprete_latex.py.

Uso mínimo
----------
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy

    latex = teclado_matematico("mi_campo")          # "" hasta que se pulse ↵
    if latex:
        expr = latex_a_sympy(latex)                 # -> sympy.Basic

Notas
-----
* El editor (MathLive) se descarga de un CDN la primera vez: hace falta internet.
  La versión está fijada en MATHLIVE_VERSION; cámbiala solo probando antes.
* Streamlit se importa de forma perezosa, así que los layouts se pueden probar con
  pytest sin tener Streamlit instalado.
"""
from __future__ import annotations

import re
from typing import Any

__all__ = [
    "teclado_matematico",
    "LAYOUTS",
    "MATHLIVE_VERSION",
    "latex_a_sympy",       # reexportados desde interprete_latex.py
    "ErrorLatex",
    "ErrorNoSoportado",
]

# ==============================================================================
# 0. CONFIGURACIÓN DEL EDITOR (MathLive)
# ==============================================================================
MATHLIVE_VERSION = "0.102.0"
_CDN = f"https://cdn.jsdelivr.net/npm/mathlive@{MATHLIVE_VERSION}"
# Se intentan en orden; si uno falla (CDN caído, bloqueo de red) se prueba el siguiente.
MATHLIVE_URLS = [
    f"{_CDN}/dist/mathlive.min.mjs",
    f"https://esm.run/mathlive@{MATHLIVE_VERSION}",
    "https://esm.run/mathlive",
]
MATHLIVE_FONTS = f"{_CDN}/dist/fonts"


# ==============================================================================
# 1. LAYOUTS (pestañas y teclas)
# ==============================================================================
# Cada tecla es un dict compacto que viaja como JSON hacia el navegador:
#   l  etiqueta (HTML de confianza: constantes de este archivo)
#   i  LaTeX que se inserta.  #@ = lo seleccionado / argumento previo,
#                             #? = casilla vacía,  #0 = selección o casilla
#   c  clases CSS (num, var, op, fn, sm, xs, abc)
#   s  columnas que ocupa (por defecto 1)
#   t  texto de ayuda (tooltip / lector de pantalla)
#   a  acción especial en lugar de insertar (por ahora solo "shift")
#   u  versión con Mayús activado: {"l": ..., "i": ...}
#   sp  separador vacío de ese ancho (no es una tecla)
# La columna de control (⌫ ← → ↵) la agrega el componente en todas las pestañas.

def _k(l, i=None, c="", s=1, t="", u=None, a=None) -> dict:
    d: dict[str, Any] = {"l": l}
    if i is not None:
        d["i"] = i
    if c:
        d["c"] = c
    if s != 1:
        d["s"] = s
    if t:
        d["t"] = t
    if u:
        d["u"] = u
    if a:
        d["a"] = a
    return d


def _num(d: str) -> dict:
    return _k(d, d, "num")


# Etiquetas dibujadas con HTML/CSS (el CSS está en _CSS)
_BOX = '<span class="mk-bx"></span>'
_BOXS = '<span class="mk-bx mk-bxs"></span>'
_FRAC = '<span class="mk-frac"><i></i><b></b><i></i></span>'
_SQRT = f'<span class="mk-rad">√{_BOX}</span>'
_NSQRT = f'<span class="mk-rad"><sup>{_BOXS}</sup>√{_BOX}</span>'
_CASES2 = '<span class="mk-cs"><b>{</b><span><i></i><i></i></span></span>'
_CASES3 = '<span class="mk-cs"><b>{</b><span><i></i><i></i><i></i></span></span>'
_INT = '<span class="mk-int">∫</span>'
_INTD = '<span class="mk-int">∫<span class="mk-lim"><sup>b</sup><sub>a</sub></span></span>'
_DDX = '<span class="mk-df"><i>d</i><b></b><i>dx</i></span>'
_PDX = '<span class="mk-df"><i>∂</i><b></b><i>∂x</i></span>'


def _sup(base: str, exp: str) -> str:
    return f"<i>{base}</i><sup>{exp}</sup>"


def _tab_123() -> dict:
    n = _num
    return {"id": "123", "label": "123", "cols": 6, "rows": [
        [_k("<i>x</i>", "x", "var", t="x"),
         _k("<i>y</i>", "y", "var", t="y"),
         _k("π", r"\pi", "fn", t="pi"),
         _k("<i>e</i>", r"\exponentialE", "var", t="número e"),
         _k(_sup("x", "2"), r"#@^{2}", "fn", t="elevar al cuadrado"),
         _k(_sup("x", "<i>n</i>"), r"#@^{#?}", "fn", t="elevar a la n")],
        [n("7"), n("8"), n("9"),
         _k(_FRAC, r"\frac{#@}{#?}", "op", t="división (fracción)"),
         _k(_SQRT, r"\sqrt{#0}", "fn", t="raíz cuadrada"),
         _k("|<i>x</i>|", r"\left|#0\right|", "fn", t="valor absoluto")],
        [n("4"), n("5"), n("6"),
         _k("×", r"\times", "op", t="multiplicación"),
         _k("(", "(", "fn", t="abrir paréntesis"),
         _k(")", ")", "fn", t="cerrar paréntesis")],
        [n("1"), n("2"), n("3"),
         _k("−", "-", "op", t="resta"),
         _k("&lt;", "<", "fn", t="menor que"),
         _k("&gt;", ">", "fn", t="mayor que")],
        [_k("0", "0", "num", s=2),
         _k(".", ".", "num", t="punto decimal"),
         _k("+", "+", "op", t="suma"),
         _k("=", "=", "fn", t="igual"),
         _k(_NSQRT, r"\sqrt[#?]{#0}", "fn", t="raíz n-ésima")],
    ]}


def _tab_fx() -> dict:
    return {"id": "fx", "label": "f(x)", "cols": 6, "rows": [
        [_k("{ }", r"\left\{#0\right\}", "fn", t="llaves"),
         _k("⌊<i>x</i>⌋", r"\left\lfloor#0\right\rfloor", "fn", t="parte entera (piso)"),
         _k("⌈<i>x</i>⌉", r"\left\lceil#0\right\rceil", "fn", t="techo"),
         _k("<i>n</i>!", "!", "fn", t="factorial"),
         _k("<i>i</i>", r"\imaginaryI", "var", t="unidad imaginaria"),
         _k("∞", r"\infty", "fn", t="infinito")],
        [_k("ln", r"\ln\left(#0\right)", "fn", t="logaritmo natural"),
         _k("log", r"\log\left(#0\right)", "fn", t="logaritmo base 10"),
         _k("log<sub><i>b</i></sub>", r"\log_{#?}\left(#0\right)", "fn", t="logaritmo en base b"),
         _k("log<sub>2</sub>", r"\log_{2}\left(#0\right)", "fn", t="logaritmo base 2"),
         _k("<i>e</i><sup><i>x</i></sup>", r"\exponentialE^{#?}", "fn", t="exponencial"),
         _k("10<sup><i>x</i></sup>", r"10^{#?}", "fn", t="10 elevado a x")],
        [_k(_CASES2, r"\begin{cases}#? & #?\\ #? & #?\end{cases}", "fn", t="función por trozos (2 casos)"),
         _k(_CASES3, r"\begin{cases}#? & #?\\ #? & #?\\ #? & #?\end{cases}", "fn", t="función por trozos (3 casos)"),
         _k("<i>x</i><sub><i>n</i></sub>", r"#@_{#?}", "fn", t="subíndice"),
         _k("Σ", r"\sum_{#?}^{#?}#?", "fn", t="sumatoria"),
         _k("Π", r"\prod_{#?}^{#?}#?", "fn", t="productoria"),
         _k("lím", r"\lim_{#?\to #?}#?", "fn", t="límite")],
        [_k(_INT, r"\int #?\,\mathrm{d}#?", "fn", t="integral indefinida"),
         _k(_INTD, r"\int_{#?}^{#?}#?\,\mathrm{d}#?", "fn", t="integral definida"),
         _k(_DDX, r"\frac{\mathrm{d}}{\mathrm{d}#?}#?", "fn", t="derivada"),
         _k(_PDX, r"\frac{\partial}{\partial #?}#?", "fn", t="derivada parcial"),
         _k("∇", r"\nabla", "fn", t="nabla / gradiente"),
         _k("<i>f</i>(<i>x</i>)", r"f\left(#?\right)", "fn", t="función f")],
        [_k("<sub>n</sub>C<sub>r</sub>", r"\binom{#?}{#?}", "fn", t="combinaciones"),
         _k("sgn", r"\operatorname{sgn}\left(#0\right)", "fn", t="signo"),
         _k("máx", r"\max\left(#?,#?\right)", "fn", t="máximo"),
         _k("mín", r"\min\left(#?,#?\right)", "fn", t="mínimo"),
         _k(",", ",", "fn", t="coma"),
         _k("…", r"\ldots", "fn", t="puntos suspensivos")],
    ]}


def _tab_trig() -> dict:
    def nombre_latex(n: str) -> str:
        # \sech y \csch no están en todas las versiones de MathLive: operatorname es seguro
        return rf"\operatorname{{{n}}}" if n in ("sech", "csch") else rf"\{n}"

    def fila(nombres, inversa, cls):
        out = []
        for n in nombres:
            lat = nombre_latex(n) + ("^{-1}" if inversa else "")
            lab = n + ("<sup>−1</sup>" if inversa else "")
            ayuda = ("inversa de " if inversa else "") + n
            out.append(_k(lab, lat + r"\left(#0\right)", cls, t=ayuda))
        return out

    trig = ["sin", "cos", "tan", "csc", "sec", "cot"]
    hip = ["sinh", "cosh", "tanh", "csch", "sech", "coth"]
    return {"id": "trig", "label": "sin cos tan", "cols": 6, "rows": [
        fila(trig, False, "fn"),
        fila(trig, True, "fn sm"),
        fila(hip, False, "fn sm"),
        fila(hip, True, "fn xs"),
        [_k("π", r"\pi", "fn", t="pi"),
         _k("θ", r"\theta", "fn", t="theta"),
         _k("φ", r"\varphi", "fn", t="phi"),
         _k("°", r"^{\circ}", "fn", t="grados"),
         _k("(", "(", "fn", t="abrir paréntesis"),
         _k(")", ")", "fn", t="cerrar paréntesis")],
    ]}


def _tab_abc() -> dict:
    def letra(c: str) -> dict:
        return _k(c, c, "abc", s=2, u={"l": c.upper(), "i": c.upper()})

    def griega(c, cmd, mayus_c=None, mayus_cmd=None) -> dict:
        u = {"l": mayus_c, "i": mayus_cmd} if mayus_c else None
        return _k(c, cmd, "abc", s=2, u=u, t=cmd.lstrip("\\"))

    fila_num = [_k(d, d, "abc", s=2) for d in "1234567890"]
    fila_q = [letra(c) for c in "qwertyuiop"]
    fila_a = [{"sp": 1}] + [letra(c) for c in "asdfghjkl"] + [{"sp": 1}]
    fila_z = ([_k("⇧", c="abc mk-shift", s=3, a="shift", t="Mayúsculas")]
              + [letra(c) for c in "zxcvbnm"]
              + [_k("<i>x</i><sub><i>n</i></sub>", r"#@_{#?}", "abc", s=3, t="subíndice")])
    fila_g = [
        griega("α", r"\alpha"), griega("β", r"\beta"),
        griega("γ", r"\gamma", "Γ", r"\Gamma"), griega("δ", r"\delta", "Δ", r"\Delta"),
        griega("θ", r"\theta", "Θ", r"\Theta"), griega("λ", r"\lambda", "Λ", r"\Lambda"),
        griega("μ", r"\mu"), griega("σ", r"\sigma", "Σ", r"\Sigma"),
        griega("φ", r"\varphi", "Φ", r"\Phi"), griega("ω", r"\omega", "Ω", r"\Omega"),
    ]
    return {"id": "abc", "label": "abc", "cols": 20,
            "rows": [fila_num, fila_q, fila_a, fila_z, fila_g]}


def _tab_simbolos() -> dict:
    def s(l, i, t=""):
        return _k(l, i, "fn", t=t)

    return {"id": "sim", "label": "#&*", "cols": 9, "rows": [
        [s("[", "[", "corchete que abre"), s("]", "]", "corchete que cierra"),
         s("{", r"\{", "llave que abre"), s("}", r"\}", "llave que cierra"),
         s("⟨", r"\langle", "ángulo que abre"), s("⟩", r"\rangle", "ángulo que cierra"),
         s("‖<i>x</i>‖", r"\left\Vert#0\right\Vert", "norma"),
         s("<i>f</i>′", r"^{\prime}", "prima (derivada)"),
         _k("∣", r"\mid", "fn", t="tal que  ( | )")],
        [s("∈", r"\in", "pertenece"), s("∉", r"\notin", "no pertenece"),
         s("⊂", r"\subset", "subconjunto propio"), s("⊆", r"\subseteq", "subconjunto"),
         s("⊃", r"\supset", "superconjunto propio"), s("⊇", r"\supseteq", "superconjunto"),
         s("∪", r"\cup", "unión"), s("∩", r"\cap", "intersección"),
         s("∖", r"\setminus", "diferencia de conjuntos")],
        [s("∅", r"\emptyset", "conjunto vacío"),
         s("ℝ", r"\mathbb{R}", "reales"), s("ℕ", r"\mathbb{N}", "naturales"),
         s("ℤ", r"\mathbb{Z}", "enteros"), s("ℚ", r"\mathbb{Q}", "racionales"),
         s("ℂ", r"\mathbb{C}", "complejos"), s("ℝ<sup><i>n</i></sup>", r"\mathbb{R}^{n}", "R a la n"),
         s("ℝ<sup>+</sup>", r"\mathbb{R}^{+}", "reales positivos"),
         s(":", ":", "dos puntos (también «tal que»)")],
        [s("≤", r"\leq", "menor o igual"), s("≥", r"\geq", "mayor o igual"),
         s("≠", r"\neq", "distinto"), s("≈", r"\approx", "aproximado"),
         s("≡", r"\equiv", "equivalente / congruente"), s("±", r"\pm", "más menos"),
         s("→", r"\to", "tiende a / función"), s("↦", r"\mapsto", "se asigna a"),
         s("∘", r"\circ", "composición de funciones")],
        [s("∧", r"\land", "y lógico"), s("∨", r"\lor", "o lógico"),
         s("¬", r"\lnot", "negación"), s("⇒", r"\Rightarrow", "implica"),
         s("⇔", r"\Leftrightarrow", "si y solo si"), s("∀", r"\forall", "para todo"),
         s("∃", r"\exists", "existe"), s("∄", r"\nexists", "no existe"),
         s("∴", r"\therefore", "por lo tanto")],
    ]}


def _layout_calculo() -> dict:
    return {"tabs": [_tab_123(), _tab_fx(), _tab_trig(), _tab_abc(), _tab_simbolos()]}


# Registro de layouts. Para otro módulo: LAYOUTS["matrices"] = {"tabs": [...]}
LAYOUTS: dict[str, dict] = {"calculo": _layout_calculo()}


# ==============================================================================
# 2. COMPONENTE (Streamlit Custom Components v2)
# ==============================================================================
_HTML = '<div class="mk-root" role="group" aria-label="Teclado matemático"></div>'

_CSS = r"""
.mk-root{
  --mk-fg: var(--st-text-color, #1f2937);
  --mk-bg: var(--st-background-color, var(--st-secondary-background-color, #ffffff));
  --mk-accent: var(--st-primary-color, #0284c7);
  --mk-key: color-mix(in srgb, var(--mk-fg) 8%, var(--mk-bg));
  --mk-key-num: color-mix(in srgb, var(--mk-fg) 2%, var(--mk-bg));
  --mk-key-hi: color-mix(in srgb, var(--mk-fg) 15%, var(--mk-bg));
  --mk-panel: color-mix(in srgb, var(--mk-fg) 5%, var(--mk-bg));
  --mk-line: color-mix(in srgb, var(--mk-fg) 20%, transparent);
  --mk-kh: clamp(40px, 11.5vw, 50px);
  --mk-cw: clamp(46px, 13vw, 60px);
  font-family: var(--st-font, system-ui, -apple-system, "Segoe UI", sans-serif);
  color: var(--mk-fg);
  width: 100%;
  box-sizing: border-box;
}
.mk-root *{ box-sizing: border-box; }
.mk-root [hidden]{ display: none !important; }

/* ---------- campo de escritura ---------- */
.mk-fieldwrap{ position: relative; }
.mk-mf{
  display: block; width: 100%; min-height: 3.4rem; padding: 8px 44px 8px 12px;
  font-size: 1.7rem; border-radius: 14px; border: 1.5px solid var(--mk-line);
  background: var(--mk-bg); color: var(--mk-fg);
  --caret-color: var(--mk-accent);
  --selection-background-color: color-mix(in srgb, var(--mk-accent) 30%, transparent);
  --selection-color: var(--mk-fg);
  --contains-highlight-background-color: color-mix(in srgb, var(--mk-accent) 14%, transparent);
  --placeholder-color: color-mix(in srgb, var(--mk-fg) 45%, transparent);
}
.mk-mf:focus-within{ outline: 2px solid var(--mk-accent); outline-offset: 0; border-color: transparent; }
.mk-mf::part(virtual-keyboard-toggle){ display: none; }
.mk-mf::part(menu-toggle){ display: none; }
.mk-clear{
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  width: 30px; height: 30px; border-radius: 50%; border: 0; cursor: pointer;
  background: var(--mk-key); color: var(--mk-fg); font-size: .85rem; line-height: 1;
}
.mk-status{ font-size: .85rem; opacity: .7; padding: 6px 2px; }
.mk-status.mk-err{ opacity: 1; color: #b91c1c; }

/* ---------- panel del teclado ---------- */
.mk-kb{
  margin-top: 10px; padding: 8px; border-radius: 18px;
  background: var(--mk-panel); border: 1px solid var(--mk-line);
  -webkit-user-select: none; user-select: none;
}
.mk-root:not(.mk-docked) .mk-kb{ max-width: 560px; }
.mk-tabs{
  display: flex; gap: 4px; padding: 3px; margin-bottom: 8px; border-radius: 13px;
  background: color-mix(in srgb, var(--mk-fg) 9%, var(--mk-bg));
}
.mk-tab{
  flex: 1 1 auto; min-width: 0; padding: 9px 8px; border: 0; border-radius: 10px; text-align: center;
  background: transparent; color: inherit; font: inherit; font-size: .84rem; font-weight: 700;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; opacity: .72;
  touch-action: manipulation; -webkit-tap-highlight-color: transparent;
}
.mk-tab[aria-selected="true"]{
  background: var(--mk-bg); color: var(--mk-accent); opacity: 1;
  box-shadow: 0 1px 4px rgba(0,0,0,.22);
}
.mk-hide{ flex: 0 0 38px; background: transparent; font-size: 1.1rem; border-radius: 10px; }
.mk-root:not(.mk-docked) .mk-hide{ display: none; }

.mk-body{ display: flex; gap: 6px; align-items: flex-start; }
.mk-grid{
  flex: 1 1 auto; min-width: 0; display: grid; gap: 6px;
  grid-template-columns: repeat(var(--cols, 6), minmax(0, 1fr));
  grid-auto-rows: var(--mk-kh);
}
.mk-ctrl{
  flex: 0 0 var(--mk-cw); display: grid; gap: 6px;
  grid-template-rows: repeat(5, var(--mk-kh));
}
.mk-sp{ pointer-events: none; }

.mk-key, .mk-ctl{
  display: flex; align-items: center; justify-content: center; min-width: 0; padding: 0;
  border: 0; border-radius: 12px; font: inherit; color: inherit; line-height: 1;
  cursor: pointer; touch-action: manipulation; -webkit-tap-highlight-color: transparent;
  transition: background .08s ease, transform .05s ease;
}
.mk-key{ background: var(--mk-key); font-size: 1.15rem; box-shadow: 0 1px 0 var(--mk-line); }
.mk-key:hover{ background: var(--mk-key-hi); }
.mk-key:active, .mk-ctl:active{ transform: scale(.95); }
.mk-key:active{ background: color-mix(in srgb, var(--mk-accent) 28%, var(--mk-key)); }
.mk-key:focus-visible, .mk-ctl:focus-visible, .mk-tab:focus-visible{ outline: 2px solid var(--mk-accent); outline-offset: 1px; }

.mk-key.num{ background: var(--mk-key-num); border: 1px solid var(--mk-line); font-size: 1.3rem; font-weight: 600; }
.mk-key.var{ font-family: "Times New Roman", "Cambria Math", serif; font-size: 1.4rem; }
.mk-key.op { font-size: 1.35rem; background: color-mix(in srgb, var(--mk-accent) 12%, var(--mk-key)); }
.mk-key.abc{ background: var(--mk-key-num); border: 1px solid var(--mk-line); font-size: 1.1rem; }
.mk-key.sm { font-size: .9rem; }
.mk-key.xs { font-size: .72rem; }
.mk-key.mk-on{ background: var(--mk-accent); color: #fff; }
.mk-lb{ display: inline-block; white-space: nowrap; line-height: 1; }
.mk-lb sup{ font-size: .7em; line-height: 0; vertical-align: super; }
.mk-lb sub{ font-size: .7em; line-height: 0; vertical-align: sub; }
.mk-lb i{ font-family: "Times New Roman", "Cambria Math", serif; }

.mk-ctl{ background: var(--mk-key); font-size: 1.2rem; }
.mk-ctl:hover{ background: var(--mk-key-hi); }
.mk-enter{ grid-row: span 2; background: var(--mk-accent); color: #fff; font-size: 1.5rem; font-weight: 700; }
.mk-enter:hover{ background: color-mix(in srgb, var(--mk-accent) 85%, #000); }

/* ---------- etiquetas dibujadas ---------- */
.mk-bx{ display: inline-block; width: .8em; height: .8em; border: 1.5px dashed currentColor; border-radius: 2px; opacity: .55; }
.mk-bxs{ width: .5em; height: .5em; }
.mk-rad{ display: inline-flex; align-items: flex-end; gap: 1px; font-size: 1.2em; }
.mk-rad .mk-bx{ border-top-style: solid; }
.mk-frac{ display: inline-flex; flex-direction: column; align-items: center; font-size: .85em; }
.mk-frac i{ display: block; width: .95em; height: .8em; border: 1.5px dashed currentColor; border-radius: 2px; opacity: .55; }
.mk-frac b{ display: block; width: 1.3em; height: 2px; background: currentColor; margin: 3px 0; }
.mk-cs{ display: inline-flex; align-items: center; gap: 1px; }
.mk-cs b{ font-size: 2.1rem; font-weight: 300; line-height: 1; }
.mk-cs span{ display: flex; flex-direction: column; gap: 3px; }
.mk-cs i{ display: block; width: .8em; height: .42em; border: 1.5px dashed currentColor; border-radius: 2px; opacity: .55; }
.mk-int{ font-size: 1.5rem; display: inline-flex; align-items: center; font-family: "Times New Roman", serif; }
.mk-lim{ display: inline-flex; flex-direction: column; font-size: .62em; line-height: 1.05; margin-left: 1px; }
.mk-lim sup, .mk-lim sub{ font-size: 1em; vertical-align: baseline; line-height: 1.1; }
.mk-df{ display: inline-flex; flex-direction: column; align-items: center; font-size: .78em; line-height: 1.1; }
.mk-df b{ display: block; width: 100%; height: 1.5px; background: currentColor; margin: 2px 0; }

/* ---------- modo acoplado (estilo móvil) ---------- */
.mk-docked .mk-kb{
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 1000000;
  margin: 0 auto; max-width: 760px; border-radius: 18px 18px 0 0;
  padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px));
  background: var(--mk-panel); box-shadow: 0 -8px 28px rgba(0,0,0,.28);
  transform: translateY(110%); transition: transform .22s ease; pointer-events: none;
}
.mk-docked.mk-open .mk-kb{ transform: none; pointer-events: auto; }
.mk-spacer{ height: 0; }
"""

_JS = r"""
const el = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };

// MathLive se carga una sola vez por página, aunque haya varios teclados.
function cargarMathLive(urls, fontsDir) {
  if (window.__mkMathLive) return window.__mkMathLive;
  const p = (async () => {
    let ultimo = null;
    for (const u of urls) {
      try {
        const mod = await import(/* @vite-ignore */ u);
        const ME = mod.MathfieldElement || customElements.get('math-field');
        try { if (ME && fontsDir) ME.fontsDirectory = fontsDir; if (ME) ME.soundsDirectory = null; } catch (_) {}
        await Promise.race([
          customElements.whenDefined('math-field'),
          new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 8000)),
        ]);
        return mod;
      } catch (e) { ultimo = e; }
    }
    throw ultimo || new Error('No se pudo cargar MathLive');
  })();
  window.__mkMathLive = p;
  p.catch(() => { if (window.__mkMathLive === p) window.__mkMathLive = null; });
  return p;
}

export default function (component) {
  const { parentElement: host, data, setStateValue } = component;
  const cfg = data || {};
  const root = host.querySelector('.mk-root');
  if (!root) return undefined;

  root.replaceChildren();
  root.classList.toggle('mk-docked', !!cfg.acoplado);
  root.classList.remove('mk-open');

  const tabs = (cfg.layout && cfg.layout.tabs) || [];
  const offs = [];
  const timers = new Set();
  let vivo = true, mf = null, shifted = false, repT = null, repI = null, deb = null;
  let activa = Math.min(host.__mkTab || 0, Math.max(tabs.length - 1, 0));
  let ultimoEnviado = host.__mkSent !== undefined ? host.__mkSent : (cfg.valor_inicial || '');

  const on = (t, ev, fn, o) => { t.addEventListener(ev, fn, o); offs.push(() => t.removeEventListener(ev, fn, o)); };
  const luego = (fn, ms) => { const t = setTimeout(() => { timers.delete(t); fn(); }, ms); timers.add(t); return t; };

  // ---------- estructura ----------
  const wrap = el('div', 'mk-fieldwrap');
  const status = el('div', 'mk-status');
  status.textContent = 'Cargando editor matemático…';
  const clearBtn = el('button', 'mk-clear');
  clearBtn.type = 'button'; clearBtn.textContent = '✕'; clearBtn.title = 'Borrar todo';
  clearBtn.setAttribute('aria-label', 'Borrar todo'); clearBtn.hidden = true;
  wrap.append(clearBtn);

  const kb = el('div', 'mk-kb');
  const tabsBar = el('div', 'mk-tabs');
  const body = el('div', 'mk-body');
  const grid = el('div', 'mk-grid');
  const ctrl = el('div', 'mk-ctrl');
  const spacer = el('div', 'mk-spacer');
  body.append(grid, ctrl);
  kb.append(tabsBar, body);
  root.append(wrap, status, kb, spacer);

  tabs.forEach((t, i) => {
    const b = el('button', 'mk-tab');
    b.type = 'button'; b.innerHTML = t.label; b.dataset.i = String(i); b.setAttribute('role', 'tab');
    tabsBar.append(b);
  });
  const hideBtn = el('button', 'mk-ctl mk-hide');
  hideBtn.type = 'button'; hideBtn.textContent = '⌄'; hideBtn.title = 'Ocultar teclado';
  hideBtn.setAttribute('aria-label', 'Ocultar teclado'); hideBtn._k = { a: 'cerrar' };
  tabsBar.append(hideBtn);

  [
    { a: 'borrar', l: '⌫', t: 'Borrar', rep: true },
    { a: 'izq', l: '←', t: 'Mover a la izquierda', rep: true },
    { a: 'der', l: '→', t: 'Mover a la derecha', rep: true },
    { a: 'enter', l: '↵', t: 'Aceptar', c: 'mk-enter' },
  ].forEach((k) => {
    const b = el('button', 'mk-ctl' + (k.c ? ' ' + k.c : ''));
    b.type = 'button'; b.textContent = k.l; b.title = k.t; b.setAttribute('aria-label', k.t); b._k = k;
    ctrl.append(b);
  });

  // ---------- acciones ----------
  function enviar() {
    if (!mf) return;
    const v = mf.value;
    if (v !== ultimoEnviado) { ultimoEnviado = v; host.__mkSent = v; setStateValue('latex', v); }
  }
  function abrir() {
    if (!cfg.acoplado) return;
    root.classList.add('mk-open');
    spacer.style.height = kb.offsetHeight + 'px';
    // el campo debe quedar visible POR ENCIMA del teclado (Streamlit hace scroll en un contenedor interno)
    luego(() => {
      try {
        const libre = window.innerHeight - kb.offsetHeight;
        const r = wrap.getBoundingClientRect();
        if (r.bottom > libre - 12 || r.top < 0) wrap.scrollIntoView({ block: 'center', behavior: 'auto' });
      } catch (_) {}
    }, 60);
  }
  function cerrar() {
    root.classList.remove('mk-open');
    spacer.style.height = '0px';
  }
  const acciones = {
    insertar: (latex) => { mf.insert(latex, { format: 'latex', focus: true, feedback: false, mode: 'math' }); },
    borrar: () => { mf.executeCommand('deleteBackward'); mf.focus(); },
    izq: () => { mf.executeCommand('moveToPreviousChar'); mf.focus(); },
    der: () => { mf.executeCommand('moveToNextChar'); mf.focus(); },
    enter: () => { enviar(); if (cfg.acoplado) cerrar(); },
  };

  function pintar() {
    tabsBar.querySelectorAll('.mk-tab').forEach((b, i) => b.setAttribute('aria-selected', i === activa ? 'true' : 'false'));
    const t = tabs[activa];
    if (!t) return;
    grid.style.setProperty('--cols', String(t.cols || 6));
    grid.replaceChildren();
    for (const fila of t.rows) {
      for (const k0 of fila) {
        if (k0.sp) { const s = el('div', 'mk-sp'); s.style.gridColumn = 'span ' + k0.sp; grid.append(s); continue; }
        const k = (shifted && k0.u) ? Object.assign({}, k0, k0.u) : k0;
        const b = el('button', 'mk-key' + (k.c ? ' ' + k.c : '') + (k.a === 'shift' && shifted ? ' mk-on' : ''));
        b.type = 'button'; b.innerHTML = '<span class="mk-lb">' + k.l + '</span>';
        if (k.t) { b.title = k.t; b.setAttribute('aria-label', k.t); }
        if (k.s) b.style.gridColumn = 'span ' + k.s;
        b._k = k;
        grid.append(b);
      }
    }
  }

  function ejecutar(b) {
    const k = b._k;
    if (!k) return;
    if (k.a === 'shift') { shifted = !shifted; pintar(); return; }
    if (k.a === 'cerrar') { cerrar(); return; }
    if (!mf) return;
    if (k.a) acciones[k.a]();
    else if (k.i !== undefined) acciones.insertar(k.i);
    if (shifted) { shifted = false; pintar(); }   // Mayús de un solo uso
  }
  function detener() { clearTimeout(repT); clearInterval(repI); repT = repI = null; }

  const bind = (cont) => {
    on(cont, 'pointerdown', (e) => {
      const b = e.target.closest('button.mk-key, button.mk-ctl');
      if (!b || (e.pointerType === 'mouse' && e.button !== 0)) return;
      e.preventDefault();                       // no le quitamos el foco al campo
      ejecutar(b);
      if (b._k && b._k.rep) { detener(); repT = setTimeout(() => { repI = setInterval(() => ejecutar(b), 65); }, 360); }
    });
    on(cont, 'click', (e) => {                  // activación con teclado físico (Tab + Enter/Espacio)
      const b = e.target.closest('button.mk-key, button.mk-ctl');
      if (b && e.detail === 0) ejecutar(b);
    });
  };
  [grid, ctrl, tabsBar].forEach(bind);
  const elegirTab = (b) => { activa = Number(b.dataset.i); host.__mkTab = activa; pintar(); };
  on(tabsBar, 'pointerdown', (e) => {
    const b = e.target.closest('.mk-tab');
    if (!b) return;
    e.preventDefault(); elegirTab(b);
  });
  on(tabsBar, 'click', (e) => { const b = e.target.closest('.mk-tab'); if (b && e.detail === 0) elegirTab(b); });
  on(root, 'mousedown', (e) => { if (e.target.closest('button')) e.preventDefault(); });
  on(window, 'pointerup', detener);
  on(window, 'pointercancel', detener);
  on(window, 'blur', detener);
  on(document, 'pointerdown', (e) => {
    if (!root.classList.contains('mk-open')) return;
    const dentro = e.composedPath().includes(host.host || host);
    if (!dentro) cerrar();
  });

  pintar();

  // ---------- campo de escritura (MathLive) ----------
  cargarMathLive(cfg.mathlive_urls || [], cfg.fonts_dir).then(() => {
    if (!vivo) return;
    mf = document.createElement('math-field');
    mf.className = 'mk-mf';
    mf.setAttribute('math-virtual-keyboard-policy', 'manual');   // el teclado de MathLive no se usa
    wrap.prepend(mf);
    try { mf.mathVirtualKeyboardPolicy = 'manual'; } catch (_) {}
    try { mf.smartMode = false; } catch (_) {}
    try { if (cfg.placeholder) mf.placeholder = cfg.placeholder; } catch (_) {}
    const inicial = host.__mkLast !== undefined ? host.__mkLast : (cfg.valor_inicial || '');
    if (inicial) { mf.value = inicial; clearBtn.hidden = false; }
    status.remove();

    if (!cfg.teclado_nativo) {                                    // que no salga el teclado del sistema
      mf.setAttribute('inputmode', 'none');
      const sink = () => {
        const ta = mf.shadowRoot && mf.shadowRoot.querySelector('textarea');
        if (ta) ta.setAttribute('inputmode', 'none');
      };
      on(mf, 'focusin', sink);
      luego(sink, 0); luego(sink, 400);
    }

    on(mf, 'input', () => {
      host.__mkLast = mf.value;
      clearBtn.hidden = !mf.value;
      if (cfg.en_vivo) { clearTimeout(deb); deb = luego(enviar, 550); }
    });
    on(mf, 'keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); e.stopPropagation(); acciones.enter(); }
    }, true);
    on(mf, 'focusin', abrir);
    on(mf, 'focusout', () => luego(enviar, 0));                   // confirmar al salir del campo
    on(clearBtn, 'pointerdown', (e) => {
      e.preventDefault(); mf.value = ''; clearBtn.hidden = true; host.__mkLast = ''; mf.focus();
      if (cfg.en_vivo) enviar();
    });
  }).catch(() => {
    if (!vivo) return;
    status.classList.add('mk-err');
    status.textContent = 'No se pudo cargar el editor matemático (MathLive). Revisa tu conexión a internet y recarga la página.';
  });

  return () => {
    vivo = false;
    try { if (mf) host.__mkLast = mf.value; } catch (_) {}
    detener();
    timers.forEach(clearTimeout);
    offs.forEach((f) => f());
    root.classList.remove('mk-open');
  };
}
"""


def _componente():
    """Registra el componente una sola vez y lo devuelve (Streamlit se importa aquí)."""
    import streamlit as st

    if not hasattr(st, "components") or not hasattr(st.components, "v2"):
        raise RuntimeError(
            "El teclado necesita Streamlit >= 1.51 (Custom Components v2). "
            "Actualiza con: pip install -U streamlit  y sube esa versión a requirements.txt."
        )
    return st.components.v2.component(
        "teclado_matematico",
        html=_HTML,
        css=_CSS,
        js=_JS,
        isolate_styles=True,
    )


def _latex_texto(txt: str) -> str:
    """Texto plano -> \\text{...} seguro para usar como placeholder de MathLive."""
    limpio = re.sub(r"([\\{}$&#_%^~])", r" ", txt)
    return rf"\text{{{limpio}}}"


def teclado_matematico(
    key: str,
    *,
    layout: str = "calculo",
    valor_inicial: str = "",
    placeholder: str = "Escribe una función…",
    acoplado: bool = False,
    en_vivo: bool = False,
    teclado_nativo: bool = False,
) -> str:
    """
    Muestra el campo de escritura matemática con su teclado y devuelve el LaTeX.

    key             identificador único del widget (igual que en cualquier widget).
    layout          nombre del layout de LAYOUTS ("calculo" por ahora).
    valor_inicial   LaTeX con el que arranca el campo.
    acoplado        True = el teclado se desliza desde el borde inferior al enfocar
                    el campo (estilo móvil); False = siempre visible bajo el campo.
    en_vivo         True = envía el valor mientras se escribe (cada ~0.5 s);
                    False = solo al pulsar ↵, al dar Enter o al salir del campo.
    teclado_nativo  True = permite que aparezca el teclado del sistema en móviles.

    Devuelve "" mientras no se haya confirmado nada.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"Layout desconocido: {layout!r}. Disponibles: {list(LAYOUTS)}")

    resultado = _componente()(
        key=key,
        data={
            "layout": LAYOUTS[layout],
            "mathlive_urls": MATHLIVE_URLS,
            "fonts_dir": MATHLIVE_FONTS,
            "valor_inicial": valor_inicial,
            "placeholder": _latex_texto(placeholder),
            "acoplado": bool(acoplado),
            "en_vivo": bool(en_vivo),
            "teclado_nativo": bool(teclado_nativo),
        },
        default={"latex": valor_inicial},
        on_latex_change=lambda: None,
    )
    return resultado.latex or ""


# ==============================================================================
# El intérprete LaTeX -> SymPy vive ahora en interprete_latex.py (aquí se reexporta por compatibilidad)
# ==============================================================================
from interprete_latex import ErrorLatex, ErrorNoSoportado, latex_a_sympy  # noqa: E402,F401
