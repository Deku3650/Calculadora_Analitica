"""
calculo_integrales_multiples.py
===============================
Integrales DOBLES y TRIPLES sobre una región dada como conjunto de desigualdades, bola, producto de
intervalos, etc.  La app deduce los límites de integración y muestra todo el procedimiento.

Cómo se obtienen los límites (para un orden de integración dado, de afuera hacia adentro):
  1. Se resuelve cada desigualdad respecto de la variable INTERIOR: lineal (cota inferior o superior) o
     cuadrática (entre las dos raíces; el discriminante ≥ 0 es una condición sobre las variables exteriores).
  2. Si hay varias cotas se elige el máximo/mínimo comprobando en puntos de muestra de la región exterior.
  3. La región exterior (las condiciones que no dependen de la variable interior + la factibilidad
     «cota inferior ≤ cota superior») se resuelve igual, una variable menos, hasta llegar a intervalos de ℝ.
  4. Para polares, cilíndricas y esféricas se sustituye, se quita el factor radial (r > 0, ρ > 0) y se aplica el
     mismo procedimiento; se agrega el jacobiano (r, r, ρ² sen φ).

Siempre se contrasta el resultado con un cálculo de Monte Carlo (evidencia numérica).
"""
from __future__ import annotations

import itertools
import math
import signal
import time

import numpy as np
import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _flt, _op, res
from estructuras import Bola, Region, Espacio, variables_por_defecto, lectura_de


class _SinSolucion(Exception):
    """No se pudo plantear (o resolver) la integral con ese orden / sistema de coordenadas."""


def _l(e) -> str:
    return sp.latex(e)


def _n(v, d=7) -> str:
    f = _flt(v)
    if f is None:
        return _l(v)
    return str(int(round(f))) if abs(f - round(f)) < 1e-9 else f"{f:.{d}g}"


# ==============================================================================
# 0. ÁTOMOS (desigualdades) DE LA REGIÓN
# ==============================================================================
_OPS = {sp.Lt: "<", sp.Le: "<=", sp.Gt: ">", sp.Ge: ">=", sp.Eq: "=", sp.Ne: "!="}


def _tipo(rel):
    for c, o in _OPS.items():
        if isinstance(rel, c):
            return o
    return None


def _atomos_de(cond):
    """Región → lista de desigualdades normalizadas a  g ≤ 0  (g, es_estricta). Solo una conjunción (sin uniones)."""
    cond = sp.simplify(cond) if sp.count_ops(cond) < 60 else cond
    d = sp.to_dnf(cond, simplify=False)
    cs = d.args if isinstance(d, sp.Or) else [d]
    if len(cs) > 1:
        raise _SinSolucion("La región es una UNIÓN de piezas: sepárala en regiones disjuntas e integra cada una (por ejemplo con dos integrales).")
    c = cs[0]
    if c == sp.false:
        return []
    out = []
    for a in (c.args if isinstance(c, sp.And) else [c]):
        if a == sp.true:
            continue
        op = _tipo(a) if isinstance(a, sp.core.relational.Relational) else None
        if op is None:
            raise _SinSolucion("La región usa una condición que no es una desigualdad entre expresiones.")
        g = a.lhs - a.rhs
        if op in (">", ">="):
            g, op = -g, "<" if op == ">" else "<="
        if op == "=":
            raise _SinSolucion("La región tiene una IGUALDAD (curva o superficie): tiene medida cero; la integral sobre ella no es una integral doble/triple.")
        if op == "!=":
            continue
        out.append((sp.expand(g), op == "<"))
    return out


# ==============================================================================
# 1. LÍMITES ITERADOS
# ==============================================================================
def _signo(v):
    v = sp.simplify(v)
    if v.is_positive:
        return 1
    if v.is_negative:
        return -1
    if not v.free_symbols:
        f = _flt(v)
        if f is not None and abs(f) > 1e-14:
            return 1 if f > 0 else -1
    return None


def _cotas(atomos, v):
    """Para la variable interior v: (cotas inferiores, superiores, átomos que no la usan, átomos de factibilidad)."""
    bajas, altas, resto, feas = [], [], [], []
    por_atomo = []
    for g, est in atomos:
        if not g.has(v):
            resto.append((g, est))
            continue
        try:
            P = sp.Poly(g, v)
        except sp.PolynomialError:
            raise _SinSolucion(f"No sé despejar {v} en la desigualdad «{g} ≤ 0».") from None
        co = P.all_coeffs()
        if P.degree() == 1:
            a, b = co
            s = _signo(a)
            if s is None:
                raise _SinSolucion("No pude decidir el signo de un coeficiente (depende de las variables).")
            raiz = sp.simplify(-b / a)
            (altas if s > 0 else bajas).append((raiz, len(por_atomo)))
            por_atomo.append(raiz)
        elif P.degree() == 2:
            a, b, c = co
            s = _signo(a)
            if s == -1 and v.is_nonnegative and sp.simplify(b) == 0:
                # a v² + c ≤ 0 con a < 0 y v ≥ 0  ⇒  v ≥ √(c / (−a))   (corona: r² ≥ 1)
                cc = sp.simplify(c / (-a))
                if cc.free_symbols:
                    raise _SinSolucion("No pude decidir el signo del radio de una corona.")
                if _flt(cc) is not None and _flt(cc) > 0:
                    bajas.append((sp.sqrt(cc), len(por_atomo)))
                por_atomo.append(None)
                continue
            if s != 1:
                raise _SinSolucion("La región, vista como función de " + str(v) + ", queda FUERA de dos raíces (no es un intervalo): "
                                   "prueba otro orden o coordenadas polares/esféricas.")
            D = sp.expand(b ** 2 - 4 * a * c)
            r1, r2 = sp.simplify((-b - sp.sqrt(D)) / (2 * a)), sp.simplify((-b + sp.sqrt(D)) / (2 * a))
            idx = len(por_atomo)
            bajas.append((r1, idx))
            altas.append((r2, idx))
            por_atomo.append(None)
            feas.append((-D, False))                      # D ≥ 0  ⇔  −D ≤ 0
        else:
            raise _SinSolucion(f"Una desigualdad de grado {P.degree()} en {v}: no sé despejarla.")
    # factibilidad entre cotas de átomos distintos: baja ≤ alta
    for (l, il), (u, iu) in itertools.product(bajas, altas):
        if il != iu:
            dif = sp.simplify(l - u)
            if dif.free_symbols:
                feas.append((dif, False))
            elif _flt(dif) is not None and _flt(dif) > 1e-12:
                raise _SinSolucion("La región es vacía (cotas incompatibles).")
    return [x for x, _ in bajas], [x for x, _ in altas], resto, feas


def _resolver_1d(atomos, v, base):
    """Intervalos (lista) de v ∈ base que cumplen todos los átomos (que solo dependen de v)."""
    S = base
    for g, est in atomos:
        rel = sp.Lt(g, 0) if est else sp.Le(g, 0)
        try:
            sol = sp.solveset(rel, v, base if base != sp.S.Reals else sp.S.Reals)
        except Exception:  # noqa: BLE001
            raise _SinSolucion("No pude resolver una desigualdad en una variable.") from None
        if isinstance(sol, sp.ConditionSet):
            raise _SinSolucion("No pude resolver una desigualdad en una variable.")
        S = sp.Intersection(S, sol)
    partes = list(S.args) if isinstance(S, sp.Union) else [S]
    ints = []
    for p in partes:
        if isinstance(p, sp.Interval) and p.start != p.end:
            if not (p.start.is_finite and p.end.is_finite):
                raise _SinSolucion("La región no está acotada (la integral sería impropia).")
            ints.append(p)
        elif isinstance(p, (sp.FiniteSet, type(sp.S.EmptySet))):
            continue
        else:
            raise _SinSolucion("La región exterior no es un intervalo.")
    if not ints:
        raise _SinSolucion("La región es vacía o de medida cero.")
    return ints


def _muestras(tramo, k=9):
    """Puntos de prueba (dict) dentro de la región exterior descrita por `tramo`."""
    pts = [{}]
    for v, a, b in tramo:
        nuevos = []
        for p in pts:
            try:
                lo, hi = float(sp.N(a.subs(p))), float(sp.N(b.subs(p)))
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(lo) and math.isfinite(hi)) or hi < lo:
                continue
            for fr in (0.2, 0.5, 0.8):
                nuevos.append({**p, v: lo + (hi - lo) * fr})
        pts = nuevos[:k * 3]
    return pts[:k]


def _elegir(cands, tramo, modo):
    """Entre varias cotas, la que domina (máximo para inferiores, mínimo para superiores) en la región exterior."""
    uniq = []
    for c in cands:
        if all(sp.simplify(c - u) != 0 for u in uniq):
            uniq.append(c)
    if len(uniq) == 1:
        return uniq[0]
    pts = _muestras(tramo)
    if not pts:
        raise _SinSolucion("No pude comparar las cotas.")
    vals = []
    for c in uniq:
        try:
            vals.append([float(sp.N(c.subs(p))) for p in pts])
        except (TypeError, ValueError):
            raise _SinSolucion("No pude evaluar una cota.") from None
    for i, c in enumerate(uniq):
        ok = all((vals[i][j] >= max(v[j] for v in vals) - 1e-9) if modo == "max" else (vals[i][j] <= min(v[j] for v in vals) + 1e-9) for j in range(len(pts)))
        if ok:
            return c
    raise _SinSolucion("Las cotas se cruzan dentro de la región: hay que partirla en trozos (prueba otro orden).")


def _limites(atomos, vs, bases):
    """Tramos [[(v, lo, hi), …]] de afuera hacia adentro, para el orden vs = [exterior, …, interior]."""
    v = vs[-1]
    if len(vs) == 1:
        return [[(v, p.start, p.end)] for p in _resolver_1d(atomos, v, bases.get(v, sp.S.Reals))]
    bajas, altas, resto, feas = _cotas(atomos, v)
    if not bajas or not altas:
        raise _SinSolucion(f"{v} no está acotada por la región (integral impropia).")
    sub = _limites(resto + feas, vs[:-1], bases)
    out = []
    for tr in sub:
        lo, hi = _elegir(bajas, tr, "max"), _elegir(altas, tr, "min")
        out.append(tr + [(v, lo, hi)])
    return out


# ==============================================================================
# 2. COORDENADAS: polares, cilíndricas, esféricas
# ==============================================================================
def _sin_factor_radial(atomos, rad):
    """r > 0: de una desigualdad  r^m · h ≤ 0  se conserva  h ≤ 0."""
    out = []
    for g, est in atomos:
        g = sp.expand(sp.trigsimp(g))
        if g.has(rad):
            try:
                P = sp.Poly(g, rad)
                m = min(mon[0] for mon in P.monoms())
                if m > 0:
                    g = sp.expand(sp.simplify(g / rad ** m))
            except sp.PolynomialError:
                pass
        if g.free_symbols:
            out.append((g, est))
        elif _flt(g) is not None and _flt(g) > 1e-12:
            raise _SinSolucion("Región vacía.")
    return out


def _centro(atomos, vars_):
    """Centro (dict variable → coordenada) si las desigualdades cuadráticas son círculos/esferas (x−a)²+(y−b)²…; si no, {}."""
    cs = {}
    for g, _ in atomos:
        try:
            P = sp.Poly(g, *vars_)
        except sp.PolynomialError:
            continue
        if P.total_degree() != 2:
            continue
        ks = {v: P.coeff_monomial(v ** 2) for v in vars_}
        inv = [v for v in vars_ if ks[v] != 0]
        if len(inv) < 2:
            continue
        k = ks[inv[0]]
        if any(sp.simplify(ks[v] - k) != 0 for v in inv):
            continue
        if any(P.coeff_monomial(a * b) != 0 for a, b in itertools.combinations(inv, 2)):
            continue
        for v in inv:
            c = sp.simplify(-P.coeff_monomial(v) / (2 * k))
            if v in cs and sp.simplify(cs[v] - c) != 0:
                return {}
            cs[v] = c
    return cs


def _pistas(atomos, vars_):
    """('esfera' | 'circulo' | None): ¿la región es redonda? (conviene polares/cilíndricas/esféricas)."""
    esfera = circulo = False
    for g, _ in atomos:
        try:
            P = sp.Poly(g, *vars_)
        except sp.PolynomialError:
            continue
        if P.total_degree() != 2:
            continue
        ks = {v: P.coeff_monomial(v ** 2) for v in vars_}
        inv = [v for v in vars_ if ks[v] != 0]
        if len(inv) >= 2 and all(sp.simplify(ks[v] - ks[inv[0]]) == 0 for v in inv) and not any(P.coeff_monomial(a * b) != 0 for a, b in itertools.combinations(inv, 2)):
            if len(inv) == len(vars_) and len(vars_) == 3:
                esfera = True
            elif set(inv) >= set(vars_[:2]):
                circulo = True
    return "esfera" if esfera else ("circulo" if circulo else None)


def _sistema(nombre, vars_, centro=None):
    """(sustitución, jacobiano, orden exterior→interior, dominios, símbolos, variable radial, desigualdades naturales)."""
    c = centro or {}
    cx, cy = c.get(vars_[0], 0), c.get(vars_[1], 0)
    if nombre == "polares":
        r, th = sp.symbols("r theta", real=True, nonnegative=True)
        nat = [(-r, False), (-th, False), (th - 2 * sp.pi, False)]
        return {vars_[0]: cx + r * sp.cos(th), vars_[1]: cy + r * sp.sin(th)}, r, [th, r], {th: sp.Interval(0, 2 * sp.pi)}, (r, th), r, nat
    if nombre == "cilíndricas":
        r, th = sp.symbols("r theta", real=True, nonnegative=True)
        z = vars_[2]
        nat = [(-r, False), (-th, False), (th - 2 * sp.pi, False)]
        return {vars_[0]: cx + r * sp.cos(th), vars_[1]: cy + r * sp.sin(th)}, r, [th, r, z], {th: sp.Interval(0, 2 * sp.pi)}, (r, th, z), r, nat
    if nombre == "esféricas":
        rho, ph, th = sp.symbols("rho phi theta", real=True, nonnegative=True)
        cz = c.get(vars_[2], 0)
        nat = [(-rho, False), (-ph, False), (ph - sp.pi, False), (-th, False), (th - 2 * sp.pi, False)]
        return ({vars_[0]: cx + rho * sp.sin(ph) * sp.cos(th), vars_[1]: cy + rho * sp.sin(ph) * sp.sin(th), vars_[2]: cz + rho * sp.cos(ph)},
                rho ** 2 * sp.sin(ph), [th, ph, rho], {th: sp.Interval(0, 2 * sp.pi), ph: sp.Interval(0, sp.pi)}, (rho, ph, th), rho, nat)
    raise _SinSolucion("Sistema de coordenadas desconocido.")


# ==============================================================================
# 3. INTEGRACIÓN ITERADA
# ==============================================================================
class _Tiempo(Exception):
    pass


_ESPECIALES = [True]          # ¿rechazar funciones especiales (erf, Ei…)? Se desactiva si todos los órdenes las producen


def _con_limite(seg, fn, *a):
    """Ejecuta fn con un tope de tiempo (si el sistema lo permite)."""
    def _h(sig, frm):
        raise _Tiempo()
    try:
        viejo = signal.signal(signal.SIGALRM, _h)
        signal.setitimer(signal.ITIMER_REAL, seg)
    except (ValueError, AttributeError, OSError):
        return fn(*a)
    try:
        return fn(*a)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, viejo)


def _integrar(f, tramo, tope=12):
    """Integral iterada exacta de f sobre un tramo. Devuelve (valor, pasos). Lanza _SinSolucion si no hay forma cerrada."""
    expr, pasos = f, []
    for v, lo, hi in reversed(tramo):
        try:
            nuevo = _con_limite(tope, lambda e=expr, vv=v, a=lo, b=hi: sp.integrate(e, (vv, a, b)))
        except _Tiempo:
            raise _SinSolucion("SymPy tardó demasiado integrando con este orden.") from None
        if nuevo.has(sp.Integral):
            raise _SinSolucion(f"No hay una primitiva sencilla al integrar respecto de {v} con este orden.")
        if _ESPECIALES[0] and nuevo.has(sp.erf, sp.erfi, sp.erfc, sp.Ei, sp.Si, sp.Ci, sp.fresnels, sp.fresnelc, sp.polylog, sp.uppergamma, sp.lowergamma):
            raise _SinSolucion(f"Al integrar respecto de {v} aparece una función especial (erf, Ei…): con este orden no hay primitiva elemental.")
        nuevo = sp.simplify(nuevo)
        pasos.append((v, lo, hi, nuevo))
        expr = nuevo
    return expr, pasos


def _latex_iterada(f, tramo, difs=None):
    """\\int_a^b \\int_c^d f dy dx"""
    izq = "".join(r"\int_{" + _l(lo) + "}^{" + _l(hi) + "}" for v, lo, hi in tramo)
    der = "".join(r"\,d" + _l(v) for v, lo, hi in reversed(tramo))
    return izq + _l(f) + der


def _nquad(f, tramo, vars_):
    """Integral numérica (scipy.nquad) con límites que dependen de las variables exteriores."""
    from scipy import integrate
    orden = [v for v, _, _ in tramo]                       # exterior → interior
    ff = sp.lambdify(list(reversed(orden)), f, "numpy")
    def b_(k):
        v, lo, hi = tramo[k]
        fo, fh = sp.lambdify(orden[:k], lo, "numpy"), sp.lambdify(orden[:k], hi, "numpy")
        # nquad pasa los argumentos de las variables ya fijadas en orden INVERSO (interior primero)
        return lambda *args: (float(fo(*reversed(args))) if args else float(fo()), float(fh(*reversed(args))) if args else float(fh()))
    rangos = []
    for k in reversed(range(len(tramo))):
        v, lo, hi = tramo[k]
        if k == 0:
            rangos.append((float(sp.N(lo)), float(sp.N(hi))))
        else:
            fo, fh = sp.lambdify(orden[:k], lo, "numpy"), sp.lambdify(orden[:k], hi, "numpy")
            rangos.append(lambda *args, fo=fo, fh=fh: (float(fo(*reversed(args))), float(fh(*reversed(args)))))
    val, err = integrate.nquad(ff, rangos, opts={"limit": 60, "epsabs": 1e-9, "epsrel": 1e-9})
    return val, err


def _mc(f, cond, vars_, caja, N=400_000, seed=21):
    """Monte Carlo: (valor, error estándar)."""
    ff = sp.lambdify(vars_, f, "numpy")
    fc = sp.lambdify(vars_, cond, "numpy")
    rng = np.random.default_rng(seed)
    lo = np.array([c[0] for c in caja])
    hi = np.array([c[1] for c in caja])
    P = rng.uniform(lo, hi, size=(N, len(vars_)))
    cols = [P[:, i] for i in range(len(vars_))]
    with np.errstate(all="ignore"):
        dentro = np.broadcast_to(np.asarray(fc(*cols), dtype=bool), (N,))
        v = np.where(dentro, np.broadcast_to(np.asarray(ff(*cols), dtype=float), (N,)), 0.0)
    vol = float(np.prod(hi - lo))
    v = np.nan_to_num(v)
    return float(v.mean() * vol), float(v.std() / math.sqrt(N) * vol)


def _caja_region(cond, vars_, B=12.0):
    """Caja envolvente de la región (refinando por pasos: en regiones pequeñas hay pocos puntos al principio); None si no está acotada."""
    fc = sp.lambdify(vars_, cond, "numpy")
    rng = np.random.default_rng(5)
    n = len(vars_)
    lo, hi = np.full(n, -B), np.full(n, B)
    for paso in range(6):
        P = rng.uniform(lo, hi, size=(400_000, n))
        with np.errstate(all="ignore"):
            ok = np.broadcast_to(np.asarray(fc(*[P[:, i] for i in range(n)]), dtype=bool), (len(P),))
        if ok.sum() < 8:
            if paso == 0:
                return None
            break
        d = P[ok]
        nlo, nhi = d.min(axis=0), d.max(axis=0)
        if paso == 0 and ((np.abs(nlo) > 0.97 * B).any() or (np.abs(nhi) > 0.97 * B).any()):
            return None
        ext = nhi - nlo
        lo, hi = nlo - 0.25 * ext - 1e-9, nhi + 0.25 * ext + 1e-9
    return list(zip(lo, hi))


# ==============================================================================
# 4. PLANTEAR Y RESOLVER
# ==============================================================================
def _plantear(f, atomos, vars_, sistema=None, orden_ext=None):
    """Devuelve (f_en_nuevas_variables, tramos, orden_exterior_a_interior, simbolos_de_coordenadas)."""
    if sistema is None:
        orden = list(orden_ext)
        return f, _limites(atomos, orden, {}), orden, vars_
    sust, jac, orden, bases, simbolos, rad, nat = _sistema(sistema, vars_, _centro(atomos, vars_))
    nuevos = []
    for g, est in atomos:
        gg = sp.simplify(g.subs(sust, simultaneous=True))
        nuevos.append((sp.expand(gg), est))
    nuevos = _sin_factor_radial(nuevos, rad) + nat          # el factor radial se descarta; r ≥ 0 y los rangos de φ, θ se agregan
    tramos = _limites(nuevos, orden, bases)
    fn = sp.simplify(f.subs(sust, simultaneous=True) * jac)
    return fn, tramos, orden, simbolos


def _validar(f, atomos, vars_, valor):
    """Contrasta el valor con Monte Carlo: SymPy a veces integra mal con raíces cuadradas; si no concuerda, el método se descarta."""
    try:
        cond = sp.And(*[(sp.Lt(g, 0) if est else sp.Le(g, 0)) for g, est in atomos])
        caja = _caja_region(cond, vars_)
        if caja is None:
            return
        mc, se = _mc(f, cond, vars_, caja, N=300_000)
        v = float(sp.N(valor))
        if abs(mc - v) > 6 * se + 1e-9 + 2e-3 * abs(mc):
            raise _SinSolucion(f"El resultado exacto ({v:.6g}) no concuerda con la comprobación numérica ({mc:.6g}): se descarta este orden.")
    except _SinSolucion:
        raise
    except Exception:  # noqa: BLE001
        return


def _resolver_metodo(f, atomos, vars_, sistema=None, orden_ext=None, numerico=False):
    fn, tramos, orden, simb = _plantear(f, atomos, vars_, sistema, orden_ext)
    total, detalle = 0, []
    for tr in tramos:
        try:
            val, pasos = _integrar(fn, tr)
            detalle.append((tr, pasos, val, True))
            total += val
        except _SinSolucion as e:
            if not numerico:
                raise
            try:
                val, err = _nquad(fn, tr, vars_)
                detalle.append((tr, [], sp.Float(val, 12), False))
                total += sp.Float(val, 12)
            except Exception:  # noqa: BLE001
                raise e
    _validar(f, atomos, vars_, total)
    extra = {}
    if sistema:
        s_, j_, *_r = _sistema(sistema, vars_, _centro(atomos, vars_))
        extra = {"sust": s_, "jac": j_, "centro": _centro(atomos, vars_)}
    return {"f": fn, "tramos": tramos, "orden": orden, "valor": total, "detalle": detalle, "simbolos": simb, "sistema": sistema, **extra}


def _forma_regla(atomos, vars_):
    """Pistas: ¿hay desigualdades tipo círculo/esfera centrada en el origen?"""
    x = sum(v ** 2 for v in vars_)
    return any(sp.simplify(g - (x - sp.Symbol("c"))).free_symbols <= {sp.Symbol("c")} for g, _ in atomos) if atomos else False


def _bloques_metodo(m, titulo, vars_):
    b = [H(titulo)]
    nombres = {"polares": "polares", "cilíndricas": "cilíndricas", "esféricas": "esféricas"}
    if m["sistema"]:
        sim = m["simbolos"]
        if m["sistema"] == "polares":
            b.append(T("Se usa $x=r\\cos\\theta,\\ y=r\\sin\\theta$ y el **jacobiano** $r$ (el elemento de área es $r\\,dr\\,d\\theta$)."))
        elif m["sistema"] == "cilíndricas":
            b.append(T("Se usa $x=r\\cos\\theta,\\ y=r\\sin\\theta,\\ z=z$ y el jacobiano $r$ (el elemento de volumen es $r\\,dz\\,dr\\,d\\theta$)."))
        else:
            b.append(T("Se usa $x=\\rho\\sin\\varphi\\cos\\theta,\\ y=\\rho\\sin\\varphi\\sin\\theta,\\ z=\\rho\\cos\\varphi$ y el jacobiano $\\rho^2\\sin\\varphi$ "
                       "(el elemento de volumen es $\\rho^2\\sin\\varphi\\,d\\rho\\,d\\varphi\\,d\\theta$)."))
        b.append(T("El integrando, ya multiplicado por el jacobiano: $" + _l(m["f"]) + "$."))
    for k, (tr, pasos, val, exacto) in enumerate(m["detalle"]):
        if len(m["detalle"]) > 1:
            b.append(T(f"**Trozo {k + 1}:**"))
        b.append(L(_latex_iterada(m["f"], tr)))
        filas = []
        for v, lo, hi, v_ in pasos:
            filas.append([f"respecto de ${_l(v)}$ de ${_l(lo)}$ a ${_l(hi)}$", f"${_l(v_)}$"])
        if filas:
            b.append(TAB(["se integra", "resultado parcial"], filas))
        if not exacto:
            b.append(IN("Este trozo no tiene primitiva elemental: se evaluó **numéricamente** (scipy)."))
    return b


@_op
def integral_region(IR, motor_extra=True):
    """Integral doble/triple sobre una región: límites, procedimiento, valor, verificación y aplicaciones."""
    f, R, vars_ = IR.f, IR.region, list(IR.vars)
    k = len(vars_)
    b = [H("La integral"), L((r"\iiint_{D}\ " if k == 3 else r"\iint_{D}\ ") + _l(f) + (r"\ dV" if k == 3 else r"\ dA")),
         T("Región $D$: " + lectura_de(R) + ".")]
    try:
        atomos = _atomos_de(R.cond)
    except _SinSolucion as e:
        raise ErrorCalculo(str(e)) from None
    if not atomos:
        return res(b + [AV("La región es vacía: la integral vale 0.")], valor=sp.Integer(0))
    # --- métodos a probar: cartesianas (varios órdenes) y radiales (polares / cilíndricas / esféricas)
    pista = _pistas(atomos, vars_)
    sistemas = ["polares"] if k == 2 else (["esféricas", "cilíndricas"] if pista == "esfera" else ["cilíndricas", "esféricas"])
    todas = [list(p_) for p_ in itertools.permutations(vars_)]
    if IR.orden:
        pref = list(reversed(IR.orden))                        # dy dx  ⇒  x exterior, y interior
        ordenes = [pref] + [o for o in todas if o != pref]
    else:
        ordenes = [o for o in todas if o[-1] == vars_[-1]] + [o for o in todas if o[-1] != vars_[-1]] if k == 3 else todas
    cart = [("Coordenadas cartesianas, orden " + " → ".join(_l(v) for v in o) + " (de afuera hacia adentro)", dict(orden_ext=o)) for o in ordenes]
    radiales = [(f"Coordenadas {sis}", dict(sistema=sis)) for sis in sistemas]
    metodos = (radiales + cart) if (pista and not IR.orden) else (cart + radiales)
    t_ini = time.time()
    exitos, errores = [], []
    for rechazar_especiales, numerico in ((True, False), (False, False), (False, True)):   # 1.º exacto elemental; 2.º con funciones especiales; 3.º numérico
        _ESPECIALES[0] = rechazar_especiales
        for titulo, kw in metodos:
            tope = 45 if not exitos else 20
            if time.time() - t_ini > tope:
                break
            try:
                m = _resolver_metodo(f, atomos, vars_, numerico=numerico, **kw)
                m["titulo"] = titulo
                exitos.append(m)
                if len(exitos) >= 2:
                    break
            except _SinSolucion as e:
                errores.append((titulo, str(e)))
            except _Tiempo:
                errores.append((titulo, "tardó demasiado"))
        if exitos:
            break
    _ESPECIALES[0] = True
    if not exitos:
        det = "; ".join(f"{t}: {e}" for t, e in errores[:3])
        raise ErrorCalculo("No pude plantear los límites de integración de esta región. " + det)
    principal = exitos[0]
    alternativas = exitos[1:]
    if IR.orden and errores and errores[0][0].startswith("Coordenadas cartesianas"):
        if "orden " + " → ".join(_l(v) for v in reversed(IR.orden)) not in principal["titulo"]:
            b.append(AV("Con el orden que escribiste (" + ", ".join("d" + _l(v) for v in IR.orden) + ") no se pudo plantear o resolver en forma cerrada; se usó otro método: " + errores[0][1]))
    b += _bloques_metodo(principal, principal["titulo"], vars_)
    valor = sp.simplify(principal["valor"])
    for m2 in alternativas:
        b += _bloques_metodo(m2, m2["titulo"] + " (otra forma de plantearla)", vars_)
        dif = _flt(sp.N(m2["valor"] - principal["valor"], 12))
        b.append((OK if dif is not None and abs(dif) < 1e-7 else AV)("Coinciden con el método anterior ✓" if dif is not None and abs(dif) < 1e-7 else f"⚠️ Difieren en {dif}"))
        if len(sp.srepr(m2["valor"])) < len(sp.srepr(principal["valor"])) and exitos:
            pass
    b.append(OK("**Resultado:** $" + _l(valor) + ("" if valor.is_Integer or valor.free_symbols else r"\approx " + _l(sp.N(valor, 10))) + "$"))
    datos = {"valor": valor, "region": R, "vars": vars_}
    # --- verificación Monte Carlo
    try:
        caja = _caja_region(R.cond, vars_)
        if caja is None:
            b.append(IN("No hice la comprobación de Monte Carlo: la región parece no estar acotada en la ventana [−12, 12]."))
        else:
            mc, se = _mc(f, R.cond, vars_, caja)
            ok = abs(mc - float(sp.N(valor))) <= 4 * se + 1e-6 * max(1, abs(mc))
            b.append((IN if ok else AV)(("✅ " if ok else "⚠️ ") + f"Comprobación numérica (Monte Carlo): {mc:.5g} ± {se:.2g} " + ("coincide" if ok else "NO coincide") + f" con ${_l(sp.N(valor, 6))}$."))
            datos["mc"] = (mc, se)
    except Exception:  # noqa: BLE001
        pass
    # --- aplicaciones: medida, promedio, centro de masa
    if motor_extra and valor.is_number:
        try:
            medida = _medida(atomos, vars_, principal)
            if medida is not None and medida != 0:
                nm = {2: "Área", 3: "Volumen"}.get(k, "Medida")
                b += [H("Aplicaciones"), T(f"{nm} de la región: ${_l(sp.simplify(medida))}" + ("" if medida.is_Integer else r"\approx " + _l(sp.N(medida, 6))) + "$.")]
                if f != 1:
                    b.append(T(f"Valor promedio de $f$ en la región: $\\dfrac{{1}}{{{nm}}}\\iint f = {_l(sp.simplify(valor / medida))}\\approx {_n(valor / medida)}$."))
                cm = _centro_masa(f, atomos, vars_, principal, valor)
                if cm:
                    b.append(T("Si $f$ es una **densidad** (y $f\\ge 0$): masa $M=" + _l(sp.simplify(valor)) + "$, centro de masa $" + _l(sp.Tuple(*cm)) +
                               "$." if f != 1 else "El **centroide** de la región (densidad uniforme) es $" + _l(sp.Tuple(*cm)) + "$."))
                datos["medida"] = medida
        except Exception:  # noqa: BLE001
            pass
    return res(b, **datos)


def _medida(atomos, vars_, m):
    """∬ 1 (área) / ∭ 1 (volumen), con el mismo método que el principal."""
    try:
        if m["sistema"]:
            fn = sp.simplify(sp.Integer(1) * m["jac"])
        else:
            fn = sp.Integer(1)
        tot = 0
        for tr in m["tramos"]:
            v, _ = _integrar(fn, tr)
            tot += v
        return sp.simplify(tot)
    except Exception:  # noqa: BLE001
        return None


def _centro_masa(f, atomos, vars_, m, masa):
    try:
        if masa == 0:
            return None
        coords = m["simbolos"] if m["sistema"] else vars_
        # momentos en las variables ORIGINALES: se integra v·f en el sistema del método
        res_ = []
        for i, v in enumerate(vars_):
            if m["sistema"]:
                integrando = sp.simplify((v * f).subs(m["sust"], simultaneous=True) * m["jac"])
            else:
                integrando = v * f
            tot = 0
            for tr in m["tramos"]:
                val, _ = _integrar(integrando, tr)
                tot += val
            res_.append(sp.simplify(tot / masa))
        return res_
    except Exception:  # noqa: BLE001
        return None


# ==============================================================================
# 5. INTERFAZ PARA OTROS MÓDULOS: ∬ f dA sobre una región (para área de superficie, flujo…)
# ==============================================================================
def integrar_region(f, region, vars_=None, sistemas=True):
    """
    Integral de f sobre `region` (Region). Devuelve (valor, bloques_metodo) con el primer método que funcione.
    Se usa desde calculo_vectorial (área de superficie, integrales de superficie, Green, Stokes).
    """
    vars_ = list(vars_ or region.vars)
    atomos = _atomos_de(region.cond)
    k = len(vars_)
    ultimo = None
    for o in itertools.permutations(vars_):
        try:
            m = _resolver_metodo(f, atomos, vars_, orden_ext=list(o))
            return sp.simplify(m["valor"]), m
        except _SinSolucion as e:
            ultimo = e
    if sistemas:
        for sis in (["polares"] if k == 2 else ["cilíndricas", "esféricas"]):
            try:
                m = _resolver_metodo(f, atomos, vars_, sistema=sis)
                return sp.simplify(m["valor"]), m
            except _SinSolucion as e:
                ultimo = e
    raise ErrorCalculo(str(ultimo) if ultimo else "No pude integrar.")
