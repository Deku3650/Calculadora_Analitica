"""
calculo_curvas.py
=================
Geometría diferencial de CURVAS PARAMÉTRICAS  r(t) = ⟨x(t), y(t), z(t)⟩  (ℝ² y ℝ³; velocidad, longitud y
curvatura también en ℝⁿ).

ANÁLISIS GENERAL (simbólico en t)
  · r′, r″, r‴      · ¿es suave? (r′ continua y r′(t) ≠ 0) y en qué puntos falla (cúspides, esquinas…)
  · rapidez ‖r′‖ y vector TANGENTE unitario T
  · CURVATURA κ y radio de curvatura ρ = 1/κ      · NORMAL N y BINORMAL B      · TORSIÓN τ
  · LONGITUD de arco (y reparametrización por longitud de arco cuando la rapidez es constante)
  · EVOLUTA (curvas planas) y clasificación: recta, circunferencia, hélice, curva plana…

EN UN PUNTO t = t₀ (exacto, con vectores numéricos)
  · triedro de Frenet (T, N, B)   · aceleración tangencial y normal
  · plano OSCULADOR, plano NORMAL y plano RECTIFICANTE
  · CIRCUNFERENCIA OSCULADORA (centro, radio, ecuación y parametrización)

Se registra en OPERACIONES (corre en el proceso aislado del motor).
"""
from __future__ import annotations

import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _flt, _op, res

_NOMBRES = ["x", "y", "z"]


def _S(e):
    try:
        return sp.simplify(e)
    except Exception:  # noqa: BLE001
        return e


def _l(e) -> str:
    return sp.latex(e)


def _lv(v, pre=r"\left\langle ", post=r"\right\rangle") -> str:
    return pre + ", ".join(_l(c) for c in v) + post


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _norm(a):
    return sp.sqrt(sum(c ** 2 for c in a))


def _num(v, d=5) -> str:
    f = _flt(v)
    if f is None:
        return _l(v)
    return str(int(round(f))) if abs(f - round(f)) < 1e-9 else f"{f:.{d}g}"


def _exacto(v):
    """Valor exacto + aproximación decimal si no es entero."""
    v = _S(v)
    if v.is_Integer or v.free_symbols:
        return _l(v)
    return _l(v) + r"\approx " + _l(sp.N(v, 6))


def _plano(normal, P, X):
    """Ecuación del plano  n·(X − P) = 0  como  a x + b y + c z = d."""
    n = [_S(c) for c in normal]
    d = _S(sum(a * b for a, b in zip(n, P)))
    return sp.Eq(sum(a * x for a, x in zip(n, X)), d)


# ==============================================================================
# 1. SUAVIDAD
# ==============================================================================
def _acotado(dom) -> bool:
    try:
        return bool(dom.inf.is_finite and dom.sup.is_finite)
    except Exception:  # noqa: BLE001
        return False


def _bloques_suavidad(C, rp, v2, dom):
    from sympy.calculus.util import continuous_domain
    t = C.param
    b = [H("¿La curva es suave?")]
    b.append(T("Una curva paramétrica es **suave** (o regular) si $\\mathbf{r}'(t)$ es **continua** y **nunca se anula**: así tiene una recta tangente bien definida en todos sus puntos."))
    malos = sp.S.EmptySet
    for c in list(C.comps) + rp:
        try:
            malos = sp.Union(malos, sp.Complement(dom, continuous_domain(c, t, dom)))
        except Exception:  # noqa: BLE001
            pass
    try:
        ceros = sp.solveset(v2, t, dom)
        if isinstance(ceros, sp.ConditionSet):
            ceros = None
    except Exception:  # noqa: BLE001
        ceros = None
    problemas = []
    # valores absolutos / signos: la curva tiene una ESQUINA donde el argumento se anula (SymPy los da por «continuos»)
    esquinas = sp.S.EmptySet
    for c in C.comps:
        for a in c.atoms(sp.Abs, sp.sign):
            try:
                z = sp.solveset(a.args[0], t, dom)
                if not isinstance(z, sp.ConditionSet):
                    esquinas = sp.Union(esquinas, z)
            except Exception:  # noqa: BLE001
                pass
    if esquinas != sp.S.EmptySet:
        malos = sp.Union(malos, esquinas)
    if malos != sp.S.EmptySet:
        problemas.append(("no_cont", malos))
        b.append(AV(f"Alguna componente de $\\mathbf{{r}}$ o de $\\mathbf{{r}}'$ **no es continua (o no existe)** en $t\\in{_l(malos)}$"
                    + (" (por un **valor absoluto**: la curva tiene una **esquina** ahí, no hay recta tangente)." if esquinas != sp.S.EmptySet else ".")))
    else:
        b.append(T("✓ $\\mathbf{r}$ y $\\mathbf{r}'$ son continuas en todo el intervalo."))
    if ceros is None:
        # respaldo numérico: ¿hay algún t donde la rapidez se hace casi cero?
        try:
            a_ = float(dom.start) if dom.start.is_finite else -10.0
            b_ = float(dom.end) if dom.end.is_finite else 10.0
            f = sp.lambdify(t, v2, "numpy")
            import numpy as np
            ts = np.linspace(a_, b_, 4001)
            vals = np.asarray(f(ts), dtype=float)
            i = int(np.nanargmin(vals))
            if vals[i] < 1e-8:
                problemas.append(("cero_num", ts[i]))
                b.append(AV(f"La rapidez se hace prácticamente cero cerca de $t\\approx{ts[i]:.4g}$ (hallado numéricamente): probablemente $\\mathbf{{r}}'=\\mathbf{{0}}$ ahí."))
            else:
                b.append(T(f"✓ No encontré ningún $t$ con $\\mathbf{{r}}'=\\mathbf{{0}}$ (revisé 4000 valores; evidencia numérica)."))
        except Exception:  # noqa: BLE001
            b.append(IN("No pude decidir si $\\mathbf{r}'$ se anula."))
    elif ceros == sp.S.EmptySet:
        b.append(T("✓ $\\|\\mathbf{r}'(t)\\|^2$ nunca vale 0: $\\mathbf{r}'$ **nunca se anula** (comprobado de forma exacta)."))
    else:
        problemas.append(("cero", ceros))
        b.append(AV(f"$\\mathbf{{r}}'(t)=\\mathbf{{0}}$ cuando $t\\in{_l(ceros)}$ (ahí la velocidad es cero)."))
        if isinstance(ceros, sp.FiniteSet) and len(ceros.args) <= 6:
            filas = []
            for tt in ceros.args:
                filas.append([f"${_l(tt)}$", "$" + _lv([_S(c.subs(t, tt)) for c in C.comps], "(", ")") + "$"])
            b.append(TAB(["valor de t", "punto de la curva"], filas))
        b.append(IN("En esos puntos la curva puede tener una **cúspide** (punto de retroceso), una esquina o simplemente pararse; no hay recta tangente única."))
    suave = not problemas
    if suave:
        b.append(OK("**La curva es suave** en todo el intervalo considerado."))
    else:
        finitos = all(isinstance(p[1], sp.FiniteSet) for p in problemas if p[0] != "cero_num")
        b.append(AV("**La curva NO es suave en todo el intervalo**" + (" (pero es **suave a trozos**: se divide en tramos suaves entre los puntos problemáticos)." if finitos and _acotado(dom) else ".")))
    return b, suave, problemas


# ==============================================================================
# 2. CLASIFICACIÓN
# ==============================================================================
def _clasifica(kappa, tau, n):
    if kappa is not None and _S(kappa) == 0:
        return "una **recta** (curvatura idénticamente 0)"
    if kappa is not None and not kappa.free_symbols:
        if n == 2:
            return "una **circunferencia** (curvatura constante)"
        if tau is not None and _S(tau) == 0:
            return "una **circunferencia** (curvatura constante y torsión 0)"
        if tau is not None and not tau.free_symbols:
            return "una **hélice circular** (curvatura y torsión constantes)"
    if tau is not None and _S(tau) == 0:
        return "una **curva plana** (torsión idénticamente 0: queda contenida en un plano)"
    return None


# ==============================================================================
# 3. ANÁLISIS GENERAL
# ==============================================================================
@_op
def analizar_curva(C, t0=None):
    """Análisis completo de una curva paramétrica (general y, si se da t0, en ese punto)."""
    t = C.param
    comps = [_S(c) for c in C.comps]
    n = len(comps)
    if n < 2:
        raise ErrorCalculo("Una curva paramétrica necesita al menos 2 componentes.")
    dom = C.dominio if C.dominio is not None else sp.S.Reals
    nom = C.nombre or "r"
    nombres = _NOMBRES if n <= 3 else [f"x_{i + 1}" for i in range(n)]
    b = [H("La curva"), L(r"\mathbf{" + nom + "}(" + _l(t) + r")=" + _lv(comps))]
    b.append(T(f"Cada coordenada es una función del parámetro ${_l(t)}$: " + ", ".join(f"${nm}({_l(t)})={_l(c)}$" for nm, c in zip(nombres, comps)) + "."
               + (f" Intervalo: ${_l(t)}\\in{_l(dom)}$." if dom != sp.S.Reals else "")))
    datos: dict = {"param": t, "comps": comps, "dominio": dom}

    # --- derivadas
    rp = [_S(sp.diff(c, t)) for c in comps]
    rpp = [_S(sp.diff(c, t)) for c in rp]
    rppp = [_S(sp.diff(c, t)) for c in rpp] if n == 3 else None
    b += [H("Velocidad y aceleración"),
          L(r"\mathbf{v}(t)=\mathbf{r}'(t)=" + _lv(rp)), L(r"\mathbf{a}(t)=\mathbf{r}''(t)=" + _lv(rpp))]
    if rppp is not None:
        b.append(L(r"\mathbf{r}'''(t)=" + _lv(rppp)))
    datos.update(rp=rp, rpp=rpp, rppp=rppp)

    # --- rapidez
    v2 = _S(sum(c ** 2 for c in rp))
    v = _S(sp.sqrt(v2))
    datos["v"] = v
    b += [H("Rapidez y vector tangente unitario"),
          L(r"\|\mathbf{r}'(t)\|=" + _l(v)),
          IN("La **rapidez** es qué tan rápido se recorre la curva (la longitud del vector velocidad).")]

    # --- suavidad
    bl, suave, problemas = _bloques_suavidad(C, rp, v2, dom)
    b += bl
    datos["suave"] = suave
    datos["problemas"] = [(a, c) for a, c in problemas]

    # --- tangente
    try:
        Tv = [_S(c / v) for c in rp]
        b.append(L(r"\mathbf{T}(t)=\frac{\mathbf{r}'(t)}{\|\mathbf{r}'(t)\|}=" + _lv(Tv)))
        datos["T"] = Tv
    except Exception:  # noqa: BLE001
        Tv = None

    # --- curvatura
    kappa = tau = None
    b.append(H("Curvatura"))
    try:
        if n == 2:
            num = _S(rp[0] * rpp[1] - rp[1] * rpp[0])
            ks = _S(num / v ** 3)
            kappa = _S(sp.Abs(num) / v ** 3) if True else None
            if ks.is_nonnegative or ks.is_nonpositive:
                kappa = _S(sp.Abs(ks))
            b += [T("Para una curva plana:"), L(r"\kappa(t)=\frac{|x'y''-y'x''|}{\left(x'^{2}+y'^{2}\right)^{3/2}}=" + _l(kappa)),
                  L(r"\kappa_{\text{con signo}}(t)=\frac{x'y''-y'x''}{\left(x'^{2}+y'^{2}\right)^{3/2}}=" + _l(ks)),
                  IN("La curvatura con signo es positiva si la curva gira a la **izquierda** (sentido contrario a las manecillas) y negativa si gira a la derecha.")]
            datos["kappa_signo"] = ks
        elif n == 3:
            cr = [_S(c) for c in _cross(rp, rpp)]
            cr2 = _S(sum(c ** 2 for c in cr))
            kappa = _S(sp.sqrt(cr2) / v ** 3)
            b += [L(r"\mathbf{r}'\times\mathbf{r}''=" + _lv(cr)),
                  L(r"\kappa(t)=\frac{\|\mathbf{r}'\times\mathbf{r}''\|}{\|\mathbf{r}'\|^{3}}=" + _l(kappa))]
            datos["cruz"] = cr
        else:
            cr2 = _S(v2 * sum(c ** 2 for c in rpp) - _dot(rp, rpp) ** 2)
            kappa = _S(sp.sqrt(cr2) / v ** 3)
            b.append(L(r"\kappa(t)=\frac{\sqrt{\|\mathbf{r}'\|^{2}\|\mathbf{r}''\|^{2}-(\mathbf{r}'\cdot\mathbf{r}'')^{2}}}{\|\mathbf{r}'\|^{3}}=" + _l(kappa)))
        datos["kappa"] = kappa
        if kappa == 0:
            b.append(OK("La curvatura es **idénticamente 0**: la curva es una **recta** (o un tramo recto); no tiene normal ni circunferencia osculadora."))
        else:
            rho = _S(1 / kappa)
            b += [L(r"\rho(t)=\frac{1}{\kappa(t)}=" + _l(rho)), IN("El **radio de curvatura** $\\rho$ es el radio de la circunferencia que mejor se pega a la curva en ese punto.")]
            datos["rho"] = rho
            try:
                ceros_k = sp.solveset(kappa, t, dom)
                if ceros_k not in (sp.S.EmptySet,) and not isinstance(ceros_k, sp.ConditionSet):
                    b.append(IN(f"La curvatura vale 0 en $t\\in{_l(ceros_k)}$: ahí la curva es localmente recta (por ejemplo, un punto de inflexión) y la normal no está definida."))
            except Exception:  # noqa: BLE001
                pass
    except Exception as e:  # noqa: BLE001
        b.append(IN(f"No pude simplificar la curvatura en forma cerrada ({type(e).__name__})."))

    # --- normal, binormal, torsión
    if n in (2, 3) and kappa is not None and kappa != 0:
        try:
            Tp = [_S(sp.diff(c, t)) for c in Tv]
            Tp_n = _S(sp.sqrt(_S(sum(c ** 2 for c in Tp))))
            Nv = [_S(c / Tp_n) for c in Tp]
            b += [H("Vector normal principal y binormal"),
                  L(r"\mathbf{T}'(t)=" + _lv(Tp)), L(r"\mathbf{N}(t)=\frac{\mathbf{T}'(t)}{\|\mathbf{T}'(t)\|}=" + _lv(Nv)),
                  IN("**N** apunta hacia donde la curva se está doblando; es perpendicular a **T**.")]
            datos["N"] = Nv
            if n == 3:
                Bv = [_S(c) for c in _cross(Tv, Nv)]
                b.append(L(r"\mathbf{B}(t)=\mathbf{T}\times\mathbf{N}=" + _lv(Bv)))
                cr2 = _S(sum(c ** 2 for c in datos["cruz"]))
                det = _S(sp.Matrix([rp, rpp, rppp]).det())
                tau = _S(det / cr2)
                b += [H("Torsión"), L(r"\tau(t)=\frac{(\mathbf{r}'\times\mathbf{r}'')\cdot\mathbf{r}'''}{\|\mathbf{r}'\times\mathbf{r}''\|^{2}}=" + _l(tau)),
                      IN("La **torsión** mide cuánto se sale la curva del plano osculador (qué tanto se «tuerce»). Si es 0, la curva es plana.")]
                datos["B"], datos["tau"] = Bv, tau
                b += [H("Fórmulas de Frenet–Serret"),
                      L(r"\frac{d\mathbf{T}}{ds}=\kappa\,\mathbf{N},\qquad \frac{d\mathbf{N}}{ds}=-\kappa\,\mathbf{T}+\tau\,\mathbf{B},\qquad \frac{d\mathbf{B}}{ds}=-\tau\,\mathbf{N}")]
        except Exception as e:  # noqa: BLE001
            b.append(IN(f"No pude dar N, B y τ en forma cerrada ({type(e).__name__}); en un punto concreto sí se calculan (más abajo)."))

    # --- aceleración tangencial y normal
    if kappa is not None and v is not None:
        try:
            aT = _S(sp.diff(v, t))
            aN = _S(kappa * v ** 2)
            b += [H("Aceleración tangencial y normal"),
                  L(r"a_T=\frac{d\|\mathbf{v}\|}{dt}=" + _l(aT) + r"\qquad a_N=\kappa\|\mathbf{v}\|^{2}=" + _l(aN)),
                  IN("La aceleración se descompone en una parte **a lo largo** de la trayectoria ($a_T$, cambia la rapidez) y otra que **dobla** la trayectoria ($a_N$, cambia la dirección).")]
            datos["aT"], datos["aN"] = aT, aN
        except Exception:  # noqa: BLE001
            pass

    # --- longitud de arco
    b.append(H("Longitud de arco"))
    b.append(L(r"ds=\|\mathbf{r}'(t)\|\,dt=" + _l(v) + r"\,dt"))
    a_, b_ = dom.start, dom.end if isinstance(dom, sp.Interval) else (None, None)
    if isinstance(dom, sp.Interval) and a_.is_finite and b_.is_finite:
        try:
            Lg = sp.integrate(v, (t, a_, b_))
            if Lg.has(sp.Integral):
                raise ValueError("sin forma cerrada")
            Lg = _S(Lg)
            b.append(L(r"L=\int_{" + _l(a_) + "}^{" + _l(b_) + r"}\|\mathbf{r}'(t)\|\,dt=" + _exacto(Lg)))
        except Exception:  # noqa: BLE001
            Lg = sp.N(sp.Integral(v, (t, a_, b_)), 10)
            b.append(L(r"L=\int_{" + _l(a_) + "}^{" + _l(b_) + r"}\|\mathbf{r}'(t)\|\,dt\approx " + _l(Lg)))
            b.append(IN("La integral no tiene una forma cerrada sencilla: se evaluó **numéricamente**."))
        datos["longitud"] = Lg
        if all(_S(c.subs(t, a_) - c.subs(t, b_)) == 0 for c in comps):
            b.append(IN("Como $\\mathbf{r}(a)=\\mathbf{r}(b)$, la curva es **cerrada**."))
    else:
        b.append(IN(f"No hay un intervalo finito para ${_l(t)}$, así que no hay una longitud total. Escribe el intervalo (por ejemplo ⟨…⟩, 0 ≤ {t} ≤ 2π) para obtenerla."))
    if v.free_symbols == set():
        s = sp.Symbol("s", real=True)
        t_de_s = (s / v) if True else None
        a0 = a_ if (isinstance(dom, sp.Interval) and a_.is_finite) else 0
        t_s = a0 + s / v
        try:
            rs = [_S(c.subs(t, t_s)) for c in comps]
            b += [T(f"Como la rapidez es **constante** ($\\|\\mathbf{{r}}'\\|={_l(v)}$), se puede reparametrizar por **longitud de arco** $s={_l(v)}({_l(t)}-{_l(a0)})$:"),
                  L(r"\mathbf{r}(s)=" + _lv(rs)), IN("Con este parámetro la rapidez es 1 y $s$ mide la distancia recorrida sobre la curva.")]
            datos["param_arco"] = rs
        except Exception:  # noqa: BLE001
            pass
    else:
        b.append(IN("La rapidez no es constante, así que la reparametrización por longitud de arco no tiene una forma cerrada sencilla."))

    # --- evoluta (curvas planas)
    if n == 2 and kappa is not None and kappa != 0:
        try:
            num = _S(rp[0] * rpp[1] - rp[1] * rpp[0])
            ev = [_S(comps[0] - rp[1] * v2 / num), _S(comps[1] + rp[0] * v2 / num)]
            b += [H("Evoluta"), T("La **evoluta** es la curva que recorren los centros de las circunferencias osculadoras:"),
                  L(r"\mathbf{e}(t)=\mathbf{r}+\frac{1}{\kappa_{\text{signo}}}\mathbf{N}=" + _lv(ev))]
            datos["evoluta"] = ev
        except Exception:  # noqa: BLE001
            pass

    # --- clasificación
    clase = _clasifica(kappa, tau, n)
    if clase:
        b.append(OK(f"**Es {clase}.**"))
        datos["clase"] = clase

    # --- en un punto
    if t0 is not None:
        b += _en_punto(C, comps, rp, rpp, rppp, dom, sp.sympify(t0), datos)
    return res(b, **datos)


# ==============================================================================
# 4. EN UN PUNTO t = t0
# ==============================================================================
def _en_punto(C, comps, rp, rpp, rppp, dom, t0, datos):
    t = C.param
    n = len(comps)
    X = sp.symbols("x y z")[:n]
    b = [H(f"En el punto t = {_l(t0)}")]
    if isinstance(dom, sp.Interval) and dom.contains(t0) == False:  # noqa: E712
        b.append(AV(f"⚠️ ${_l(t0)}$ no está en el intervalo de la curva ${_l(dom)}$; igual se calcula como si la fórmula valiera ahí."))
    P = [_S(c.subs(t, t0)) for c in comps]
    r1 = [_S(c.subs(t, t0)) for c in rp]
    r2 = [_S(c.subs(t, t0)) for c in rpp]
    r3 = [_S(c.subs(t, t0)) for c in rppp] if rppp is not None else None
    for q in P + r1 + r2:
        if q.has(sp.zoo, sp.oo, -sp.oo, sp.nan):
            raise ErrorCalculo(f"La curva (o sus derivadas) no está definida en t = {t0}.")
    v0 = _S(_norm(r1))
    b += [T("Punto y derivadas en $t_0$:"), L(r"\mathbf{r}(t_0)=" + _lv(P, "(", ")") + r",\quad \mathbf{r}'(t_0)=" + _lv(r1) + r",\quad \mathbf{r}''(t_0)=" + _lv(r2)),
          L(r"\|\mathbf{r}'(t_0)\|=" + _exacto(v0))]
    fig = {"P": [float(sp.N(c)) for c in P], "n": n, "t0": float(sp.N(t0))}
    datos["P0"] = P
    if v0 == 0:
        b.append(AV("En este punto **r′(t₀) = 0**: la curva está en un punto singular (se detiene o tiene una cúspide). **No hay vector tangente unitario ni triedro de Frenet.**"))
        datos["figura"] = fig
        return b
    T0 = [_S(c / v0) for c in r1]
    b.append(L(r"\mathbf{T}(t_0)=" + _lv(T0)))
    fig["T"] = [float(sp.N(c)) for c in T0]
    datos["T0"] = T0
    # recta tangente
    s = sp.Symbol("s", real=True)
    if n == 2:
        b.append(L(r"\text{Recta tangente: }\ " + _l(sp.Eq(r1[1] * (X[0] - P[0]) - r1[0] * (X[1] - P[1]), 0)) + r"\ \ \Longleftrightarrow\ \ (x,y)=" + _lv([P[i] + s * r1[i] for i in range(2)], "(", ")")))
    else:
        b.append(L(r"\text{Recta tangente: }\ (x,y,z)=" + _lv([P[i] + s * r1[i] for i in range(3)], "(", ")")))
    # curvatura en el punto, con vectores numéricos
    if n == 2:
        num = _S(r1[0] * r2[1] - r1[1] * r2[0])
        k0 = _S(sp.Abs(num) / v0 ** 3)
        ks0 = _S(num / v0 ** 3)
        cr_norm = _S(sp.Abs(num))
    elif n == 3:
        cr = [_S(c) for c in _cross(r1, r2)]
        cr_norm = _S(_norm(cr))
        k0 = _S(cr_norm / v0 ** 3)
        ks0 = k0
    else:
        cr_norm = _S(sp.sqrt(_S(_dot(r1, r1) * _dot(r2, r2) - _dot(r1, r2) ** 2)))
        k0 = _S(cr_norm / v0 ** 3)
        ks0 = k0
    b.append(L(r"\kappa(t_0)=" + _exacto(k0)))
    datos["kappa0"] = k0
    fig["kappa"] = float(sp.N(k0))
    if k0 == 0:
        b.append(AV("La curvatura en este punto es **0**: la curva es localmente recta. **No hay vector normal principal, ni circunferencia osculadora** (su radio sería infinito)"
                    + (", ni plano osculador definido por **r′ × r″** (es el vector cero)." if n == 3 else ".")))
        datos["figura"] = fig
        return b
    rho0 = _S(1 / k0)
    # normal principal = parte de la aceleración perpendicular a la velocidad
    a_perp = [_S(r2[i] - _dot(r2, T0) * T0[i]) for i in range(n)]
    N0 = [_S(c / _norm(a_perp)) for c in a_perp]
    b += [L(r"\rho(t_0)=\frac{1}{\kappa}=" + _exacto(rho0)),
          L(r"\mathbf{N}(t_0)=" + _lv(N0)),
          IN("**N** se obtiene como la parte de la aceleración perpendicular a la velocidad, normalizada.")]
    fig["N"] = [float(sp.N(c)) for c in N0]
    fig["rho"] = float(sp.N(rho0))
    datos.update(N0=N0, rho0=rho0)
    aT0 = _S(_dot(r2, T0))
    aN0 = _S(k0 * v0 ** 2)
    b.append(T(f"Aceleración: $a_T={_exacto(aT0)}$ y $a_N=\\kappa\\|\\mathbf{{v}}\\|^2={_exacto(aN0)}$ (se cumple $a_T^2+a_N^2=\\|\\mathbf{{a}}\\|^2$: "
               f"${_l(_S(aT0 ** 2 + aN0 ** 2))}={_l(_S(_dot(r2, r2)))}$)."))
    # centro y circunferencia osculadora
    C0 = [_S(P[i] + rho0 * N0[i]) for i in range(n)]
    fig["centro"] = [float(sp.N(c)) for c in C0]
    datos["centro0"] = C0
    if n == 2:
        b += [H("Circunferencia osculadora"),
              T("Es la circunferencia que mejor aproxima a la curva en el punto: pasa por él, tiene la **misma tangente** y la **misma curvatura**. Su centro está sobre la normal, a distancia $\\rho$:"),
              L(r"\mathbf{c}=\mathbf{r}(t_0)+\rho\,\mathbf{N}=" + _lv(C0, "(", ")") + r",\qquad \rho=" + _exacto(rho0)),
              L(_l(sp.Eq((X[0] - C0[0]) ** 2 + (X[1] - C0[1]) ** 2, _S(rho0 ** 2)))),
              T("Es decir, tiene **contacto de segundo orden** con la curva (coinciden en posición, pendiente y curvatura).")]
        if ks0 != 0:
            b.append(IN("La curva gira hacia " + ("la **izquierda**" if _flt(ks0) and _flt(ks0) > 0 else "la **derecha**") + " en este punto (signo de la curvatura)."))
        datos["circulo"] = {"centro": C0, "radio": rho0}
        recta_n = sp.Eq(N0[1] * (X[0] - P[0]) - N0[0] * (X[1] - P[1]), 0)
        b.append(T("Recta normal: $" + _l(recta_n) + "$."))
    else:
        if n == 3:
            B0 = [_S(c) for c in _cross(T0, N0)]
            fig["B"] = [float(sp.N(c)) for c in B0]
            tau0 = _S(sp.Matrix([r1, r2, r3]).det() / cr_norm ** 2)
            b += [L(r"\mathbf{B}(t_0)=\mathbf{T}\times\mathbf{N}=" + _lv(B0)), L(r"\tau(t_0)=" + _exacto(tau0)),
                  T("Los tres vectores **T, N, B** son unitarios y perpendiculares entre sí: forman el **triedro de Frenet** en ese punto.")]
            datos.update(B0=B0, tau0=tau0)
            ok = all(_S(_dot(u, w)) == 0 for u, w in ((T0, N0), (T0, B0), (N0, B0)))
            b.append(IN("✅ Comprobado: T·N = T·B = N·B = 0." if ok else "⚠️ Revisa: no salieron exactamente ortogonales (puede ser un problema de simplificación)."))
            b.append(H("Planos del triedro"))
            filas = [["**Osculador** (contiene a T y N, normal B)", "$" + _l(_plano(B0, P, X)) + "$"],
                     ["**Normal** (perpendicular a T)", "$" + _l(_plano(T0, P, X)) + "$"],
                     ["**Rectificante** (perpendicular a N)", "$" + _l(_plano(N0, P, X)) + "$"]]
            b.append(TAB(["plano", "ecuación"], filas))
            b.append(IN("El **plano osculador** es el plano que mejor se pega a la curva en ese punto (el límite de los planos por tres puntos de la curva que se juntan)."))
            fig["plano_osc"] = [float(sp.N(c)) for c in B0]
            phi = sp.Symbol("phi", real=True)
            param = [_S(C0[i] - rho0 * N0[i] * sp.cos(phi) + rho0 * T0[i] * sp.sin(phi)) for i in range(3)]
            b += [H("Circunferencia osculadora"),
                  T("Está en el plano osculador, es tangente a la curva en el punto y tiene su misma curvatura. Centro $\\mathbf{c}=\\mathbf{r}+\\rho\\mathbf{N}$:"),
                  L(r"\mathbf{c}=" + _lv(C0, "(", ")") + r",\qquad \rho=" + _exacto(rho0)),
                  L(r"\mathbf{c}(\varphi)=\mathbf{c}-\rho\,\mathbf{N}\cos\varphi+\rho\,\mathbf{T}\sin\varphi=" + _lv(param, "(", ")"))]
            datos["circulo"] = {"centro": C0, "radio": rho0, "param": param}
    datos["figura"] = fig
    return b
