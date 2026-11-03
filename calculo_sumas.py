"""
calculo_sumas.py
================
Sumatorias y productorias FINITAS con análisis paso a paso:

  · desarrollo de los términos (x₁ + x₂ + ⋯ + xₙ)
  · suma TELESCÓPICA (xᵢ − xᵢ₋₁, 1/(i(i+1)), ln((i+1)/i)…) con la explicación de qué se cancela
  · separación por LINEALIDAD (Σ(3xᵢ + 2) = 3Σxᵢ + 2n) y fórmulas cerradas de cada pieza
  · REINDEXADO (Σ xᵢ₋₁ = Σ xⱼ con j = i − 1)
  · sumas DOBLES (Σᵢ Σⱼ aᵢⱼ), con la tabla de términos cuando es pequeña
  · EVALUACIÓN con valores dados para los xᵢ (y x̄ = promedio automático)

Se registran en el mismo registro OPERACIONES que calculo_motor.py (corren en el proceso aislado).
"""
from __future__ import annotations

import re

import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _op, _simplificar, lx, res

_MAX_DESARROLLO = 8


def _l(e) -> str:
    return sp.latex(e)


def _fmt_suma(terminos) -> str:
    """Une términos con «+», dejando «−» cuando el término ya es negativo."""
    partes = []
    for t in terminos:
        s = _l(t)
        if isinstance(t, sp.Add):
            s = r"\left(" + s + r"\right)"
        partes.append(s)
    out = partes[0]
    for s in partes[1:]:
        out += (" " + s) if s.startswith("-") else (" + " + s)
    return out


def _desarrollo(f, k, a, b) -> str:
    """Los primeros y últimos términos de la suma, con puntos suspensivos si son muchos."""
    if a.is_Integer and b.is_Integer:
        n = int(b - a + 1)
        if n <= 0:
            return r"\text{(suma vacía: no hay términos)}"
        if n <= _MAX_DESARROLLO:
            return _fmt_suma([f.subs(k, a + j) for j in range(n)])
        return _fmt_suma([f.subs(k, a + j) for j in range(3)]) + r" + \cdots + " + _l(f.subs(k, b))
    return _fmt_suma([f.subs(k, a + j) for j in range(3)]) + r" + \cdots + " + _l(f.subs(k, b))


# ==============================================================================
# 1. TELESCOPADO
# ==============================================================================
def _normas(f, k):
    """Formas equivalentes de f donde un telescopado puede verse (expandida, fracciones parciales, logaritmos)."""
    formas = []
    if f.has(sp.log):                       # primero separar el logaritmo (expand() lo reescribiría como ln(1 + 1/i))
        try:
            formas.append(sp.expand(sp.expand_log(f, force=True)))
        except Exception:  # noqa: BLE001
            pass
    formas.append(sp.expand(f))
    try:
        if f.is_rational_function(k):
            formas.append(sp.apart(f, k))
    except Exception:  # noqa: BLE001
        pass
    return formas


def _telescopa(f, k):
    """
    Busca f(k) = F(k) − F(k+s) (+ resto) con s = −1 ó +1.
    Devuelve dict(F=..., s=..., resto=...) o None. `resto` es lo que NO se cancela.
    """
    for g in _normas(f, k):
        terminos = list(sp.Add.make_args(g))
        for s in (-1, 1):
            usados, F_terms = set(), []
            for t in terminos:
                if t in usados:
                    continue
                u = sp.expand(-t.subs(k, k + s))
                if u != t and u in terminos and u not in usados:
                    F_terms.append(t)
                    usados.update({t, u})
            if F_terms:
                F = sp.Add(*F_terms)
                resto = sp.Add(*[t for t in terminos if t not in usados])
                return {"F": F, "s": s, "resto": resto, "g": g}
    return None


def _bloques_telescopa(tele, f, k, a, b):
    F, s, resto = tele["F"], tele["s"], tele["resto"]
    Fk = F
    Fs = F.subs(k, k + s)
    blo = [H("Suma telescópica")]
    pat = _l(Fk) + (r"-\left(" + _l(Fs) + r"\right)" if isinstance(Fs, sp.Add) else "-" + _l(Fs)) if False else \
        _l(Fk) + "-" + (r"\left(" + _l(Fs) + r"\right)" if isinstance(Fs, sp.Add) else _l(Fs))
    if resto == 0:
        blo.append(T("El término se puede escribir como una **diferencia** de dos valores consecutivos, de modo que casi todo se **cancela** al sumar:"))
        blo.append(L(r"f(" + _l(k) + r")=" + pat))
    else:
        blo.append(T("Una parte del término es una diferencia de valores consecutivos (se cancela) y la otra no:"))
        blo.append(L(r"f(" + _l(k) + r")=\underbrace{" + pat + r"}_{\text{telescópica}}+\underbrace{" + _l(resto) + r"}_{\text{resto}}"))
    # ilustración: los primeros términos y cómo se cancelan
    if s == -1:
        ej = [Fk.subs(k, a + j) for j in range(3)], [Fs.subs(k, a + j) for j in range(3)]
        valor_tele = F.subs(k, b) - F.subs(k, a - 1)
        formula = r"\sum_{" + _l(k) + "=" + _l(a) + "}^{" + _l(b) + r"}\bigl[F(" + _l(k) + r")-F(" + _l(k) + r"-1)\bigr]=F(" + _l(b) + r")-F(" + _l(a - 1) + ")"
    else:
        ej = [Fk.subs(k, a + j) for j in range(3)], [Fs.subs(k, a + j) for j in range(3)]
        valor_tele = F.subs(k, a) - F.subs(k, b + 1)
        formula = r"\sum_{" + _l(k) + "=" + _l(a) + "}^{" + _l(b) + r"}\bigl[F(" + _l(k) + r")-F(" + _l(k) + r"+1)\bigr]=F(" + _l(a) + r")-F(" + _l(b + 1) + ")"
    filas = []
    for j in range(3):
        t1, t2 = ej[0][j], ej[1][j]
        filas.append([f"${_l(a + j)}$", f"${_l(t1)}$", f"$-\\left({_l(t2)}\\right)$"])
    blo.append(TAB([f"{_l(k)}", "entra (+)", "sale (−)"], filas))
    blo.append(T("Cada término que **sale** en un paso es el que **entra** en el siguiente (o en el anterior), así que se anulan. Solo sobreviven los de los extremos:"))
    blo.append(L(formula))
    blo.append(L(r"=" + _l(sp.simplify(valor_tele))))
    return blo, sp.simplify(valor_tele), resto


# ==============================================================================
# 2. LINEALIDAD
# ==============================================================================
def _lineal(f, k):
    """f = Σ cⱼ·gⱼ(k): lista [(cⱼ, gⱼ)] agrupando por la parte que depende de k. None si no hay nada que separar."""
    terminos = sp.Add.make_args(sp.expand(f))
    grupos: dict = {}
    for t in terminos:
        c, g = t.as_independent(k, as_Add=False)
        grupos[g] = grupos.get(g, 0) + c
    pares = [(sp.simplify(c), g) for g, c in grupos.items()]
    if len(terminos) == 1 and pares[0][0] == 1:
        return None
    return pares


def _bloques_lineal(pares, k, a, b):
    blo = [H("Separar por linealidad")]
    blo.append(T("Una suma de sumas es la suma de las sumas, y las constantes salen de la sumatoria: $\\sum (c\\,g+d)=c\\sum g+d\\sum 1$."))
    sg = r"\sum_{" + _l(k) + "=" + _l(a) + "}^{" + _l(b) + "}"
    izq = " + ".join((f"{_l(c)}\\," if c != 1 else "") + sg + (_l(g) if not isinstance(g, sp.Add) else r"\left(" + _l(g) + r"\right)") if g != 1 else
                     f"{_l(c)}\\," + sg + "1" for c, g in pares).replace("+ -", "- ")
    blo.append(L(izq))
    filas, total = [], 0
    for c, g in pares:
        S = sp.Sum(g, (k, a, b))
        try:
            v = sp.summation(g, (k, a, b))
        except Exception:  # noqa: BLE001
            v = S
        if v.has(sp.Sum):
            v = S
        filas.append([f"${sg}{_l(g)}$", f"${_l(sp.simplify(v)) if not v.has(sp.Sum) else _l(v)}$"])
        total += c * v
    blo.append(TAB(["pieza", "vale"], filas))
    return blo, total


# ==============================================================================
# 3. REINDEXADO
# ==============================================================================
def _desplazamientos(f, k):
    """Constantes c tales que algún elemento indexado de f tiene índice k + c (c ≠ 0)."""
    cs = set()
    for ix in f.atoms(sp.Indexed):
        for i in ix.indices:
            d = sp.simplify(i - k)
            if d.is_Integer and d != 0:
                cs.add(int(d))
    return sorted(cs)


def _bloque_reindexado(f, k, a, b):
    cs = _desplazamientos(f, k)
    if not cs:
        return []
    c = cs[0]
    j = sp.Symbol("j", integer=True)
    if j in f.free_symbols:
        j = sp.Symbol("m", integer=True)
    nuevo = f.subs(k, j - c)
    nuevo = sp.simplify(nuevo)
    ini, fin = a + c, b + c
    return [H("Reindexado (cambio de variable)"),
            T(f"Si llamas ${_l(j)}={_l(k)}{'+' if c > 0 else '-'}{abs(c)}$, la misma suma queda con los índices desplazados:"),
            L(r"\sum_{" + _l(k) + "=" + _l(a) + "}^{" + _l(b) + "}" + _l(f) + r"=\sum_{" + _l(j) + "=" + _l(ini) + "}^{" + _l(fin) + "}" + _l(nuevo)),
            IN("Cambiar el nombre o el desfase del índice no cambia el valor: solo desplaza dónde empieza y dónde termina.")]


# ==============================================================================
# 4. VALORES PARA LOS ELEMENTOS INDEXADOS
# ==============================================================================
def _sustituir_valores(expr, valores, inicio=1):
    """x[3] → valores['x'][3 - inicio]. Devuelve (expr, faltan) donde faltan = elementos sin valor."""
    faltan = set()
    medias = {}
    for nm, vs in valores.items():
        medias[nm] = sum(vs) / len(vs) if vs else 0

    def rep(e):
        nm = e.base.label.name
        if nm not in valores:
            return e
        if not all(i.is_Integer for i in e.indices):
            return e
        pos = int(e.indices[0]) - inicio
        if 0 <= pos < len(valores[nm]) and len(e.indices) == 1:
            return valores[nm][pos]
        faltan.add(e)
        return e

    out = expr.replace(lambda e: isinstance(e, sp.Indexed), rep)
    # x̄ = promedio de la lista x
    cambios = {}
    for s in out.free_symbols:
        m = re.match(r"^\\bar\{(.+)\}$", s.name) if isinstance(s, sp.Symbol) else None
        if m and m.group(1) in medias:
            cambios[s] = medias[m.group(1)]
    if cambios:
        out = out.xreplace(cambios)
    return out, faltan, cambios


def _bases_indexadas(obj):
    return sorted({ib.label.name for ib in obj.atoms(sp.IndexedBase)})


def _tabla_terminos(f, k, a, b, nombre):
    """Tabla de los términos cuando la suma es chica (≤ 12 términos)."""
    if not (a.is_Integer and b.is_Integer and 0 < int(b - a + 1) <= 12):
        return None
    return TAB([_l(k), "término"], [[f"${_l(a + j)}$", f"${_l(f.subs(k, a + j))}$"] for j in range(int(b - a + 1))])


# ==============================================================================
# 5. SUMA FINITA
# ==============================================================================
def _binomial_cerrado(f, k, a, b):
    """Teorema del binomio: Σ_{k=0}^{n} C(n,k)·cᵏ = (1+c)ⁿ  y  Σ k·C(n,k)·cᵏ = n·c·(1+c)ⁿ⁻¹. Devuelve (valor, explicación) o None."""
    if a != 0:
        return None
    bins = [t for t in f.atoms(sp.binomial) if t.args[1] == k]
    if len(bins) != 1 or sp.simplify(b - bins[0].args[0]) != 0:
        return None
    n_ = bins[0].args[0]
    resto = sp.simplify(f / bins[0])
    c = sp.Wild("c", exclude=[k])
    if resto == 1:
        m0, m1 = {c: sp.Integer(1)}, None
    elif resto == k:
        m0, m1 = None, {c: sp.Integer(1)}
    else:
        m0, m1 = resto.match(c ** k), resto.match(k * c ** k)
    if m0 is not None:
        cc = m0[c]
        val = sp.Integer(0) if cc == -1 else sp.simplify((1 + cc) ** n_)
        txt = r"\sum_{k=0}^{n}\binom{n}{k}c^{k}=(1+c)^{n}" + (r"\quad\text{con } c=" + sp.latex(cc))
        return val, txt, (" (para $n\\ge1$; con $c=-1$ queda $0^n=0$)" if cc == -1 else "")
    if m1 is not None:
        cc = m1[c]
        return sp.simplify(n_ * cc * (1 + cc) ** (n_ - 1)), r"\sum_{k=0}^{n}k\binom{n}{k}c^{k}=nc(1+c)^{n-1}\quad\text{con } c=" + sp.latex(cc), ""
    return None


def _valor_cerrado(f, k, a, b):
    try:
        v = sp.summation(f, (k, a, b))
    except Exception:  # noqa: BLE001
        return None
    return None if v.has(sp.Sum) else v


@_op
def evaluar_suma(obj, valores=None, inicio=1):
    """Σ finita (una o varias variables de suma): estructura, método y valor."""
    if isinstance(obj, sp.Product):
        return evaluar_producto(obj, valores, inicio)
    limites = list(obj.limits)
    f = obj.function
    b = [H("La suma"), L(_l(obj))]
    bases = _bases_indexadas(obj)
    if bases:
        b.append(IN("Los subíndices que usan el índice de la suma (" + ", ".join(f"$ {_l(sp.Symbol(nm))}_{{i}}$" for nm in bases[:2]) +
                    ") son **elementos de una lista**: $x_i$ es el i-ésimo valor de $x$. Como no conozco esos valores, la respuesta se deja en términos de ellos, "
                    "a menos que me los des abajo."))
    if len(limites) > 1:
        return _suma_multiple(obj, b, valores, inicio)
    k, a, bb = limites[0]
    if bb in (sp.oo, -sp.oo) or a in (sp.oo, -sp.oo):
        raise ErrorCalculo("Esta suma tiene un límite infinito: es una **serie**. Para analizarla necesito la fórmula del término general en una sola variable (sin xᵢ desconocidos).")
    if sp.simplify(bb - a + 1) .is_negative:
        b.append(AV("El límite superior es menor que el inferior: la suma está **vacía** y vale 0 (por convención)."))
        return res(b, valor=sp.Integer(0))
    b += [H("Desarrollo de los términos"), L(_desarrollo(f, k, a, bb))]
    t = _tabla_terminos(f, k, a, bb, "")
    if t is not None and not f.atoms(sp.Indexed):
        b.append(t)
    b += _bloque_reindexado(f, k, a, bb)
    valor = None
    metodo = None
    tele = _telescopa(f, k)
    if tele:
        blo, vtele, resto = _bloques_telescopa(tele, f, k, a, bb)
        b += blo
        valor, metodo = vtele, "telescópica"
        if resto != 0:
            rv = _valor_cerrado(resto, k, a, bb)
            valor = vtele + (rv if rv is not None else sp.Sum(resto, (k, a, bb)))
            b.append(T("La parte restante se suma aparte: $" + _l(sp.Sum(resto, (k, a, bb))) + ("=" + _l(sp.simplify(rv)) if rv is not None else "") + "$."))
    else:
        pares = _lineal(f, k)
        if pares and (len(pares) > 1 or pares[0][0] != 1):
            blo, total = _bloques_lineal(pares, k, a, bb)
            b += blo
            valor, metodo = total, "lineal"
        cerrado = _valor_cerrado(f, k, a, bb)
        if cerrado is None:
            bn = _binomial_cerrado(f, k, a, bb)
            if bn is not None:
                cerrado, formula, nota = bn
                b += [H("Teorema del binomio"), T("$(1+c)^n=\\sum_{k=0}^{n}\\binom{n}{k}c^k$: la suma es una evaluación del desarrollo del binomio."), L(formula)]
                if nota:
                    b.append(IN(nota))
                metodo = "binomio"
        if cerrado is not None:
            valor = cerrado
            if metodo is None:
                metodo = "fórmula"
    if valor is None:
        if not bases:
            raise ErrorCalculo("No encontré una fórmula cerrada para esta suma.")
        b.append(IN("Como depende de los valores de " + ", ".join(f"${_l(sp.Symbol(nm))}_i$" for nm in bases) + ", **no se reduce a una fórmula**: queda indicada tal cual. "
                    "Escribe los valores en la caja de abajo para obtener un número."))
        if valores:
            b += _evaluar_con_valores(obj, valores, inicio)
        return res(b, valor=obj, metodo=None)
    valor = _simplificar(sp.simplify(valor)) if not valor.has(sp.Sum) else valor
    b.append(OK(f"**Resultado:** ${lx(valor)}$" + ("" if valor.is_Integer or valor.free_symbols else f" $\\approx {_l(sp.N(valor, 10))}$")))
    if bb.free_symbols and not valor.has(sp.Sum):
        b.append(IN("Es una **fórmula en función de** " + ", ".join(f"${_l(s)}$" for s in sorted(bb.free_symbols, key=lambda v: v.name)) + "."))
    # comprobación numérica con un caso concreto
    if bb.free_symbols and not valor.has(sp.Sum) and not f.atoms(sp.Indexed):
        n_ = list(bb.free_symbols)[0]
        try:
            for n0 in (4, 7):
                if bb.subs(n_, n0) - a + 1 > 0:
                    real = sp.summation(f.subs(bb, bb), (k, a, bb.subs(n_, n0)))
                    formula = valor.subs(n_, n0)
                    if sp.simplify(real - formula) == 0:
                        b.append(IN(f"✅ Comprobación con ${_l(n_)}={n0}$: la suma término a término da ${_l(sp.simplify(real))}$, igual que la fórmula."))
                        break
        except Exception:  # noqa: BLE001
            pass
    # evaluación con valores
    out = {"valor": valor, "metodo": metodo}
    if valores and bases:
        b += _evaluar_con_valores(obj, valores, inicio)
    return res(b, **out)


def _evaluar_con_valores(obj, valores, inicio):
    b = [H("Evaluación con tus valores")]
    ls = {nm: [sp.nsimplify(v) for v in vs] for nm, vs in valores.items() if vs}
    if not ls:
        return []
    for nm, vs in ls.items():
        b.append(T(f"${_l(sp.Symbol(nm))}$: " + ", ".join(f"$ {_l(sp.Symbol(nm))}_{{{inicio + i}}}={_l(v)}$" for i, v in enumerate(vs[:8])) + (" …" if len(vs) > 8 else "")))
    expr = obj
    sub_n = {}
    for (k, a, bb) in obj.limits:
        for sym in bb.free_symbols:
            if sym not in sub_n:
                largo = max(len(v) for v in ls.values())
                sub_n[sym] = largo + inicio - 1
    if sub_n:
        b.append(IN("Tomé " + ", ".join(f"${_l(s)}={v}$" for s, v in sub_n.items()) + " (la cantidad de valores dados)."))
        expr = expr.subs(sub_n)
    try:
        expr = expr.doit()
    except Exception:  # noqa: BLE001
        pass
    expr, faltan, medias = _sustituir_valores(expr, ls, inicio)
    if medias:
        b.append(IN("Usé como " + ", ".join(f"${_l(s)}$" for s in medias) + " el **promedio** de los valores dados: " + ", ".join(f"${_l(v)}$" for v in medias.values()) + "."))
    if faltan:
        b.append(AV("Faltan valores para: " + ", ".join(f"${_l(e)}$" for e in sorted(faltan, key=str)) + ". Agrega más datos a la lista."))
        return b
    val = sp.simplify(expr)
    if val.free_symbols:
        b.append(AV(f"Aún quedan letras sin valor: ${_l(val)}$"))
    else:
        b.append(OK(f"**Valor con tus datos:** ${_l(val)}$" + ("" if val.is_Integer else f" $\\approx {_l(sp.N(val, 10))}$")))
    return b


def _suma_multiple(obj, b, valores, inicio):
    lims = list(obj.limits)          # el primero es la suma INTERIOR
    f = obj.function
    nombres = " y ".join(f"${_l(k)}$" for k, _, _ in lims)
    b.append(T(f"Es una **suma doble** (o múltiple): se suma primero sobre ${_l(lims[0][0])}$ (la interior) y después sobre " + ", ".join(f"${_l(k)}$" for k, _, _ in lims[1:]) + ". Se suma sobre " + nombres + "."))
    # tabla de términos si es chica
    if len(lims) == 2 and all(a.is_Integer and bb.is_Integer for _, a, bb in lims):
        (kj, aj, bj), (ki, ai, bi) = lims
        nj, ni = int(bj - aj + 1), int(bi - ai + 1)
        if 0 < ni <= 6 and 0 < nj <= 6:
            enc = [f"{_l(ki)} \\ {_l(kj)}"] + [f"${_l(aj + c)}$" for c in range(nj)] + ["fila"]
            filas = []
            for r in range(ni):
                fila = [f"${_l(ai + r)}$"]
                suma_fila = 0
                for c in range(nj):
                    t = f.subs({ki: ai + r, kj: aj + c})
                    fila.append(f"${_l(t)}$")
                    suma_fila += t
                fila.append(f"${_l(sp.simplify(suma_fila))}$")
                filas.append(fila)
            b += [H("Tabla de términos (filas = " + _l(ki) + ", columnas = " + _l(kj) + ")"), TAB(enc, filas)]
    # evaluación por etapas
    interior = sp.Sum(f, lims[0])
    try:
        vi = sp.summation(f, lims[0])
    except Exception:  # noqa: BLE001
        vi = interior
    if not vi.has(sp.Sum):
        b += [H("Primero la suma interior"), L(_l(interior) + "=" + _l(sp.simplify(vi)))]
    try:
        total = sp.summation(f, *lims)
    except Exception:  # noqa: BLE001
        total = None
    if total is not None and not total.has(sp.Sum):
        total = _simplificar(sp.simplify(total))
        b.append(OK(f"**Resultado:** ${lx(total)}$" + ("" if total.is_Integer or total.free_symbols else f" $\\approx {_l(sp.N(total, 10))}$")))
        if len(lims) == 2 and f.is_polynomial() is False:
            pass
        out = {"valor": total}
    else:
        b.append(AV("No hay una fórmula cerrada con los datos como están; se deja indicada la suma doble."))
        out = {"valor": obj}
    if valores and _bases_indexadas(obj):
        b += _evaluar_con_valores(obj, valores, inicio)
    return res(b, **out)


# ==============================================================================
# 6. PRODUCTORIA FINITA
# ==============================================================================
def _telescopa_producto(f, k):
    """f(k) = A(k)/A(k−1)  ó  A(k−1)/A(k). Devuelve (A, s) o None."""
    num, den = sp.fraction(sp.together(f))
    for s in (-1, 1):
        cand = [num, 1 / den if False else den]
        # f = N(k)/D(k) con D(k) = N(k+s)  ⇒  f = N(k)/N(k+s)
        if sp.simplify(den - num.subs(k, k + s)) == 0:
            return num, s
    return None


@_op
def evaluar_producto(obj, valores=None, inicio=1):
    f = obj.function
    k, a, bb = obj.limits[0]
    b = [H("La productoria"), L(_l(obj))]
    if bb in (sp.oo, -sp.oo):
        raise ErrorCalculo("Este producto es infinito: se analiza como producto infinito (no con elementos indexados desconocidos).")
    b += [H("Desarrollo de los factores"), L(_desarrollo(f, k, a, bb).replace(" + ", r" \cdot ").replace("+", r"\cdot "))]
    valor = None
    tele = _telescopa_producto(f, k)
    if tele:
        A, s = tele
        if s == 1:
            valor = A.subs(k, a) / A.subs(k, bb + 1)
        else:
            valor = A.subs(k, bb) / A.subs(k, a - 1)
        b += [H("Producto telescópico"), T("Cada factor es un **cociente de valores consecutivos**, así que casi todo se cancela:"),
              L(r"f(" + _l(k) + r")=\frac{" + _l(A) + "}{" + _l(A.subs(k, k + s)) + "}"),
              L(r"\prod_{" + _l(k) + "=" + _l(a) + "}^{" + _l(bb) + r"}f(" + _l(k) + r")=" + _l(sp.simplify(valor)))]
    else:
        try:
            v = sp.product(f, (k, a, bb))
            if not v.has(sp.Product):
                valor = v
        except Exception:  # noqa: BLE001
            valor = None
    if valor is None:
        raise ErrorCalculo("No encontré una fórmula cerrada para esta productoria. Si tiene elementos xᵢ, dame sus valores para evaluarla.")
    valor = sp.simplify(valor)
    b.append(OK(f"**Resultado:** ${lx(valor)}$"))
    if valores and _bases_indexadas(obj):
        b += _evaluar_con_valores(obj, valores, inicio)
    return res(b, valor=valor)


# ==============================================================================
# 7. EXPRESIONES CON ELEMENTOS INDEXADOS FUERA DE UNA SUMA  (aᵢ₊₁/aᵢ, xᵢ − xᵢ₋₁…)
# ==============================================================================
@_op
def evaluar_indexada(expr):
    """Expresión con elementos indexados: qué significa, simplificación y valores del índice."""
    b = [H("La expresión"), L(_l(expr))]
    idx_syms = sorted({s for ix in expr.atoms(sp.Indexed) for i in ix.indices for s in i.free_symbols}, key=lambda v: v.name)
    bases = _bases_indexadas(expr)
    b.append(T("Aquí " + ", ".join(f"${_l(sp.Symbol(nm))}_{{k}}$" for nm in bases) + " es el elemento número $k$ de una lista " + ", ".join(f"${_l(sp.Symbol(nm))}$" for nm in bases)
               + ". Los **subíndices con operaciones** (como $i-1$ o $n+1$) se refieren a elementos vecinos."))
    simp = sp.simplify(expr)
    if simp != expr:
        b += [H("Simplificada"), L(_l(expr) + "=" + _l(simp))]
    if len(idx_syms) == 1:
        i = idx_syms[0]
        filas = []
        for v in range(1, 6):
            filas.append([f"${_l(i)}={v}$", f"${_l(sp.simplify(expr.subs(i, v)))}$"])
        b += [H(f"Para varios valores de {_l(i)}"), TAB([_l(i), "expresión"], filas)]
    elif len(idx_syms) > 1:
        b.append(IN("Tiene varios índices (" + ", ".join(_l(s) for s in idx_syms) + "): sustituye valores concretos para evaluarla."))
    return res(b, valor=simp)
