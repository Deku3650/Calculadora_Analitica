# pages/7_Ecuaciones_Diferenciales.py
import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.ticker import AutoMinorLocator, MaxNLocator

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(
    page_title="Ecuaciones Diferenciales - MATHESIS",
    page_icon="🌀",
    layout="wide",
)

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from interprete_latex import ErrorLatex, ErrorNoSoportado, latex_a_sympy, leer_en_espanol  # noqa: E402
from teclado_matematico import LAYOUTS, teclado_matematico  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    imprimir_matriz_simbolica,
    inicializar_estado,
    leer_expresion_st,
    mostrar_figura_segura,
)

cargar_estilos_globales()
inicializar_estado()

# Registrar layout "edo" en el teclado matemático (sin las pestañas de conjuntos/lógica #&* ni ℝⁿ)
if "edo" not in LAYOUTS and "calculo" in LAYOUTS:
    LAYOUTS["edo"] = {
        "tabs": [t for t in LAYOUTS["calculo"]["tabs"] if t.get("id") in ("123", "fx", "trig", "abc")]
    }

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
MORADO = "#7c3aed"
ROSA_EJE = "#db2777"
LIMA_EJE = "#65a30d"
CIAN_EJE = "#0284c7"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"


# ==============================================================================
# UTILIDADES MATEMÁTICAS Y DE TRAZADO ANALÍTICO RÁPIDO
# ==============================================================================
def _limpiar_vector_propio(v: sp.Matrix) -> sp.Matrix:
    """Escala un vector propio para obtener componentes enteras coprimas."""
    try:
        denoms = [sp.fraction(sp.simplify(e))[1] for e in v]
        mcm = sp.Integer(1)
        for d in denoms:
            mcm = sp.lcm(mcm, d)
        v_ent = sp.simplify(v * mcm)
        nums = [sp.simplify(e) for e in v_ent if e != 0]
        if nums and all(n.is_Integer for n in nums):
            mcd = math.gcd(*[abs(int(n)) for n in nums])
            if mcd > 1:
                v_ent = v_ent / mcd
        for e in v_ent:
            if e != 0:
                if e.is_real and e < 0:
                    v_ent = -v_ent
                break
        return v_ent
    except Exception:
        return v


def _lienzo_fase_2d(w=5.6, h=5.2, lim=4.0, xlabel="x₁", ylabel="x₂", titulo=""):
    """Crea un lienzo limpio con cuadrícula acotada que nunca se congela al escalar límites."""
    fig, ax = plt.subplots(figsize=(w, h), dpi=105, facecolor=FONDO)
    ax.set_facecolor("#fbfdff")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color="#cbd5e1", lw=0.9, alpha=0.95)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)

    ax.annotate(
        "",
        xy=(lim * 0.98, 0),
        xytext=(-lim * 0.98, 0),
        arrowprops=dict(arrowstyle="->", color=CIAN_EJE, lw=1.7, mutation_scale=14),
        zorder=2,
    )
    ax.annotate(
        "",
        xy=(0, lim * 0.98),
        xytext=(0, -lim * 0.98),
        arrowprops=dict(arrowstyle="->", color=CIAN_EJE, lw=1.7, mutation_scale=14),
        zorder=2,
    )
    ax.text(lim * 0.90, -lim * 0.08, xlabel, fontsize=10, fontweight="bold", color=OSCURO)
    ax.text(lim * 0.04, lim * 0.89, ylabel, fontsize=10, fontweight="bold", color=OSCURO)
    ax.tick_params(colors=OSCURO, labelsize=8)
    if titulo:
        ax.set_title(titulo, fontsize=10, fontweight="bold", color=OSCURO, pad=8)
    return fig, ax


def _trazar_curva_con_flechas(ax, xs, ys, color, n_flechas=2, lw=1.9):
    """Dibuja una trayectoria paramétrica y coloca puntas de flecha en la dirección del flujo."""
    ax.plot(xs, ys, color=color, lw=lw, zorder=4)
    n_pts = len(xs)
    if n_pts < 10:
        return
    ds = np.hypot(np.diff(xs), np.diff(ys))
    s_acum = np.concatenate([[0.0], np.cumsum(ds)])
    l_total = s_acum[-1]
    if l_total < 0.25:
        return
    fracciones = np.linspace(0.28, 0.72, n_flechas)
    for fr in fracciones:
        idx = int(np.searchsorted(s_acum, fr * l_total))
        idx = min(max(idx, 1), n_pts - 2)
        dx = xs[idx + 1] - xs[idx - 1]
        dy = ys[idx + 1] - ys[idx - 1]
        if math.hypot(dx, dy) > 1e-5:
            ax.annotate(
                "",
                xy=(xs[idx + 1], ys[idx + 1]),
                xytext=(xs[idx], ys[idx]),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, mutation_scale=12.5),
                zorder=5,
            )


def _dibujar_subespacio_invariante(ax, vec_2d, lam_val, lim, etiqueta, color=ROSA_EJE):
    """Dibuja la recta invariante generada por un vector propio con flechas de dirección."""
    vx, vy = float(vec_2d[0]), float(vec_2d[1])
    nrm = math.hypot(vx, vy)
    if nrm < 1e-9:
        return
    ux, uy = vx / nrm, vy / nrm
    L = lim * 0.92
    ax.plot([-L * ux, L * ux], [-L * uy, L * uy], color=color, lw=2.2, zorder=3, label=f"{etiqueta} (λ={lam_val:g})")

    if abs(lam_val) > 1e-9:
        for signo_rama in (1.0, -1.0):
            for r_pos in (0.40 * L, 0.74 * L):
                x_base = signo_rama * r_pos * ux
                y_base = signo_rama * r_pos * uy
                sentido = 1.0 if lam_val > 0 else -1.0
                paso = 0.08 * L * sentido * signo_rama
                ax.annotate(
                    "",
                    xy=(x_base + paso * ux, y_base + paso * uy),
                    xytext=(x_base, y_base),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.1, mutation_scale=13.5),
                    zorder=6,
                )
    ax.text(L * ux * 0.82, L * uy * 0.82 + 0.16, etiqueta, color=color, fontweight="bold", fontsize=9, zorder=7)


def _retrato_2d_real(P_trans, lams, lim=4.0, xl="y₁", yl="y₂", titulo="", eti_ejes=("y₁", "y₂")):
    """Retrato de fase 2D rápido y exacto usando tiempo normalizado τ = máx|λ|·t."""
    lam1 = float(sp.N(lams[0]))
    lam2 = float(sp.N(lams[1]))
    P_np = np.array(P_trans, dtype=float)

    # Normalizar columnas de P_np si son muy grandes para mantener una ventana limpia
    n0 = np.linalg.norm(P_np[:, 0]) or 1.0
    n1 = np.linalg.norm(P_np[:, 1]) or 1.0
    P_vis = np.column_stack([P_np[:, 0] / n0 * 2.0, P_np[:, 1] / n1 * 2.0]) if max(n0, n1) > 4.0 else P_np
    escala_p = max(np.linalg.norm(P_vis[:, 0]), np.linalg.norm(P_vis[:, 1]), 1.0)
    lim_eff = lim * (escala_p * 0.85 if escala_p > 1.2 else 1.0)

    fig, ax = _lienzo_fase_2d(lim=lim_eff, xlabel=xl, ylabel=yl, titulo=titulo)
    _dibujar_subespacio_invariante(ax, P_vis[:, 0], lam1, lim_eff, eti_ejes[0], color=ROSA_EJE)
    _dibujar_subespacio_invariante(ax, P_vis[:, 1], lam2, lim_eff, eti_ejes[1], color=LIMA_EJE)
    ax.plot([0], [0], "o", color=ROJO, ms=6, zorder=8)

    # Reescalado positivo del tiempo: conserva exactamente las curvas geométricas sin desbordar exp()
    max_l = max(abs(lam1), abs(lam2), 1e-6)
    l1_n, l2_n = lam1 / max_l, lam2 / max_l
    taus = np.linspace(-2.3, 2.3, 180)

    if lam1 * lam2 < 0:
        semillas_y = [(sx * c, sy * c) for sx in (-1, 1) for sy in (-1, 1) for c in (0.65, 1.35)]
    else:
        semillas_y = [(sx * 1.4, sy * c) for sx in (-1, 1) for sy in (-1, 1) for c in (0.45, 1.15, 2.1)]

    for c1, c2 in semillas_y:
        y1_t = c1 * np.exp(np.clip(l1_n * taus, -12.0, 12.0))
        y2_t = c2 * np.exp(np.clip(l2_n * taus, -12.0, 12.0))
        pts_x = P_vis @ np.vstack([y1_t, y2_t])
        mask = (np.abs(pts_x[0]) <= lim_eff * 0.94) & (np.abs(pts_x[1]) <= lim_eff * 0.94)
        if np.sum(mask) > 12:
            _trazar_curva_con_flechas(ax, pts_x[0, mask], pts_x[1, mask], color=MORADO, n_flechas=2, lw=1.8)

    ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)
    return fig


def _retrato_2d_complejo(a_re, b_im, Q_mat=None, lim=4.0, xl="ξ₁", yl="ξ₂", titulo=""):
    """Retrato de fase 2D para raíces complejas con círculos/elipses guía y vectores de la base real Q."""
    Q_np = np.eye(2) if Q_mat is None else np.array(Q_mat, dtype=float)
    escala_q = max(np.linalg.norm(Q_np[:, 0]), np.linalg.norm(Q_np[:, 1]), 1.0)
    lim_eff = lim * (escala_q * 0.9 if Q_mat is not None else 1.0)
    fig, ax = _lienzo_fase_2d(lim=lim_eff, xlabel=xl, ylabel=yl, titulo=titulo)

    ang_g = np.linspace(0, 2 * np.pi, 200)
    for r_guia in (0.9, 1.8, 2.7):
        circ_xi = np.vstack([r_guia * np.cos(ang_g), r_guia * np.sin(ang_g)])
        elip_x = Q_np @ circ_xi
        ax.plot(elip_x[0], elip_x[1], color=MORADO, ls="--", lw=1.0, alpha=0.38, zorder=2)

    if Q_mat is not None:
        v_col, u_col = Q_np[:, 0], Q_np[:, 1]
        ax.annotate("", xy=(v_col[0], v_col[1]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=ROSA_EJE, lw=2.3), zorder=7)
        ax.annotate("", xy=(u_col[0], u_col[1]), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=VERDE, lw=2.3), zorder=7)
        ax.plot([], [], color=ROSA_EJE, lw=2.3, label=f"v = Im(w₁) = ({v_col[0]:g}, {v_col[1]:g})")
        ax.plot([], [], color=VERDE, lw=2.3, label=f"u = Re(w₁) = ({u_col[0]:g}, {u_col[1]:g})")

    # Parametrizar por ángulo de giro θ para garantizar espirales limpias sin importar la escala de a y b
    signo_b = 1.0 if b_im >= 0 else -1.0
    if abs(a_re) < 1e-7:
        thetas = np.linspace(0, 2 * np.pi * signo_b, 220)
        semillas_r = [1.0, 1.9, 2.8]
        for r0 in semillas_r:
            xi1 = r0 * np.cos(thetas)
            xi2 = r0 * np.sin(thetas)
            pts_x = Q_np @ np.vstack([xi1, xi2])
            _trazar_curva_con_flechas(ax, pts_x[0], pts_x[1], color=AZUL, n_flechas=4, lw=2.0)
    else:
        # 2.5 vueltas completas con tasa radial visualmente calibrada según el signo de a_re
        thetas = np.linspace(-2.5 * np.pi, 2.5 * np.pi, 400) * signo_b
        tasa_vis = 0.14 * (1.0 if a_re > 0 else -1.0)
        for s_rama in (1.0, -1.0):
            r_th = 1.35 * np.exp(tasa_vis * (thetas * signo_b))
            xi1 = s_rama * r_th * np.cos(thetas)
            xi2 = s_rama * r_th * np.sin(thetas)
            pts_x = Q_np @ np.vstack([xi1, xi2])
            mask = (np.abs(pts_x[0]) <= lim_eff * 0.94) & (np.abs(pts_x[1]) <= lim_eff * 0.94)
            if np.sum(mask) > 20:
                _trazar_curva_con_flechas(ax, pts_x[0, mask], pts_x[1, mask], color=AZUL, n_flechas=4, lw=2.0)

    ax.plot([0], [0], "o", color=ROJO, ms=6.5, zorder=8)
    if Q_mat is not None:
        ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)
    return fig


def _retrato_3d_real(P_mat, lams_info, titulo="Retrato de Fase en ℝ³"):
    """Dibuja el retrato de fase 3D para raíces reales."""
    fig = plt.figure(figsize=(6.8, 5.5), dpi=105, facecolor=FONDO)
    ax = fig.add_subplot(111, projection="3d")
    M_np = np.array(P_mat, dtype=float)
    # Normalizar columnas visualmente para que ningún vector propio gigante aplaste los demás
    cols_norm = [M_np[:, i] / (np.linalg.norm(M_np[:, i]) or 1.0) * 2.5 for i in range(3)]
    M_vis = np.column_stack(cols_norm)
    escala = 3.2

    ax.set_xlim(-escala, escala)
    ax.set_ylim(-escala, escala)
    ax.set_zlim(-escala, escala)
    ax.set_xlabel("x₁", fontweight="bold")
    ax.set_ylabel("x₂", fontweight="bold")
    ax.set_zlabel("x₃", fontweight="bold")
    ax.view_init(elev=22, azim=-52)
    ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=OSCURO)

    l1, l2, l3 = [float(sp.N(x)) for x in lams_info]
    max_l = max(abs(l1), abs(l2), abs(l3), 1e-6)
    l1_n, l2_n, l3_n = l1 / max_l, l2 / max_l, l3 / max_l

    colores_v = [ROSA_EJE, LIMA_EJE, CIAN_EJE]
    for idx, (lam_i, col_i) in enumerate(zip((l1, l2, l3), colores_v)):
        vi = M_vis[:, idx] * 1.15
        ax.plot([-vi[0], vi[0]], [-vi[1], vi[1]], [-vi[2], vi[2]], color=col_i, lw=2.4, label=f"⟨v_{idx+1}⟩ (λ={lam_i:g})")

    taus = np.linspace(-2.0, 2.0, 180)
    for s1, s2, s3 in [(1, 1, 1), (-1, 1, 1), (1, -1, -1), (-1, -1, 1), (1, 1, -1), (-1, -1, -1)]:
        y_t = np.vstack([
            0.7 * s1 * np.exp(np.clip(l1_n * taus, -8, 8)),
            0.7 * s2 * np.exp(np.clip(l2_n * taus, -8, 8)),
            0.7 * s3 * np.exp(np.clip(l3_n * taus, -8, 8)),
        ])
        x_t = M_vis @ y_t
        mask = np.max(np.abs(x_t), axis=0) <= escala * 0.95
        if np.sum(mask) > 10:
            ax.plot(x_t[0, mask], x_t[1, mask], x_t[2, mask], color=MORADO, lw=1.8, alpha=0.88)

    ax.scatter([0], [0], [0], color=ROJO, s=45)
    ax.legend(loc="upper left", fontsize=8.0)
    return fig


def _retrato_3d_resorte_complejo(a_re, b_im, l3, Q_mat=None, titulo=""):
    """
    Dibuja un resorte helicoidal 3D nítido (5 vueltas completas) con flechas de flujo y superficie guía:
    - Si Q_mat es None: dibuja el retrato de fases para z (ż = Λz) alrededor del eje vertical z₃.
    - Si Q_mat se pasa: dibuja el espacio original x = Qz alrededor del eje propio inclinado ⟨w₃⟩.
    """
    fig = plt.figure(figsize=(6.6, 5.6), dpi=110, facecolor=FONDO)
    ax = fig.add_subplot(111, projection="3d")

    if Q_mat is None:
        Q_vis = np.eye(3)
        xl, yl, zl = "z₁", "z₂", "z₃"
    else:
        Q_np = np.array(Q_mat, dtype=float)
        # Normalizar visualmente las columnas de Q para que la elipse y el eje w3 tengan proporción armónica
        c0 = Q_np[:, 0] / (np.linalg.norm(Q_np[:, 0]) or 1.0) * 1.6
        c1 = Q_np[:, 1] / (np.linalg.norm(Q_np[:, 1]) or 1.0) * 1.6
        c2 = Q_np[:, 2] / (np.linalg.norm(Q_np[:, 2]) or 1.0) * 2.2
        Q_vis = np.column_stack([c0, c1, c2])
        xl, yl, zl = "x₁", "x₂", "x₃"

    escala = 3.2
    ax.set_xlim(-escala, escala)
    ax.set_ylim(-escala, escala)
    ax.set_zlim(-escala, escala)
    ax.set_xlabel(xl, fontweight="bold")
    ax.set_ylabel(yl, fontweight="bold")
    ax.set_zlabel(zl, fontweight="bold")
    ax.view_init(elev=23, azim=-50)
    ax.set_title(titulo, fontsize=10.2, fontweight="bold", color=OSCURO)

    # 1. Dibujar el plano invariante (z3 = 0 ó plano generado por u1, v1) como disco translúcido
    r_disco = np.linspace(0, 2.2, 12)
    th_disco = np.linspace(0, 2 * np.pi, 40)
    RD, TD = np.meshgrid(r_disco, th_disco)
    Z1_d = RD * np.cos(TD)
    Z2_d = RD * np.sin(TD)
    Z3_d = np.zeros_like(Z1_d)
    pts_disco = np.einsum("ij,jkl->ikl", Q_vis, np.array([Z1_d, Z2_d, Z3_d]))
    ax.plot_surface(pts_disco[0], pts_disco[1], pts_disco[2], color=CIAN_EJE, alpha=0.12, linewidth=0)

    # 2. Dibujar eje invariante z3 ó ⟨w3⟩ (con flechas según el signo de l3) y vectores u1, v1
    eje_w3 = Q_vis[:, 2] * 1.35
    ax.plot(
        [-eje_w3[0], eje_w3[0]],
        [-eje_w3[1], eje_w3[1]],
        [-eje_w3[2], eje_w3[2]],
        color=ROSA_EJE,
        lw=2.6,
        label=f"{'Eje z₃' if Q_mat is None else 'Eje ⟨w₃⟩'} (λ₃={l3:g})",
    )
    if Q_mat is not None:
        v1_c, u1_c = Q_vis[:, 0], Q_vis[:, 1]
        ax.quiver(0, 0, 0, u1_c[0], u1_c[1], u1_c[2], color=VERDE, lw=2.3, arrow_length_ratio=0.18, label="u₁ = Re(w₁)")
        ax.quiver(0, 0, 0, v1_c[0], v1_c[1], v1_c[2], color=NARANJA, lw=2.3, arrow_length_ratio=0.18, label="v₁ = Im(w₁)")

    # 3. Parametrizar el resorte con 4.5 vueltas completas bien definidas
    n_vueltas = 4.5
    s_param = np.linspace(0.0, 1.0, 550)
    signo_giro = 1.0 if b_im >= 0 else -1.0
    theta = signo_giro * (2.0 * np.pi * n_vueltas) * s_param

    # Radio r(s) según el signo de a_re (expande si a>0, contrae si a<0, constante si a=0)
    if a_re > 1e-7:
        r_s = 0.35 * np.exp(1.55 * s_param)
    elif a_re < -1e-7:
        r_s = 2.05 * np.exp(-1.55 * s_param)
    else:
        r_s = np.full_like(s_param, 1.45)

    # Altura axial z3(s) según el signo de l3 (se aleja del plano si l3>0, se acerca al plano si l3<0)
    if l3 > 1e-7:
        z3_base = 0.18 * np.exp(2.55 * s_param)
    elif l3 < -1e-7:
        z3_base = 2.35 * np.exp(-2.55 * s_param)
    else:
        z3_base = np.full_like(s_param, 1.2)

    z1_s = r_s * np.cos(theta)
    z2_s = r_s * np.sin(theta)

    # Dibujar el resorte superior (z3 > 0), el resorte inferior (z3 < 0) y la espiral en el plano (z3 = 0)
    for signo_z, col_res, lbl_res in [
        (1.0, AZUL, "Resorte superior (z₃ > 0)"),
        (-1.0, MORADO, "Resorte inferior (z₃ < 0)"),
        (0.0, VERDE, "Órbita en plano invariante (z₃ = 0)"),
    ]:
        z3_curva = signo_z * z3_base
        pts_3d = Q_vis @ np.vstack([z1_s, z2_s, z3_curva])
        lw_c = 2.2 if signo_z != 0 else 1.5
        ls_c = "-" if signo_z != 0 else "--"
        ax.plot(pts_3d[0], pts_3d[1], pts_3d[2], color=col_res, lw=lw_c, ls=ls_c, label=lbl_res)

        # Colocar 4 flechas 3D sobre las vueltas del resorte indicando el sentido del flujo
        if signo_z != 0:
            for idx_f in (110, 240, 370, 490):
                p0 = pts_3d[:, idx_f]
                dp = pts_3d[:, idx_f + 4] - p0
                n_dp = np.linalg.norm(dp)
                if n_dp > 1e-6:
                    dp_u = dp / n_dp * 0.42
                    ax.quiver(
                        p0[0], p0[1], p0[2],
                        dp_u[0], dp_u[1], dp_u[2],
                        color=col_res,
                        lw=2.0,
                        arrow_length_ratio=0.45,
                    )

    ax.scatter([0], [0], [0], color=ROJO, s=48, zorder=10)
    ax.legend(loc="upper left", fontsize=7.8)
    return fig


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
encabezado_pagina(
    "🌀 Módulo de Ecuaciones Diferenciales Ordinarias y Sistemas en ℝⁿ",
    "Sistemas lineales homogéneos ẋ = Ax en ℝ² y ℝ³, cambio de coordenadas canónicas, complejificación, retratos de fase analíticos, EDOs de 1.º y 2.º orden y Laplace.",
)

tab_sistemas, tab_edo1, tab_edo2 = st.tabs([
    "🧭 1. Sistemas Lineales ẋ = Ax (ℝ² y ℝ³)",
    "📈 2. EDOs de Primer Orden y Campo de Direcciones",
    "🌊 3. EDOs de 2.º Orden y Transformada de Laplace",
])

# ==============================================================================
# PESTAÑA 1: SISTEMAS LINEALES X' = A X EN R^2 Y R^3 (CON BOTÓN DE EJECUCIÓN)
# ==============================================================================
with tab_sistemas:
    with st.container(border=True):
        header_tarjeta("Definición del Sistema Lineal Homogéneo ẋ = Ax")

        c_modo, c_dim = st.columns([1.6, 1])
        with c_modo:
            fuente_mat = st.radio(
                "Método de entrada de la matriz A:",
                ["Ingresar componentes manualmente", "Importar desde el Inventario de Matrices"],
                horizontal=True,
                key="edo_fuente_mat",
            )
        with c_dim:
            dim_sys = int(st.radio(
                "Dimensión del sistema (ℝⁿ):",
                [2, 3],
                horizontal=True,
                key="edo_dim_sys",
            ))

        if fuente_mat == "Importar desde el Inventario de Matrices":
            mats_compatibles = {
                k: v for k, v in st.session_state.get("mis_matrices", {}).items()
                if v.shape == (dim_sys, dim_sys) and not v.free_symbols and not v.has(sp.I)
            }
            if mats_compatibles:
                nom_m_imp = st.selectbox("Seleccione matriz cuadrada del inventario:", list(mats_compatibles.keys()), key="edo_imp_sel")
                imprimir_matriz_simbolica(mats_compatibles[nom_m_imp])
                if st.button("🚀 Analizar y Resolver Sistema Importado", type="primary", use_container_width=True):
                    st.session_state["edo_matriz_activa"] = mats_compatibles[nom_m_imp]
                    st.session_state["edo_dim_activa"] = dim_sys
            else:
                st.info(f"No hay matrices numéricas reales de tamaño {dim_sys}×{dim_sys} en el inventario.")
        else:
            valores_def_2x2 = [["-2", "-2"], ["6", "5"]]
            valores_def_3x3 = [["12", "-4", "-5"], ["12", "2", "-4"], ["30", "-8", "-13"]]
            plantilla = valores_def_2x2 if dim_sys == 2 else valores_def_3x3

            with st.form(f"form_matriz_edo_{dim_sys}"):
                st.caption("Complete las entradas de la matriz $A$ y pulse el botón para ejecutar el análisis:")
                matriz_input_str = []
                for i in range(dim_sys):
                    cols_m = st.columns(dim_sys)
                    fila_m = []
                    for j in range(dim_sys):
                        with cols_m[j]:
                            celda_txt = st.text_input(
                                f"Entrada a_({i+1},{j+1})",
                                value=plantilla[i][j],
                                key=f"edo_cell_{dim_sys}_{i}_{j}",
                            )
                            fila_m.append(celda_txt)
                    matriz_input_str.append(fila_m)

                ejecutar_sis = st.form_submit_button("🚀 Analizar y Resolver Sistema ẋ = Ax", use_container_width=True)

            if ejecutar_sis:
                mat_parsed = []
                err_parse = False
                for i in range(dim_sys):
                    fila_p = []
                    for j in range(dim_sys):
                        val_p = leer_expresion_st(matriz_input_str[i][j], solo_reales=True)
                        if val_p is None or val_p.free_symbols:
                            err_parse = True
                        else:
                            fila_p.append(val_p)
                    mat_parsed.append(fila_p)
                if err_parse:
                    st.error("⛔ Ingrese valores numéricos reales válidos en todas las entradas de la matriz A.")
                else:
                    st.session_state["edo_matriz_activa"] = sp.Matrix(mat_parsed)
                    st.session_state["edo_dim_activa"] = dim_sys

    # Si aún no se ha pulsado el botón o cambió la dimensión, inicializar con la matriz por defecto
    if "edo_matriz_activa" not in st.session_state or st.session_state.get("edo_dim_activa") != dim_sys:
        st.session_state["edo_matriz_activa"] = (
            sp.Matrix([[-2, -2], [6, 5]]) if dim_sys == 2
            else sp.Matrix([[12, -4, -5], [12, 2, -4], [30, -8, -13]])
        )
        st.session_state["edo_dim_activa"] = dim_sys

    A_sp = st.session_state["edo_matriz_activa"]
    t_sym = sp.Symbol("t", real=True)
    lam_sym = sp.Symbol("lambda")

    char_poly = calcular_con_limite(A_sp.charpoly, args=(lam_sym,), timeout=8)
    eigenvects_raw = calcular_con_limite(A_sp.eigenvects, timeout=8)
    tiene_complejos = any(sp.im(ev[0]) != 0 for ev in eigenvects_raw)
    suma_mg = sum(len(ev[2]) for ev in eigenvects_raw)

    with st.container(border=True):
        header_tarjeta("1. Sistema Diferencial, Puntos Singulares y Valores Propios")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            vars_x = [sp.Symbol(f"x_{i+1}") for i in range(dim_sys)]
            dot_x = [sp.Symbol(f"\\dot{{x}}_{i+1}") for i in range(dim_sys)]
            st.markdown("**Sistema $\\dot{x} = Ax$:**")
            st.latex(sp.latex(sp.Matrix(dot_x)) + " = " + sp.latex(A_sp) + sp.latex(sp.Matrix(vars_x)))
            det_A = sp.simplify(A_sp.det())
            if det_A != 0:
                st.success("Punto singular (equilibrio) único en el origen: $\\mathbf{x} = \\mathbf{0}$ ($\\det(A) = " + sp.latex(det_A) + " \\neq 0$).")
            else:
                st.warning("La matriz tiene $\\det(A) = 0$: existe todo un subespacio de puntos de equilibrio $\\ker(A)$.")
        with c_p2:
            st.markdown("**Polinomio Característico $P_A(\\lambda)$ y Valores Propios:**")
            st.latex("P_A(\\lambda) = " + sp.latex(char_poly.as_expr()) + " = " + sp.latex(sp.factor(char_poly.as_expr())))
            raices_ltx = [
                r"\lambda = " + sp.latex(sp.simplify(val)) + r" \;(\text{mult. }" + str(mult_a) + ")"
                for val, mult_a, _ in eigenvects_raw
            ]
            st.latex(r", \quad ".join(raices_ltx))

    # ======================================================================
    # RAMA A: VALORES PROPIOS REALES (DIAGONALIZACIÓN)
    # ======================================================================
    if not tiene_complejos and suma_mg == dim_sys:
        pares_vp = []
        for val, mult_a, vects in eigenvects_raw:
            for v_i in vects:
                pares_vp.append((sp.simplify(val), _limpiar_vector_propio(v_i)))
        pares_vp.sort(key=lambda item: float(sp.N(item[0])), reverse=True)

        lams_r = [p[0] for p in pares_vp]
        vecs_r = [p[1] for p in pares_vp]
        P_mat = sp.Matrix.hstack(*vecs_r)
        P_inv = calcular_con_limite(P_mat.inv, timeout=8)
        Lambda_mat = sp.diag(*lams_r)

        with st.container(border=True):
            header_tarjeta("2. Resolución por Cambio de Coordenadas Canónicas y Retratos de Fase")
            t_r_paso2, t_r_paso3, t_r_paso4, t_r_graf = st.tabs([
                "📐 1. Vectores Propios y Cambio P",
                "🔄 2. Sistema Canónico ẏ = Λy y Norma ‖φ(t)‖²",
                "🔭 3. Comportamiento Asintótico y Curvas Implícitas",
                "🎨 4. Retratos de Fase (Canónico y Original)",
            ])

            with t_r_paso2:
                cols_vp = st.columns(dim_sys)
                for idx, (lam_i, v_i) in enumerate(pares_vp):
                    with cols_vp[idx]:
                        st.markdown(f"**Valor propio $\\lambda_{{{idx+1}}} = {sp.latex(lam_i)}$:**")
                        M_ker = A_sp - lam_i * sp.eye(dim_sys)
                        st.latex("(A - (" + sp.latex(lam_i) + ")I) = " + sp.latex(M_ker))
                        st.latex("v_{" + str(idx + 1) + "} = " + sp.latex(v_i))

                st.divider()
                st.markdown("**Matriz de cambio de coordenadas ($x = Py \\iff y = P^{-1}x$):**")
                st.latex(
                    "P = " + sp.latex(P_mat)
                    + r", \qquad P^{-1} = " + sp.latex(P_inv)
                    + r", \qquad \Lambda = P^{-1}AP = " + sp.latex(Lambda_mat)
                )

            with t_r_paso3:
                cs_sym = [sp.Symbol(f"c_{i+1}", real=True) for i in range(dim_sys)]
                phi_y = sp.Matrix([cs_sym[i] * sp.exp(lams_r[i] * t_sym) for i in range(dim_sys)])
                phi_x = sp.simplify(P_mat * phi_y)

                st.markdown("**1. Sistema desacoplado en coordenadas canónicas $\\dot{y} = \\Lambda y$ y su solución $\\varphi_\\Lambda(t)$:**")
                st.latex(r"\dot{y} = " + sp.latex(Lambda_mat) + r"y \implies \varphi_{\Lambda}(t) = " + sp.latex(phi_y))

                st.markdown("**2. Análisis de la norma al cuadrado $\\|\\varphi_\\Lambda(t)\\|^2$:**")
                norma_sq = sum((cs_sym[i] ** 2) * sp.exp(2 * lams_r[i] * t_sym) for i in range(dim_sys))
                st.latex(r"\|\varphi_{\Lambda}(t)\|^{2} = " + sp.latex(norma_sq))

                l_flts = [float(sp.N(l)) for l in lams_r]
                if all(l > 0 for l in l_flts):
                    st.info(
                        "📈 **Nodo Repulsor (Fuente):** $\\lim_{t\\to +\\infty} \\|\\varphi(t)\\|^2 = \\infty$ y "
                        "$\\lim_{t\\to -\\infty} \\|\\varphi(t)\\|^2 = 0$. **Las soluciones nacen en el origen ($t\\to -\\infty$) y se alejan sin cota ($t\\to +\\infty$).**"
                    )
                elif all(l < 0 for l in l_flts):
                    st.info(
                        "📉 **Nodo Atractor (Sumidero):** $\\lim_{t\\to +\\infty} \\|\\varphi(t)\\|^2 = 0$ y "
                        "$\\lim_{t\\to -\\infty} \\|\\varphi(t)\\|^2 = \\infty$. **Las soluciones vienen desde el infinito ($t\\to -\\infty$) y tienden al origen ($t\\to +\\infty$).**"
                    )
                else:
                    st.info(
                        "🔀 **Punto Silla (Hiperbólico):** Tanto para $t\\to +\\infty$ como para $t\\to -\\infty$, "
                        "$\\|\\varphi(t)\\|^2 \\to \\infty$ (salvo sobre las variedades invariantes donde alguna constante es cero)."
                    )

                st.markdown("**3. Solución general en las coordenadas originales $\\varphi_A(t) = P\\varphi_\\Lambda(t)$:**")
                suma_vec_ltx = " + ".join(f"c_{{{i+1}}} e^{{{sp.latex(lams_r[i])}t}} " + sp.latex(vecs_r[i]) for i in range(dim_sys))
                st.latex(r"\varphi_A(t) = P\varphi_{\Lambda}(t) = " + suma_vec_ltx + " = " + sp.latex(phi_x))

            with t_r_paso4:
                if dim_sys == 2:
                    l1, l2 = lams_r[0], lams_r[1]
                    st.markdown("**1. Pendiente de los vectores tangentes en coordenadas canónicas ($m_y = \\dot{y}_2 / \\dot{y}_1$):**")
                    cociente_y = sp.simplify((l2 * cs_sym[1] * sp.exp(l2 * t_sym)) / (l1 * cs_sym[0] * sp.exp(l1 * t_sym))) if l1 != 0 else sp.oo
                    st.latex(r"m_y(t) = \frac{\dot{y}_2(t)}{\dot{y}_1(t)} = " + sp.latex(cociente_y))

                    dif_l = float(sp.N(l2 - l1))
                    if dif_l > 0:
                        dom_pos, dom_neg = "v_2", "v_1"
                        eje_pos, eje_neg = "y_2 (vertical)", "y_1 (horizontal)"
                    elif dif_l < 0:
                        dom_pos, dom_neg = "v_1", "v_2"
                        eje_pos, eje_neg = "y_1 (horizontal)", "y_2 (vertical)"
                    else:
                        dom_pos = dom_neg = "todo rayo"
                        eje_pos = eje_neg = "rectas por el origen"

                    st.markdown(
                        f"* **Cuando $t \\to +\\infty$:** domina el término asociado a $\\max(\\lambda_1, \\lambda_2)$. "
                        f"En el plano canónico las trayectorias se alinean con el eje **${eje_pos}$**, y en el plano original tienden paralelamente al subespacio propio **$\\langle {dom_pos} \\rangle$**.\n"
                        f"* **Cuando $t \\to -\\infty$:** domina el término asociado a $\\min(\\lambda_1, \\lambda_2)$. "
                        f"En el plano canónico las trayectorias son tangentes al eje **${eje_neg}$**, y en el plano original son tangentes al subespacio propio **$\\langle {dom_neg} \\rangle$**."
                    )

                    if l1 != 0:
                        exp_ratio = sp.simplify(l2 / l1)
                        st.markdown("**2. Ecuación cartesiana implícita de las curvas solución (eliminando $t$):**")
                        st.latex(
                            r"y_1(t) = c_1 e^{" + sp.latex(l1) + r"t} \implies y_2 = K \cdot y_1^{" + sp.latex(exp_ratio) + r"}"
                        )
                else:
                    st.markdown("**Análisis por Planos Invariantes en $\\mathbb{R}^3$ (anulando una constante a la vez):**")
                    planos_info = [
                        ("c_3 = 0", "y_1 y_2", "⟨v₁, v₂⟩", 0, 1),
                        ("c_2 = 0", "y_1 y_3", "⟨v₁, v₃⟩", 0, 2),
                        ("c_1 = 0", "y_2 y_3", "⟨v₂, v₃⟩", 1, 2),
                    ]
                    for cond_k, plano_y, gen_v, i_a, i_b in planos_info:
                        la_i, lb_i = lams_r[i_a], lams_r[i_b]
                        st.markdown(
                            f"- **Si ${cond_k}$:** $\\varphi_\\Lambda(t)$ está contenida en el plano coordenado **${plano_y}$** "
                            f"(y $\\varphi_A(t)$ está contenida en el plano invariante **${gen_v}$**), con valores propios "
                            f"$\\lambda_{{{i_a+1}}} = {sp.latex(la_i)}$ y $\\lambda_{{{i_b+1}}} = {sp.latex(lb_i)}$."
                        )

            with t_r_graf:
                if dim_sys == 2:
                    cg1, cg2 = st.columns(2)
                    with cg1:
                        fig_can = _retrato_2d_real(
                            sp.eye(2),
                            lams_r,
                            xl="y₁",
                            yl="y₂",
                            titulo="Plano Canónico ẏ = Λy",
                            eti_ejes=("Eje y₁", "Eje y₂"),
                        )
                        mostrar_figura_segura(fig_can)
                    with cg2:
                        fig_ori = _retrato_2d_real(
                            P_mat,
                            lams_r,
                            xl="x₁",
                            yl="x₂",
                            titulo="Plano Original ẋ = Ax (x = Py)",
                            eti_ejes=("⟨v₁⟩", "⟨v₂⟩"),
                        )
                        mostrar_figura_segura(fig_ori)
                else:
                    st.markdown("##### 1. Retratos de Fase en los 3 Planos Coordenados Invariantes ($c_3=0$, $c_2=0$, $c_1=0$)")
                    cp1, cp2, cp3 = st.columns(3)
                    with cp1:
                        f_p12 = _retrato_2d_real(
                            sp.eye(2),
                            (lams_r[0], lams_r[1]),
                            xl="y₁",
                            yl="y₂",
                            titulo="Plano y₁y₂ (c₃ = 0)",
                            eti_ejes=("y₁", "y₂"),
                        )
                        mostrar_figura_segura(f_p12)
                    with cp2:
                        f_p13 = _retrato_2d_real(
                            sp.eye(2),
                            (lams_r[0], lams_r[2]),
                            xl="y₁",
                            yl="y₃",
                            titulo="Plano y₁y₃ (c₂ = 0)",
                            eti_ejes=("y₁", "y₃"),
                        )
                        mostrar_figura_segura(f_p13)
                    with cp3:
                        f_p23 = _retrato_2d_real(
                            sp.eye(2),
                            (lams_r[1], lams_r[2]),
                            xl="y₂",
                            yl="y₃",
                            titulo="Plano y₂y₃ (c₁ = 0)",
                            eti_ejes=("y₂", "y₃"),
                        )
                        mostrar_figura_segura(f_p23)

                    st.divider()
                    st.markdown("##### 2. Retrato de Fase en $\\mathbb{R}^3$ ($\\dot{x} = Ax$ con Ejes Propios $\\langle v_1 \\rangle, \\langle v_2 \\rangle, \\langle v_3 \\rangle$)")
                    fig_3d_r = _retrato_3d_real(P_mat, lams_r, titulo="Espacio Original ℝ³ (x = Py)")
                    mostrar_figura_segura(fig_3d_r)

    # ======================================================================
    # RAMA B: RAÍCES COMPLEJAS (COMPLEJIFICACIÓN Y ECUACIÓN MODELO)
    # ======================================================================
    elif tiene_complejos:
        ev_complejo = None
        ev_real_3d = None
        for val, mult_a, vects in eigenvects_raw:
            if sp.im(val) > 0:
                ev_complejo = (sp.simplify(val), vects[0])
            elif sp.im(val) == 0:
                ev_real_3d = (sp.simplify(val), _limpiar_vector_propio(vects[0]))

        if ev_complejo is None:
            for val, mult_a, vects in eigenvects_raw:
                if sp.im(val) != 0:
                    ev_complejo = (sp.simplify(sp.conjugate(val)), vects[0].conjugate())
                    break

        lam_c, w1_raw = ev_complejo
        a_re = sp.simplify(sp.re(lam_c))
        b_im = sp.simplify(sp.im(lam_c))
        w1_vec = _limpiar_vector_propio(w1_raw)
        w2_vec = sp.simplify(w1_vec.conjugate())

        u1_vec = sp.Matrix([sp.simplify(sp.re(e)) for e in w1_vec])
        v1_vec = sp.Matrix([sp.simplify(sp.im(e)) for e in w1_vec])

        if dim_sys == 2:
            Pc_mat = sp.Matrix.hstack(w1_vec, w2_vec)
            Q_real = sp.Matrix.hstack(v1_vec, u1_vec)
        else:
            lam3_r, w3_vec = ev_real_3d
            Pc_mat = sp.Matrix.hstack(w1_vec, w2_vec, w3_vec)
            Q_real = sp.Matrix.hstack(v1_vec, u1_vec, w3_vec)

        Q_inv = calcular_con_limite(Q_real.inv, timeout=8)
        Lambda_modelo = sp.simplify(Q_inv * A_sp * Q_real)
        det_Q = sp.simplify(Q_real.det())

        with st.container(border=True):
            header_tarjeta("2. Resolución por Complejificación, Ecuación Modelo y Retratos de Fase")
            t_c1, t_c2, t_c3, t_c4 = st.tabs([
                "🔢 1. Complejificación (ẋ_c = A_c x_c) y Matriz P_c",
                "🪞 2. Condición de Realidad (x_c = x̄_c)",
                "🧭 3. Matriz Real Q y Ecuación Modelo (ż = Λz)",
                "🎨 4. Retratos de Fase (Plano Invariante, Espacio z y Espacio Original x)",
            ])

            with t_c1:
                st.markdown("**1. Vectores propios de la complejificación $\\dot{x}_c = A_c x_c$:**")
                st.latex(
                    "w_1 = " + sp.latex(w1_vec) + " = " + sp.latex(u1_vec) + " + i" + sp.latex(v1_vec)
                    + r", \qquad w_2 = \overline{w_1} = " + sp.latex(w2_vec)
                )
                if dim_sys == 3:
                    st.latex(r"\text{Para } \lambda_3 = " + sp.latex(ev_real_3d[0]) + r": \quad w_3 = " + sp.latex(ev_real_3d[1]))

                st.markdown("**2. Cambio de coordenadas complejo $P_c$ ($x_c = P_c y_c$) y solución de $\\dot{y}_c = \\Lambda_c y_c$:**")
                Lambda_c_diag = sp.diag(lam_c, sp.conjugate(lam_c)) if dim_sys == 2 else sp.diag(lam_c, sp.conjugate(lam_c), ev_real_3d[0])
                st.latex("P_c = " + sp.latex(Pc_mat) + r", \qquad \Lambda_c = P_c^{-1} A_c P_c = " + sp.latex(Lambda_c_diag))
                if dim_sys == 2:
                    st.latex(
                        r"y_c(t) = \begin{pmatrix} c_1 e^{(" + sp.latex(lam_c) + r")t} \\ c_2 e^{(" + sp.latex(sp.conjugate(lam_c))
                        + r")t} \end{pmatrix} \implies x_c(t) = c_1 e^{(" + sp.latex(lam_c) + r")t} w_1 + c_2 e^{(" + sp.latex(sp.conjugate(lam_c)) + r")t} \overline{w_1}"
                    )
                else:
                    st.latex(
                        r"x_c(t) = c_1 e^{(" + sp.latex(lam_c) + r")t} w_1 + c_2 e^{(" + sp.latex(sp.conjugate(lam_c))
                        + r")t} \overline{w_1} + c_3 e^{" + sp.latex(ev_real_3d[0]) + r"t} w_3"
                    )

            with t_c2:
                st.markdown("**Condición para obtener soluciones reales ($x_c(t) = \\overline{x_c(t)}$ $\\forall t \\in \\mathbb{R}$):**")
                st.markdown(
                    "Dado que $w_2 = \\overline{w_1}$ y $\\lambda_2 = \\overline{\\lambda_1}$, la solución $x_c(t)$ pertenece a $\\mathbb{R}^n$ "
                    "si y solo si **$c_2 = \\overline{c_1}$** (y $c_3 \\in \\mathbb{R}$ en $\\mathbb{R}^3$). "
                    "Aplicando $z + \\overline{z} = 2\\operatorname{Re}(z)$ y la fórmula de Euler $e^{(a+bi)t} = e^{at}(\\cos bt + i\\sin bt)$:"
                )
                st.latex(
                    r"x(t) = 2\operatorname{Re}\left(c_1 e^{(" + sp.latex(a_re) + " + " + sp.latex(b_im) + r"i)t} (u_1 + i v_1)\right)"
                    + (r" + c_3 e^{" + sp.latex(ev_real_3d[0]) + r"t} w_3" if dim_sys == 3 else "")
                )
                st.latex(
                    r"u_1 = \operatorname{Re}(w_1) = " + sp.latex(u1_vec)
                    + r", \qquad v_1 = \operatorname{Im}(w_1) = " + sp.latex(v1_vec)
                )

            with t_c3:
                st.markdown("**Matriz real de cambio de coordenadas $Q$ hacia la Ecuación Diferencial Modelo ($x = Qz \\iff z = Q^{-1}x$):**")
                st.latex(
                    "Q = " + sp.latex(Q_real) + r", \qquad Q^{-1} = " + sp.latex(Q_inv)
                    + r", \qquad \Lambda = Q^{-1}AQ = " + sp.latex(Lambda_modelo)
                )

                st.markdown("**Solución de la Ecuación Modelo $\\dot{z} = \\Lambda z$ ($\dot{r} = ar, \\; \\dot{\\theta} = b$) y Regreso $x(t) = Qz(t)$:**")
                exp_a_ltx = "e^{" + sp.latex(a_re) + "t}" if a_re != 0 else "1"
                if dim_sys == 2:
                    mat_rot_ltx = (
                        r"\begin{pmatrix} " + exp_a_ltx + r"\cos(" + sp.latex(b_im) + r"t) & -" + exp_a_ltx + r"\sin(" + sp.latex(b_im) + r"t) \\ "
                        + exp_a_ltx + r"\sin(" + sp.latex(b_im) + r"t) & " + exp_a_ltx + r"\cos(" + sp.latex(b_im) + r"t) \end{pmatrix}"
                    )
                    st.latex(r"\xi(t) = " + mat_rot_ltx + r"\begin{pmatrix} k_1 \\ k_2 \end{pmatrix}, \qquad x(t) = Q\,\xi(t)")
                    giro_ori = "antihorario (se mantiene el sentido porque det(Q) > 0)" if float(sp.N(det_Q)) > 0 else "horario (se invierte el sentido porque det(Q) < 0)"
                    st.info(
                        f"**Sentido de giro y curvas guía:** $\\det(Q) = {sp.latex(det_Q)}$. "
                        f"En el plano modelo $\\xi$ las trayectorias giran en sentido antihorario ($b > 0$); al aplicar $Q$, en el plano original $x$ el giro es **{giro_ori}**. "
                        "Las circunferencias guía $\\xi_1^2 + \\xi_2^2 = r^2$ se transforman en las elipses inclinadas $\\|Q^{-1}x\\|^2 = r^2$."
                    )
                else:
                    mat_rot_3d = (
                        r"\begin{pmatrix} " + exp_a_ltx + r"\cos(" + sp.latex(b_im) + r"t) & -" + exp_a_ltx + r"\sin(" + sp.latex(b_im) + r"t) & 0 \\ "
                        + exp_a_ltx + r"\sin(" + sp.latex(b_im) + r"t) & " + exp_a_ltx + r"\cos(" + sp.latex(b_im) + r"t) & 0 \\ "
                        + r"0 & 0 & e^{" + sp.latex(ev_real_3d[0]) + r"t} \end{pmatrix}"
                    )
                    st.latex(r"z(t) = " + mat_rot_3d + r"\begin{pmatrix} k_1 \\ k_2 \\ k_3 \end{pmatrix}, \qquad x(t) = Q\,z(t)")

            with t_c4:
                a_flt = float(sp.N(a_re))
                b_flt = float(sp.N(b_im))
                if dim_sys == 2:
                    cg1, cg2 = st.columns(2)
                    with cg1:
                        fig_mod = _retrato_2d_complejo(
                            a_flt,
                            b_flt,
                            Q_mat=None,
                            xl="ξ₁",
                            yl="ξ₂",
                            titulo=f"Plano Modelo ξ̇ = Λξ (a={a_flt:g}, b={b_flt:g})",
                        )
                        mostrar_figura_segura(fig_mod)
                    with cg2:
                        fig_ori_c = _retrato_2d_complejo(
                            a_flt,
                            b_flt,
                            Q_mat=Q_real,
                            xl="x₁",
                            yl="x₂",
                            titulo="Plano Original ẋ = Ax (x = Qξ con elipses guía)",
                        )
                        mostrar_figura_segura(fig_ori_c)
                else:
                    l3_flt = float(sp.N(ev_real_3d[0]))
                    st.markdown("##### 1. Plano Invariante $z_3 = 0$ (2D) y Retrato de las Fases para $z$ ($\dot{z} = \\Lambda z$ en $\\mathbb{R}^3$)")
                    cg1, cg2 = st.columns(2)
                    with cg1:
                        fig_z3_0 = _retrato_2d_complejo(
                            a_flt,
                            b_flt,
                            Q_mat=None,
                            xl="z₁",
                            yl="z₂",
                            titulo="Plano Invariante z₃ = 0 (en ℝ²)",
                        )
                        mostrar_figura_segura(fig_z3_0)
                    with cg2:
                        fig_3d_z = _retrato_3d_resorte_complejo(
                            a_flt,
                            b_flt,
                            l3_flt,
                            Q_mat=None,
                            titulo="Retrato de las Fases para z (ż = Λz en ℝ³)",
                        )
                        mostrar_figura_segura(fig_3d_z)

                    st.divider()
                    st.markdown("##### 2. Retrato de las Fases para la Ecuación Original $x = Qz$ ($\dot{x} = Ax$ en $\\mathbb{R}^3$)")
                    fig_3d_x = _retrato_3d_resorte_complejo(
                        a_flt,
                        b_flt,
                        l3_flt,
                        Q_mat=Q_real,
                        titulo="Espacio Original ℝ³ (x = Qz: Resorte alrededor de ⟨w₃⟩ y plano ⟨u₁, v₁⟩)",
                    )
                    mostrar_figura_segura(fig_3d_x)

    # ======================================================================
    # RAMA C: CASO NO DIAGONALIZABLE (FORMA DE JORDAN)
    # ======================================================================
    else:
        with st.container(border=True):
            header_tarjeta("2. Sistema No Diagonalizable (Forma Canónica de Jordan)")
            st.warning("La multiplicidad geométrica es menor que la algebraica; las soluciones contienen términos seculares $t e^{\\lambda t}$.")
            P_jord, J_mat = calcular_con_limite(A_sp.jordan_form, timeout=8)
            st.latex("P = " + sp.latex(P_jord) + r", \qquad J = P^{-1}AP = " + sp.latex(J_mat))
            exp_At = sp.simplify(P_jord * sp.exp(J_mat * t_sym) * P_jord.inv())
            st.markdown("**Matriz Exponencial Fundamental $e^{At}$:**")
            imprimir_matriz_simbolica(exp_At)


# ==============================================================================
# PESTAÑA 2: EDOS DE PRIMER ORDEN CON TECLADO MATEMÁTICO
# ==============================================================================
with tab_edo1:
    c_e1, c_e2 = st.columns([1.05, 1.25], gap="large")
    with c_e1:
        with st.container(border=True):
            header_tarjeta("Resolución Analítica de EDO de 1.º Orden y' = f(x, y)")
            st.caption("Escribe el lado derecho $f(x, y)$ con el teclado matemático y pulsa **↵**.")
            latex_edo1 = teclado_matematico(
                "kb_edo1_rhs",
                layout="edo",
                valor_inicial="x-y",
                placeholder="Escribe f(x, y) y pulsa ↵",
                acoplado=False,
            )

            usar_pvi = st.checkbox("Resolver Problema de Valor Inicial (PVI): y(x₀) = y₀", value=True, key="edo1_pvi_chk")
            if usar_pvi:
                cp1, cp2 = st.columns(2)
                x0_e1 = cp1.number_input("x₀:", value=0.0, step=0.5, key="edo1_x0")
                y0_e1 = cp2.number_input("y₀:", value=2.0, step=0.5, key="edo1_y0")

    f_rhs = None
    if latex_edo1:
        try:
            obj_e1 = latex_a_sympy(latex_edo1)
            if isinstance(obj_e1, sp.Eq):
                f_rhs = obj_e1.rhs
            elif isinstance(obj_e1, sp.Expr):
                f_rhs = obj_e1
            else:
                st.error("Escribe una expresión algebraica en términos de x e y.")
        except (ErrorLatex, ErrorNoSoportado) as e:
            st.error("No pude interpretar la expresión: " + str(e))

    if f_rhs is not None:
        x_s = sp.Symbol("x", real=True)
        y_s = sp.Symbol("y", real=True)
        y_fn = sp.Function("y")(x_s)
        f_sub = f_rhs.subs({s: (x_s if s.name == "x" else y_s if s.name == "y" else s) for s in f_rhs.free_symbols})
        eq_diff1 = sp.Eq(sp.diff(y_fn, x_s), f_sub.subs(y_s, y_fn))

        with c_e1:
            with st.container(border=True):
                subheader_tarjeta("Clasificación y Solución Simbólica")
                st.markdown("**Entiendo:** $y'(x) = " + sp.latex(f_sub) + "$ (" + leer_en_espanol(f_sub) + ")")
                try:
                    tipos_edo = sp.classify_ode(eq_diff1, y_fn)
                    if tipos_edo:
                        st.info("**Clasificación:** `" + ", ".join(tipos_edo[:3]) + "`")
                    sol_gen = calcular_con_limite(sp.dsolve, args=(eq_diff1, y_fn), timeout=8)
                    st.markdown("**Solución General:**")
                    st.latex(sp.latex(sol_gen))

                    sol_pvi_expr = None
                    if usar_pvi:
                        sol_pvi = calcular_con_limite(
                            sp.dsolve,
                            args=(eq_diff1, y_fn),
                            kwargs={"ics": {y_fn.subs(x_s, sp.nsimplify(x0_e1)): sp.nsimplify(y0_e1)}},
                            timeout=8,
                        )
                        st.markdown(f"**Solución Particular para $y({x0_e1:g}) = {y0_e1:g}$:**")
                        st.latex(sp.latex(sol_pvi))
                        if isinstance(sol_pvi, sp.Eq) and sol_pvi.lhs == y_fn:
                            sol_pvi_expr = sol_pvi.rhs
                except Exception as e:
                    st.warning("No se encontró solución cerrada elemental; se grafica el campo de direcciones. (" + str(e) + ")")
                    sol_pvi_expr = None

        with c_e2:
            with st.container(border=True):
                header_tarjeta("Campo de Direcciones y Curva Solución")
                fig_d, ax_d = _lienzo_fase_2d(lim=4.5, xlabel="x", ylabel="y", titulo="Campo de Pendientes dy/dx = f(x, y)")
                xg = np.linspace(-4.2, 4.2, 19)
                yg = np.linspace(-4.2, 4.2, 19)
                Xg, Yg = np.meshgrid(xg, yg)
                try:
                    f_num = sp.lambdify((x_s, y_s), f_sub, "numpy")
                    with np.errstate(all="ignore"):
                        slopes = np.broadcast_to(np.asarray(f_num(Xg, Yg), dtype=float), Xg.shape)
                    norm_s = np.hypot(1.0, slopes)
                    dx_s = 1.0 / norm_s
                    dy_s = slopes / norm_s
                    ax_d.quiver(Xg, Yg, dx_s, dy_s, color=OSCURO, alpha=0.45, pivot="mid", headwidth=3, scale=26, zorder=3)
                except Exception:
                    pass

                if usar_pvi and sol_pvi_expr is not None:
                    try:
                        y_pvi_fn = sp.lambdify(x_s, sol_pvi_expr, "numpy")
                        xs_c = np.linspace(-4.3, 4.3, 350)
                        with np.errstate(all="ignore"):
                            ys_c = np.asarray(y_pvi_fn(xs_c), dtype=float)
                        mask_c = np.isfinite(ys_c) & (np.abs(ys_c) <= 4.4)
                        ax_d.plot(xs_c[mask_c], ys_c[mask_c], color=AZUL, lw=2.6, label=f"Solución PVI y({x0_e1:g})={y0_e1:g}", zorder=6)
                        ax_d.plot([x0_e1], [y0_e1], "o", color=ROJO, ms=7.5, zorder=7)
                        ax_d.legend(loc="upper right", fontsize=8.5)
                    except Exception:
                        pass
                mostrar_figura_segura(fig_d)


# ==============================================================================
# PESTAÑA 3: EDOS LINEALES DE 2.º ORDEN Y LAPLACE CON TECLADO MATEMÁTICO
# ==============================================================================
with tab_edo2:
    c_l1, c_l2 = st.columns(2, gap="large")

    with c_l1:
        with st.container(border=True):
            header_tarjeta("1. EDO Lineal de 2.º Orden: a·y'' + b·y' + c·y = g(t)")
            k1, k2, k3 = st.columns(3)
            a_o2 = k1.number_input("Coeficiente a (≠ 0):", value=1.0, step=0.5, key="o2_a")
            b_o2 = k2.number_input("Coeficiente b:", value=2.0, step=0.5, key="o2_b")
            c_o2 = k3.number_input("Coeficiente c:", value=5.0, step=0.5, key="o2_c")

            st.caption("Escribe el término no homogéneo $g(t)$ (en variable $t$ o $x$) con el teclado matemático y pulsa **↵**:")
            lat_g_o2 = teclado_matematico(
                "kb_edo2_g",
                layout="edo",
                valor_inicial="0",
                placeholder="Escribe g(t) y pulsa ↵",
                acoplado=True,
            )

            if abs(a_o2) < 1e-12:
                st.error("El coeficiente principal 'a' debe ser distinto de cero.")
            elif lat_g_o2:
                try:
                    g_raw = latex_a_sympy(lat_g_o2)
                    if isinstance(g_raw, sp.Expr):
                        t_s = sp.Symbol("t", real=True)
                        y_f = sp.Function("y")(t_s)
                        g_expr = g_raw.subs({s: t_s for s in g_raw.free_symbols if s.name in ("t", "x")})
                        eq_o2 = sp.Eq(
                            sp.nsimplify(a_o2) * sp.diff(y_f, t_s, 2)
                            + sp.nsimplify(b_o2) * sp.diff(y_f, t_s)
                            + sp.nsimplify(c_o2) * y_f,
                            g_expr,
                        )
                        disc_o2 = b_o2**2 - 4 * a_o2 * c_o2
                        reg_osc = (
                            "Subamortiguado (Raíces complejas conjugadas)" if disc_o2 < -1e-9
                            else "Críticamente amortiguado (Raíz real repetida)" if abs(disc_o2) <= 1e-9
                            else "Sobreamortiguado (Dos raíces reales distintas)"
                        )
                        st.markdown("**Ecuación planteada:**")
                        st.latex(sp.latex(eq_o2))
                        st.info(f"**Discriminante $\\Delta = b^2 - 4ac = {disc_o2:.3f}$:** {reg_osc}")
                        sol_o2 = calcular_con_limite(sp.dsolve, args=(eq_o2, y_f), timeout=8)
                        st.markdown("**Solución General $y(t)$:**")
                        st.latex(sp.latex(sol_o2))
                except (ErrorLatex, ErrorNoSoportado) as e:
                    st.error("Error en g(t): " + str(e))

    with c_l2:
        with st.container(border=True):
            header_tarjeta("2. Transformada de Laplace Directa ℒ{f(t)} e Inversa ℒ⁻¹{F(s)}")
            modo_lap = st.radio(
                "Operación:",
                ["Transformada Directa ℒ{f(t)}(s)", "Transformada Inversa ℒ⁻¹{F(s)}(t)"],
                horizontal=True,
                key="lap_modo",
            )
            t_s = sp.Symbol("t", positive=True)
            s_s = sp.Symbol("s")

            if modo_lap.startswith("Transformada Directa"):
                st.caption("Escribe $f(t)$ en variable $t$ (o $x$) con el teclado matemático y pulsa **↵**:")
                lat_f_lap = teclado_matematico(
                    "kb_lap_dir",
                    layout="edo",
                    valor_inicial=r"\exponentialE^{-2t}\cos\left(3t\right)",
                    placeholder="Escribe f(t) y pulsa ↵",
                    acoplado=True,
                )
                if lat_f_lap:
                    try:
                        f_l = latex_a_sympy(lat_f_lap)
                        if isinstance(f_l, sp.Expr):
                            f_l = f_l.subs({sym: t_s for sym in f_l.free_symbols if sym.name in ("t", "x")})
                            st.caption("Entiendo: " + leer_en_espanol(f_l))
                            F_s = calcular_con_limite(sp.laplace_transform, args=(f_l, t_s, s_s), kwargs={"noconds": True}, timeout=8)
                            st.latex(r"\mathcal{L}\left\{" + sp.latex(f_l) + r"\right\}(s) = " + sp.latex(sp.simplify(F_s)))
                    except (ErrorLatex, ErrorNoSoportado) as e:
                        st.error("Error al interpretar f(t): " + str(e))
            else:
                st.caption("Escribe $F(s)$ en variable $s$ con el teclado matemático y pulsa **↵**:")
                lat_F_lap = teclado_matematico(
                    "kb_lap_inv",
                    layout="edo",
                    valor_inicial=r"\frac{1}{s^{2}+4s+13}",
                    placeholder="Escribe F(s) y pulsa ↵",
                    acoplado=False,
                )
                if lat_F_lap:
                    try:
                        F_l = latex_a_sympy(lat_F_lap)
                        if isinstance(F_l, sp.Expr):
                            F_l = F_l.subs({sym: s_s for sym in F_l.free_symbols if sym.name in ("s", "x")})
                            st.caption("Entiendo: " + leer_en_espanol(F_l))
                            f_t = calcular_con_limite(sp.inverse_laplace_transform, args=(F_l, s_s, t_s), timeout=8)
                            st.latex(r"\mathcal{L}^{-1}\left\{" + sp.latex(F_l) + r"\right\}(t) = " + sp.latex(sp.simplify(f_t)))
                    except (ErrorLatex, ErrorNoSoportado) as e:
                        st.error("Error al interpretar F(s): " + str(e))
