# pages/1_Geometria.py
import math
import numpy as np
import streamlit as st
import sympy as sp
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
st.set_page_config(page_title="Geometría - MATHESIS", page_icon="📐", layout="wide")

from estilos import cargar_estilos_globales  # noqa: E402
from utils import inicializar_estado  # noqa: E402

cargar_estilos_globales()
inicializar_estado()

# Paleta institucional unificada (idéntica a calculo_graficas.py)
AZUL = "#0284c7"
NARANJA = "#ea580c"
VERDE = "#16a34a"
ROJO = "#dc2626"
MORADO = "#7c3aed"
GRIS = "#6b7280"


def header_tarjeta(texto: str):
    st.markdown(f'<div class="card-header-title">{texto}</div>', unsafe_allow_html=True)


def subheader_tarjeta(texto: str):
    st.markdown(f'<div class="card-subheader-title">{texto}</div>', unsafe_allow_html=True)


# ==============================================================================
# UTILIDADES GRÁFICAS (ESTILO UNIFICADO CON EL MÓDULO DE CÁLCULO)
# ==============================================================================
def _fig_2d(w=6.2, h=4.2, titulo=""):
    fig = Figure(figsize=(w, h), dpi=110, layout="constrained")
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111)
    ax.patch.set_alpha(0.0)
    ax.grid(True, alpha=0.25, linestyle="--")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
        ax.spines[lado].set_alpha(0.6)
    ax.axhline(0, color=GRIS, lw=0.8, alpha=0.6)
    ax.axvline(0, color=GRIS, lw=0.8, alpha=0.6)
    ax.tick_params(colors=GRIS, labelsize=8.5)
    if titulo:
        ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=AZUL, pad=8)
    return fig, ax


def _fig_3d(w=6.0, h=4.8, titulo=""):
    fig = Figure(figsize=(w, h), dpi=110, layout="constrained")
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111, projection="3d")
    ax.patch.set_alpha(0.0)
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel("x", color=GRIS)
    ax.set_ylabel("y", color=GRIS)
    ax.set_zlabel("z", color=GRIS)
    ax.tick_params(colors=GRIS, labelsize=8)
    if titulo:
        ax.set_title(titulo, fontsize=10.5, fontweight="bold", color=AZUL)
    return fig, ax


def renderizar_solido_3d(figura: str, params: dict):
    fig, ax = _fig_3d(titulo=f"Vista 3D: {figura}")
    alfa = 0.55

    if figura == "Cilindro":
        r, h = params["r"], params["h"]
        z = np.linspace(0, h, 32)
        theta = np.linspace(0, 2 * np.pi, 32)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=AZUL, edgecolor="#0369a1", lw=0.3)
        lim = max(r, h / 2) * 1.2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(0, h * 1.1)

    elif figura == "Esfera":
        r = params["r"]
        u = np.linspace(0, 2 * np.pi, 32)
        v = np.linspace(0, np.pi, 32)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x, y, z, color=AZUL, alpha=alfa, edgecolor="#0369a1", lw=0.3)
        ax.set_xlim(-r * 1.2, r * 1.2)
        ax.set_ylim(-r * 1.2, r * 1.2)
        ax.set_zlim(-r * 1.2, r * 1.2)

    elif figura == "Cono":
        r, h = params["r"], params["h"]
        z = np.linspace(0, h, 32)
        theta = np.linspace(0, 2 * np.pi, 32)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r_grid = r * (1 - z_grid / h)
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=AZUL, edgecolor="#0369a1", lw=0.3)
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
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=AZUL, edgecolors="#0369a1", lw=1.0))
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
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=AZUL, edgecolors="#0369a1", lw=1.0))
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
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=AZUL, edgecolors="#0369a1", lw=1.0))
        lim = max(b, h_tri, h) * 0.8
        ax.set_xlim([-lim, lim])
        ax.set_ylim([-lim, lim])
        ax.set_zlim([0, h * 1.2])

    elif figura == "Toro (Dona)":
        R_may, r_men = params["R"], params["r"]
        u = np.linspace(0, 2 * np.pi, 32)
        v = np.linspace(0, 2 * np.pi, 32)
        U, V = np.meshgrid(u, v)
        X = (R_may + r_men * np.cos(V)) * np.cos(U)
        Y = (R_may + r_men * np.cos(V)) * np.sin(U)
        Z = r_men * np.sin(V)
        ax.plot_surface(X, Y, Z, color=AZUL, alpha=alfa, edgecolor="#0369a1", lw=0.25)
        lim = (R_may + r_men) * 1.15
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)

    return fig


# ==============================================================================
# ENCABEZADO PRINCIPAL
# ==============================================================================
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">📐 Módulo de Geometría</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("Geometría plana, analítica en $\\mathbb{R}^2$, secciones cónicas y modelado espacial en $\\mathbb{R}^3$.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📏 1. Figuras Planas 2D",
    "📈 2. Rectas y Parábolas",
    "🪐 3. Secciones Cónicas",
    "🧊 4. Sólidos y Planos 3D",
])

# ==============================================================================
# PESTAÑA 1: FIGURAS PLANAS 2D (DISEÑO ESPACIOSO SIN TRUNCAR MÉTRICAS)
# ==============================================================================
with tab1:
    with st.container(border=True):
        header_tarjeta("📏 Parámetros de la Figura Plana")

        c_sel, c_metodo = st.columns([1.2, 1.8])
        with c_sel:
            figura_2d = st.selectbox(
                "Seleccione la figura:",
                [
                    "Triángulo",
                    "Polígono Regular (n lados)",
                    "Círculo y Sector Circular",
                    "Elipse",
                    "Cuadrado",
                    "Rectángulo",
                    "Trapecio",
                ],
            )

        fig_plana, ax_p = _fig_2d(w=5.8, h=4.0, titulo=figura_2d)
        ax_p.set_aspect("equal", adjustable="box")
        datos_validos = True
        metricas = []
        resumen_extra = ""
        formula_latex = ""

        if figura_2d == "Triángulo":
            with c_metodo:
                metodo_tri = st.radio(
                    "Datos conocidos:",
                    ["Tres lados (Herón)", "Dos lados y ángulo (LAL)", "Base y Altura"],
                    horizontal=True,
                )
            st.write("")
            if metodo_tri == "Base y Altura":
                c1, c2 = st.columns(2)
                b_t = c1.number_input("Base ($b$):", min_value=0.01, value=6.0, step=0.5)
                h_t = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5)
                area = (b_t * h_t) / 2.0
                lado_iso = math.hypot(b_t / 2.0, h_t)
                perim = b_t + 2 * lado_iso
                metricas = [("Área", f"{area:,.2f}"), ("Perímetro (isósceles)", f"{perim:,.2f}")]
                formula_latex = r"A = \frac{b \cdot h}{2}"
                pts = [[-b_t / 2, 0], [b_t / 2, 0], [0, h_t]]
                ax_p.add_patch(Polygon(pts, closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2))
                lim = max(b_t, h_t) * 0.75
                ax_p.set_xlim(-lim, lim)
                ax_p.set_ylim(-0.15 * lim, lim * 1.15)
            else:
                c1, c2, c3 = st.columns(3)
                if metodo_tri == "Tres lados (Herón)":
                    a_t = c1.number_input("Lado $a$:", min_value=0.01, value=5.0, step=0.5)
                    b_t = c2.number_input("Lado $b$:", min_value=0.01, value=6.0, step=0.5)
                    c_t = c3.number_input("Lado $c$:", min_value=0.01, value=7.0, step=0.5)
                else:
                    a_t = c1.number_input("Lado $a$:", min_value=0.01, value=5.0, step=0.5, key="lal_a")
                    b_t = c2.number_input("Lado $b$:", min_value=0.01, value=6.0, step=0.5, key="lal_b")
                    ang_C = c3.number_input("Ángulo comprendido $\\gamma$ (°):", min_value=0.1, max_value=179.9, value=60.0, step=5.0)
                    c_t = math.sqrt(a_t**2 + b_t**2 - 2 * a_t * b_t * math.cos(math.radians(ang_C)))

                if not ((a_t + b_t > c_t) and (a_t + c_t > b_t) and (b_t + c_t > a_t)):
                    st.error("⛔ Esos lados violan la Desigualdad Triangular ($a + b > c$). No forman un triángulo cerrado.")
                    datos_validos = False
                else:
                    s = (a_t + b_t + c_t) / 2.0
                    area = math.sqrt(s * (s - a_t) * (s - b_t) * (s - c_t))
                    r_in = area / s
                    R_circ = (a_t * b_t * c_t) / (4.0 * area)
                    A_deg = math.degrees(math.acos(np.clip((b_t**2 + c_t**2 - a_t**2) / (2 * b_t * c_t), -1.0, 1.0)))
                    B_deg = math.degrees(math.acos(np.clip((a_t**2 + c_t**2 - b_t**2) / (2 * a_t * c_t), -1.0, 1.0)))
                    C_deg = 180.0 - A_deg - B_deg

                    metricas = [
                        ("Área (Herón)", f"{area:,.3f}"),
                        ("Perímetro", f"{2 * s:,.3f}"),
                        ("Radio Inscrito (r)", f"{r_in:,.3f}"),
                        ("Radio Circunscrito (R)", f"{R_circ:,.3f}"),
                    ]
                    resumen_extra = (
                        f"**Ángulos internos:** $\\alpha = {A_deg:.2f}^\\circ$, $\\beta = {B_deg:.2f}^\\circ$, $\\gamma = {C_deg:.2f}^\\circ$  \n"
                        f"**Lados:** $a = {a_t:.2f}$, $b = {b_t:.2f}$, $c = {c_t:.2f}$"
                    )
                    formula_latex = r"s = \frac{a+b+c}{2}, \quad A = \sqrt{s(s-a)(s-b)(s-c)}, \quad r = \frac{A}{s}, \quad R = \frac{abc}{4A}"

                    xC = b_t * math.cos(math.radians(A_deg))
                    yC = b_t * math.sin(math.radians(A_deg))
                    pts = np.array([[0.0, 0.0], [c_t, 0.0], [xC, yC]])
                    baricentro = pts.mean(axis=0)
                    ax_p.add_patch(Polygon(pts, closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2))
                    ax_p.plot(baricentro[0], baricentro[1], "o", color=NARANJA, ms=7, label=f"Baricentro ({baricentro[0]:.2f}, {baricentro[1]:.2f})")
                    ax_p.legend(fontsize=8, frameon=False)
                    lim = max(c_t, abs(xC), yC) * 1.2
                    ax_p.set_xlim(-0.15 * lim, lim)
                    ax_p.set_ylim(-0.15 * lim, max(yC * 1.25, lim * 0.6))

        elif figura_2d == "Polígono Regular (n lados)":
            c1, c2 = st.columns(2)
            n_lados = int(c1.number_input("Número de lados ($n$):", min_value=3, max_value=30, value=6, step=1))
            s_lado = c2.number_input("Longitud de cada lado ($L$):", min_value=0.01, value=4.0, step=0.5)
            perim = n_lados * s_lado
            apotema = s_lado / (2.0 * math.tan(math.pi / n_lados))
            r_circun = s_lado / (2.0 * math.sin(math.pi / n_lados))
            area = (perim * apotema) / 2.0
            ang_int = ((n_lados - 2) * 180.0) / n_lados
            diagonales = (n_lados * (n_lados - 3)) // 2

            metricas = [
                ("Área Total", f"{area:,.3f}"),
                ("Perímetro", f"{perim:,.3f}"),
                ("Apotema (r)", f"{apotema:,.3f}"),
                ("Radio Circunscrito (R)", f"{r_circun:,.3f}"),
            ]
            resumen_extra = f"**Ángulo interior:** ${ang_int:.2f}^\\circ$ | **Diagonales totales:** {diagonales}"
            formula_latex = r"a = \frac{L}{2\tan(\pi/n)}, \quad A = \frac{P \cdot a}{2}, \quad D = \frac{n(n-3)}{2}"
            angulos = np.linspace(0, 2 * np.pi, n_lados, endpoint=False) + np.pi / 2
            verts = np.column_stack([r_circun * np.cos(angulos), r_circun * np.sin(angulos)])
            ax_p.add_patch(Polygon(verts, closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2))
            ax_p.set_xlim(-r_circun * 1.25, r_circun * 1.25)
            ax_p.set_ylim(-r_circun * 1.25, r_circun * 1.25)

        elif figura_2d == "Círculo y Sector Circular":
            c1, c2 = st.columns(2)
            r_circ = c1.number_input("Radio ($r$):", min_value=0.01, value=3.0, step=0.5)
            ang_sec = c2.number_input("Ángulo del sector (°):", min_value=1.0, max_value=360.0, value=90.0, step=15.0)
            area_tot = math.pi * r_circ**2
            perim_tot = 2 * math.pi * r_circ
            area_sec = area_tot * (ang_sec / 360.0)
            long_arco = perim_tot * (ang_sec / 360.0)
            metricas = [
                ("Área del Círculo", f"{area_tot:,.3f}"),
                ("Circunferencia", f"{perim_tot:,.3f}"),
                ("Área del Sector", f"{area_sec:,.3f}"),
                ("Longitud de Arco", f"{long_arco:,.3f}"),
            ]
            formula_latex = r"A = \pi r^2, \quad L_{\text{arco}} = r\theta_{\text{rad}}, \quad A_{\text{sector}} = \frac{1}{2}r^2\theta_{\text{rad}}"
            ax_p.add_patch(Circle((0, 0), r_circ, facecolor=AZUL, alpha=0.15, edgecolor=AZUL, lw=2))
            th = np.linspace(0, math.radians(ang_sec), 80)
            pts_sec = np.vstack([[0, 0], np.column_stack([r_circ * np.cos(th), r_circ * np.sin(th)])])
            ax_p.add_patch(Polygon(pts_sec, closed=True, facecolor=NARANJA, alpha=0.35, edgecolor=NARANJA, lw=1.8))
            ax_p.set_xlim(-r_circ * 1.25, r_circ * 1.25)
            ax_p.set_ylim(-r_circ * 1.25, r_circ * 1.25)

        elif figura_2d == "Elipse":
            c1, c2 = st.columns(2)
            a_el = c1.number_input("Semieje horizontal ($a$):", min_value=0.01, value=5.0, step=0.5)
            b_el = c2.number_input("Semieje vertical ($b$):", min_value=0.01, value=3.0, step=0.5)
            area = math.pi * a_el * b_el
            h_ram = ((a_el - b_el) ** 2) / ((a_el + b_el) ** 2)
            perim = math.pi * (a_el + b_el) * (1 + (3 * h_ram) / (10 + math.sqrt(4 - 3 * h_ram)))
            c_foco = math.sqrt(abs(a_el**2 - b_el**2))
            exc = c_foco / max(a_el, b_el)
            metricas = [
                ("Área", f"{area:,.3f}"),
                ("Perímetro aprox.", f"{perim:,.3f}"),
                ("Distancia Focal (c)", f"{c_foco:,.3f}"),
                ("Excentricidad (e)", f"{exc:,.4f}"),
            ]
            formula_latex = r"A = \pi a b, \quad c = \sqrt{|a^2 - b^2|}, \quad e = \frac{c}{\max(a,b)}"
            ax_p.add_patch(Ellipse((0, 0), 2 * a_el, 2 * b_el, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2))
            lim = max(a_el, b_el) * 1.25
            ax_p.set_xlim(-lim, lim)
            ax_p.set_ylim(-lim, lim)

        elif figura_2d == "Cuadrado":
            L = st.number_input("Lado del cuadrado ($L$):", min_value=0.01, value=4.0, step=0.5)
            metricas = [
                ("Área", f"{L**2:,.3f}"),
                ("Perímetro", f"{4 * L:,.3f}"),
                ("Diagonal", f"{L * math.sqrt(2):,.3f}"),
                ("Radio inscrito", f"{L / 2:,.3f}"),
            ]
            formula_latex = r"A = L^2, \quad P = 4L, \quad d = L\sqrt{2}"
            poly = Polygon([[-L / 2, -L / 2], [L / 2, -L / 2], [L / 2, L / 2], [-L / 2, L / 2]], closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2)
            ax_p.add_patch(poly)
            ax_p.set_xlim(-L * 0.8, L * 0.8)
            ax_p.set_ylim(-L * 0.8, L * 0.8)

        elif figura_2d == "Rectángulo":
            c1, c2 = st.columns(2)
            b_rect = c1.number_input("Base ($b$):", min_value=0.01, value=6.0, step=0.5)
            h_rect = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5)
            metricas = [
                ("Área", f"{b_rect * h_rect:,.3f}"),
                ("Perímetro", f"{2 * (b_rect + h_rect):,.3f}"),
                ("Diagonal", f"{math.hypot(b_rect, h_rect):,.3f}"),
            ]
            formula_latex = r"A = b \cdot h, \quad P = 2(b + h), \quad d = \sqrt{b^2 + h^2}"
            poly = Polygon([[-b_rect / 2, -h_rect / 2], [b_rect / 2, -h_rect / 2], [b_rect / 2, h_rect / 2], [-b_rect / 2, h_rect / 2]], closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2)
            ax_p.add_patch(poly)
            lim = max(b_rect, h_rect) * 0.75
            ax_p.set_xlim(-lim, lim)
            ax_p.set_ylim(-lim, lim)

        elif figura_2d == "Trapecio":
            c1, c2, c3 = st.columns(3)
            B_may = c1.number_input("Base mayor ($B$):", min_value=0.01, value=8.0, step=0.5)
            b_men = c2.number_input("Base menor ($b$):", min_value=0.01, value=4.0, step=0.5)
            h_trap = c3.number_input("Altura ($h$):", min_value=0.01, value=3.0, step=0.5)
            lado_lat = math.hypot((B_may - b_men) / 2.0, h_trap)
            metricas = [
                ("Área", f"{((B_may + b_men) * h_trap) / 2.0:,.3f}"),
                ("Perímetro (isósceles)", f"{B_may + b_men + 2 * lado_lat:,.3f}"),
                ("Mediana", f"{(B_may + b_men) / 2.0:,.3f}"),
                ("Lado oblicuo", f"{lado_lat:,.3f}"),
            ]
            formula_latex = r"A = \frac{(B + b)\cdot h}{2}"
            pts_t = [[-B_may / 2, -h_trap / 2], [B_may / 2, -h_trap / 2], [b_men / 2, h_trap / 2], [-b_men / 2, h_trap / 2]]
            ax_p.add_patch(Polygon(pts_t, closed=True, facecolor=AZUL, alpha=0.22, edgecolor=AZUL, lw=2.2))
            lim = max(B_may, h_trap) * 0.75
            ax_p.set_xlim(-lim, lim)
            ax_p.set_ylim(-lim, lim)

    if datos_validos:
        st.write("")
        col_res, col_graf = st.columns([1.05, 1.15], gap="large")

        with col_res:
            with st.container(border=True):
                subheader_tarjeta("📊 Resultados Métricos")
                # Máximo 2 métricas por renglón para que jamás se corten los números
                for i in range(0, len(metricas), 2):
                    par = metricas[i:i + 2]
                    cols_m = st.columns(2)
                    for j, (et, val) in enumerate(par):
                        cols_m[j].metric(et, val)
                    st.write("")

                if resumen_extra:
                    st.info(resumen_extra)

                if formula_latex:
                    with st.expander("📖 Ver fórmulas aplicadas", expanded=True):
                        st.latex(formula_latex)

        with col_graf:
            with st.container(border=True):
                subheader_tarjeta("🖼️ Representación a Escala")
                st.pyplot(fig_plana)


# ==============================================================================
# PESTAÑA 2: GEOMETRÍA ANALÍTICA EN R² (RECTAS Y PARÁBOLAS)
# ==============================================================================
with tab2:
    with st.container(border=True):
        header_tarjeta("📈 Herramientas de Geometría Analítica")
        herramienta = st.radio(
            "Seleccione el análisis:",
            [
                "📍 Recta por 2 Puntos y Distancia",
                "⚔️ Intersección de 2 Rectas",
                "📐 Parábola / Ecuación Cuadrática",
            ],
            horizontal=True,
        )
        st.divider()

        if "Recta por 2 Puntos" in herramienta:
            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                st.markdown("**Punto $A(x_1, y_1)$**")
                x1 = st.number_input("x₁:", value=-2.0, step=1.0)
                y1 = st.number_input("y₁:", value=1.0, step=1.0)
            with c2:
                st.markdown("**Punto $B(x_2, y_2)$**")
                x2 = st.number_input("x₂:", value=4.0, step=1.0)
                y2 = st.number_input("y₂:", value=5.0, step=1.0)
            with c3:
                st.markdown("**Punto Externo $P_0(x_0, y_0)$**")
                x0 = st.number_input("x₀:", value=2.0, step=1.0)
                y0 = st.number_input("y₀:", value=-1.0, step=1.0)

            dx, dy = x2 - x1, y2 - y1
            dist_ab = math.hypot(dx, dy)
            xm, ym = (x1 + x2) / 2.0, (y1 + y2) / 2.0

            if dist_ab < 1e-12:
                st.error("Los puntos $A$ y $B$ son idénticos: no definen una única recta.")
            else:
                A_r, B_r, C_r = dy, -dx, dx * y1 - dy * x1
                dist_p0 = abs(A_r * x0 + B_r * y0 + C_r) / math.hypot(A_r, B_r)
                factor_p = (A_r * x0 + B_r * y0 + C_r) / (A_r**2 + B_r**2)
                xp, yp = x0 - A_r * factor_p, y0 - B_r * factor_p

                st.write("")
                col_r, col_g = st.columns([1.05, 1.15], gap="large")
                with col_r:
                    m1, m2 = st.columns(2)
                    m1.metric("Distancia d(A, B)", f"{dist_ab:,.3f}")
                    m2.metric("Punto Medio M", f"({xm:.2f}, {ym:.2f})")
                    st.write("")
                    m3, m4 = st.columns(2)
                    m3.metric("Distancia d(P₀, Recta)", f"{dist_p0:,.3f}")
                    if abs(dx) > 1e-12:
                        m_pend = dy / dx
                        ang_inc = math.degrees(math.atan(m_pend))
                        if ang_inc < 0:
                            ang_inc += 180.0
                        b_ord = y1 - m_pend * x1
                        m4.metric("Pendiente (m)", f"{m_pend:,.3f}")
                        signo_b = "+" if b_ord >= 0 else "-"
                        st.latex(rf"y = {m_pend:.4g}x {signo_b} {abs(b_ord):.4g} \quad (\theta = {ang_inc:.2f}^\circ)")
                    else:
                        m4.metric("Pendiente (m)", "Indefinida (90°)")
                        st.latex(rf"x = {x1:.4g}")
                    st.latex(rf"\text{{Forma General: }} ({A_r:.4g})x + ({B_r:.4g})y + ({C_r:.4g}) = 0")

                with col_g:
                    fig_r, ax_r = _fig_2d(titulo="Recta AB y proyección desde P₀")
                    xmin, xmax = min(x1, x2, x0, xp) - 2.5, max(x1, x2, x0, xp) + 2.5
                    if abs(dx) > 1e-12:
                        xx = np.linspace(xmin, xmax, 200)
                        ax_r.plot(xx, m_pend * (xx - x1) + y1, color=AZUL, lw=2.2, label="Recta AB")
                    else:
                        ax_r.axvline(x1, color=AZUL, lw=2.2, label="Recta AB")
                    ax_r.plot([x0, xp], [y0, yp], ls="--", color=ROJO, lw=1.6, label=f"d = {dist_p0:.2f}")
                    ax_r.plot([x1, x2], [y1, y2], "o", color=AZUL, ms=6)
                    ax_r.plot([xm], [ym], "s", color=VERDE, ms=6, label="Punto Medio")
                    ax_r.plot([x0], [y0], "o", color=ROJO, ms=6, label="P₀")
                    ax_r.legend(fontsize=8, frameon=False)
                    st.pyplot(fig_r)

        elif "Intersección de 2 Rectas" in herramienta:
            c1, c2 = st.columns(2, gap="large")
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

            n1, n2 = math.hypot(a1, b1), math.hypot(a2, b2)
            if n1 < 1e-12 or n2 < 1e-12:
                st.error("Los coeficientes $A$ y $B$ de cada recta no pueden ser ambos cero.")
            else:
                det_sis = a1 * b2 - a2 * b1
                cos_ang = abs(a1 * a2 + b1 * b2) / (n1 * n2)
                ang_agudo = math.degrees(math.acos(np.clip(cos_ang, 0.0, 1.0)))

                st.write("")
                if abs(det_sis) < 1e-12:
                    if abs(a1 * c2_v - a2 * c1_v) < 1e-12 and abs(b1 * c2_v - b2 * c1_v) < 1e-12:
                        st.info("Las dos rectas son **COINCIDENTES**.")
                    else:
                        st.warning("Las dos rectas son **PARALELAS** (no se cortan).")
                else:
                    xi = (b1 * c2_v - b2 * c1_v) / det_sis
                    yi = (c1_v * a2 - c2_v * a1) / det_sis
                    col_r, col_g = st.columns([1, 1.2], gap="large")
                    with col_r:
                        m1, m2 = st.columns(2)
                        m1.metric("Intersección (x, y)", f"({xi:.2f}, {yi:.2f})")
                        m2.metric("Ángulo entre rectas", f"{ang_agudo:.2f}°")
                        st.success("Rectas **Perpendiculares**" if abs(ang_agudo - 90.0) < 1e-5 else "Rectas **Secantes**")
                    with col_g:
                        fig_l, ax_l = _fig_2d(titulo=f"Intersección en ({xi:.2f}, {yi:.2f})")
                        xx = np.linspace(xi - 5, xi + 5, 200)
                        for ai, bi, ci, col, lab in ((a1, b1, c1_v, AZUL, "L₁"), (a2, b2, c2_v, NARANJA, "L₂")):
                            if abs(bi) > 1e-12:
                                ax_l.plot(xx, (-ai * xx - ci) / bi, color=col, lw=2.2, label=lab)
                            else:
                                ax_l.axvline(-ci / ai, color=col, lw=2.2, label=lab)
                        ax_l.plot([xi], [yi], "o", color=ROJO, ms=7, zorder=6)
                        ax_l.set_xlim(xi - 5, xi + 5)
                        ax_l.set_ylim(yi - 5, yi + 5)
                        ax_l.legend(fontsize=8, frameon=False)
                        st.pyplot(fig_l)

        else:
            st.markdown("Ecuación cuadrática de la forma: $y = Ax^2 + Bx + C$")
            c1, c2, c3 = st.columns(3, gap="medium")
            a_coef = c1.number_input("Coeficiente $A$:", value=1.0, step=0.5)
            b_coef = c2.number_input("Coeficiente $B$:", value=-4.0, step=0.5)
            c_coef = c3.number_input("Coeficiente $C$:", value=3.0, step=0.5)

            if a_coef == 0 and b_coef == 0:
                st.warning("No es una ecuación válida ($A = 0$ y $B = 0$).")
            elif a_coef == 0:
                st.info(f"Es una función lineal con raíz en $x = {-c_coef / b_coef:.4f}$.")
            else:
                disc = b_coef**2 - 4 * a_coef * c_coef
                xv = -b_coef / (2.0 * a_coef)
                yv = a_coef * xv**2 + b_coef * xv + c_coef
                p_focal = 1.0 / (4.0 * a_coef)
                yf = yv + p_focal
                y_dir = yv - p_focal

                st.write("")
                col_r, col_g = st.columns([1.05, 1.15], gap="large")
                with col_r:
                    m1, m2 = st.columns(2)
                    m1.metric("Vértice V(h, k)", f"({xv:.2f}, {yv:.2f})")
                    m2.metric("Foco F", f"({xv:.2f}, {yf:.2f})")
                    st.write("")
                    m3, m4 = st.columns(2)
                    m3.metric("Directriz", f"y = {y_dir:.2f}")
                    m4.metric("Discriminante (Δ)", f"{disc:.2f}")

                    if disc >= 0:
                        x1 = (-b_coef + math.sqrt(disc)) / (2 * a_coef)
                        x2 = (-b_coef - math.sqrt(disc)) / (2 * a_coef)
                        st.success(f"**Raíces Reales:** $x_1 = {x1:.3f}$, $x_2 = {x2:.3f}$")
                    else:
                        re_p = -b_coef / (2 * a_coef)
                        im_p = abs(math.sqrt(-disc) / (2 * a_coef))
                        st.warning(f"**Raíces Complejas:** $x = {re_p:.3f} \\pm {im_p:.3f}i$")

                with col_g:
                    ancho = max(5.0, abs(math.sqrt(abs(disc)) / a_coef) * 1.4)
                    xx = np.linspace(xv - ancho, xv + ancho, 400)
                    yy = a_coef * xx**2 + b_coef * xx + c_coef
                    fig_q, ax_q = _fig_2d(titulo="Parábola f(x) = Ax² + Bx + C")
                    ax_q.plot(xx, yy, color=AZUL, lw=2.3, label="f(x)")
                    ax_q.axhline(y_dir, color=ROJO, ls=":", lw=1.4, label=f"Directriz y={y_dir:.2f}")
                    ax_q.plot([xv], [yv], "o", color=VERDE, ms=7, label="Vértice")
                    ax_q.plot([xv], [yf], "*", color=NARANJA, ms=8, label="Foco")
                    if disc >= 0:
                        ax_q.plot([x1, x2], [0, 0], "o", color=ROJO, ms=6, label="Raíces")
                    ax_q.legend(fontsize=8, frameon=False)
                    st.pyplot(fig_q)


# ==============================================================================
# PESTAÑA 3: SECCIONES CÓNICAS (Ax² + Bxy + Cy² + Dx + Ey + F = 0)
# ==============================================================================
with tab3:
    with st.container(border=True):
        header_tarjeta("🪐 Clasificador de Secciones Cónicas y Rotación de Ejes")
        st.caption("Ingrese los coeficientes de la ecuación general $Ax^2 + Bxy + Cy^2 + Dx + Ey + F = 0$:")

        c1, c2, c3 = st.columns(3, gap="medium")
        A_c = c1.number_input("Coeficiente $A$ ($x^2$):", value=5.0, step=1.0)
        B_c = c2.number_input("Coeficiente $B$ ($xy$):", value=4.0, step=1.0)
        C_c = c3.number_input("Coeficiente $C$ ($y^2$):", value=2.0, step=1.0)

        c4, c5, c6 = st.columns(3, gap="medium")
        D_c = c4.number_input("Coeficiente $D$ ($x$):", value=0.0, step=1.0)
        E_c = c5.number_input("Coeficiente $E$ ($y$):", value=0.0, step=1.0)
        F_c = c6.number_input("Término independiente $F$:", value=-6.0, step=1.0)

        if abs(A_c) < 1e-12 and abs(B_c) < 1e-12 and abs(C_c) < 1e-12:
            st.warning("Al menos uno de los coeficientes cuadráticos ($A, B, C$) debe ser distinto de cero.")
        else:
            inv_I = B_c**2 - 4 * A_c * C_c
            M_3 = np.array([
                [A_c, B_c / 2.0, D_c / 2.0],
                [B_c / 2.0, C_c, E_c / 2.0],
                [D_c / 2.0, E_c / 2.0, F_c],
            ])
            det_3 = float(np.linalg.det(M_3))

            if abs(inv_I) < 1e-10:
                tipo_con = "Parábola" if abs(det_3) > 1e-10 else "Parábola Degenerada"
            elif inv_I < 0:
                if abs(det_3) < 1e-10:
                    tipo_con = "Punto Único"
                elif det_3 * (A_c + C_c) > 0:
                    tipo_con = "Conjunto Vacío en ℝ²"
                elif abs(A_c - C_c) < 1e-10 and abs(B_c) < 1e-10:
                    tipo_con = "Circunferencia"
                else:
                    tipo_con = "Elipse"
            else:
                tipo_con = "Hipérbola" if abs(det_3) > 1e-10 else "Dos Rectas que se Cortan"

            if abs(B_c) < 1e-12:
                theta_rad = 0.0
            elif abs(A_c - C_c) < 1e-12:
                theta_rad = math.pi / 4.0
            else:
                theta_rad = 0.5 * math.atan2(B_c, A_c - C_c)
            theta_deg = math.degrees(theta_rad)

            cx_c, cy_c = 0.0, 0.0
            if abs(inv_I) > 1e-10:
                sol_c = np.linalg.solve([[2 * A_c, B_c], [B_c, 2 * C_c]], [-D_c, -E_c])
                cx_c, cy_c = float(sol_c[0]), float(sol_c[1])

            st.write("")
            col_r, col_g = st.columns([1.05, 1.15], gap="large")
            with col_r:
                m1, m2 = st.columns(2)
                m1.metric("Tipo de Cónica", tipo_con)
                m2.metric("Ángulo de Rotación θ", f"{theta_deg:.2f}°")
                st.write("")
                m3, m4 = st.columns(2)
                m3.metric("Discriminante B²-4AC", f"{inv_I:.2f}")
                m4.metric("Centro", f"({cx_c:.2f}, {cy_c:.2f})" if abs(inv_I) > 1e-10 else "No central")

            with col_g:
                fig_c, ax_c = _fig_2d(titulo=f"Lugar Geométrico: {tipo_con}")
                ax_c.set_aspect("equal", adjustable="box")
                r_vent = max(5.0, abs(cx_c) + 4.5, abs(cy_c) + 4.5)
                Xg, Yg = np.meshgrid(np.linspace(cx_c - r_vent, cx_c + r_vent, 300), np.linspace(cy_c - r_vent, cy_c + r_vent, 300))
                Zg = A_c * Xg**2 + B_c * Xg * Yg + C_c * Yg**2 + D_c * Xg + E_c * Yg + F_c
                if np.nanmin(Zg) <= 0 <= np.nanmax(Zg):
                    ax_c.contour(Xg, Yg, Zg, levels=[0], colors=[AZUL], linewidths=2.3)
                if abs(B_c) > 1e-10:
                    tt = np.linspace(-r_vent, r_vent, 100)
                    ax_c.plot(cx_c + tt * math.cos(theta_rad), cy_c + tt * math.sin(theta_rad), ls="--", color=NARANJA, lw=1.2, label=f"Eje rotado ({theta_deg:.1f}°)")
                    ax_c.legend(fontsize=8, frameon=False)
                st.pyplot(fig_c)


# ==============================================================================
# PESTAÑA 4: SÓLIDOS 3D Y COORDENADAS ESPACIALES
# ==============================================================================
with tab4:
    with st.container(border=True):
        header_tarjeta("🧊 Cálculo de Sólidos en ℝ³")
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
            ],
        )

        params_3d = {}
        vol = area_lat = area_tot = 0.0
        valido_3d = True

        if figura_3d == "Cilindro":
            c1, c2 = st.columns(2)
            r = c1.number_input("Radio ($r$):", min_value=0.01, value=2.0, step=0.5, key="cil_r")
            h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5, key="cil_h")
            params_3d = {"r": r, "h": h}
            vol = math.pi * r**2 * h
            area_lat = 2 * math.pi * r * h
            area_tot = area_lat + 2 * math.pi * r**2

        elif figura_3d == "Esfera":
            r = st.number_input("Radio ($r$):", min_value=0.01, value=3.0, step=0.5, key="esf_r")
            params_3d = {"r": r}
            vol = (4.0 / 3.0) * math.pi * r**3
            area_lat = 4 * math.pi * r**2
            area_tot = area_lat

        elif figura_3d == "Cono":
            c1, c2 = st.columns(2)
            r = c1.number_input("Radio ($r$):", min_value=0.01, value=3.0, step=0.5, key="cono_r")
            h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5, key="cono_h")
            s = math.hypot(r, h)
            params_3d = {"r": r, "h": h}
            vol = (math.pi * r**2 * h) / 3.0
            area_lat = math.pi * r * s
            area_tot = area_lat + math.pi * r**2

        elif figura_3d == "Pirámide cuadrangular":
            c1, c2 = st.columns(2)
            b = c1.number_input("Lado de la base ($b$):", min_value=0.01, value=4.0, step=0.5, key="pir_b")
            h = c2.number_input("Altura ($h$):", min_value=0.01, value=4.0, step=0.5, key="pir_h")
            s = math.hypot(b / 2.0, h)
            params_3d = {"b": b, "h": h}
            vol = (b**2 * h) / 3.0
            area_lat = 2 * b * s
            area_tot = area_lat + b**2

        elif figura_3d == "Prisma rectangular":
            c1, c2, c3 = st.columns(3)
            l = c1.number_input("Largo ($l$):", min_value=0.01, value=4.0, step=0.5, key="prect_l")
            w = c2.number_input("Ancho ($w$):", min_value=0.01, value=3.0, step=0.5, key="prect_w")
            h = c3.number_input("Altura ($h$):", min_value=0.01, value=5.0, step=0.5, key="prect_h")
            params_3d = {"l": l, "w": w, "h": h}
            vol = l * w * h
            area_lat = 2 * (l + w) * h
            area_tot = area_lat + 2 * l * w

        elif figura_3d == "Prisma triangular":
            c1, c2, c3 = st.columns(3)
            b = c1.number_input("Base triángulo ($b$):", min_value=0.01, value=4.0, step=0.5, key="ptri_b")
            h_tri = c2.number_input("Altura triángulo ($h_t$):", min_value=0.01, value=3.0, step=0.5, key="ptri_l")
            h = c3.number_input("Altura prisma ($H$):", min_value=0.01, value=5.0, step=0.5, key="ptri_h")
            params_3d = {"b": b, "h_tri": h_tri, "h": h}
            lado_iso = math.hypot(b / 2.0, h_tri)
            area_base = (b * h_tri) / 2.0
            vol = area_base * h
            area_lat = (b + 2 * lado_iso) * h
            area_tot = area_lat + 2 * area_base

        elif figura_3d == "Toro (Dona)":
            c1, c2 = st.columns(2)
            R_may = c1.number_input("Radio Mayor ($R$):", min_value=0.1, value=4.0, step=0.5)
            r_men = c2.number_input("Radio del Tubo ($r < R$):", min_value=0.05, value=1.5, step=0.25)
            if r_men >= R_may:
                st.error("⛔ El radio del tubo $r$ debe ser menor que el radio mayor $R$.")
                valido_3d = False
            else:
                params_3d = {"R": R_may, "r": r_men}
                vol = 2 * (math.pi**2) * R_may * (r_men**2)
                area_lat = 4 * (math.pi**2) * R_may * r_men
                area_tot = area_lat

        if valido_3d:
            st.write("")
            col_r3d, col_g3d = st.columns([1, 1.15], gap="large")
            with col_r3d:
                m1, m2 = st.columns(2)
                m1.metric("Volumen (V)", f"{vol:,.3f}")
                m2.metric("Área Total (A_T)", f"{area_tot:,.3f}")
                st.write("")
                st.metric("Área Lateral (A_L)", f"{area_lat:,.3f}")
            with col_g3d:
                st.pyplot(renderizar_solido_3d(figura_3d, params_3d))
