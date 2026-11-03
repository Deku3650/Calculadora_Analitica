"""
calculo_vectorial.py
====================
Cálculo diferencial e integral de CAMPOS y SUPERFICIES (Cálculo III y IV).

PARTE A (este archivo, primera mitad)
  · ∇·F, ∇×F, ∇²f con el procedimiento y la interpretación
  · análisis de un campo: jacobiano, divergencia, rotacional, ¿conservativo? y FUNCIÓN POTENCIAL
    (con la advertencia clásica: rotacional cero NO basta si el dominio tiene un hueco)
  · integrales de LÍNEA: ∫ f ds, ∫ F·dr (trabajo/circulación), flujo plano; con el teorema de Green
  · derivación IMPLÍCITA (una y dos variables independientes) y REGLA DE LA CADENA

PARTE B (segunda mitad)
  · superficies paramétricas: normal, plano tangente, formas fundamentales, curvaturas K y H, área
  · integrales de superficie y FLUJO
  · verificación de los teoremas de GREEN, STOKES y GAUSS (divergencia)
"""
from __future__ import annotations

import math

import sympy as sp

import calculo_motor as M
from calculo_motor import AV, ER, H, IN, L, OK, T, TAB, ErrorCalculo, _flt, _op, res
from estructuras import (Bola, Curva, Divergencia, Laplaciano, Region, Rotacional, Superficie, Vector, Punto, evaluar_operador, variables_campo,
                         variables_escalar, variables_por_defecto)


def _l(e) -> str:
    return sp.latex(e)


def _S(e):
    try:
        return sp.simplify(e)
    except Exception:  # noqa: BLE001
        return e


def _lv(v, pre=r"\left\langle ", post=r"\right\rangle") -> str:
    return pre + ", ".join(_l(c) for c in v) + post


def _num(v, d=6) -> str:
    f = _flt(v)
    if f is None:
        return _l(v)
    return str(int(round(f))) if abs(f - round(f)) < 1e-9 else f"{f:.{d}g}"


def _exacto(v) -> str:
    v = _S(v)
    return _l(v) if (v.is_Integer or v.free_symbols) else _l(v) + r"\approx " + _l(sp.N(v, 8))


def _nombres_comp(n):
    return ["P", "Q", "R"][:n] if n <= 3 else [f"F_{{{i + 1}}}" for i in range(n)]


# ==============================================================================
# 1. OPERADORES  ∇·F, ∇×F, ∇²f
# ==============================================================================
@_op
def evaluar_operador_vec(obj):
    """Divergencia, rotacional o laplaciano con el procedimiento paso a paso."""
    b = []
    if isinstance(obj, Laplaciano):
        f = _S(obj.arg)
        vs = variables_escalar(f)
        segs = [_S(sp.diff(f, v, 2)) for v in vs]
        total = _S(sum(segs))
        b += [H("Laplaciano"), L(r"\nabla^{2}f=" + "+".join(r"\frac{\partial^{2} f}{\partial " + _l(v) + r"^{2}}" for v in vs)),
              TAB(["derivada segunda", "resultado"], [[f"$\\dfrac{{\\partial^2 f}}{{\\partial {_l(v)}^2}}$", f"${_l(s)}$"] for v, s in zip(vs, segs)]),
              L(r"\nabla^{2}f=" + _l(total))]
        if total == 0:
            b.append(OK("El laplaciano es **0**: $f$ es una función **armónica** (cumple la ecuación de Laplace)."))
        else:
            b.append(IN("El laplaciano mide cuánto difiere el valor de $f$ en un punto del promedio de sus vecinos: positivo si $f$ está «por debajo» de su entorno."))
        return res(b, valor=total)
    comps = tuple(_S(c) for c in obj.comps)
    n = len(comps)
    vs = variables_campo(comps)
    if len(vs) != n:
        raise ErrorCalculo(f"El campo tiene {n} componentes pero {len(vs)} variable(s) ({', '.join(str(v) for v in vs)}): hacen falta tantas variables como componentes.")
    nm = _nombres_comp(n)
    b += [H("El campo"), L(r"\mathbf{F}=" + _lv(comps) + r"\quad\text{con variables }" + ", ".join(_l(v) for v in vs))]
    if isinstance(obj, Divergencia):
        parc = [_S(sp.diff(c, v)) for c, v in zip(comps, vs)]
        total = _S(sum(parc))
        b += [H("Divergencia"), L(r"\nabla\cdot\mathbf{F}=" + "+".join(r"\frac{\partial " + a + r"}{\partial " + _l(v) + "}" for a, v in zip(nm, vs))),
              TAB(["término", "valor"], [[f"$\\dfrac{{\\partial {a}}}{{\\partial {_l(v)}}}$", f"${_l(p)}$"] for a, v, p in zip(nm, vs, parc)]),
              L(r"\nabla\cdot\mathbf{F}=" + _l(total))]
        if total == 0:
            b.append(OK("La divergencia es **0**: el campo es **solenoidal** (incompresible). El flujo neto a través de cualquier superficie cerrada es cero."))
        elif not total.free_symbols:
            b.append(IN(f"La divergencia es la constante ${_l(total)}$: " + ("el campo **se expande** (fuente) en todos los puntos." if _flt(total) and _flt(total) > 0 else "el campo **se comprime** (sumidero) en todos los puntos.")))
        else:
            b.append(IN("Donde la divergencia es **positiva** el campo se expande (hay una **fuente**); donde es **negativa** se comprime (**sumidero**)."))
            try:
                ceros = sp.solve(total, vs[0]) if len(total.free_symbols) == 1 else None
                if ceros:
                    b.append(T(f"La divergencia se anula en ${_l(vs[0])}\\in{_l(sp.FiniteSet(*ceros))}$."))
            except Exception:  # noqa: BLE001
                pass
        return res(b, valor=total, campo=comps, vars=vs)
    # rotacional
    if n == 2:
        P, Q = comps
        val = _S(sp.diff(Q, vs[0]) - sp.diff(P, vs[1]))
        b += [H("Rotacional (campo plano)"), L(r"\operatorname{rot}\mathbf{F}=\frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}=" + _l(sp.diff(Q, vs[0])) + "-" + f"({_l(sp.diff(P, vs[1]))})=" + _l(val)),
              IN("En el plano el rotacional es un **escalar** (la componente $z$ del rotacional en ℝ³).")]
        if val == 0:
            b.append(OK("El rotacional es **0**: el campo es **irrotacional**."))
        return res(b, valor=val, campo=comps, vars=vs)
    P, Q, R = comps
    x, y, z = vs
    cx, cy, cz = _S(sp.diff(R, y) - sp.diff(Q, z)), _S(sp.diff(P, z) - sp.diff(R, x)), _S(sp.diff(Q, x) - sp.diff(P, y))
    b += [H("Rotacional"),
          L(r"\nabla\times\mathbf{F}=\begin{vmatrix}\mathbf{i}&\mathbf{j}&\mathbf{k}\\ \partial_{" + _l(x) + r"}&\partial_{" + _l(y) + r"}&\partial_{" + _l(z) + r"}\\ P&Q&R\end{vmatrix}"
            r"=\left\langle \frac{\partial R}{\partial y}-\frac{\partial Q}{\partial z},\ \frac{\partial P}{\partial z}-\frac{\partial R}{\partial x},\ \frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}\right\rangle"),
          TAB(["componente", "cálculo", "valor"], [["$\\mathbf{i}$", f"${_l(sp.diff(R, y))}-({_l(sp.diff(Q, z))})$", f"${_l(cx)}$"],
                                                    ["$\\mathbf{j}$", f"${_l(sp.diff(P, z))}-({_l(sp.diff(R, x))})$", f"${_l(cy)}$"],
                                                    ["$\\mathbf{k}$", f"${_l(sp.diff(Q, x))}-({_l(sp.diff(P, y))})$", f"${_l(cz)}$"]]),
          L(r"\nabla\times\mathbf{F}=" + _lv([cx, cy, cz]))]
    if cx == cy == cz == 0:
        b.append(OK("El rotacional es **0**: el campo es **irrotacional**. Si su dominio no tiene huecos, es **conservativo** (existe una función potencial)."))
    else:
        b.append(IN("El rotacional mide cuánto **gira** el campo alrededor de cada punto; su dirección es el eje de giro (regla de la mano derecha)."))
    return res(b, valor=Vector([cx, cy, cz]), campo=comps, vars=vs)


# ==============================================================================
# 2. CAMPOS: jacobiano, ¿conservativo?, potencial
# ==============================================================================
def potencial(comps, vs):
    """φ con ∇φ = F (o None). Devuelve (φ, pasos)."""
    n = len(comps)
    pasos = []
    phi = sp.integrate(comps[0], vs[0])
    pasos.append(f"Se integra la 1.ª componente respecto de ${_l(vs[0])}$: $\\varphi={_l(phi)}+g({', '.join(_l(v) for v in vs[1:])})$.")
    for k in range(1, n):
        resto = _S(comps[k] - sp.diff(phi, vs[k]))
        if any(resto.has(v) for v in vs[:k]):
            return None, pasos + [f"Al comparar con la componente {k + 1} queda ${_l(resto)}$, que todavía depende de {', '.join(_l(v) for v in vs[:k])}: **no existe potencial**."]
        extra = sp.integrate(resto, vs[k])
        pasos.append(f"$\\partial\\varphi/\\partial {_l(vs[k])}$ debe ser ${_l(comps[k])}$; lo que falta es ${_l(resto)}$, que integrado respecto de ${_l(vs[k])}$ da ${_l(extra)}$.")
        phi = phi + extra
    phi = _S(phi)
    if all(_S(sp.diff(phi, v) - c) == 0 for v, c in zip(vs, comps)):
        return phi, pasos
    return None, pasos + ["La verificación $\\nabla\\varphi=\\mathbf{F}$ falló."]


def _hueco_2d(comps, vs):
    """Punto singular aislado (a, b) de un campo plano con denominadores tipo (x−a)²+(y−b)² (el «hueco» del dominio)."""
    if len(vs) != 2:
        return None
    x, y = vs
    for c in comps:
        den = sp.denom(sp.together(c))
        if not den.has(x) and not den.has(y):
            continue
        try:
            P = sp.Poly(sp.expand(den), x, y)
        except sp.PolynomialError:
            continue
        if P.total_degree() != 2:
            continue
        kx, ky = P.coeff_monomial(x ** 2), P.coeff_monomial(y ** 2)
        if kx == 0 or sp.simplify(kx - ky) != 0 or P.coeff_monomial(x * y) != 0:
            continue
        a, b = -P.coeff_monomial(x) / (2 * kx), -P.coeff_monomial(y) / (2 * ky)
        c0 = P.coeff_monomial(1)
        if sp.simplify(c0 - kx * (a ** 2 + b ** 2)) == 0:             # den = k[(x−a)² + (y−b)²]: se anula SOLO en (a, b)
            return (sp.simplify(a), sp.simplify(b))
    return None


def _singularidad_general(comps, vs):
    for c in comps:
        den = sp.denom(sp.together(c))
        if den.free_symbols & set(vs):
            return den
    return None


@_op
def analizar_campo(F):
    """Campo vectorial: jacobiano, divergencia, rotacional, ¿conservativo? y función potencial."""
    comps = tuple(_S(c) for c in F.c)
    n = len(comps)
    vs = variables_campo(comps)
    b = [H("El campo"), L(r"\mathbf{F}=" + _lv(comps)), T("Variables: " + ", ".join(f"${_l(v)}$" for v in vs) + f". Es una función de ℝ^{len(vs)} en ℝ^{n}.")]
    datos = {"campo": comps, "vars": vs}
    J = sp.Matrix([[sp.diff(c, v) for v in vs] for c in comps])
    b += [H("Matriz jacobiana"), L(r"J_{\mathbf{F}}=\left(\frac{\partial F_i}{\partial x_j}\right)=" + _l(J.applyfunc(_S)))]
    if J.shape[0] == J.shape[1]:
        det = _S(J.det())
        b.append(L(r"\det J_{\mathbf{F}}=" + _l(det)))
        b.append(IN("Donde el determinante jacobiano **no se anula**, la función es localmente invertible (teorema de la función inversa); su valor absoluto es el factor con que se **escala el área/volumen**."))
        datos["det_jacobiano"] = det
    if len(vs) != n or n not in (2, 3):
        return res(b, **datos)
    div = _S(sum(sp.diff(c, v) for c, v in zip(comps, vs)))
    b += [H("Divergencia"), L(r"\nabla\cdot\mathbf{F}=" + _l(div))]
    datos["div"] = div
    if div == 0:
        b.append(IN("Divergencia 0: campo **solenoidal** (incompresible)."))
    if n == 2:
        P, Q = comps
        rot = _S(sp.diff(Q, vs[0]) - sp.diff(P, vs[1]))
        b += [H("Rotacional"), L(r"\operatorname{rot}\mathbf{F}=Q_x-P_y=" + _l(rot))]
        irrot = rot == 0
    else:
        P, Q, R = comps
        rotv = [_S(sp.diff(R, vs[1]) - sp.diff(Q, vs[2])), _S(sp.diff(P, vs[2]) - sp.diff(R, vs[0])), _S(sp.diff(Q, vs[0]) - sp.diff(P, vs[1]))]
        b += [H("Rotacional"), L(r"\nabla\times\mathbf{F}=" + _lv(rotv))]
        irrot = all(c == 0 for c in rotv)
        rot = Vector(rotv)
    datos["rot"] = rot
    b.append(H("¿Es conservativo?"))
    if not irrot:
        b.append(AV("El rotacional **no es 0**, así que el campo **NO es conservativo**: no existe una función $\\varphi$ con $\\nabla\\varphi=\\mathbf{F}$, y el trabajo depende del camino."))
        datos["conservativo"] = False
        return res(b, **datos)
    b.append(T("El rotacional es **0** (irrotacional). Esto es **necesario**, pero para ser conservativo también hace falta que el **dominio no tenga huecos** (que sea simplemente conexo)."))
    hueco = _hueco_2d(comps, vs)
    sing = _singularidad_general(comps, vs)
    if hueco is not None:
        a, bb = hueco
        t = sp.Symbol("t", real=True)
        cx, cy = vs
        circ = _S(sp.integrate(_S(comps[0].subs({cx: a + sp.cos(t), cy: bb + sp.sin(t)}, simultaneous=True) * (-sp.sin(t)) +
                                  comps[1].subs({cx: a + sp.cos(t), cy: bb + sp.sin(t)}, simultaneous=True) * sp.cos(t)), (t, 0, 2 * sp.pi)))
        b += [AV(f"⚠️ **El campo no está definido en $({_l(a)}, {_l(bb)})$** y el dominio tiene un **hueco** ahí."),
              T(f"Se comprueba con la circulación alrededor del hueco (circunferencia de radio 1): $\\oint\\mathbf{{F}}\\cdot d\\mathbf{{r}}={_l(circ)}$.")]
        if circ != 0:
            b.append(AV("La circulación **no es 0**, así que el campo **NO es conservativo** en ese dominio (aunque su rotacional sea 0). Es el ejemplo clásico del campo del «remolino»."))
            datos["conservativo"] = False
            return res(b, **datos)
        b.append(IN("La circulación alrededor del hueco es 0."))
    elif sing is not None:
        b.append(AV(f"⚠️ El campo no está definido donde ${_l(sing)}=0$: **revisa si el dominio tiene huecos**; si los tiene, rotacional cero no basta."))
    phi, pasos = potencial(comps, vs)
    if phi is None:
        b += [T("No se encontró función potencial:")] + [T("- " + p) for p in pasos]
        datos["conservativo"] = False
        return res(b, **datos)
    b += [H("Función potencial")] + [T("- " + p) for p in pasos]
    b += [L(r"\varphi(" + ",".join(_l(v) for v in vs) + r")=" + _l(phi) + r"+C"), OK(f"✅ **Es conservativo** con potencial $\\varphi={_l(phi)}$ (se verifica que $\\nabla\\varphi=\\mathbf{{F}}$).")]
    b.append(IN("Con un potencial, la integral de línea **no depende del camino**: $\\int_C\\mathbf{F}\\cdot d\\mathbf{r}=\\varphi(B)-\\varphi(A)$, y es **0** para toda curva cerrada."))
    datos.update(conservativo=True, potencial=phi)
    return res(b, **datos)


# ==============================================================================
# 3. INTEGRALES DE LÍNEA
# ==============================================================================
def _intervalos(dom):
    """Lista de intervalos finitos de un conjunto de ℝ."""
    if dom is None or dom == sp.S.Reals:
        raise ErrorCalculo("La integral de línea necesita un intervalo FINITO para el parámetro: escribe, por ejemplo, ⟨…⟩, 0 ≤ t ≤ 2π.")
    partes = list(dom.args) if isinstance(dom, sp.Union) else [dom]
    out = []
    for p in partes:
        if isinstance(p, sp.Interval) and p.start.is_finite and p.end.is_finite:
            out.append(p)
        elif isinstance(p, sp.FiniteSet):
            continue
        else:
            raise ErrorCalculo("El parámetro debe recorrer intervalos finitos.")
    if not out:
        raise ErrorCalculo("El intervalo del parámetro es vacío.")
    return out


def _integrar_1d(g, t, a, b):
    """Integral definida exacta (o numérica si no hay primitiva). Devuelve (valor, exacto?)."""
    try:
        v = sp.integrate(g, (t, a, b))
        if not v.has(sp.Integral):
            return _S(v), True
    except Exception:  # noqa: BLE001
        pass
    return sp.N(sp.Integral(g, (t, a, b)), 12), False


@_op
def integral_linea(C, campo, modo="trabajo"):
    """
    ∫_C f ds (modo 'escalar'), ∫_C F·dr (modo 'trabajo') o flujo plano ∮ F·n ds (modo 'flujo').
    `campo` es una expresión en x, y, z (escalar) o un Vector con componentes en x, y, z.
    """
    t = C.param
    comps = [_S(c) for c in C.comps]
    n = len(comps)
    X = variables_por_defecto(n)
    ints = _intervalos(C.dominio)
    sub = {X[i]: comps[i] for i in range(n)}
    rp = [_S(sp.diff(c, t)) for c in comps]
    v = _S(sp.sqrt(sum(c ** 2 for c in rp)))
    b = [H("La curva"), L(r"\mathbf{r}(" + _l(t) + r")=" + _lv(comps) + r",\quad " + _l(t) + r"\in" + _l(C.dominio)), L(r"\mathbf{r}'(" + _l(t) + r")=" + _lv(rp) + r",\quad \|\mathbf{r}'\|=" + _l(v))]
    cerrada = len(ints) == 1 and all(_S(c.subs(t, ints[0].start) - c.subs(t, ints[0].end)) == 0 for c in comps)
    if modo == "escalar":
        f = campo if isinstance(campo, sp.Expr) else None
        if f is None:
            raise ErrorCalculo("Para ∫ f ds hace falta un campo ESCALAR (una función de x, y, z).")
        integrando = _S(f.subs(sub, simultaneous=True) * v)
        b += [H("Integral de línea de un campo escalar"), T("$\\displaystyle\\int_C f\\,ds=\\int_a^b f(\\mathbf{r}(t))\\,\\|\\mathbf{r}'(t)\\|\\,dt$"),
              T(f"Se sustituye $(x,y{',z' if n == 3 else ''})$ por la curva: $f(\\mathbf{{r}}(t))={_l(_S(f.subs(sub, simultaneous=True)))}$."), L(r"\int_C f\,ds=\int" + r"_{" + _l(ints[0].start) + "}^{" + _l(ints[0].end) + "}" + _l(integrando) + r"\,d" + _l(t))]
        titulo_res = r"\int_C f\,ds"
    else:
        if not isinstance(campo, (Vector, Punto)):
            raise ErrorCalculo("Para el trabajo o el flujo hace falta un CAMPO VECTORIAL, por ejemplo ⟨y, x⟩ o ⟨−y, x, 0⟩.")
        Fc = [sp.sympify(c) for c in campo.c]
        if len(Fc) != n:
            raise ErrorCalculo(f"La curva está en ℝ^{n} y el campo tiene {len(Fc)} componentes: deben coincidir.")
        Ft = [_S(c.subs(sub, simultaneous=True)) for c in Fc]
        if modo == "trabajo":
            integrando = _S(sum(a * c for a, c in zip(Ft, rp)))
            b += [H("Integral de línea de un campo vectorial (trabajo / circulación)"), T("$\\displaystyle\\int_C\\mathbf{F}\\cdot d\\mathbf{r}=\\int_a^b \\mathbf{F}(\\mathbf{r}(t))\\cdot\\mathbf{r}'(t)\\,dt$"),
                  L(r"\mathbf{F}(\mathbf{r}(t))=" + _lv(Ft)), L(r"\mathbf{F}(\mathbf{r}(t))\cdot\mathbf{r}'(t)=" + _l(integrando))]
            titulo_res = r"\int_C\mathbf{F}\cdot d\mathbf{r}"
        else:
            if n != 2:
                raise ErrorCalculo("El flujo a través de una CURVA solo tiene sentido para curvas planas (ℝ²). Para superficies usa la integral de superficie.")
            integrando = _S(Ft[0] * rp[1] - Ft[1] * rp[0])
            b += [H("Flujo plano a través de la curva"), T("Con la normal $\\mathbf{n}\\,ds=(y',-x')\\,dt$ (hacia la **derecha** del recorrido; hacia **afuera** si la curva cerrada se recorre en sentido antihorario):"),
                  L(r"\oint_C\mathbf{F}\cdot\mathbf{n}\,ds=\int (P\,y'-Q\,x')\,dt=\int " + _l(integrando) + r"\,d" + _l(t))]
            titulo_res = r"\oint_C\mathbf{F}\cdot\mathbf{n}\,ds"
    total, exacto = 0, True
    for iv in ints:
        val, ex = _integrar_1d(integrando, t, iv.start, iv.end)
        total += val
        exacto = exacto and ex
    total = _S(total) if exacto else total
    simbolo = r"\oint_C" if cerrada else r"\int_C"
    b.append(OK("**Resultado:** $" + titulo_res.replace(r"\int_C", simbolo).replace(r"\oint_C", simbolo if cerrada else r"\int_C") + "=" + _exacto(total) + "$"))
    if not exacto:
        b.append(IN("No hay primitiva sencilla: se evaluó **numéricamente**."))
    datos = {"valor": total, "integrando": integrando, "cerrada": cerrada}
    if modo == "escalar" and f == 1:
        b.append(IN("Con $f=1$ la integral es la **longitud** de la curva."))
    if modo == "trabajo":
        b.append(IN("Si se recorre la curva en sentido **contrario**, el resultado cambia de **signo**."))
        # ¿conservativo? entonces coincide con la diferencia de potencial
        try:
            vs = X
            if all(c.free_symbols <= set(vs) for c in Fc):
                phi, _p = potencial(tuple(Fc), vs)
                if phi is not None and not _hueco_2d(tuple(Fc), vs) and _singularidad_general(tuple(Fc), vs) is None:
                    A = {vs[i]: comps[i].subs(t, ints[0].start) for i in range(n)}
                    B_ = {vs[i]: comps[i].subs(t, ints[-1].end) for i in range(n)}
                    dif = _S(phi.subs(B_, simultaneous=True) - phi.subs(A, simultaneous=True))
                    b += [H("Comprobación con la función potencial"), T(f"El campo es conservativo con $\\varphi={_l(phi)}$, así que $\\int_C\\mathbf{{F}}\\cdot d\\mathbf{{r}}=\\varphi(B)-\\varphi(A)={_l(dif)}$"
                                                                   + (" ✅ coincide." if exacto and _S(dif - total) == 0 else "."))]
                    datos["potencial"] = phi
        except Exception:  # noqa: BLE001
            pass
        if cerrada and n == 2:
            P_, Q_ = Fc
            x, y = X
            g = _S(sp.diff(Q_, x) - sp.diff(P_, y))
            b.append(H("Teorema de Green"))
            area_signo = _S(sum(sp.integrate(_S(comps[0] * rp[1] - comps[1] * rp[0]), (t, iv.start, iv.end)) for iv in ints) / 2)
            if not g.free_symbols:
                esperado = _S(g * area_signo)
                b.append(T(f"La curva es cerrada y plana: $\\oint P\\,dx+Q\\,dy=\\iint_D\\left(\\dfrac{{\\partial Q}}{{\\partial x}}-\\dfrac{{\\partial P}}{{\\partial y}}\\right)dA$. Aquí el integrando de Green es la constante ${_l(g)}$ y el área (con signo, positiva si es antihoraria) es ${_l(area_signo)}$, "
                           f"así que la integral vale ${_l(g)}\\cdot{_l(area_signo)}={_l(esperado)}$" + (" ✅ **coincide**." if exacto and _S(esperado - total) == 0 else ".")))
            else:
                b.append(T(f"El integrando de Green es $\\dfrac{{\\partial Q}}{{\\partial x}}-\\dfrac{{\\partial P}}{{\\partial y}}={_l(g)}$: la integral de línea es igual a la integral **doble** de eso sobre la región encerrada (usa ∬ para comprobarlo)."))
            datos["green_integrando"] = g
    if modo == "flujo" and cerrada:
        P_, Q_ = Fc
        x, y = X
        d = _S(sp.diff(P_, x) + sp.diff(Q_, y))
        b.append(IN(f"Por el teorema de la divergencia en el plano, este flujo es $\\iint_D\\nabla\\cdot\\mathbf{{F}}\\,dA$ con $\\nabla\\cdot\\mathbf{{F}}={_l(d)}$."))
    return res(b, **datos)


# ==============================================================================
# 4. DERIVACIÓN IMPLÍCITA
# ==============================================================================
@_op
def derivada_implicita(rel, dependiente=None, punto=None):
    """
    F(x, y) = G  ⇒  dy/dx  (y d²y/dx²);   F(x, y, z) = G ⇒ ∂z/∂x, ∂z/∂y.
    `dependiente`: la variable que se despeja «implícitamente» (por defecto la última por orden alfabético: y, o z).
    `punto`: dict {variable: valor} para evaluar y obtener la recta/plano tangente.
    """
    if not isinstance(rel, sp.Equality):
        raise ErrorCalculo("La derivación implícita necesita una ECUACIÓN, por ejemplo x² + y² = 25.")
    Fx = _S(rel.lhs - rel.rhs)
    vs = sorted([s for s in Fx.free_symbols if isinstance(s, sp.Symbol)], key=lambda s: s.name)
    if len(vs) < 2:
        raise ErrorCalculo("Hacen falta al menos dos variables (por ejemplo x e y).")
    dep = dependiente or ("z" if any(s.name == "z" for s in vs) else "y" if any(s.name == "y" for s in vs) else vs[-1])
    dep = next((s for s in vs if (s == dep or s.name == str(dep))), vs[-1])
    indep = [s for s in vs if s != dep]
    b = [H("La relación"), L(_l(rel.lhs) + "=" + _l(rel.rhs)),
         T(f"Se supone que **${_l(dep)}$ es una función de** " + ", ".join(f"${_l(s)}$" for s in indep) + f" definida por la ecuación. Se reescribe como $F={_l(Fx)}=0$."),
         IN("**Teorema de la función implícita:** si $F=0$ y $\\partial F/\\partial " + _l(dep) + "\\ne0$, la ecuación define a " + f"${_l(dep)}$ localmente como función de las demás, y sus derivadas son $-F_{{x_i}}/F_{{{_l(dep)}}}$.")]
    Fd = _S(sp.diff(Fx, dep))
    if Fd == 0:
        raise ErrorCalculo(f"∂F/∂{dep} = 0: la ecuación no define a {dep} como función de las otras variables.")
    datos = {"F": Fx, "dep": dep}
    primeras = {}
    for s in indep:
        Fs = _S(sp.diff(Fx, s))
        d1 = _S(-Fs / Fd)
        primeras[s] = d1
        b += [L(r"\frac{\partial " + _l(dep) + r"}{\partial " + _l(s) + r"}=-\frac{F_{" + _l(s) + r"}}{F_{" + _l(dep) + r"}}=-\frac{" + _l(Fs) + "}{" + _l(Fd) + "}=" + _l(d1))]
        datos[f"d{dep}_d{s}"] = d1
    if len(indep) == 1:
        s = indep[0]
        d1 = primeras[s]
        # segunda derivada:  y'' = ∂/∂x(y') + ∂/∂y(y')·y'
        d2 = _S(sp.diff(d1, s) + sp.diff(d1, dep) * d1)
        # con F=0 se puede simplificar sustituyendo (cuando hay relación polinómica)
        try:
            red = sp.simplify(d2)
            red2 = sp.simplify(sp.ratsimp(red))
            d2s = min([d2, red, red2], key=lambda e: sp.count_ops(e))
            # usar la propia ecuación F = 0 para simplificar: el numerador se reduce módulo F (como polinomio en la variable dependiente)
            num_, den_ = sp.fraction(sp.together(d2s))
            if sp.Poly(num_, dep).degree() >= sp.Poly(Fx, dep).degree() > 0:
                resto = sp.rem(sp.expand(num_), sp.expand(Fx), dep)
                cand = _S(resto / den_)
                if sp.count_ops(cand) <= sp.count_ops(d2s):
                    d2s = cand
        except Exception:  # noqa: BLE001
            d2s = d2
        b += [H("Segunda derivada"), L(r"\frac{d^{2}" + _l(dep) + "}{d" + _l(s) + r"^{2}}=\frac{\partial}{\partial " + _l(s) + r"}\!\left(" + _l(d1) + r"\right)+\frac{\partial}{\partial " + _l(dep) + r"}\!\left(" + _l(d1) + r"\right)\frac{d" + _l(dep) + "}{d" + _l(s) + "}=" + _l(d2s)),
              IN("Se deriva de nuevo la expresión de $dy/dx$ y se vuelve a sustituir $dy/dx$ cuando aparece $y$ (regla de la cadena).")]
        datos["segunda"] = d2s
    if punto:
        pt = {s: sp.sympify(v) for s, v in punto.items()}
        falta = [s for s in vs if s not in pt]
        if falta:
            b.append(AV("Para evaluar en un punto dame todas las variables: falta " + ", ".join(str(s) for s in falta) + "."))
        else:
            val0 = _S(Fx.subs(pt, simultaneous=True))
            b.append(H("En el punto " + _l(sp.Tuple(*[pt[s] for s in vs]))))
            if val0 != 0:
                b.append(AV(f"⚠️ El punto **no está en la curva/superficie**: $F={_l(val0)}\\ne0$."))
            elif Fd.subs(pt, simultaneous=True) == 0:
                b.append(AV(f"En ese punto $F_{{{_l(dep)}}}=0$: la tangente es **vertical** (o la ecuación no define a {_l(dep)} ahí)."))
            else:
                pend = {s: _S(primeras[s].subs(pt, simultaneous=True)) for s in indep}
                b.append(T(", ".join(f"$\\partial {_l(dep)}/\\partial {_l(s)}={_l(p_)}$" for s, p_ in pend.items()) + "."))
                if len(indep) == 1:
                    s = indep[0]
                    m = pend[s]
                    recta = sp.Eq(dep, _S(pt[dep] + m * (s - pt[s])))
                    b.append(L(r"\text{Recta tangente: }\ " + _l(recta)))
                    b.append(L(r"\text{Recta normal: }\ " + _l(sp.Eq(dep, _S(pt[dep] - (s - pt[s]) / m))) if m != 0 else r"\text{Recta normal: }\ " + _l(sp.Eq(s, pt[s]))))
                else:
                    plano = sp.Eq(dep, _S(pt[dep] + sum(pend[s] * (s - pt[s]) for s in indep)))
                    b.append(L(r"\text{Plano tangente: }\ " + _l(plano)))
    return res(b, **datos)


# ==============================================================================
# 5. REGLA DE LA CADENA
# ==============================================================================
@_op
def regla_cadena(f, vs, sustituciones, parametros):
    """
    f(x1, …, xk) con xi = gi(parámetros). Calcula ∂f/∂parámetro por la regla de la cadena y lo comprueba sustituyendo.
    `sustituciones`: lista de expresiones gi en el mismo orden que `vs`; `parametros`: lista de símbolos.
    """
    if len(sustituciones) != len(vs):
        raise ErrorCalculo("Hace falta una expresión por cada variable de f.")
    b = [H("La función compuesta"), L(r"f(" + ",".join(_l(v) for v in vs) + r")=" + _l(f)),
         L(r"\begin{cases}" + r"\\".join(_l(v) + "=" + _l(g) for v, g in zip(vs, sustituciones)) + r"\end{cases}")]
    fp = [_S(sp.diff(f, v)) for v in vs]
    b += [H("Derivadas parciales de f"), TAB(["derivada", "valor"], [[f"$\\dfrac{{\\partial f}}{{\\partial {_l(v)}}}$", f"${_l(d)}$"] for v, d in zip(vs, fp)])]
    sub = dict(zip(vs, sustituciones))
    datos = {}
    for p in parametros:
        dg = [_S(sp.diff(g, p)) for g in sustituciones]
        termino = [fp[i].subs(sub, simultaneous=True) * dg[i] for i in range(len(vs))]
        total = _S(sum(termino))
        directo = _S(sp.diff(f.subs(sub, simultaneous=True), p))
        d_o = "d" if len(parametros) == 1 else r"\partial "
        b += [H(f"Derivada respecto de {_l(p)}"),
              L(r"\frac{" + d_o + "f}{" + d_o + _l(p) + r"}=" + "+".join(r"\frac{\partial f}{\partial " + _l(v) + r"}\frac{" + d_o + _l(v) + "}{" + d_o + _l(p) + "}" for v in vs)),
              TAB(["término", "valor"], [[f"$\\dfrac{{\\partial f}}{{\\partial {_l(v)}}}\\dfrac{{\\partial {_l(v)}}}{{\\partial {_l(p)}}}$", f"${_l(_S(tm))}$"] for v, tm in zip(vs, termino)]),
              L(r"\frac{" + d_o + "f}{" + d_o + _l(p) + "}=" + _l(total))]
        ok = _S(total - directo) == 0
        b.append((IN)(("✅ " if ok else "⚠️ ") + f"Comprobación: sustituyendo primero y derivando directamente se obtiene ${_l(directo)}$" + (", igual." if ok else ", distinto (revisa).")))
        datos[f"d_{p}"] = total
    return res(b, **datos)
