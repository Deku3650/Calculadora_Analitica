"""
calculo_superficies.py
======================
SUPERFICIES paramétricas  r(u, v) = ⟨x, y, z⟩  y los teoremas del cálculo vectorial.

  · vector normal N = r_u × r_v, elemento de área dS = ‖N‖ du dv, plano tangente, recta normal
  · formas fundamentales (E, F, G; L, M, N), curvatura de GAUSS K y curvatura MEDIA H, curvaturas principales
  · reconocimiento: plano, esfera, cilindro, cono, superficie de silla…
  · ÁREA, integral de superficie ∬ f dS y FLUJO ∬ F·dS
  · verificación de GREEN, STOKES y GAUSS (teorema de la divergencia): se calculan los DOS lados
"""
from __future__ import annotations

import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _flt, _op, res
import calculo_integrales_multiples as _IM          # (se usa por atributo, en tiempo de llamada: evita problemas de importación circular)


def _atomos_de(*a, **k):
    return _IM._atomos_de(*a, **k)


def _bloques_metodo(*a, **k):
    return _IM._bloques_metodo(*a, **k)


def _caja_region(*a, **k):
    return _IM._caja_region(*a, **k)


def integrar_region(*a, **k):
    return _IM.integrar_region(*a, **k)


from calculo_vectorial import _S, _l, _lv, _exacto, potencial
from estructuras import Bola, Region, Superficie, Vector, Punto, evaluar_operador, Rotacional, Divergencia, variables_por_defecto


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _quitar_abs(expr, region, params):
    """Si el signo del argumento de un Abs es constante en el dominio, se quita (por ejemplo |sin φ| con φ ∈ [0, π])."""
    if not expr.has(sp.Abs) or region is None:
        return expr
    try:
        import numpy as np
        caja = _caja_region(region.cond, list(params))
        if caja is None:
            return expr
        rng = np.random.default_rng(2)
        P = rng.uniform([c[0] for c in caja], [c[1] for c in caja], size=(600, len(params)))
        fc = sp.lambdify(params, region.cond, "numpy")
        ok = np.broadcast_to(np.asarray(fc(*[P[:, i] for i in range(len(params))]), dtype=bool), (len(P),))
        P = P[ok]
        if len(P) == 0:
            return expr
        cambios = {}
        for a in expr.atoms(sp.Abs):
            fa = sp.lambdify(params, a.args[0], "numpy")
            vals = np.broadcast_to(np.asarray(fa(*[P[:, i] for i in range(len(params))]), dtype=float), (len(P),))
            if (vals >= -1e-9).all():
                cambios[a] = a.args[0]
            elif (vals <= 1e-9).all():
                cambios[a] = -a.args[0]
        return expr.xreplace(cambios) if cambios else expr
    except Exception:  # noqa: BLE001
        return expr


def _rect(region):
    """{variable: (a, b)} si la región es un rectángulo [a,b]×[c,d] en sus variables; si no, None."""
    try:
        atomos = _atomos_de(region.cond)
    except Exception:  # noqa: BLE001  (_SinSolucion)
        return None
    lim = {}
    for g, _ in atomos:
        vs = [v for v in region.vars if g.has(v)]
        if len(vs) != 1:
            return None
        v = vs[0]
        try:
            P = sp.Poly(g, v)
        except sp.PolynomialError:
            return None
        if P.degree() != 1:
            return None
        a, b = P.all_coeffs()
        raiz = sp.simplify(-b / a)
        lo, hi = lim.get(v, [None, None])
        if a > 0:
            hi = raiz
        else:
            lo = raiz
        lim[v] = [lo, hi]
    if set(lim) != set(region.vars) or any(l is None or h is None for l, h in lim.values()):
        return None
    return {v: (l, h) for v, (l, h) in lim.items()}


def _geom(S):
    """Cantidades geométricas simbólicas de la superficie (con el dominio para quitar valores absolutos)."""
    u, v = S.params
    r = [_S(c) for c in S.comps]
    ru = [_S(sp.diff(c, u)) for c in r]
    rv = [_S(sp.diff(c, v)) for c in r]
    N = [_S(c) for c in _cross(ru, rv)]
    Nn2 = _S(_dot(N, N))
    Nn = _quitar_abs(_S(sp.sqrt(Nn2)), S.dominio, S.params)
    return {"u": u, "v": v, "r": r, "ru": ru, "rv": rv, "N": N, "Nn2": Nn2, "Nn": Nn}


def _formas(S, g):
    u, v = g["u"], g["v"]
    ru, rv = g["ru"], g["rv"]
    ruu = [_S(sp.diff(c, u)) for c in ru]
    ruv = [_S(sp.diff(c, v)) for c in ru]
    rvv = [_S(sp.diff(c, v)) for c in rv]
    E, F, G = _S(_dot(ru, ru)), _S(_dot(ru, rv)), _S(_dot(rv, rv))
    nh = [_S(c / g["Nn"]) for c in g["N"]]
    Lf, Mf, Nf = _S(_dot(ruu, nh)), _S(_dot(ruv, nh)), _S(_dot(rvv, nh))
    den = _S(E * G - F ** 2)
    K = _S((Lf * Nf - Mf ** 2) / den)
    Hm = _S((E * Nf - 2 * F * Mf + G * Lf) / (2 * den))
    return {"E": E, "F": F, "G": G, "L": Lf, "M": Mf, "Nf": Nf, "K": K, "H": Hm, "nh": nh}


def _clasifica(g, f, S):
    K, Hm = f["K"], f["H"]
    if K == 0 and Hm == 0:
        return "un **plano** (o parte de uno): curvatura gaussiana y media nulas"
    if not K.free_symbols and not Hm.free_symbols and _flt(K) is not None and _flt(K) > 0 and _S(Hm ** 2 - K) == 0:
        R = _S(1 / sp.sqrt(K))
        return f"una **esfera** (o parte de ella) de radio ${_l(R)}$: $K=1/R^2$ constante y todos sus puntos son umbílicos"
    if K == 0 and not Hm.free_symbols and Hm != 0:
        return f"una **superficie cilíndrica** de radio ${_l(_S(1 / (2 * abs(Hm))))}$ ($K=0$ y $H$ constante)"
    if K == 0:
        return "una superficie **desarrollable** (cono, cilindro…): $K=0$ (no tiene curvatura gaussiana)"
    if _flt(K.subs({p: 0.3 for p in S.params})) is not None and K.free_symbols:
        return None
    return None


@_op
def analizar_superficie(S, punto=None):
    """Análisis diferencial de una superficie paramétrica: normal, plano tangente, curvaturas, área."""
    u, v = S.params
    g = _geom(S)
    f = _formas(S, g)
    r, ru, rv, N, Nn = g["r"], g["ru"], g["rv"], g["N"], g["Nn"]
    X = variables_por_defecto(3)
    b = [H("La superficie"), L(r"\mathbf{r}(" + _l(u) + "," + _l(v) + r")=" + _lv(r))]
    if S.dominio is not None:
        b.append(T("Dominio de los parámetros: " + S.dominio.lectura + "."))
    b += [H("Vectores tangentes y normal"), T(f"Orden de los parámetros: $(u,v)=({_l(u)},{_l(v)})$. La **orientación** de la superficie es la que da $\\mathbf{{N}}=\\mathbf{{r}}_{{{_l(u)}}}\\times\\mathbf{{r}}_{{{_l(v)}}}$ "
                                           "(si escribes los parámetros en otro orden, la normal cambia de sentido)."),
          L(r"\mathbf{r}_{" + _l(u) + r"}=" + _lv(ru) + r",\qquad \mathbf{r}_{" + _l(v) + r"}=" + _lv(rv)),
          L(r"\mathbf{N}=\mathbf{r}_{" + _l(u) + r"}\times\mathbf{r}_{" + _l(v) + r"}=" + _lv(N)), L(r"\|\mathbf{N}\|=" + _l(Nn) + r"\quad\Rightarrow\quad dS=\|\mathbf{N}\|\,d" + _l(u) + r"\,d" + _l(v)),
          IN("**N** es perpendicular a la superficie; su longitud es el factor con que los parámetros $(u,v)$ **escalan el área**.")]
    # puntos singulares
    try:
        ceros = []
        for fac in sp.factor_list(g["Nn2"])[1]:
            base = fac[0]
            if base.free_symbols & set(S.params):
                sol = sp.solve(base, dict=True)
                ceros += [s_ for s_ in sol if s_]
        if g["Nn2"] == 0:
            b.append(AV("$\\mathbf{N}\\equiv\\mathbf{0}$: la parametrización es **degenerada** (no es una superficie)."))
        elif ceros:
            b.append(AV("**La parametrización es singular** donde $\\|\\mathbf{N}\\|=0$: " + "; ".join("$" + ", ".join(f"{_l(k)}={_l(v_)}" for k, v_ in c.items()) + "$" for c in ceros[:4]) +
                        ". En esos puntos no hay plano tangente definido por esta parametrización (por ejemplo los polos de una esfera o el vértice de un cono)."))
        else:
            b.append(OK("✓ $\\mathbf{N}$ nunca se anula: la superficie es **regular (suave)** con esta parametrización."))
    except Exception:  # noqa: BLE001
        pass
    # formas fundamentales y curvaturas
    b += [H("Formas fundamentales y curvaturas"),
          TAB(["forma", "coeficientes"], [["Primera ($E,F,G$)", f"$E={_l(f['E'])},\\ F={_l(f['F'])},\\ G={_l(f['G'])}$"], ["Segunda ($L,M,N$)", f"$L={_l(f['L'])},\\ M={_l(f['M'])},\\ N={_l(f['Nf'])}$"]]),
          L(r"K=\frac{LN-M^{2}}{EG-F^{2}}=" + _l(f["K"]) + r"\qquad H=\frac{EN-2FM+GL}{2(EG-F^{2})}=" + _l(f["H"]))]
    K, Hm = f["K"], f["H"]
    try:
        disc = _S(Hm ** 2 - K)
        k1, k2 = _S(Hm + sp.sqrt(disc)), _S(Hm - sp.sqrt(disc))
        b.append(L(r"\kappa_{1,2}=H\pm\sqrt{H^{2}-K}=" + _l(k1) + r",\ " + _l(k2)))
    except Exception:  # noqa: BLE001
        pass
    if not K.free_symbols:
        kf = _flt(K)
        b.append(IN(("**K > 0**: forma de cúpula (punto elíptico)." if kf and kf > 0 else "**K < 0**: forma de silla (punto hiperbólico)." if kf and kf < 0 else "**K = 0**: superficie desarrollable (se puede «desenrollar» sin deformar).")))
    else:
        b.append(IN("**K > 0**: cúpula (elíptico); **K < 0**: silla (hiperbólico); **K = 0**: se puede desenrollar. (Teorema Egregio de Gauss: $K$ no cambia si la superficie se pliega sin estirarla.)"))
    clase = _clasifica(g, f, S)
    if clase:
        b.append(OK(f"**Es {clase}.**"))
    datos = {"r": r, "ru": ru, "rv": rv, "N": N, "Nn": Nn, "K": K, "H": Hm, "clase": clase, "params": S.params}
    # área
    if S.dominio is not None:
        try:
            area, m = integrar_region(Nn, S.dominio, list(S.params))
            b += [H("Área de la superficie"), L(r"A=\iint_D\|\mathbf{N}\|\,dA=" + _exacto(area))]
            b += _bloques_metodo(m, "Cómo se integra", list(S.params))[1:]
            datos["area"] = area
        except ErrorCalculo as e:
            b.append(IN("No pude calcular el área en forma cerrada: " + str(e)))
    else:
        b.append(IN("Para el **área** escribe el dominio de los parámetros, por ejemplo ⟨…⟩, 0 ≤ u ≤ 1, 0 ≤ v ≤ 2π."))
    # en un punto
    fig = {}
    if punto is not None:
        u0, v0 = [sp.sympify(c) for c in punto]
        sub = {u: u0, v: v0}
        P0 = [_S(c.subs(sub)) for c in r]
        N0 = [_S(c.subs(sub)) for c in N]
        nn0 = _S(sp.sqrt(_dot(N0, N0)))
        b.append(H(f"En el punto ({_l(u)}, {_l(v)}) = ({_l(u0)}, {_l(v0)})"))
        b.append(L(r"\mathbf{r}=" + _lv(P0, "(", ")") + r",\qquad \mathbf{N}=" + _lv(N0)))
        if nn0 == 0:
            b.append(AV("Ahí **N = 0**: el punto es singular (no hay plano tangente con esta parametrización)."))
        else:
            n0 = [_S(c / nn0) for c in N0]
            plano = sp.Eq(sum(a * x for a, x in zip(N0, X)), _S(_dot(N0, P0)))
            s_ = sp.Symbol("s", real=True)
            b += [L(r"\text{Plano tangente: }\ " + _l(plano)), L(r"\text{Recta normal: }\ (x,y,z)=" + _lv([P0[i] + s_ * N0[i] for i in range(3)], "(", ")")),
                  L(r"\mathbf{n}=\frac{\mathbf{N}}{\|\mathbf{N}\|}=" + _lv(n0)), T(f"Curvaturas en el punto: $K={_exacto(f['K'].subs(sub))}$ y $H={_exacto(f['H'].subs(sub))}$.")]
            fig = {"P": [float(sp.N(c)) for c in P0], "n": [float(sp.N(c)) for c in n0], "u0": float(sp.N(u0)), "v0": float(sp.N(v0))}
            datos.update(P0=P0, N0=N0, plano=plano)
    datos["figura"] = fig
    return res(b, **datos)


# ==============================================================================
# INTEGRALES DE SUPERFICIE Y FLUJO
# ==============================================================================
def _nota_exterior(S, g):
    """« (la normal apunta hacia afuera/adentro del centro de la superficie)» según el promedio de la superficie; '' si no está claro."""
    try:
        import numpy as np
        caja = _caja_region(S.dominio.cond, list(S.params))
        if caja is None:
            return ""
        rng = np.random.default_rng(4)
        P = rng.uniform([c[0] for c in caja], [c[1] for c in caja], size=(400, 2))
        fc = sp.lambdify(S.params, S.dominio.cond, "numpy")
        ok = np.broadcast_to(np.asarray(fc(P[:, 0], P[:, 1]), dtype=bool), (len(P),))
        P = P[ok]
        fr = sp.lambdify(S.params, g["r"], "numpy")
        fn = sp.lambdify(S.params, g["N"], "numpy")
        R = np.array([np.broadcast_to(np.asarray(c, dtype=float), (len(P),)) for c in fr(P[:, 0], P[:, 1])]).T
        Nn = np.array([np.broadcast_to(np.asarray(c, dtype=float), (len(P),)) for c in fn(P[:, 0], P[:, 1])]).T
        centro = R.mean(axis=0)
        s = np.sign(((R - centro) * Nn).sum(axis=1))
        s = s[s != 0]
        if len(s) and (s > 0).mean() > 0.9:
            return " (en este caso la normal apunta **hacia afuera**, alejándose del centro de la superficie)"
        if len(s) and (s < 0).mean() > 0.9:
            return " (en este caso la normal apunta **hacia adentro**, hacia el centro de la superficie)"
    except Exception:  # noqa: BLE001
        pass
    return ""


@_op
def integral_superficie(S, campo=None, modo="area"):
    """∬ f dS ('escalar'), flujo ∬ F·dS ('flujo') o área ('area') de una superficie paramétrica con dominio."""
    if S.dominio is None:
        raise ErrorCalculo("La integral de superficie necesita el DOMINIO de los parámetros: escribe, por ejemplo, ⟨…⟩, 0 ≤ u ≤ 1, 0 ≤ v ≤ 2π.")
    u, v = S.params
    g = _geom(S)
    X = variables_por_defecto(3)
    sub = {X[i]: g["r"][i] for i in range(3)}
    b = [H("La superficie"), L(r"\mathbf{r}(" + _l(u) + "," + _l(v) + r")=" + _lv(g["r"])), L(r"\mathbf{N}=\mathbf{r}_{" + _l(u) + r"}\times\mathbf{r}_{" + _l(v) + r"}=" + _lv(g["N"]) + r",\quad \|\mathbf{N}\|=" + _l(g["Nn"]))]
    if modo == "area" or campo is None:
        integrando = g["Nn"]
        b += [H("Área"), T("$A=\\iint_D\\|\\mathbf{N}\\|\\,dA$")]
        etiqueta = "A"
    elif modo == "escalar":
        f = campo
        integrando = _S(f.subs(sub, simultaneous=True) * g["Nn"])
        b += [H("Integral de superficie de un campo escalar"), T("$\\displaystyle\\iint_S f\\,dS=\\iint_D f(\\mathbf{r}(u,v))\\,\\|\\mathbf{N}\\|\\,dA$"),
              T(f"$f(\\mathbf{{r}}(u,v))={_l(_S(f.subs(sub, simultaneous=True)))}$, y el integrando completo es ${_l(integrando)}$.")]
        etiqueta = r"\iint_S f\,dS"
    else:
        Fc = [sp.sympify(c) for c in campo.c]
        if len(Fc) != 3:
            raise ErrorCalculo("El flujo a través de una superficie necesita un campo de ℝ³ (tres componentes).")
        Ft = [_S(c.subs(sub, simultaneous=True)) for c in Fc]
        integrando = _S(_dot(Ft, g["N"]))
        b += [H("Flujo de un campo a través de la superficie"), T("$\\displaystyle\\iint_S\\mathbf{F}\\cdot d\\mathbf{S}=\\iint_D\\mathbf{F}(\\mathbf{r}(u,v))\\cdot\\mathbf{N}\\,dA$ (con la orientación dada por $\\mathbf{N}=\\mathbf{r}_u\\times\\mathbf{r}_v$)"),
              L(r"\mathbf{F}(\mathbf{r}(u,v))=" + _lv(Ft)), L(r"\mathbf{F}\cdot\mathbf{N}=" + _l(integrando)),
              IN(f"Orientación: $\\mathbf{{N}}=\\mathbf{{r}}_{{{_l(u)}}}\\times\\mathbf{{r}}_{{{_l(v)}}}$ con $(u,v)=({_l(u)},{_l(v)})$" + _nota_exterior(S, g) + ". Si se invierte la orientación (se usa $-\\mathbf{N}$), el flujo cambia de **signo**.")]
        etiqueta = r"\iint_S\mathbf{F}\cdot d\mathbf{S}"
    integrando = _quitar_abs(integrando, S.dominio, S.params)
    try:
        val, m = integrar_region(integrando, S.dominio, list(S.params))
    except ErrorCalculo as e:
        raise ErrorCalculo("No pude integrar sobre el dominio: " + str(e)) from None
    b += _bloques_metodo(m, "Integral sobre el dominio de los parámetros", [u, v])
    b.append(OK("**Resultado:** $" + etiqueta + "=" + _exacto(val) + "$"))
    return res(b, valor=val, integrando=integrando, N=g["N"], Nn=g["Nn"])


# ==============================================================================
# TEOREMAS: Green, Stokes, Gauss  (se calculan los dos lados)
# ==============================================================================
def _borde_circulo(c, R, t):
    return [c[0] + R * sp.cos(t), c[1] + R * sp.sin(t)]


def _trabajo_param(Fc, vars_, comps, t, a, b_):
    """∫_a^b F(r(t))·r'(t) dt."""
    sub = dict(zip(vars_, comps))
    integrando = _S(sum(_S(F.subs(sub, simultaneous=True)) * sp.diff(c, t) for F, c in zip(Fc, comps)))
    try:
        v = sp.integrate(integrando, (t, a, b_))
        if v.has(sp.Integral):
            return sp.N(sp.Integral(integrando, (t, a, b_)), 12)
        return _S(v)
    except Exception:  # noqa: BLE001
        return sp.N(sp.Integral(integrando, (t, a, b_)), 12)


@_op
def teorema_green(campo, region):
    """∮_{∂D} P dx + Q dy = ∬_D (Q_x − P_y) dA, con D un círculo o un rectángulo."""
    P, Q = [sp.sympify(c) for c in campo.c]
    X = variables_por_defecto(2)
    x, y = X
    t = sp.Symbol("t", real=True)
    g = _S(sp.diff(Q, x) - sp.diff(P, y))
    R = region.region(X) if isinstance(region, Bola) else region
    b = [H("Teorema de Green"), L(r"\oint_{\partial D}P\,dx+Q\,dy=\iint_D\left(\frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}\right)dA"),
         T("Campo: $\\mathbf{F}=" + _lv([P, Q]) + "$. Integrando de Green: $Q_x-P_y=" + _l(g) + "$. La frontera se recorre en sentido **antihorario**.")]
    lado_doble, m = integrar_region(g, R, list(X)) if not isinstance(region, Bola) or True else (None, None)
    b += [H("Lado izquierdo: integral doble"), L(r"\iint_D\left(" + _l(g) + r"\right)dA=" + _exacto(lado_doble))]
    # frontera
    if isinstance(region, Bola):
        c, rad = region.centro.c, region.radio
        comps = _borde_circulo(c, rad, t)
        lado_linea = _trabajo_param([P, Q], X, comps, t, 0, 2 * sp.pi)
        b += [H("Lado derecho: integral de línea sobre la circunferencia"), T(f"$\\mathbf{{r}}(t)={_lv(comps)}$, $t\\in[0,2\\pi]$."), L(r"\oint_{\partial D}P\,dx+Q\,dy=" + _exacto(lado_linea))]
    else:
        rc = _rect(R)
        if rc is None:
            raise ErrorCalculo("La verificación automática de Green funciona para círculos (bolas) y rectángulos.")
        (a, bb), (c, d) = rc[x], rc[y]
        bordes = [([t, c], (a, bb)), ([bb, t], (c, d)), ([t, d], (bb, a)), ([a, t], (d, c))]
        total, filas = 0, []
        for k, (comps, (t0, t1)) in enumerate(bordes):
            val = _trabajo_param([P, Q], X, comps, t, t0, t1)
            total += val
            filas.append([f"lado {k + 1}", f"$\\mathbf{{r}}(t)={_lv(comps, '(', ')')},\\ t\\ \\text{{de }}{_l(t0)}\\text{{ a }}{_l(t1)}$", f"${_l(_S(val))}$"])
        lado_linea = _S(total)
        b += [H("Lado derecho: integral de línea sobre los cuatro lados"), TAB(["lado", "parametrización", "∫ F·dr"], filas), L(r"\oint_{\partial D}P\,dx+Q\,dy=" + _exacto(lado_linea))]
    ok = abs(float(sp.N(lado_doble - lado_linea))) < 1e-8
    b.append((OK if ok else AV)(("✅ **Los dos lados coinciden**: " if ok else "⚠️ Difieren: ") + f"${_exacto(lado_doble)}$ frente a ${_exacto(lado_linea)}$."))
    return res(b, doble=lado_doble, linea=lado_linea, coincide=ok)


@_op
def teorema_gauss(campo, bola):
    """∯_{∂E} F·n dS = ∭_E ∇·F dV, con E una bola (esfera de frontera)."""
    if not isinstance(bola, Bola) or bola.n != 3:
        raise ErrorCalculo("La verificación del teorema de la divergencia funciona para bolas de ℝ³.")
    Fc = [sp.sympify(c) for c in campo.c]
    X = variables_por_defecto(3)
    div = _S(sum(sp.diff(c, v) for c, v in zip(Fc, X)))
    R = bola.region(X)
    b = [H("Teorema de la divergencia (Gauss)"), L(r"\oiint_{\partial E}\mathbf{F}\cdot\mathbf{n}\,dS=\iiint_E\nabla\cdot\mathbf{F}\,dV"),
         T("Campo: $\\mathbf{F}=" + _lv(Fc) + "$, con $\\nabla\\cdot\\mathbf{F}=" + _l(div) + "$.")]
    triple, m = integrar_region(div, R, list(X))
    b += [H("Lado derecho: integral triple de la divergencia"), L(r"\iiint_E\nabla\cdot\mathbf{F}\,dV=" + _exacto(triple))]
    ph, th = sp.symbols("phi theta", real=True)
    c, rad = bola.centro.c, bola.radio
    r_ = [c[0] + rad * sp.sin(ph) * sp.cos(th), c[1] + rad * sp.sin(ph) * sp.sin(th), c[2] + rad * sp.cos(ph)]
    dom = Region((ph, th), sp.And(sp.Ge(ph, 0), sp.Le(ph, sp.pi), sp.Ge(th, 0), sp.Le(th, 2 * sp.pi)), "φ ∈ [0, π], θ ∈ [0, 2π]")
    S = Superficie((ph, th), r_, dom)
    g = _geom(S)
    N = g["N"]
    # orientación hacia afuera: N·(r − c) debe ser positivo
    prueba = {ph: sp.pi / 3, th: sp.Rational(1, 5)}
    signo = _flt(sp.N(_dot([n_.subs(prueba) for n_ in N], [(r_[i] - c[i]).subs(prueba) for i in range(3)])))
    if signo is not None and signo < 0:
        N = [-n_ for n_ in N]
    sub = dict(zip(X, r_))
    integrando = _quitar_abs(_S(_dot([_S(f.subs(sub, simultaneous=True)) for f in Fc], N)), dom, (ph, th))
    flujo, m2 = integrar_region(integrando, dom, [ph, th])
    b += [H("Lado izquierdo: flujo a través de la esfera (hacia afuera)"),
          T("Parametrización de la esfera: $\\mathbf{r}(\\varphi,\\theta)=" + _lv(r_) + "$, $\\varphi\\in[0,\\pi]$, $\\theta\\in[0,2\\pi]$, con la normal $\\mathbf{N}$ orientada **hacia afuera**."),
          L(r"\mathbf{F}\cdot\mathbf{N}=" + _l(integrando)), L(r"\oiint_{\partial E}\mathbf{F}\cdot\mathbf{n}\,dS=" + _exacto(flujo))]
    ok = abs(float(sp.N(triple - flujo))) < 1e-8
    b.append((OK if ok else AV)(("✅ **Los dos lados coinciden**: " if ok else "⚠️ Difieren: ") + f"${_exacto(triple)}$ frente a ${_exacto(flujo)}$."))
    return res(b, triple=triple, flujo=flujo, coincide=ok)


@_op
def teorema_stokes(campo, S):
    """∬_S (∇×F)·dS = ∮_{∂S} F·dr, con S de dominio RECTANGULAR en los parámetros (borde = imagen del borde del rectángulo)."""
    Fc = [sp.sympify(c) for c in campo.c]
    X = variables_por_defecto(3)
    u, v = S.params
    rc = _rect(S.dominio) if S.dominio is not None else None
    if rc is None:
        raise ErrorCalculo("La verificación automática de Stokes necesita un dominio rectangular en los parámetros: a ≤ u ≤ b, c ≤ v ≤ d.")
    (a, bb), (c, d) = rc[u], rc[v]
    P, Q, R = Fc
    rot = [_S(sp.diff(R, X[1]) - sp.diff(Q, X[2])), _S(sp.diff(P, X[2]) - sp.diff(R, X[0])), _S(sp.diff(Q, X[0]) - sp.diff(P, X[1]))]
    g = _geom(S)
    sub = dict(zip(X, g["r"]))
    integrando = _quitar_abs(_S(_dot([_S(f.subs(sub, simultaneous=True)) for f in rot], g["N"])), S.dominio, S.params)
    b = [H("Teorema de Stokes"), L(r"\iint_S(\nabla\times\mathbf{F})\cdot d\mathbf{S}=\oint_{\partial S}\mathbf{F}\cdot d\mathbf{r}"),
         T("Campo $\\mathbf{F}=" + _lv(Fc) + "$ con $\\nabla\\times\\mathbf{F}=" + _lv(rot) + "$. La orientación del borde es la inducida por $\\mathbf{N}=\\mathbf{r}_u\\times\\mathbf{r}_v$ (el borde del rectángulo en sentido antihorario en el plano $(u,v)$).")]
    lado_sup, m = integrar_region(integrando, S.dominio, [u, v])
    b += [H("Lado izquierdo: flujo del rotacional por la superficie"), L(r"(\nabla\times\mathbf{F})\cdot\mathbf{N}=" + _l(integrando)), L(r"\iint_S(\nabla\times\mathbf{F})\cdot d\mathbf{S}=" + _exacto(lado_sup))]
    t = sp.Symbol("t", real=True)
    bordes = [({u: t, v: c}, (a, bb)), ({u: bb, v: t}, (c, d)), ({u: t, v: d}, (bb, a)), ({u: a, v: t}, (d, c))]
    total, filas = 0, []
    for k, (asign, (t0, t1)) in enumerate(bordes):
        comps = [_S(co.subs(asign, simultaneous=True)) for co in g["r"]]
        val = _trabajo_param(Fc, X, comps, t, t0, t1)
        total += val
        filas.append([f"lado {k + 1}", f"${_lv(comps, '(', ')')}$", f"${_l(_S(val))}$"])
    lado_lin = _S(total)
    b += [H("Lado derecho: circulación sobre el borde (imagen de los cuatro lados)"), TAB(["lado", "curva r(t)", "∫ F·dr"], filas),
          IN("Si un lado del rectángulo se colapsa a un punto (como los polos de una esfera), su integral es 0."), L(r"\oint_{\partial S}\mathbf{F}\cdot d\mathbf{r}=" + _exacto(lado_lin))]
    ok = abs(float(sp.N(lado_sup - lado_lin))) < 1e-8
    b.append((OK if ok else AV)(("✅ **Los dos lados coinciden**: " if ok else "⚠️ Difieren: ") + f"${_exacto(lado_sup)}$ frente a ${_exacto(lado_lin)}$."))
    return res(b, superficie=lado_sup, borde=lado_lin, coincide=ok)


@_op
def gauss_desde_region(IR):
    """Comprueba el teorema de la divergencia cuando el integrando de ∭ era ∇·F y la región es una bola."""
    if IR.origen_div is None or len(IR.vars) != 3:
        raise ErrorCalculo("Esta comprobación necesita una integral triple de ∇·F (por ejemplo ∭ ∇·⟨x,y,z⟩ dV) sobre una bola.")
    vs = list(IR.vars)
    atomos = _atomos_de(IR.region.cond)
    if len(atomos) != 1:
        raise ErrorCalculo("La región no es una bola (hay más de una desigualdad).")
    g, _ = atomos[0]
    cs = _IM._centro(atomos, vs)
    try:
        P = sp.Poly(g, *vs)
        k = P.coeff_monomial(vs[0] ** 2)
        centro = [cs.get(v, sp.Integer(0)) for v in vs]
        R2 = sp.simplify(-g.subs(dict(zip(vs, centro)), simultaneous=True) / k)
        if k == 0 or R2 <= 0 or any(sp.simplify(P.coeff_monomial(v ** 2) - k) != 0 for v in vs):
            raise ValueError
    except Exception:  # noqa: BLE001
        raise ErrorCalculo("La región no es una bola (esfera sólida).") from None
    return teorema_gauss(IR.origen_div, Bola(Punto(centro), sp.sqrt(R2)))
