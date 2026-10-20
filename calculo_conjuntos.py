# calculo_conjuntos.py
"""
calculo_conjuntos.py
====================
Operaciones del motor para lo que el teclado escribe además de funciones:
puntos, vectores, listas, conjuntos (intervalos, regiones de ℝⁿ, bolas), topología, relaciones entre
conjuntos y —en la segunda parte de este archivo— lógica, cuantificadores y argumentos.

Se registran en el mismo registro OPERACIONES que calculo_motor.py (así corren en el proceso aislado).
Punto de entrada para la interfaz: `evaluar_estructura(obj)`.

Honestidad sobre el rigor. Cada conclusión lleva una etiqueta de qué tan firme es:
  · EXACTO        cálculo simbólico (intervalos, bolas…)
  · CRITERIO      criterio suficiente (p. ej. «todas las desigualdades son ≤ ⇒ cerrado»)
  · CONTRAEJEMPLO un punto concreto que refuta la afirmación (verificado exactamente)
  · EVIDENCIA     muestreo numérico (no es una demostración)
"""
from __future__ import annotations

import itertools
import math
import random
from collections import Counter

import numpy as np
import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _clase, _flt, _op, lx, m, res
from estructuras import (
    Angulo, Argumento, Aproximado, Bola, Congruencia, ConjuntoImagen, Cuantificado, Distancia, Divisibilidad, Equivalencia,
    Espacio, Funcion, Lista, Norma, OpTop, Pertenencia, ProdPunto, Punto, Region, RelConj, Vector, a_conjunto, a_region,
    complemento, conjunto_nb, dimension_de, evaluar_nodos, lectura_de, pertenece, variables_por_defecto,
)

_OPS = {sp.Lt: "<", sp.Le: "<=", sp.Gt: ">", sp.Ge: ">=", sp.Eq: "=", sp.Ne: "!="}


def _tipo_op(rel):
    for cls, o in _OPS.items():
        if isinstance(rel, cls):
            return o
    return None


def _n(v, cifras=6):
    f = _flt(v)
    return "—" if f is None else (str(int(round(f))) if abs(f - round(f)) < 1e-9 else f"{f:.{cifras}g}")


def _ltx_region(R) -> str:
    v = sp.latex(R.vars[0]) if R.n == 1 else r"\left(" + ", ".join(sp.latex(x) for x in R.vars) + r"\right)"
    return r"\left\{" + v + r"\ \middle|\ " + sp.latex(R.cond) + r"\right\}"


def _ltx(S) -> str:
    if isinstance(S, Region):
        return _ltx_region(S)
    if isinstance(S, Bola):
        return _ltx_region(S.region())
    if isinstance(S, Espacio):
        return r"\mathbb{R}^{" + sp.latex(S.n) + "}"
    try:
        return sp.latex(S)
    except Exception:  # noqa: BLE001
        return str(S)


# ==============================================================================
# 0. CONDICIONES → CONJUNTOS (una variable)
# ==============================================================================
def resolver_cond(cond, x, base=sp.S.Reals):
    """Conjunto de x ∈ base que cumplen la condición (puede devolver un ConditionSet si no se pudo)."""
    if cond == sp.true:
        return base
    if cond == sp.false:
        return sp.S.EmptySet
    if isinstance(cond, sp.And):
        return sp.Intersection(*[resolver_cond(a, x, base) for a in cond.args])
    if isinstance(cond, sp.Or):
        return sp.Union(*[resolver_cond(a, x, base) for a in cond.args])
    if isinstance(cond, sp.Not):
        return sp.Complement(base, resolver_cond(cond.args[0], x, base))
    if isinstance(cond, sp.Implies):
        return resolver_cond(sp.Or(sp.Not(cond.args[0]), cond.args[1]), x, base)
    if isinstance(cond, sp.Equivalent):
        a, b = cond.args
        return resolver_cond(sp.Or(sp.And(a, b), sp.And(sp.Not(a), sp.Not(b))), x, base)
    if isinstance(cond, sp.Contains):
        if cond.args[0] == x:
            return sp.Intersection(cond.args[1], base)
        raise ErrorCalculo("La pertenencia solo se puede resolver cuando el elemento es la variable misma (x ∈ A).")
    if isinstance(cond, sp.core.relational.Relational):
        sol = sp.solveset(cond, x, sp.S.Reals)
        return sp.Intersection(sol, base) if base != sp.S.Reals else sol
    raise ErrorCalculo("No sé resolver esa condición.")


def _a_set_1d(S):
    """Convierte lo que haya (sympy Set, Region 1D, Bola 1D…) en un sympy Set de ℝ."""
    if isinstance(S, sp.Set):
        return S
    if isinstance(S, Region) and S.n == 1:
        return resolver_cond(S.cond, S.vars[0], S.dominio if S.dominio is not None else sp.S.Reals)
    if isinstance(S, Espacio) and S.dim == 1:
        return sp.S.Reals
    if isinstance(S, ConjuntoImagen):
        return _resolver_imagen(S)[0]
    raise ErrorCalculo("Ese conjunto no es un subconjunto de ℝ.")


def _resolver_imagen(CI: ConjuntoImagen):
    """(conjunto, nota). El conjunto es un ImageSet / Set de SymPy."""
    base = CI.dominio
    if CI.cond is not None:
        base = sp.Intersection(base, resolver_cond(CI.cond, CI.var))
    img = sp.imageset(sp.Lambda(CI.var, CI.expr), base)
    return img, base


# ==============================================================================
# 1. PUNTOS Y VECTORES
# ==============================================================================
def _cuadrante(c):
    xs = [_flt(v) for v in c]
    if any(v is None for v in xs):
        return None
    if len(xs) == 2:
        x, y = xs
        if x == 0 and y == 0:
            return "el origen"
        if x == 0:
            return "sobre el eje y"
        if y == 0:
            return "sobre el eje x"
        return {
            (1, 1): "primer cuadrante",
            (-1, 1): "segundo cuadrante",
            (-1, -1): "tercer cuadrante",
            (1, -1): "cuarto cuadrante",
        }[(1 if x > 0 else -1, 1 if y > 0 else -1)]
    if len(xs) == 3:
        if all(v == 0 for v in xs):
            return "el origen"
        ceros = [n for n, v in zip("xyz", xs) if v == 0]
        if ceros:
            if len(ceros) == 2:
                eje_activo = [n for n, v in zip("xyz", xs) if v != 0][0]
                return "sobre el eje " + eje_activo
            plano_activo = "".join(n for n in "xyz" if n not in ceros)
            return "sobre el plano " + plano_activo
        octante = 1 + (4 if xs[0] < 0 else 0) + (2 if xs[1] < 0 else 0) + (1 if xs[2] < 0 else 0)
        return f"el octante {octante}"
    return None


@_op
def analizar_vectorial(obj):
    """Propiedades de un punto o de un vector."""
    es_p = isinstance(obj, Punto)
    c = obj.c
    n = len(c)
    nombre = "punto" if es_p else "vector"
    b = [
        H(f"El {nombre}"),
        L((r"P=\left(" if es_p else r"\mathbf{v}=\left\langle ") + ", ".join(sp.latex(v) for v in c) + (r"\right)" if es_p else r"\right\rangle")),
        T(f"Vive en **ℝ^{n}** (tiene {n} coordenada" + ("s" if n != 1 else "") + ")."),
    ]
    norma = sp.sqrt(sum(v ** 2 for v in c))
    norma_s = sp.simplify(norma)
    aprox_n = (r"\approx " + sp.latex(sp.N(norma_s, 6))) if not norma_s.is_Integer and not norma_s.free_symbols else ""
    b += [
        H("Distancia al origen" if es_p else "Norma (longitud)"),
        L(r"\|" + ("P" if es_p else r"\mathbf{v}") + r"\|=\sqrt{" + "+".join(sp.latex(v) + "^{2}" for v in c) + "}=" + sp.latex(norma_s) + aprox_n),
    ]
    numerico = not any(v.free_symbols for v in c)
    graf = [{"tipo": "punto" if es_p else "vector", "coords": c, "etiqueta": "P" if es_p else "v"}] if numerico and n in (2, 3) else []
    if es_p:
        q = _cuadrante(c)
        if q:
            b.append(T(f"**Ubicación:** {q}."))
        if n == 2 and numerico and not all(v == 0 for v in c):
            r, th = norma_s, sp.atan2(c[1], c[0])
            b += [
                H("Coordenadas polares"),
                L(
                    r"(r,\theta)=\left(" + sp.latex(r) + r",\," + sp.latex(sp.simplify(th))
                    + r"\right)\approx\left(" + sp.latex(sp.N(r, 5)) + r",\," + sp.latex(sp.N(th, 5)) + r"\right)"
                ),
            ]
        if n == 3 and numerico and not all(v == 0 for v in c):
            rho = sp.sqrt(c[0] ** 2 + c[1] ** 2)
            phi = sp.acos(c[2] / norma_s)
            th = sp.atan2(c[1], c[0])
            b += [
                H("Coordenadas cilíndricas y esféricas"),
                L(r"(\rho,\theta,z)=\left(" + sp.latex(sp.simplify(rho)) + r",\," + sp.latex(sp.simplify(th)) + r",\," + sp.latex(c[2]) + r"\right)"),
                L(r"(r,\theta,\varphi)=\left(" + sp.latex(norma_s) + r",\," + sp.latex(sp.simplify(th)) + r",\," + sp.latex(sp.simplify(phi)) + r"\right)"),
            ]
    else:
        if norma_s == 0:
            b.append(IN("Es el vector cero: no tiene dirección."))
        elif numerico or not norma_s.free_symbols:
            u = [sp.simplify(v / norma_s) for v in c]
            b += [
                H("Vector unitario (misma dirección, longitud 1)"),
                L(r"\hat{\mathbf{v}}=\frac{\mathbf{v}}{\|\mathbf{v}\|}=\left\langle " + ", ".join(sp.latex(v) for v in u) + r"\right\rangle"),
            ]
            if n == 2:
                th = sp.atan2(c[1], c[0])
                b += [
                    H("Dirección"),
                    T("Ángulo con el eje x positivo: $" + sp.latex(sp.simplify(th)) + r"\approx " + _n(th) + "$ rad $= " + _n(th * 180 / sp.pi, 5) + "°$."),
                ]
            if n == 3:
                ang = [sp.acos(v / norma_s) for v in c]
                filas_ang = [
                    [e, "$" + sp.latex(sp.simplify(v / norma_s)) + "$", "$" + _n(a_, 5) + "$ rad = $" + _n(a_ * 180 / sp.pi, 5) + "°$"]
                    for e, v, a_ in zip("xyz", c, ang)
                ]
                b += [
                    H("Cosenos y ángulos directores"),
                    TAB(["eje", "cos", "ángulo"], filas_ang),
                    IN("Se cumple cos²α + cos²β + cos²γ = 1."),
                ]
        b += [H("Opuesto"), L(r"-\mathbf{v}=\left\langle " + ", ".join(sp.latex(-v) for v in c) + r"\right\rangle")]
    if n >= 4:
        b.append(IN(f"Como vive en ℝ^{n}, se pueden calcular sus propiedades pero no dibujarlo."))
    return res(b, elementos=graf)


@_op
def evaluar_vectorial(expr):
    """Evalúa operaciones entre puntos y vectores que dan un número: ‖v‖, u·v, d(p,q), ángulo."""
    nodos = sorted(expr.atoms(Norma, ProdPunto, Distancia, Angulo), key=lambda t: sp.count_ops(t))
    b = []
    graf = []
    for nodo in nodos:
        a = tuple(nodo.args[0])
        c2 = tuple(nodo.args[1]) if len(nodo.args) > 1 else None
        if isinstance(nodo, Norma):
            v = sp.simplify(sp.sqrt(sum(t ** 2 for t in a)))
            aprox_v = (r"\approx " + sp.latex(sp.N(v, 6))) if not v.is_Integer and not v.free_symbols else ""
            b += [
                H("Norma"),
                L(r"\|\mathbf{v}\|=\sqrt{" + "+".join(sp.latex(t) + "^{2}" for t in a) + "}=" + sp.latex(v) + aprox_v),
            ]
            if len(a) in (2, 3) and not any(t.free_symbols for t in a):
                graf.append({"tipo": "vector", "coords": a, "etiqueta": "v"})
        elif isinstance(nodo, ProdPunto):
            if len(a) != len(c2):
                raise ErrorCalculo("Los vectores deben tener la misma dimensión.")
            v = sp.simplify(sum(x * y for x, y in zip(a, c2)))
            terminos_pp = "+".join("(" + sp.latex(x) + ")(" + sp.latex(y) + ")" for x, y in zip(a, c2))
            b += [H("Producto punto"), L(r"\mathbf{u}\cdot\mathbf{v}=" + terminos_pp + "=" + sp.latex(v))]
            if not v.free_symbols:
                nu, nv = sp.sqrt(sum(t ** 2 for t in a)), sp.sqrt(sum(t ** 2 for t in c2))
                if v == 0:
                    b.append(OK("El producto punto es 0: los vectores son **ortogonales** (perpendiculares)."))
                elif nu != 0 and nv != 0:
                    cos = sp.simplify(v / (nu * nv))
                    th = sp.acos(cos)
                    b += [
                        T(
                            r"Ángulo entre ellos: $\cos\theta=\dfrac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}="
                            + sp.latex(cos) + r"$, $\theta\approx " + _n(th * 180 / sp.pi, 5) + "°$."
                        ),
                        T("Proyección escalar de u sobre v: $" + sp.latex(sp.simplify(v / nv)) + "$."),
                    ]
                    if abs(abs(_flt(cos) or 0) - 1) < 1e-12:
                        b.append(IN("Son **paralelos** (cos θ = ±1)."))
                if len(a) in (2, 3):
                    graf += [{"tipo": "vector", "coords": a, "etiqueta": "u"}, {"tipo": "vector", "coords": c2, "etiqueta": "v"}]
        elif isinstance(nodo, Distancia):
            if len(a) != len(c2):
                raise ErrorCalculo("Los puntos deben tener la misma dimensión.")
            v = sp.simplify(sp.sqrt(sum((x - y) ** 2 for x, y in zip(a, c2))))
            aprox_d = (r"\approx " + sp.latex(sp.N(v, 6))) if not v.is_Integer and not v.free_symbols else ""
            terminos_d = "+".join("(" + sp.latex(x) + "-" + sp.latex(y) + ")^{2}" for x, y in zip(a, c2))
            b += [
                H("Distancia entre dos puntos"),
                L(r"d(P,Q)=\sqrt{" + terminos_d + "}=" + sp.latex(v) + aprox_d),
            ]
            if len(a) in (2, 3) and not any(t.free_symbols for t in a + c2):
                graf += [{"tipo": "punto", "coords": a, "etiqueta": "P"}, {"tipo": "punto", "coords": c2, "etiqueta": "Q"}]
        else:
            v = sp.simplify(evaluar_nodos(nodo))
            b += [
                H("Ángulo entre vectores"),
                L(r"\theta=\arccos\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}=" + sp.latex(v) + r"\approx " + sp.latex(sp.N(v * 180 / sp.pi, 5)) + r"^{\circ}"),
            ]
    total = sp.simplify(evaluar_nodos(expr))
    if not (len(nodos) == 1 and expr == nodos[0]):
        b += [H("Resultado de toda la expresión"), L(sp.latex(expr) + "=" + sp.latex(total))]
    aprox_tot = "" if total.is_Integer or total.free_symbols else r"  $\approx " + sp.latex(sp.N(total, 8)) + "$"
    b.append(OK("**Valor:** $" + sp.latex(total) + "$" + aprox_tot))
    return res(b, valor=total, elementos=graf)


# ==============================================================================
# 2. LISTAS
# ==============================================================================
@_op
def analizar_lista(lst):
    """Estadística y patrón de una lista (de números, de puntos o de vectores)."""
    items = lst.items
    b = [
        H("La lista"),
        L(r"\left[" + ", ".join(sp.latex(i) if isinstance(i, sp.Basic) else sp.latex(sp.Tuple(*i.c)) for i in items) + (r", \ldots" if lst.abierta else "") + r"\right]"),
        T(f"Tiene **{len(items)}** elemento(s)" + (" (y sigue indefinidamente)." if lst.abierta else ".")),
    ]
    if lst.simbolica:
        return res(b + [IN("Tiene elementos simbólicos con «…»: no se pueden calcular estadísticos.")])
    if lst.patron:
        tipo, p = lst.patron
        a1 = items[0]
        k = sp.Symbol("n", integer=True, positive=True)
        if tipo == "aritmetica":
            term = sp.simplify(a1 + (k - 1) * p)
            suma = sp.simplify(k * (2 * a1 + (k - 1) * p) / 2)
            b += [
                H("Progresión aritmética"),
                T("Diferencia constante $d=" + sp.latex(p) + "$."),
                L(r"a_n=a_1+(n-1)d=" + sp.latex(term)),
                L(r"S_n=\frac{n(2a_1+(n-1)d)}{2}=" + sp.latex(suma)),
            ]
            if not lst.abierta:
                b.append(T(f"Suma de los {len(items)} términos: $" + sp.latex(sp.simplify(sum(items))) + "$."))
        else:
            term = sp.simplify(a1 * p ** (k - 1))
            b += [
                H("Progresión geométrica"),
                T("Razón constante $r=" + sp.latex(p) + "$."),
                L(r"a_n=a_1r^{n-1}=" + sp.latex(term)),
                L(r"S_n=a_1\frac{r^{n}-1}{r-1}=" + sp.latex(sp.simplify(a1 * (p ** k - 1) / (p - 1)))),
            ]
            if abs(_flt(p) or 2) < 1:
                b.append(OK("Como $|r|<1$, la serie infinita converge a $" + sp.latex(sp.simplify(a1 / (1 - p))) + "$."))
            if not lst.abierta:
                b.append(T(f"Suma de los {len(items)} términos: $" + sp.latex(sp.simplify(sum(items))) + "$."))
    if all(isinstance(i, sp.Expr) for i in items) and items:
        vals = [i for i in items]
        n = len(vals)
        if all(not v.free_symbols for v in vals):
            fl = [float(sp.N(v)) for v in vals]
            media = sum(vals) / n
            ord_ = sorted(vals, key=lambda v: float(sp.N(v)))
            mediana = ord_[n // 2] if n % 2 else (ord_[n // 2 - 1] + ord_[n // 2]) / 2
            var_p = sum((v - media) ** 2 for v in vals) / n
            var_m = (sum((v - media) ** 2 for v in vals) / (n - 1)) if n > 1 else None
            cont = Counter(vals)
            mx = max(cont.values())
            moda = [k_m for k_m, v_m in cont.items() if v_m == mx] if mx > 1 else []
            filas = [
                ["Suma", "$" + sp.latex(sum(vals)) + "$"],
                ["Producto", "$" + sp.latex(sp.simplify(sp.Mul(*vals))) + "$"],
                ["Media (promedio)", "$" + sp.latex(sp.simplify(media)) + "$ ≈ " + _n(media)],
                ["Mediana", "$" + sp.latex(mediana) + "$"],
                ["Moda", ", ".join("$" + sp.latex(k_m) + "$" for k_m in moda) if moda else "no hay (ningún valor se repite)"],
                ["Mínimo / Máximo", "$" + sp.latex(ord_[0]) + "$ / $" + sp.latex(ord_[-1]) + "$"],
                ["Rango", "$" + sp.latex(sp.simplify(ord_[-1] - ord_[0])) + "$"],
                ["Varianza poblacional σ²", "$" + sp.latex(sp.simplify(var_p)) + "$ ≈ " + _n(var_p)],
            ]
            if var_m is not None:
                filas += [
                    ["Varianza muestral s²", "$" + sp.latex(sp.simplify(var_m)) + "$ ≈ " + _n(var_m)],
                    ["Desviación estándar σ / s", f"{_n(sp.sqrt(var_p))} / {_n(sp.sqrt(var_m))}"],
                ]
            b += [
                H("Estadísticos"),
                TAB(["medida", "valor"], filas),
                T("Ordenada: " + ", ".join("$" + sp.latex(v) + "$" for v in ord_)),
            ]
            return res(b, valores=fl)
    elif items and all(isinstance(i, (Punto, Vector)) for i in items):
        n = items[0].n
        if any(i.n != n for i in items):
            raise ErrorCalculo("Todos los elementos deben tener la misma dimensión.")
        if all(isinstance(i, Punto) for i in items):
            cen = [sp.simplify(sum(i.c[k_i] for i in items) / len(items)) for k_i in range(n)]
            b += [H("Puntos"), T("**Centroide** (promedio de las coordenadas): $(" + ", ".join(sp.latex(v) for v in cen) + ")$.")]
            if len(items) >= 2:
                long = sum(sp.sqrt(sum((a - c) ** 2 for a, c in zip(p.c, q.c))) for p, q in zip(items[:-1], items[1:]))
                b.append(T("Longitud de la poligonal que los une en orden: $" + sp.latex(sp.simplify(long)) + r"\approx " + _n(long) + "$."))
            if len(items) <= 6:
                filas = [
                    [
                        f"P{i + 1}–P{j + 1}",
                        "$" + sp.latex(sp.simplify(sp.sqrt(sum((a - c) ** 2 for a, c in zip(items[i].c, items[j].c))))) + "$",
                    ]
                    for i in range(len(items))
                    for j in range(i + 1, len(items))
                ]
                b += [H("Distancias entre pares"), TAB(["par", "distancia"], filas)]
            if n in (2, 3):
                return res(b, elementos=[{"tipo": "punto", "coords": p.c, "etiqueta": f"P{i + 1}"} for i, p in enumerate(items)])
        else:
            Mtx = sp.Matrix([list(v.c) for v in items])
            rango = Mtx.rank()
            b += [
                H("Vectores"),
                T(
                    f"**Rango:** {rango}. Los {len(items)} vectores son "
                    + ("**linealmente independientes**." if rango == len(items) else "**linealmente dependientes** (alguno es combinación de los otros).")
                ),
            ]
            G = sp.Matrix(len(items), len(items), lambda i, j: sum(a * c for a, c in zip(items[i].c, items[j].c)))
            b += [H("Matriz de productos punto (Gram)"), L(sp.latex(G))]
            ortog = all(G[i, j] == 0 for i in range(len(items)) for j in range(len(items)) if i != j)
            if ortog:
                b.append(OK(
                    "Son **ortogonales** entre sí"
                    + (" y además **unitarios**: forman un conjunto ortonormal." if all(G[i, i] == 1 for i in range(len(items))) else ".")
                ))
            if n in (2, 3):
                return res(b, elementos=[{"tipo": "vector", "coords": v.c, "etiqueta": f"v{i + 1}"} for i, v in enumerate(items)])
    return res(b)


# ==============================================================================
# 3. CONJUNTOS DE ℝ (exacto con SymPy)
# ==============================================================================
def _info_1d(S) -> dict:
    """Propiedades de un subconjunto de ℝ. Valores: True/False/None(no se sabe) y conjuntos de SymPy."""
    P: dict = {"S": S, "notas": []}
    oo = sp.oo
    if S == sp.S.EmptySet:
        P.update(abierto=True, cerrado=True, acotado=True, interior=S, cierre=S, frontera=S, derivado=S, aislados=S, inf=None, sup=None,
                 medida=0, cardinal="0 (vacío)", conexo=True)
    elif S in (sp.S.Naturals, sp.S.Naturals0, sp.S.Integers):
        inf = sp.sympify({sp.S.Naturals: 1, sp.S.Naturals0: 0, sp.S.Integers: -oo}[S])
        P.update(abierto=False, cerrado=True, acotado=False, interior=sp.S.EmptySet, cierre=S, frontera=S, derivado=sp.S.EmptySet, aislados=S,
                 inf=inf, sup=oo, medida=0, cardinal="infinito numerable", conexo=False)
    elif S == sp.S.Rationals:
        P.update(abierto=False, cerrado=False, acotado=False, interior=sp.S.EmptySet, cierre=sp.S.Reals, frontera=sp.S.Reals, derivado=sp.S.Reals,
                 aislados=sp.S.EmptySet, inf=-oo, sup=oo, medida=0, cardinal="infinito numerable", conexo=False)
        P["notas"].append("ℚ es denso en ℝ: entre dos reales siempre hay racionales, por eso su cerradura es todo ℝ y su interior es vacío.")
    elif S == sp.S.Reals:
        P.update(abierto=True, cerrado=True, acotado=False, interior=S, cierre=S, frontera=sp.S.EmptySet, derivado=S, aislados=sp.S.EmptySet,
                 inf=-oo, sup=oo, medida=oo, cardinal="no numerable (continuo)", conexo=True)
    else:
        try:
            S = S.simplify() if hasattr(S, "simplify") else S
        except Exception:  # noqa: BLE001
            pass
        P["S"] = S
        try:
            interior, cierre, frontera = S.interior, S.closure, S.boundary
            P.update(interior=interior, cierre=cierre, frontera=frontera, abierto=(S == interior), cerrado=(S == cierre))
        except Exception:  # noqa: BLE001
            P.update(interior=None, cierre=None, frontera=None, abierto=None, cerrado=None)
        try:
            inf, sup = S.inf, S.sup
            P.update(inf=inf, sup=sup, acotado=bool(inf.is_finite and sup.is_finite))
        except Exception:  # noqa: BLE001
            P.update(inf=None, sup=None, acotado=None)
        try:
            P["medida"] = S.measure
        except Exception:  # noqa: BLE001
            P["medida"] = None
        partes = list(S.args) if isinstance(S, sp.Union) else [S]
        ints = [t for t in partes if isinstance(t, sp.Interval)]
        pts = [t for t in partes if isinstance(t, sp.FiniteSet)]
        if all(isinstance(t, (sp.Interval, sp.FiniteSet)) for t in partes):
            deg = [i for i in ints if i.start != i.end]
            P["derivado"] = sp.Union(*[sp.Interval(i.start, i.end) for i in deg]) if deg else sp.S.EmptySet
            aisl = [p for f in pts for p in f.args if not P["derivado"].contains(p) == True]  # noqa: E712
            P["aislados"] = sp.FiniteSet(*aisl)
            P["cardinal"] = ("no numerable (continuo)" if deg else (f"{sum(len(f.args) for f in pts)} elemento(s)"))
            P["conexo"] = (len(partes) == 1 and (not pts or len(pts[0].args) <= 1))
        else:
            P.update(derivado=None, aislados=None, cardinal=None, conexo=None)
    if P.get("acotado") is not None and P.get("cerrado") is not None:
        P["compacto"] = bool(P["acotado"] and P["cerrado"])
    else:
        P["compacto"] = None
    return P


def _sn(v):
    return "sí" if v is True else "no" if v is False else "no se pudo determinar"


def _bloques_1d(S, nombre="A") -> tuple:
    P = _info_1d(S)
    S = P["S"]
    b = [H("El conjunto"), L(nombre + "=" + _ltx(S))]
    filas = []

    def fila(prop, val, porque=""):
        filas.append([prop, val, porque])

    fila("¿Abierto?", _sn(P["abierto"]), "coincide con su interior" if P["abierto"] else "tiene puntos de frontera que le pertenecen" if P["abierto"] is False else "")
    fila("¿Cerrado?", _sn(P["cerrado"]), "contiene toda su frontera" if P["cerrado"] else "le falta algún punto de su frontera" if P["cerrado"] is False else "")
    fila("¿Acotado?", _sn(P["acotado"]), "" if P["acotado"] is None else ("cabe en un intervalo finito" if P["acotado"] else "se extiende sin límite"))
    fila("¿Compacto?", _sn(P["compacto"]), "compacto = cerrado y acotado (Heine–Borel)")
    fila("¿Conexo?", _sn(P["conexo"]), "")
    for et, k in (("Interior", "interior"), ("Cerradura", "cierre"), ("Frontera", "frontera"), ("Puntos de acumulación", "derivado"), ("Puntos aislados", "aislados")):
        v = P.get(k)
        fila(et, "no se pudo calcular" if v is None else "$" + sp.latex(v) + "$")
    if P.get("inf") is not None:
        inf, sup = P["inf"], P["sup"]
        fila("Ínfimo", "$" + sp.latex(inf) + "$")
        fila("Supremo", "$" + sp.latex(sup) + "$")
        mn = inf if (inf.is_finite and S.contains(inf) == True) else None  # noqa: E712
        mx = sup if (sup.is_finite and S.contains(sup) == True) else None  # noqa: E712
        fila("Mínimo", ("$" + sp.latex(mn) + "$") if mn is not None else "no existe", "el ínfimo pertenece al conjunto" if mn is not None else "")
        fila("Máximo", ("$" + sp.latex(mx) + "$") if mx is not None else "no existe", "el supremo pertenece al conjunto" if mx is not None else "")
    if P.get("medida") is not None:
        fila("Medida (longitud)", "$" + sp.latex(P["medida"]) + "$")
    if P.get("cardinal"):
        fila("Cardinal", P["cardinal"])
    b += [H("Propiedades"), TAB(["propiedad", "valor", "por qué"], filas)]
    b += [IN(n_) for n_ in P["notas"]]
    b.append(IN("Rigor: **exacto** (cálculo simbólico con conjuntos de ℝ)."))
    return b, P


# ==============================================================================
# 4. BOLAS (fórmulas exactas) Y REGIONES DE ℝⁿ (criterios)
# ==============================================================================
def _volumen_bola(n, r):
    return sp.simplify(sp.pi ** sp.Rational(n, 2) / sp.gamma(sp.Rational(n, 2) + 1) * r ** n)


def _bloques_bola(B: Bola) -> tuple:
    n, r, c = B.n, B.radio, B.centro
    nombre = "esfera" if B.esfera else "bola cerrada" if B.cerrada else "bola abierta"
    b = [
        H(f"La {nombre}"),
        L(_ltx_region(B.region())),
        T(
            "Centro $" + sp.latex(sp.Tuple(*c.c)).replace(r"\left(", "(").replace(r"\right)", ")")
            + "$, radio $" + sp.latex(r) + f"$, en ℝ^{n}. Los puntos se miden con la distancia euclidiana."
        ),
    ]
    tabla = [
        ["¿Abierta?", "no" if (B.cerrada or B.esfera) else "sí", "toda bola abierta es un conjunto abierto"],
        ["¿Cerrada?", "sí" if (B.cerrada or B.esfera) else "no", "contiene todo su borde" if B.cerrada or B.esfera else "no contiene su borde (la esfera)"],
        ["¿Acotada?", "sí", "está contenida en la bola de radio ‖c‖+r"],
        ["¿Compacta?", "sí" if (B.cerrada or B.esfera) else "no", "cerrada y acotada (Heine–Borel)" if (B.cerrada or B.esfera) else "no es cerrada"],
        ["¿Conexa?", "sí" if not B.esfera or n >= 2 else "no", ""],
        ["¿Convexa?", "no" if B.esfera else "sí", "el segmento entre dos puntos queda dentro" if not B.esfera else ""],
        ["Diámetro", "$" + sp.latex(2 * r) + "$", "2r"],
    ]
    if B.esfera:
        tabla += [["Interior", r"$\varnothing$", "la esfera no tiene puntos interiores"], ["Cerradura", "ella misma", ""], ["Frontera", "ella misma", ""]]
    else:
        tabla += [["Interior", "la bola abierta", ""], ["Cerradura", "la bola cerrada", ""], ["Frontera", "la esfera de radio r", "puntos con ‖p − c‖ = r"]]
    b += [H("Propiedades"), TAB(["propiedad", "valor", "por qué"], tabla)]
    if n >= 1:
        vol = _volumen_bola(n, r)
        sup = sp.simplify(n * vol / r) if r != 0 else 0
        etiquetas = {1: ("longitud", "longitud de la frontera"), 2: ("área", "perímetro (circunferencia)"), 3: ("volumen", "área de la superficie")}
        et = etiquetas.get(n, (f"volumen {n}-dimensional", "medida de la frontera"))
        b += [
            H("Tamaño"),
            L(r"V_{" + str(n) + r"}=\frac{\pi^{n/2}}{\Gamma\left(\frac{n}{2}+1\right)}r^{n}=" + sp.latex(vol)),
            T(
                et[0].capitalize() + " de la bola: $" + sp.latex(vol) + r"\approx " + _n(vol)
                + "$; " + et[1] + ": $" + sp.latex(sp.simplify(sup)) + r"\approx " + _n(sup) + "$."
            ),
        ]
    b.append(IN("Rigor: **exacto** (propiedades de la bola euclidiana)."))
    return b, {"bola": B}


def _lambdify_cond(R):
    try:
        f = sp.lambdify(R.vars, R.cond, modules=["numpy"])
    except Exception:  # noqa: BLE001
        return None

    def g(*cols):
        with np.errstate(all="ignore"):
            out = f(*cols)
        return np.broadcast_to(np.asarray(out, dtype=bool), cols[0].shape)
    return g


def _conjunciones(cond):
    if sp.count_ops(cond) > 300:
        raise ErrorCalculo("La condición es demasiado larga para analizar su topología por desigualdades.")
    d = sp.to_dnf(cond, simplify=False)
    out = []
    for c in (d.args if isinstance(d, sp.Or) else [d]):
        if c == sp.false:
            continue
        if c == sp.true:
            out.append([])
            continue
        atoms = []
        for a in (c.args if isinstance(c, sp.And) else [c]):
            op = _tipo_op(a) if isinstance(a, sp.core.relational.Relational) else None
            if op is None:
                if a == sp.true:
                    continue
                raise ErrorCalculo(
                    "Esta región usa una condición que no es una desigualdad entre expresiones (por ejemplo una pertenencia a ℕ "
                    "en ℝⁿ): su topología no se puede analizar con este criterio."
                )
            atoms.append((a.lhs - a.rhs, op))
        out.append(atoms)
    return out


def _cond_de(conjs, modo):
    """modo 'cierre' (estrictas→no estrictas; ≠ se quita) o 'interior' (no estrictas→estrictas; = vacía)."""
    out = []
    for c in conjs:
        if modo == "interior" and any(op == "=" for _, op in c):
            continue
        at = []
        for g, op in c:
            if modo == "cierre":
                if op == "<":
                    at.append(sp.Le(g, 0))
                elif op == ">":
                    at.append(sp.Ge(g, 0))
                elif op != "!=":
                    at.append(_rel_de(g, op))
            else:
                at.append(sp.Lt(g, 0) if op in ("<", "<=") else sp.Gt(g, 0) if op in (">", ">=") else sp.Ne(g, 0))
        out.append(sp.And(*at) if at else sp.true)
    return sp.Or(*out) if out else sp.false


def _rel_de(g, op):
    return {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge, "=": sp.Eq, "!=": sp.Ne}[op](g, 0)


def _ventana_region(R, B=12.0):
    return B


def _acotacion(R):
    """(veredicto, detalle, caja). veredicto: 'no' (hay un testigo lejano), 'prob' (no se encontró ninguno) o None."""
    f = _lambdify_cond(R)
    if f is None:
        return None, "no se pudo evaluar la condición numéricamente", None
    n = R.n
    rng = np.random.default_rng(7)
    for Rr in (10.0, 100.0, 1e3, 1e4, 1e6):
        dirs = (
            [np.eye(n)[i] * s for i in range(n) for s in (1, -1)]
            + [np.array(s) / np.sqrt(n) for s in itertools.product([1, -1], repeat=min(n, 4))]
            + [v / np.linalg.norm(v) for v in rng.normal(size=(150, n))]
        )
        P = np.array(dirs) * Rr
        cols = [P[:, i] for i in range(n)]
        try:
            ok = f(*cols)
        except Exception:  # noqa: BLE001
            return None, "no se pudo evaluar la condición numéricamente", None
        if ok.any():
            i = int(np.argmax(ok))
            return "no", f"contiene puntos arbitrariamente lejanos, por ejemplo cerca de {tuple(float(f'{v:.4g}') for v in P[i])}", None
    return "prob", "no se encontró ningún punto lejano del origen (hasta distancia 10⁶)", None


def _montecarlo(R, B=12.0, N=240_000):
    """(fracción, caja de puntos dentro, error estándar) en [−B, B]ⁿ; None si no se pudo evaluar."""
    f = _lambdify_cond(R)
    if f is None:
        return None
    n = R.n
    rng = np.random.default_rng(11)
    P = rng.uniform(-B, B, size=(N, n))
    try:
        ok = f(*[P[:, i] for i in range(n)])
    except Exception:  # noqa: BLE001
        return None
    if not ok.any():
        return 0.0, None, 0.0, False
    dentro = P[ok]
    caja = (dentro.min(axis=0), dentro.max(axis=0))
    toca_borde = bool((np.abs(caja[0]) > 0.98 * B).any() or (np.abs(caja[1]) > 0.98 * B).any())
    p = ok.mean()
    return float(p), caja, float(math.sqrt(p * (1 - p) / N)), toca_borde


def _regularidad(conjs, vars_):
    """Puntos donde g = 0 y ∇g = 0 (la frontera puede no ser {g = 0} ahí)."""
    malos = []
    for c in conjs:
        for g, op in c:
            if op == "!=" or sp.count_ops(g) > 60 or len(vars_) > 3:
                continue
            try:
                sols = sp.solve([g] + [sp.diff(g, v) for v in vars_], list(vars_), dict=True)
            except Exception:  # noqa: BLE001
                continue
            for s in sols:
                if len(s) == len(vars_) and all(v.is_real is not False and not v.has(sp.I) for v in s.values()):
                    malos.append(tuple(sp.simplify(s[v]) for v in vars_))
    return malos[:3]


def _bloques_region(R: Region) -> tuple:
    n = R.n
    b = [H("El conjunto"), L(_ltx_region(R)), T(f"Vive en **ℝ^{n}**.")]
    datos = {"region": R}
    if R.puntos:
        pts = R.puntos
        b += [
            H("Conjunto finito de puntos"),
            T(f"Tiene **{len(pts)}** punto(s): " + ", ".join(p.txt() for p in pts) + "."),
            TAB(
                ["propiedad", "valor"],
                [
                    ["¿Abierto?", "no (a menos que sea vacío)"],
                    ["¿Cerrado?", "sí (todo conjunto finito es cerrado)"],
                    ["¿Acotado?", "sí"],
                    ["¿Compacto?", "sí"],
                    ["Interior", "vacío"],
                    ["Frontera", "él mismo (todos sus puntos son aislados)"],
                    ["Puntos de acumulación", "ninguno"],
                ],
            ),
            IN("Rigor: **exacto**."),
        ]
        return b, datos
    try:
        conjs = _conjunciones(R.cond)
    except ErrorCalculo as e:
        return b + [AV(str(e))], datos
    filas = []
    if not conjs:
        filas += [["¿Abierto?", "sí", "es el conjunto vacío"], ["¿Cerrado?", "sí", "es el conjunto vacío"]]
        b += [H("Propiedades"), TAB(["propiedad", "valor", "por qué"], filas), IN("La condición no la cumple ningún punto: el conjunto es **vacío**.")]
        return b, datos
    if any(len(c) == 0 for c in conjs):
        b += [
            H("Propiedades"),
            TAB(["propiedad", "valor"], [["¿Abierto?", "sí"], ["¿Cerrado?", "sí"], ["¿Acotado?", "no"]]),
            IN("La condición siempre se cumple: es todo ℝⁿ."),
        ]
        return b, datos
    ops = [op for c in conjs for _, op in c]
    abierto, cerrado = all(o in ("<", ">", "!=") for o in ops), all(o in ("<=", ">=", "=") for o in ops)
    cierre, interior = _cond_de(conjs, "cierre"), _cond_de(conjs, "interior")
    frontera = sp.And(cierre, sp.Not(interior))
    veredicto, detalle, _ = _acotacion(R)
    mc = _montecarlo(R)
    acotado_txt = "no" if veredicto == "no" else "probablemente sí (evidencia)" if veredicto == "prob" else "no se pudo determinar"
    compacto = (
        "no" if (veredicto == "no" or (not cerrado and not abierto))
        else ("probablemente sí (cerrado y, según el muestreo, acotado)" if (cerrado and veredicto == "prob") else "no (no es cerrado)" if abierto else "no se pudo determinar")
    )
    if abierto and cerrado:
        a_txt = c_txt = "sí"
    else:
        a_txt = "**sí**" if abierto else "no se puede asegurar (mezcla desigualdades estrictas y no estrictas)" if not cerrado else "no (tiene puntos de su frontera)"
        c_txt = "**sí**" if cerrado else "no se puede asegurar (mezcla desigualdades estrictas y no estrictas)" if not abierto else "no (le faltan puntos de su frontera)"
    filas = [
        ["¿Abierto?", a_txt, "todas las desigualdades son estrictas (< > ≠)" if abierto else ""],
        ["¿Cerrado?", c_txt, "todas son no estrictas o igualdades (≤ ≥ =)" if cerrado else ""],
        ["¿Acotado?", acotado_txt, detalle],
        ["¿Compacto?", compacto, "compacto = cerrado y acotado"],
    ]
    b += [H("Propiedades"), TAB(["propiedad", "valor", "por qué"], filas)]
    ri = Region(R.vars, interior, "el interior (criterio)")
    rc = Region(R.vars, cierre, "la cerradura (criterio)")
    rf = Region(R.vars, frontera, "la frontera (criterio)")
    b += [
        H("Interior, cerradura y frontera (por el criterio de regularidad)"),
        T("Se obtienen **cambiando** las desigualdades: interior = estrictas (las igualdades lo vacían); cerradura = no estrictas; frontera = cerradura menos interior."),
        T("**Interior:**"), L(_ltx_region(ri)),
        T("**Cerradura:**"), L(_ltx_region(rc)),
        T("**Frontera:**"), L(_ltx_region(rf)),
    ]
    malos = _regularidad(conjs, R.vars)
    if malos:
        b.append(AV(
            r"⚠️ **Criterio no confiable en algunos puntos:** donde $g=0$ y $\nabla g=0$ a la vez (por ejemplo en "
            + ", ".join("$" + sp.latex(sp.Tuple(*p)) + "$" for p in malos)
            + ") la frontera real puede ser distinta de la que se calculó."
        ))
    else:
        b.append(IN(r"Se comprobó que en ningún punto $g=0$ y $\nabla g=0$ a la vez: el criterio de regularidad aplica."))
    if mc is not None:
        p, caja, se, toca = mc
        if caja is not None and not toca and n in (1, 2, 3):
            vol_caja = (2 * 12.0) ** n
            est = p * vol_caja
            nombre = {1: "longitud", 2: "área", 3: "volumen"}[n]
            b += [
                H("Tamaño (estimación numérica)"),
                T(f"{nombre.capitalize()} ≈ **{est:.4g}** (± {2 * se * vol_caja:.2g}) por muestreo aleatorio (Monte Carlo)."),
                T("Caja envolvente: " + " × ".join(f"[{lo:.3g}, {hi:.3g}]" for lo, hi in zip(*caja)) + "."),
                IN("Rigor: **evidencia** (muestreo), no un cálculo exacto."),
            ]
        elif toca:
            b.append(IN("El conjunto llega al borde de la ventana de muestreo [−12, 12]ⁿ: probablemente es no acotado o muy grande, así que no se estima su tamaño."))
    b.append(IN(
        "Rigor: abierto/cerrado por **criterio suficiente**; interior/cerradura/frontera por **criterio de regularidad**; acotación por **muestreo** "
        "(si hay un punto lejano encontrado, «no acotado» es seguro)."
    ))
    datos["interior"], datos["cierre"], datos["frontera"] = ri, rc, rf
    return b, datos


# ==============================================================================
# 5. CANONIZAR, ANALIZAR Y CLASIFICAR PUNTOS
# ==============================================================================
def _canon(S):
    if isinstance(S, OpTop):
        return aplicar_optop(S)
    if isinstance(S, ConjuntoImagen):
        return _canon_imagen(S)
    if isinstance(S, Region) and S.n == 1:
        return _a_set_1d(S)
    if isinstance(S, Espacio) and S.dim == 1:
        return sp.S.Reals
    return S


def _canon_imagen(CI: ConjuntoImagen):
    img, _ = _resolver_imagen(CI)
    return img


def aplicar_optop(op: OpTop):
    """Resultado de int / cl / Fr / ext / diam aplicado a un conjunto (otro conjunto, o un número para diam)."""
    S = _canon(op.conjunto)
    nombre = op.nombre
    if isinstance(S, Bola):
        c, r = S.centro, S.radio
        if nombre == "int":
            return sp.S.EmptySet if S.esfera else Bola(c, r, False, False)
        if nombre == "cl":
            return Bola(c, r, True, S.esfera)
        if nombre == "Fr":
            return Bola(c, r, False, True)
        if nombre == "ext":
            return complemento(Bola(c, r, True, S.esfera))
        return 2 * r
    if isinstance(S, Espacio) or S == sp.S.Complexes:
        return {"int": S, "cl": S, "Fr": sp.S.EmptySet, "ext": sp.S.EmptySet}.get(nombre, sp.oo)
    if isinstance(S, sp.Set):
        P = _info_1d(S)
        if nombre == "int":
            return P["interior"] if P.get("interior") is not None else S
        if nombre == "cl":
            return P["cierre"] if P.get("cierre") is not None else S
        if nombre == "Fr":
            return P["frontera"] if P.get("frontera") is not None else S
        if nombre == "ext":
            return sp.Complement(sp.S.Reals, P["cierre"])
        if P.get("inf") is not None and P["acotado"]:
            return sp.simplify(P["sup"] - P["inf"])
        return sp.oo
    if isinstance(S, Region):
        if nombre == "diam":
            v, _, _ = _acotacion(S)
            if v == "no":
                return sp.oo
            raise ErrorCalculo("El diámetro de una región general no se puede calcular de forma exacta; para bolas e intervalos sí.")
        conjs = _conjunciones(S.cond)
        cierre, interior = _cond_de(conjs, "cierre"), _cond_de(conjs, "interior")
        cond = {"int": interior, "cl": cierre, "Fr": sp.And(cierre, sp.Not(interior)), "ext": sp.Not(cierre)}[nombre]
        pref = {"int": "el interior", "cl": "la cerradura", "Fr": "la frontera", "ext": "el exterior"}[nombre]
        return Region(S.vars, cond, f"{pref} de {lectura_de(op.conjunto)} (por criterio)")
    raise ErrorCalculo("No sé aplicar ese operador a este conjunto.")


def _bloques_conjunto(S, nombre="A") -> tuple:
    S = _canon(S)
    if isinstance(S, Bola):
        return _bloques_bola(S)
    if S == sp.S.Complexes:
        return [
            H("El cuerpo de los números complejos"),
            L(r"\mathbb{C}=\{a+bi : a,b\in\mathbb{R}\}"),
            TAB(
                ["propiedad", "valor"],
                [
                    ["¿Abierto?", "sí"],
                    ["¿Cerrado?", "sí"],
                    ["¿Acotado?", "no"],
                    ["¿Compacto?", "no"],
                    ["¿Conexo?", "sí"],
                    ["Frontera", "vacía"],
                    ["Dimensión sobre ℝ", "$2$ (isomorfo a $\\mathbb{R}^2$)"],
                ],
            ),
            IN("Rigor: **exacto**. Como espacio métrico, ℂ se identifica con el plano euclidiano ℝ²."),
        ], {}
    if isinstance(S, Espacio):
        n = S.n
        return [
            H("El espacio"),
            L(r"\mathbb{R}^{" + sp.latex(n) + "}"),
            TAB(
                ["propiedad", "valor"],
                [
                    ["¿Abierto?", "sí"],
                    ["¿Cerrado?", "sí"],
                    ["¿Acotado?", "no"],
                    ["¿Compacto?", "no"],
                    ["¿Conexo?", "sí"],
                    ["Frontera", "vacía"],
                    ["Dimensión", "$" + sp.latex(n) + "$"],
                ],
            ),
            IN("Rigor: **exacto**. ℝⁿ es el único conjunto (junto con ∅) que es abierto y cerrado a la vez."),
        ], {}
    if isinstance(S, Region):
        return _bloques_region(S)
    if isinstance(S, sp.Set):
        return _bloques_1d(S, nombre)
    raise ErrorCalculo("No sé analizar ese conjunto.")


@_op
def analizar_conjunto(obj):
    """Descripción y topología de un conjunto (intervalos, regiones, bolas, ℝⁿ, imágenes y operadores topológicos)."""
    b = []
    if isinstance(obj, OpTop):
        S0 = _canon(obj.conjunto)
        r = aplicar_optop(obj)
        nombres = {"int": "El interior", "cl": "La cerradura", "Fr": "La frontera", "ext": "El exterior", "diam": "El diámetro"}
        b += [H(nombres[obj.nombre] + " del conjunto"), T("Conjunto original:"), L(_ltx(S0))]
        if obj.nombre == "diam":
            b += [L(r"\operatorname{diam}=" + sp.latex(r)), OK("**Diámetro:** $" + sp.latex(r) + "$ (la mayor distancia entre dos puntos del conjunto).")]
            return res(b, valor=r, conjunto=S0)
        b += [T(f"{nombres[obj.nombre]} es:"), L(_ltx(r))]
        bl, datos = _bloques_conjunto(r, "B")
        return res(b + [H("Propiedades del resultado")] + bl, conjunto=r, original=S0, **{k: v for k, v in datos.items() if k not in ("conjunto",)})
    if isinstance(obj, ConjuntoImagen):
        S0, base = _resolver_imagen(obj)
        b += [
            H("Conjunto de valores"),
            T("Los valores $" + sp.latex(obj.expr) + "$ con $" + sp.latex(obj.var) + r"\in" + sp.latex(base) + "$:"),
            L(sp.latex(S0)),
        ]
        f = obj.expr
        if base in (sp.S.Naturals, sp.S.Naturals0, sp.S.Integers):
            n_ = obj.var
            Lp = M.lim(f, n_, sp.oo)
            Lm = M.lim(f, n_, -sp.oo) if base == sp.S.Integers else None
            tiende = [v for v in (Lp, Lm) if v is not None and _clase(v) == "fin"]
            primeros = []
            for k in range(0 if base != sp.S.Naturals else 1, (0 if base != sp.S.Naturals else 1) + 8):
                primeros.append(sp.simplify(f.subs(n_, k)))
            if base == sp.S.Integers:
                primeros = sorted({sp.simplify(f.subs(n_, k)) for k in range(-4, 5)}, key=lambda v: float(sp.N(v)))
            b.append(T("Primeros valores: " + ", ".join("$" + sp.latex(v) + "$" for v in primeros) + ", …"))
            if tiende:
                lim_ = tiende[0]
                b += [
                    OK(
                        "Los valores se **acumulan** en $" + sp.latex(lim_)
                        + "$ (el límite de la expresión): ese número es un punto de acumulación y **no pertenece** al conjunto (salvo que algún término lo valga)."
                    ),
                    TAB(
                        ["propiedad", "valor"],
                        [
                            ["¿Cerrado?", "no (le falta el punto de acumulación)"],
                            ["¿Abierto?", "no"],
                            ["Interior", "vacío"],
                            ["Puntos de acumulación", "$" + sp.latex(lim_) + "$"],
                            ["Cerradura", "el conjunto junto con ese punto"],
                            ["¿Acotado?", "sí"],
                        ],
                    ),
                ]
            elif Lp is not None and _clase(Lp) in ("+oo", "-oo"):
                b += [
                    OK("Los valores **se alejan** sin límite: el conjunto es **discreto**: no tiene puntos de acumulación."),
                    TAB(
                        ["propiedad", "valor"],
                        [
                            ["¿Cerrado?", "sí (sin puntos de acumulación)"],
                            ["¿Abierto?", "no"],
                            ["Interior", "vacío"],
                            ["Frontera", "él mismo"],
                            ["¿Acotado?", "no"],
                            ["Cardinal", "infinito numerable"],
                        ],
                    ),
                ]
        return res(b, conjunto=S0)
    bl, datos = _bloques_conjunto(obj)
    return res(bl, conjunto=_canon(obj), **{k: v for k, v in datos.items() if k != "S"}) if isinstance(datos, dict) else res(bl)


def _signo_exacto(v):
    v = sp.simplify(v)
    if v.is_zero:
        return 0
    if v.is_positive:
        return 1
    if v.is_negative:
        return -1
    f = _flt(v)
    return None if f is None else (0 if abs(f) < 1e-12 else 1 if f > 0 else -1)


@_op
def clasificar_punto(S, p):
    """¿El punto p es interior, de frontera o exterior al conjunto S? (con la explicación)."""
    S = _canon(S)
    pt = p if isinstance(p, Punto) else Punto((p,)) if isinstance(p, sp.Expr) else Punto(p.c) if isinstance(p, Vector) else None
    if pt is None:
        raise ErrorCalculo("Escribe un punto con coordenadas numéricas.")
    ltx_pt = sp.latex(sp.Tuple(*pt.c)) if pt.n > 1 else sp.latex(pt.c[0])
    b = [H("El punto y el conjunto"), T("Punto $p=" + ltx_pt + "$.")]
    pos, rigor, expl, pertenece_ = None, "exacto", [], None
    if isinstance(S, sp.Set):
        if pt.n != 1:
            raise ErrorCalculo(f"El conjunto es un subconjunto de ℝ (1 coordenada) y el punto tiene {pt.n}.")
        x0 = pt.c[0]
        P = _info_1d(S)
        pertenece_ = S.contains(x0) == True  # noqa: E712
        en_int = P["interior"] is not None and P["interior"].contains(x0) == True  # noqa: E712
        en_cl = P["cierre"] is not None and P["cierre"].contains(x0) == True  # noqa: E712
        pos = "interior" if en_int else "frontera" if en_cl else "exterior"
        acum = P.get("derivado") is not None and P["derivado"].contains(x0) == True  # noqa: E712
        aislado = pertenece_ and not acum
        expl += [
            "Interior del conjunto: $" + sp.latex(P["interior"]) + f"$ → {'contiene' if en_int else 'no contiene'} a $p$.",
            "Cerradura: $" + sp.latex(P["cierre"]) + f"$ → {'contiene' if en_cl else 'no contiene'} a $p$.",
        ]
        b.append(L(sp.latex(S)))
        extra = "**Punto de acumulación:** " + ("sí" if acum else "no") + ". " + ("Además es un **punto aislado** del conjunto." if aislado else "")
    elif isinstance(S, Bola):
        if pt.n != S.n:
            raise ErrorCalculo(f"La bola vive en ℝ^{S.n} y el punto tiene {pt.n} coordenada(s).")
        d = sp.simplify(sp.sqrt(sum((a - c) ** 2 for a, c in zip(pt.c, S.centro.c))))
        r = S.radio
        cmp_ = _signo_exacto(d - r)
        terminos_b = "+".join("(" + sp.latex(a) + "-" + sp.latex(c) + ")^{2}" for a, c in zip(pt.c, S.centro.c))
        b += [L(r"\|p-c\|=\sqrt{" + terminos_b + "}=" + sp.latex(d) + r"\quad\text{y}\quad r=" + sp.latex(r))]
        if cmp_ is None:
            raise ErrorCalculo("No pude comparar la distancia con el radio.")
        if S.esfera:
            pos = "frontera" if cmp_ == 0 else "exterior"
            pertenece_ = cmp_ == 0
            expl.append("La esfera no tiene interior: sus puntos son todos de frontera.")
        else:
            pos = "interior" if cmp_ < 0 else "frontera" if cmp_ == 0 else "exterior"
            pertenece_ = cmp_ < 0 or (cmp_ == 0 and S.cerrada)
        simb_cmp = "<" if cmp_ < 0 else "=" if cmp_ == 0 else ">"
        pal_cmp = "menor" if cmp_ < 0 else "igual" if cmp_ == 0 else "mayor"
        expl.append("$" + sp.latex(d) + "$ " + simb_cmp + " $" + sp.latex(r) + f"$ → la distancia al centro es {pal_cmp} que el radio.")
        extra = ""
    elif isinstance(S, Region):
        if pt.n != S.n:
            raise ErrorCalculo(f"El conjunto vive en ℝ^{S.n} y el punto tiene {pt.n} coordenada(s).")
        sub = dict(zip(S.vars, pt.c))
        pertenece_ = S.cond.subs(sub, simultaneous=True) == sp.true
        if S.puntos:
            pos = "frontera" if pertenece_ else "exterior"
            expl.append("En un conjunto finito, todos sus puntos son aislados (de frontera).")
        else:
            conjs = _conjunciones(S.cond)
            cierre, interior = _cond_de(conjs, "cierre"), _cond_de(conjs, "interior")
            en_int = interior.subs(sub, simultaneous=True) == sp.true
            en_cl = cierre.subs(sub, simultaneous=True) == sp.true
            pos = "interior" if en_int else "frontera" if en_cl else "exterior"
            rigor = "criterio"
            filas = []
            mapa_op = {"<": "<", "<=": r"\le", ">": ">", ">=": r"\ge", "=": "=", "!=": r"\ne"}
            for c in conjs:
                for g, op in c:
                    v = sp.simplify(g.subs(sub, simultaneous=True))
                    filas.append(["$" + sp.latex(g) + r"\ " + mapa_op[op] + r"\ 0$", "$" + sp.latex(v) + "$"])
            b += [H("Evaluación de las condiciones en p"), TAB(["condición g ⋈ 0", "valor de g(p)"], filas)]
            expl.append("**Interior** si todas las desigualdades se cumplen de forma ESTRICTA; **frontera** si cumple las no estrictas pero alguna es una igualdad; **exterior** si alguna se viola.")
        extra = ""
    else:
        raise ErrorCalculo("No sé clasificar puntos respecto de ese conjunto.")
    color = {"interior": "interior", "frontera": "de frontera", "exterior": "exterior"}[pos]
    b += [
        H("Veredicto"),
        OK(f"El punto es **{color}** al conjunto."),
        T(f"**¿Pertenece al conjunto?** {'sí' if pertenece_ else 'no'}."),
    ] + [T("- " + e) for e in expl]
    if extra:
        b.append(T(extra))
    b.append(IN({"exacto": "Rigor: **exacto**.", "criterio": "Rigor: por **criterio de regularidad** (supone que la frontera es suave)."}[rigor]))
    return res(b, posicion=pos, pertenece=bool(pertenece_), punto=pt)


# ==============================================================================
# 6. PERTENENCIA E INCLUSIÓN ENTRE CONJUNTOS
# ==============================================================================
def _pt_de(p):
    if isinstance(p, Punto):
        return p
    if isinstance(p, Vector):
        return Punto(p.c)
    if isinstance(p, sp.Expr):
        return Punto((p,))
    raise ErrorCalculo("Eso no es un punto.")


@_op
def evaluar_pertenencia(per):
    """a ∈ S  /  a ∉ S: veredicto con la cuenta que lo justifica."""
    a, S0 = per.a, per.S
    S = _canon(S0)
    val = Pertenencia(a, S, negado=per.negado).valor()
    simbolo = r"\notin" if per.negado else r"\in"
    pa = sp.latex(sp.Tuple(*a.c)) if isinstance(a, (Punto, Vector)) and a.n > 1 else sp.latex(a.c[0] if isinstance(a, (Punto, Vector)) else a)
    b = [H("La afirmación"), L(pa + simbolo + _ltx(S0 if isinstance(S0, (Bola, Region, Espacio)) else S))]
    elementos = []
    if val.free_symbols:
        x = sorted(val.free_symbols, key=lambda v: v.name)
        if len(x) == 1 and isinstance(S, sp.Set):
            sol = resolver_cond(val, x[0])
            b += [T("Es una **condición** sobre $" + sp.latex(x[0]) + "$: se cumple exactamente para"), L(sp.latex(x[0]) + r"\in " + sp.latex(sol))]
            return res(b, conjunto=sol, valor=None)
        return res(b + [T("Es una condición con variables: $" + sp.latex(val) + "$")], valor=None)
    cierto = val == sp.true
    pos = None
    expl = []
    if isinstance(S, sp.Set):
        x0 = _pt_de(a).c[0]
        if isinstance(S, sp.Interval):
            lo = "<" if S.left_open else r"\le"
            hi = "<" if S.right_open else r"\le"
            expl.append(
                "¿$" + sp.latex(S.start) + r"\ " + lo + r"\ " + sp.latex(x0) + r"\ " + hi + r"\ " + sp.latex(S.end) + "$? "
                + ("Sí." if S.contains(x0) == True else "No.")  # noqa: E712
            )
        elif isinstance(S, sp.FiniteSet):
            expl.append("¿$" + sp.latex(x0) + "$ es uno de los elementos $" + sp.latex(S) + "$? " + ("Sí." if S.contains(x0) == True else "No."))  # noqa: E712
        elif isinstance(S, sp.Union):
            donde = [t for t in S.args if t.contains(x0) == True]  # noqa: E712
            expl.append("Está en " + (("$" + sp.latex(donde[0]) + "$.") if donde else "ninguna de las partes de la unión."))
        else:
            nombre = {
                sp.S.Naturals: "un entero positivo",
                sp.S.Naturals0: "un entero no negativo",
                sp.S.Integers: "un entero",
                sp.S.Rationals: "un número racional",
                sp.S.Reals: "un número real",
                sp.S.Complexes: "un número complejo",
            }.get(S)
            if nombre:
                expl.append("¿$" + sp.latex(x0) + f"$ es {nombre}? " + ("Sí." if S.contains(x0) == True else "No."))  # noqa: E712
        if S != sp.S.Complexes and not x0.has(sp.I):
            pos = [(x0, "pertenece ✓" if cierto != per.negado else "no pertenece ✗", "#15803d" if (S.contains(x0) == True) else "#dc2626")]  # noqa: E712
    elif isinstance(S, Bola):
        pt = _pt_de(a)
        d = sp.simplify(sp.sqrt(sum((u - c) ** 2 for u, c in zip(pt.c, S.centro.c))))
        cmp_ = _signo_exacto(d - S.radio)
        expl.append(
            r"Distancia al centro: $\|p-c\|=" + sp.latex(d) + "$; radio $r=" + sp.latex(S.radio) + "$. "
            + {
                -1: "La distancia es menor que el radio.",
                0: "La distancia es igual al radio (está justo en el borde).",
                1: "La distancia es mayor que el radio.",
            }[cmp_]
        )
        elementos = [(pt, "interior" if cmp_ < 0 else "frontera" if cmp_ == 0 else "exterior")]
    elif isinstance(S, Region):
        pt = _pt_de(a)
        expl.append(
            "Se sustituye el punto en la condición: $" + sp.latex(S.cond) + "$ con "
            + ", ".join("$" + sp.latex(v) + "=" + sp.latex(c) + "$" for v, c in zip(S.vars, pt.c)) + "."
        )
    elif isinstance(S, Espacio):
        expl.append("Un punto pertenece a ℝ^" + sp.latex(S.n) + " si tiene exactamente " + sp.latex(S.n) + " coordenadas reales.")
    if per.negado:
        expl.append("«∉» significa que NO pertenece.")
    b += [T("- " + e) for e in expl]
    b.append((OK if cierto else AV)(f"La afirmación es **{'VERDADERA' if cierto else 'FALSA'}**."))
    return res(b, valor=bool(cierto), conjunto=(None if S == sp.S.Complexes else S), puntos_1d=pos, elementos=elementos)


def _extensiones(S):
    """Caja (min, max) por coordenada donde mirar el conjunto, o None."""
    if isinstance(S, Bola):
        return [(float(sp.N(c)) - float(sp.N(S.radio)) - 1, float(sp.N(c)) + float(sp.N(S.radio)) + 1) for c in S.centro.c]
    return None


def _rac(v, dec=3):
    return sp.nsimplify(round(float(v), dec), rational=True)


def _comparar_nd(A, B):
    """¿A ⊆ B? para conjuntos de ℝⁿ (n ≥ 2): (valor, texto, rigor, contraejemplo)."""
    if isinstance(A, Bola) and isinstance(B, Bola) and not A.esfera and not B.esfera and not (A.radio.free_symbols or B.radio.free_symbols):
        d = sp.simplify(sp.sqrt(sum((u - v) ** 2 for u, v in zip(A.centro.c, B.centro.c))))
        r, s = A.radio, B.radio
        estricto = A.cerrada and not B.cerrada
        cond = sp.Lt(d + r, s) if estricto else sp.Le(d + r, s)
        v = bool(cond)
        simb_est = "<" if estricto else r"\le"
        txt = (
            "Distancia entre centros $d=" + sp.latex(d) + "$. Una bola está dentro de otra si $d+r_1" + simb_est + " r_2$: "
            "$" + sp.latex(d) + "+" + sp.latex(r) + "=" + sp.latex(sp.simplify(d + r)) + "$ frente a $r_2=" + sp.latex(s) + "$ → "
            + ("se cumple." if v else "NO se cumple.")
        )
        return v, txt, "exacto", None
    RA, RB = a_region(A), a_region(B)
    if RA.n != RB.n:
        raise ErrorCalculo(f"Los conjuntos viven en espacios distintos (ℝ^{RA.n} y ℝ^{RB.n}).")
    RB = RB.renombrar(RA.vars)
    fa, fb = _lambdify_cond(RA), _lambdify_cond(RB)
    if fa is None or fb is None:
        raise ErrorCalculo("No pude evaluar numéricamente estos conjuntos para compararlos.")
    n = RA.n
    ext = [(-12.0, 12.0)] * n
    for S_ in (A, B):
        e = _extensiones(S_)
        if e:
            ext = [(max(-60, min(lo, a)), min(60, max(hi, b_))) for (a, b_), (lo, hi) in zip(ext, e)]
    rng = np.random.default_rng(3)
    P = np.column_stack([rng.uniform(lo, hi, 160_000) for lo, hi in ext])
    cols = [P[:, i] for i in range(n)]
    ina, inb = fa(*cols), fb(*cols)
    malos = np.where(ina & ~inb)[0]
    for i in malos[:25]:
        q = [_rac(v) for v in P[i]]
        sub = dict(zip(RA.vars, q))
        if RA.cond.subs(sub, simultaneous=True) == sp.true and RB.cond.subs(dict(zip(RA.vars, q)), simultaneous=True) == sp.false:
            return False, "Hay un punto de A que no está en B: $p=" + sp.latex(sp.Tuple(*q)) + "$.", "contraejemplo", Punto(q)
    if ina.sum() == 0:
        return True, "El primer conjunto parece vacío, así que está contenido en cualquiera.", "evidencia", None
    return True, f"Se probaron {int(ina.sum())} puntos de A al azar y todos están en B (no se encontró ningún contraejemplo).", "evidencia", None


def _contenido(A, B):
    """(valor, texto, rigor, contraejemplo) de A ⊆ B."""
    A, B = _canon(A), _canon(B)
    da, db = dimension_de(A), dimension_de(B)
    if da is not None and db is not None and da != db:
        raise ErrorCalculo(f"Los conjuntos viven en espacios distintos (ℝ^{da} y ℝ^{db}): no se pueden comparar.")
    if isinstance(A, sp.Set) and isinstance(B, sp.Set):
        dif = sp.Complement(A, B)
        if dif == sp.S.EmptySet:
            return True, r"$A\setminus B=\varnothing$: todo elemento de A está en B.", "exacto", None
        if dif.is_empty is False or not isinstance(dif, sp.Complement):
            ej = _una_muestra(dif)
            nota_ej = ("; por ejemplo $" + sp.latex(ej) + "$ está en A y no en B.") if ej is not None else "."
            return False, r"$A\setminus B=" + sp.latex(dif) + "$ no es vacío" + nota_ej, "exacto", ej
        return A.is_subset(B), "(comprobado con SymPy)", "exacto", None
    if isinstance(A, Espacio) and isinstance(B, Espacio):
        return A.n == B.n, "Se comparan las dimensiones.", "exacto", None
    if isinstance(B, Espacio) and B.dim == db:
        return True, "Todo conjunto de ℝⁿ está contenido en ℝⁿ.", "exacto", None
    return _comparar_nd(A, B)


def _una_muestra(S):
    """Un elemento de un conjunto de ℝ, o None."""
    try:
        if isinstance(S, sp.FiniteSet):
            return S.args[0]
        if isinstance(S, sp.Interval):
            a, b = S.start, S.end
            if a.is_finite and b.is_finite:
                return (a + b) / 2
            return (a + 1) if a.is_finite else (b - 1) if b.is_finite else sp.Integer(0)
        if isinstance(S, sp.Union):
            for t in S.args:
                v = _una_muestra(t)
                if v is not None:
                    return v
        for k in range(0, 40):
            for v in (k, -k):
                if S.contains(v) == True:  # noqa: E712
                    return sp.Integer(v)
    except Exception:  # noqa: BLE001
        return None
    return None


@_op
def evaluar_relconj(rel):
    """⊂ ⊆ ⊃ ⊇ = ≠ entre conjuntos, con la razón y, si falla, un contraejemplo."""
    op, A, B = rel.op, rel.a, rel.b
    simb = {"subset": r"\subset", "subseteq": r"\subseteq", "supset": r"\supset", "supseteq": r"\supseteq", "eq": "=", "ne": r"\neq"}[op]
    b = [H("La afirmación"), L(_ltx(A) + simb + _ltx(B))]
    datos = {"A": _canon(A), "B": _canon(B)}
    if op in ("subset", "subseteq"):
        v1, t1, r1, c1 = _contenido(A, B)
        b += [H("¿A ⊆ B?"), T(t1)]
        valor, rigor, cej = v1, r1, c1
        if op == "subset" and v1:
            v2, t2, r2, _ = _contenido(B, A)
            b += [H("¿B ⊆ A también?"), T(t2)]
            valor = not v2
            rigor = "evidencia" if "evidencia" in (r1, r2) else "exacto"
            b.append(T("«⊂» exige que A esté contenido en B **y** que sean distintos (B tiene algo que A no tiene)."))
    elif op in ("supset", "supseteq"):
        v1, t1, r1, c1 = _contenido(B, A)
        b += [H("¿B ⊆ A?"), T(t1)]
        valor, rigor, cej = v1, r1, c1
        if op == "supset" and v1:
            v2, t2, r2, _ = _contenido(A, B)
            b += [H("¿A ⊆ B también?"), T(t2)]
            valor, rigor = not v2, ("evidencia" if "evidencia" in (r1, r2) else "exacto")
    else:
        v1, t1, r1, c1 = _contenido(A, B)
        v2, t2, r2, c2 = _contenido(B, A)
        b += [H("¿A ⊆ B?"), T(t1), H("¿B ⊆ A?"), T(t2), T("Dos conjuntos son **iguales** si cada uno está contenido en el otro.")]
        igual = v1 and v2
        valor = igual if op == "eq" else not igual
        rigor = (
            "contraejemplo" if (not igual and (r1 == "contraejemplo" or r2 == "contraejemplo" or "exacto" in (r1, r2)))
            else ("evidencia" if "evidencia" in (r1, r2) else "exacto")
        )
        cej = c1 or c2
    etiqueta = {
        "exacto": "demostrado de forma **exacta**",
        "contraejemplo": "**refutado** con un contraejemplo verificado",
        "evidencia": "solo con **evidencia numérica** (no es una demostración)",
    }[rigor]
    if rigor == "evidencia" and not valor:
        etiqueta = "con evidencia numérica"
    b.append((OK if valor else AV)(f"La afirmación es **{'VERDADERA' if valor else 'FALSA'}** ({etiqueta})."))
    return res(b, valor=bool(valor), rigor=rigor, contraejemplo=cej, **datos)


# ==============================================================================
# 7. LÓGICA PROPOSICIONAL Y SOBRE ℝ
# ==============================================================================
def _subformulas(e):
    out = []

    def rec(x):
        if isinstance(x, sp.Symbol) or x in (sp.true, sp.false) or not x.args:
            return
        for a in x.args:
            rec(a)
        if x not in out:
            out.append(x)
    rec(e)
    return out


def _aplanar(e):
    if isinstance(e, sp.Implies):
        return sp.Or(sp.Not(_aplanar(e.args[0])), _aplanar(e.args[1]))
    if isinstance(e, sp.Equivalent):
        a, b = _aplanar(e.args[0]), _aplanar(e.args[1])
        return sp.Or(sp.And(a, b), sp.And(sp.Not(a), sp.Not(b)))
    if isinstance(e, (sp.And, sp.Or)):
        return type(e)(*[_aplanar(a) for a in e.args])
    if isinstance(e, sp.Not):
        return sp.Not(_aplanar(e.args[0]))
    return e


def _vf(v):
    return "V" if v == sp.true or v is True else "F"


def _tabla(expr, atomos, extras=()):
    """Tabla de verdad en Markdown (con columnas de subfórmulas) y la lista de valores de `expr` por fila."""
    subs = [s for s in _subformulas(expr)]
    cols = list(atomos) + (subs if len(subs) <= 7 else [expr])
    if expr not in cols:
        cols.append(expr)
    cabecera = ["$" + sp.latex(c) + "$" for c in cols] + ["$" + sp.latex(e) + "$" for e in extras]
    filas, valores = [], []
    for vals in itertools.product([True, False], repeat=len(atomos)):
        d = dict(zip(atomos, vals))
        fila = [_vf(v) for v in vals]
        for c in cols[len(atomos):]:
            fila.append(_vf(c.subs(d)))
        for e in extras:
            fila.append(_vf(e.subs(d)))
        valores.append(expr.subs(d) == sp.true)
        filas.append(fila)
    return cabecera, filas, valores


def _clase_logica(valores):
    if all(valores):
        return "tautologia"
    if not any(valores):
        return "contradiccion"
    return "contingencia"


def _equivalentes(a, b, atomos):
    return all((a.subs(dict(zip(atomos, v))) == b.subs(dict(zip(atomos, v)))) for v in itertools.product([True, False], repeat=len(atomos)))


def _logica_proposicional(expr, atomos):
    b = [H("Proposición"), L(sp.latex(expr))]
    if len(atomos) > 5:
        raise ErrorCalculo("Hay más de 5 letras proposicionales: la tabla de verdad tendría más de 32 filas. Simplifica la fórmula.")
    cab, filas, valores = _tabla(expr, atomos)
    b += [H("Tabla de verdad"), TAB(cab, filas)]
    clase = _clase_logica(valores)
    nm = sum(valores)
    b.append({
        "tautologia": OK(f"Es una **TAUTOLOGÍA**: es verdadera en las {len(valores)} filas (siempre verdadera, sin importar los valores de las letras)."),
        "contradiccion": AV("Es una **CONTRADICCIÓN**: es falsa en todas las filas."),
        "contingencia": IN(f"Es una **CONTINGENCIA**: verdadera en {nm} de {len(valores)} filas (depende de los valores de las letras)."),
    }[clase])
    try:
        dnf, cnf = sp.simplify_logic(expr, form="dnf"), sp.simplify_logic(expr, form="cnf")
        b += [
            H("Formas equivalentes más sencillas"),
            T("**Forma normal disyuntiva (suma de productos):**"), L(sp.latex(dnf)),
            T("**Forma normal conjuntiva (producto de sumas):**"), L(sp.latex(cnf)),
        ]
        neg = sp.simplify_logic(sp.Not(expr))
        b += [H("Negación (leyes de De Morgan)"), L(r"\neg\left(" + sp.latex(expr) + r"\right)\equiv " + sp.latex(neg))]
    except Exception:  # noqa: BLE001
        pass
    if isinstance(expr, sp.Implies):
        P_, Q_ = expr.args
        rel = [
            ("Recíproca", sp.Implies(Q_, P_)),
            ("Inversa", sp.Implies(sp.Not(P_), sp.Not(Q_))),
            ("Contrapositiva", sp.Implies(sp.Not(Q_), sp.Not(P_))),
        ]
        filas2 = [[n_, "$" + sp.latex(e) + "$", "**sí**" if _equivalentes(expr, e, atomos) else "no"] for n_, e in rel]
        b += [
            H("Enunciados relacionados con la implicación"),
            TAB(["nombre", "enunciado", "¿equivale a la original?"], filas2),
            IN("La **contrapositiva** siempre equivale a la implicación; la recíproca y la inversa, en general, no."),
        ]
    if isinstance(expr, sp.Equivalent) and clase == "tautologia":
        b.append(OK("Las dos fórmulas son **lógicamente equivalentes**."))
    if isinstance(expr, sp.Implies) and clase == "tautologia":
        b.append(OK("La implicación es **válida**: siempre que el antecedente es verdadero, el consecuente también."))
    return res(b, clase=clase, modelos=nm, filas=len(valores))


def _muestras_n(vars_, N=80_000, B=6.0, seed=5):
    rng = np.random.default_rng(seed)
    return np.column_stack([rng.uniform(-B, B, N) for _ in vars_])


def _logica_real(expr):
    vars_ = sorted([v for v in expr.free_symbols if isinstance(v, sp.Symbol)], key=lambda v: v.name)
    b = [H("Proposición sobre los números reales"), L(sp.latex(expr))]
    if len(vars_) == 1:
        x = vars_[0]
        sol = resolver_cond(expr, x)
        b += [H("¿Para qué valores se cumple?"), L(sp.latex(x) + r"\in " + sp.latex(sol))]
        if sol == sp.S.Reals:
            b.append(OK("Es verdadera para **todo** real: es una **tautología sobre ℝ** (identidad lógica)."))
            clase = "tautologia"
        elif sol == sp.S.EmptySet:
            b.append(AV("No se cumple para **ningún** real: es una **contradicción sobre ℝ**."))
            clase = "contradiccion"
        else:
            b.append(IN("Se cumple solo para algunos valores: es una **contingencia** (condición que depende de x)."))
            clase = "contingencia"
        if isinstance(expr, sp.Implies):
            P_, Q_ = expr.args
            sp_, sq_ = resolver_cond(P_, x), resolver_cond(Q_, x)
            b += [
                H("Antecedente y consecuente"),
                T(
                    "$P$ se cumple en $" + sp.latex(sp_) + "$ y $Q$ en $" + sp.latex(sq_)
                    + r"$. La implicación $P\Rightarrow Q$ es válida cuando $P\subseteq Q$: "
                    + ("**sí se cumple**." if sp_.is_subset(sq_) == True else "**no se cumple**.")  # noqa: E712
                ),
            ]
        if isinstance(expr, sp.Equivalent):
            P_, Q_ = expr.args
            sp_, sq_ = resolver_cond(P_, x), resolver_cond(Q_, x)
            b.append(T(r"$P\Leftrightarrow Q$ es válida cuando $P$ y $Q$ se cumplen exactamente en los mismos valores: " + ("**sí**." if sp_ == sq_ else "**no**.")))
        return res(b, clase=clase, conjunto=sol, rigor="exacto")
    if not vars_:
        return res(b + [OK("No hay variables: es " + ("verdadera." if bool(expr) else "falsa."))], clase="constante")
    if len(vars_) > 3:
        raise ErrorCalculo("Con más de 3 variables reales solo se admite análisis exacto de proposiciones de una variable.")
    ap = _aplanar(expr)
    f = sp.lambdify(vars_, ap, modules=["numpy"])
    P = _muestras_n(vars_)
    with np.errstate(all="ignore"):
        ok = np.broadcast_to(np.asarray(f(*[P[:, i] for i in range(len(vars_))]), dtype=bool), (len(P),))
    frac = float(ok.mean())
    ej_v = _verificado(expr, vars_, P, ok, True)
    ej_f = _verificado(expr, vars_, P, ok, False)
    b.append(H("Análisis numérico (varias variables)"))
    if frac == 1.0:
        b.append(OK("Se cumplió en **todas** las muestras: probablemente es una **tautología sobre ℝ** (evidencia, no demostración)."))
        clase = "tautologia"
    elif frac == 0.0:
        b.append(AV("No se cumplió en **ninguna** muestra: probablemente es una **contradicción sobre ℝ** (evidencia)."))
        clase = "contradiccion"
    else:
        clase = "contingencia"
        b.append(IN(f"Es una **contingencia**: se cumplió en el {100 * frac:.1f} % de las muestras."))
    for et, ej in (("Un punto donde SÍ se cumple", ej_v), ("Un punto donde NO se cumple", ej_f)):
        if ej is not None:
            b.append(T(f"**{et}:** " + ", ".join("$" + sp.latex(v) + "=" + sp.latex(c) + "$" for v, c in zip(vars_, ej)) + " (verificado exactamente)."))
    datos = {"clase": clase, "rigor": "evidencia"}
    if len(vars_) == 2:
        datos["region"] = Region(tuple(vars_), ap, "la región donde se cumple")
        datos["vars"] = vars_
    return res(b, **datos)


def _verificado(expr, vars_, P, ok, buscar):
    idx = np.where(ok == buscar)[0]
    for i in idx[:30]:
        q = [_rac(v) for v in P[i]]
        r = expr.subs(dict(zip(vars_, q)), simultaneous=True)
        if (r == sp.true) == buscar and r in (sp.true, sp.false):
            return q
    return None


def _separar_vars_logicas(expr):
    """Separa átomos proposicionales de variables que aparecen en desigualdades/ecuaciones reales."""
    nodos_rel = expr.atoms(sp.core.relational.Relational, sp.Contains)
    reales_en_rel = {s for rel in nodos_rel for s in rel.free_symbols if isinstance(s, sp.Symbol)}
    libres = [v for v in expr.free_symbols if isinstance(v, sp.Symbol)]
    if not nodos_rel:
        reemplazo = {v: sp.Symbol(v.name) for v in libres if v.is_real}
        if reemplazo:
            expr = expr.subs(reemplazo)
            libres = [v for v in expr.free_symbols if isinstance(v, sp.Symbol)]
        return expr, sorted(libres, key=lambda v: v.name), []
    atomos = sorted([v for v in libres if v not in reales_en_rel and not v.is_real], key=lambda v: v.name)
    reales = sorted([v for v in libres if v in reales_en_rel or v.is_real], key=lambda v: v.name)
    return expr, atomos, reales


@_op
def evaluar_logica(expr):
    """Proposiciones: tabla de verdad (letras) o solución sobre ℝ (relaciones)."""
    expr, atomos, reales = _separar_vars_logicas(expr)
    if atomos and reales:
        raise ErrorCalculo("Mezclas letras proposicionales (p, q) con variables reales (x): no se pueden evaluar juntas.")
    if atomos:
        return _logica_proposicional(expr, atomos)
    return _logica_real(expr)


# ------------------------------------------------------------------ argumentos
def _forma_argumento(prem, conc):
    ps = list(prem)
    imp = [p for p in ps if isinstance(p, sp.Implies)]
    for p in imp:
        A, B = p.args
        otros = [q for q in ps if q != p]
        if A in otros and conc == B:
            return "Modus ponens (afirmar el antecedente)", True
        if sp.Not(B) in otros and conc == sp.Not(A):
            return "Modus tollens (negar el consecuente)", True
        if B in otros and conc == A:
            return "Falacia de afirmar el consecuente", False
        if sp.Not(A) in otros and conc == sp.Not(B):
            return "Falacia de negar el antecedente", False
        for q in otros:
            if isinstance(q, sp.Implies) and q.args[0] == B and conc == sp.Implies(A, q.args[1]):
                return "Silogismo hipotético", True
    for p in [p for p in ps if isinstance(p, sp.Or)]:
        if len(p.args) == 2:
            A, B = p.args
            otros = [q for q in ps if q != p]
            if sp.Not(A) in otros and conc == B:
                return "Silogismo disyuntivo", True
            if sp.Not(B) in otros and conc == A:
                return "Silogismo disyuntivo", True
    return None, None


@_op
def evaluar_argumento(arg):
    """Validez de un argumento: premisas ∴ conclusión."""
    prem, conc = arg.premisas, arg.conclusion
    libres = [v for e in list(prem) + [conc] for v in e.free_symbols if isinstance(v, sp.Symbol)]
    atomos = sorted({v for v in libres if not v.is_real}, key=lambda v: v.name)
    if any(v.is_real for v in libres):
        impl = sp.Implies(sp.And(*prem), conc)
        r = _logica_real(impl)
        r["bloques"].insert(0, T("Con relaciones sobre ℝ, el argumento es **válido** si «premisas ⇒ conclusión» se cumple para todos los valores."))
        return r
    if len(atomos) > 5:
        raise ErrorCalculo("Hay más de 5 letras proposicionales: la tabla tendría más de 32 filas.")
    b = [H("El argumento"), L(r",\ ".join(sp.latex(p) for p in prem) + r"\ \therefore\ " + sp.latex(conc))]
    cols = ["$" + sp.latex(a) + "$" for a in atomos] + ["$" + sp.latex(p) + "$" for p in prem] + ["$" + sp.latex(conc) + "$", "¿premisas todas V?"]
    filas2, malas = [], []
    for vals in itertools.product([True, False], repeat=len(atomos)):
        d = dict(zip(atomos, vals))
        pv = [p.subs(d) == sp.true for p in prem]
        cv = conc.subs(d) == sp.true
        fila = [_vf(v) for v in vals] + [_vf(v) for v in pv] + [_vf(cv), "✔" if all(pv) else ""]
        filas2.append(fila)
        if all(pv) and not cv:
            malas.append(d)
    b += [H("Tabla de verdad"), TAB(cols, filas2)]
    forma, valida_forma = _forma_argumento(prem, conc)
    valido = not malas
    if forma:
        b.append(IN(f"Forma reconocida: **{forma}**" + (" (una forma válida)." if valida_forma else " (¡es una falacia!).")))
    if valido:
        b.append(OK("El argumento es **VÁLIDO**: en todas las filas donde las premisas son verdaderas (✔), la conclusión también lo es."))
    else:
        b.append(AV("El argumento es **INVÁLIDO**: hay filas donde las premisas son verdaderas y la conclusión es FALSA:"))
        for d in malas[:3]:
            b.append(T("- " + ", ".join("$" + sp.latex(k) + "=" + ("V" if v else "F") + "$" for k, v in d.items())))
    b.append(IN("«Válido» no significa que la conclusión sea verdadera en el mundo real: significa que **si** las premisas fueran verdaderas, la conclusión lo sería."))
    return res(b, valido=valido, forma=forma, contraejemplos=malas[:3])


# ------------------------------------------------------------------ cuantificadores
_SIMB = {"para_todo": r"\forall", "existe": r"\exists", "no_existe": r"\nexists"}


def _ltx_q(Q) -> str:
    if not isinstance(Q, Cuantificado):
        return sp.latex(Q)
    vs = ",".join(sp.latex(v) for v in Q.vars)
    dom = (r"\in " + _ltx(Q.dominio)) if Q.dominio is not None else ""
    return _SIMB[Q.cuantificador] + r"\," + vs + dom + r":\ " + _ltx_q(Q.cuerpo)


def _neg_rel(r):
    mp_rel = {sp.Lt: sp.Ge, sp.Le: sp.Gt, sp.Gt: sp.Le, sp.Ge: sp.Lt, sp.Eq: sp.Ne, sp.Ne: sp.Eq}
    for cls, neg in mp_rel.items():
        if isinstance(r, cls):
            return neg(r.lhs, r.rhs, evaluate=False)
    return sp.Not(r)


def _neg(c):
    if isinstance(c, Cuantificado):
        return _negar_q(c)
    if isinstance(c, sp.core.relational.Relational):
        return _neg_rel(c)
    if isinstance(c, sp.And):
        return sp.Or(*[_neg(a) for a in c.args])
    if isinstance(c, sp.Or):
        return sp.And(*[_neg(a) for a in c.args])
    if isinstance(c, sp.Implies):
        return sp.And(c.args[0], _neg(c.args[1]))
    if isinstance(c, sp.Not):
        return c.args[0]
    return sp.Not(c)


def _negar_q(Q):
    if Q.cuantificador == "para_todo":
        return Cuantificado("existe", Q.vars, Q.dominio, _neg(Q.cuerpo))
    if Q.cuantificador == "existe":
        return Cuantificado("para_todo", Q.vars, Q.dominio, _neg(Q.cuerpo))
    return Cuantificado("existe", Q.vars, Q.dominio, Q.cuerpo)


def _candidatos(dom, k=48):
    """Valores de prueba (racionales) dentro del dominio `dom` (sympy Set de ℝ)."""
    if isinstance(dom, sp.FiniteSet):
        return list(dom.args)
    base = [
        0, 1, -1, 2, -2, 3, -3, 5, -5, 10, -10, 100, -100,
        sp.Rational(1, 2), -sp.Rational(1, 2), sp.Rational(1, 3), -sp.Rational(1, 3),
        sp.Rational(3, 2), -sp.Rational(3, 2), sp.Rational(1, 10), -sp.Rational(1, 10), 4, -4, 7, -7,
    ]
    rng = random.Random(1)
    base += [sp.Rational(rng.randint(-200, 200), rng.choice([1, 2, 3, 4, 5, 8, 10])) for _ in range(40)]
    if isinstance(dom, sp.Interval) and dom.start.is_finite and dom.end.is_finite:
        a, b_ = dom.start, dom.end
        base += [a + (b_ - a) * sp.Rational(i, 10) for i in range(0, 11)] + [a + (b_ - a) * sp.Rational(1, 100), b_ - (b_ - a) * sp.Rational(1, 100)]
    out = []
    for v in base:
        v = sp.sympify(v)
        try:
            if dom.contains(v) == True and v not in out:  # noqa: E712
                out.append(v)
        except Exception:  # noqa: BLE001
            pass
    return sorted(out, key=lambda v: abs(float(v)))[:k]


def _base_1d(D):
    if D is None:
        return sp.S.Reals
    S = _canon(D)
    if not isinstance(S, sp.Set) or S == sp.S.Complexes:
        raise ErrorCalculo("El dominio de una variable cuantificada debe ser un subconjunto de ℝ (ℝ, ℕ, ℤ, [a, b]…). Para ℝⁿ declara cada variable por separado.")
    return S


def _evaluar_q(Q, sub):
    """(valor, rigor, ejemplo) con rigor ∈ {'exacto', 'testigo', 'contraejemplo', 'evidencia'}."""
    q, vars_, D, cuerpo = Q.cuantificador, Q.vars, Q.dominio, Q.cuerpo
    if q == "no_existe":
        v, r, e = _evaluar_q(Cuantificado("existe", vars_, D, cuerpo), sub)
        return (None if v is None else not v), r, e
    if len(vars_) > 1:
        return _evaluar_q(Cuantificado(q, vars_[:1], D, Cuantificado(q, vars_[1:], D, cuerpo)), sub)
    x = vars_[0]
    dom = _base_1d(D)
    if not isinstance(cuerpo, Cuantificado):
        cond = cuerpo.subs(sub, simultaneous=True) if sub else cuerpo
        libres = cond.free_symbols - {x}
        try:
            sol = resolver_cond(cond, x, dom)
        except ErrorCalculo:
            sol = None
        except Exception:  # noqa: BLE001
            sol = None
        if sol is not None and not isinstance(sol, sp.ConditionSet) and not sol.has(sp.ConditionSet):
            if q == "para_todo":
                malos = sp.Complement(dom, sol)
                if malos == sp.S.EmptySet:
                    return True, "exacto", None
                if not libres:
                    ej = _una_muestra(malos)
                    return False, "contraejemplo", ({x: ej} if ej is not None else None)
            else:
                if sol == sp.S.EmptySet:
                    return False, "exacto", None
                if not libres:
                    ej = _una_muestra(sol)
                    return True, "testigo", ({x: ej} if ej is not None else None)
                if sol.is_empty is False:
                    return True, "exacto", None
    vals = _candidatos(dom)
    candidato_dudoso = None
    for v in vals:
        sub2 = {**sub, x: v}
        if isinstance(cuerpo, Cuantificado):
            iv, ir, _ = _evaluar_q(cuerpo, sub2)
            rig = ir != "evidencia"
        else:
            r_ = cuerpo.subs(sub2, simultaneous=True)
            iv, rig = (True if r_ == sp.true else False if r_ == sp.false else None), True
        if iv is None:
            continue
        if q == "para_todo" and iv is False and rig:
            return False, "contraejemplo", {x: v}
        if q == "existe" and iv is True and rig:
            return True, "testigo", {x: v}
        if (q == "para_todo" and iv is False) or (q == "existe" and iv is True):
            candidato_dudoso = {x: v}
    if q == "para_todo":
        return (False if candidato_dudoso else True), "evidencia", candidato_dudoso
    return (True if candidato_dudoso else False), "evidencia", candidato_dudoso


@_op
def evaluar_cuantificado(Q):
    """∀ / ∃ / ∄: veredicto (exacto cuando se puede), testigo o contraejemplo, y la negación."""
    b = [H("El enunciado"), L(_ltx_q(Q))]
    val, rigor, ej = _evaluar_q(Q, {})
    neg = _negar_q(Q)
    base = None
    if len(Q.vars) == 1 and not isinstance(Q.cuerpo, Cuantificado):
        try:
            dom = _base_1d(Q.dominio)
            sol = resolver_cond(Q.cuerpo, Q.vars[0], dom)
            if not sol.has(sp.ConditionSet):
                base = (dom, sol)
                b += [
                    H("¿Para qué valores se cumple la condición?"),
                    L(sp.latex(Q.vars[0]) + r"\in " + sp.latex(sol)),
                    T("El dominio es $" + sp.latex(dom) + "$."),
                ]
        except Exception:  # noqa: BLE001
            pass
    if ej:
        txt = ", ".join("$" + sp.latex(k) + "=" + sp.latex(v) + "$" for k, v in ej.items())
        etiqueta = {
            "testigo": "**Testigo** (un valor que cumple)",
            "contraejemplo": "**Contraejemplo** (un valor que NO cumple)",
            "evidencia": "Valor que llamó la atención",
            "exacto": "Ejemplo",
        }[rigor]
        b.append(T(f"{etiqueta}: {txt}"))
    texto_rigor = {
        "exacto": "Resuelto de forma **exacta** (con conjuntos de ℝ).",
        "testigo": "Demostrado con un **testigo** verificado exactamente.",
        "contraejemplo": "Refutado con un **contraejemplo** verificado exactamente.",
        "evidencia": "Resultado por **muestreo** de valores (evidencia): no es una demostración; si el enunciado es falso para algún valor que no se probó, no se habría detectado.",
    }[rigor]
    if val is None:
        b.append(AV("No se pudo decidir."))
    else:
        b.append((OK if val else AV)(f"El enunciado es **{'VERDADERO' if val else 'FALSO'}**."))
    b += [
        IN(texto_rigor),
        H("Su negación"),
        L(_ltx_q(neg)),
        IN("Negar un enunciado cuantificado cambia ∀ por ∃ (y al revés) y niega la condición interna."),
    ]
    return res(b, valor=val, rigor=rigor, ejemplo=ej, **({"conjunto": base[1], "universo": base[0]} if base else {}))


# ==============================================================================
# 8. COMPARACIONES: ≡ ≈ ≡ (mod n) ∣
# ==============================================================================
def _puntos_prueba(vars_, k=7):
    rng = random.Random(4)
    base = [sp.Rational(v) for v in (0, 1, -1, 2, sp.Rational(1, 2), 3, -2)]
    return [
        {v: (base[i % len(base)] + (0 if j == 0 else sp.Rational(rng.randint(-9, 9), rng.choice([1, 2, 3, 5])))) for i, v in enumerate(vars_)}
        for j in range(k)
    ]


@_op
def evaluar_comparacion(obj):
    """Equivalencia, aproximación, congruencia y divisibilidad."""
    if isinstance(obj, Equivalencia):
        a, c = obj.a, obj.b
        b = [H("La afirmación"), L(sp.latex(a) + r"\equiv " + sp.latex(c))]
        es_log_a = isinstance(a, sp.logic.boolalg.Boolean) and not isinstance(a, sp.Symbol)
        es_log_c = isinstance(c, sp.logic.boolalg.Boolean) and not isinstance(c, sp.Symbol)
        if es_log_a or es_log_c or (
            isinstance(a, sp.logic.boolalg.Boolean) and isinstance(c, sp.logic.boolalg.Boolean)
            and (not getattr(a, "is_real", False) or not getattr(c, "is_real", False))
        ):
            r = evaluar_logica(sp.Equivalent(a, c))
            return res(
                b + [T("Entre proposiciones, «≡» es **equivalencia lógica**: ambas son verdaderas o falsas exactamente en los mismos casos.")] + r["bloques"][1:],
                **r["datos"],
            )
        d = sp.simplify(a - c)
        if d == 0:
            b.append(OK("Son **idénticas**: $a-b$ se simplifica a 0, así que valen lo mismo para cualquier valor."))
            return res(b, valor=True, rigor="exacto")
        vars_ = sorted(d.free_symbols, key=lambda v: v.name)
        for sub in _puntos_prueba(vars_):
            va, vc = sp.simplify(a.subs(sub)), sp.simplify(c.subs(sub))
            if va.is_number and vc.is_number and sp.simplify(va - vc) != 0 and va.is_finite and vc.is_finite:
                ej = ", ".join("$" + sp.latex(k) + "=" + sp.latex(v) + "$" for k, v in sub.items())
                b += [
                    AV("**NO son idénticas.** Contraejemplo: con " + ej + " una vale $" + sp.latex(va) + "$ y la otra $" + sp.latex(vc) + "$."),
                    T("Su diferencia es $" + sp.latex(d) + "$."),
                ]
                return res(b, valor=False, rigor="contraejemplo")
        b.append(IN("No pude demostrar que sean idénticas (la diferencia no se simplifica a 0: $" + sp.latex(d) + "$), pero tampoco encontré un valor donde difieran."))
        return res(b, valor=None, rigor="evidencia")
    if isinstance(obj, Aproximado):
        a, c = obj.a, obj.b
        va, vc = sp.N(a, 20), sp.N(c, 20)
        if not (va.is_number and vc.is_number) or va.free_symbols or vc.free_symbols:
            raise ErrorCalculo("«≈» compara dos valores numéricos (sin variables).")
        dif = abs(va - vc)
        rel = dif / max(abs(va), abs(vc), 1e-300)
        ok_ = bool(rel < sp.Rational(1, 1000))
        b = [
            H("La afirmación"),
            L(sp.latex(a) + r"\approx " + sp.latex(c)),
            TAB(["valor", "decimal"], [["$" + sp.latex(a) + "$", f"{_n(va, 12)}"], ["$" + sp.latex(c) + "$", f"{_n(vc, 12)}"]]),
            T(f"Diferencia absoluta: {float(dif):.3g}; diferencia relativa: {float(rel) * 100:.3g} %."),
        ]
        b.append((OK if ok_ else AV)(f"Se consideran **{'aproximadamente iguales' if ok_ else 'NO aproximadamente iguales'}** (umbral: 0.1 % de diferencia relativa)."))
        if sp.simplify(a - c) == 0:
            b.append(IN("En realidad son exactamente iguales."))
        return res(b, valor=ok_)
    if isinstance(obj, Divisibilidad):
        a, c = obj.a, obj.b
        b = [H("La afirmación"), L(sp.latex(a) + r"\mid " + sp.latex(c))]
        if a.is_Integer and c.is_Integer:
            if a == 0:
                v = c == 0
                b.append((OK if v else AV)("El 0 solo divide al 0." if v else "El 0 no divide a ningún número distinto de 0."))
                return res(b, valor=v)
            q_, r_ = divmod(int(c), int(a))
            v = r_ == 0
            b.append(T("$" + sp.latex(c) + "=" + sp.latex(a) + r"\cdot(" + str(q_) + ")+" + str(r_) + f"$ → cociente {q_}, resto {r_}."))
            b.append((OK if v else AV)(f"**{'Sí' if v else 'No'}**: $" + sp.latex(a) + f"$ {'divide' if v else 'no divide'} a $" + sp.latex(c) + "$."))
            if v:
                b.append(T("Es decir, $" + sp.latex(c) + "$ es **múltiplo** de $" + sp.latex(a) + f"$ ($c = a\\cdot k$ con $k={q_}$)."))
            divs = sp.divisors(abs(int(c))) if c != 0 and abs(int(c)) < 10**7 else []
            if divs:
                b.append(T("Divisores de $" + sp.latex(c) + "$: " + ", ".join(str(d_) for d_ in divs) + "."))
            return res(b, valor=v)
        res_ = sp.simplify(sp.Mod(c, a))
        b.append(T(r"Con letras, «a ∣ b» equivale a que el resto de dividir sea 0: $b\bmod a=" + sp.latex(res_) + "$."))
        return res(b, valor=None)
    if isinstance(obj, Congruencia):
        a, c, n_ = obj.a, obj.b, obj.n
        b = [H("La afirmación"), L(sp.latex(a) + r"\equiv " + sp.latex(c) + r"\pmod{" + sp.latex(n_) + "}")]
        if not (n_.is_Integer and n_ > 0):
            raise ErrorCalculo("El módulo debe ser un entero positivo.")
        N = int(n_)
        if not a.free_symbols and not c.free_symbols:
            if not (a.is_Integer and c.is_Integer):
                raise ErrorCalculo("Las congruencias se definen entre números enteros.")
            d = int(a - c)
            v = d % N == 0
            b += [
                T("$" + sp.latex(a) + "-" + sp.latex(c) + f"={d}$ y ${d}\\div {N}$ " + (f"da {d // N} exacto." if v else f"deja resto {d % N}.")),
                T(f"Residuos módulo {N}: $" + sp.latex(a) + f"\\bmod {N}={int(a) % N}$ y $" + sp.latex(c) + f"\\bmod {N}={int(c) % N}$."),
                (OK if v else AV)(f"**{'Son congruentes' if v else 'NO son congruentes'}** módulo {N}" + (" (tienen el mismo residuo: $a-b$ es múltiplo de $n$)." if v else ".")),
            ]
            return res(b, valor=v)
        vars_ = sorted((a - c).free_symbols, key=lambda v: v.name)
        if len(vars_) != 1:
            raise ErrorCalculo("Para resolver una congruencia con letras se admite una sola variable.")
        x = vars_[0]
        P = sp.Poly(sp.expand(a - c), x)
        if P.degree() != 1:
            raise ErrorCalculo("Solo se resuelven congruencias LINEALES (a·x + b ≡ c mod n).")
        k1, k0 = P.coeff_monomial(x), P.coeff_monomial(1)
        if not (k1.is_Integer and k0.is_Integer):
            raise ErrorCalculo("Los coeficientes deben ser enteros.")
        k1, rhs = int(k1), int(-k0)
        g = math.gcd(k1 % N if k1 % N else N, N)
        b.append(T(f"Se resuelve ${k1}\\," + sp.latex(x) + f"\\equiv {rhs % N}\\pmod{{{N}}}$ (tras pasar los términos independientes)."))
        if (rhs % g) != 0:
            b.append(AV(f"**No tiene solución:** mcd({k1 % N}, {N}) = {g} no divide a {rhs % N}."))
            return res(b, valor=False)
        n2 = N // g
        x0 = (sp.mod_inverse(k1 // g, n2) * (rhs // g)) % n2 if n2 > 1 else 0
        b += [
            T(f"mcd = {g}, así que hay **{g}** solución(es) distintas módulo {N}."),
            OK("**Solución:** $" + sp.latex(x) + f"\\equiv {int(x0)}\\pmod{{{n2}}}$, es decir $" + sp.latex(x) + f"={int(x0)}+{n2}k$ con $k$ entero."),
        ]
        b.append(T("Algunas soluciones: " + ", ".join(str(int(x0) + n2 * k) for k in range(-2, 4)) + ", …"))
        return res(b, valor=None, solucion=(int(x0), n2))
    raise ErrorCalculo("No sé evaluar esa comparación.")


# ==============================================================================
# 9. DESPACHO
# ==============================================================================
@_op
def evaluar_estructura(obj):
    """Punto de entrada: decide qué análisis corresponde al objeto que el intérprete devolvió."""
    if isinstance(obj, Funcion):
        return M.dominio(obj.expr)
    if isinstance(obj, (Punto, Vector)):
        return analizar_vectorial(obj)
    if isinstance(obj, Lista):
        return analizar_lista(obj)
    if isinstance(obj, Pertenencia):
        return evaluar_pertenencia(obj)
    if isinstance(obj, RelConj):
        return evaluar_relconj(obj)
    if isinstance(obj, Cuantificado):
        return evaluar_cuantificado(obj)
    if isinstance(obj, Argumento):
        return evaluar_argumento(obj)
    if isinstance(obj, (Equivalencia, Aproximado, Divisibilidad, Congruencia)):
        return evaluar_comparacion(obj)
    if isinstance(obj, (Region, Bola, Espacio, ConjuntoImagen, OpTop, sp.Set)):
        return analizar_conjunto(obj)
    if isinstance(obj, sp.Basic) and obj.has(Norma, ProdPunto, Distancia, Angulo):
        return evaluar_vectorial(obj)
    if isinstance(obj, sp.logic.boolalg.Boolean) and not isinstance(obj, sp.Symbol):
        return evaluar_logica(obj)
    raise ErrorCalculo("No sé analizar este tipo de objeto.")
