"""
calculo_motor.py
================
Motor matemático del módulo de Cálculo (sin Streamlit, sin matplotlib).

Cada operación recibe objetos de SymPy (los que produce interprete_latex.py) y devuelve:

    {"bloques": [...], "datos": {...}}

  bloques  lista de piezas para mostrar, en orden:
             ("h", titulo)            encabezado
             ("md", texto)            texto en Markdown (admite $...$ para fórmulas)
             ("latex", formula)       fórmula en pantalla
             ("ok"|"aviso"|"error"|"info", texto)
             ("tabla", columnas, filas)   filas = listas de textos Markdown
  datos    información para las gráficas (expresiones, puntos, valores…)

Ejecución segura
----------------
SymPy puede tardar horas con ciertas expresiones. `ejecutar_seguro(nombre, *args)` corre la
operación en un proceso aparte con tiempo límite: si se pasa, lo mata y avisa, sin congelar la
app. Las operaciones están registradas en OPERACIONES.

Secciones: 0 utilidades · 1 funciones de una variable · 2 límites y continuidad ·
           3 derivadas y aproximaciones · 4 varias variables · 5 integrales ·
           6 sucesiones y series · 7 niveles, relaciones y operaciones · 8 ejecución segura
"""
from __future__ import annotations

import functools
import itertools
import math
import random

import sympy as sp
from sympy.calculus.singularities import singularities
from sympy.calculus.util import continuous_domain, function_range, periodicity

from interprete_latex import Gradiente, LimiteMulti

# ==============================================================================
# 0. UTILIDADES
# ==============================================================================
OPERACIONES: dict = {}
INF = sp.oo


class ErrorCalculo(Exception):
    """Problema esperable (mensaje en español, listo para mostrar)."""


def _op(f):
    """Registra la función como operación y convierte cualquier fallo en un bloque de error."""
    @functools.wraps(f)
    def envuelto(*a, **k):
        try:
            return f(*a, **k)
        except ErrorCalculo as e:
            return res([ER(str(e))])
        except RecursionError:
            return res([ER("La expresión es demasiado compleja para este análisis.")])
        except MemoryError:
            return res([ER("Se agotó la memoria disponible calculando esto. Prueba con una expresión más sencilla.")])
        except Exception as e:  # noqa: BLE001
            return res([ER(f"No pude completar este cálculo ({type(e).__name__}: {str(e)[:120]}). "
                           "Prueba con una expresión más sencilla.")])
    OPERACIONES[f.__name__] = envuelto
    return envuelto


def T(s): return ("md", s)
def L(s): return ("latex", s)
def H(s): return ("h", s)
def OK(s): return ("ok", s)
def AV(s): return ("aviso", s)
def ER(s): return ("error", s)
def IN(s): return ("info", s)
def TAB(cols, filas): return ("tabla", list(cols), [list(map(str, f)) for f in filas])
def res(bloques, **datos): return {"bloques": list(bloques), "datos": datos}


def lx(e) -> str:
    """LaTeX de un valor, con infinitos legibles."""
    if e == sp.oo:
        return r"+\infty"
    if e == -sp.oo:
        return r"-\infty"
    if e == sp.zoo:
        return r"\tilde{\infty}"
    return sp.latex(e)


def m(e) -> str:
    """Fórmula en línea para Markdown."""
    return f"${lx(e)}$"


def _vars(e) -> list:
    return sorted((s for s in e.free_symbols if isinstance(s, sp.Symbol)), key=lambda s: s.name)


def _clase(v) -> str:
    """'fin' | '+oo' | '-oo' | 'zoo' | 'osc' | 'nd' (no definido o no calculado)."""
    if v is None:
        return "nd"
    if v == sp.oo:
        return "+oo"
    if v == -sp.oo:
        return "-oo"
    if v == sp.zoo:
        return "zoo"
    if isinstance(v, sp.AccumBounds):
        return "osc"
    if v == sp.nan or v.has(sp.nan, sp.I):
        return "nd"
    try:
        if v.is_finite is False:
            return "nd"
    except Exception:  # noqa: BLE001
        pass
    return "fin"


def _flt(v):
    """float de un número real finito, o None."""
    try:
        f = float(sp.N(v, 20))
        return f if math.isfinite(f) else None
    except Exception:  # noqa: BLE001
        return None


def _igual(a, b, tol=1e-9) -> bool:
    try:
        if sp.simplify(a - b) == 0:
            return True
    except Exception:  # noqa: BLE001
        pass
    fa, fb = _flt(a), _flt(b)
    return fa is not None and fb is not None and abs(fa - fb) <= tol * (1 + abs(fa))


def _resolver_trozos(expr, x, a, signo):
    """Reemplaza cada Piecewise por el trozo que aplica justo a la derecha (signo=+1) o a la
    izquierda (-1) de a. (El limit de SymPy sobre Piecewise puede dar un valor incorrecto.)"""
    if a == sp.oo:
        punto = sp.Integer(10 ** 8)
    elif a == -sp.oo:
        punto = sp.Integer(-10 ** 8)
    else:
        punto = a + signo * sp.Rational(1, 10 ** 8)

    def rama(pw):
        for e, c in pw.args:
            try:
                if c.subs(x, punto) == sp.true:
                    return e
            except Exception:  # noqa: BLE001
                pass
        return pw

    return expr.replace(lambda e: isinstance(e, sp.Piecewise), rama)


def lim(expr, x, a, direccion="+-"):
    """Límite de SymPy o None si no pudo (o devolvió un Limit sin evaluar)."""
    if expr is None:                       # p. ej. un límite iterado cuyo límite interior no se pudo calcular
        return None
    if expr.has(sp.Piecewise):
        if direccion == "+-" and a not in (sp.oo, -sp.oo):
            izq, der = lim(expr, x, a, "-"), lim(expr, x, a, "+")
            if izq is None or der is None:
                return None
            return izq if izq == der else sp.zoo
        expr = _resolver_trozos(expr, x, a, -1 if direccion == "-" else 1)
        direccion = "+-" if a in (sp.oo, -sp.oo) else direccion
    try:
        r = sp.limit(expr, x, a, direccion)
    except Exception:  # noqa: BLE001
        return None
    if r.has(sp.Limit):
        return None
    return r


def _desc_lim(v) -> str:
    c = _clase(v)
    if c == "fin":
        return m(v)
    return {"+oo": "$+\\infty$ (crece sin cota)", "-oo": "$-\\infty$ (decrece sin cota)",
            "zoo": "infinito (sin signo definido)", "osc": "no existe (oscila)", "nd": "no pude calcularlo"}[c]


def _valor_en(expr, sub: dict):
    """Valor de expr sustituyendo TODAS las variables A LA VEZ (simultaneous=True).
    Importante: sustituir en secuencia daría 0 para xy/(x²+y²) en el origen (0·y/y² = 0), cuando en
    realidad es 0/0."""
    try:
        v = expr.subs(sub, simultaneous=True) if len(sub) > 1 else expr.subs(sub)
        return v
    except Exception:  # noqa: BLE001
        return None


def _num_str(v, cifras=10) -> str:
    f = _flt(v)
    if f is None:
        if v == sp.oo:
            return "+∞"
        if v == -sp.oo:
            return "−∞"
        return "no definido"
    return f"{f:.{cifras}g}"


def _signo(expr, x, v):
    """Signo (−1, 0, 1) de expr en x=v, o None si no es real/finito."""
    try:
        val = sp.N(expr.subs(x, sp.Float(v, 30) if getattr(v, "is_Rational", False) and not v.is_Integer else v), 25)
        if not val.is_real:
            return None
        f = float(val)
        if not math.isfinite(f):
            return None
        return 0 if abs(f) < 1e-12 else (1 if f > 0 else -1)
    except Exception:  # noqa: BLE001
        return None


def sol_reales(expr, x):
    """Ceros reales de expr: (lista ordenada, nota) con nota en {None, 'ventana', 'todos', 'no_resuelto'}."""
    try:
        s = sp.solveset(expr, x, sp.S.Reals)
    except Exception:  # noqa: BLE001
        s = None
    if s is not None and s == sp.S.EmptySet:
        return [], None
    if s == sp.S.Reals:
        return [], "todos"
    nota = None
    if isinstance(s, sp.FiniteSet):
        pts = list(s)
    else:
        try:
            s2 = sp.solveset(expr, x, sp.Interval(-2 * sp.pi, 2 * sp.pi))
        except Exception:  # noqa: BLE001
            s2 = None
        if isinstance(s2, sp.FiniteSet):
            pts, nota = list(s2), "ventana"
        else:
            return [], "no_resuelto"
    pts = [p for p in pts if p.is_real and _flt(p) is not None]
    pts.sort(key=lambda p: _flt(p))
    return pts, nota


def _intervalo_txt(a, b) -> str:
    return sp.latex(sp.Interval.open(a, b))


def _cortes_piecewise(expr, x) -> set:
    """Puntos donde cambia de trozo o saltan signo/parte entera."""
    pts = set()
    for nodo in sp.preorder_traversal(expr):
        conds = []
        if isinstance(nodo, sp.Piecewise):
            conds = [c for _, c in nodo.args]
        for c in conds:
            for rel in c.atoms(sp.core.relational.Relational):
                try:
                    sol = sp.solveset(rel.lhs - rel.rhs, x, sp.S.Reals)
                    if isinstance(sol, sp.FiniteSet):
                        pts |= set(sol)
                except Exception:  # noqa: BLE001
                    pass
        if isinstance(nodo, sp.sign):
            try:
                sol = sp.solveset(nodo.args[0], x, sp.S.Reals)
                if isinstance(sol, sp.FiniteSet):
                    pts |= set(sol)
            except Exception:  # noqa: BLE001
                pass
    return pts


# ==============================================================================
# 1. FUNCIONES: DOMINIO Y ANÁLISIS DE UNA VARIABLE
# ==============================================================================
def condiciones_dominio(expr) -> list[tuple]:
    """Condiciones para que la expresión exista en los reales: [(relación, explicación)]."""
    conds, vistos = [], set()

    def add(rel, txt):
        if rel in (sp.true,) or (hasattr(rel, "free_symbols") and not rel.free_symbols):
            return
        k = sp.srepr(rel)
        if k not in vistos:
            vistos.add(k)
            conds.append((rel, txt))

    for n in sp.preorder_traversal(expr):
        if isinstance(n, sp.Pow):
            b, e = n.as_base_exp()
            if b == sp.E or not b.free_symbols and not e.free_symbols:
                continue
            if e.is_Number and e < 0:
                add(sp.Ne(b, 0), "el denominador no puede ser cero")
            if e.is_Rational and not e.is_Integer and e.q % 2 == 0:
                add(sp.Gt(b, 0) if e < 0 else sp.Ge(b, 0), "la raíz de índice par necesita radicando no negativo")
            elif e.free_symbols and b.free_symbols:
                add(sp.Gt(b, 0), "una base variable elevada a una potencia variable exige base positiva")
        elif isinstance(n, sp.log):
            add(sp.Gt(n.args[0], 0), "el argumento del logaritmo debe ser positivo")
        elif isinstance(n, (sp.asin, sp.acos)):
            add(sp.Le(sp.Abs(n.args[0]), 1), "el arcoseno/arcocoseno exige un argumento entre −1 y 1")
        elif isinstance(n, (sp.tan, sp.sec)):
            add(sp.Ne(sp.cos(n.args[0]), 0), "la tangente/secante no existe donde el coseno vale 0")
        elif isinstance(n, (sp.cot, sp.csc)):
            add(sp.Ne(sp.sin(n.args[0]), 0), "la cotangente/cosecante no existe donde el seno vale 0")
        elif isinstance(n, sp.acosh):
            add(sp.Ge(n.args[0], 1), "el coseno hiperbólico inverso exige argumento ≥ 1")
        elif isinstance(n, sp.atanh):
            add(sp.Lt(sp.Abs(n.args[0]), 1), "la tangente hiperbólica inversa exige |argumento| < 1")
        elif isinstance(n, (sp.coth, sp.csch)):
            add(sp.Ne(n.args[0], 0), "la cotangente/cosecante hiperbólica no existe en 0")
        elif isinstance(n, sp.factorial):
            add(sp.Ge(n.args[0], 0), "el factorial exige un argumento no negativo")
    # una condición «≠ 0» sobra si ya hay «> 0» sobre la misma expresión (la implica)
    estrictas = {sp.srepr(r.lhs) for r, _ in conds if isinstance(r, sp.StrictGreaterThan) and r.rhs == 0}
    conds = [(r, t) for r, t in conds
             if not (isinstance(r, sp.Ne) and r.rhs == 0 and sp.srepr(r.lhs) in estrictas)]
    return conds


@_op
def dominio(expr, x=None):
    """Dominio natural (condiciones y, con una variable, el conjunto y el rango)."""
    vs = _vars(expr)
    b = [H("Condiciones para que la expresión exista (en los reales)")]
    conds = condiciones_dominio(expr)
    if expr.has(sp.Piecewise):
        b.append(IN("Es una función por trozos: cada trozo tiene su propia condición; el dominio es la unión de los "
                    "intervalos donde algún trozo aplica."))
    if conds:
        for rel, txt in conds:
            b.append(T(f"- ${sp.latex(rel)}$ — {txt}."))
    else:
        b.append(T("No hay restricciones (denominadores, raíces pares, logaritmos…): se puede evaluar en cualquier valor real."))
    datos = {"condiciones": [rel for rel, _ in conds]}
    if len(vs) == 1:
        x = vs[0]
        try:
            dom = continuous_domain(expr, x, sp.S.Reals)
            datos["dominio"] = dom
            b += [H("Dominio"), L(f"\\operatorname{{Dom}}(f)={sp.latex(dom)}")]
            if dom == sp.S.EmptySet:
                b.append(ER("La función no está definida para NINGÚN número real: revisa la expresión."))
        except Exception:  # noqa: BLE001
            b.append(IN("No pude expresar el dominio como conjunto; usa las condiciones de arriba."))
        try:
            rango = function_range(expr, x, datos.get("dominio", sp.S.Reals))
            if rango.has(sp.Intersection) or rango.has(sp.ImageSet):
                raise ValueError
            datos["rango"] = rango
            b += [H("Rango"), L(f"\\operatorname{{Rango}}(f)={sp.latex(rango)}")]
        except Exception:  # noqa: BLE001
            b.append(IN("No pude determinar el rango de forma exacta; mira la gráfica para estimarlo."))
    elif len(vs) >= 2:
        b.append(IN(f"Con {len(vs)} variables el dominio es una región de ℝ^{len(vs)}: es el conjunto de puntos que cumplen "
                    "TODAS las condiciones de arriba a la vez. En «Niveles y gráficas» puedes verlo dibujado (n = 2)."))
    return res(b, **datos)


@_op
def ceros_cortes(expr, x):
    """Ceros (cortes con el eje x) y ordenada al origen."""
    b = [H("Cortes con los ejes")]
    f0 = _valor_en(expr, {x: 0})
    if f0 is not None and _clase(f0) == "fin":
        b.append(T(f"**Corte con el eje y:** $f(0)={lx(f0)}$ → el punto $(0,\\,{lx(f0)})$."))
    else:
        b.append(T("**Corte con el eje y:** la función no está definida en $x=0$ (no corta al eje y)."))
    pts, nota = sol_reales(expr, x)
    if nota == "todos":
        b.append(IN("La función es idénticamente cero: toda la recta es un «cero»."))
    elif nota == "no_resuelto":
        b.append(AV("No pude resolver $f(x)=0$ de forma exacta. Mira la gráfica para ubicar los ceros aproximados."))
    elif not pts:
        b.append(T("**Ceros:** $f(x)=0$ no tiene solución real: la gráfica no corta al eje x."))
    else:
        etiqueta = " (solo los de la ventana $[-2\\pi,2\\pi]$; la función es periódica y hay más)" if nota == "ventana" else ""
        b.append(T(f"**Ceros** (donde $f(x)=0$){etiqueta}:"))
        b.append(L(r",\quad ".join(f"x={sp.latex(p)}" for p in pts)))
    return res(b, ceros=pts, f0=f0)


@_op
def simetria_periodo(expr, x):
    """Paridad (par/impar) y periodicidad."""
    b = [H("Simetría y periodicidad")]
    try:
        d_par = sp.simplify(expr.subs(x, -x) - expr)
        d_imp = sp.simplify(expr.subs(x, -x) + expr)
    except Exception:  # noqa: BLE001
        d_par = d_imp = None
    par = d_par == 0
    impar = d_imp == 0
    if par and impar:
        b.append(T("La función es **idénticamente cero** (par e impar a la vez)."))
    elif par:
        b.append(OK("**Función PAR:** $f(-x)=f(x)$. Su gráfica es simétrica respecto del eje y."))
    elif impar:
        b.append(OK("**Función IMPAR:** $f(-x)=-f(x)$. Su gráfica es simétrica respecto del origen."))
    elif d_par is None:
        b.append(IN("No pude comprobar la paridad."))
    else:
        b.append(T("**Sin simetría de paridad:** no es par ni impar."))
    b.append(IN("La paridad solo tiene sentido si el dominio es simétrico respecto de 0 (si $x$ está en el dominio, $-x$ también)."))
    try:
        per = periodicity(expr, x)
    except Exception:  # noqa: BLE001
        per = None
    if per is not None and per != 0:
        b.append(OK(f"**Periódica** con período $T={lx(per)}$: $f(x+T)=f(x)$."))
    else:
        b.append(T("**No periódica** (o no pude detectar un período)."))
    return res(b, par=par, impar=impar, periodo=per)


def _dom_1d(expr, x):
    try:
        return continuous_domain(expr, x, sp.S.Reals)
    except Exception:  # noqa: BLE001
        return sp.S.Reals


def _candidatos(expr, x, dom=None):
    """Puntos aislados donde la función podría fallar (huecos, polos, cortes de trozos)."""
    dom = dom if dom is not None else _dom_1d(expr, x)
    cand = set()
    try:
        comp = sp.Complement(sp.S.Reals, dom)
        for parte in (comp.args if isinstance(comp, sp.Union) else [comp]):
            if isinstance(parte, sp.FiniteSet):
                cand |= set(parte)
            elif isinstance(parte, sp.Interval):
                cand |= {parte.start, parte.end}
    except Exception:  # noqa: BLE001
        pass
    try:
        sing = singularities(expr, x)
        if isinstance(sing, sp.FiniteSet):          # los conjuntos infinitos NO se recorren (no terminaría)
            cand |= set(sing)
    except Exception:  # noqa: BLE001
        pass
    cand |= _cortes_piecewise(expr, x)
    cand = {c for c in cand if c.is_real and _flt(c) is not None}
    return sorted(cand, key=lambda c: _flt(c)), dom


def _familias(dom) -> list:
    """Conjuntos infinitos numerables fuera del dominio (p. ej. π/2 + kπ para la tangente)."""
    fams = []
    try:
        comp = sp.Complement(sp.S.Reals, dom)
        for p in (comp.args if isinstance(comp, sp.Union) else [comp]):
            if not isinstance(p, (sp.FiniteSet, sp.Interval)) and (isinstance(p, sp.ImageSet) or p.has(sp.ImageSet)):
                fams.append(p)
    except Exception:  # noqa: BLE001
        pass
    return fams


def _representantes(familia, n=2) -> list:
    """Primeros elementos de una familia infinita (sin iterar de más)."""
    out = []
    try:
        for e in itertools.islice(iter(familia), n):
            if e.is_real and _flt(e) is not None:
                out.append(e)
    except Exception:  # noqa: BLE001
        pass
    return out


def _lado_en_dominio(dom, a, signo) -> bool:
    try:
        return bool(dom.contains(a + signo * sp.Rational(1, 10 ** 6)))
    except Exception:  # noqa: BLE001
        return True


@_op
def asintotas(expr, x):
    """Asíntotas verticales, horizontales y oblicuas."""
    b = [H("Asíntotas")]
    cand, dom = _candidatos(expr, x)
    verticales, familias_v = [], []
    for a in cand:
        izq = lim(expr, x, a, "-") if _lado_en_dominio(dom, a, -1) else None
        der = lim(expr, x, a, "+") if _lado_en_dominio(dom, a, 1) else None
        if _clase(izq) in ("+oo", "-oo") or _clase(der) in ("+oo", "-oo"):
            verticales.append((a, izq, der))
    for fam in _familias(dom):
        for a in _representantes(fam, 1):
            izq, der = lim(expr, x, a, "-"), lim(expr, x, a, "+")
            if _clase(izq) in ("+oo", "-oo") or _clase(der) in ("+oo", "-oo"):
                familias_v.append((fam, a))
    if verticales or familias_v:
        b.append(T("**Verticales:**"))
        for a, izq, der in verticales:
            lados = []
            if _clase(izq) != "nd":
                lados.append(f"por la izquierda tiende a {_desc_lim(izq)}")
            if _clase(der) != "nd":
                lados.append(f"por la derecha tiende a {_desc_lim(der)}")
            b.append(T(f"- $x={lx(a)}$: " + "; ".join(lados) + "."))
        for fam, a in familias_v:
            b.append(T(f"- **Infinitas (periódicas):** en todos los puntos de ${sp.latex(fam)}$ (por ejemplo $x={lx(a)}$)."))
    else:
        b.append(T("**Verticales:** ninguna."))

    horiz, obl = [], []
    for nombre, destino in (("+∞", sp.oo), ("−∞", -sp.oo)):
        L0 = lim(expr, x, destino)
        if _clase(L0) == "fin":
            horiz.append((nombre, L0))
            continue
        if _clase(L0) in ("+oo", "-oo"):
            mm = lim(expr / x, x, destino)
            if _clase(mm) == "fin" and mm != 0:
                bb = lim(expr - mm * x, x, destino)
                if _clase(bb) == "fin":
                    obl.append((nombre, mm, bb))
    if horiz:
        b.append(T("**Horizontales:**"))
        for nombre, v in horiz:
            b.append(T(f"- Hacia {nombre}: $y={lx(v)}$."))
    else:
        b.append(T("**Horizontales:** ninguna (los límites en $\\pm\\infty$ no son finitos)."))
    if obl:
        b.append(T("**Oblicuas** $y=mx+b$:"))
        for nombre, mm, bb in obl:
            b.append(T(f"- Hacia {nombre}: $y={lx(mm)}\\,x{'+' if (_flt(bb) or 0) >= 0 else ''}{lx(bb)}$."))
    else:
        b.append(T("**Oblicuas:** ninguna."))
    return res(b, verticales=[a for a, _, _ in verticales] + [a for _, a in familias_v],
               horizontales=[v for _, v in horiz], oblicuas=[(mm, bb) for _, mm, bb in obl])


def _intervalos(puntos, dom=None):
    """Intervalos abiertos determinados por los puntos (incluyendo ±∞) y un punto de prueba en cada uno."""
    pts = sorted({p for p in puntos if _flt(p) is not None}, key=lambda p: _flt(p))
    ext = [-sp.oo] + pts + [sp.oo]
    out = []
    for a, bb in zip(ext[:-1], ext[1:]):
        if a == -sp.oo and bb == sp.oo:
            prueba = sp.Integer(0)
        elif a == -sp.oo:
            prueba = bb - 1
        elif bb == sp.oo:
            prueba = a + 1
        else:
            prueba = (a + bb) / 2
        out.append((a, bb, prueba))
    return out


@_op
def monotonia_extremos(expr, x):
    """Derivada, puntos críticos, intervalos de crecimiento y extremos locales."""
    b = [H("Primera derivada")]
    f1 = sp.diff(expr, x)
    try:
        f1s = sp.simplify(f1)
        f1 = f1s if sp.count_ops(f1s) <= sp.count_ops(f1) else f1
    except Exception:  # noqa: BLE001
        pass
    b.append(L(f"f'(x)={sp.latex(f1)}"))
    dom = _dom_1d(expr, x)
    crit, nota = sol_reales(f1, x)
    # puntos donde f' no existe pero f sí (picos, tangentes verticales)
    sing = []
    try:
        sing = [s for s in singularities(f1, x) if s.is_real and _flt(s) is not None and dom.contains(s) == True]  # noqa: E712
    except Exception:  # noqa: BLE001
        pass
    sing += [s for s in _cortes_piecewise(expr, x) if s.is_real and dom.contains(s) == True and s not in sing]  # noqa: E712
    crit = [c for c in crit if dom.contains(c) == True]  # noqa: E712
    puntos = sorted(set(crit) | set(sing), key=lambda p: _flt(p))
    if nota == "no_resuelto":
        b.append(AV("No pude resolver $f'(x)=0$ de forma exacta; los puntos críticos pueden estar incompletos."))
    if nota == "ventana":
        b.append(IN("Hay infinitos puntos críticos (función periódica): se muestran los de la ventana $[-2\\pi,2\\pi]$."))
    b.append(H("Puntos críticos"))
    if crit:
        b.append(T("Donde $f'(x)=0$:  " + ", ".join(f"$x={sp.latex(c)}$" for c in crit)))
    else:
        b.append(T("No hay puntos donde $f'(x)=0$."))
    if sing:
        b.append(T("Donde $f'$ no existe pero $f$ sí:  " + ", ".join(f"$x={sp.latex(c)}$" for c in sing)))

    rangos = _intervalos(puntos)
    # también cortar por huecos del dominio para que el signo tenga sentido
    filas = []
    for a, bb, prueba in rangos:
        s = _signo(f1, x, prueba)
        if s is None:
            continue
        txt = "creciente ↑" if s > 0 else "decreciente ↓" if s < 0 else "constante →"
        filas.append([f"${_intervalo_txt(a, bb)}$", f"${lx(sp.N(prueba, 4))}$", "+" if s > 0 else "−" if s < 0 else "0", txt])
    if filas:
        b += [H("Crecimiento y decrecimiento"), TAB(["Intervalo", "x de prueba", "signo de f′", "f es…"], filas)]

    f2 = sp.diff(f1, x)
    extremos = []
    for c in puntos:
        fc = _valor_en(expr, {x: c})
        if fc is None or _clase(fc) != "fin":
            continue
        tipo = None
        if c in crit:
            f2c = _valor_en(f2, {x: c})
            sg = None
            if f2c is not None and _clase(f2c) == "fin":
                sg = (_flt(f2c) or 0)
                sg = None if abs(sg) < 1e-12 else (1 if sg > 0 else -1)
            if sg is not None:
                tipo = "mínimo local" if sg > 0 else "máximo local"
        if tipo is None:
            vecinos = [p for p in puntos if p != c]
            d = min([abs(_flt(p) - _flt(c)) for p in vecinos] + [2.0]) / 2
            sl = _signo(f1, x, c - sp.Float(d, 15))
            sr = _signo(f1, x, c + sp.Float(d, 15))
            if sl is not None and sr is not None:
                tipo = ("máximo local" if (sl > 0 and sr < 0) else "mínimo local" if (sl < 0 and sr > 0)
                        else "ni máximo ni mínimo (f′ no cambia de signo)")
        if tipo:
            extremos.append((c, fc, tipo))
    if extremos:
        b += [H("Extremos locales"),
              TAB(["x", "f(x)", "tipo"], [[m(c), m(fc), t] for c, fc, t in extremos])]
        b.append(IN("Criterio de la segunda derivada ($f''(c)>0$: mínimo, $f''(c)<0$: máximo); si $f''(c)=0$ o $f'$ no existe, "
                    "se usa el cambio de signo de $f'$."))
    elif puntos:
        b.append(T("Ningún punto crítico es un extremo local."))
    return res(b, derivada=f1, criticos=puntos, extremos=[(c, fc, t) for c, fc, t in extremos])


@_op
def concavidad(expr, x):
    """Segunda derivada, concavidad y puntos de inflexión."""
    b = [H("Segunda derivada")]
    f2 = sp.diff(expr, x, 2)
    try:
        f2s = sp.simplify(f2)
        f2 = f2s if sp.count_ops(f2s) <= sp.count_ops(f2) else f2
    except Exception:  # noqa: BLE001
        pass
    b.append(L(f"f''(x)={sp.latex(f2)}"))
    dom = _dom_1d(expr, x)
    cand, nota = sol_reales(f2, x)
    cand = [c for c in cand if dom.contains(c) == True]  # noqa: E712
    if nota == "no_resuelto":
        b.append(AV("No pude resolver $f''(x)=0$ de forma exacta; la lista de inflexiones puede estar incompleta."))
    filas, signos = [], []
    for a, bb, prueba in _intervalos(cand):
        s = _signo(f2, x, prueba)
        if s is None:
            continue
        signos.append((a, bb, s))
        filas.append([f"${_intervalo_txt(a, bb)}$", "+" if s > 0 else "−" if s < 0 else "0",
                      "cóncava hacia arriba ∪" if s > 0 else "cóncava hacia abajo ∩" if s < 0 else "recta"])
    if filas:
        b += [H("Concavidad"), TAB(["Intervalo", "signo de f″", "forma"], filas)]
    infl = []
    for c in cand:
        fc = _valor_en(expr, {x: c})
        if fc is None or _clase(fc) != "fin":
            continue
        d = 0.5
        sl, sr = _signo(f2, x, c - sp.Float(d, 15)), _signo(f2, x, c + sp.Float(d, 15))
        if sl is not None and sr is not None and sl != sr and sl != 0 and sr != 0:
            infl.append((c, fc))
    if infl:
        b += [H("Puntos de inflexión"), TAB(["x", "f(x)"], [[m(c), m(fc)] for c, fc in infl])]
    else:
        b.append(T("**Puntos de inflexión:** ninguno (la concavidad no cambia)."))
    return res(b, segunda=f2, inflexion=infl)


@_op
def extremos_absolutos(expr, x, a, bb):
    """Máximo y mínimo ABSOLUTOS de f en [a, b] (método del intervalo cerrado)."""
    fa_, fb_ = _flt(a), _flt(bb)
    if fa_ is None or fb_ is None:
        raise ErrorCalculo("Los extremos del intervalo deben ser números reales finitos.")
    if fa_ >= fb_:
        raise ErrorCalculo("El extremo izquierdo debe ser menor que el derecho.")
    b = [H("Método del intervalo cerrado"),
         T(f"Si $f$ es **continua** en $[{lx(a)},{lx(bb)}]$, el teorema de **Weierstrass** garantiza que alcanza un máximo y un mínimo "
           "absolutos. Se buscan entre: los **extremos** del intervalo y los **puntos críticos** interiores.")]
    dom = _dom_1d(expr, x)
    cerrado = sp.Interval(a, bb)
    try:
        dentro = cerrado.is_subset(dom)
    except Exception:  # noqa: BLE001
        dentro = None
    cand_disc = [c for c in _candidatos(expr, x, dom)[0] if fa_ <= _flt(c) <= fb_]
    if dentro is False or cand_disc:
        b.append(AV("La función **no es continua (o no está definida) en todo el intervalo**: el teorema no aplica y los resultados "
                    "de abajo podrían no ser los extremos absolutos." + (
                        " Puntos problemáticos: " + ", ".join(f"$x={lx(c)}$" for c in cand_disc) + "." if cand_disc else "")))
    f1 = sp.diff(expr, x)
    crit, nota = sol_reales(f1, x)
    sing = [s_ for s_ in _cortes_piecewise(expr, x)]
    if nota == "ventana":                       # función periódica: buscar solo dentro del intervalo
        try:
            sol = sp.solveset(f1, x, sp.Interval(a, bb))
            crit = sorted(list(sol), key=lambda p: _flt(p)) if isinstance(sol, sp.FiniteSet) else crit
        except Exception:  # noqa: BLE001
            pass
    interiores = sorted({c for c in list(crit) + sing if _flt(c) is not None and fa_ < _flt(c) < fb_}, key=lambda p: _flt(p))
    b.append(H("Candidatos"))
    cands = [("extremo izquierdo", a)] + [("punto crítico", c) for c in interiores] + [("extremo derecho", bb)]
    filas, vals = [], []
    for et, c in cands:
        v = _valor_en(expr, {x: c})
        if v is None or _clase(v) != "fin":
            filas.append([f"${lx(c)}$", et, "no definida"])
            continue
        v = sp.simplify(v)
        filas.append([f"${lx(c)}$", et, m(v)])
        vals.append((c, v))
    b.append(TAB(["x", "tipo de candidato", "f(x)"], filas))
    if not vals:
        return res(b + [ER("f no está definida en ningún candidato.")])
    vals.sort(key=lambda t: _flt(t[1]))
    vmin, vmax = vals[0][1], vals[-1][1]
    donde_min = [c for c, v in vals if _igual(v, vmin)]
    donde_max = [c for c, v in vals if _igual(v, vmax)]
    b.append(H("Conclusión"))
    b.append(OK(f"**Máximo absoluto:** ${lx(vmax)}$ en " + ", ".join(f"$x={lx(c)}$" for c in donde_max) + "."))
    b.append(OK(f"**Mínimo absoluto:** ${lx(vmin)}$ en " + ", ".join(f"$x={lx(c)}$" for c in donde_min) + "."))
    if _igual(vmin, vmax):
        b.append(IN("El máximo y el mínimo coinciden: la función es constante en los candidatos."))
    return res(b, maximo=(donde_max[0], vmax), minimo=(donde_min[0], vmin), candidatos=vals)


# ==============================================================================
# 2. LÍMITES Y CONTINUIDAD
# ==============================================================================
def _forma_indeterminada(expr, x, a, d):
    """(nombre en LaTeX, N, D) de la forma indeterminada de la estructura superior, o None."""
    def li(e):
        return lim(e, x, a, d)

    try:
        if expr.is_Add:
            cl = [_clase(li(t)) for t in expr.args]
            if "+oo" in cl and "-oo" in cl:
                return r"\infty-\infty", None, None
        elif expr.is_Mul or (expr.is_Pow and expr.exp.is_Number and expr.exp < 0):
            n, den = sp.fraction(expr)
            if den != 1:
                ln, ld = li(n), li(den)
                cn, cd = _clase(ln), _clase(ld)
                if cn == "fin" and cd == "fin" and ln == 0 and ld == 0:
                    return r"\tfrac{0}{0}", n, den
                if cn in ("+oo", "-oo") and cd in ("+oo", "-oo"):
                    return r"\tfrac{\infty}{\infty}", n, den
            else:
                cl = [(_clase(li(f)), li(f)) for f in expr.args]
                tiene0 = any(c == "fin" and v == 0 for c, v in cl)
                tieneoo = any(c in ("+oo", "-oo") for c, _ in cl)
                if tiene0 and tieneoo:
                    return r"0\cdot\infty", None, None
        elif expr.is_Pow:
            lb, le = li(expr.base), li(expr.exp)
            cb, ce = _clase(lb), _clase(le)
            if cb == "fin" and lb == 1 and ce in ("+oo", "-oo"):
                return r"1^{\infty}", None, None
            if cb == "fin" and lb == 0 and ce == "fin" and le == 0:
                return r"0^{0}", None, None
            if cb in ("+oo", "-oo") and ce == "fin" and le == 0:
                return r"\infty^{0}", None, None
    except Exception:  # noqa: BLE001
        pass
    return None


def _tabla_aproximacion(expr, x, a, direccion):
    """Valores de f cerca de a (o grandes si a=±∞) para ver el límite con números."""
    if a in (sp.oo, -sp.oo):
        signo = 1 if a == sp.oo else -1
        xs = [signo * 10 ** k for k in (1, 2, 3, 6)]
        etiquetas = [("x", xs)]
    else:
        pasos = [sp.Rational(1, 10 ** k) for k in (1, 2, 3, 6)]
        etiquetas = []
        if direccion in ("-", "+-"):
            etiquetas.append(("x → a⁻", [a - p for p in pasos]))
        if direccion in ("+", "+-"):
            etiquetas.append(("x → a⁺", [a + p for p in pasos]))
    filas = []
    for nombre, xs in etiquetas:
        for xv in xs:
            val = _valor_en(expr, {x: sp.Float(xv, 40)})      # Float: nunca potencias exactas gigantes
            filas.append([nombre, _num_str(xv, 8), _num_str(sp.N(val, 20) if val is not None else None, 9)])
    return filas


@_op
def limite_1d(expr, x, a, direccion="+-"):
    """Límite de una variable con laterales, formas indeterminadas, L'Hôpital y tabla numérica."""
    inf = a in (sp.oo, -sp.oo)
    b = [H("Planteamiento"), L(sp.latex(sp.Limit(expr, x, a, "+-" if inf else direccion)))]
    d = "+-" if inf else direccion
    dato = {}
    if not inf:
        f_a = _valor_en(expr, {x: a})
        cfa = _clase(f_a)
        b.append(H("Paso 1 · Sustitución directa"))
        if cfa == "fin":
            b.append(T(f"Al sustituir $x={lx(a)}$ se obtiene $f({lx(a)})={lx(f_a)}$ (un valor finito)."
                       " Ojo: esto es el **valor** de la función; el límite se confirma abajo con los laterales."))
        else:
            forma = _forma_indeterminada(expr, x, a, d if d != "+-" else "+")
            if forma:
                b.append(AV(f"Al sustituir se obtiene una **forma indeterminada** ${forma[0]}$: no se puede concluir "
                            "sustituyendo; hay que simplificar, factorizar o usar L'Hôpital."))
            else:
                b.append(T("Al sustituir $x=a$ la expresión **no está definida** (división entre cero u otra operación "
                           "inválida). Hay que estudiar qué ocurre *cerca* de $a$."))
    else:
        forma = _forma_indeterminada(expr, x, a, "+-")
        b.append(H("Paso 1 · Comportamiento en el infinito"))
        if forma:
            b.append(AV(f"Al evaluar directamente aparece una **forma indeterminada** ${forma[0]}$."))
        else:
            b.append(T("Se estudia qué hace la función cuando $x$ crece (o decrece) sin cota."))

    b.append(H("Paso 2 · Límite" + ("" if inf else "s laterales")))
    if inf:
        Lv = lim(expr, x, a)
        b.append(T(f"$\\lim_{{x\\to {lx(a)}}} f(x)=$ {_desc_lim(Lv)}"))
        final, existe = Lv, _clase(Lv) in ("fin", "+oo", "-oo")
        izq = der = None
    else:
        izq = lim(expr, x, a, "-") if d in ("-", "+-") else None
        der = lim(expr, x, a, "+") if d in ("+", "+-") else None
        if d in ("-", "+-"):
            b.append(T(f"Por la **izquierda** ($x\\to {lx(a)}^-$): {_desc_lim(izq)}"))
        if d in ("+", "+-"):
            b.append(T(f"Por la **derecha** ($x\\to {lx(a)}^+$): {_desc_lim(der)}"))
        if d == "-":
            final, existe = izq, _clase(izq) in ("fin", "+oo", "-oo")
        elif d == "+":
            final, existe = der, _clase(der) in ("fin", "+oo", "-oo")
        else:
            ci, cd = _clase(izq), _clase(der)
            if ci == "fin" and cd == "fin" and _igual(izq, der):
                final, existe = izq, True
            elif ci == cd and ci in ("+oo", "-oo"):
                final, existe = izq, True
            else:
                final, existe = None, False

    b.append(H("Conclusión"))
    cf = _clase(final)
    if inf or d != "+-":
        etiqueta = "" if inf else (" por la derecha" if d == "+" else " por la izquierda")
        if cf == "fin":
            b.append(OK(f"El límite{etiqueta} **existe y vale** ${lx(final)}$."))
        elif cf in ("+oo", "-oo"):
            b.append(OK(f"El límite{etiqueta} es ${lx(final)}$: la función {'crece' if cf == '+oo' else 'decrece'} sin cota."))
        elif cf == "osc":
            b.append(AV("El límite **no existe**: la función oscila sin acercarse a ningún valor."))
        else:
            b.append(AV("No pude determinar este límite."))
    elif existe and _clase(final) == "fin":
        b.append(OK(f"Los dos laterales coinciden → el límite **existe y vale** ${lx(final)}$."))
    elif existe:
        b.append(OK(f"Los dos laterales tienden a ${lx(final)}$ → el límite es ${lx(final)}$ (la función diverge)."))
    elif _clase(izq) == "nd" or _clase(der) == "nd":
        b.append(AV("No pude calcular alguno de los laterales (o la función no está definida de un lado)."))
    else:
        b.append(AV("Los laterales son **distintos** → el límite bilateral **NO existe**."))
        if _clase(izq) == "fin" and _clase(der) == "fin":
            b.append(T(f"Hay un **salto** de tamaño ${lx(sp.simplify(der - izq))}$."))
        elif _clase(izq) in ("+oo", "-oo") and _clase(der) in ("+oo", "-oo"):
            b.append(T("Hay una **asíntota vertical** con signos opuestos a cada lado."))

    if not inf:
        forma = _forma_indeterminada(expr, x, a, "+")
        if forma and forma[1] is not None:
            n, den = forma[1], forma[2]
            Lh = lim(sp.diff(n, x) / sp.diff(den, x), x, a, d)
            b += [H("Regla de L'Hôpital"),
                  T(f"Como la forma es ${forma[0]}$, se puede derivar numerador y denominador por separado:"),
                  L(r"\lim \frac{N'(x)}{D'(x)}=\lim " + sp.latex(sp.diff(n, x) / sp.diff(den, x)) + "=" + lx(Lh if Lh is not None else sp.Symbol("?")))]
            if Lh is not None and final is not None and _clase(Lh) == "fin" and _clase(final) == "fin" and not _igual(Lh, final):
                b.append(AV("L'Hôpital no coincide con el valor anterior: revisa."))

    filas = _tabla_aproximacion(expr, x, a, d)
    if filas:
        b += [H("Comprobación numérica"), TAB(["acercamiento", "x", "f(x)"], filas)]
        # validar el resultado simbólico contra el numérico (red de seguridad)
        try:
            ult = [f for f in filas if f[1] != "no definido"]
            if ult and final is not None and _clase(final) == "fin":
                vals = [_flt(sp.Float(f[2])) for f in ult[-1:] if f[2] not in ("no definido", "+∞", "−∞")]
                lf = _flt(final)
                if vals and vals[0] is not None and lf is not None and abs(vals[0] - lf) > 1e-3 * (1 + abs(lf)):
                    b.append(AV("⚠️ El valor numérico más cercano no coincide con el resultado simbólico; "
                                "desconfía y revisa la expresión."))
        except Exception:  # noqa: BLE001
            pass
    return res(b, limite=final, izq=izq, der=der, existe=existe)


def _clasificar_discontinuidad(expr, x, a, dom):
    """(tipo, descripción en Markdown) para un punto aislado a."""
    fa = _valor_en(expr, {x: a})
    fa_ok = fa is not None and _clase(fa) == "fin"
    izq = lim(expr, x, a, "-") if _lado_en_dominio(dom, a, -1) else None
    der = lim(expr, x, a, "+") if _lado_en_dominio(dom, a, 1) else None
    ci, cd = _clase(izq), _clase(der)
    ref = (f"$f({lx(a)})={lx(fa)}$" if fa_ok else f"$f({lx(a)})$ no está definida")
    if ci == "nd" and cd == "nd":
        return "no pude clasificarla", f"No pude calcular los límites laterales en $x={lx(a)}$."
    if ci == "nd" or cd == "nd":
        lado, v = ("derecha", der) if ci == "nd" else ("izquierda", izq)
        if _clase(v) == "fin" and fa_ok and _igual(v, fa):
            return "continua en la frontera", (f"$x={lx(a)}$ es **frontera del dominio**: solo hay función de un lado y es "
                                                f"continua por la {lado} ({ref}, límite ${lx(v)}$).")
        return "frontera del dominio", f"$x={lx(a)}$ es frontera del dominio (solo hay función por la {lado}); {ref}, límite {_desc_lim(v)}."
    if ci == "fin" and cd == "fin":
        if _igual(izq, der):
            if fa_ok and _igual(fa, izq):
                return "continua", f"Es continua en $x={lx(a)}$ ({ref} = límite)."
            return "evitable", (f"**Discontinuidad evitable (removible)**: el límite existe y vale ${lx(izq)}$, pero {ref}. "
                                f"Se «repara» definiendo $f({lx(a)})={lx(izq)}$.")
        salto = sp.simplify(der - izq)
        return "salto", (f"**Discontinuidad de salto finito**: límite izquierdo ${lx(izq)}$, derecho ${lx(der)}$ "
                         f"(salto ${lx(salto)}$); {ref}.")
    if ci in ("+oo", "-oo") or cd in ("+oo", "-oo"):
        return "infinita", (f"**Discontinuidad infinita** (asíntota vertical $x={lx(a)}$): izquierda {_desc_lim(izq)}, "
                            f"derecha {_desc_lim(der)}.")
    if ci == "osc" or cd == "osc":
        return "esencial", f"**Discontinuidad esencial**: cerca de $x={lx(a)}$ la función oscila y no tiene límite."
    return "no pude clasificarla", f"No pude clasificar la discontinuidad en $x={lx(a)}$."


@_op
def continuidad_1d(expr, x):
    """Continuidad de una variable: dominio, discontinuidades clasificadas y teoremas útiles."""
    b = [H("Dónde está definida")]
    cand, dom = _candidatos(expr, x)
    b.append(L(f"\\operatorname{{Dom}}(f)={sp.latex(dom)}"))
    if dom == sp.S.EmptySet:
        return res(b + [ER("La función no está definida en ningún real.")])
    if expr.has(sp.floor, sp.ceiling):
        b.append(AV("Contiene parte entera (piso/techo): salta en cada punto donde su argumento es un entero, "
                    "así que hay (infinitas) discontinuidades de salto además de las listadas."))
    fams = _familias(dom)
    for fam in fams:
        for a in _representantes(fam, 1):
            tipo, desc = _clasificar_discontinuidad(expr, x, a, dom)
            b.append(T(f"**Discontinuidades periódicas:** la función no está definida en ningún punto de ${sp.latex(fam)}$. "
                       "Por ejemplo, " + desc))
    if not cand and not fams:
        b += [OK("**La función es continua en todo su dominio** (composición de funciones elementales continuas)."),
              T("Nota: «continua en su dominio» no significa continua en todo $\\mathbb{R}$ si el dominio tiene huecos.")]
        return res(b, discontinuidades=[], dominio=dom)
    if not cand:
        return res(b + [IN("Fuera de esas familias periódicas, la función es continua en su dominio.")],
                   discontinuidades=["periódicas"], dominio=dom)
    b.append(H("Puntos a revisar"))
    filas, malos, notas = [], [], []
    for a in cand:
        tipo, desc = _clasificar_discontinuidad(expr, x, a, dom)
        filas.append([f"${lx(a)}$", tipo])
        notas.append(desc)
        if tipo not in ("continua", "continua en la frontera"):
            malos.append((a, tipo))
    b.append(TAB(["x", "clasificación"], filas))
    for d_ in notas:
        b.append(T("- " + d_))
    if not malos:
        b.append(OK("Todos los puntos revisados resultan continuos."))
    else:
        b.append(T("**Conclusión:** la función es continua en su dominio salvo en "
                   + ", ".join(f"$x={lx(a)}$" for a, _ in malos) + "."))
    b.append(IN("Teorema del valor intermedio: si $f$ es continua en $[a,b]$ y $f(a)$, $f(b)$ tienen signos opuestos, "
                "existe al menos un cero en $(a,b)$. Úsalo solo en intervalos donde NO haya discontinuidades."))
    return res(b, discontinuidades=malos, dominio=dom)


# ==============================================================================
# 3. DERIVADAS Y APROXIMACIONES
# ==============================================================================
def _simplificar(e, limite_ops=150):
    try:
        if sp.count_ops(e) > limite_ops:
            return e
        s = sp.simplify(e)
        return s if sp.count_ops(s) <= sp.count_ops(e) else e
    except Exception:  # noqa: BLE001
        return e


def _en_punto(expr, vars_, punto):
    return _valor_en(expr, dict(zip(vars_, punto)))


def _vec(lista) -> str:
    return sp.latex(sp.Matrix(list(lista)))


def _no_derivable(expr, x=None):
    """Puntos (n=1) donde |·|, signo, piso… impiden derivar; o aviso genérico."""
    if not expr.has(sp.Abs, sp.sign, sp.floor, sp.ceiling, sp.Max, sp.Min, sp.Piecewise):
        return None
    pts = set()
    if x is not None:
        for nodo in sp.preorder_traversal(expr):
            if isinstance(nodo, (sp.Abs, sp.sign)):
                try:
                    sol = sp.solveset(nodo.args[0], x, sp.S.Reals)
                    if isinstance(sol, sp.FiniteSet):
                        pts |= set(sol)
                except Exception:  # noqa: BLE001
                    pass
        pts |= _cortes_piecewise(expr, x)
    return sorted(pts, key=lambda p: _flt(p) or 0)


@_op
def derivar(expr, variables, punto=None):
    """
    Derivada (ordinaria, de orden superior, parcial o mixta).
    variables = [(símbolo, veces), ...] en el orden de derivación; punto = {símbolo: valor} opcional.
    """
    vc = [(v, int(c)) for v, c in variables]
    orden = sum(c for _, c in vc)
    if orden < 1 or orden > 8:
        raise ErrorCalculo("El orden de derivación debe estar entre 1 y 8.")
    b = [H("Planteamiento"), L(sp.latex(sp.Derivative(expr, *vc)))]
    d = sp.diff(expr, *vc)
    d_s = _simplificar(d)
    b += [H("Resultado"), L(sp.latex(sp.Derivative(expr, *vc)) + "=" + sp.latex(d_s))]
    if len(vc) == 1 and orden == 1:
        b.append(IN("Interpretación geométrica: $f'(a)$ es la **pendiente de la recta tangente** a la gráfica en $x=a$; "
                    "interpretación como razón de cambio: cuánto cambia $f$ por cada unidad que crece $x$."))
    elif len(vc) > 1 or len(expr.free_symbols) > 1:
        b.append(IN("Una derivada parcial mide cómo cambia $f$ al mover SOLO esa variable, dejando las demás fijas."))
    if len(vc) > 1:
        try:
            inv = sp.diff(expr, *reversed(vc))
            if sp.simplify(inv - d) == 0:
                b.append(OK("Se verificó que el orden de derivación no importa en este caso (teorema de Clairaut–Schwarz)."))
        except Exception:  # noqa: BLE001
            pass
    nd = _no_derivable(expr, vc[0][0] if len(expr.free_symbols) == 1 else None)
    if nd is not None:
        if nd:
            b.append(AV("La función **no es derivable** en " + ", ".join(f"$x={lx(p)}$" for p in nd) +
                        " (pico, salto o cambio de trozo); allí la fórmula de arriba no vale."))
        else:
            b.append(AV("La expresión contiene valor absoluto, signo, parte entera, máx/mín o trozos: puede no ser derivable "
                        "en algunos puntos; la fórmula solo vale donde sí lo es."))
    valor = None
    if punto:
        b.append(H("Valor en el punto"))
        valor = _valor_en(d_s, punto)
        etiqueta = ",\\,".join(f"{sp.latex(k)}={sp.latex(v)}" for k, v in punto.items())
        if valor is None or _clase(valor) != "fin":
            b.append(AV(f"La derivada no está definida (o no es finita) en ${etiqueta}$."))
        else:
            b.append(L(f"\\left.{sp.latex(sp.Derivative(expr, *vc))}\\right|_{{{etiqueta}}}={lx(sp.nsimplify(valor) if valor.is_Float else valor)}"
                       + (f"\\approx {sp.latex(sp.N(valor, 8))}" if not valor.is_Integer and not valor.is_Float else "")))
            if orden == 1 and len(vc) == 1:       # comprobación numérica por diferencia central
                v0 = vc[0][0]
                h = sp.Float("1e-6", 30)
                try:
                    p_mas = {**punto, v0: punto[v0] + h}
                    p_menos = {**punto, v0: punto[v0] - h}
                    num = (expr.subs(p_mas) - expr.subs(p_menos)) / (2 * h)
                    nv, vv = _flt(num), _flt(valor)
                    if nv is not None and vv is not None:
                        if abs(nv - vv) <= 1e-4 * (1 + abs(vv)):
                            b.append(OK(f"Comprobación numérica (diferencia central): ≈ {nv:.8g} ✔"))
                        else:
                            b.append(AV(f"La comprobación numérica da ≈ {nv:.8g}, que no coincide: la función podría no ser derivable ahí."))
                except Exception:  # noqa: BLE001
                    pass
    return res(b, derivada=d_s, valor=valor)


@_op
def gradiente_hessiana(expr, vars_, punto=None):
    """Gradiente, Hessiana, Laplaciano y, en un punto, su clasificación."""
    n = len(vars_)
    b = [H("Gradiente")]
    grad = [_simplificar(sp.diff(expr, v)) for v in vars_]
    b += [L(r"\nabla f=" + _vec(grad)),
          IN("El gradiente apunta en la dirección de **máximo crecimiento** de $f$, y es perpendicular a las curvas/superficies de nivel.")]
    datos = {"gradiente": grad}
    hess = None
    if n <= 4:
        hess = sp.Matrix(n, n, lambda i, j: _simplificar(sp.diff(expr, vars_[i], vars_[j])))
        b += [H("Matriz Hessiana"), L("H_f=" + sp.latex(hess))]
        datos["hessiana"] = hess
        if all(sp.simplify(hess[i, j] - hess[j, i]) == 0 for i in range(n) for j in range(i + 1, n)):
            b.append(T("La Hessiana es **simétrica** (derivadas parciales mixtas iguales: Clairaut–Schwarz)."))
        lap = _simplificar(sum(hess[i, i] for i in range(n)))
        b += [H("Laplaciano"), L(r"\nabla^{2}f=\sum_i \frac{\partial^{2}f}{\partial x_i^{2}}=" + sp.latex(lap))]
        if lap == 0:
            b.append(OK("$\\nabla^{2}f=0$: la función es **armónica**."))
    else:
        b.append(IN("Con más de 4 variables se omite la Hessiana en este módulo."))
    if punto is not None:
        etiqueta = ",\\,".join(f"{sp.latex(v)}={sp.latex(p)}" for v, p in zip(vars_, punto))
        b.append(H(f"En el punto (${etiqueta}$)"))
        fp = _en_punto(expr, vars_, punto)
        gp = [_en_punto(g, vars_, punto) for g in grad]
        if fp is None or _clase(fp) != "fin" or any(g is None or _clase(g) != "fin" for g in gp):
            b.append(AV("La función o su gradiente no están definidos (o no son finitos) en ese punto."))
        else:
            norma = sp.sqrt(sum(g ** 2 for g in gp))
            b.append(L(r"\nabla f=" + _vec([sp.simplify(g) for g in gp]) + r",\quad \|\nabla f\|=" + sp.latex(sp.simplify(norma))))
            if norma == 0:
                b.append(T("El gradiente es el **vector cero**: es un **punto crítico** (candidato a máximo, mínimo o silla)."))
            else:
                b.append(T(f"Dirección de máximo crecimiento: $\\nabla f$; razón máxima de cambio $={m(sp.simplify(norma))}$."))
            datos["en_punto"] = {"f": fp, "grad": gp}
            if hess is not None:
                hp = hess.subs(dict(zip(vars_, punto)))
                if not hp.has(sp.zoo, sp.nan, sp.oo):
                    b.append(L("H_f(p)=" + sp.latex(sp.simplify(hp))))
                    b += _clasificar_hessiana(hp, n)
    return res(b, **datos)


def _clasificar_hessiana(hp, n) -> list:
    """Bloques con la clasificación de una Hessiana evaluada (valores propios + menores principales)."""
    import numpy as np
    out = []
    try:
        ev = np.linalg.eigvalsh(np.array(hp.evalf(), dtype=float))
    except Exception:  # noqa: BLE001
        return [IN("No pude calcular los valores propios de la Hessiana.")]
    tol = 1e-9 * max(1.0, float(np.max(np.abs(ev))))
    pos, neg, cero = int(np.sum(ev > tol)), int(np.sum(ev < -tol)), int(np.sum(np.abs(ev) <= tol))
    out.append(T("Valores propios de $H_f(p)$: " + ", ".join(f"${v:.6g}$" for v in ev)))
    if neg == 0 and cero == 0:
        out.append(OK("**Definida positiva** → el punto crítico (si lo es) es un **mínimo local estricto**."))
    elif pos == 0 and cero == 0:
        out.append(OK("**Definida negativa** → el punto crítico (si lo es) es un **máximo local estricto**."))
    elif pos > 0 and neg > 0:
        out.append(OK("**Indefinida** (valores propios de ambos signos) → el punto crítico (si lo es) es un **punto silla**."))
    else:
        out.append(AV("**Semidefinida** (algún valor propio es 0) → el criterio de la Hessiana **no es concluyente**; "
                      "hay que estudiar el comportamiento de $f$ cerca del punto."))
    if n == 2:
        D = sp.simplify(hp.det())
        out.append(T(f"Criterio del discriminante: $D=f_{{xx}}f_{{yy}}-f_{{xy}}^2={lx(D)}$ y $f_{{xx}}={lx(sp.simplify(hp[0, 0]))}$."))
    return out


@_op
def derivada_direccional(expr, vars_, punto, direccion):
    """Derivada direccional D_u f(p) con u = dirección normalizada."""
    n = len(vars_)
    if len(punto) != n or len(direccion) != n:
        raise ErrorCalculo(f"La función tiene {n} variable(s): el punto y la dirección deben tener {n} componentes.")
    v = sp.Matrix(direccion)
    nv = sp.sqrt(sum(c ** 2 for c in direccion))
    if nv == 0:
        raise ErrorCalculo("La dirección no puede ser el vector cero.")
    u = (v / nv).applyfunc(sp.simplify)
    b = [H("Dirección unitaria"), L(r"\mathbf{u}=\frac{\mathbf{v}}{\|\mathbf{v}\|}=" + sp.latex(u))]
    grad = [sp.diff(expr, w) for w in vars_]
    gp = [_en_punto(g, vars_, punto) for g in grad]
    if any(g is None or _clase(g) != "fin" for g in gp):
        raise ErrorCalculo("El gradiente no está definido (o no es finito) en ese punto: no hay derivada direccional.")
    gv = sp.Matrix([sp.simplify(g) for g in gp])
    b += [H("Gradiente en el punto"), L(r"\nabla f(p)=" + sp.latex(gv))]
    Du = sp.simplify(gv.dot(u))
    b += [H("Derivada direccional"), L(r"D_{\mathbf{u}}f(p)=\nabla f(p)\cdot\mathbf{u}=" + sp.latex(Du) + r"\approx " + sp.latex(sp.N(Du, 6)))]
    s = _flt(Du)
    if s is not None:
        b.append(T("**Interpretación:** " + ("al avanzar en esa dirección, $f$ **crece**." if s > 1e-12
                                              else "al avanzar en esa dirección, $f$ **decrece**." if s < -1e-12
                                              else "en esa dirección $f$ **no cambia** (a primer orden): es tangente a la curva de nivel.")))
    nm = sp.simplify(sp.sqrt(sum(g ** 2 for g in gv)))
    b += [H("Direcciones especiales"),
          T(f"- **Máximo crecimiento:** hacia $\\nabla f(p)$, con razón $\\|\\nabla f(p)\\|={m(nm)}$."),
          T(f"- **Máximo decrecimiento:** hacia $-\\nabla f(p)$, con razón $-{lx(nm)}$."),
          T("- **Cambio nulo:** direcciones perpendiculares a $\\nabla f(p)$ (tangentes a la curva de nivel).")]
    if _flt(nm) is not None and s is not None and abs(s) > _flt(nm) + 1e-9:
        b.append(ER("Error interno: |D_u f| no puede superar |∇f|. Revisa los datos."))
    return res(b, Du=Du, u=u)


@_op
def tangente(expr, vars_, punto):
    """Recta tangente (n=1), plano tangente (n=2) o hiperplano tangente, y linealización."""
    n = len(vars_)
    if len(punto) != n:
        raise ErrorCalculo(f"La función tiene {n} variable(s): el punto debe tener {n} componentes.")
    fp = _en_punto(expr, vars_, punto)
    grad = [sp.diff(expr, v) for v in vars_]
    gp = [_en_punto(g, vars_, punto) for g in grad]
    if fp is None or _clase(fp) != "fin" or any(g is None or _clase(g) != "fin" for g in gp):
        raise ErrorCalculo("La función o su derivada no están definidas (o no son finitas) en ese punto: no hay tangente.")
    fp, gp = sp.simplify(fp), [sp.simplify(g) for g in gp]
    lin = fp + sum(g * (v - p) for g, v, p in zip(gp, vars_, punto))
    lin = sp.expand(lin)
    nombre = {1: "Recta tangente", 2: "Plano tangente"}.get(n, "Hiperplano tangente")
    b = [H(nombre)]
    if n == 1:
        b += [T(f"Pendiente $f'({lx(punto[0])})={lx(gp[0])}$ y punto $({lx(punto[0])},\\,{lx(fp)})$:"),
              L(f"y={sp.latex(lin)}")]
        if gp[0] != 0:
            norm = sp.expand(fp - (vars_[0] - punto[0]) / gp[0])
            b += [H("Recta normal"), L(f"y={sp.latex(norm)}")]
        else:
            b.append(T("La tangente es **horizontal** (derivada 0); la normal es la recta vertical $x=" + lx(punto[0]) + "$."))
    elif n == 2:
        z = sp.Symbol("z")
        b += [T("$z=f(p)+f_x(p)(x-x_0)+f_y(p)(y-y_0)$:"), L("z=" + sp.latex(lin)),
              T(f"Vector normal al plano: $\\mathbf{{n}}=({lx(gp[0])},\\,{lx(gp[1])},\\,-1)$.")]
    else:
        b += [L(r"w=" + sp.latex(lin))]
    b += [H("Linealización"), T("Cerca de $p$, $f(x)\\approx L(x)$ (la tangente aproxima a la función). "
                                 "Comparación con la función real a una distancia pequeña:")]
    filas = []
    for dlt in (sp.Rational(1, 10), sp.Rational(1, 100), sp.Rational(1, 1000)):
        q = {v: p + dlt for v, p in zip(vars_, punto)}
        real = _valor_en(expr, {k: sp.Float(val, 30) for k, val in q.items()})
        aprox = lin.subs({k: sp.Float(val, 30) for k, val in q.items()})
        if real is not None and _flt(real) is not None:
            filas.append([lx(dlt) if False else f"${sp.latex(dlt)}$", _num_str(real, 10), _num_str(aprox, 10),
                          _num_str(abs(sp.N(real - aprox, 15)), 3)])
    if filas:
        b.append(TAB(["desplazamiento (en cada variable)", "f real", "L (tangente)", "error"], filas))
    return res(b, tangente=lin, f_p=fp, grad_p=gp)


@_op
def taylor(expr, x, a, orden, evaluar_en=None):
    """Polinomio de Taylor de f en x=a, residuo de Lagrange y tabla de errores."""
    if not (0 <= orden <= 15):
        raise ErrorCalculo("El orden del polinomio debe estar entre 0 y 15.")
    fa = _valor_en(expr, {x: a})
    if fa is None or _clase(fa) != "fin":
        raise ErrorCalculo("La función no está definida (o no es finita) en el punto de desarrollo.")
    try:
        serie = sp.series(expr, x, a, orden + 1)
    except Exception as e:  # noqa: BLE001
        raise ErrorCalculo("SymPy no pudo desarrollar esta función en serie alrededor de ese punto "
                           "(¿no es analítica ahí?).") from e
    P = serie.removeO()
    b = [H(f"Polinomio de Taylor de orden {orden} alrededor de $x={lx(a)}$"),
         L(r"f(x)\approx\sum_{k=0}^{" + str(orden) + r"}\frac{f^{(k)}(" + lx(a) + r")}{k!}(x-" + (lx(a) if a != 0 else "0") + ")^k"),
         L(f"P_{{{orden}}}(x)={sp.latex(sp.expand(P))}")]
    if a == 0:
        b.append(IN("Con centro en 0 se llama **serie (polinomio) de Maclaurin**."))
    terminos = []
    for k in range(0, orden + 1):
        dk = _valor_en(sp.diff(expr, x, k), {x: a}) if k else fa
        if dk is not None and _clase(dk) == "fin":
            terminos.append([str(k), f"${lx(sp.simplify(dk))}$", f"${lx(sp.simplify(dk / sp.factorial(k)))}$"])
    if terminos:
        b += [H("Coeficientes"), TAB(["k", f"f^(k)({lx(a)})", "coeficiente f^(k)/k!"], terminos)]
    b += [H("Residuo (forma de Lagrange)"),
          L(r"R_{" + str(orden) + r"}(x)=\frac{f^{(" + str(orden + 1) + r")}(\xi)}{" + str(orden + 1) + r"!}(x-" + (lx(a) if a != 0 else "0") + r")^{" + str(orden + 1) + r"},\quad \xi\ \text{entre}\ a\ \text{y}\ x"),
          T("El error $|f(x)-P_n(x)|$ está acotado por el máximo de $|f^{(n+1)}|$ entre $a$ y $x$, dividido entre $(n+1)!$, por $|x-a|^{n+1}$.")]
    datos = {"polinomio": sp.expand(P), "orden": orden, "centro": a}
    ordenes = sorted({k for k in (1, 2, 3, orden) if 1 <= k <= orden})
    try:
        datos["polinomios"] = [(k, sp.series(expr, x, a, k + 1).removeO()) for k in ordenes]
    except Exception:  # noqa: BLE001
        datos["polinomios"] = [(orden, P)]
    if evaluar_en is not None:
        filas = []
        fx = _valor_en(expr, {x: evaluar_en})
        for k in range(1, orden + 1):
            Pk = sp.series(expr, x, a, k + 1).removeO()
            err = abs(sp.N(fx - Pk.subs(x, evaluar_en), 15)) if fx is not None else None
            filas.append([str(k), _num_str(Pk.subs(x, evaluar_en), 10), _num_str(err, 4)])
        if fx is not None:
            b += [H(f"Aproximación de $f({lx(evaluar_en)})$"),
                  T(f"Valor real: ${lx(sp.N(fx, 12))}$"),
                  TAB(["orden k", f"P_k({lx(evaluar_en)})", "error |f − P_k|"], filas)]
            b.append(T("Fíjate cómo el error baja al subir el orden (si $x$ está dentro de la zona donde la serie converge)."))
    return res(b, **datos)


@_op
def taylor_multi(expr, vars_, punto, orden=2):
    """Polinomio de Taylor de varias variables hasta orden 1-3."""
    n = len(vars_)
    if not 1 <= orden <= 3:
        raise ErrorCalculo("En varias variables se admiten órdenes 1 a 3.")
    if len(punto) != n:
        raise ErrorCalculo(f"El punto debe tener {n} componentes.")
    fp = _en_punto(expr, vars_, punto)
    if fp is None or _clase(fp) != "fin":
        raise ErrorCalculo("La función no está definida (o no es finita) en el punto de desarrollo.")
    h = [v - p for v, p in zip(vars_, punto)]
    total = sp.Integer(0)
    for k in range(orden + 1):
        parte = sp.Integer(0)
        for combo in itertools.combinations_with_replacement(range(n), k):
            dv = sp.diff(expr, *[vars_[i] for i in combo]) if k else expr
            val = _en_punto(dv, vars_, punto)
            if val is None or _clase(val) != "fin":
                raise ErrorCalculo("Alguna derivada parcial no está definida en ese punto.")
            mult = math.factorial(k)
            for i in set(combo):
                mult //= math.factorial(combo.count(i))
            parte += mult * val * sp.Mul(*[h[i] for i in combo])
        total += parte / sp.factorial(k)
    P = sp.expand(total)
    b = [H(f"Polinomio de Taylor de orden {orden} (varias variables)"),
         L(r"f(\mathbf{x})\approx f(p)+\nabla f(p)\cdot\mathbf{h}" + (r"+\tfrac12\,\mathbf{h}^{T}H_f(p)\,\mathbf{h}" if orden >= 2 else "") + (r"+\cdots" if orden >= 3 else "") + r",\quad \mathbf{h}=\mathbf{x}-p"),
         L(f"P_{{{orden}}}={sp.latex(P)}")]
    filas = []
    for dlt in (sp.Rational(1, 10), sp.Rational(1, 100)):
        q = {v: sp.Float(p + dlt, 30) for v, p in zip(vars_, punto)}
        real = _valor_en(expr, q)
        if real is not None and _flt(real) is not None:
            filas.append([f"${sp.latex(dlt)}$", _num_str(real, 10), _num_str(P.subs(q), 10), _num_str(abs(sp.N(real - P.subs(q), 15)), 3)])
    if filas:
        b += [H("Comparación con la función"), TAB(["desplazamiento", "f real", "P", "error"], filas)]
    return res(b, polinomio=P, orden=orden)


# ==============================================================================
# 4. VARIAS VARIABLES: LÍMITES, CONTINUIDAD, EXTREMOS
# ==============================================================================
def _caminos(n):
    """Trayectorias de prueba: [(etiqueta LaTeX, función t -> offsets, lado)]."""
    out = []
    if n == 2:
        rayos = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1), (1, 2), (2, 1), (-1, 2), (-2, 1),
                 (1, -2), (2, -1), (-1, -2), (-2, -1), (1, 3), (3, 1), (1, -3), (3, -1)]
        curvas = [("y=x^{2}", lambda t: (t, t ** 2)), ("y=-x^{2}", lambda t: (t, -t ** 2)), ("y=2x^{2}", lambda t: (t, 2 * t ** 2)),
                  ("y=x^{3}", lambda t: (t, t ** 3)), ("x=y^{2}", lambda t: (t ** 2, t)), ("x=-y^{2}", lambda t: (-t ** 2, t)),
                  ("x=y^{3}", lambda t: (t ** 3, t)), ("y=x^{2}/2", lambda t: (t, t ** 2 / 2))]
    elif n == 3:
        rayos = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1), (1, 1, 1), (-1, -1, -1), (1, -1, 1),
                 (1, 1, -1), (-1, 1, 1), (1, 2, 3), (2, -1, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, -1, 0)]
        curvas = [("(t,\\,t^{2},\\,t^{3})", lambda t: (t, t ** 2, t ** 3)), ("(t^{2},\\,t,\\,t)", lambda t: (t ** 2, t, t)),
                  ("(t,\\,t,\\,t^{2})", lambda t: (t, t, t ** 2))]
    else:
        rayos = [tuple(1 if i == j else 0 for i in range(n)) for j in range(n)] + [tuple([1] * n), tuple([-1] * n)]
        curvas = []
    for d in rayos:
        et = "(" + ",\\,".join(str(c) + "t" if c not in (0, 1, -1) else ("t" if c == 1 else "-t" if c == -1 else "0") for c in d) + ")"
        out.append((f"\\text{{recta }}{et}", (lambda t, d=d: tuple(c * t for c in d)), "+"))
    for et, fn in curvas:
        out.append((f"\\text{{curva }}{et}", fn, "+-"))
    return out


def _muestreo_numerico(expr, vars_, punto, L0):
    """Máxima desviación |f - L| en puntos aleatorios a distancias 1e-3, 1e-5, 1e-7 (mpmath, 40 dígitos)."""
    import mpmath as mp
    mp.mp.dps = 40
    try:
        f = sp.lambdify(vars_, expr, "mpmath")
    except Exception:  # noqa: BLE001
        return None
    rng = random.Random(20240601)
    n = len(vars_)
    Lf = mp.mpf(str(sp.N(L0, 30)))
    out = {}
    for r0 in (1e-3, 1e-5, 1e-7):
        dmax, vistos = 0.0, 0
        for i in range(70):
            if i % 3 == 2 and n == 2:                       # trayectorias curvas y = k x^2 (parábolas)
                k = rng.uniform(-6, 6)
                pt = [punto[0] + r0, punto[1] + k * r0 ** 2]
            else:
                dv = [rng.gauss(0, 1) for _ in range(n)]
                nr = math.sqrt(sum(c * c for c in dv)) or 1.0
                pt = [p + r0 * c / nr for p, c in zip(punto, dv)]
            try:
                val = f(*[mp.mpf(str(sp.N(c, 30))) if not isinstance(c, float) else mp.mpf(c) for c in pt])
                if isinstance(val, mp.mpc):
                    continue
                dmax = max(dmax, float(abs(val - Lf)))
                vistos += 1
            except Exception:  # noqa: BLE001
                continue
        out[r0] = dmax if vistos else None
    return out


def _limite_multi_core(expr, vars_, punto):
    """(bloques, existe, valor) del límite en varias variables."""
    n = len(vars_)
    b = []
    p = list(punto)
    sin_trozos = not expr.has(sp.Piecewise, sp.floor, sp.ceiling, sp.sign)
    # x**y con base y exponente variables: SymPy evalúa 0**0 = 1, pero la función NO es continua ahí
    pot_variable = any(isinstance(q, sp.Pow) and q.base.free_symbols and q.exp.free_symbols
                       for q in sp.preorder_traversal(expr))
    b.append(H("Paso 1 · Sustitución directa"))
    fp = _en_punto(expr, vars_, p)
    if fp is not None and _clase(fp) == "fin" and sin_trozos and not pot_variable:
        b.append(OK(f"Al sustituir se obtiene el valor finito ${lx(fp)}$ y la expresión es una combinación de funciones "
                    "elementales continuas en ese punto → el límite **existe y vale " + f"${lx(fp)}$**."))
        return b, True, fp
    if fp is not None and _clase(fp) == "fin":
        b.append(IN(f"Al sustituir se obtiene ${lx(fp)}$, pero la función tiene trozos, parte entera, signo o potencias con base "
                    "y exponente variables, así que no basta sustituir: hay que revisar las trayectorias."))
    else:
        b.append(AV("Al sustituir **no se obtiene un número** (forma indeterminada o división entre cero). "
                    "Hay que estudiar las trayectorias."))

    b.append(H("Paso 2 · Límites a lo largo de trayectorias"))
    b.append(T("Si **dos trayectorias dan límites distintos**, el límite **NO existe** (eso sí es una demostración). "
               "Si todas dan lo mismo, solo es evidencia a favor."))
    t = sp.Symbol("t", real=True)
    tp = sp.Symbol("t", positive=True)
    filas, valores = [], []
    for etiqueta, fn, lado in _caminos(n):
        tt = tp if lado == "+" else t
        offs = fn(tt)
        g = expr.subs({v: pp + o for v, pp, o in zip(vars_, p, offs)}, simultaneous=True)
        if sp.count_ops(g) < 200:
            try:
                g = sp.simplify(g)
            except Exception:  # noqa: BLE001
                pass
        val = lim(g, tt, 0, lado)
        c = _clase(val)
        filas.append([f"${etiqueta}$", _desc_lim(val) if c != "fin" else m(val)])
        valores.append((etiqueta, val, c))
    b.append(TAB(["trayectoria", "límite a lo largo de ella"], filas))

    fin = [(e, v) for e, v, c in valores if c == "fin"]
    distintos = []
    for e, v in fin:
        if not any(_igual(v, w) for _, w in distintos):
            distintos.append((e, v))
    infinitos = [(e, v, c) for e, v, c in valores if c in ("+oo", "-oo", "zoo")]
    osc = [e for e, v, c in valores if c == "osc"]

    b.append(H("Paso 3 · Límites iterados" if n == 2 else "Paso 3 · Conclusión"))
    if n == 2:
        x_, y_ = vars_
        L1 = lim(lim(expr, y_, p[1]), x_, p[0])
        L2 = lim(lim(expr, x_, p[0]), y_, p[1])
        b.append(T(f"$\\lim_{{x\\to {lx(p[0])}}}\\lim_{{y\\to {lx(p[1])}}} f={_desc_lim(L1)[:80]}$  y  "
                   f"$\\lim_{{y\\to {lx(p[1])}}}\\lim_{{x\\to {lx(p[0])}}} f={_desc_lim(L2)[:80]}$"))
        if _clase(L1) == "fin" and _clase(L2) == "fin" and not _igual(L1, L2):
            b.append(AV("Los límites iterados son **distintos** → el límite doble **NO existe**."))
            return b, False, None
        b.append(IN("Si los iterados coinciden NO se concluye nada (el límite doble podría no existir); si el límite doble "
                    "existe, entonces los iterados (cuando existen) coinciden con él."))

    b.append(H("Conclusión"))
    if len(distintos) >= 2:
        (e1, v1), (e2, v2) = distintos[0], distintos[1]
        b.append(AV(f"Por la trayectoria ${e1}$ el límite es ${lx(v1)}$, pero por ${e2}$ es ${lx(v2)}$ → **el límite NO existe**."))
        return b, False, None
    if infinitos and fin:
        b.append(AV("Unas trayectorias dan un valor finito y otras divergen → **el límite NO existe**."))
        return b, False, None
    if osc:
        b.append(AV("Por alguna trayectoria el límite oscila y no existe → **el límite NO existe**."))
        return b, False, None
    if infinitos and not fin:
        signos = {c for _, _, c in infinitos}
        if len(signos) == 1 and len(infinitos) == len(valores):
            b.append(OK(f"Por todas las trayectorias la función tiende a ${'+' if '+oo' in signos else '-'}\\infty$: "
                        "el límite **diverge** (no existe como número real)."))
        else:
            b.append(AV("La función diverge por las trayectorias probadas pero no de forma uniforme: **el límite no existe**."))
        return b, False, None
    if not distintos:
        b.append(AV("No pude calcular los límites por trayectorias (expresión demasiado compleja)."))
        return b, None, None

    L0 = distintos[0][1]
    b.append(T(f"Todas las trayectorias probadas dan el mismo valor ${lx(L0)}$. Eso es **evidencia**, no demostración: "
               "falta descartar trayectorias que no probamos."))
    evidencia = True
    if n == 2:
        r = sp.Symbol("r", positive=True)
        th = sp.Symbol("theta", real=True)
        g = expr.subs({vars_[0]: p[0] + r * sp.cos(th), vars_[1]: p[1] + r * sp.sin(th)}, simultaneous=True)
        try:
            g = sp.simplify(g) if sp.count_ops(g) < 120 else g
        except Exception:  # noqa: BLE001
            pass
        Lp = lim(g, r, 0, "+")
        b.append(H("Coordenadas polares"))
        b.append(T("Se sustituye $x=x_0+r\\cos\\theta$, $y=y_0+r\\sin\\theta$ y se hace $r\\to0^+$:"))
        if Lp is not None and _clase(Lp) == "fin" and th not in Lp.free_symbols and _igual(Lp, L0):
            b.append(OK(f"El resultado en polares es ${lx(Lp)}$ **sin depender de $\\theta$**: refuerza que el límite vale ${lx(L0)}$."))
        elif Lp is not None and th in Lp.free_symbols:
            b.append(AV(f"En polares el resultado depende de $\\theta$ (${lx(sp.simplify(Lp))}$): **el límite NO existe**."))
            return b, False, None
        else:
            b.append(IN("No pude resolver el límite en polares de forma simbólica; se confía en el muestreo numérico."))
    mues = _muestreo_numerico(expr, vars_, p, L0)
    if mues:
        b.append(H("Muestreo numérico cerca del punto"))
        filas = [[f"{r0:g}", ("sin datos" if d is None else f"{d:.3g}")] for r0, d in mues.items()]
        b.append(TAB(["distancia al punto", "máx |f − L| en 70 puntos al azar"], filas))
        ds = [d for d in mues.values() if d is not None]
        if ds:
            tol = 1e-2 * (1 + abs(_flt(L0) or 0))
            if ds[-1] > tol and ds[-1] > 0.5 * ds[0]:
                b.append(AV("Las desviaciones **no se achican** al acercarse: probablemente **el límite NO existe** "
                            "(alguna trayectoria curva da otro valor)."))
                return b, False, None
            if len(ds) >= 2 and ds[-1] < ds[0] and ds[-1] < tol:
                b.append(OK("Las desviaciones se achican al acercarse al punto: consistente con que el límite existe."))
    b.append(OK(f"**Conclusión:** el límite **existe y vale ${lx(L0)}$** (evidencia sólida por trayectorias, polares y muestreo). "
                "Para una demostración formal usa el **teorema del sandwich** (acotar $|f-L|$ por algo que tienda a 0)."))
    return b, True, L0


@_op
def limite_multi(expr, vars_, punto):
    """Límite en varias variables (trayectorias, iterados, polares y muestreo numérico)."""
    n = len(vars_)
    if len(punto) != n:
        raise ErrorCalculo(f"La función tiene {n} variable(s): el punto debe tener {n} componentes.")
    pt = ",\\,".join(lx(c) for c in punto)
    b = [H("Planteamiento"), L(f"\\lim_{{({','.join(sp.latex(v) for v in vars_)})\\to({pt})}} {sp.latex(expr)}")]
    bl, existe, valor = _limite_multi_core(expr, vars_, punto)
    return res(b + bl, existe=existe, limite=valor)


@_op
def continuidad_multi(expr, vars_, punto):
    """Continuidad en un punto: f(p) definida, límite existente e igual a f(p)."""
    n = len(vars_)
    if len(punto) != n:
        raise ErrorCalculo(f"La función tiene {n} variable(s): el punto debe tener {n} componentes.")
    pt = ",\\,".join(lx(c) for c in punto)
    b = [H("Las tres condiciones de continuidad en $p$"),
         T("Una función es continua en $p$ si: **(1)** $f(p)$ existe, **(2)** $\\lim_{x\\to p}f(x)$ existe y **(3)** ambos coinciden.")]
    fp = _en_punto(expr, vars_, punto)
    cond1 = fp is not None and _clase(fp) == "fin"
    b.append(H("(1) ¿Existe $f(p)$?"))
    if cond1:
        b.append(OK(f"$f({pt})={lx(fp)}$"))
    else:
        b.append(AV(f"$f({pt})$ **no está definida** (el punto no está en el dominio)."))
    b.append(H("(2) ¿Existe el límite?"))
    bl, existe, valor = _limite_multi_core(expr, vars_, punto)
    b += bl
    b.append(H("(3) Conclusión"))
    if cond1 and existe and valor is not None and _igual(fp, valor):
        b.append(OK(f"**f es continua en $({pt})$**: $f(p)=\\lim f=" + lx(fp) + "$."))
        cont = True
    elif existe and valor is not None and not cond1:
        b.append(AV(f"**Discontinuidad evitable**: el límite existe (${lx(valor)}$) pero $f(p)$ no está definida. "
                    f"Se repara definiendo $f({pt})={lx(valor)}$."))
        cont = False
    elif existe and cond1 and valor is not None:
        b.append(AV(f"**Discontinuidad evitable**: $\\lim f={lx(valor)}$ pero $f(p)={lx(fp)}$. Se repara redefiniendo $f(p)$."))
        cont = False
    elif existe is False:
        b.append(AV("**f NO es continua en $p$**: el límite no existe (discontinuidad esencial)."))
        cont = False
    else:
        b.append(IN("No se pudo decidir con certeza."))
        cont = None
    return res(b, continua=cont)


def _soluciones_reales(sistema_eqs, incognitas):
    """Soluciones reales de un sistema como lista de dicts completos."""
    try:
        sols = sp.solve(sistema_eqs, incognitas, dict=True)
    except Exception:  # noqa: BLE001
        sols = []
    out, incompletas = [], 0
    for s in sols:
        if not all(v in s for v in incognitas):
            incompletas += 1
            continue
        if all(val.is_real is not False and not val.has(sp.I) for val in s.values()):
            out.append({k: sp.simplify(v) for k, v in s.items()})
    return out, incompletas


@_op
def extremos_multi(expr, vars_):
    """Puntos críticos de f(x1..xn) y su clasificación con la Hessiana."""
    n = len(vars_)
    grad = [sp.diff(expr, v) for v in vars_]
    b = [H("Paso 1 · Gradiente igual a cero"), L(r"\nabla f=" + _vec([_simplificar(g) for g in grad]) + r"=\mathbf{0}")]
    sols, incompletas = _soluciones_reales(grad, list(vars_))
    if incompletas:
        b.append(AV("El sistema tiene soluciones que forman una **familia** (curva o recta de puntos críticos); no se listan."))
    if not sols:
        b.append(T("No hay puntos críticos reales: **no hay máximos ni mínimos locales** en el interior del dominio "
                   "(solo podrían estar en la frontera, si la hay)."))
        return res(b, criticos=[])
    b.append(T(f"Hay **{len(sols)}** punto(s) crítico(s):"))
    hess = sp.Matrix(n, n, lambda i, j: sp.diff(expr, vars_[i], vars_[j]))
    b += [H("Paso 2 · Matriz Hessiana"), L("H_f=" + sp.latex(hess.applyfunc(sp.simplify)))]
    b.append(H("Paso 3 · Clasificación"))
    filas, crit = [], []
    import numpy as np
    for s in sols:
        pt = [s[v] for v in vars_]
        fp = _en_punto(expr, vars_, pt)
        hp = hess.subs(s)
        tipo = "no pude clasificarla"
        try:
            ev = np.linalg.eigvalsh(np.array(hp.evalf(), dtype=float))
            tol = 1e-9 * max(1.0, float(np.max(np.abs(ev))))
            pos, neg = int(np.sum(ev > tol)), int(np.sum(ev < -tol))
            if neg == 0 and pos == n:
                tipo = "**mínimo local**"
            elif pos == 0 and neg == n:
                tipo = "**máximo local**"
            elif pos > 0 and neg > 0:
                tipo = "**punto silla**"
            else:
                tipo = "no concluyente (Hessiana semidefinida)"
        except Exception:  # noqa: BLE001
            pass
        filas.append([f"$({','.join(sp.latex(c) for c in pt)})$", m(sp.simplify(fp)) if fp is not None else "—", tipo])
        crit.append((pt, fp, tipo.replace("*", "")))
    b.append(TAB(["punto crítico", "f(p)", "tipo"], filas))
    if n == 2:
        b.append(T("Para $n=2$: $D=f_{xx}f_{yy}-f_{xy}^2$. Si $D>0$ y $f_{xx}>0$: mínimo; $D>0$ y $f_{xx}<0$: máximo; $D<0$: silla; $D=0$: no concluye."))
    if not hess.free_symbols:
        b.append(IN("La Hessiana es **constante** (función cuadrática): la clasificación vale de forma **global**."))
    b.append(IN("Si la Hessiana es semidefinida, el criterio no decide: estudia $f$ a lo largo de varias trayectorias por ese punto."))
    return res(b, criticos=[(pt, fp, tp) for pt, fp, tp in crit])


@_op
def lagrange(expr, vars_, restricciones):
    """
    Extremos con restricciones de igualdad g_i(x)=0 (multiplicadores de Lagrange).
    restricciones = [g1, g2, ...] ya como expresiones que deben valer 0.
    """
    n, k = len(vars_), len(restricciones)
    if k < 1:
        raise ErrorCalculo("Escribe al menos una restricción.")
    if k >= n:
        raise ErrorCalculo(f"Hay {k} restricción(es) para {n} variable(s): con tantas restricciones el problema queda sin "
                           "grados de libertad (o sobredeterminado).")
    lams = sp.symbols(f"lambda_1:{k + 1}", real=True)
    b = [H("Planteamiento"),
         T("Se buscan los extremos de $f$ **sobre** la curva/superficie definida por las restricciones $g_i=0$."),
         L(r"\nabla f=" + "+".join(f"\\lambda_{{{i + 1}}}\\nabla g_{{{i + 1}}}" for i in range(k)) + r",\qquad "
           + r",\ ".join(f"g_{{{i + 1}}}={sp.latex(g)}=0" for i, g in enumerate(restricciones))),
         H("Sistema de ecuaciones")]
    eqs = []
    for v in vars_:
        eqs.append(sp.diff(expr, v) - sum(l * sp.diff(g, v) for l, g in zip(lams, restricciones)))
    eqs += list(restricciones)
    for e in eqs:
        b.append(L(sp.latex(sp.Eq(sp.simplify(e), 0))))
    sols, incompletas = _soluciones_reales(eqs, list(vars_) + list(lams))
    if incompletas:
        b.append(AV("Parte de las soluciones forma una familia (curva de candidatos) y no se lista."))
    if not sols:
        b.append(AV("No encontré soluciones reales del sistema: la restricción podría no tener puntos que cumplan las "
                    "condiciones, o el sistema es demasiado difícil para el método simbólico."))
        return res(b, candidatos=[])
    filas, cand = [], []
    for s in sols:
        pt = [s[v] for v in vars_]
        fp = _en_punto(expr, vars_, pt)
        gradg = [[_en_punto(sp.diff(g, v), vars_, pt) for v in vars_] for g in restricciones]
        regular = sp.Matrix(gradg).rank() == k
        filas.append([f"$({','.join(sp.latex(c) for c in pt)})$", ", ".join(m(sp.simplify(s[l])) for l in lams),
                      m(sp.simplify(fp)) if fp is not None else "—", "sí" if regular else "NO (∇g = 0)"])
        cand.append((pt, fp, regular))
    b += [H("Puntos candidatos"), TAB(["punto", "multiplicadores λ", "f(p)", "restricción regular"], filas)]
    vals = [(pt, fp) for pt, fp, _ in cand if fp is not None and _flt(fp) is not None]
    if len(vals) >= 1:
        vals.sort(key=lambda t: _flt(t[1]))
        mn, mx = vals[0], vals[-1]
        b.append(H("Conclusión"))
        if len(vals) == 1:
            b.append(T(f"Un único candidato, con $f={m(mn[1])}$."))
        elif _igual(mn[1], mx[1]):
            b.append(T(f"Todos los candidatos dan el mismo valor $f={m(mn[1])}$."))
        else:
            b.append(OK(f"**Valor máximo** entre los candidatos: ${lx(sp.simplify(mx[1]))}$ en $({','.join(sp.latex(c) for c in mx[0])})$."))
            b.append(OK(f"**Valor mínimo** entre los candidatos: ${lx(sp.simplify(mn[1]))}$ en $({','.join(sp.latex(c) for c in mn[0])})$."))
        b.append(IN("Si el conjunto restringido es **cerrado y acotado** (compacto, p. ej. una circunferencia o elipse), el máximo y "
                    "mínimo absolutos existen y son los mayor/menor de esta lista (teorema de Weierstrass). "
                    "Si no es acotado, un candidato puede no ser un extremo."))
    if n == 2 and k == 1:
        g = restricciones[0]
        b.append(H("Criterio de la Hessiana orlada (n=2, una restricción)"))
        x, y = vars_
        lam = lams[0]
        Lg = expr - lam * g
        Hb = sp.Matrix([[0, sp.diff(g, x), sp.diff(g, y)],
                        [sp.diff(g, x), sp.diff(Lg, x, 2), sp.diff(Lg, x, y)],
                        [sp.diff(g, y), sp.diff(Lg, x, y), sp.diff(Lg, y, 2)]])
        filas2 = []
        for s in sols:
            d = sp.simplify(Hb.det().subs(s))
            sg = _flt(d)
            tipo = "no concluyente" if sg is None or abs(sg) < 1e-12 else ("**máximo local** (det > 0)" if sg > 0 else "**mínimo local** (det < 0)")
            filas2.append([f"$({sp.latex(s[x])},\\,{sp.latex(s[y])})$", m(d), tipo])
        b.append(TAB(["punto", "det(Hessiana orlada)", "tipo"], filas2))
    return res(b, candidatos=[(pt, fp) for pt, fp, _ in cand])


# ==============================================================================
# 5. INTEGRALES
# ==============================================================================
def _mp_f(expr, var):
    import mpmath as mp
    mp.mp.dps = 25
    return sp.lambdify(var, expr, "mpmath")


@_op
def integral_indefinida(expr, x):
    """Primitiva ∫ f dx + C, con verificación por derivación."""
    b = [H("Planteamiento"), L(r"\int " + sp.latex(expr) + r"\,\mathrm{d}" + sp.latex(x))]
    F = sp.integrate(expr, x)
    if F.has(sp.Integral):
        b.append(AV("SymPy **no encontró una primitiva** en términos de funciones elementales. Esto puede ser verdad "
                    "(p. ej. $\\int e^{-x^2}dx$ no es elemental, aunque se expresa con la función error) o una limitación del "
                    "programa. Prueba con una sustitución o integración por partes a mano, o calcula la integral definida "
                    "numéricamente."))
        return res(b, primitiva=None)
    Fs = _simplificar(F)
    b += [H("Resultado"), L(r"\int " + sp.latex(expr) + r"\,\mathrm{d}" + sp.latex(x) + "=" + sp.latex(Fs) + "+C")]
    try:
        if sp.simplify(sp.diff(Fs, x) - expr) == 0:
            b.append(OK("**Verificación:** al derivar el resultado se recupera el integrando ✔"))
        else:
            ok_num = all(abs(_flt(sp.N((sp.diff(Fs, x) - expr).subs(x, sp.Rational(k, 7) + sp.Rational(1, 3)), 15)) or 0) < 1e-8
                         for k in (1, 2, 3))
            b.append(OK("**Verificación numérica:** la derivada del resultado coincide con el integrando ✔") if ok_num
                     else AV("No pude verificar que la derivada del resultado sea el integrando (podría haber saltos de rama)."))
    except Exception:  # noqa: BLE001
        pass
    if F.has(sp.erf, sp.erfi, sp.Ei, sp.li, sp.fresnels, sp.fresnelc, sp.Si, sp.Ci):
        b.append(IN("El resultado usa una **función especial** (error, integral exponencial, seno integral…): la primitiva no es "
                    "elemental, pero sí está bien definida."))
    return res(b, primitiva=Fs)


def _integral_val(expr, x, a, bb):
    """Valor de ∫_a^b con tratamiento de singularidades interiores (SymPy puede dar valor principal)."""
    pts = []
    try:
        sing = singularities(expr, x)
        if isinstance(sing, sp.FiniteSet):
            lo, hi = sorted([_flt(a) if a not in (sp.oo, -sp.oo) else (math.inf if a == sp.oo else -math.inf),
                             _flt(bb) if bb not in (sp.oo, -sp.oo) else (math.inf if bb == sp.oo else -math.inf)],
                            key=lambda v: v if v is not None else 0)
            pts = [s for s in sing if s.is_real and _flt(s) is not None and lo < _flt(s) < hi]
    except Exception:  # noqa: BLE001
        pass
    pts.sort(key=lambda p: _flt(p))
    cortes = [a] + pts + [bb]
    total, partes = sp.Integer(0), []
    for l, r in zip(cortes[:-1], cortes[1:]):
        v = sp.integrate(expr, (x, l, r))
        partes.append((l, r, v))
        total += v
    return total, partes, pts


@_op
def integral_definida(expr, x, a, bb):
    """Integral definida (incluye impropias): valor exacto, aproximado y convergencia."""
    b = [H("Planteamiento"), L(r"\int_{" + lx(a) + "}^{" + lx(bb) + "} " + sp.latex(expr) + r"\,\mathrm{d}" + sp.latex(x))]
    if a == bb:
        return res(b + [OK("Los límites coinciden: la integral vale **0**.")], valor=sp.Integer(0), converge=True)
    inf_lim = a in (sp.oo, -sp.oo) or bb in (sp.oo, -sp.oo)
    total, partes, interiores = _integral_val(expr, x, a, bb)
    impropia = inf_lim or bool(interiores)
    try:
        sing_ext = singularities(expr, x)
        if isinstance(sing_ext, sp.FiniteSet):
            impropia = impropia or any(s in (a, bb) for s in sing_ext)
    except Exception:  # noqa: BLE001
        pass
    if impropia:
        b.append(IN("Es una **integral impropia** (hay un límite infinito o el integrando se dispara en el intervalo). "
                    "Se define como un **límite**; la integral **converge** si ese límite es un número finito."))
    if interiores:
        b.append(T("El integrando tiene singularidades **dentro** del intervalo en " + ", ".join(f"$x={lx(p)}$" for p in interiores) +
                   ": se parte en tramos y cada tramo debe converger por separado."))
    Fx = None
    try:
        Fx = sp.integrate(expr, x)
        if Fx.has(sp.Integral):
            Fx = None
    except Exception:  # noqa: BLE001
        Fx = None
    if Fx is not None:
        b += [H("Primitiva (Teorema Fundamental del Cálculo)"),
              L(r"F(x)=" + sp.latex(_simplificar(Fx)) + r",\qquad \int_a^b f=F(b)-F(a)")]

    b.append(H("Resultado"))
    clases = [_clase(v) for _, _, v in partes]
    if any(c in ("+oo", "-oo", "zoo") for c in clases):
        malo = [(l, r) for (l, r, v) in partes if _clase(v) in ("+oo", "-oo", "zoo")]
        b.append(AV("La integral **diverge** (el límite es infinito)" +
                    (": falla el tramo " + ", ".join(f"$[{lx(l)},{lx(r)}]$" for l, r in malo) if len(partes) > 1 else "") + "."))
        return res(b, valor=total if len(partes) == 1 else sp.oo, converge=False)
    if any(c in ("nd", "osc") for c in clases) or total.has(sp.Integral):
        # no exacta: intentar numéricamente
        try:
            import mpmath as mp
            f = _mp_f(expr, x)
            lo = mp.inf if a == sp.oo else (-mp.inf if a == -sp.oo else mp.mpf(str(sp.N(a, 20))))
            hi = mp.inf if bb == sp.oo else (-mp.inf if bb == -sp.oo else mp.mpf(str(sp.N(bb, 20))))
            pts_q = [lo] + [mp.mpf(str(sp.N(p, 20))) for p in interiores] + [hi]
            val = mp.quad(f, pts_q)
            if isinstance(val, mp.mpc) or not mp.isfinite(val):
                raise ValueError
            b.append(AV(f"SymPy no obtuvo una fórmula exacta. **Valor numérico aproximado:** ${float(val):.10g}$ "
                        "(cuadratura numérica; si la integral fuera divergente este número no tendría significado)."))
            return res(b, valor=sp.Float(float(val)), converge=None, aproximado=True)
        except Exception:  # noqa: BLE001
            b.append(AV("No pude calcular esta integral (ni exacta ni numéricamente). Puede ser divergente o muy compleja."))
            return res(b, valor=None, converge=None)
    totals = _simplificar(sp.simplify(total))
    b.append(OK(f"**Converge** y vale ${lx(totals)}$" + ("" if totals.is_Integer or totals.is_Float else f"  $\\approx {sp.latex(sp.N(totals, 10))}$")))
    if len(partes) > 1:
        b.append(T("Tramos: " + "; ".join(f"$[{lx(l)},{lx(r)}]$: ${lx(sp.simplify(v))}$" for l, r, v in partes)))
    # verificación numérica independiente
    try:
        import mpmath as mp
        f = _mp_f(expr, x)
        lo = mp.inf if a == sp.oo else (-mp.inf if a == -sp.oo else mp.mpf(str(sp.N(a, 20))))
        hi = mp.inf if bb == sp.oo else (-mp.inf if bb == -sp.oo else mp.mpf(str(sp.N(bb, 20))))
        pts_q = [lo] + [mp.mpf(str(sp.N(p, 20))) for p in interiores] + [hi]
        num = mp.quad(f, pts_q)
        tv = _flt(totals)
        if tv is not None and not isinstance(num, mp.mpc):
            if abs(float(num) - tv) <= 1e-6 * (1 + abs(tv)):
                b.append(OK(f"**Verificación numérica independiente:** ≈ {float(num):.10g} ✔"))
            else:
                b.append(AV(f"⚠️ La cuadratura numérica da ≈ {float(num):.10g}, que no coincide con el valor exacto: "
                            "desconfía (puede haber una singularidad no detectada)."))
    except Exception:  # noqa: BLE001
        pass
    sg = _flt(totals)
    if sg is not None and not impropia and sg < 0:
        b.append(IN("Una integral definida puede ser negativa: es un **área con signo** (la parte bajo el eje x cuenta negativa)."))
    return res(b, valor=totals, converge=True, primitiva=Fx)


@_op
def integral_multiple(expr, limites):
    """
    Integral iterada. limites = [(var, a, b), ...] de ADENTRO hacia AFUERA.
    Los límites de una integral pueden depender de las variables de las integrales exteriores.
    """
    if not 2 <= len(limites) <= 3:
        raise ErrorCalculo("Se admiten integrales dobles y triples.")
    vs = [l[0] for l in limites]
    for i, (v, a, bb) in enumerate(limites):
        interiores = set(vs[:i])
        if (a.free_symbols | bb.free_symbols) & interiores:
            raise ErrorCalculo(f"Los límites de la integral en ${sp.latex(v)}$ no pueden depender de una variable de una integral "
                               "INTERIOR; solo pueden depender de las exteriores.")
    nombre = {2: "doble", 3: "triple"}[len(limites)]
    b = [H(f"Integral {nombre}"),
         L("".join(r"\int_{" + lx(a) + "}^{" + lx(bb) + "}" for v, a, bb in reversed(limites)) + sp.latex(expr)
           + "".join(r"\,\mathrm{d}" + sp.latex(v) for v in vs))]
    if expr == 1:
        b.append(IN("Con integrando 1, esta integral mide el **" + ("área" if len(limites) == 2 else "volumen") + "** de la región."))
    acc = expr
    b.append(H("Se integra de adentro hacia afuera"))
    for v, a, bb in limites:
        acc = sp.integrate(acc, (v, a, bb))
        if acc.has(sp.Integral):
            b.append(AV(f"SymPy no pudo integrar respecto de ${sp.latex(v)}$ en este paso."))
            return res(b, valor=None)
        accs = _simplificar(acc)
        b.append(T(f"Tras integrar en ${sp.latex(v)}$ de ${lx(a)}$ a ${lx(bb)}$:"))
        b.append(L(sp.latex(accs)))
        acc = accs
    if _clase(acc) in ("+oo", "-oo", "zoo"):
        b.append(AV("La integral **diverge**."))
        return res(b, valor=acc, converge=False)
    b.append(OK(f"**Resultado:** ${lx(acc)}$" + ("" if acc.is_Integer else f" $\\approx {sp.latex(sp.N(acc, 10))}$")))
    if acc.free_symbols:
        b.append(IN("El resultado todavía contiene variables: algún límite dependía de una variable que no se integró."))
    return res(b, valor=acc, converge=True)


# ==============================================================================
# 6. SUCESIONES Y SERIES
# ==============================================================================
def _nn():
    return sp.Symbol("n", integer=True, positive=True)


def _valores_numericos(a, nn, n0, cuantos):
    """Valores float de a(n) para n=n0..n0+cuantos-1 (None donde no se pueden evaluar)."""
    import mpmath as mp
    mp.mp.dps = 30
    try:
        f = sp.lambdify(nn, a, "mpmath")
    except Exception:  # noqa: BLE001
        return [None] * cuantos
    out = []
    for k in range(n0, n0 + cuantos):
        try:
            v = f(k)
            out.append(None if isinstance(v, mp.mpc) or not mp.isfinite(v) else float(v))
        except Exception:  # noqa: BLE001
            out.append(None)
    return out


def _tendencia(vals, tol=1e-12):
    """'creciente' | 'decreciente' | 'constante' | 'no monótona' | None, con sus versiones estrictas."""
    v = [x for x in vals if x is not None]
    if len(v) < 3:
        return None
    d = [b_ - a_ for a_, b_ in zip(v[:-1], v[1:])]
    esc = tol * max(1.0, max(abs(t) for t in v))
    if all(abs(t) <= esc for t in d):
        return "constante"
    if all(t >= -esc for t in d):
        return "creciente" if all(t > esc for t in d) else "no decreciente"
    if all(t <= esc for t in d):
        return "decreciente" if all(t < -esc for t in d) else "no creciente"
    return "no monótona"


@_op
def sucesion(expr, n, n0=1):
    """Sucesión a_n: términos, límite, monotonía, cotas, tipo (aritmética/geométrica)."""
    nn = _nn()
    a = expr.subs(n, nn)
    b = [H("Sucesión"), L(r"a_n=" + sp.latex(a) + r",\quad n\ge " + str(n0))]
    primero = a.subs(nn, n0)
    if _clase(primero) != "fin":
        raise ErrorCalculo(f"El primer término $a_{{{n0}}}$ no está definido (da una división entre cero u otra operación inválida): "
                           "elige otro valor inicial de n.")
    filas = []
    for k in range(n0, n0 + 10):
        v = a.subs(nn, k)
        filas.append([str(k), m(sp.simplify(v)), _num_str(v, 8)])
    b += [H("Primeros términos"), TAB(["n", "a_n (exacto)", "a_n (decimal)"], filas)]
    nume = _valores_numericos(a, nn, n0, 300)

    b.append(H("Límite"))
    Lv = _lim_sec(a, nn)
    c = _clase(Lv)
    if c == "fin":
        b.append(OK(f"$\\lim_{{n\\to\\infty}}a_n={lx(Lv)}$ → la sucesión **converge** a ${lx(Lv)}$."))
    elif c in ("+oo", "-oo"):
        b.append(AV(f"$\\lim a_n={lx(Lv)}$ → la sucesión **diverge** ({'crece' if c == '+oo' else 'decrece'} sin cota)."))
    elif c == "osc":
        b.append(AV("El límite **no existe**: la sucesión **oscila**, así que diverge."))
    else:
        b.append(AV("No pude calcular el límite de forma exacta; mira los términos de la tabla."))

    b.append(H("Monotonía"))
    d_ = sp.simplify(a.subs(nn, nn + 1) - a)
    simb = None
    try:
        if d_.is_positive:
            simb = "estrictamente creciente"
        elif d_.is_negative:
            simb = "estrictamente decreciente"
        elif d_.is_nonnegative:
            simb = "creciente (no decreciente)"
        elif d_.is_nonpositive:
            simb = "decreciente (no creciente)"
    except Exception:  # noqa: BLE001
        pass
    tend = _tendencia(nume)
    b.append(L(r"a_{n+1}-a_n=" + sp.latex(d_)))
    if simb:
        b.append(OK(f"Como $a_{{n+1}}-a_n$ es {'positivo' if 'creciente' in simb and 'no' not in simb[:3] else 'no negativo' if 'creciente' in simb else 'negativo' if 'estrictamente' in simb else 'no positivo'}, "
                    f"la sucesión es **{simb}** (demostrado)."))
    elif tend:
        txt = {"creciente": "estrictamente creciente", "decreciente": "estrictamente decreciente", "constante": "constante",
               "no decreciente": "creciente (no decreciente)", "no creciente": "decreciente (no creciente)",
               "no monótona": "no monótona (sube y baja)"}[tend]
        b.append(T(f"En los primeros 300 términos es **{txt}** (evidencia numérica; no es una demostración)."))
    b.append(H("Cotas y tipo"))
    if c == "fin":
        b.append(OK("Toda sucesión **convergente es acotada**. Si además es monótona, converge a su supremo (si crece) o ínfimo (si decrece)."))
    elif c in ("+oo", "-oo"):
        b.append(T("**No está acotada** " + ("superiormente." if c == "+oo" else "inferiormente.")))
    if not d_.has(nn):
        b.append(OK(f"Es una **sucesión aritmética** de diferencia ${lx(d_)}$: $a_n=a_{{{n0}}}+(n-{n0})\\cdot({lx(d_)})$."))
    else:
        try:
            r_ = sp.simplify(a.subs(nn, nn + 1) / a)
            if not r_.has(nn) and _clase(r_) == "fin":
                b.append(OK(f"Es una **sucesión geométrica** de razón ${lx(r_)}$: $a_n=a_{{{n0}}}\\cdot({lx(r_)})^{{n-{n0}}}$."
                            + (" Converge porque $|r|<1$." if abs(_flt(r_) or 2) < 1 else " No converge a 0 porque $|r|\\ge1$." if abs(_flt(r_) or 0) >= 1 else "")))
        except Exception:  # noqa: BLE001
            pass
    return res(b, limite=Lv, valores=[v for v in nume[:40]], n0=n0)


def _lim_sec(a, nn):
    """Límite de a_n con respaldo: si SymPy no puede, |a_n|→0 implica a_n→0; si |a_n| no se acerca a 0
    pero el signo alterna sin parar, la sucesión oscila (no tiene límite)."""
    Lv = lim(a, nn, sp.oo)
    if Lv is not None and _clase(Lv) != "nd":
        return Lv
    La = lim(sp.Abs(a), nn, sp.oo)
    if La is not None and _clase(La) == "fin" and La == 0:
        return sp.Integer(0)
    if La is not None and _clase(La) in ("fin", "+oo"):
        vals = [v for v in _valores_numericos(a, nn, 1, 400)[-120:] if v is not None]
        if len(vals) > 20 and any(v > 0 for v in vals) and any(v < 0 for v in vals):
            cambios = sum(1 for u, w in zip(vals[:-1], vals[1:]) if u * w < 0)
            if cambios >= 10:
                return sp.AccumBounds(-sp.oo if _clase(La) == "+oo" else -La, sp.oo if _clase(La) == "+oo" else La)
    return Lv


def _sumas_parciales(a, nn, n0, cortes):
    import mpmath as mp
    mp.mp.dps = 30
    f = sp.lambdify(nn, a, "mpmath")
    out, S = [], mp.mpf(0)
    objetivo = set(cortes)
    for k in range(n0, n0 + max(cortes)):
        try:
            S += f(k)
        except Exception:  # noqa: BLE001
            return out
        if (k - n0 + 1) in objetivo:
            out.append((k - n0 + 1, S if isinstance(S, mp.mpc) else float(S)))
    return out


def _serie_core(a, nn, n0, detalle=True, buscar_absoluta=True):
    """Aplica criterios en orden; devuelve (bloques, veredicto, tipo) con
    veredicto ∈ {'conv','div',None} y tipo ∈ {'absoluta','condicional',None}."""
    b = []
    veredicto, tipo = None, None

    def paso(titulo):
        b.append(H(titulo))

    # 1) condición necesaria
    paso("Criterio 1 · Del término general (condición necesaria)")
    L1 = _lim_sec(a, nn)
    c1 = _clase(L1)
    if c1 == "fin" and L1 == 0:
        b.append(T("$\\lim a_n=0$: la condición necesaria **se cumple**, pero **no basta** para concluir convergencia (p. ej. la serie armónica)."))
    elif c1 in ("fin", "+oo", "-oo", "zoo") or (c1 == "osc" and not (L1.min == 0 and L1.max == 0)):
        b.append(AV(f"$\\lim a_n={_desc_lim(L1).replace('$', '') if c1 != 'fin' else lx(L1)}\\neq 0$ (o no existe) → la serie **DIVERGE** "
                    "(criterio del término $n$-ésimo: si $a_n\\not\\to0$, $\\sum a_n$ diverge)."))
        return b, "div", None
    else:
        b.append(IN("No pude calcular $\\lim a_n$; se continúa con otros criterios."))

    # 2) geométrica
    try:
        r_ = sp.simplify(a.subs(nn, nn + 1) / a)
    except Exception:  # noqa: BLE001
        r_ = None
    if r_ is not None and not r_.has(nn) and _clase(r_) == "fin":
        paso("Criterio 2 · Serie geométrica")
        b.append(T(f"El cociente $a_{{n+1}}/a_n={lx(r_)}$ es **constante**: es una serie geométrica de razón $r={lx(r_)}$."))
        if abs(_flt(r_)) < 1:
            b.append(OK(f"Como $|r|={lx(abs(r_))}<1$, **CONVERGE** (absolutamente). Suma $=\\dfrac{{a_{{{n0}}}}}{{1-r}}={lx(sp.simplify(a.subs(nn, n0) / (1 - r_)))}$."))
            return b, "conv", "absoluta"
        b.append(AV(f"Como $|r|={lx(abs(r_))}\\ge1$, **DIVERGE**."))
        return b, "div", None

    # 3) p-serie / potencia
    try:
        c_, e_ = a.as_coeff_exponent(nn)
    except Exception:  # noqa: BLE001
        c_, e_ = None, None
    if c_ is not None and not c_.has(nn) and _clase(e_) == "fin" and c_ != 0:
        p_ = -e_
        paso("Criterio 3 · Serie $p$")
        b.append(T(f"El término es ${lx(sp.simplify(a))}=\\dfrac{{{lx(c_)}}}{{n^{{{lx(p_)}}}}}$: serie $p$ con $p={lx(p_)}$ "
                   "(converge si $p>1$, diverge si $p\\le1$)."))
        if _flt(p_) > 1:
            b.append(OK(f"$p={lx(p_)}>1$ → **CONVERGE** (absolutamente)."))
            return b, "conv", "absoluta"
        b.append(AV(f"$p={lx(p_)}\\le1$ → **DIVERGE**."))
        return b, "div", None

    # 4) alternante (Leibniz)
    alt = [f for f in sp.Mul.make_args(a) if f.is_Pow and f.base == -1 and f.exp.has(nn)]
    if alt:
        bn = sp.simplify(sp.Mul(*[f for f in sp.Mul.make_args(a) if f not in alt]))
        paso("Criterio 4 · Serie alternante (Leibniz)")
        b.append(T(f"La serie alterna de signo: $a_n=(-1)^{{\\cdots}}\\,b_n$ con $b_n={sp.latex(bn)}$."))
        vals = _valores_numericos(bn, nn, 1, 300)
        positivo = all(v is None or v > 0 for v in vals) and any(v is not None for v in vals)
        tend = _tendencia(vals)
        Lb = lim(bn, nn, sp.oo)
        b.append(T(f"$b_n>0$: {'sí' if positivo else 'no (revisa)'}; $b_n$ decreciente: "
                   f"{'sí' if tend in ('decreciente', 'no creciente') else 'no / no se pudo comprobar'}; "
                   f"$\\lim b_n={_desc_lim(Lb).replace('$', '') if _clase(Lb) != 'fin' else lx(Lb)}$."))
        if positivo and tend in ("decreciente", "no creciente") and _clase(Lb) == "fin" and Lb == 0:
            b.append(OK("Se cumplen las tres condiciones de Leibniz → la serie **CONVERGE**."))
            if buscar_absoluta:
                bl2, v2, _ = _serie_core(sp.Abs(bn) if False else bn, nn, n0, detalle=False, buscar_absoluta=False)
                if v2 == "conv":
                    b.append(OK("Además $\\sum |a_n|$ también converge → **converge ABSOLUTAMENTE**."))
                    return b, "conv", "absoluta"
                if v2 == "div":
                    b.append(OK("Pero $\\sum |a_n|$ **diverge** → converge solo **CONDICIONALMENTE**."))
                    return b, "conv", "condicional"
            return b, "conv", None
        b.append(IN("Leibniz no se pudo aplicar o no se cumple; se prueban otros criterios."))

    # 5) razón
    paso("Criterio 5 · De la razón (D'Alembert)")
    try:
        rs = sp.simplify(sp.combsimp(a.subs(nn, nn + 1) / a))
        Lr = lim(sp.Abs(rs), nn, sp.oo)
    except Exception:  # noqa: BLE001
        Lr = None
    cr = _clase(Lr)
    if cr == "fin":
        b.append(T(f"$\\rho=\\lim\\left|\\dfrac{{a_{{n+1}}}}{{a_n}}\\right|={lx(Lr)}$"))
        if _flt(Lr) < 1:
            b.append(OK("$\\rho<1$ → la serie **CONVERGE ABSOLUTAMENTE**."))
            return b, "conv", "absoluta"
        if _flt(Lr) > 1:
            b.append(AV("$\\rho>1$ → la serie **DIVERGE**."))
            return b, "div", None
        b.append(IN("$\\rho=1$ → el criterio **no decide**."))
    elif cr == "+oo":
        b.append(AV("$\\rho=\\infty>1$ → la serie **DIVERGE**."))
        return b, "div", None
    else:
        b.append(IN("No pude calcular el límite de la razón."))

    # 6) raíz
    paso("Criterio 6 · De la raíz (Cauchy)")
    try:
        Lq = lim(sp.Abs(a) ** (1 / nn), nn, sp.oo)
    except Exception:  # noqa: BLE001
        Lq = None
    cq = _clase(Lq)
    if cq == "fin":
        b.append(T(f"$\\lim\\sqrt[n]{{|a_n|}}={lx(Lq)}$"))
        if _flt(Lq) < 1:
            b.append(OK("$<1$ → **CONVERGE ABSOLUTAMENTE**."))
            return b, "conv", "absoluta"
        if _flt(Lq) > 1:
            b.append(AV("$>1$ → **DIVERGE**."))
            return b, "div", None
        b.append(IN("$=1$ → no decide."))
    else:
        b.append(IN("No pude calcular este límite."))

    # 7) comparación en el límite con una serie p
    paso("Criterio 7 · Comparación en el límite con $\\sum 1/n^p$")
    try:
        p_est = -lim(sp.log(sp.Abs(a)) / sp.log(nn), nn, sp.oo)
    except Exception:  # noqa: BLE001
        p_est = None
    if p_est is not None and _clase(p_est) == "fin":
        p_est = sp.nsimplify(p_est)
        K = lim(sp.Abs(a) * nn ** p_est, nn, sp.oo)
        if _clase(K) == "fin" and K > 0:
            b.append(T(f"Para $n$ grande, $|a_n|$ se parece a $\\dfrac{{{lx(K)}}}{{n^{{{lx(p_est)}}}}}$: "
                       f"$\\lim |a_n|\\,n^{{{lx(p_est)}}}={lx(K)}\\in(0,\\infty)$."))
            if _flt(p_est) > 1:
                b.append(OK(f"Como $\\sum 1/n^{{{lx(p_est)}}}$ converge ($p>1$), la serie **CONVERGE ABSOLUTAMENTE**."))
                return b, "conv", "absoluta"
            b.append(AV(f"Como $\\sum 1/n^{{{lx(p_est)}}}$ diverge ($p\\le1$), $\\sum|a_n|$ **diverge**."
                        + (" Si la serie no es de términos positivos, esto no basta para decidir la serie original." if True else "")))
            if all(v is None or v >= 0 for v in _valores_numericos(a, nn, n0, 200)):
                return b, "div", None
        else:
            b.append(IN("No hay una comparación limpia con una serie $p$."))
    else:
        b.append(IN("No pude identificar el orden de magnitud de $a_n$."))

    # 8) integral
    paso("Criterio 8 · De la integral (términos positivos y decrecientes)")
    vals = _valores_numericos(a, nn, n0, 200)
    if all(v is None or v > 0 for v in vals) and _tendencia(vals) in ("decreciente", "no creciente"):
        xr = sp.Symbol("x", positive=True)
        fI = a.subs(nn, xr)
        try:
            I = sp.integrate(fI, (xr, n0, sp.oo))
            ci = _clase(I)
            if ci == "fin":
                b.append(OK(f"$\\displaystyle\\int_{{{n0}}}^{{\\infty}}f(x)\\,dx={lx(I)}$ **converge** → la serie **CONVERGE**."))
                return b, "conv", "absoluta"
            if ci == "+oo":
                b.append(AV(f"$\\displaystyle\\int_{{{n0}}}^{{\\infty}}f(x)\\,dx=\\infty$ → la serie **DIVERGE**."))
                return b, "div", None
        except Exception:  # noqa: BLE001
            pass
        b.append(IN("No pude calcular la integral impropia."))
    else:
        b.append(IN("No aplica: los términos no son positivos y decrecientes (o no pude comprobarlo)."))

    # 9) SymPy
    paso("Criterio 9 · Verificación con SymPy")
    try:
        conv = sp.Sum(a, (nn, n0, sp.oo)).is_convergent()
        if conv is True:
            b.append(OK("SymPy determina que la serie **CONVERGE**."))
            return b, "conv", None
        if conv is False:
            b.append(AV("SymPy determina que la serie **DIVERGE**."))
            return b, "div", None
    except Exception:  # noqa: BLE001
        pass
    b.append(IN("Ningún criterio pudo decidir. Prueba con otro criterio a mano (comparación directa, Dirichlet, Abel…)."))
    return b, None, None


@_op
def serie(expr, n, n0=1):
    """Serie infinita Σ a_n: criterios de convergencia (en orden), valor de la suma y sumas parciales."""
    nn = _nn()
    a = expr.subs(n, nn)
    b = [H("Serie"), L(r"\sum_{n=" + str(n0) + r"}^{\infty}" + sp.latex(a))]
    primero = a.subs(nn, n0)
    if _clase(primero) != "fin":
        raise ErrorCalculo(f"El primer término ($n={n0}$) no está definido: elige un valor inicial de $n$ donde la fórmula tenga sentido.")
    bl, v, tipo = _serie_core(a, nn, n0)
    b += bl
    b.append(H("Conclusión"))
    if v == "conv":
        det = {"absoluta": " **absolutamente**", "condicional": " **condicionalmente**"}.get(tipo, "")
        b.append(OK(f"La serie **CONVERGE**{det}."))
    elif v == "div":
        b.append(AV("La serie **DIVERGE**."))
    else:
        b.append(IN("No se pudo concluir con los criterios disponibles."))
    suma = None
    if v != "div":
        try:
            S = sp.summation(a, (nn, n0, sp.oo))
            if not S.has(sp.Sum) and _clase(S) == "fin":
                suma = sp.simplify(S)
                b.append(OK(f"**Suma exacta:** $\\sum_{{n={n0}}}^{{\\infty}}a_n={lx(suma)}\\approx{sp.latex(sp.N(suma, 10))}$"))
        except Exception:  # noqa: BLE001
            pass
        if suma is None and v == "conv":
            try:
                import mpmath as mp
                mp.mp.dps = 25
                f = sp.lambdify(nn, a, "mpmath")
                val = mp.nsum(f, [n0, mp.inf])
                suma = sp.Float(str(val), 15)
                b.append(T(f"**Suma aproximada:** ${float(val):.12g}$ (no hay fórmula cerrada; estimación numérica)."))
            except Exception:  # noqa: BLE001
                pass
    sums = []
    try:
        sums = _sumas_parciales(a, nn, n0, [5, 10, 50, 100, 500])
        filas = [[str(N_), f"{S_:.12g}" if isinstance(S_, float) else str(S_)] for N_, S_ in sums]
        if filas:
            b += [H("Sumas parciales"), TAB(["N (términos)", "S_N"], filas)]
            b.append(T("Si la serie converge, $S_N$ se estabiliza; si diverge, crece sin cota u oscila."))
    except Exception:  # noqa: BLE001
        pass
    return res(b, converge=(True if v == "conv" else False if v == "div" else None), tipo=tipo, suma=suma, sumas=sums)


@_op
def serie_potencias(expr, n, x, centro=0, n0=0):
    """Serie de potencias Σ a_n(x): radio e intervalo de convergencia (con prueba de los extremos)."""
    nn = _nn()
    a = expr.subs(n, nn)
    if x not in a.free_symbols:
        raise ErrorCalculo("Una serie de potencias debe contener la variable $x$ además del índice $n$.")
    b = [H("Serie de potencias"), L(r"\sum_{n=" + str(n0) + r"}^{\infty}" + sp.latex(a))]
    b.append(H("Radio de convergencia (criterio de la razón)"))
    try:
        rs = sp.simplify(sp.combsimp(a.subs(nn, nn + 1) / a))
    except Exception:  # noqa: BLE001
        rs = None
    Lx = lim(sp.Abs(rs), nn, sp.oo) if rs is not None else None
    usado = "razón"
    if Lx is None or Lx.has(sp.Limit):
        Lx = lim(sp.Abs(a) ** (1 / nn), nn, sp.oo)
        usado = "raíz"
    if Lx is None:
        b.append(AV("No pude calcular el límite de la razón ni de la raíz; no se pudo determinar el radio."))
        return res(b)
    b.append(L(r"\lim_{n\to\infty}\left|\frac{a_{n+1}}{a_n}\right|=" + sp.latex(Lx) if usado == "razón"
               else r"\lim_{n\to\infty}\sqrt[n]{|a_n|}=" + sp.latex(Lx)))
    if Lx == 0:
        b.append(OK("El límite es 0 para todo $x$ → radio $R=\\infty$: la serie **converge para todo real** $x$."))
        return res(b, radio=sp.oo, intervalo=sp.S.Reals)
    if Lx.has(sp.oo, sp.zoo):
        b.append(OK(f"El límite es infinito para $x\\neq {lx(centro)}$ → radio $R=0$: converge **solo en $x={lx(centro)}$**."))
        return res(b, radio=sp.Integer(0), intervalo=sp.FiniteSet(centro))
    try:
        sol = sp.solve_univariate_inequality(Lx < 1, x, relational=False, domain=sp.S.Reals)
    except Exception:  # noqa: BLE001
        sol = None
    if not isinstance(sol, sp.Interval):
        b.append(AV("No pude resolver la desigualdad $\\rho(x)<1$ para encontrar el intervalo."))
        return res(b)
    alfa, beta = sol.start, sol.end
    R = sp.simplify((beta - alfa) / 2)
    cen = sp.simplify((beta + alfa) / 2)
    b += [T(f"Convergencia absoluta cuando $\\rho(x)<1$, es decir $x\\in{sp.latex(sol)}$."),
          OK(f"**Radio de convergencia** $R={lx(R)}$, con centro en $x={lx(cen)}$.")]
    b.append(H("Extremos del intervalo (hay que probarlos uno por uno)"))
    estado = {}
    for nombre, e in (("izquierdo", alfa), ("derecho", beta)):
        ae = a.subs(x, e)
        _, v, tipo = _serie_core(sp.simplify(ae), nn, n0, detalle=False)
        txt = {"conv": f"**converge**{' (condicionalmente)' if tipo == 'condicional' else ''}", "div": "**diverge**", None: "no pude decidirlo"}[v]
        b.append(T(f"- En $x={lx(e)}$ ({nombre}): la serie numérica ${sp.latex(sp.simplify(ae))}$ {txt}."))
        estado[nombre] = v
    cierra_izq, cierra_der = estado["izquierdo"] == "conv", estado["derecho"] == "conv"
    inc_dudoso = None in estado.values()
    intervalo = sp.Interval(alfa, beta, left_open=not cierra_izq, right_open=not cierra_der)
    b.append(H("Intervalo de convergencia"))
    b.append(L(sp.latex(intervalo)))
    if inc_dudoso:
        b.append(AV("Algún extremo no se pudo decidir: el intervalo mostrado lo trata como abierto en ese lado."))
    return res(b, radio=R, intervalo=intervalo, centro=cen)


# ==============================================================================
# 7. NIVELES, RELACIONES Y EVALUACIÓN DE OPERACIONES
# ==============================================================================
def _clasificar_cuadrica(expr, vars_, c):
    """Nombre y datos de {f = c} cuando f es cuadrática en 2 o 3 variables, o None."""
    try:
        P = sp.Poly(sp.expand(expr - c), *vars_)
    except Exception:  # noqa: BLE001
        return None
    if P.total_degree() != 2:
        return None
    if len(vars_) == 2:
        x, y = vars_
        A, B, C = (P.coeff_monomial(t) for t in (x ** 2, x * y, y ** 2))
        D, E, F = P.coeff_monomial(x), P.coeff_monomial(y), P.coeff_monomial(1)
        Q = B ** 2 - 4 * A * C
        Dl = sp.Matrix([[A, B / 2, D / 2], [B / 2, C, E / 2], [D / 2, E / 2, F]]).det()
        if Q < 0:
            if Dl == 0:
                return "un único punto"
            if Dl * (A + C) < 0:
                if A == C and B == 0:
                    cx, cy = -D / (2 * A), -E / (2 * A)
                    r2 = sp.simplify((D ** 2 + E ** 2) / (4 * A ** 2) - F / A)
                    return f"una **circunferencia** de centro $({lx(cx)},{lx(cy)})$ y radio ${lx(sp.sqrt(r2))}$"
                return "una **elipse**"
            return "el **conjunto vacío** (no hay puntos reales)"
        if Q > 0:
            return "una **hipérbola**" if Dl != 0 else "**dos rectas** que se cortan"
        return "una **parábola**" if Dl != 0 else "**rectas paralelas** (o una recta, o vacío)"
    if len(vars_) == 3:
        sq = [P.coeff_monomial(v ** 2) for v in vars_]
        cruz = [P.coeff_monomial(vars_[i] * vars_[j]) for i in range(3) for j in range(i + 1, 3)]
        if all(cr == 0 for cr in cruz) and sq[0] == sq[1] == sq[2] != 0:
            lin = [P.coeff_monomial(v) for v in vars_]
            F = P.coeff_monomial(1)
            r2 = sp.simplify(sum(l ** 2 for l in lin) / (4 * sq[0] ** 2) - F / sq[0])
            cen = [-l / (2 * sq[0]) for l in lin]
            if r2 > 0:
                return f"una **esfera** de centro $({','.join(lx(t) for t in cen)})$ y radio ${lx(sp.sqrt(r2))}$"
            return "un único punto" if r2 == 0 else "el **conjunto vacío**"
        if all(cr == 0 for cr in cruz) and all(s != 0 for s in sq):
            return "una **cuádrica** (elipsoide, hiperboloide…) según los signos"
    return None


@_op
def niveles(expr, vars_, niveles_):
    """Conjuntos de nivel {f = c}: ecuación, forma despejada y clasificación de cónicas/cuádricas."""
    n = len(vars_)
    nombre = {1: "puntos de nivel", 2: "curvas de nivel", 3: "superficies de nivel"}.get(n, "conjuntos de nivel")
    b = [H(f"Conjuntos de nivel ({nombre})"),
         T("El **conjunto de nivel** $c$ de $f$ es $\\{p : f(p)=c\\}$: todos los puntos donde la función vale lo mismo. "
           + {2: "Son las **curvas de nivel** (como las líneas de un mapa topográfico).",
              3: "Son **superficies** en el espacio."}.get(n, ""))]
    datos = {"niveles": list(niveles_)}
    for c in niveles_:
        b.append(H(f"Nivel $c={lx(c)}$"))
        b.append(L(sp.latex(sp.Eq(expr, c))))
        if n == 1:
            pts, nota = sol_reales(expr - c, vars_[0])
            b.append(T(("Puntos: " + ", ".join(f"$x={lx(p)}$" for p in pts)) if pts else "No hay puntos reales en este nivel."))
            continue
        desc = _clasificar_cuadrica(expr, vars_, c)
        if desc:
            b.append(T(f"Es {desc}."))
        for v in vars_[:2] if n >= 2 else []:
            try:
                sol = sp.solve(sp.Eq(expr, c), v)
            except Exception:  # noqa: BLE001
                sol = []
            sol = [s for s in sol if s.is_real is not False and not s.has(sp.I)][:3]
            if sol and len(sol) <= 3:
                b.append(T(f"Despejando ${sp.latex(v)}$: " + "; ".join(f"${sp.latex(v)}={sp.latex(sp.simplify(s))}$" for s in sol)))
                break
    if n >= 2:
        b.append(IN("**Propiedad clave:** el gradiente $\\nabla f$ es **perpendicular** a la curva (superficie) de nivel en cada punto, "
                    "y apunta hacia donde $f$ crece más rápido. Donde las curvas de nivel están muy juntas, $f$ cambia rápido."))
    if n == 3:
        b.append(IN("Para verlas, la pestaña de gráficas muestra **cortes** (secciones con $z$ fija) de cada superficie de nivel."))
    return res(b, **datos)


@_op
def resolver_relacion(rel):
    """Resuelve una ecuación o desigualdad (en ℝ) o describe la región/curva en varias variables."""
    vs = _vars(rel)
    n = len(vs)
    b = [H("Planteamiento"), L(sp.latex(rel))]
    if rel in (sp.true, sp.false):
        b = [H("Planteamiento"), L(r"\text{(la relación se simplificó por completo)}")]
    if rel == sp.false:
        return res(b + [AV("**No tiene solución** en los reales: es una condición **siempre falsa** (por ejemplo, un cuadrado "
                           "nunca es negativo).")], solucion=sp.S.EmptySet)
    if rel == sp.true:
        return res(b + [OK("Se cumple para **todo** valor real: es una condición **siempre verdadera**.")], solucion=sp.S.Reals)
    if n == 0:
        return res(b + [OK("Es **verdadera**.") if bool(rel) else AV("Es **falsa**.")])
    if n == 1:
        x = vs[0]
        b.append(H("Solución en los reales"))
        try:
            if isinstance(rel, sp.And):
                sol = sp.S.Reals
                for r_ in rel.args:
                    sol = sol.intersect(sp.solveset(r_, x, sp.S.Reals))
            elif isinstance(rel, sp.Or):
                sol = sp.S.EmptySet
                for r_ in rel.args:
                    sol = sol.union(sp.solveset(r_, x, sp.S.Reals))
            else:
                sol = sp.solveset(rel, x, sp.S.Reals)
        except Exception:  # noqa: BLE001
            b.append(AV("No pude resolverla de forma exacta."))
            return res(b)
        b.append(L(f"{sp.latex(x)}\\in {sp.latex(sol)}"))
        if sol == sp.S.EmptySet:
            b.append(AV("**No tiene solución** en los reales."))
        elif sol == sp.S.Reals:
            b.append(OK("Se cumple para **todo** número real."))
        elif isinstance(sol, sp.FiniteSet):
            b.append(OK(f"Tiene **{len(sol)}** solución(es) real(es)."))
        return res(b, solucion=sol)
    b.append(H("Descripción"))
    if isinstance(rel, sp.Eq):
        g = rel.lhs - rel.rhs
        b.append(T(f"Es la **curva/superficie de nivel 0** de $g={sp.latex(sp.simplify(g))}$ en ℝ^{n}."))
        for v in vs[:2]:
            try:
                sol = [s for s in sp.solve(rel, v) if s.is_real is not False and not s.has(sp.I)][:3]
            except Exception:  # noqa: BLE001
                sol = []
            if sol:
                b.append(T(f"Despejando ${sp.latex(v)}$: " + "; ".join(f"${sp.latex(v)}={sp.latex(sp.simplify(s))}$" for s in sol)))
                break
        desc = _clasificar_cuadrica(g, vs, 0) if n in (2, 3) else None
        if desc:
            b.append(OK(f"Es {desc}."))
    else:
        b.append(T(f"Es una **región** de ℝ^{n}: los puntos que cumplen la condición. Su **frontera** es donde la desigualdad se vuelve igualdad."))
        if isinstance(rel, (sp.Lt, sp.Le, sp.Gt, sp.Ge)):
            g = rel.lhs - rel.rhs
            desc = _clasificar_cuadrica(g, vs, 0) if n in (2, 3) else None
            if desc:
                b.append(T(f"La frontera es {desc}."))
    b.append(IN("En «Niveles y gráficas» puedes verla dibujada (n = 2)."))
    return res(b)


@_op
def evaluar_operacion(obj):
    """Evalúa la operación que el usuario escribió directamente (lím, ∫, Σ, Π, d/dx, ∇)."""
    if isinstance(obj, sp.Limit):
        f, x, a, d = obj.args[0], obj.args[1], obj.args[2], str(obj.args[3])
        return limite_1d(f, x, a, d)
    if isinstance(obj, LimiteMulti):
        f, xs, as_ = obj.args
        return limite_multi(f, list(xs), list(as_))
    if isinstance(obj, sp.Integral):
        lim_ = list(obj.limits)
        if len(lim_) == 1 and len(lim_[0]) == 1:
            return integral_indefinida(obj.function, lim_[0][0])
        if len(lim_) == 1:
            v, a, bb = lim_[0]
            return integral_definida(obj.function, v, a, bb)
        if all(len(l) == 3 for l in lim_):
            return integral_multiple(obj.function, [tuple(l) for l in lim_])
        raise ErrorCalculo("En una integral múltiple, todas las integrales deben tener límites (o ninguna).")
    if isinstance(obj, sp.Sum):
        k, a, bb = obj.limits[0]
        if bb in (sp.oo, -sp.oo):
            return serie(obj.function, k, int(a) if a.is_Integer else 1)
        b = [H("Suma finita"), L(sp.latex(obj))]
        val = sp.summation(obj.function, (k, a, bb))
        if val.has(sp.Sum):
            raise ErrorCalculo("SymPy no encontró una fórmula cerrada para esta suma.")
        val = _simplificar(val)
        b.append(OK(f"**Resultado:** ${lx(val)}$" + ("" if val.is_Integer or val.free_symbols else f" $\\approx{sp.latex(sp.N(val, 10))}$")))
        if bb.free_symbols:
            b.append(IN("El resultado es una **fórmula en función de** " + ", ".join(f"${sp.latex(s)}$" for s in bb.free_symbols) + "."))
        return res(b, valor=val)
    if isinstance(obj, sp.Product):
        k, a, bb = obj.limits[0]
        b = [H("Productoria"), L(sp.latex(obj))]
        if bb in (sp.oo, -sp.oo):
            val = obj.doit()
            if val.has(sp.Product):
                raise ErrorCalculo("No pude evaluar este producto infinito de forma exacta.")
        else:
            val = sp.product(obj.function, (k, a, bb))
            if val.has(sp.Product):
                raise ErrorCalculo("SymPy no encontró una fórmula cerrada para este producto.")
        b.append(OK(f"**Resultado:** ${lx(_simplificar(val))}$"))
        return res(b, valor=val)
    if isinstance(obj, sp.Derivative):
        return derivar(obj.expr, [(v, c) for v, c in obj.variable_count])
    if isinstance(obj, Gradiente):
        f = obj.args[0]
        return gradiente_hessiana(f, _vars(f))
    val = obj.doit()
    b = [H("Evaluación de la expresión completa"), L(sp.latex(obj) + "=" + sp.latex(val))]
    return res(b, valor=val)


# ==============================================================================
# 8. EJECUCIÓN SEGURA (proceso aparte con tiempo límite)
# ==============================================================================
# SymPy puede tardar horas (o agotar la memoria) con ciertas expresiones. Para que eso nunca
# congele la app, cada operación corre en un PROCESO TRABAJADOR persistente (así SymPy ya viene
# importado y las llamadas siguientes son rápidas). Si se pasa del tiempo, el proceso se mata y
# se levanta otro; la app solo muestra un aviso.
import atexit as _atexit
import multiprocessing as _mp
import os as _os
import queue as _queue

TIEMPO_POR_DEFECTO = 25                                           # segundos por operación
LIMITE_MEMORIA_MB = 3072                                          # tope de memoria virtual del trabajador (Linux)
N_TRABAJADORES = max(1, int(_os.environ.get("CALCULO_TRABAJADORES", "1")))


class TiempoAgotado(Exception):
    pass


class ErrorArranque(Exception):
    """El proceso trabajador murió antes de responder por primera vez (entorno que no permite `spawn`)."""


@_op
def _autotest(segundos=0, memoria_mb=0, colgar=False):
    """Gancho de pruebas del aislamiento (no lo usa la interfaz)."""
    import time
    if colgar:
        while True:
            pass
    if memoria_mb:
        _ = bytearray(int(min(memoria_mb, 20000)) * 1024 * 1024)
    if segundos:
        time.sleep(min(segundos, 120))
    return res([OK("autotest terminado")], pid=_os.getpid())


def _bucle_trabajador(conn):
    """Código del proceso trabajador: recibe (nombre, args, kwargs) y responde ('ok', dict) o ('err', texto)."""
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (LIMITE_MEMORIA_MB * 1024 * 1024,) * 2)
    except Exception:  # noqa: BLE001  (Windows u otros sistemas sin `resource`)
        pass
    while True:
        try:
            msg = conn.recv()
        except (EOFError, OSError):
            break
        if msg is None:
            break
        nombre, args, kwargs = msg
        try:
            salida = ("ok", OPERACIONES[nombre](*args, **kwargs))
        except BaseException as e:  # noqa: BLE001  (incluye MemoryError)
            salida = ("err", f"{type(e).__name__}: {str(e)[:200]}")
        try:
            conn.send(salida)
        except Exception as e:  # noqa: BLE001  (resultado no serializable)
            try:
                conn.send(("err", f"No se pudo devolver el resultado ({type(e).__name__})."))
            except Exception:  # noqa: BLE001
                break


class _Trabajador:
    def __init__(self):
        self.proc = None
        self.conn = None
        self.respondio = False                       # ¿ha contestado alguna vez este trabajador?
        self._arrancar()

    def _arrancar(self):
        ctx = _mp.get_context("spawn")
        padre, hijo = ctx.Pipe()
        self.proc = ctx.Process(target=_bucle_trabajador, args=(hijo,), daemon=True)
        self.proc.start()
        hijo.close()
        self.conn = padre

    def _matar(self):
        try:
            self.proc.kill()
            self.proc.join(2)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass

    def correr(self, nombre, args, kwargs, timeout):
        if not self.proc.is_alive():
            self._arrancar()
        self.conn.send((nombre, args, kwargs))
        if not self.conn.poll(timeout):
            self._matar()
            self._arrancar()                       # deja uno nuevo listo (calentándose) para la siguiente
            raise TiempoAgotado()
        try:
            tipo, val = self.conn.recv()
            self.respondio = True
        except (EOFError, ConnectionError, OSError):
            nunca_respondio = not self.respondio
            self._matar()
            if nunca_respondio:
                raise ErrorArranque()                # ni siquiera arrancó: no vale la pena reintentar con procesos
            self._arrancar()
            raise ErrorCalculo("El proceso de cálculo se cerró inesperadamente (probablemente se agotó la memoria). "
                               "Prueba con una expresión más sencilla.") from None
        if tipo == "err":
            if val.startswith("MemoryError"):
                self._matar()
                self._arrancar()
                raise ErrorCalculo("Se agotó la memoria disponible para este cálculo. Prueba con una expresión más sencilla.")
            raise ErrorCalculo(f"No pude completar este cálculo ({val}).")
        return val

    def cerrar(self):
        try:
            self.conn.send(None)
        except Exception:  # noqa: BLE001
            pass
        self._matar()


_POOL: "_queue.Queue | None" = None
_TRABAJADORES: list = []
_POOL_LOCK = __import__("threading").Lock()
_SIN_AISLAMIENTO = False


def _obtener_pool():
    global _POOL, _SIN_AISLAMIENTO
    with _POOL_LOCK:
        if _POOL is None and not _SIN_AISLAMIENTO:
            try:
                q = _queue.Queue()
                for _ in range(N_TRABAJADORES):
                    t = _Trabajador()
                    _TRABAJADORES.append(t)
                    q.put(t)
                _POOL = q
                _atexit.register(cerrar_trabajadores)
            except Exception:  # noqa: BLE001  (entorno que no permite crear procesos)
                _SIN_AISLAMIENTO = True
                _POOL = None
        return _POOL


def precalentar():
    """Levanta los procesos trabajadores desde ya (así la primera operación del usuario no espera el arranque)."""
    return _obtener_pool() is not None


def cerrar_trabajadores():
    for t in _TRABAJADORES:
        t.cerrar()
    _TRABAJADORES.clear()


def ejecutar_seguro(nombre, *args, timeout=TIEMPO_POR_DEFECTO, **kwargs):
    """
    Ejecuta OPERACIONES[nombre](*args, **kwargs) en un proceso aparte con tiempo límite.
    SIEMPRE devuelve un dict {"bloques": [...], "datos": {...}}; nunca lanza ni se cuelga.
    """
    import time
    if nombre not in OPERACIONES:
        return res([ER(f"Operación desconocida: {nombre}.")])
    t0 = time.time()
    pool = _obtener_pool()
    if pool is None:                                   # sin procesos: se corre aquí (sin protección contra cuelgues)
        r = OPERACIONES[nombre](*args, **kwargs)
        r.setdefault("datos", {})["_sin_aislamiento"] = True
        return r
    try:
        trabajador = pool.get(timeout=timeout + 15)
    except _queue.Empty:
        return res([AV("El servidor está ocupado con otros cálculos. Inténtalo de nuevo en unos segundos.")], ocupado=True)
    try:
        r = trabajador.correr(nombre, args, kwargs, timeout)
    except ErrorArranque:                      # los procesos no funcionan aquí: se calcula en el mismo proceso
        global _POOL, _SIN_AISLAMIENTO
        _SIN_AISLAMIENTO, _POOL = True, None
        _TRABAJADORES.clear()
        r = OPERACIONES[nombre](*args, **kwargs)
        r.setdefault("datos", {})["_sin_aislamiento"] = True
        return r
    except TiempoAgotado:
        r = res([AV(f"⏱ Este cálculo tardó más de **{timeout} s** y se canceló para no bloquear la aplicación. "
                    "Prueba con una expresión más sencilla, otro punto, o un orden menor.")], timeout=True)
    except ErrorCalculo as e:
        r = res([ER(str(e))])
    except Exception as e:  # noqa: BLE001
        r = res([ER(f"Error inesperado al calcular ({type(e).__name__}).")])
    finally:
        pool.put(trabajador)
    r.setdefault("datos", {})["_tiempo"] = round(time.time() - t0, 2)
    return r
