# pages/7_Ecuaciones_Diferenciales.py
import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.ticker import AutoMinorLocator

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(
    page_title="Ecuaciones Diferenciales - MATHESIS",
    page_icon="🌀",
    layout="wide",
)

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import (  # noqa: E402
    calcular_con_limite,
    imprimir_matriz_simbolica,
    inicializar_estado,
    leer_expresion_st,
    mostrar_figura_segura,
)

cargar_estilos_globales()
inicializar_estado()

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
# UTILIDADES MATEMÁTICAS Y DE TRAZADO ANALÍTICO LIMPIO
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


def _lienzo_fase_2d(w=5.8, h=5.4, lim=4.0, xlabel="x₁", ylabel="x₂", titulo=""):
    """Crea un lienzo limpio con cuadrícula principal y secundaria y ejes cartesianos."""
    fig, ax = plt.subplots(figsize=(w, h), dpi=110, facecolor=FONDO)
    ax.set_facecolor("#fbfdff")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color="#cbd5e1", lw=0.95, alpha=0.95)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.55, alpha=0.85)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)

    ax.annotate(
        "",
        xy=(lim * 0.98, 0),
        xytext=(-lim * 0.98, 0),
        arrowprops=dict(arrowstyle="->", color=CIAN_EJE, lw=1.8, mutation_scale=15),
        zorder=2,
    )
    ax.annotate(
        "",
        xy=(0, lim * 0.98),
        xytext=(0, -lim * 0.98),
        arrowprops=dict(arrowstyle="->", color=CIAN_EJE, lw=1.8, mutation_scale=15),
        zorder=2,
    )
    ax.text(lim * 0.91, -lim * 0.08, xlabel, fontsize=10.5, fontweight="bold", color=OSCURO)
    ax.text(lim * 0.04, lim * 0.90, ylabel, fontsize=10.5, fontweight="bold", color=OSCURO)
    ax.tick_params(colors=OSCURO, labelsize=8)
    if titulo:
        ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=OSCURO, pad=8)
    return fig, ax


def _trazar_curva_con_flechas(ax, xs, ys, color, n_flechas=3, lw=2.0):
    """Dibuja una trayectoria paramétrica y coloca puntas de flecha limpias según la dirección del flujo."""
    ax.plot(xs, ys, color=color, lw=lw, zorder=4)
    n_pts = len(xs)
    if n_pts < 12:
        return
    ds = np.hypot(np.diff(xs), np.diff(ys))
    s_acum = np.concatenate([[0.0], np.cumsum(ds)])
    l_total = s_acum[-1]
    if l_total < 0.25:
        return
    fracciones = np.linspace(0.22, 0.78, n_flechas)
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
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, mutation_scale=13),
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
    ax.plot([-L * ux, L * ux], [-L * uy, L * uy], color=color, lw=2.3, zorder=3, label=f"{etiqueta} (λ={lam_val:g})")

    if abs(lam_val) > 1e-9:
        for signo_rama in (1.0, -1.0):
            for r_pos in (0.38 * L, 0.72 * L):
                x_base = signo_rama * r_pos * ux
                y_base = signo_rama * r_pos * uy
                sentido = 1.0 if lam_val > 0 else -1.0
                paso = 0.08 * L * sentido * signo_rama
                ax.annotate(
                    "",
                    xy=(x_base + paso * ux, y_base + paso * uy),
                    xytext=(x_base, y_base),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.2, mutation_scale=14),
                    zorder=6,
                )
    ax.text(L * ux * 0.84, L * uy * 0.84 + 0.18, etiqueta, color=color, fontweight="bold", fontsize=9.5, zorder=7)


def _retrato_2d_real(P_trans, lams, lim=4.0, xl="y₁", yl="y₂", titulo="", eti_ejes=("y₁", "y₂")):
    """Retrato de fase 2D exacto mediante curvas paramétricas analíticas."""
    fig, ax = _lienzo_fase_2d(lim=lim, xlabel=xl, ylabel=yl, titulo=titulo)
    lam1, lam2 = float(lams[0]), float(lams[1])
    P_np = np.array(P_trans, dtype=float)
    escala_p = max(np.linalg.norm(P_np[:, 0]), np.linalg.norm(P_np[:, 1]), 1.0)
    lim_eff = lim * (escala_p * 0.85 if escala_p > 1.2 else 1.0)
    ax.set_xlim(-lim_eff, lim_eff)
    ax.set_ylim(-lim_eff, lim_eff)

    _dibujar_subespacio_invariante(ax, P_np[:, 0], lam1, lim_eff, eti_ejes[0], color=ROSA_EJE)
    _dibujar_subespacio_invariante(ax, P_np[:, 1], lam2, lim_eff, eti_ejes[1], color=LIMA_EJE)
    ax.plot([0], [0], "o", color=ROJO, ms=6.5, zorder=8)

    escala_t = 1.0 / max(abs(lam1), abs(lam2), 0.5)
    ts = np.linspace(-2.5 * escala_t, 2.5 * escala_t, 280)

    if lam1 * lam2 < 0:
        semillas_y = [(sx * c, sy * c) for sx in (-1, 1) for sy in (-1, 1) for c in (0.65, 1.35)]
    else:
        semillas_y = [(sx * 1.5, sy * c) for sx in (-1, 1) for sy in (-1, 1) for c in (0.45, 1.15, 2.2)]

    for c1, c2 in semillas_y:
        y1_t = c1 * np.exp(lam1 * ts)
        y2_t = c2 * np.exp(lam2 * ts)
        pts_x = P_np @ np.vstack([y1_t, y2_t])
        mask = (np.abs(pts_x[0]) <= lim_eff * 0.94) & (np.abs(pts_x[1]) <= lim_eff * 0.94)
        if np.sum(mask) > 15:
            _trazar_curva_con_flechas(ax, pts_x[0, mask], pts_x[1, mask], color=MORADO, n_flechas=2, lw=1.85)

    ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)
    return fig


def _retrato_2d_complejo(a_re, b_im, Q_mat=None, lim=4.0, xl="ξ₁", yl="ξ₂", titulo=""):
    """Retrato de fase 2D para raíces complejas con círculos/elipses guía y vectores de la base real Q."""
    fig, ax = _lienzo_fase_2d(lim=lim, xlabel=xl, ylabel=yl, titulo=titulo)
    Q_np = np.eye(2) if Q_mat is None else np.array(Q_mat, dtype=float)
    escala_q = max(np.linalg.norm(Q_np[:, 0]), np.linalg.norm(Q_np[:, 1]), 1.0)
    lim_eff = lim * (escala_q * 0.9 if Q_mat is not None else 1.0)
    ax.set_xlim(-lim_eff, lim_eff)
    ax.set_ylim(-lim_eff, lim_eff)

    ang_g = np.linspace(0, 2 * np.pi, 240)
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

    T_vuelta = 2 * math.pi / max(abs(b_im), 0.2)
    if abs(a_re) < 1e-7:
        ts = np.linspace(0, T_vuelta, 260)
        semillas = [(1.0, 0.0), (1.9, 0.0), (2.8, 0.0)]
    else:
        t_max = min(1.8 * T_vuelta, 2.2 / abs(a_re))
        ts = np.linspace(-t_max, t_max, 420)
        semillas = [(1.2, 0.0), (-1.2, 0.0)]

    for k1, k2 in semillas:
        exp_at = np.exp(a_re * ts)
        xi1 = exp_at * (k1 * np.cos(b_im * ts) - k2 * np.sin(b_im * ts))
        xi2 = exp_at * (k1 * np.sin(b_im * ts) + k2 * np.cos(b_im * ts))
        pts_x = Q_np @ np.vstack([xi1, xi2])
        mask = (np.abs(pts_x[0]) <= lim_eff * 0.94) & (np.abs(pts_x[1]) <= lim_eff * 0.94)
        if np.sum(mask) > 20:
            _trazar_curva_con_flechas(ax, pts_x[0, mask], pts_x[1, mask], color=AZUL, n_flechas=5, lw=2.0)

    ax.plot([0], [0], "o", color=ROJO, ms=6.5, zorder=8)
    if Q_mat is not None:
        ax.legend(loc="upper right", fontsize=8.0, framealpha=0.92)
    return fig


def _retrato_3d_completo(P_o_Q, lams_info, modo="real", titulo="Retrato de Fase en ℝ³"):
    """Dibuja el retrato de fase 3D con los subespacios propios y las curvas/hélices solución."""
    fig = plt.figure(figsize=(6.8, 5.6), dpi=110, facecolor=FONDO)
    ax = fig.add_subplot(111, projection="3d")
    M_np = np.array(P_o_Q, dtype=float)
    escala = max(np.max(np.abs(M_np)), 1.5) * 2.2

    ax.set_xlim(-escala, escala)
    ax.set_ylim(-escala, escala)
    ax.set_zlim(-escala, escala)
    ax.set_xlabel("x₁", fontweight="bold")
    ax.set_ylabel("x₂", fontweight="bold")
    ax.set_zlabel("x₃", fontweight="bold")
    ax.view_init(elev=22, azim=-52)
    ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=OSCURO)

    if modo == "real":
        l1, l2, l3 = [float(x) for x in lams_info]
        colores_v = [ROSA_EJE, LIMA_EJE, CIAN_EJE]
        for idx, (lam_i, col_i) in enumerate(zip((l1, l2, l3), colores_v)):
            vi = M_np[:, idx]
            vi_u = vi / (np.linalg.norm(vi) or 1.0) * (escala * 0.85)
            ax.plot([-vi_u[0], vi_u[0]], [-vi_u[1], vi_u[1]], [-vi_u[2], vi_u[2]], color=col_i, lw=2.3, label=f"⟨v_{idx+1}⟩ (λ={lam_i:g})")

        t_esc = 1.0 / max(abs(l1), abs(l2), abs(l3), 0.5)
        ts = np.linspace(-2.0 * t_esc, 2.0 * t_esc, 220)
        for s1, s2, s3 in [(1, 1, 1), (-1, 1, 1), (1, -1, -1), (-1, -1, 1), (1, 1, -1), (-1, 1, -1)]:
            y_t = np.vstack([0.7 * s1 * np.exp(l1 * ts), 0.7 * s2 * np.exp(l2 * ts), 0.7 * s3 * np.exp(l3 * ts)])
            x_t = M_np @ y_t
            mask = np.max(np.abs(x_t), axis=0) <= escala * 0.95
            if np.sum(mask) > 10:
                ax.plot(x_t[0, mask], x_t[1, mask], x_t[2, mask], color=MORADO, lw=1.7, alpha=0.85)
    else:
        a_re, b_im, l3 = [float(x) for x in lams_info]
        v1_col, u1_col, w3_col = M_np[:, 0], M_np[:, 1], M_np[:, 2]
        w3_u = w3_col / (np.linalg.norm(w3_col) or 1.0) * (escala * 0.88)
        ax.plot([-w3_u[0], w3_u[0]], [-w3_u[1], w3_u[1]], [-w3_u[2], w3_u[2]], color=ROSA_EJE, lw=2.6, label=f"Eje ⟨w₃⟩ (λ₃={l3:g})")
        ax.quiver(0, 0, 0, u1_col[0], u1_col[1], u1_col[2], color=VERDE, lw=2.2, label="u₁ = Re(w₁)")
        ax.quiver(0, 0, 0, v1_col[0], v1_col[1], v1_col[2], color=NARANJA, lw=2.2, label="v₁ = Im(w₁)")

        T_v = 2 * math.pi / max(abs(b_im), 0.5)
        ts = np.linspace(-1.6 * T_v, 1.6 * T_v, 450)
        for s_z in (1.0, -1.0):
            r_t = 0.65 * np.exp(a_re * ts)
            z1 = r_t * np.cos(b_im * ts)
            z2 = r_t * np.sin(b_im * ts)
            z3 = 0.55 * s_z * np.exp(l3 * ts)
            x_t = M_np @ np.vstack([z1, z2, z3])
            mask = np.max(np.abs(x_t), axis=0) <= escala * 0.95
            if np.sum(mask) > 15:
                ax.plot(x_t[0, mask], x_t[1, mask], x_t[2, mask], color=AZUL, lw=2.0)

    ax.scatter([0], [0], [0], color=ROJO, s=45)
    ax.legend(loc="upper left", fontsize=8.0)
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
# PESTAÑA 1: SISTEMAS LINEALES X' = A X EN R^2 Y R^3
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

        A_sp = None
        error_mat_edo = False

        if fuente_mat == "Importar desde el Inventario de Matrices":
            mats_compatibles = {
                k: v for k, v in st.session_state.get("mis_matrices", {}).items()
                if v.shape == (dim_sys, dim_sys) and not v.free_symbols and not v.has(sp.I)
            }
            if mats_compatibles:
                nom_m_imp = st.selectbox("Seleccione matriz cuadrada del inventario:", list(mats_compatibles.keys()), key="edo_imp_sel")
                A_sp = mats_compatibles[nom_m_imp]
            else:
                st.info(f"No hay matrices numéricas reales de tamaño {dim_sys}×{dim_sys} en el inventario. Ingrese la matriz manualmente.")

        if A_sp is None:
            valores_def_2x2 = [["-2", "-2"], ["6", "5"]]
            valores_def_3x3 = [["8", "-2", "2"], ["-3", "7", "-12"], ["0", "0", "-5"]]
            plantilla = valores_def_2x2 if dim_sys == 2 else valores_def_3x3

            matriz_input = []
            for i in range(dim_sys):
                cols_m = st.columns(dim_sys)
                fila_m = []
                for j in range(dim_sys):
                    with cols_m[j]:
                        celda_txt = st.text_input(
                            f"a_({i+1},{j+1})",
                            value=plantilla[i][j],
                            key=f"edo_cell_{dim_sys}_{i}_{j}",
                        )
                        val_p = leer_expresion_st(celda_txt, solo_reales=True)
                        if val_p is None or val_p.free_symbols:
                            error_mat_edo = True
                        else:
                            fila_m.append(val_p)
                matriz_input.append(fila_m)
            if not error_mat_edo:
                A_sp = sp.Matrix(matriz_input)

    if error_mat_edo or A_sp is None:
        st.error("⛔ Ingrese valores numéricos reales válidos en todas las entradas de la matriz A.")
    else:
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
                st.markdown("**Polinomio Característico $P_A(\\lambda)$ y Raíces:**")
                st.latex("P_A(\\lambda) = " + sp.latex(char_poly.as_expr()) + " = " + sp.latex(sp.factor(char_poly.as_expr())))
                raices_ltx = [
                    r"\lambda = " + sp.latex(sp.simplify(val)) + " \\;(\\text{mult. } " + str(mult_a) + ")"
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
                            "$\\|\\varphi(t)\\|^2 \\to \\infty$ (salvo sobre las variedades estables/inestables donde una constante es cero)."
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
                        fig_3d_r = _retrato_3d_completo(P_mat, lams_r, modo="real", titulo="Espacio Original ℝ³ (x = Py)")
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
                    "🧭 3. Matriz Real Q y Ecuación Modelo (ξ̇ = Λξ)",
                    "🎨 4. Retratos de Fase (Plano Modelo y Original)",
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
                        "Dado que $w_2 = \\overline{w_1}$ y $\\lambda_2 = \\overline{\\lambda_1}$, la solución $x_c(t)$ es real "
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
                    st.markdown("**Matriz real de cambio de coordenadas $Q = [\\operatorname{Im}(w_1) \\mid \\operatorname{Re}(w_1)]$ ($x = Q\\xi \\iff \\xi = Q^{-1}x$):**")
                    st.latex(
                        "Q = " + sp.latex(Q_real) + r", \qquad Q^{-1} = " + sp.latex(Q_inv)
                        + r", \qquad \Lambda = Q^{-1}AQ = " + sp.latex(Lambda_modelo)
                    )

                    st.markdown("**Solución de la Ecuación Diferencial Modelo $\\dot{\\xi} = \\Lambda\\xi$ ($\dot{r} = ar, \\; \\dot{\\theta} = b$) y Regreso $x(t) = Q\\xi(t)$:**")
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
                        cg1, cg2 = st.columns(2)
                        with cg1:
                            fig_z3_0 = _retrato_2d_complejo(
                                a_flt,
                                b_flt,
                                Q_mat=None,
                                xl="z₁",
                                yl="z₂",
                                titulo="Plano Invariante Modelo z₃ = 0",
                            )
                            mostrar_figura_segura(fig_z3_0)
                        with cg2:
                            fig_3d_c = _retrato_3d_completo(
                                Q_real,
                                (a_flt, b_flt, l3_flt),
                                modo="complejo",
                                titulo="Espacio Original ℝ³ (Hélice alrededor de ⟨w₃⟩)",
                            )
                            mostrar_figura_segura(fig_3d_c)

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
# PESTAÑA 2: EDOS DE PRIMER ORDEN Y CAMPO DE DIRECCIONES
# ==============================================================================
with tab_edo1:
    c_e1, c_e2 = st.columns([1.05, 1.25], gap="large")
    with c_e1:
        with st.container(border=True):
            header_tarjeta("Resolución Analítica de EDO de 1.º Orden y' = f(x, y)")
            st.caption("Ejemplos: `x - y`, `x*y`, `y*(1 - y)`, `(x^2 + y^2)/(2*x*y)`.")
            f_edo1_str = st.text_input("Escriba f(x, y) para dy/dx = f(x, y):", value="x - y", key="edo1_rhs")
            usar_pvi = st.checkbox("Resolver Problema de Valor Inicial (PVI): y(x₀) = y₀", value=True, key="edo1_pvi_chk")
            if usar_pvi:
                cp1, cp2 = st.columns(2)
                x0_e1 = cp1.number_input("x₀:", value=0.0, step=0.5, key="edo1_x0")
                y0_e1 = cp2.number_input("y₀:", value=2.0, step=0.5, key="edo1_y0")

    f_rhs = leer_expresion_st(f_edo1_str, solo_reales=True)
    if f_rhs is not None:
        x_s = sp.Symbol("x", real=True)
        y_s = sp.Symbol("y", real=True)
        y_fn = sp.Function("y")(x_s)
        f_sub = f_rhs.subs({s: (x_s if s.name == "x" else y_s if s.name == "y" else s) for s in f_rhs.free_symbols})
        eq_diff1 = sp.Eq(sp.diff(y_fn, x_s), f_sub.subs(y_s, y_fn))

        with c_e1:
            with st.container(border=True):
                subheader_tarjeta("Clasificación y Solución Simbólica")
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
# PESTAÑA 3: EDOS LINEALES DE 2.º ORDEN Y TRANSFORMADA DE LAPLACE
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
            g_o2_str = st.text_input("Término no homogéneo g(t):", value="0", key="o2_g")

            if abs(a_o2) < 1e-12:
                st.error("El coeficiente principal 'a' debe ser distinto de cero.")
            else:
                t_s = sp.Symbol("t", real=True)
                y_f = sp.Function("y")(t_s)
                g_expr = leer_expresion_st(g_o2_str, solo_reales=True)
                if g_expr is not None:
                    g_expr = g_expr.subs({s: t_s for s in g_expr.free_symbols if s.name == "t"})
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
                    st.info(f"**Discriminante $\\Delta = b^2 - 4ac = {disc_o2:.3f}$:** {reg_osc}")
                    sol_o2 = calcular_con_limite(sp.dsolve, args=(eq_o2, y_f), timeout=8)
                    st.latex(sp.latex(sol_o2))

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
                f_lap_str = st.text_input("Función temporal f(t) (Ej: exp(-2*t)*cos(3*t)):", value="exp(-2*t)*cos(3*t)", key="lap_f_in")
                f_l = leer_expresion_st(f_lap_str)
                if f_l is not None:
                    f_l = f_l.subs({sym: t_s for sym in f_l.free_symbols if sym.name == "t"})
                    F_s = calcular_con_limite(sp.laplace_transform, args=(f_l, t_s, s_s), kwargs={"noconds": True}, timeout=8)
                    st.latex(r"\mathcal{L}\left\{" + sp.latex(f_l) + r"\right\}(s) = " + sp.latex(sp.simplify(F_s)))
            else:
                F_lap_str = st.text_input("Función en frecuencia F(s) (Ej: 1/(s^2 + 4*s + 13)):", value="1/(s^2 + 4*s + 13)", key="lap_F_in")
                F_l = leer_expresion_st(F_lap_str)
                if F_l is not None:
                    F_l = F_l.subs({sym: s_s for sym in F_l.free_symbols if sym.name == "s"})
                    f_t = calcular_con_limite(sp.inverse_laplace_transform, args=(F_l, s_s, t_s), timeout=8)
                    st.latex(r"\mathcal{L}^{-1}\left\{" + sp.latex(F_l) + r"\right\}(t) = " + sp.latex(sp.simplify(f_t)))
