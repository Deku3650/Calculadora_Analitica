"""
calculo_graficas.py
===================
Gráficas del módulo de Cálculo. Todas devuelven un `matplotlib.figure.Figure` (se muestran con
st.pyplot(fig)). Se construyen SIN pyplot, así no se acumulan figuras abiertas en memoria.

  fig_funcion_1d     curva con asíntotas, puntos notables, tangente y/o derivada
  fig_taylor         f junto a sus polinomios de Taylor
  fig_niveles        curvas de nivel (con campo de gradiente opcional)
  fig_cortes         cortes z = c de una función de 3 variables
  fig_superficie     z = f(x, y) en 3D (con plano tangente opcional)
  fig_region         región/curva definida por una relación o por el dominio
  fig_sumas_parciales / fig_sucesion
"""
from __future__ import annotations

import math

import numpy as np
import sympy as sp
from matplotlib.figure import Figure

AZUL = "#0284c7"
NARANJA = "#ea580c"
VERDE = "#16a34a"
ROJO = "#dc2626"
GRIS = "#6b7280"
MAX_PUNTOS = 400          # tope por eje en mallas 2D (evita gráficas que tardan o gastan memoria)


def _fig(w=7.2, h=4.4):
    f = Figure(figsize=(w, h), dpi=110, layout="constrained")
    f.patch.set_alpha(0.0)
    return f


def _estilo(ax):
    ax.grid(True, alpha=0.25)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.axhline(0, color=GRIS, lw=0.8, alpha=0.6)
    ax.axvline(0, color=GRIS, lw=0.8, alpha=0.6)


def _evaluar(expr, vars_, *arrays):
    """expr evaluada con NumPy sobre arreglos; complejos y valores inválidos -> nan."""
    try:
        f = sp.lambdify(vars_, expr, modules=["scipy", "numpy"])
    except Exception:  # noqa: BLE001
        f = sp.lambdify(vars_, expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        out = np.asarray(f(*arrays))
    if out.shape != arrays[0].shape:
        out = np.broadcast_to(out, arrays[0].shape).copy()
    if np.iscomplexobj(out):
        out = np.where(np.abs(out.imag) < 1e-9, out.real, np.nan)
    out = out.astype(float, copy=False)
    out[~np.isfinite(out)] = np.nan
    return out


def _f(v):
    try:
        return float(sp.N(v))
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------ una variable
def _vacio(ax, texto):
    ax.text(0.5, 0.5, texto, transform=ax.transAxes, ha="center", va="center", color=GRIS, fontsize=11, wrap=True)


def fig_funcion_1d(expr, x, ventana=(-6.0, 6.0), verticales=(), horizontales=(), oblicuas=(), puntos=(),
                   tangente=None, derivada=None, titulo=None, cortes=(), sombrear=None):
    """
    puntos = [(x, y, 'etiqueta', color)]; tangente/derivada = expresiones en x (opcionales);
    cortes = abscisas donde se debe levantar el lápiz (saltos de funciones por trozos);
    sombrear = (a, b) para sombrear el área entre la curva y el eje x (integral definida).
    """
    a, b = ventana
    xs = np.linspace(a, b, 2400)
    ys = _evaluar(expr, [x], xs)
    fig = _fig()
    ax = fig.add_subplot(111)
    _estilo(ax)
    for c in cortes:                       # levantar el lápiz en los saltos
        fc = _f(c)
        if fc is not None and a < fc < b:
            ys[min(int(np.searchsorted(xs, fc)), len(xs) - 1)] = np.nan
    finitos = ys[np.isfinite(ys)]
    if not finitos.size:
        _vacio(ax, "La función no está definida (no toma valores reales)\nen esta ventana de x.")
    if finitos.size:
        lo, hi = np.percentile(finitos, [3, 97])
        pad = (hi - lo) * 0.35 + 1e-9
        ylo, yhi = lo - pad, hi + pad
        if hi - lo < 1e-9:
            ylo, yhi = lo - 1, hi + 1
        # cortar el trazo en las asíntotas (saltos enormes)
        ys = ys.copy()
        salto = np.abs(np.diff(ys)) > (yhi - ylo) * 1.2
        ys[1:][salto] = np.nan
        ys[(ys < ylo - 5 * (yhi - ylo)) | (ys > yhi + 5 * (yhi - ylo))] = np.nan
        ax.set_ylim(ylo, yhi)
    ax.plot(xs, ys, color=AZUL, lw=2.2, label="f(x)")
    if sombrear is not None:
        sa, sb = _f(sombrear[0]), _f(sombrear[1])
        if sa is not None and sb is not None and sa < sb:
            m_ = (xs >= sa) & (xs <= sb)
            ax.fill_between(xs[m_], 0, np.where(np.isfinite(ys[m_]), ys[m_], 0), color=AZUL, alpha=0.2)
    for c in cortes:                       # círculos vacíos en los extremos de cada lado del salto
        fc = _f(c)
        if fc is not None and a < fc < b:
            for lado in (-1, 1):
                v = _evaluar(expr, [x], np.array([fc + lado * 1e-7 * max(1.0, abs(fc))]))[0]
                if np.isfinite(v):
                    ax.plot([fc], [v], "o", mfc="white", mec=AZUL, ms=6, zorder=6)
    if derivada is not None:
        d = _evaluar(derivada, [x], xs)
        ax.plot(xs, d, color=VERDE, lw=1.6, ls="--", label="f′(x)")
    if tangente is not None:
        t = _evaluar(tangente, [x], xs)
        ax.plot(xs, t, color=NARANJA, lw=1.6, label="tangente")
    for v in verticales:
        fv = _f(v)
        if fv is not None and a <= fv <= b:
            ax.axvline(fv, color=ROJO, ls=":", lw=1.4)
    for h in horizontales:
        fh = _f(h)
        if fh is not None:
            ax.axhline(fh, color=ROJO, ls=":", lw=1.4)
    for mm, bb in oblicuas:
        fm, fb = _f(mm), _f(bb)
        if fm is not None and fb is not None:
            ax.plot(xs, fm * xs + fb, color=ROJO, ls=":", lw=1.4)
    for px, py, et, col in puntos:
        fx, fy = _f(px), _f(py)
        if fx is not None and fy is not None and a <= fx <= b:
            ax.plot([fx], [fy], "o", color=col, ms=7, zorder=5)
            ax.annotate(et, (fx, fy), textcoords="offset points", xytext=(6, 8), fontsize=8, color=col)
    ax.set_xlim(a, b)
    ax.set_xlabel("x")
    if titulo:
        ax.set_title(titulo, fontsize=10)
    if derivada is not None or tangente is not None:
        ax.legend(fontsize=8, frameon=False)
    return fig


def fig_taylor(expr, x, centro, polinomios, ventana=None):
    """polinomios = [(orden, expresión)]. La ventana por defecto es centro ± 4."""
    c = _f(centro) or 0.0
    a, b = ventana if ventana else (c - 4, c + 4)
    xs = np.linspace(a, b, 1500)
    ys = _evaluar(expr, [x], xs)
    fig = _fig()
    ax = fig.add_subplot(111)
    _estilo(ax)
    ax.plot(xs, ys, color="black", lw=2.6, label="f(x)")
    cmap = [AZUL, VERDE, NARANJA, "#9333ea", "#0891b2", "#be185d"]
    for i, (k, P) in enumerate(polinomios):
        ax.plot(xs, _evaluar(P, [x], xs), color=cmap[i % len(cmap)], lw=1.6, label=f"orden {k}")
    ref = ys[np.isfinite(ys)]
    if ref.size:
        lo, hi = np.percentile(ref, [2, 98])
        pad = (hi - lo) * 0.6 + 1e-9
        ax.set_ylim(lo - pad, hi + pad)
    ax.plot([c], [_f(expr.subs(x, centro))] if _f(expr.subs(x, centro)) is not None else [], "o", color=ROJO, zorder=6)
    ax.set_xlim(a, b)
    ax.legend(fontsize=8, frameon=False, ncol=3)
    ax.set_title("Aproximación de Taylor", fontsize=10)
    return fig


# ------------------------------------------------------------------ dos o tres variables
def _malla(ventana, N):
    N = int(min(max(N, 20), MAX_PUNTOS))
    x0, x1, y0, y1 = ventana
    X, Y = np.meshgrid(np.linspace(x0, x1, N), np.linspace(y0, y1, N))
    return X, Y


def niveles_automaticos(expr, x, y, ventana, k=9):
    X, Y = _malla(ventana, 80)
    Z = _evaluar(expr, [x, y], X, Y)
    z = Z[np.isfinite(Z)]
    if not z.size:
        return []
    lo, hi = np.percentile(z, [2, 98])
    if hi - lo < 1e-12:
        return [float(lo)]
    return [float(v) for v in np.linspace(lo, hi, k)]


def fig_niveles(expr, x, y, ventana=(-3, 3, -3, 3), niveles=None, gradiente=False, punto=None, N=260,
                restriccion=None, candidatos=()):
    """restriccion = expresión g (se dibuja g = 0 en rojo); candidatos = [(px, py)] puntos a marcar."""
    X, Y = _malla(ventana, N)
    Z = _evaluar(expr, [x, y], X, Y)
    fig = _fig(6.4, 5.4)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="box")
    _estilo(ax)
    if np.isfinite(Z).any():
        lv = sorted(set(niveles)) if niveles else niveles_automaticos(expr, x, y, ventana)
        if lv and len(lv) >= 1:
            if len(lv) == 1:
                cs = ax.contour(X, Y, Z, levels=[lv[0]], colors=[AZUL], linewidths=2)
            else:
                cs = ax.contour(X, Y, Z, levels=lv, cmap="viridis", linewidths=1.6)
            ax.clabel(cs, inline=True, fontsize=7, fmt="%.3g")
        if gradiente:
            Xg, Yg = _malla(ventana, 14)
            gx = _evaluar(sp.diff(expr, x), [x, y], Xg, Yg)
            gy = _evaluar(sp.diff(expr, y), [x, y], Xg, Yg)
            nrm = np.hypot(gx, gy)
            nrm[nrm == 0] = np.nan
            ax.quiver(Xg, Yg, gx / nrm, gy / nrm, color=NARANJA, alpha=0.8, scale=28, width=0.004)
        if restriccion is not None:
            Gz = _evaluar(restriccion, [x, y], X, Y)
            if np.isfinite(Gz).any():
                ax.contour(X, Y, Gz, levels=[0], colors=[ROJO], linewidths=2.6)
        for cx, cy in candidatos:
            fx, fy = _f(cx), _f(cy)
            if fx is not None and fy is not None:
                ax.plot([fx], [fy], "*", color=NARANJA, ms=13, zorder=7, mec="black", mew=0.6)
        if punto is not None:
            px, py = _f(punto[0]), _f(punto[1])
            if px is not None and py is not None:
                ax.plot([px], [py], "o", color=ROJO, ms=7, zorder=6)
                if gradiente:
                    gx0 = _f(sp.diff(expr, x).subs({x: punto[0], y: punto[1]}))
                    gy0 = _f(sp.diff(expr, y).subs({x: punto[0], y: punto[1]}))
                    if gx0 is not None and gy0 is not None and (gx0 or gy0):
                        n_ = math.hypot(gx0, gy0)
                        esc = 0.12 * (ventana[1] - ventana[0])
                        ax.annotate("", xy=(px + esc * gx0 / n_, py + esc * gy0 / n_), xytext=(px, py),
                                    arrowprops=dict(arrowstyle="->", color=ROJO, lw=2))
    else:
        _vacio(ax, "La función no está definida (no toma valores reales)\nen esta ventana.")
    ax.set_xlim(ventana[0], ventana[1])
    ax.set_ylim(ventana[2], ventana[3])
    ax.set_xlabel(sp.latex(x).join(["$", "$"]))
    ax.set_ylabel(sp.latex(y).join(["$", "$"]))
    ax.set_title("Curvas de nivel" + (" y campo de gradiente (flechas naranja)" if gradiente else ""), fontsize=10)
    return fig


def fig_cortes(expr, vars3, nivel, valores_z, ventana=(-3, 3, -3, 3), N=200):
    """Cortes de la superficie de nivel f(x,y,z)=nivel con z = cada valor de valores_z."""
    x, y, z = vars3
    k = len(valores_z)
    fig = _fig(3.2 * min(k, 3), 3.4 * math.ceil(k / 3))
    X, Y = _malla(ventana, N)
    for i, z0 in enumerate(valores_z):
        ax = fig.add_subplot(math.ceil(k / 3), min(k, 3), i + 1)
        ax.set_aspect("equal", adjustable="box")
        _estilo(ax)
        Z = _evaluar(expr.subs(z, z0), [x, y], X, Y)
        if np.isfinite(Z).any() and np.nanmin(Z) <= nivel <= np.nanmax(Z):
            ax.contour(X, Y, Z, levels=[nivel], colors=[AZUL], linewidths=2)
        else:
            ax.text(0.5, 0.5, "vacío", transform=ax.transAxes, ha="center", color=GRIS)
        ax.set_title(f"z = {z0:.3g}", fontsize=9)
        ax.set_xlim(ventana[0], ventana[1])
        ax.set_ylim(ventana[2], ventana[3])
    return fig


def fig_superficie(expr, x, y, ventana=(-3, 3, -3, 3), plano=None, punto=None, N=70):
    X, Y = _malla(ventana, min(N, 110))
    Z = _evaluar(expr, [x, y], X, Y)
    fig = _fig(6.6, 5.4)
    ax = fig.add_subplot(111, projection="3d")
    if np.isfinite(Z).any():
        zl, zh = np.nanpercentile(Z, [1, 99])
        Zc = np.where((Z >= zl - 2 * (zh - zl)) & (Z <= zh + 2 * (zh - zl)), Z, np.nan)
        ax.plot_surface(X, Y, Zc, cmap="viridis", alpha=0.88, linewidth=0, antialiased=True)
        if plano is not None:
            P = _evaluar(plano, [x, y], X, Y)
            P = np.where((P >= zl - (zh - zl)) & (P <= zh + (zh - zl)), P, np.nan)
            ax.plot_surface(X, Y, P, color=NARANJA, alpha=0.35, linewidth=0)
        if punto is not None:
            px, py = _f(punto[0]), _f(punto[1])
            pz = _f(expr.subs({x: punto[0], y: punto[1]}))
            if None not in (px, py, pz):
                ax.scatter([px], [py], [pz], color=ROJO, s=40, zorder=10)
        ax.set_zlim(zl - 0.1 * (zh - zl), zh + 0.1 * (zh - zl))
    else:
        ax.text2D(0.5, 0.5, "La función no está definida en esta ventana.", transform=ax.transAxes, ha="center", color=GRIS)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_title("z = f(x, y)" + (" y plano tangente (naranja)" if plano is not None else ""), fontsize=10)
    return fig


def fig_region(rel, x, y, ventana=(-3, 3, -3, 3), N=320, titulo=None):
    """Relación (Eq, <, ≤, >, ≥, And…) en dos variables: curva o región."""
    X, Y = _malla(ventana, N)
    fig = _fig(6.4, 5.4)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="box")
    _estilo(ax)
    partes = list(rel.args) if isinstance(rel, sp.And) else [rel]
    mascara = np.ones_like(X, dtype=bool)
    for r in partes:
        if isinstance(r, sp.Eq):
            g = _evaluar(r.lhs - r.rhs, [x, y], X, Y)
            if np.isfinite(g).any():
                ax.contour(X, Y, g, levels=[0], colors=[AZUL], linewidths=2.2)
            continue
        if isinstance(r, (sp.Lt, sp.Le, sp.Gt, sp.Ge, sp.Ne)):
            g = _evaluar(r.lhs - r.rhs, [x, y], X, Y)
            ok = {sp.Lt: g < 0, sp.Le: g <= 0, sp.Gt: g > 0, sp.Ge: g >= 0, sp.Ne: g != 0}[type(r)]
            mascara &= np.where(np.isfinite(g), ok, False)
            if np.isfinite(g).any():
                ax.contour(X, Y, g, levels=[0], colors=[AZUL], linewidths=1.8,
                           linestyles="-" if isinstance(r, (sp.Le, sp.Ge)) else "--")
    if not all(isinstance(r, sp.Eq) for r in partes):
        ax.contourf(X, Y, mascara.astype(float), levels=[0.5, 1.5], colors=[AZUL], alpha=0.25)
    ax.set_xlim(ventana[0], ventana[1])
    ax.set_ylim(ventana[2], ventana[3])
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if titulo:
        ax.set_title(titulo, fontsize=10)
    return fig


# ------------------------------------------------------------------ sucesiones y series
def fig_sumas_parciales(sumas, suma=None, titulo="Sumas parciales $S_N$"):
    """sumas = [(N, S_N)] (ya calculadas); si hay suma exacta, se dibuja la asíntota."""
    fig = _fig(6.6, 3.8)
    ax = fig.add_subplot(111)
    _estilo(ax)
    Ns = [n for n, s in sumas if isinstance(s, float)]
    Ss = [s for n, s in sumas if isinstance(s, float)]
    ax.plot(Ns, Ss, "o-", color=AZUL, lw=2)
    if suma is not None and _f(suma) is not None:
        ax.axhline(_f(suma), color=ROJO, ls="--", lw=1.4, label=f"suma = {_f(suma):.6g}")
        ax.legend(fontsize=8, frameon=False)
    ax.set_xscale("log")
    if Ss:
        ref = Ss + ([_f(suma)] if suma is not None and _f(suma) is not None else [])
        lo, hi = min(ref), max(ref)
        pad = (hi - lo) * 0.25 + 1e-9
        ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("N (número de términos)")
    ax.set_title(titulo, fontsize=10)
    return fig


def fig_sucesion(valores, n0=1, limite=None):
    """valores = lista de a_n (floats o None) desde n0."""
    fig = _fig(6.6, 3.8)
    ax = fig.add_subplot(111)
    _estilo(ax)
    ns = [n0 + i for i, v in enumerate(valores) if v is not None]
    vs = [v for v in valores if v is not None]
    ax.plot(ns, vs, "o", color=AZUL, ms=4)
    if limite is not None and _f(limite) is not None:
        ax.axhline(_f(limite), color=ROJO, ls="--", lw=1.4, label=f"límite = {_f(limite):.6g}")
        ax.legend(fontsize=8, frameon=False)
    if vs:
        lo, hi = np.percentile(vs, [2, 98])
        pad = (hi - lo) * 0.3 + 1e-9
        ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("n")
    ax.set_title("Términos $a_n$", fontsize=10)
    return fig
