# pages/1_Geometria.py
import math
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

st.set_page_config(page_title="Geometría - MATHESIS", page_icon="📐", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, titulo_tarjeta  # noqa: E402
from utils import inicializar_estado, leer_expresion_st  # noqa: E402

try:
    from teclado_matematico import teclado_matematico
    from interprete_latex import latex_a_sympy, ErrorLatex
    _TIENE_TECLADO = True
except Exception:
    _TIENE_TECLADO = False

cargar_estilos_globales()
inicializar_estado()


# ==============================================================================
# UTILIDADES GRÁFICAS (SIN PYPLOT PARA EVITAR FUGAS DE MEMORIA)
# ==============================================================================
def _crear_fig_2d(w=6.5, h=4.5, titulo=""):
    fig = Figure(figsize=(w, h), dpi=110, layout="constrained")
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0f172a")
    ax.axhline(0, color="#64748b", lw=1, ls="--", alpha=0.7)
    ax.axvline(0, color="#64748b", lw=1, ls="--", alpha=0.7)
    ax.grid(True, ls=":", alpha=0.35, color="#334155")
    ax.tick_params(colors="#94a3b8", labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_color("#0284c7")
        spine.set_alpha(0.4)
    if titulo:
        ax.set_title(titulo, fontsize=11, fontweight="bold", color="#38bdf8")
    return fig, ax


def _crear_fig_3d(w=6.0, h=5.5, titulo=""):
    fig = Figure(figsize=(w, h), dpi=110, layout="constrained")
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0f172a")
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel("Eje X", color="#94a3b8")
    ax.set_ylabel("Eje Y", color="#94a3b8")
    ax.set_zlabel("Eje Z", color="#94a3b8")
    ax.tick_params(colors="#64748b", labelsize=8)
    if titulo:
        ax.set_title(titulo, fontsize=11, fontweight="bold", color="#38bdf8")
    return fig, ax


def renderizar_solido_3d(figura: str, params: dict):
    fig, ax = _crear_fig_3d(titulo=f"Modelo 3D: {figura}")
    color_cara = "#38bdf8"
    alfa = 0.58

    if figura == "Cilindro":
        r, h = params["r"], params["h"]
        z = np.linspace(0, h, 35)
        theta = np.linspace(0, 2 * np.pi, 35)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor="#0284c7", lw=0.4)
        lim = max(r, h / 2) * 1.2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(0, h * 1.1)

    elif figura == "Esfera":
        r = params["r"]
        u = np.linspace(0, 2 * np.pi, 35)
        v = np.linspace(0, np.pi, 35)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x, y, z, color=color_cara, alpha=alfa, edgecolor="#0284c7", lw=0.4)
        ax.set_xlim(-r * 1.2, r * 1.2)
        ax.set_ylim(-r * 1.2, r * 1.2)
        ax.set_zlim(-r * 1.2, r * 1.2)

    elif figura == "Cono":
        r, h = params["r"], params["h"]
        z = np.linspace(0, h, 35)
        theta = np.linspace(0, 2 * np.pi, 35)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r_grid = r * (1 - z_grid / h)
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor="#0284c7", lw=0.4)
        lim = max(r, h / 2) * 1.2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(0, h * 1.1)

    elif figura == "Pirámide cuadrangular":
        b, h = params["b"], params["h"]
        Z = np.array([[-b / 2, -b / 2, 0], [b / 2, -b / 2, 0], [b / 2, b / 2, 0], [-b / 2, b / 2, 0], [0, 0, h]])
        caras = [
            [Z[0], Z[1], Z[2], Z[3]],
            [Z[0], Z[1], Z[4]],
            [Z[1], Z[2], Z[4]],
            [Z[2], Z[3], Z[4]],
            [Z[3], Z[0], Z[4]],
        ]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors="#0284c7", lw=1.2))
        ax.set_xlim([-b, b])
        ax.set_ylim([-b, b])
        ax.set_zlim([0, h * 1.2])

    elif figura == "Prisma rectangular":
        l, w, h = params["l"], params["w"], params["h"]
        Z = np.array([
            [-l / 2, -w / 2, 0], [l / 2, -w / 2, 0], [l / 2, w / 2, 0], [-l / 2, w / 2, 0],
            [-l / 2, -w / 2, h], [l / 2, -w / 2, h], [l / 2, w / 2, h], [-l / 2, w / 2, h],
        ])
        caras = [
            [Z[0], Z[1], Z[2], Z[3]], [Z[4], Z[5], Z[6], Z[7]],
            [Z[0], Z[1], Z[5], Z[4]], [Z[2], Z[3], Z[7], Z[6]],
            [Z[1], Z[2], Z[6], Z[5]], [Z[4], Z[7], Z[3], Z[0]],
        ]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors="#0284c7", lw=1.2))
        lim = max(l, w, h) * 0.8
        ax.set_xlim([-lim, lim])
        ax.set_ylim([-lim, lim])
        ax.set_zlim([0, h * 1.2])

    elif figura == "Prisma triangular":
        b, h_tri, h = params["b"], params["h_tri"], params["h"]
        Z = np.array([
            [-b / 2, -h_tri / 3, 0], [b / 2, -h_tri / 3, 0], [0, 2 * h_tri / 3, 0],
            [-b / 2, -h_tri / 3, h], [b / 2, -h_tri / 3, h], [0, 2 * h_tri / 3, h],
        ])
        caras = [
            [Z[0], Z[1], Z[2]], [Z[3], Z[4], Z[5]],
            [Z[0], Z[1], Z[4], Z[3]], [Z[1], Z[2], Z[5], Z[4]], [Z[2], Z[0], Z[3], Z[5]],
        ]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors="#0284c7", lw=1.2))
        lim = max(b, h_tri, h) * 0.8
        ax.set_xlim([-lim, lim])
        ax.set_ylim([-lim, lim])
        ax.set_zlim([0, h * 1.2])

    elif figura == "Toro (Dona)":
        R_may, r_men = params["R"], params["r"]
        u = np.linspace(0, 2 * np.pi, 36)
        v = np.linspace(0, 2 * np.pi, 36)
        U, V = np.meshgrid(u, v)
        X = (R_may + r_men * np.cos(V)) * np.cos(U)
        Y = (R_may + r_men * np.cos(V)) * np.sin(U)
        Z = r_men * np.sin(V)
        ax.plot_surface(X, Y, Z, color=color_cara, alpha=alfa, edgecolor="#0284c7", lw=0.3)
        lim = (R_may + r_men) * 1.15
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)

    elif figura == "Elipsoide":
        a, b, c = params["a"], params["b"], params["c"]
        u = np.linspace(0, 2 * np.pi, 35)
        v = np.linspace(0, np.pi, 35)
        X = a * np.outer(np.cos(u), np.sin(v))
        Y = b * np.outer(np.sin(u), np.sin(v))
        Z = c * np.outer(np.ones_like(u), np.cos(v))
        ax.plot_surface(X, Y, Z, color=color_cara, alpha=alfa, edgecolor="#0284c7", lw=0.3)
        lim = max(a, b, c) * 1.2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)

    return fig


# ==============================================================================
# ENCABEZADO Y PESTAÑAS
# ==============================================================================
encabezado_pagina(
    "📐 Módulo de Geometría",
    "Geometría plana, trigonometría, geometría analítica en $\\mathbb{R}^2$ y $\\mathbb{R}^3$, secciones cónicas y modelado 3D.",
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📏 1. Figuras 2D y Polígonos",
    "📈 2. Rectas y Parábolas (ℝ²)",
    "🪐 3. Secciones Cónicas",
    "🧭 4. Planos y Coordenadas (ℝ³)",
    "🧊 5. Sólidos 3D",
])

# ==============================================================================
# PESTAÑA 1: FIGURAS 2D Y POLÍGONOS
# ==============================================================================
with tab1:
    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        with st.container(border=True):
            titulo_tarjeta("📏 Propiedades Métricas de Figuras Planas")
            figura_2d = st.selectbox(
                "Seleccione la figura:",
                [
                    "Triángulo (Análisis completo)",
                    "Polígono Regular (n lados)",
                    "Polígono por Coordenadas (Fórmula de Gauss)",
                    "Círculo y Sector Circular",
                    "Elipse",
                    "Cuadrado",
                    "Rectángulo",
                    "Trapecio",
                ],
            )

            fig_plana, ax_p = _crear_fig_2d(w=5.5, h=4.5, titulo=figura_2d)
            ax_p.set_aspect("equal", adjustable="box")

            if figura_2d == "Cuadrado":
                L = st.number_input("Lado ($L$):", min_value=0.01, value=4.0, step=0.5)
                area = L**2
                perim = 4 * L
                diag = L * math.sqrt(2)
                c1, c2, c3 = st.columns(3)
                c1.metric("Área", f"{area:,.3f}")
                c2.metric("Perímetro", f"{perim:,.3f}")
                c3.metric("Diagonal", f"{diag:,.3f}")
                st.latex(r"A = L^2, \quad P = 4L, \quad d = L\sqrt{2}")
                poly = Polygon([[-L / 2, -L / 2], [L / 2, -L / 2], [L / 2, L / 2], [-L / 2, L / 2]], closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2)
                ax_p.add_patch(poly)
                ax_p.set_xlim(-L * 0.8, L * 0.8)
                ax_p.set_ylim(-L * 0.8, L * 0.8)

            elif figura_2d == "Rectángulo":
                c1, c2 = st.columns(2)
                with c1:
                    b_rect = st.number_input("Base ($b$):", min_value=0.01, value=6.0, step=0.5)
                with c2:
                    h_rect = st.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5)
                area = b_rect * h_rect
                perim = 2 * (b_rect + h_rect)
                diag = math.hypot(b_rect, h_rect)
                m1, m2, m3 = st.columns(3)
                m1.metric("Área", f"{area:,.3f}")
                m2.metric("Perímetro", f"{perim:,.3f}")
                m3.metric("Diagonal", f"{diag:,.3f}")
                st.latex(r"A = b \cdot h, \quad P = 2(b + h), \quad d = \sqrt{b^2 + h^2}")
                poly = Polygon([[-b_rect / 2, -h_rect / 2], [b_rect / 2, -h_rect / 2], [b_rect / 2, h_rect / 2], [-b_rect / 2, h_rect / 2]], closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2)
                ax_p.add_patch(poly)
                lim = max(b_rect, h_rect) * 0.75
                ax_p.set_xlim(-lim, lim)
                ax_p.set_ylim(-lim, lim)

            elif figura_2d == "Círculo y Sector Circular":
                c1, c2 = st.columns(2)
                with c1:
                    r_circ = st.number_input("Radio ($r$):", min_value=0.01, value=3.0, step=0.5)
                with c2:
                    ang_sec = st.number_input("Ángulo del sector (°):", min_value=1.0, max_value=360.0, value=360.0, step=15.0)
                area_tot = math.pi * r_circ**2
                perim_tot = 2 * math.pi * r_circ
                area_sec = area_tot * (ang_sec / 360.0)
                long_arco = perim_tot * (ang_sec / 360.0)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Área Círculo", f"{area_tot:,.3f}")
                m2.metric("Circunferencia", f"{perim_tot:,.3f}")
                m3.metric("Área Sector", f"{area_sec:,.3f}")
                m4.metric("Longitud Arco", f"{long_arco:,.3f}")
                st.latex(r"A = \pi r^2, \quad L_{\text{arco}} = r\theta_{\text{rad}}, \quad A_{\text{sector}} = \frac{1}{2}r^2\theta_{\text{rad}}")
                circ = Circle((0, 0), r_circ, facecolor="#0284c7", alpha=0.25, edgecolor="#38bdf8", lw=2)
                ax_p.add_patch(circ)
                if ang_sec < 360:
                    th = np.linspace(0, math.radians(ang_sec), 80)
                    pts_sec = np.vstack([[0, 0], np.column_stack([r_circ * np.cos(th), r_circ * np.sin(th)])])
                    ax_p.add_patch(Polygon(pts_sec, closed=True, facecolor="#38bdf8", alpha=0.55, edgecolor="#f8fafc", lw=1.5))
                ax_p.set_xlim(-r_circ * 1.3, r_circ * 1.3)
                ax_p.set_ylim(-r_circ * 1.3, r_circ * 1.3)

            elif figura_2d == "Elipse":
                c1, c2 = st.columns(2)
                with c1:
                    a_el = st.number_input("Semieje mayor ($a$):", min_value=0.01, value=5.0, step=0.5)
                with c2:
                    b_el = st.number_input("Semieje menor ($b$):", min_value=0.01, value=3.0, step=0.5)
                area = math.pi * a_el * b_el
                h_ram = ((a_el - b_el) ** 2) / ((a_el + b_el) ** 2)
                perim = math.pi * (a_el + b_el) * (1 + (3 * h_ram) / (10 + math.sqrt(4 - 3 * h_ram)))
                c_foco = math.sqrt(abs(a_el**2 - b_el**2))
                exc = c_foco / max(a_el, b_el)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Área", f"{area:,.3f}")
                m2.metric("Perímetro (Ramanujan)", f"{perim:,.3f}")
                m3.metric("Distancia Focal (c)", f"{c_foco:,.3f}")
                m4.metric("Excentricidad (e)", f"{exc:,.4f}")
                st.latex(r"A = \pi a b, \quad c = \sqrt{|a^2 - b^2|}, \quad e = \frac{c}{\max(a,b)}")
                elip = Ellipse((0, 0), 2 * a_el, 2 * b_el, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2)
                ax_p.add_patch(elip)
                lim = max(a_el, b_el) * 1.3
                ax_p.set_xlim(-lim, lim)
                ax_p.set_ylim(-lim, lim)

            elif figura_2d == "Trapecio":
                c1, c2, c3 = st.columns(3)
                with c1:
                    B_may = st.number_input("Base mayor ($B$):", min_value=0.01, value=8.0, step=0.5)
                with c2:
                    b_men = st.number_input("Base menor ($b$):", min_value=0.01, value=4.0, step=0.5)
                with c3:
                    h_trap = st.number_input("Altura ($h$):", min_value=0.01, value=3.0, step=0.5)
                lado_lat = math.hypot((B_may - b_men) / 2, h_trap)
                area = ((B_may + b_men) * h_trap) / 2
                perim = B_may + b_men + 2 * lado_lat
                m1, m2, m3 = st.columns(3)
                m1.metric("Área", f"{area:,.3f}")
                m2.metric("Perímetro (Isósceles)", f"{perim:,.3f}")
                m3.metric("Mediana", f"{(B_may + b_men)/2:,.3f}")
                pts_t = [[-B_may / 2, -h_trap / 2], [B_may / 2, -h_trap / 2], [b_men / 2, h_trap / 2], [-b_men / 2, h_trap / 2]]
                ax_p.add_patch(Polygon(pts_t, closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2))
                lim = max(B_may, h_trap) * 0.75
                ax_p.set_xlim(-lim, lim)
                ax_p.set_ylim(-lim, lim)

            elif figura_2d == "Polígono Regular (n lados)":
                c1, c2 = st.columns(2)
                with c1:
                    n_lados = int(st.number_input("Número de lados ($n$):", min_value=3, max_value=30, value=6, step=1))
                with c2:
                    s_lado = st.number_input("Longitud de cada lado ($L$):", min_value=0.01, value=4.0, step=0.5)
                perim = n_lados * s_lado
                apotema = s_lado / (2 * math.tan(math.pi / n_lados))
                r_circun = s_lado / (2 * math.sin(math.pi / n_lados))
                area = (perim * apotema) / 2
                ang_int = ((n_lados - 2) * 180.0) / n_lados
                diagonales = (n_lados * (n_lados - 3)) // 2
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Área", f"{area:,.3f}")
                m2.metric("Perímetro", f"{perim:,.3f}")
                m3.metric("Apotema (r)", f"{apotema:,.3f}")
                m4.metric("Radio Circunscrito (R)", f"{r_circun:,.3f}")
                st.caption(f"**Ángulo interior:** {ang_int:.2f}° | **Suma de ángulos interiores:** {(n_lados-2)*180}° | **Diagonales totales:** {diagonales}")
                st.latex(r"a = \frac{L}{2\tan(\pi/n)}, \quad A = \frac{P \cdot a}{2}, \quad D = \frac{n(n-3)}{2}")
                angulos = np.linspace(0, 2 * np.pi, n_lados, endpoint=False) + np.pi / 2
                verts = np.column_stack([r_circun * np.cos(angulos), r_circun * np.sin(angulos)])
                ax_p.add_patch(Polygon(verts, closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2))
                ax_p.set_xlim(-r_circun * 1.3, r_circun * 1.3)
                ax_p.set_ylim(-r_circun * 1.3, r_circun * 1.3)

            elif figura_2d == "Triángulo (Análisis completo)":
                metodo_tri = st.radio(
                    "Datos conocidos:",
                    ["Tres lados (Fórmula de Herón y Radios)", "Dos lados y el ángulo comprendido (LAL)", "Base y Altura"],
                    horizontal=True,
                )
                if metodo_tri == "Base y Altura":
                    c1, c2 = st.columns(2)
                    with c1:
                        b_t = st.number_input("Base ($b$):", min_value=0.01, value=6.0)
                    with c2:
                        h_t = st.number_input("Altura ($h$):", min_value=0.01, value=4.0)
                    st.metric("Área del Triángulo", f"{(b_t * h_t) / 2:,.3f}")
                    pts = [[-b_t / 2, 0], [b_t / 2, 0], [0, h_t]]
                    ax_p.add_patch(Polygon(pts, closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2))
                    lim = max(b_t, h_t) * 0.8
                    ax_p.set_xlim(-lim, lim)
                    ax_p.set_ylim(-0.2 * lim, lim * 1.2)
                else:
                    if "Tres lados" in metodo_tri:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            a_t = st.number_input("Lado $a$:", min_value=0.01, value=5.0)
                        with c2:
                            b_t = st.number_input("Lado $b$:", min_value=0.01, value=6.0)
                        with c3:
                            c_t = st.number_input("Lado $c$:", min_value=0.01, value=7.0)
                    else:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            a_t = st.number_input("Lado $a$:", min_value=0.01, value=5.0, key="lal_a")
                        with c2:
                            b_t = st.number_input("Lado $b$:", min_value=0.01, value=6.0, key="lal_b")
                        with c3:
                            ang_C = st.number_input("Ángulo $\\gamma$ (°):", min_value=0.1, max_value=179.9, value=60.0)
                        c_t = math.sqrt(a_t**2 + b_t**2 - 2 * a_t * b_t * math.cos(math.radians(ang_C)))

                    if not ((a_t + b_t > c_t) and (a_t + c_t > b_t) and (b_t + c_t > a_t)):
                        st.error("⛔ Esos lados violan la Desigualdad Triangular ($a + b > c$). No forman un triángulo cerrado.")
                    else:
                        s = (a_t + b_t + c_t) / 2
                        area = math.sqrt(s * (s - a_t) * (s - b_t) * (s - c_t))
                        r_in = area / s
                        R_circ = (a_t * b_t * c_t) / (4 * area)
                        A_deg = math.degrees(math.acos(np.clip((b_t**2 + c_t**2 - a_t**2) / (2 * b_t * c_t), -1.0, 1.0)))
                        B_deg = math.degrees(math.acos(np.clip((a_t**2 + c_t**2 - b_t**2) / (2 * a_t * c_t), -1.0, 1.0)))
                        C_deg = 180.0 - A_deg - B_deg

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Área (Herón)", f"{area:,.3f}")
                        m2.metric("Perímetro", f"{2*s:,.3f}")
                        m3.metric("Inradio (r)", f"{r_in:,.3f}")
                        m4.metric("Circunradio (R)", f"{R_circ:,.3f}")
                        st.info(
                            f"**Ángulos internos:** $\\alpha = {A_deg:.2f}^\\circ$, $\\beta = {B_deg:.2f}^\\circ$, $\\gamma = {C_deg:.2f}^\\circ$ "
                            f"| **Lados:** $a={a_t:.2f}, b={b_t:.2f}, c={c_t:.2f}$"
                        )
                        st.latex(r"A = \sqrt{s(s-a)(s-b)(s-c)}, \quad r = \frac{A}{s}, \quad R = \frac{abc}{4A}")

                        # Coordenadas de vértices para graficar (A en origen, B en (c,0))
                        xC = b_t * math.cos(math.radians(A_deg))
                        yC = b_t * math.sin(math.radians(A_deg))
                        pts = np.array([[0.0, 0.0], [c_t, 0.0], [xC, yC]])
                        baricentro = pts.mean(axis=0)
                        ax_p.add_patch(Polygon(pts, closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2))
                        ax_p.plot(baricentro[0], baricentro[1], "o", color="#f59e0b", label="Baricentro G")
                        ax_p.legend(facecolor="#1e293b", labelcolor="#f8fafc", fontsize=8)
                        lim = max(c_t, xC, yC) * 1.25
                        ax_p.set_xlim(-0.2 * lim, lim)
                        ax_p.set_ylim(-0.2 * lim, lim)

            elif figura_2d == "Polígono por Coordenadas (Fórmula de Gauss)":
                st.caption("Ingrese los vértices en orden (horario o antihorario) como pares `x, y` (uno por renglón):")
                texto_verts = st.text_area(
                    "Vértices (x, y):",
                    value="0, 0\n5, 0\n6, 4\n2, 6\n-1, 3",
                    height=130,
                )
                try:
                    pts = []
                    for linea in texto_verts.strip().splitlines():
                        if linea.strip():
                            partes = [float(p.strip()) for p in linea.replace("(", "").replace(")", "").split(",")]
                            if len(partes) != 2:
                                raise ValueError
                            pts.append(partes)
                    if len(pts) < 3:
                        st.warning("Ingrese al menos 3 vértices para formar un polígono.")
                    else:
                        arr = np.array(pts)
                        x_v, y_v = arr[:, 0], arr[:, 1]
                        area_gauss = 0.5 * abs(np.dot(x_v, np.roll(y_v, -1)) - np.dot(y_v, np.roll(x_v, -1)))
                        perim = float(np.sum(np.hypot(np.diff(np.append(x_v, x_v[0])), np.diff(np.append(y_v, y_v[0])))))
                        cx, cy = float(np.mean(x_v)), float(np.mean(y_v))
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Área (Shoelace)", f"{area_gauss:,.4f}")
                        m2.metric("Perímetro", f"{perim:,.4f}")
                        m3.metric("Centroide Promedio", f"({cx:.2f}, {cy:.2f})")
                        st.latex(r"A = \frac{1}{2}\left|\sum_{i=1}^{n} (x_i y_{i+1} - x_{i+1} y_i)\right|")
                        ax_p.add_patch(Polygon(arr, closed=True, facecolor="#0284c7", alpha=0.35, edgecolor="#38bdf8", lw=2))
                        ax_p.plot(x_v, y_v, "o", color="#f8fafc", ms=5)
                        ax_p.plot(cx, cy, "*", color="#f59e0b", ms=10, label="Centroide")
                        ax_p.legend(facecolor="#1e293b", labelcolor="#f8fafc", fontsize=8)
                        pad_x = max((x_v.max() - x_v.min()) * 0.25, 1.0)
                        pad_y = max((y_v.max() - y_v.min()) * 0.25, 1.0)
                        ax_p.set_xlim(x_v.min() - pad_x, x_v.max() + pad_x)
                        ax_p.set_ylim(y_v.min() - pad_y, y_v.max() + pad_y)
                except ValueError:
                    st.error("Formato inválido. Escriba cada vértice como `x, y` en una línea distinta.")

    with col_der:
        with st.container(border=True):
            titulo_tarjeta("🖼️ Visualización a Escala")
            st.pyplot(fig_plana)


# ==============================================================================
# PESTAÑA 2: GEOMETRÍA ANALÍTICA EN R² (RECTAS Y PARÁBOLAS)
# ==============================================================================
with tab2:
    herramienta = st.radio(
        "Seleccione el estudio analítico:",
        [
            "📍 Recta por 2 Puntos y Distancia Punto-Recta",
            "⚔️ Intersección y Ángulo entre 2 Rectas",
            "📈 Parábola / Ecuación Cuadrática (Vértice, Foco y Directriz)",
        ],
        horizontal=True,
    )

    if "Recta por 2 Puntos" in herramienta:
        col_in, col_out = st.columns([1.1, 1])
        with col_in:
            with st.container(border=True):
                titulo_tarjeta("Coordenadas en el Plano")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**Punto $A(x_1, y_1)$**")
                    x1 = st.number_input("x₁:", value=-2.0, step=1.0)
                    y1 = st.number_input("y₁:", value=1.0, step=1.0)
                with c2:
                    st.markdown("**Punto $B(x_2, y_2)$**")
                    x2 = st.number_input("x₂:", value=4.0, step=1.0)
                    y2 = st.number_input("y₂:", value=5.0, step=1.0)
                with c3:
                    st.markdown("**Punto Externo $P_0$**")
                    x0 = st.number_input("x₀:", value=2.0, step=1.0)
                    y0 = st.number_input("y₀:", value=-1.0, step=1.0)

                dx, dy = x2 - x1, y2 - y1
                dist_ab = math.hypot(dx, dy)
                xm, ym = (x1 + x2) / 2, (y1 + y2) / 2

                if dist_ab < 1e-12:
                    st.error("Los puntos $A$ y $B$ coinciden: no definen una única recta.")
                else:
                    # Ecuación general Ax + By + C = 0
                    A_r = dy
                    B_r = -dx
                    C_r = dx * y1 - dy * x1
                    dist_p0 = abs(A_r * x0 + B_r * y0 + C_r) / math.hypot(A_r, B_r)
                    # Proyección ortogonal de P0 sobre la recta
                    factor_p = (A_r * x0 + B_r * y0 + C_r) / (A_r**2 + B_r**2)
                    xp = x0 - A_r * factor_p
                    yp = y0 - B_r * factor_p

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Distancia d(A, B)", f"{dist_ab:,.4f}")
                    m2.metric("Punto Medio M", f"({xm:.2f}, {ym:.2f})")
                    m3.metric("Distancia d(P₀, Recta)", f"{dist_p0:,.4f}")

                    if abs(dx) > 1e-12:
                        m_pend = dy / dx
                        ang_inc = math.degrees(math.atan(m_pend))
                        if ang_inc < 0:
                            ang_inc += 180.0
                        b_ord = y1 - m_pend * x1
                        signo_b = "+" if b_ord >= 0 else "-"
                        st.latex(
                            rf"m = {m_pend:.4g}, \quad \theta = {ang_inc:.2f}^\circ, \quad "
                            rf"y = {m_pend:.4g}x {signo_b} {abs(b_ord):.4g}"
                        )
                    else:
                        st.latex(rf"\text{{Recta vertical: }} x = {x1:.4g} \quad (\theta = 90^\circ)")

                    st.latex(
                        rf"\text{{Forma General: }} ({A_r:.4g})x + ({B_r:.4g})y + ({C_r:.4g}) = 0"
                    )
                    st.latex(
                        rf"d(P_0, L) = \frac{{|Ax_0 + By_0 + C|}}{{\sqrt{{A^2 + B^2}}}} = {dist_p0:.4f}"
                    )

        with col_out:
            with st.container(border=True):
                titulo_tarjeta("Gráfica de la Recta y Proyección Ortogonal")
                fig_r, ax_r = _crear_fig_2d(titulo="Recta AB y distancia desde P₀")
                xs_all = [x1, x2, x0]
                ys_all = [y1, y2, y0]
                xmin, xmax = min(xs_all) - 3, max(xs_all) + 3
                if dist_ab >= 1e-12:
                    if abs(dx) > 1e-12:
                        xx = np.linspace(xmin, xmax, 200)
                        ax_r.plot(xx, m_pend * (xx - x1) + y1, color="#38bdf8", lw=2.2, label="Recta AB")
                    else:
                        ax_r.axvline(x1, color="#38bdf8", lw=2.2, label="Recta AB")
                    ax_r.plot([x0, xp], [y0, yp], ls="--", color="#f43f5e", lw=1.8, label=f"d(P₀, L) = {dist_p0:.2f}")
                    ax_r.plot([x1, x2], [y1, y2], "o", color="#f8fafc", ms=7)
                    ax_r.plot([xm], [ym], "s", color="#22c55e", ms=6, label="Punto Medio M")
                    ax_r.plot([x0], [y0], "o", color="#f43f5e", ms=7, label="P₀")
                    ax_r.legend(facecolor="#1e293b", labelcolor="#f8fafc", fontsize=8)
                st.pyplot(fig_r)

    elif "Intersección y Ángulo" in herramienta:
        with st.container(border=True):
            titulo_tarjeta("Posición Relativa de Dos Rectas ($A_i x + B_i y + C_i = 0$)")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Recta $L_1: A_1x + B_1y + C_1 = 0$**")
                a1 = st.number_input("A₁:", value=2.0, step=1.0)
                b1 = st.number_input("B₁:", value=-1.0, step=1.0)
                c1_v = st.number_input("C₁:", value=-1.0, step=1.0)
            with c2:
                st.markdown("**Recta $L_2: A_2x + B_2y + C_2 = 0$**")
                a2 = st.number_input("A₂:", value=1.0, step=1.0)
                b2 = st.number_input("B₂:", value=1.0, step=1.0)
                c2_v = st.number_input("C₂:", value=-5.0, step=1.0)

            n1 = math.hypot(a1, b1)
            n2 = math.hypot(a2, b2)
            if n1 < 1e-12 or n2 < 1e-12:
                st.error("Los coeficientes $A$ y $B$ de cada recta no pueden ser ambos cero.")
            else:
                det_sis = a1 * b2 - a2 * b1
                cos_ang = abs(a1 * a2 + b1 * b2) / (n1 * n2)
                ang_agudo = math.degrees(math.acos(np.clip(cos_ang, 0.0, 1.0)))

                if abs(det_sis) < 1e-12:
                    if abs(a1 * c2_v - a2 * c1_v) < 1e-12 and abs(b1 * c2_v - b2 * c1_v) < 1e-12:
                        st.info("Las dos rectas son **COINCIDENTES** (infinitos puntos de intersección).")
                    else:
                        dist_par = abs(c1_v / n1 - (c2_v / n2) * (1 if (a1 * a2 + b1 * b2) > 0 else -1))
                        st.warning(f"Las rectas son **PARALELAS** ($\\theta = 0^\\circ$). Distancia entre ellas: **{dist_par:.4f}**.")
                else:
                    xi = (b1 * c2_v - b2 * c1_v) / det_sis
                    yi = (c1_v * a2 - c2_v * a1) / det_sis
                    tipo_corte = "PERPENDICULARES (Ortogonales)" if abs(ang_agudo - 90.0) < 1e-6 else "SECANTES"
                    st.success(
                        f"Rectas **{tipo_corte}** | **Punto de intersección:** $P({xi:.4f}, {yi:.4f})$ | "
                        f"**Ángulo agudo entre ellas:** $\\theta = {ang_agudo:.2f}^\\circ$"
                    )

                    fig_l, ax_l = _crear_fig_2d(w=7, h=4, titulo=f"Intersección en ({xi:.2f}, {yi:.2f})")
                    xx = np.linspace(xi - 6, xi + 6, 200)
                    for ai, bi, ci, col, lab in ((a1, b1, c1_v, "#38bdf8", "L₁"), (a2, b2, c2_v, "#a855f7", "L₂")):
                        if abs(bi) > 1e-12:
                            ax_l.plot(xx, (-ai * xx - ci) / bi, color=col, lw=2.2, label=lab)
                        else:
                            ax_l.axvline(-ci / ai, color=col, lw=2.2, label=lab)
                    ax_l.plot([xi], [yi], "o", color="#f43f5e", ms=8, zorder=6, label="Intersección")
                    ax_l.set_xlim(xi - 6, xi + 6)
                    ax_l.set_ylim(yi - 6, yi + 6)
                    ax_l.legend(facecolor="#1e293b", labelcolor="#f8fafc")
                    st.pyplot(fig_l)

    else:
        with st.container(border=True):
            titulo_tarjeta("Ecuación Cuadrática y Elementos de la Parábola ($y = Ax^2 + Bx + C$)")
            c1, c2, c3 = st.columns(3)
            with c1:
                a_coef = st.number_input("Coeficiente $A$:", value=1.0, step=0.5)
            with c2:
                b_coef = st.number_input("Coeficiente $B$:", value=-4.0, step=0.5)
            with c3:
                c_coef = st.number_input("Coeficiente $C$:", value=3.0, step=0.5)

            if a_coef == 0 and b_coef == 0:
                st.warning("No hay variable $x$: es la función constante $y = C$.")
            elif a_coef == 0:
                raiz_lin = -c_coef / b_coef
                st.info(f"Como $A = 0$, es una recta con raíz única en $x = {raiz_lin:.4f}$.")
            else:
                disc = b_coef**2 - 4 * a_coef * c_coef
                xv = -b_coef / (2 * a_coef)
                yv = a_coef * xv**2 + b_coef * xv + c_coef
                p_focal = 1.0 / (4.0 * a_coef)
                yf = yv + p_focal
                y_dir = yv - p_focal
                lado_recto = abs(4 * p_focal)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Vértice V(h, k)", f"({xv:.3f}, {yv:.3f})")
                m2.metric("Foco F", f"({xv:.3f}, {yf:.3f})")
                m3.metric("Directriz", f"y = {y_dir:.3f}")
                m4.metric("Lado Recto |4p|", f"{lado_recto:.3f}")

                if disc >= 0:
                    x1 = (-b_coef + math.sqrt(disc)) / (2 * a_coef)
                    x2 = (-b_coef - math.sqrt(disc)) / (2 * a_coef)
                    st.success(f"**Discriminante $\\Delta = {disc:.3f} \\ge 0$ → Raíces Reales:** $x_1 = {x1:.4f}$, $x_2 = {x2:.4f}$")
                else:
                    re_p = -b_coef / (2 * a_coef)
                    im_p = abs(math.sqrt(-disc) / (2 * a_coef))
                    st.warning(f"**Discriminante $\\Delta = {disc:.3f} < 0$ → Raíces Complejas Conjugadas:** $x = {re_p:.4f} \\pm {im_p:.4f}i$")

                st.latex(
                    rf"\text{{Forma Canónica: }} (x - ({xv:.4g}))^2 = {4*p_focal:.4g}(y - ({yv:.4g}))"
                )

                ancho = max(6.0, abs(math.sqrt(abs(disc)) / a_coef) * 1.5)
                xx = np.linspace(xv - ancho, xv + ancho, 400)
                yy = a_coef * xx**2 + b_coef * xx + c_coef
                fig_q, ax_q = _crear_fig_2d(w=7.5, h=4.2, titulo="Parábola, Vértice, Foco y Directriz")
                ax_q.plot(xx, yy, color="#38bdf8", lw=2.5, label="f(x)")
                ax_q.axhline(y_dir, color="#f43f5e", ls=":", lw=1.6, label=f"Directriz y={y_dir:.2f}")
                ax_q.axvline(xv, color="#94a3b8", ls="-.", lw=1.0, alpha=0.6, label=f"Eje x={xv:.2f}")
                ax_q.plot([xv], [yv], "o", color="#22c55e", ms=7, label="Vértice V")
                ax_q.plot([xv], [yf], "*", color="#f59e0b", ms=9, label="Foco F")
                if disc >= 0:
                    ax_q.plot([x1, x2], [0, 0], "o", color="#f8fafc", ms=6, label="Raíces")
                ax_q.legend(facecolor="#1e293b", labelcolor="#f8fafc", fontsize=8, ncol=3)
                st.pyplot(fig_q)


# ==============================================================================
# PESTAÑA 3: SECCIONES CÓNICAS Y ROTACIÓN DE EJES (NIVEL FACULTAD DE CIENCIAS)
# ==============================================================================
with tab3:
    with st.container(border=True):
        titulo_tarjeta("🪐 Clasificador de Secciones Cónicas y Rotación de Ejes")
        st.markdown(
            r"Analiza la ecuación general de segundo grado **$Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0$**, "
            r"calcula sus invariantes y elimina el término mixto $Bxy$ mediante rotación de ejes."
        )

        usar_kb_conica = False
        if _TIENE_TECLADO:
            usar_kb_conica = st.toggle("⌨️ Escribir ecuación con el Teclado Matemático", value=False, key="conica_kb_tog")

        A_c, B_c, C_c, D_c, E_c, F_c = 1.0, 0.0, 4.0, 0.0, 0.0, -16.0
        ok_conica = True

        if usar_kb_conica:
            lat_con = teclado_matematico(
                "kb_conica",
                valor_inicial=r"5x^{2}+4xy+2y^{2}-6=0",
                placeholder="Ej: x² + xy + y² - 4 = 0",
                acoplado=True,
            )
            if lat_con:
                try:
                    obj_c = latex_a_sympy(lat_con)
                    expr_c = (obj_c.lhs - obj_c.rhs) if isinstance(obj_c, sp.Eq) else obj_c
                    x_s, y_s = sp.Symbol("x", real=True), sp.Symbol("y", real=True)
                    P_con = sp.Poly(sp.expand(expr_c), x_s, y_s)
                    if P_con.total_degree() != 2:
                        st.error("La ecuación debe ser de segundo grado en $x, y$.")
                        ok_conica = False
                    else:
                        A_c = float(P_con.coeff_monomial(x_s**2))
                        B_c = float(P_con.coeff_monomial(x_s * y_s))
                        C_c = float(P_con.coeff_monomial(y_s**2))
                        D_c = float(P_con.coeff_monomial(x_s))
                        E_c = float(P_con.coeff_monomial(y_s))
                        F_c = float(P_con.coeff_monomial(1))
                except Exception as e:
                    st.error(f"No se pudo extraer el polinomio cuadrático: {e}")
                    ok_conica = False
            else:
                ok_conica = False
        else:
            cols_c = st.columns(6)
            A_c = cols_c[0].number_input("A (x²):", value=5.0, step=1.0)
            B_c = cols_c[1].number_input("B (xy):", value=4.0, step=1.0)
            C_c = cols_c[2].number_input("C (y²):", value=2.0, step=1.0)
            D_c = cols_c[3].number_input("D (x):", value=0.0, step=1.0)
            E_c = cols_c[4].number_input("E (y):", value=0.0, step=1.0)
            F_c = cols_c[5].number_input("F (indep.):", value=-6.0, step=1.0)

        if ok_conica and (abs(A_c) > 1e-12 or abs(B_c) > 1e-12 or abs(C_c) > 1e-12):
            inv_I = B_c**2 - 4 * A_c * C_c
            M_3 = np.array([
                [A_c, B_c / 2.0, D_c / 2.0],
                [B_c / 2.0, C_c, E_c / 2.0],
                [D_c / 2.0, E_c / 2.0, F_c],
            ])
            det_3 = float(np.linalg.det(M_3))

            if abs(inv_I) < 1e-10:
                tipo_con = "Parábola" if abs(det_3) > 1e-10 else "Parábola Degenerada (Rectas paralelas)"
            elif inv_I < 0:
                if abs(det_3) < 1e-10:
                    tipo_con = "Elipse Degenerada (Un único punto)"
                elif det_3 * (A_c + C_c) > 0:
                    tipo_con = "Conjunto Vacío en ℝ² (Elipse imaginaria)"
                elif abs(A_c - C_c) < 1e-10 and abs(B_c) < 1e-10:
                    tipo_con = "Circunferencia"
                else:
                    tipo_con = "Elipse"
            else:
                tipo_con = "Hipérbola" if abs(det_3) > 1e-10 else "Hipérbola Degenerada (Dos rectas que se cortan)"

            # Ángulo de rotación para eliminar Bxy
            if abs(B_c) < 1e-12:
                theta_rad = 0.0
            elif abs(A_c - C_c) < 1e-12:
                theta_rad = math.pi / 4.0
            else:
                theta_rad = 0.5 * math.atan2(B_c, A_c - C_c)
            theta_deg = math.degrees(theta_rad)

            cos_t, sin_t = math.cos(theta_rad), math.sin(theta_rad)
            Ap = A_c * cos_t**2 + B_c * cos_t * sin_t + C_c * sin_t**2
            Cp = A_c * sin_t**2 - B_c * cos_t * sin_t + C_c * cos_t**2

            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Clasificación", tipo_con)
            m2.metric("Discriminante B²-4AC", f"{inv_I:,.3f}")
            m3.metric("Determinante Δ₃", f"{det_3:,.3f}")
            m4.metric("Ángulo de Rotación θ", f"{theta_deg:,.2f}°")

            # Centro si es cónica central (inv_I != 0)
            cx_c, cy_c = 0.0, 0.0
            if abs(inv_I) > 1e-10:
                M_2 = np.array([[2 * A_c, B_c], [B_c, 2 * C_c]])
                sol_c = np.linalg.solve(M_2, [-D_c, -E_c])
                cx_c, cy_c = float(sol_c[0]), float(sol_c[1])
                st.info(
                    f"**Centro de la cónica:** $C({cx_c:.3f}, {cy_c:.3f})$ | "
                    f"**Coeficientes rotados (sin término $x'y'$):** $A' = {Ap:.4g}$, $C' = {Cp:.4g}$"
                )

            fig_c, ax_c = _crear_fig_2d(w=7, h=5, titulo=f"Lugar Geométrico: {tipo_con}")
            ax_c.set_aspect("equal", adjustable="box")
            r_vent = max(6.0, abs(cx_c) + 5.0, abs(cy_c) + 5.0)
            Xg, Yg = np.meshgrid(np.linspace(cx_c - r_vent, cx_c + r_vent, 350), np.linspace(cy_c - r_vent, cy_c + r_vent, 350))
            Zg = A_c * Xg**2 + B_c * Xg * Yg + C_c * Yg**2 + D_c * Xg + E_c * Yg + F_c
            if np.nanmin(Zg) <= 0 <= np.nanmax(Zg):
                ax_c.contour(Xg, Yg, Zg, levels=[0], colors=["#38bdf8"], linewidths=2.5)
            if abs(B_c) > 1e-10:
                tt = np.linspace(-r_vent, r_vent, 100)
                ax_c.plot(cx_c + tt * cos_t, cy_c + tt * sin_t, ls="--", color="#f59e0b", lw=1.2, label=f"Eje X' ({theta_deg:.1f}°)")
                ax_c.plot(cx_c - tt * sin_t, cy_c + tt * cos_t, ls="--", color="#a855f7", lw=1.2, label="Eje Y'")
                ax_c.legend(facecolor="#1e293b", labelcolor="#f8fafc", fontsize=8)
            st.pyplot(fig_c)


# ==============================================================================
# PESTAÑA 4: GEOMETRÍA EN EL ESPACIO R³ (PLANOS Y COORDENADAS)
# ==============================================================================
with tab4:
    col_p3d, col_coord = st.columns(2)

    with col_p3d:
        with st.container(border=True):
            titulo_tarjeta("🧭 Ecuación del Plano en ℝ³ y Distancia")
            modo_plano = st.radio("Definir plano mediante:", ["Tres Puntos (P, Q, R)", "Punto P₀ y Vector Normal n"], horizontal=True)
            if modo_plano == "Tres Puntos (P, Q, R)":
                cp1, cp2, cp3 = st.columns(3)
                with cp1:
                    P_pt = [st.number_input("Px", value=1.0), st.number_input("Py", value=0.0), st.number_input("Pz", value=0.0)]
                with cp2:
                    Q_pt = [st.number_input("Qx", value=0.0), st.number_input("Qy", value=1.0), st.number_input("Qz", value=0.0)]
                with cp3:
                    R_pt = [st.number_input("Rx", value=0.0), st.number_input("Ry", value=0.0), st.number_input("Rz", value=1.0)]
                v_pq = np.array(Q_pt) - np.array(P_pt)
                v_pr = np.array(R_pt) - np.array(P_pt)
                vec_n = np.cross(v_pq, v_pr)
                pto_base = np.array(P_pt)
            else:
                cp1, cp2 = st.columns(2)
                with cp1:
                    pto_base = np.array([st.number_input("x₀", value=1.0), st.number_input("y₀", value=2.0), st.number_input("z₀", value=3.0)])
                with cp2:
                    vec_n = np.array([st.number_input("nx", value=2.0), st.number_input("ny", value=-1.0), st.number_input("nz", value=2.0)])

            norma_n = float(np.linalg.norm(vec_n))
            if norma_n < 1e-12:
                st.error("El vector normal es nulo (los 3 puntos son colineales): no definen un único plano.")
            else:
                A_pl, B_pl, C_pl = vec_n
                D_pl = -float(np.dot(vec_n, pto_base))
                dist_orig = abs(D_pl) / norma_n
                st.success(f"**Vector Normal:** $\\vec{{n}} = ({A_pl:.3g}, {B_pl:.3g}, {C_pl:.3g})$ | **Distancia al origen:** {dist_orig:.4f}")
                st.latex(rf"\Pi: ({A_pl:.4g})x + ({B_pl:.4g})y + ({C_pl:.4g})z + ({D_pl:.4g}) = 0")

                fig_pl, ax_pl = _crear_fig_3d(w=5.5, h=4.5, titulo="Plano en ℝ³")
                grid_u = np.linspace(-4, 4, 20)
                Xm, Ym = np.meshgrid(grid_u, grid_u)
                if abs(C_pl) > 1e-9:
                    Zm = (-A_pl * Xm - B_pl * Ym - D_pl) / C_pl
                    ax_pl.plot_surface(Xm, Ym, Zm, color="#38bdf8", alpha=0.55, edgecolor="#0284c7", lw=0.3)
                st.pyplot(fig_pl)

    with col_coord:
        with st.container(border=True):
            titulo_tarjeta("🌐 Conversor de Coordenadas 3D")
            sist_orig = st.selectbox("Sistema de entrada:", ["Cartesianas (x, y, z)", "Cilíndricas (r, θ°, z)", "Esféricas (ρ, θ°, φ°)"])
            cc1, cc2, cc3 = st.columns(3)
            if sist_orig.startswith("Cart"):
                xv = cc1.number_input("x:", value=3.0)
                yv = cc2.number_input("y:", value=4.0)
                zv = cc3.number_input("z:", value=5.0)
            elif sist_orig.startswith("Cil"):
                rv = cc1.number_input("r (≥0):", min_value=0.0, value=5.0)
                th_d = cc2.number_input("θ (grados):", value=53.13)
                zv = cc3.number_input("z:", value=5.0)
                xv = rv * math.cos(math.radians(th_d))
                yv = rv * math.sin(math.radians(th_d))
            else:
                rho_v = cc1.number_input("ρ (≥0):", min_value=0.0, value=7.071)
                th_d = cc2.number_input("θ acimutal (°):", value=45.0)
                phi_d = cc3.number_input("φ polar (°):", min_value=0.0, max_value=180.0, value=45.0)
                xv = rho_v * math.sin(math.radians(phi_d)) * math.cos(math.radians(th_d))
                yv = rho_v * math.sin(math.radians(phi_d)) * math.sin(math.radians(th_d))
                zv = rho_v * math.cos(math.radians(phi_d))

            r_cil = math.hypot(xv, yv)
            theta_cil = math.degrees(math.atan2(yv, xv))
            rho_esf = math.sqrt(xv**2 + yv**2 + zv**2)
            phi_esf = math.degrees(math.acos(zv / rho_esf)) if rho_esf > 1e-12 else 0.0

            st.divider()
            st.markdown("##### Equivalencias Exactas")
            st.latex(rf"\text{{Cartesianas }}(x, y, z) = \left({xv:.4f},\; {yv:.4f},\; {zv:.4f}\right)")
            st.latex(rf"\text{{Cilíndricas }}(r, \theta, z) = \left({r_cil:.4f},\; {theta_cil:.2f}^\circ,\; {zv:.4f}\right)")
            st.latex(rf"\text{{Esféricas }}(\rho, \theta, \varphi) = \left({rho_esf:.4f},\; {theta_cil:.2f}^\circ,\; {phi_esf:.2f}^\circ\right)")


# ==============================================================================
# PESTAÑA 5: SÓLIDOS 3D (VOLUMEN, ÁREA LATERAL Y TOTAL SIMULTÁNEOS)
# ==============================================================================
with tab5:
    col_s_in, col_s_3d = st.columns([1.15, 1])

    with col_s_in:
        with st.container(border=True):
            titulo_tarjeta("🧊 Cálculo Espacial de Sólidos 3D")
            figura_3d = st.selectbox(
                "Seleccione el sólido:",
                [
                    "Cilindro",
                    "Esfera",
                    "Cono",
                    "Pirámide cuadrangular",
                    "Prisma rectangular",
                    "Prisma triangular",
                    "Toro (Dona)",
                    "Elipsoide",
                ],
            )

            params_3d = {}
            vol = area_lat = area_tot = 0.0
            valido_3d = True

            if figura_3d == "Cilindro":
                c1, c2 = st.columns(2)
                r = c1.number_input("Radio ($r$):", min_value=0.01, value=2.0, key="cil_r")
                h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, key="cil_h")
                params_3d = {"r": r, "h": h}
                vol = math.pi * r**2 * h
                area_lat = 2 * math.pi * r * h
                area_tot = area_lat + 2 * math.pi * r**2
                st.latex(r"V = \pi r^2 h, \quad A_L = 2\pi r h, \quad A_T = 2\pi r(r + h)")

            elif figura_3d == "Esfera":
                r = st.number_input("Radio ($r$):", min_value=0.01, value=3.0, key="esf_r")
                params_3d = {"r": r}
                vol = (4.0 / 3.0) * math.pi * r**3
                area_lat = 4 * math.pi * r**2
                area_tot = area_lat
                st.latex(r"V = \frac{4}{3}\pi r^3, \quad A_T = 4\pi r^2")

            elif figura_3d == "Cono":
                modo_cono = st.radio("Dato conocido además del radio:", ["Altura (h)", "Generatriz (s)"], horizontal=True)
                c1, c2 = st.columns(2)
                r = c1.number_input("Radio ($r$):", min_value=0.01, value=3.0, key="cono_r")
                if modo_cono == "Altura (h)":
                    h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, key="cono_h")
                    s = math.hypot(r, h)
                else:
                    s = c2.number_input("Generatriz ($s > r$):", min_value=0.02, value=5.0, key="cono_s")
                    if s <= r:
                        st.error("⛔ La generatriz $s$ debe ser estrictamente mayor que el radio $r$ ($s^2 = r^2 + h^2$).")
                        valido_3d = False
                        h = 0.0
                    else:
                        h = math.sqrt(s**2 - r**2)
                if valido_3d:
                    params_3d = {"r": r, "h": h}
                    vol = (math.pi * r**2 * h) / 3.0
                    area_lat = math.pi * r * s
                    area_tot = area_lat + math.pi * r**2
                    st.caption(f"Altura $h = {h:.3f}$ | Generatriz $s = {s:.3f}$")
                    st.latex(r"V = \frac{1}{3}\pi r^2 h, \quad A_L = \pi r s, \quad A_T = \pi r(r + s)")

            elif figura_3d == "Pirámide cuadrangular":
                modo_pir = st.radio("Dato conocido además del lado base:", ["Altura vertical (h)", "Apotema lateral (s)"], horizontal=True)
                c1, c2 = st.columns(2)
                b = c1.number_input("Lado de la base ($b$):", min_value=0.01, value=4.0, key="pir_b")
                if modo_pir == "Altura vertical (h)":
                    h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, key="pir_h")
                    s = math.hypot(b / 2.0, h)
                else:
                    s = c2.number_input("Apotema lateral ($s > b/2$):", min_value=0.02, value=5.0, key="pir_s")
                    if s <= b / 2.0:
                        st.error("⛔ La apotema lateral $s$ debe ser mayor a la mitad de la base ($b/2$).")
                        valido_3d = False
                        h = 0.0
                    else:
                        h = math.sqrt(s**2 - (b / 2.0) ** 2)
                if valido_3d:
                    params_3d = {"b": b, "h": h}
                    vol = (b**2 * h) / 3.0
                    area_lat = 2 * b * s
                    area_tot = area_lat + b**2
                    st.caption(f"Altura $h = {h:.3f}$ | Apotema lateral $s = {s:.3f}$")
                    st.latex(r"V = \frac{1}{3}b^2 h, \quad A_L = 2 b s, \quad A_T = b^2 + 2bs")

            elif figura_3d == "Prisma rectangular":
                c1, c2, c3 = st.columns(3)
                l = c1.number_input("Largo ($l$):", min_value=0.01, value=4.0, key="prect_l")
                w = c2.number_input("Ancho ($w$):", min_value=0.01, value=3.0, key="prect_w")
                h = c3.number_input("Altura ($h$):", min_value=0.01, value=5.0, key="prect_h")
                params_3d = {"l": l, "w": w, "h": h}
                vol = l * w * h
                area_lat = 2 * (l + w) * h
                area_tot = area_lat + 2 * l * w
                st.caption(f"Diagonal espacial $D = \\sqrt{{l^2+w^2+h^2}} = {math.sqrt(l**2+w**2+h**2):.3f}$")

            elif figura_3d == "Prisma triangular":
                st.caption("Base triangular isósceles de base $b$ y altura $h_{\\text{tri}}$, extruida a una altura $H$:")
                c1, c2, c3 = st.columns(3)
                b = c1.number_input("Base triángulo ($b$):", min_value=0.01, value=4.0, key="ptri_b")
                h_tri = c2.number_input("Altura triángulo ($h_{\\text{tri}}$):", min_value=0.01, value=3.0, key="ptri_l")
                h = c3.number_input("Altura prisma ($H$):", min_value=0.01, value=5.0, key="ptri_h")
                params_3d = {"b": b, "h_tri": h_tri, "h": h}
                lado_iso = math.hypot(b / 2.0, h_tri)
                area_base = (b * h_tri) / 2.0
                vol = area_base * h
                area_lat = (b + 2 * lado_iso) * h
                area_tot = area_lat + 2 * area_base

            elif figura_3d == "Toro (Dona)":
                c1, c2 = st.columns(2)
                R_may = c1.number_input("Radio Mayor ($R$):", min_value=0.1, value=4.0)
                r_men = c2.number_input("Radio del Tubo ($r < R$):", min_value=0.05, value=1.5)
                if r_men >= R_may:
                    st.error("⛔ Para un toro ordinario, el radio del tubo $r$ debe ser menor que el radio mayor $R$.")
                    valido_3d = False
                else:
                    params_3d = {"R": R_may, "r": r_men}
                    vol = 2 * (math.pi**2) * R_may * (r_men**2)
                    area_lat = 4 * (math.pi**2) * R_may * r_men
                    area_tot = area_lat
                    st.latex(r"V = 2\pi^2 R r^2, \quad A_T = 4\pi^2 R r")

            elif figura_3d == "Elipsoide":
                c1, c2, c3 = st.columns(3)
                a_e = c1.number_input("Semieje $a$:", min_value=0.1, value=4.0)
                b_e = c2.number_input("Semieje $b$:", min_value=0.1, value=3.0)
                c_e = c3.number_input("Semieje $c$:", min_value=0.1, value=2.0)
                params_3d = {"a": a_e, "b": b_e, "c": c_e}
                vol = (4.0 / 3.0) * math.pi * a_e * b_e * c_e
                p_knud = 1.6075
                area_tot = 4 * math.pi * (((a_e**p_knud * b_e**p_knud + a_e**p_knud * c_e**p_knud + b_e**p_knud * c_e**p_knud) / 3.0) ** (1.0 / p_knud))
                area_lat = area_tot
                st.latex(r"V = \frac{4}{3}\pi a b c")

            if valido_3d:
                m1, m2, m3 = st.columns(3)
                m1.metric("Volumen (V)", f"{vol:,.3f}")
                m2.metric("Área Lateral (A_L)", f"{area_lat:,.3f}")
                m3.metric("Área Total (A_T)", f"{area_tot:,.3f}")

    with col_s_3d:
        with st.container(border=True):
            titulo_tarjeta("🌐 Renderizado 3D")
            if valido_3d:
                st.pyplot(renderizar_solido_3d(figura_3d, params_3d))
