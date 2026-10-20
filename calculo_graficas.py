# calculo_graficas.py
"""
calculo_graficas.py  (v2 · didáctica)
=====================================
Gráficas del módulo de Cálculo. Todas devuelven un `matplotlib.figure.Figure` (se muestran con
st.pyplot(fig)). Se construyen SIN pyplot, así no se acumulan figuras abiertas en memoria.

Estilo de libro de texto, legible en tema claro y oscuro:
  · fondo OPACO (antes era transparente: en tema oscuro los números de los ejes desaparecían),
  · ejes cartesianos con flecha y nombre, números en los ejes (π, π/2… para funciones trigonométricas),
  · cuadrícula principal y secundaria,
  · cada punto notable lleva su nombre y sus coordenadas,
  · leyenda con la fórmula, las asíntotas, la tangente…

  fig_funcion_1d     curva con asíntotas, puntos con coordenadas, tangente/derivada, guías (a, L), área
  fig_taylor         f junto a sus polinomios de Taylor
  fig_niveles        curvas de nivel (con barra de color, gradiente y restricción)
  fig_cortes         cortes z = c de una función de 3 variables
  fig_superficie     z = f(x, y) en 3D (con plano tangente opcional)
  fig_region         región/curva definida por una relación o por el dominio
  fig_sumas_parciales / fig_sucesion      (con banda ε y N₀)
  fig_recta_numerica conjuntos de ℝ: intervalos con extremos abiertos/cerrados
  fig_puntos_vectores puntos y vectores en ℝ² / ℝ³
  fig_bola_2d / fig_bola_3d   bolas abiertas y cerradas con puntos clasificados
  fig_lista          lista de datos con media y mediana
"""
from __future__ import annotations

import math

import numpy as np
import sympy as sp
from matplotlib import mathtext
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, MultipleLocator

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
MORADO = "#7c3aed"
GRIS = "#475569"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"
MAX_PUNTOS = 400          # tope por eje en mallas 2D (evita gráficas que tardan o gastan memoria)


# ==============================================================================
# Utilidades de formato
# ==============================================================================
def _f(v):
    try:
        r = float(sp.N(v))
        return r if math.isfinite(r) else None
    except Exception:  # noqa: BLE001
        return None


def _num(v, cifras=4) -> str:
    """Número legible: sin ceros sobrantes y con el signo menos tipográfico."""
    f = _f(v)
    if f is None:
        return str(v)
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f))).replace("-", "−")
    return f"{f:.{cifras}g}".replace("-", "−")


def _fmt_pi(v) -> str:
    """Etiquetas en múltiplos de π/2 para los ejes de funciones trigonométricas."""
    if abs(v) < 1e-9:
        return "0"
    k = v / (math.pi / 2)
    if abs(k - round(k)) > 1e-6:
        return _num(v)
    k = int(round(k))
    s = "-" if k < 0 else ""
    k = abs(k)
    if k % 2 == 0:
        m = k // 2
        return "$" + s + r"\pi$" if m == 1 else "$" + s + str(m) + r"\pi$"
    return "$" + s + r"\frac{\pi}{2}$" if k == 1 else "$" + s + r"\frac{" + str(k) + r"\pi}{2}$"


_PARSER_MT = None


def _mt(expr, max_len=90):
    """LaTeX de `expr` apto para mathtext de matplotlib (o None si no se puede)."""
    global _PARSER_MT
    try:
        s = sp.latex(expr)
    except Exception:  # noqa: BLE001
        return None
    for a, b in ((r"\left(", "("), (r"\right)", ")"), (r"\left[", "["), (r"\right]", "]"), (r"\left|", "|"),
                 (r"\right|", "|"), (r"\left\{", r"\{"), (r"\right\}", r"\}"), (r"\left.", ""), (r"\right.", ""),
                 (r"\operatorname", r"\mathrm"), (r"\tfrac", r"\frac"), (r"\dfrac", r"\frac"), (r"\mathrm{d}", "d")):
        s = s.replace(a, b)
    if len(s) > max_len or "begin{" in s or r"\text" in s:
        return None
    formula_mt = "$" + s + "$"
    try:
        if _PARSER_MT is None:
            _PARSER_MT = mathtext.MathTextParser("path")
        _PARSER_MT.parse(formula_mt, dpi=72, prop=FontProperties())
    except Exception:  # noqa: BLE001
        return None
    return formula_mt


def _usa_trig(expr) -> bool:
    try:
        return bool(expr.has(sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc))
    except Exception:  # noqa: BLE001
        return False


def _puntos_1d(expr, cortes=()) -> int:
    """Muestreo adaptativo: 800 puntos en curvas suaves; 3000 si hay asíntotas, saltos o trigonométricas."""
    if cortes:
        return 3000
    try:
        if expr.has(sp.Piecewise, sp.floor, sp.ceiling, sp.sign, sp.Abs, sp.tan, sp.cot, sp.sec, sp.csc, sp.sin, sp.cos, sp.factorial):
            return 3000
        for nodo in sp.preorder_traversal(expr):
            if isinstance(nodo, sp.Pow) and nodo.exp.is_Number and nodo.exp < 0:
                return 3000
    except Exception:  # noqa: BLE001
        return 2400
    return 800


def _cortar_saltos(arr, ylo, yhi):
    """Corta trazos verticales falsos en asíntotas o saltos bruscos."""
    out = arr.copy()
    rango = max(yhi - ylo, 1e-9)
    salto = np.abs(np.diff(out)) > rango * 1.2
    out[1:][salto] = np.nan
    out[(out < ylo - 5 * rango) | (out > yhi + 5 * rango)] = np.nan
    return out


def _fig(w=7.4, h=4.6):
    f = Figure(figsize=(w, h), dpi=110, layout="constrained", facecolor=FONDO, edgecolor=CLARO)
    return f


def _evaluar(expr, vars_, *arrays):
    """expr evaluada con NumPy sobre arreglos; complejos y valores inválidos -> nan."""
    if expr.has(sp.factorial):               # SciPy da 0 para x! con x real negativo; con gamma sí sale bien
        expr = expr.rewrite(sp.gamma)
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


# ==============================================================================
# Ejes y anotaciones
# ==============================================================================
def _ejes(ax, vx, vy, xl="x", yl="y", pi_x=False, flechas=True, logx=False):
    """Ejes cartesianos de libro de texto: cruzan en el origen si está a la vista, con flecha, nombre y números."""
    x0, x1 = vx
    y0, y1 = vy
    if logx:
        ax.set_xscale("log")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_facecolor("#fbfdff")
    ax.minorticks_on()
    if not logx:
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color=CLARO, lw=0.9, alpha=0.9)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    origen_x, origen_y = x0 < 0 < x1, y0 < 0 < y1
    if origen_x:
        ax.spines["left"].set_position("zero")
    if origen_y:
        ax.spines["bottom"].set_position("zero")
    for s in ("left", "bottom"):
        ax.spines[s].set_color(OSCURO)
        ax.spines[s].set_linewidth(1.6)
    ax.tick_params(which="major", labelsize=9, colors=OSCURO, length=5, width=1.2)
    ax.tick_params(which="minor", length=2.5, colors="#94a3b8")
    if pi_x:
        ax.xaxis.set_major_locator(MultipleLocator(math.pi / 2 if (x1 - x0) <= 4 * math.pi else math.pi))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _fmt_pi(v)))
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    ocultar_cero_y = origen_x and origen_y
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "" if (ocultar_cero_y and abs(v) < 1e-12) else _num(v)))
    if flechas:
        yb, xb = (0 if origen_y else y0), (0 if origen_x else x0)
        ax.plot([1], [yb], ">", color=OSCURO, ms=8, transform=ax.get_yaxis_transform(), clip_on=False, zorder=10)
        ax.plot([xb], [1], "^", color=OSCURO, ms=8, transform=ax.get_xaxis_transform(), clip_on=False, zorder=10)
        ax.annotate(xl, xy=(1, yb), xycoords=ax.get_yaxis_transform(), xytext=(-6, 9), textcoords="offset points",
                    ha="right", fontsize=11.5, fontweight="bold", color=OSCURO, annotation_clip=False, zorder=20,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
        ax.annotate(yl, xy=(xb, 1), xycoords=ax.get_xaxis_transform(), xytext=(10, -4), textcoords="offset points",
                    ha="left", va="top", fontsize=11.5, fontweight="bold", color=OSCURO, annotation_clip=False, zorder=20,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))


_OFFS = [(14, 18), (14, -34), (-70, 18), (-70, -34), (30, 42), (30, -56), (-90, 44), (-90, -58)]


def _anotar(ax, px, py, texto, color=ROJO, k=0, coord=True, marcador="o"):
    """Punto notable con su nombre y sus coordenadas en una etiqueta."""
    ax.plot([px], [py], marcador, color=color, mec="white", mew=1.4, ms=8.5, zorder=6)
    et = f"{texto}\n({_num(px)}, {_num(py)})" if (coord and texto) else (f"({_num(px)}, {_num(py)})" if coord else texto)
    dx, dy = _OFFS[k % len(_OFFS)]
    ax.annotate(et, (px, py), xytext=(dx, dy), textcoords="offset points", fontsize=8.5, color=OSCURO, zorder=8,
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=color, lw=1.1, alpha=0.96),
                arrowprops=dict(arrowstyle="-", color=color, lw=1.0, shrinkA=0, shrinkB=3))


def _leyenda(ax, **kw):
    h, l = ax.get_legend_handles_labels()
    if h:
        ax.legend(fontsize=8.5, frameon=True, framealpha=0.92, edgecolor=CLARO, facecolor="white", **kw)


def _vacio(ax, texto):
    ax.text(0.5, 0.5, texto, transform=ax.transAxes, ha="center", va="center", color=GRIS, fontsize=11,
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=CLARO))


def _titulo(ax, partes):
    ax.set_title(partes, fontsize=11, color=OSCURO, pad=10, loc="left", fontweight="bold")


# ==============================================================================
# 1 · Una variable
# ==============================================================================
def fig_funcion_1d(expr, x, ventana=(-6.0, 6.0), verticales=(), horizontales=(), oblicuas=(), puntos=(),
                   tangente=None, derivada=None, titulo=None, cortes=(), sombrear=None, guias=(),
                   etiqueta_y=None, area_texto=None, nombre="f"):
    """
    puntos   = [(x, y, 'etiqueta', color)]   (se rotulan con su nombre y coordenadas)
    cortes   = abscisas donde se levanta el lápiz (saltos de funciones por trozos)
    sombrear = (a, b) para sombrear el área entre la curva y el eje x; area_texto = rótulo del área
    guias    = [(a, L)] guías punteadas hacia los ejes con «a» y «L» (dibujo del límite)
    """
    a, b = ventana
    n_pts = _puntos_1d(expr, cortes)
    xs = np.linspace(a, b, n_pts)
    ys = _evaluar(expr, [x], xs)
    for c in cortes:                       # levantar el lápiz en los saltos
        fc = _f(c)
        if fc is not None and a < fc < b:
            ys[min(int(np.searchsorted(xs, fc)), len(xs) - 1)] = np.nan
    finitos = ys[np.isfinite(ys)]
    ylo, yhi = -1.0, 1.0
    if finitos.size:
        lo, hi = np.percentile(finitos, [3, 97])
        pad = (hi - lo) * 0.35 + 1e-9
        ylo, yhi = lo - pad, hi + pad
        if hi - lo < 1e-9:
            ylo, yhi = lo - 1, hi + 1
        ys = _cortar_saltos(ys, ylo, yhi)
    for _, py, _, _ in puntos:             # que los puntos notables queden dentro de la ventana vertical
        fy = _f(py)
        if fy is not None and not (ylo <= fy <= yhi):
            ylo, yhi = min(ylo, fy - 0.15 * (yhi - ylo)), max(yhi, fy + 0.15 * (yhi - ylo))

    fig = _fig()
    ax = fig.add_subplot(111)
    _ejes(ax, (a, b), (ylo, yhi), xl=str(x), yl=etiqueta_y or f"y = {nombre}({x})", pi_x=_usa_trig(expr) and (b - a) >= 3)
    if not finitos.size:
        _vacio(ax, "La función no está definida (no toma valores reales)\nen esta ventana de x.")

    if sombrear is not None:
        sa, sb = _f(sombrear[0]), _f(sombrear[1])
        if sa is not None and sb is not None and sa < sb:
            m_ = (xs >= sa) & (xs <= sb)
            yy = np.where(np.isfinite(ys[m_]), ys[m_], 0)
            ax.fill_between(xs[m_], 0, yy, color=AZUL, alpha=0.22, label="área bajo la curva", zorder=1)
            ax.plot([sa, sa], [0, np.nan_to_num(yy[0])], color=AZUL, lw=1, ls=":")
            ax.plot([sb, sb], [0, np.nan_to_num(yy[-1])], color=AZUL, lw=1, ls=":")
            if area_texto:
                ax.text((sa + sb) / 2, np.nanmax(yy) * 0.3 if np.isfinite(np.nanmax(yy)) else 0, area_texto, ha="center",
                        fontsize=10, fontweight="bold", color=AZUL, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=AZUL))
    mt = _mt(expr)
    et = f"{nombre}({x}) = {mt}" if mt else f"{nombre}({x})"
    ax.plot(xs, ys, color=AZUL, lw=2.4, label=et, zorder=4)
    for c in cortes:                       # círculos vacíos en los dos lados del salto
        fc = _f(c)
        if fc is not None and a < fc < b:
            for lado in (-1, 1):
                v = _evaluar(expr, [x], np.array([fc + lado * 1e-7 * max(1.0, abs(fc))]))[0]
                if np.isfinite(v):
                    ax.plot([fc], [v], "o", mfc="white", mec=AZUL, ms=7, mew=1.6, zorder=6)
            ax.axvline(fc, color=GRIS, ls=":", lw=1)
    if derivada is not None:
        d_ys = _cortar_saltos(_evaluar(derivada, [x], xs), ylo, yhi)
        ax.plot(xs, d_ys, color=VERDE, lw=1.8, ls="--", label=f"{nombre}′({x})  (derivada)", zorder=3)
    if tangente is not None:
        mtt = _mt(tangente)
        ax.plot(xs, _evaluar(tangente, [x], xs), color=NARANJA, lw=1.8,
                label=f"recta tangente  y = {mtt[1:-1] if mtt else ''}" if mtt else "recta tangente", zorder=3)
        if mtt:
            ax.lines[-1].set_label("recta tangente:  " + mtt.replace("$", "$y = ", 1))
    for i, v in enumerate(verticales):
        fv = _f(v)
        if fv is not None and a <= fv <= b:
            ax.axvline(fv, color=ROJO, ls="--", lw=1.5, label=f"asíntota vertical  x = {_num(fv)}" if i < 3 else None, zorder=2)
    for i, h in enumerate(horizontales):
        fh = _f(h)
        if fh is not None:
            ax.axhline(fh, color=ROJO, ls="--", lw=1.5, label=f"asíntota horizontal  y = {_num(fh)}" if i < 2 else None, zorder=2)
    vistas = set()
    for mm, bb in oblicuas:
        fm, fb = _f(mm), _f(bb)
        if fm is not None and fb is not None and (round(fm, 9), round(fb, 9)) not in vistas:
            vistas.add((round(fm, 9), round(fb, 9)))
            ax.plot(xs, fm * xs + fb, color=ROJO, ls="--", lw=1.5,
                    label=f"asíntota oblicua  y = {_num(fm)}x {'+' if fb >= 0 else '−'} {_num(abs(fb))}", zorder=2)
    for g_a, g_L in guias:                 # dibujo didáctico del límite
        ga, gl = _f(g_a), _f(g_L)
        if ga is None or gl is None:
            continue
        xl = max(a, min(0, ga)) if a < 0 < b else a
        ax.plot([ga, ga], [min(0, gl) if ylo < 0 < yhi else ylo, gl], color=ROJO, ls=":", lw=1.4, zorder=3)
        ax.plot([xl, ga], [gl, gl], color=ROJO, ls=":", lw=1.4, zorder=3)
        ax.plot([ga], [gl], "o", mfc="white", mec=ROJO, ms=9, mew=2, zorder=7)
        ax.annotate(f"a = {_num(ga)}", (ga, 0 if ylo < 0 < yhi else ylo), xytext=(0, -26), textcoords="offset points", ha="center",
                    fontsize=9, fontweight="bold", color=ROJO, annotation_clip=False,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ROJO))
        ax.annotate(f"L = {_num(gl)}", (0 if a < 0 < b else a, gl), xytext=(-12, 0), textcoords="offset points", ha="right", va="center",
                    fontsize=9, fontweight="bold", color=ROJO, annotation_clip=False,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ROJO))
    for k, (px, py, et_, col) in enumerate(puntos):
        fx, fy = _f(px), _f(py)
        if fx is not None and fy is not None and a <= fx <= b:
            _anotar(ax, fx, fy, et_, col, k)
    if titulo:
        _titulo(ax, titulo)
    _leyenda(ax, loc="best")
    return fig


def fig_taylor(expr, x, centro, polinomios, ventana=None):
    """polinomios = [(orden, expresión)]. La ventana por defecto es centro ± 4."""
    c_val = _f(centro)
    c = c_val if c_val is not None else 0.0
    a, b = ventana if ventana else (c - 4, c + 4)
    xs = np.linspace(a, b, 1500)
    ys = _evaluar(expr, [x], xs)
    ref = ys[np.isfinite(ys)]
    ylo, yhi = (-1.0, 1.0)
    if ref.size:
        lo, hi = np.percentile(ref, [2, 98])
        pad = (hi - lo) * 0.6 + 1e-9
        ylo, yhi = lo - pad, hi + pad
        ys = _cortar_saltos(ys, ylo, yhi)
    fig = _fig()
    ax = fig.add_subplot(111)
    _ejes(ax, (a, b), (ylo, yhi), xl=str(x), yl="y", pi_x=_usa_trig(expr) and (b - a) >= 3)
    mt = _mt(expr)
    ax.plot(xs, ys, color="black", lw=3, label=f"f({x}) = {mt}" if mt else f"f({x})  (la función real)", zorder=3)
    cmap = [AZUL, VERDE, NARANJA, MORADO, "#0891b2", "#be185d"]
    for i, (k, P) in enumerate(polinomios):
        ax.plot(xs, _evaluar(P, [x], xs), color=cmap[i % len(cmap)], lw=1.9, label=f"polinomio de orden {k}", zorder=4)
    fc = _f(expr.subs(x, centro))
    if fc is not None:
        _anotar(ax, c, fc, f"centro  {x} = {_num(c)}", ROJO, 0)
    ax.axvline(c, color=ROJO, ls=":", lw=1)
    _titulo(ax, "Aproximación de Taylor: cerca del centro los polinomios se pegan a f")
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=3, fontsize=8.5, frameon=True, framealpha=0.95, edgecolor=CLARO)
    return fig


# ==============================================================================
# 2 · Dos y tres variables
# ==============================================================================
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
    from matplotlib.ticker import MaxNLocator
    redondos = [float(v) for v in MaxNLocator(nbins=k, steps=[1, 2, 2.5, 5, 10]).tick_values(lo, hi) if lo <= v <= hi]
    return redondos if len(redondos) >= 2 else [float(v) for v in np.linspace(lo, hi, k)]


def fig_niveles(expr, x, y, ventana=(-3, 3, -3, 3), niveles=None, gradiente=False, punto=None, N=260,
                restriccion=None, candidatos=()):
    """restriccion = expresión g (se dibuja g = 0 en rojo); candidatos = [(px, py)] puntos a marcar."""
    X, Y = _malla(ventana, N)
    Z = _evaluar(expr, [x, y], X, Y)
    fig = _fig(7.0, 5.6)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="box")
    _ejes(ax, (ventana[0], ventana[1]), (ventana[2], ventana[3]), xl=str(x), yl=str(y))
    mt = _mt(expr)
    if np.isfinite(Z).any():
        lv = sorted(set(niveles)) if niveles else niveles_automaticos(expr, x, y, ventana)
        if lv:
            if len(lv) == 1:
                ax.contour(X, Y, Z, levels=[lv[0]], colors=[AZUL], linewidths=2.4)
                ax.plot([], [], color=AZUL, lw=2.4, label=f"nivel  f = {_num(lv[0])}")
            else:
                cs = ax.contour(X, Y, Z, levels=lv, cmap="viridis", linewidths=1.8)
                ax.clabel(cs, inline=True, fontsize=8, fmt=lambda v: _num(v))
                sm = ScalarMappable(norm=cs.norm, cmap=cs.cmap)
                cb = fig.colorbar(sm, ax=ax, shrink=0.78, pad=0.02)
                cb.set_label("valor de f  (cada curva es un nivel c)", fontsize=9)
                cb.ax.tick_params(labelsize=8)
        if gradiente:
            Xg, Yg = _malla(ventana, 12)
            gx = _evaluar(sp.diff(expr, x), [x, y], Xg, Yg)
            gy = _evaluar(sp.diff(expr, y), [x, y], Xg, Yg)
            nrm = np.hypot(gx, gy)
            nrm[nrm == 0] = np.nan
            ax.quiver(Xg, Yg, gx / nrm, gy / nrm, color=NARANJA, alpha=0.85, scale=28, width=0.0045, zorder=5)
            ax.plot([], [], color=NARANJA, marker=r"$\rightarrow$", ls="", ms=11, label="∇f: dirección de máximo crecimiento")
        if restriccion is not None:
            Gz = _evaluar(restriccion, [x, y], X, Y)
            if np.isfinite(Gz).any():
                ax.contour(X, Y, Gz, levels=[0], colors=[ROJO], linewidths=2.8)
                ax.plot([], [], color=ROJO, lw=2.8, label="restricción  g = 0")
        for i, (cx, cy) in enumerate(candidatos):
            fx, fy = _f(cx), _f(cy)
            if fx is not None and fy is not None:
                ax.plot([fx], [fy], "*", color=NARANJA, ms=15, zorder=7, mec="black", mew=0.7)
                ax.annotate(f"({_num(fx)}, {_num(fy)})", (fx, fy), xytext=(8, 8), textcoords="offset points", fontsize=8,
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=NARANJA))
        if candidatos:
            ax.plot([], [], "*", color=NARANJA, mec="black", ms=12, ls="", label="puntos candidatos / críticos")
        if punto is not None:
            px, py = _f(punto[0]), _f(punto[1])
            if px is not None and py is not None:
                txt = "punto p"
                gx0 = _f(sp.diff(expr, x).subs({x: punto[0], y: punto[1]}))
                gy0 = _f(sp.diff(expr, y).subs({x: punto[0], y: punto[1]}))
                if gradiente and gx0 is not None and gy0 is not None:
                    txt += f"\n∇f(p) = ({_num(gx0)}, {_num(gy0)})"
                    if gx0 or gy0:
                        n_ = math.hypot(gx0, gy0)
                        esc = 0.14 * (ventana[1] - ventana[0])
                        ax.annotate("", xy=(px + esc * gx0 / n_, py + esc * gy0 / n_), xytext=(px, py),
                                    arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=2.4), zorder=8)
                _anotar(ax, px, py, txt, ROJO, 1, coord=True)
    else:
        _vacio(ax, "La función no está definida (no toma valores reales)\nen esta ventana.")
    _titulo(ax, f"Curvas de nivel de  f({x}, {y})" + (f" = {mt}" if mt else ""))
    _leyenda(ax, loc="lower right")
    return fig


def fig_cortes(expr, vars3, nivel, valores_z, ventana=(-3, 3, -3, 3), N=200):
    """Cortes de la superficie de nivel f(x,y,z)=nivel con z = cada valor de valores_z."""
    x, y, z = vars3
    k = len(valores_z)
    cols = min(k, 3)
    fig = _fig(3.9 * cols, 4.1 * math.ceil(k / 3))
    X, Y = _malla(ventana, N)
    for i, z0 in enumerate(valores_z):
        ax = fig.add_subplot(math.ceil(k / 3), cols, i + 1)
        ax.set_aspect("equal", adjustable="box")
        _ejes(ax, (ventana[0], ventana[1]), (ventana[2], ventana[3]), xl=str(x), yl=str(y))
        ax.tick_params(labelsize=7)
        Zc = _evaluar(expr.subs(z, z0), [x, y], X, Y)
        if np.isfinite(Zc).any() and np.nanmin(Zc) <= nivel <= np.nanmax(Zc):
            ax.contour(X, Y, Zc, levels=[nivel], colors=[AZUL], linewidths=2.2)
        else:
            _vacio(ax, "corte vacío")
        ax.set_title(f"corte  {z} = {_num(z0)}", fontsize=9.5, color=OSCURO, fontweight="bold")
    fig.suptitle(f"Cortes de la superficie  f({x}, {y}, {z}) = {_num(nivel)}", fontsize=11, color=OSCURO, fontweight="bold")
    return fig


def _ejes3d(ax, ventana=None, zlabel="z"):
    ax.set_xlabel("x", fontsize=11.5, fontweight="bold", labelpad=6)
    ax.set_ylabel("y", fontsize=11.5, fontweight="bold", labelpad=6)
    ax.set_zlabel(zlabel, fontsize=11.5, fontweight="bold", labelpad=4)
    ax.tick_params(labelsize=8, colors=OSCURO)
    ax.view_init(elev=24, azim=-58)


def fig_superficie(expr, x, y, ventana=(-3, 3, -3, 3), plano=None, punto=None, N=70):
    X, Y = _malla(ventana, min(N, 110))
    Z = _evaluar(expr, [x, y], X, Y)
    fig = _fig(7.2, 5.8)
    ax = fig.add_subplot(111, projection="3d")
    _ejes3d(ax, zlabel=f"z = f({x}, {y})")
    ax.set_xlabel(str(x), fontsize=11.5, fontweight="bold", labelpad=6)
    ax.set_ylabel(str(y), fontsize=11.5, fontweight="bold", labelpad=6)
    if np.isfinite(Z).any():
        zl, zh = np.nanpercentile(Z, [1, 99])
        Zc = np.where((Z >= zl - 2 * (zh - zl)) & (Z <= zh + 2 * (zh - zl)), Z, np.nan)
        surf = ax.plot_surface(X, Y, Zc, cmap="viridis", alpha=0.9, linewidth=0, antialiased=True)
        cb = fig.colorbar(surf, ax=ax, shrink=0.6, pad=0.1)
        cb.set_label("altura  z = f", fontsize=9)
        cb.ax.tick_params(labelsize=8)
        if plano is not None:
            P = _evaluar(plano, [x, y], X, Y)
            P = np.where((P >= zl - (zh - zl)) & (P <= zh + (zh - zl)), P, np.nan)
            ax.plot_surface(X, Y, P, color=NARANJA, alpha=0.38, linewidth=0)
        if punto is not None:
            px, py = _f(punto[0]), _f(punto[1])
            pz = _f(expr.subs({x: punto[0], y: punto[1]}))
            if None not in (px, py, pz):
                ax.scatter([px], [py], [pz], color=ROJO, s=55, zorder=10, depthshade=False)
                ax.text(px, py, pz + 0.08 * (zh - zl), f"({_num(px)}, {_num(py)}, {_num(pz)})", fontsize=8.5,
                        color=OSCURO, ha="center", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ROJO))
        ax.set_zlim(zl - 0.1 * (zh - zl), zh + 0.1 * (zh - zl))
    else:
        ax.text2D(0.5, 0.5, "La función no está definida en esta ventana.", transform=ax.transAxes, ha="center", color=GRIS)
    if plano is not None:
        ax.plot([], [], color=NARANJA, lw=6, alpha=0.5, label="plano tangente / aproximación")
        _leyenda(ax, loc="upper left")
    mt = _mt(expr)
    _titulo(ax, f"Superficie  z = f({x}, {y})" + (f" = {mt}" if mt else ""))
    return fig


def fig_region(rel, x, y, ventana=(-3, 3, -3, 3), N=320, titulo=None, puntos=()):
    """
    Relación (Eq, <, ≤, >, ≥, And…) en dos variables: curva o región.
    puntos = [(px, py, 'etiqueta', color)] para marcar puntos de prueba con sus coordenadas.
    """
    X, Y = _malla(ventana, N)
    fig = _fig(7.0, 5.6)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="box")
    _ejes(ax, (ventana[0], ventana[1]), (ventana[2], ventana[3]), xl=str(x), yl=str(y))
    partes = list(rel.args) if isinstance(rel, sp.And) else [rel]
    mascara = np.ones_like(X, dtype=bool)
    hay_region, hay_curva = False, False
    for r in partes:
        if isinstance(r, sp.Eq):
            g = _evaluar(r.lhs - r.rhs, [x, y], X, Y)
            if np.isfinite(g).any():
                ax.contour(X, Y, g, levels=[0], colors=[AZUL], linewidths=2.6)
                hay_curva = True
            continue
        if isinstance(r, (sp.Lt, sp.Le, sp.Gt, sp.Ge, sp.Ne)):
            g = _evaluar(r.lhs - r.rhs, [x, y], X, Y)
            ok = {sp.Lt: g < 0, sp.Le: g <= 0, sp.Gt: g > 0, sp.Ge: g >= 0, sp.Ne: g != 0}[type(r)]
            mascara &= np.where(np.isfinite(g), ok, False)
            hay_region = True
            if np.isfinite(g).any():
                ax.contour(X, Y, g, levels=[0], colors=[AZUL], linewidths=2.2,
                           linestyles="-" if isinstance(r, (sp.Le, sp.Ge)) else "--")
    if hay_region:
        ax.contourf(X, Y, mascara.astype(float), levels=[0.5, 1.5], colors=[AZUL], alpha=0.22)
    asa = []
    if hay_region:
        asa.append(Patch(fc=AZUL, alpha=0.3, label="la región (puntos que cumplen)"))
        asa.append(Line2D([0], [0], color=AZUL, lw=2.2, label="frontera incluida (≤ ≥)"))
        asa.append(Line2D([0], [0], color=AZUL, lw=2.2, ls="--", label="frontera NO incluida (< >)"))
    elif hay_curva:
        asa.append(Line2D([0], [0], color=AZUL, lw=2.6, label="la curva (puntos que cumplen)"))
    for k, (px, py, et, col) in enumerate(puntos):
        fx, fy = _f(px), _f(py)
        if fx is not None and fy is not None:
            _anotar(ax, fx, fy, et, col, k)
    if asa:
        ax.legend(handles=asa, fontsize=8.5, loc="upper right", frameon=True, framealpha=0.92, edgecolor=CLARO)
    if titulo:
        _titulo(ax, titulo)
    return fig


# ==============================================================================
# 3 · Sucesiones y series
# ==============================================================================
def fig_sumas_parciales(sumas, suma=None, titulo="Sumas parciales de la serie"):
    """sumas = [(N, S_N)] (ya calculadas); si hay suma exacta, se dibuja la asíntota."""
    Ns = [n for n, s in sumas if isinstance(s, float)]
    Ss = [s for n, s in sumas if isinstance(s, float)]
    fig = _fig(7.2, 4.4)
    ax = fig.add_subplot(111)
    lo, hi = (min(Ss), max(Ss)) if Ss else (0, 1)
    fs = _f(suma) if suma is not None else None
    if fs is not None:
        lo, hi = min(lo, fs), max(hi, fs)
    pad = (hi - lo) * 0.3 + 1e-9
    usar_log = bool(Ns) and max(Ns) / max(min(Ns), 1) > 20
    if usar_log:
        _ejes(ax, (max(min(Ns) * 0.8, 1), max(Ns) * 1.3), (lo - pad, hi + pad), xl="N", yl="Sₙ", flechas=False, logx=True)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    else:
        _ejes(ax, (0, max(Ns) * 1.08 if Ns else 1), (lo - pad, hi + pad), xl="N", yl="Sₙ", flechas=True)
    ax.plot(Ns, Ss, "o-", color=AZUL, lw=2.2, ms=7, label="suma de los primeros N términos  Sₙ", zorder=4)
    for n_, s_ in zip(Ns, Ss):
        ax.annotate(_num(s_, 6), (n_, s_), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8, color=OSCURO)
    if fs is not None:
        ax.axhline(fs, color=ROJO, ls="--", lw=1.7, label=f"suma de la serie  = {_num(fs, 8)}", zorder=2)
    ax.set_xlabel("N  (número de términos sumados)", fontsize=9.5)
    _titulo(ax, titulo)
    _leyenda(ax, loc="lower right")
    return fig


def fig_sucesion(valores, n0=1, limite=None, epsilon=None):
    """
    valores = lista de a_n (floats o None) desde n0.
    Si hay límite finito se dibuja una banda  L ± ε  y se marca desde qué n los términos quedan dentro.
    """
    ns = [n0 + i for i, v in enumerate(valores) if v is not None]
    vs = [v for v in valores if v is not None]
    fig = _fig(7.2, 4.4)
    ax = fig.add_subplot(111)
    lo, hi = (min(vs), max(vs)) if vs else (0, 1)
    fl = _f(limite) if limite is not None else None
    if fl is not None:
        lo, hi = min(lo, fl), max(hi, fl)
    pad = (hi - lo) * 0.25 + 1e-9
    _ejes(ax, (n0 - 1 if n0 > 0 else n0 - 0.5, (max(ns) + 1) if ns else n0 + 10), (lo - pad, hi + pad), xl="n", yl="aₙ")
    ax.plot(ns, vs, "o", color=AZUL, ms=6, mec="white", label="términos  aₙ", zorder=5)
    if fl is not None:
        ax.axhline(fl, color=ROJO, ls="--", lw=1.7, label=f"límite  L = {_num(fl, 6)}", zorder=2)
        eps = epsilon if epsilon is not None else 0.2 * (max(vs) - min(vs)) if vs and max(vs) > min(vs) else 0.1
        ax.axhspan(fl - eps, fl + eps, color=ROJO, alpha=0.10, label=f"banda  L ± ε   (ε = {_num(eps, 3)})", zorder=1)
        dentro = [abs(v - fl) <= eps for v in vs]
        N0 = None
        for i in range(len(vs)):
            if all(dentro[i:]):
                N0 = ns[i]
                break
        if N0 is not None and N0 > ns[0]:
            ax.axvline(N0 - 0.5, color=VERDE, ls=":", lw=1.6, label=f"desde n = {N0} todos los términos están en la banda")
    ax.set_xlabel("n  (posición del término)", fontsize=9.5)
    _titulo(ax, "Términos de la sucesión")
    _leyenda(ax, loc="best")
    return fig


# ==============================================================================
# 4 · Conjuntos, puntos, vectores, bolas y listas
# ==============================================================================
def _componentes_1d(conjunto):
    """sympy Set de ℝ -> ([(a, b, abre_izq, abre_der)], [puntos aislados], notas)."""
    ints, pts, notas = [], [], []
    S = conjunto

    def visita(s):
        if isinstance(s, sp.Union):
            for t in s.args:
                visita(t)
        elif isinstance(s, sp.Interval):
            ints.append((s.start, s.end, s.left_open, s.right_open))
        elif isinstance(s, sp.FiniteSet):
            pts.extend(s.args)
        elif s == sp.S.Reals:
            ints.append((-sp.oo, sp.oo, True, True))
        elif s == sp.S.EmptySet:
            pass
        else:
            notas.append(s)

    visita(S)
    return ints, pts, notas


def fig_recta_numerica(conjunto, ventana=None, puntos=(), titulo=None, nombre="A"):
    """
    conjunto: sympy Set de ℝ (Interval, Union, FiniteSet, Naturals, Integers, Range…).
    puntos  = [(valor, 'etiqueta', color)]  para marcar elementos de prueba (✓ pertenece / ✗ no pertenece).
    """
    ints, pts, notas = _componentes_1d(conjunto)
    discreto = None
    if conjunto in (sp.S.Naturals, sp.S.Naturals0, sp.S.Integers) or isinstance(conjunto, sp.Range):
        discreto = conjunto
    cand = [_f(v) for a_, b_, _, _ in ints for v in (a_, b_) if _f(v) is not None] + [_f(p) for p in pts if _f(p) is not None] \
        + [_f(p[0]) for p in puntos if _f(p[0]) is not None]
    if ventana is None:
        if cand:
            lo, hi = min(cand), max(cand)
            marg = max((hi - lo) * 0.35, 1.5)
            ventana = (lo - marg, hi + marg)
        else:
            ventana = (-6, 6)
    a, b = ventana
    fig = _fig(7.6, 2.9)
    ax = fig.add_subplot(111)
    ax.set_xlim(a, b)
    ax.set_ylim(-1.3, 1.5)
    ax.set_facecolor("#fbfdff")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["bottom"].set_color(OSCURO)
    ax.spines["bottom"].set_linewidth(1.6)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    ax.tick_params(labelsize=9, colors=OSCURO, length=6, width=1.2)
    ax.grid(True, axis="x", color=CLARO, alpha=0.8)
    ax.plot([1], [0], ">", color=OSCURO, ms=8, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot([0], [0], "<", color=OSCURO, ms=8, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.annotate("ℝ", xy=(1, 0), xycoords=ax.get_yaxis_transform(), xytext=(-4, 12), textcoords="offset points", ha="right",
                fontsize=12, fontweight="bold", color=OSCURO)
    for s_, e_, lo_, ro_ in ints:
        fs, fe = _f(s_), _f(e_)
        xs0 = a if (s_ == -sp.oo or fs is None) else max(fs, a)
        xe0 = b if (e_ == sp.oo or fe is None) else min(fe, b)
        if xs0 < xe0:
            ax.plot([xs0, xe0], [0, 0], color=AZUL, lw=7, solid_capstyle="butt", alpha=0.85, zorder=3)
        for val, abierto, borde in ((fs, lo_, xs0), (fe, ro_, xe0)):
            if val is not None and a <= val <= b:
                ax.plot([val], [0], "o", ms=11, mfc="white" if abierto else AZUL, mec=AZUL, mew=2.4, zorder=6)
                ax.annotate(_num(val), (val, 0), xytext=(0, -38), textcoords="offset points", ha="center", fontsize=9,
                            color=AZUL, fontweight="bold", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=AZUL, lw=0.8))
        if s_ == -sp.oo:
            ax.annotate("−∞", (a, 0), xytext=(14, 14), textcoords="offset points", fontsize=9, color=AZUL, fontweight="bold")
        if e_ == sp.oo:
            ax.annotate("+∞", (b, 0), xytext=(-28, 26), textcoords="offset points", fontsize=9, color=AZUL, fontweight="bold")
    for p in pts:
        fp = _f(p)
        if fp is not None and a <= fp <= b:
            ax.plot([fp], [0], "o", ms=11, color=AZUL, mec="white", mew=1.5, zorder=6)
            ax.annotate(_num(fp), (fp, 0), xytext=(0, -38), textcoords="offset points", ha="center", fontsize=9, color=AZUL,
                        fontweight="bold", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=AZUL, lw=0.8))
    if discreto is not None:
        k0, k1 = int(math.floor(a)), int(math.ceil(b))
        vals = [k for k in range(k0, k1 + 1) if a <= k <= b and bool(discreto.contains(k))]
        if len(vals) > 60:
            vals = vals[:: max(1, len(vals) // 60)]
        ax.plot(vals, [0] * len(vals), "o", ms=8, color=AZUL, mec="white", zorder=6)
    for v, et, col in puntos:
        fv = _f(v)
        if fv is not None and a <= fv <= b:
            ax.plot([fv], [0.55], "v", ms=11, color=col, zorder=7)
            ax.annotate(et, (fv, 0.55), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=9, color=col,
                        fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col))
    if notas and not ints and not pts and discreto is None:
        ax.text(0.5, 0.55, "(conjunto no representable en la recta)", transform=ax.transAxes, ha="center", color=GRIS)
    asa = [Patch(fc=AZUL, alpha=0.85, label=f"{nombre}"),
           Line2D([0], [0], marker="o", color="w", mfc=AZUL, mec=AZUL, ms=9, label="extremo incluido (cerrado)"),
           Line2D([0], [0], marker="o", color="w", mfc="white", mec=AZUL, mew=2, ms=9, label="extremo NO incluido (abierto)")]
    ax.legend(handles=asa, fontsize=8, loc="upper left", frameon=True, framealpha=0.92, edgecolor=CLARO, ncol=3)
    if titulo:
        _titulo(ax, titulo)
    return fig


def fig_puntos_vectores(elementos, titulo=None):
    """
    elementos = [{"tipo": "punto"|"vector", "coords": (...), "origen": (...), "etiqueta": "p", "color": "#..."}]
    2 coordenadas -> plano; 3 coordenadas -> espacio. Los puntos llevan sus coordenadas; los vectores, su longitud.
    """
    cols = [AZUL, ROJO, VERDE, NARANJA, MORADO]
    dim = max((len(e["coords"]) for e in elementos), default=2)
    dim = 3 if dim >= 3 else 2
    if dim == 2:
        xs = [0.0]
        ys = [0.0]
        for e in elementos:
            c = [float(sp.N(v)) for v in e["coords"]] + [0.0] * (2 - len(e["coords"]))
            o = [float(sp.N(v)) for v in e.get("origen", (0, 0))] + [0.0] * 2
            xs += [c[0], o[0], o[0] + c[0] if e["tipo"] == "vector" else c[0]]
            ys += [c[1], o[1], o[1] + c[1] if e["tipo"] == "vector" else c[1]]
        lx, hx, ly, hy = min(xs), max(xs), min(ys), max(ys)
        m = max(hx - lx, hy - ly, 2) * 0.28
        fig = _fig(6.6, 5.4)
        ax = fig.add_subplot(111)
        ax.set_aspect("equal", adjustable="box")
        _ejes(ax, (lx - m, hx + m), (ly - m, hy + m))
        for i, e in enumerate(elementos):
            col = e.get("color") or cols[i % len(cols)]
            c = [float(sp.N(v)) for v in e["coords"]] + [0.0] * (2 - len(e["coords"]))
            et = e.get("etiqueta", "")
            if e["tipo"] == "punto":
                _anotar(ax, c[0], c[1], et, col, i)
            else:
                o = [float(sp.N(v)) for v in e.get("origen", (0, 0))] + [0.0] * 2
                ax.annotate("", xy=(o[0] + c[0], o[1] + c[1]), xytext=(o[0], o[1]),
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=2.8, mutation_scale=18), zorder=6)
                lon = math.hypot(c[0], c[1])
                ax.annotate(f"{et}  ⟨{_num(c[0])}, {_num(c[1])}⟩\n‖{et}‖ = {_num(lon)}", (o[0] + c[0] / 2, o[1] + c[1] / 2),
                            xytext=(10, 12), textcoords="offset points", fontsize=8.5, color=OSCURO, zorder=8,
                            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col))
        if titulo:
            _titulo(ax, titulo)
        return fig
    fig = _fig(7.0, 5.8)
    ax = fig.add_subplot(111, projection="3d")
    _ejes3d(ax)
    for i, e in enumerate(elementos):
        col = e.get("color") or cols[i % len(cols)]
        c = [float(sp.N(v)) for v in e["coords"]] + [0.0] * (3 - len(e["coords"]))
        et = e.get("etiqueta", "")
        if e["tipo"] == "punto":
            ax.scatter([c[0]], [c[1]], [c[2]], color=col, s=55, depthshade=False)
            ax.text(c[0], c[1], c[2], f" {et}({_num(c[0])}, {_num(c[1])}, {_num(c[2])})", fontsize=8.5, color=OSCURO)
        else:
            o = [float(sp.N(v)) for v in e.get("origen", (0, 0, 0))] + [0.0] * 3
            ax.quiver(o[0], o[1], o[2], c[0], c[1], c[2], color=col, linewidth=2.6, arrow_length_ratio=0.12)
            ax.text(o[0] + c[0], o[1] + c[1], o[2] + c[2], f" {et}", fontsize=9, color=col, fontweight="bold")
    if titulo:
        _titulo(ax, titulo)
    return fig


def fig_bola_2d(centro, radio, cerrada=False, puntos=(), titulo=None, esfera=False):
    """
    Bola (disco) en ℝ²: borde continuo si es cerrada, discontinuo si es abierta.
    puntos = [(x, y, 'etiqueta', 'interior'|'frontera'|'exterior')]  se colorean según su posición.
    """
    cx, cy, r = _f(centro[0]), _f(centro[1]), _f(radio)
    m = r * 0.45 + 0.5
    ext = [(cx - r, cx + r), (cy - r, cy + r)]
    for p in puntos:
        px, py = _f(p[0]), _f(p[1])
        if px is not None and py is not None:
            ext[0] = (min(ext[0][0], px), max(ext[0][1], px))
            ext[1] = (min(ext[1][0], py), max(ext[1][1], py))
    fig = _fig(6.6, 5.6)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="box")
    _ejes(ax, (ext[0][0] - m, ext[0][1] + m), (ext[1][0] - m, ext[1][1] + m))
    if not esfera:
        ax.add_patch(Circle((cx, cy), r, fc=AZUL, alpha=0.18, ec="none", zorder=2))
    ax.add_patch(Circle((cx, cy), r, fc="none", ec=AZUL, lw=2.8, ls="-" if (cerrada or esfera) else (0, (5, 3)), zorder=4))
    ax.plot([cx], [cy], "o", color=OSCURO, ms=7, zorder=6)
    ax.annotate(f"centro ({_num(cx)}, {_num(cy)})", (cx, cy), xytext=(-8, -22), textcoords="offset points", ha="center",
                fontsize=8.5, color=OSCURO, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=OSCURO))
    ang = math.radians(145)
    ax.annotate("", xy=(cx + r * math.cos(ang), cy + r * math.sin(ang)), xytext=(cx, cy),
                arrowprops=dict(arrowstyle="-|>", color=ROJO, lw=1.8), zorder=5)
    ax.text(cx + 0.55 * r * math.cos(ang), cy + 0.55 * r * math.sin(ang) + 0.06 * r, f"r = {_num(r)}", color=ROJO, fontsize=10,
            fontweight="bold", ha="center", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    colores = {"interior": VERDE, "frontera": NARANJA, "exterior": ROJO}
    for k, p in enumerate(puntos):
        px, py, et, pos = p
        _anotar(ax, _f(px), _f(py), f"{et}: {pos}", colores.get(pos, GRIS), k)
    asa = [Patch(fc=AZUL, alpha=0.3, label="puntos de la bola" if not esfera else "puntos de la esfera (solo el borde)"),
           Line2D([0], [0], color=AZUL, lw=2.8, ls="-" if (cerrada or esfera) else (0, (5, 3)),
                  label="borde incluido (bola cerrada)" if (cerrada or esfera) else "borde NO incluido (bola abierta)")]
    if puntos:
        asa += [Line2D([0], [0], marker="o", color="w", mfc=c, ms=9, label=n) for n, c in colores.items()]
    fig.legend(handles=asa, loc="outside lower center", ncol=2, fontsize=8.5, frameon=True, framealpha=0.95, edgecolor=CLARO)
    if titulo:
        _titulo(ax, titulo)
    return fig


def fig_bola_3d(centro, radio, cerrada=False, puntos=(), titulo=None):
    cx, cy, cz, r = _f(centro[0]), _f(centro[1]), _f(centro[2]), _f(radio)
    fig = _fig(6.8, 5.8)
    ax = fig.add_subplot(111, projection="3d")
    _ejes3d(ax)
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:24j]
    ax.plot_surface(cx + r * np.cos(u) * np.sin(v), cy + r * np.sin(u) * np.sin(v), cz + r * np.cos(v), color=AZUL,
                    alpha=0.28 if cerrada else 0.18, linewidth=0.3, edgecolor=AZUL if cerrada else None)
    ax.scatter([cx], [cy], [cz], color=OSCURO, s=40, depthshade=False)
    ax.plot([cx, cx + r], [cy, cy], [cz, cz], color=ROJO, lw=2.4)
    ax.text(cx + r / 2, cy, cz, f"  r = {_num(r)}", color=ROJO, fontsize=10, fontweight="bold")
    colores = {"interior": VERDE, "frontera": NARANJA, "exterior": ROJO}
    for px, py, pz, et, pos in puntos:
        ax.scatter([_f(px)], [_f(py)], [_f(pz)], color=colores.get(pos, GRIS), s=50, depthshade=False)
        ax.text(_f(px), _f(py), _f(pz), f" {et}: {pos}", fontsize=8.5, color=OSCURO)
    lim = r * 1.25
    ax.set_xlim(cx - lim, cx + lim)
    ax.set_ylim(cy - lim, cy + lim)
    ax.set_zlim(cz - lim, cz + lim)
    ax.set_box_aspect((1, 1, 1))
    _titulo(ax, titulo or ("Bola cerrada en ℝ³" if cerrada else "Bola abierta en ℝ³"))
    return fig


def fig_lista(valores, titulo="Datos de la lista"):
    """Diagrama de puntos de una lista numérica, con su media y su mediana."""
    vs = [float(sp.N(v)) for v in valores]
    n = len(vs)
    fig = _fig(7.2, 4.2)
    ax = fig.add_subplot(111)
    lo, hi = min(vs), max(vs)
    pad = (hi - lo) * 0.3 + 1
    _ejes(ax, (0, n + 1), (min(lo - pad, -0.5 if lo >= 0 else lo - pad), hi + pad), xl="posición", yl="valor")
    ax.vlines(range(1, n + 1), 0, vs, color=CLARO, lw=1.5, zorder=2)
    ax.plot(range(1, n + 1), vs, "o", color=AZUL, ms=8, mec="white", zorder=5, label="datos")
    for i, v in enumerate(vs, 1):
        if n <= 14:
            ax.annotate(_num(v), (i, v), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8.5, color=OSCURO)
    media = sum(vs) / n
    med = float(np.median(vs))
    ax.axhline(media, color=ROJO, ls="--", lw=1.6, label=f"media = {_num(media, 5)}")
    ax.axhline(med, color=VERDE, ls=":", lw=1.8, label=f"mediana = {_num(med, 5)}")
    _titulo(ax, titulo)
    _leyenda(ax, loc="best")
    return fig
