# pages/1_Geometria.py
import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Circle, Polygon
from matplotlib.ticker import AutoMinorLocator

st.set_page_config(page_title="Geometría Analítica - MATHESIS", page_icon="📐", layout="wide")

from estilos import cargar_estilos_globales, encabezado_pagina, header_tarjeta, subheader_tarjeta  # noqa: E402
from utils import inicializar_estado, mostrar_figura_segura  # noqa: E402

cargar_estilos_globales()
inicializar_estado()

AZUL = "#0369a1"
NARANJA = "#ea580c"
VERDE = "#15803d"
ROJO = "#dc2626"
MORADO = "#7c3aed"
OSCURO = "#1e293b"
CLARO = "#cbd5e1"
FONDO = "#ffffff"


# ==============================================================================
# UTILIDADES DE ESTILO GRÁFICO (LIBRO DE TEXTO)
# ==============================================================================
def _crear_fig_2d(w=6.6, h=5.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110, facecolor=FONDO)
    ax.set_facecolor("#fbfdff")
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="major", color=CLARO, lw=0.9, alpha=0.9)
    ax.grid(True, which="minor", color="#e2e8f0", lw=0.5, alpha=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(OSCURO)
        ax.spines[s].set_linewidth(1.4)
    ax.tick_params(colors=OSCURO, labelsize=9)
    ax.set_aspect("equal", adjustable="box")
    return fig, ax


def _anotar_pt(ax, x, y, etiqueta, color=ROJO, dx=10, dy=10):
    ax.plot([x], [y], "o", color=color, mec="white", mew=1.3, ms=7.5, zorder=7)
    texto = f"{etiqueta} ({x:.2f}, {y:.2f})"
    ax.annotate(
        texto,
        (x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=8.5,
        color=OSCURO,
        zorder=9,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=1.0, alpha=0.95),
    )


def _crear_fig_3d(w=6.8, h=5.4, titulo=""):
    fig = plt.figure(figsize=(w, h), dpi=110, facecolor=FONDO)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlabel("X", fontweight="bold", labelpad=5)
    ax.set_ylabel("Y", fontweight="bold", labelpad=5)
    ax.set_zlabel("Z", fontweight="bold", labelpad=5)
    ax.tick_params(labelsize=8, colors=OSCURO)
    ax.view_init(elev=24, azim=-55)
    if titulo:
        ax.set_title(titulo, fontsize=11, fontweight="bold", color=OSCURO, pad=10)
    return fig, ax


encabezado_pagina(
    "📐 Módulo de Geometría Euclidiana y Analítica (ℝ² y ℝ³)",
    "Análisis de triángulos, recta de Euler, rectas, secciones cónicas con rotación de ejes, planos, rectas en ℝ³ y superficies cuádricas interactivas.",
)

tab_2d, tab_analitica_2d, tab_3d = st.tabs([
    "📐 1. Triángulos y Figuras Planas",
    "📈 2. Rectas y Cónicas en ℝ²",
    "🧊 3. Sólidos, Planos, Rectas y Cuádricas en ℝ³",
])


# ==============================================================================
# PESTAÑA 1: TRIÁNGULOS Y FIGURAS PLANAS
# ==============================================================================
with tab_2d:
    modo_2d = st.radio(
        "Seleccione el objeto geométrico a estudiar:",
        [
            "Triángulo Completo (Puntos Notables y Recta de Euler)",
            "Círculo, Corona y Sector Circular",
            "Polígono Regular de n Lados",
            "Trapecio Simétrico",
        ],
        horizontal=True,
        key="geo_modo_2d",
    )

    st.divider()

    if modo_2d.startswith("Triángulo"):
        col_in, col_out = st.columns([1, 1.35])
        with col_in:
            with st.container(border=True):
                header_tarjeta("Definición del Triángulo")
                metodo_tri = st.selectbox(
                    "Método de entrada:",
                    [
                        "1. Tres lados (LLL)",
                        "2. Dos lados y el ángulo comprendido (LAL)",
                        "3. Un lado y dos ángulos adyacentes (ALA)",
                        "4. Coordenadas de los 3 vértices A, B, C",
                    ],
                    key="tri_metodo",
                )

                valido_tri = True
                A_pt = B_pt = C_pt = None

                if metodo_tri.startswith("1."):
                    c1, c2, c3 = st.columns(3)
                    a = c1.number_input("Lado a (BC):", min_value=0.01, value=5.0, step=0.5, key="tri_a")
                    b = c2.number_input("Lado b (AC):", min_value=0.01, value=6.0, step=0.5, key="tri_b")
                    c = c3.number_input("Lado c (AB):", min_value=0.01, value=7.0, step=0.5, key="tri_c")
                    if a + b <= c or a + c <= b or b + c <= a:
                        st.error("⛔ Violación de la Desigualdad Triangular: la suma de dos lados debe ser estrictamente mayor que el tercero.")
                        valido_tri = False
                    else:
                        A_pt = np.array([0.0, 0.0])
                        B_pt = np.array([float(c), 0.0])
                        cos_A = np.clip((b**2 + c**2 - a**2) / (2 * b * c), -1.0, 1.0)
                        sin_A = math.sqrt(max(0.0, 1.0 - cos_A**2))
                        C_pt = np.array([b * cos_A, b * sin_A])

                elif metodo_tri.startswith("2."):
                    c1, c2, c3 = st.columns(3)
                    b = c1.number_input("Lado b (AC):", min_value=0.01, value=6.0, step=0.5, key="lal_b")
                    c = c2.number_input("Lado c (AB):", min_value=0.01, value=8.0, step=0.5, key="lal_c")
                    ang_A_deg = c3.number_input("Ángulo α (en A, °):", min_value=0.1, max_value=179.9, value=60.0, step=1.0, key="lal_ang")
                    ang_A = math.radians(ang_A_deg)
                    A_pt = np.array([0.0, 0.0])
                    B_pt = np.array([float(c), 0.0])
                    C_pt = np.array([b * math.cos(ang_A), b * math.sin(ang_A)])

                elif metodo_tri.startswith("3."):
                    c1, c2, c3 = st.columns(3)
                    c = c1.number_input("Lado base c (AB):", min_value=0.01, value=8.0, step=0.5, key="ala_c")
                    ang_A_deg = c2.number_input("Ángulo α (en A, °):", min_value=0.1, max_value=179.0, value=45.0, step=1.0, key="ala_a")
                    ang_B_deg = c3.number_input("Ángulo β (en B, °):", min_value=0.1, max_value=179.0, value=60.0, step=1.0, key="ala_b")
                    if ang_A_deg + ang_B_deg >= 180.0:
                        st.error("⛔ La suma de los ángulos α + β debe ser estrictamente menor que 180°.")
                        valido_tri = False
                    else:
                        ang_C_deg = 180.0 - (ang_A_deg + ang_B_deg)
                        ang_A = math.radians(ang_A_deg)
                        ang_C = math.radians(ang_C_deg)
                        b = c * math.sin(math.radians(ang_B_deg)) / math.sin(ang_C)
                        A_pt = np.array([0.0, 0.0])
                        B_pt = np.array([float(c), 0.0])
                        C_pt = np.array([b * math.cos(ang_A), b * math.sin(ang_A)])

                else:
                    ca1, ca2 = st.columns(2)
                    ax_v = ca1.number_input("A_x:", value=0.0, step=1.0, key="v_ax")
                    ay_v = ca2.number_input("A_y:", value=0.0, step=1.0, key="v_ay")
                    cb1, cb2 = st.columns(2)
                    bx_v = cb1.number_input("B_x:", value=6.0, step=1.0, key="v_bx")
                    by_v = cb2.number_input("B_y:", value=0.0, step=1.0, key="v_by")
                    cc1, cc2 = st.columns(2)
                    cx_v = cc1.number_input("C_x:", value=2.0, step=1.0, key="v_cx")
                    cy_v = cc2.number_input("C_y:", value=4.0, step=1.0, key="v_cy")
                    A_pt = np.array([ax_v, ay_v], dtype=float)
                    B_pt = np.array([bx_v, by_v], dtype=float)
                    C_pt = np.array([cx_v, cy_v], dtype=float)
                    det_col = abs((B_pt[0] - A_pt[0]) * (C_pt[1] - A_pt[1]) - (C_pt[0] - A_pt[0]) * (B_pt[1] - A_pt[1]))
                    if det_col < 1e-9:
                        st.error("⛔ Los tres puntos A, B y C son colineales (están sobre la misma recta): no forman un triángulo.")
                        valido_tri = False

                subheader_tarjeta("Capas en la gráfica")
                ver_in = st.checkbox("Mostrar Incentro y Circunferencia Inscrita", value=True, key="tri_chk_in")
                ver_circ = st.checkbox("Mostrar Circuncentro y Circunscrita", value=True, key="tri_chk_circ")
                ver_euler = st.checkbox("Mostrar Baricentro, Ortocentro y Recta de Euler", value=True, key="tri_chk_euler")

        if valido_tri and A_pt is not None:
            a = float(np.linalg.norm(B_pt - C_pt))
            b = float(np.linalg.norm(A_pt - C_pt))
            c = float(np.linalg.norm(A_pt - B_pt))
            perimetro = a + b + c
            s = perimetro / 2.0
            area = 0.5 * abs((B_pt[0] - A_pt[0]) * (C_pt[1] - A_pt[1]) - (C_pt[0] - A_pt[0]) * (B_pt[1] - A_pt[1]))

            alpha = math.degrees(math.acos(np.clip((b**2 + c**2 - a**2) / (2 * b * c), -1.0, 1.0)))
            beta = math.degrees(math.acos(np.clip((a**2 + c**2 - b**2) / (2 * a * c), -1.0, 1.0)))
            gamma = 180.0 - alpha - beta

            ha, hb, hc = 2 * area / a, 2 * area / b, 2 * area / c
            ma = 0.5 * math.sqrt(2 * b**2 + 2 * c**2 - a**2)
            mb = 0.5 * math.sqrt(2 * a**2 + 2 * c**2 - b**2)
            mc = 0.5 * math.sqrt(2 * a**2 + 2 * b**2 - c**2)
            ba = (2 * b * c * math.cos(math.radians(alpha / 2))) / (b + c)
            bb = (2 * a * c * math.cos(math.radians(beta / 2))) / (a + c)
            bc = (2 * a * b * math.cos(math.radians(gamma / 2))) / (a + b)

            r_in = area / s
            R_circ = (a * b * c) / (4.0 * area)
            G_pt = (A_pt + B_pt + C_pt) / 3.0
            I_pt = (a * A_pt + b * B_pt + c * C_pt) / perimetro

            d_det = 2.0 * (A_pt[0] * (B_pt[1] - C_pt[1]) + B_pt[0] * (C_pt[1] - A_pt[1]) + C_pt[0] * (A_pt[1] - B_pt[1]))
            ux = (
                (np.dot(A_pt, A_pt)) * (B_pt[1] - C_pt[1])
                + (np.dot(B_pt, B_pt)) * (C_pt[1] - A_pt[1])
                + (np.dot(C_pt, C_pt)) * (A_pt[1] - B_pt[1])
            ) / d_det
            uy = (
                (np.dot(A_pt, A_pt)) * (C_pt[0] - B_pt[0])
                + (np.dot(B_pt, B_pt)) * (A_pt[0] - C_pt[0])
                + (np.dot(C_pt, C_pt)) * (B_pt[0] - A_pt[0])
            ) / d_det
            O_pt = np.array([ux, uy])
            H_pt = 3.0 * G_pt - 2.0 * O_pt

            if abs(a - b) < 1e-5 and abs(b - c) < 1e-5:
                tipo_lados = "Equilátero"
            elif abs(a - b) < 1e-5 or abs(b - c) < 1e-5 or abs(a - c) < 1e-5:
                tipo_lados = "Isósceles"
            else:
                tipo_lados = "Escaleno"

            max_ang = max(alpha, beta, gamma)
            if abs(max_ang - 90.0) < 1e-4:
                tipo_ang = "Rectángulo"
            elif max_ang > 90.0:
                tipo_ang = "Obtusángulo"
            else:
                tipo_ang = "Acutángulo"

            with col_out:
                with st.container(border=True):
                    header_tarjeta(f"Triángulo {tipo_lados} y {tipo_ang}")
                    fig, ax = _crear_fig_2d()
                    pol = Polygon([A_pt, B_pt, C_pt], closed=True, fc=AZUL, alpha=0.14, ec=AZUL, lw=2.4, zorder=3)
                    ax.add_patch(pol)

                    _anotar_pt(ax, A_pt[0], A_pt[1], "A", AZUL, -18, -22)
                    _anotar_pt(ax, B_pt[0], B_pt[1], "B", AZUL, 10, -22)
                    _anotar_pt(ax, C_pt[0], C_pt[1], "C", AZUL, 0, 12)

                    pts_encuadre = [A_pt, B_pt, C_pt, G_pt]

                    if ver_in:
                        circ_in = Circle(I_pt, r_in, fc="none", ec=VERDE, lw=1.8, ls="--", label=f"Inscrita (r={r_in:.2f})", zorder=4)
                        ax.add_patch(circ_in)
                        _anotar_pt(ax, I_pt[0], I_pt[1], "I", VERDE, 8, 8)
                        pts_encuadre.append(I_pt)

                    if ver_circ:
                        circ_out = Circle(O_pt, R_circ, fc="none", ec=NARANJA, lw=1.6, ls=":", label=f"Circunscrita (R={R_circ:.2f})", zorder=2)
                        ax.add_patch(circ_out)
                        _anotar_pt(ax, O_pt[0], O_pt[1], "O", NARANJA, -24, 10)
                        pts_encuadre.extend([O_pt + np.array([R_circ, R_circ]), O_pt - np.array([R_circ, R_circ])])

                    if ver_euler:
                        _anotar_pt(ax, G_pt[0], G_pt[1], "G", MORADO, 8, -18)
                        _anotar_pt(ax, H_pt[0], H_pt[1], "H", ROJO, 8, 10)
                        pts_encuadre.append(H_pt)
                        if np.linalg.norm(H_pt - O_pt) > 1e-6:
                            dir_e = H_pt - O_pt
                            p1_e = O_pt - 0.25 * dir_e
                            p2_e = H_pt + 0.25 * dir_e
                            ax.plot([p1_e[0], p2_e[0]], [p1_e[1], p2_e[1]], color=ROJO, lw=1.6, ls="-.", label="Recta de Euler (O-G-H)", zorder=5)

                    arr_pts = np.array(pts_encuadre)
                    xmin, ymin = arr_pts.min(axis=0)
                    xmax, ymax = arr_pts.max(axis=0)
                    margen = max(xmax - xmin, ymax - ymin, 2.0) * 0.22
                    ax.set_xlim(xmin - margen, xmax + margen)
                    ax.set_ylim(ymin - margen, ymax + margen)
                    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92)
                    mostrar_figura_segura(fig)

            # Resultados organizados limpiamente en pestañas
            with st.container(border=True):
                subheader_tarjeta("Resultados Analíticos del Triángulo")
                t_res, t_cev, t_not, t_cir = st.tabs([
                    "📋 Resumen y Vértices",
                    "📐 Lados, Ángulos y Cevianas",
                    "🎯 Puntos Notables y Recta de Euler",
                    "⭕ Circunferencias Inscrita y Circunscrita",
                ])

                with t_res:
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Área (A)", f"{area:.4f}")
                    m2.metric("Perímetro (2s)", f"{perimetro:.4f}")
                    m3.metric("Semiperímetro (s)", f"{s:.4f}")
                    m4.metric("Clasificación", f"{tipo_lados} · {tipo_ang}")
                    st.markdown(
                        f"| Vértice | Coordenada $x$ | Coordenada $y$ | Ángulo Interior |\n"
                        f"|---|---|---|---|\n"
                        f"| **Vértice $A$** | `{A_pt[0]:.4f}` | `{A_pt[1]:.4f}` | $\\alpha = {alpha:.2f}^\\circ$ ({math.radians(alpha):.4f} rad) |\n"
                        f"| **Vértice $B$** | `{B_pt[0]:.4f}` | `{B_pt[1]:.4f}` | $\\beta = {beta:.2f}^\\circ$ ({math.radians(beta):.4f} rad) |\n"
                        f"| **Vértice $C$** | `{C_pt[0]:.4f}` | `{C_pt[1]:.4f}` | $\\gamma = {gamma:.2f}^\\circ$ ({math.radians(gamma):.4f} rad) |"
                    )

                with t_cev:
                    st.markdown(
                        f"| Métrica | Lado $a$ ($BC$) | Lado $b$ ($AC$) | Lado $c$ ($AB$) |\n"
                        f"|---|---|---|---|\n"
                        f"| **Longitud del lado** | `{a:.4f}` | `{b:.4f}` | `{c:.4f}` |\n"
                        f"| **Ángulo opuesto** | `{alpha:.2f}°` | `{beta:.2f}°` | `{gamma:.2f}°` |\n"
                        f"| **Altura ($h = 2A/\\text{{lado}}$)** | `{ha:.4f}` | `{hb:.4f}` | `{hc:.4f}` |\n"
                        f"| **Mediana ($m$)** | `{ma:.4f}` | `{mb:.4f}` | `{mc:.4f}` |\n"
                        f"| **Bisectriz interna ($b$)** | `{ba:.4f}` | `{bb:.4f}` | `{bc:.4f}` |"
                    )

                with t_not:
                    d_OG = float(np.linalg.norm(G_pt - O_pt))
                    d_GH = float(np.linalg.norm(H_pt - G_pt))
                    d_OH = float(np.linalg.norm(H_pt - O_pt))
                    st.markdown(
                        f"| Punto Notable | Coordenadas $(x, y)$ | Definición Geométrica |\n"
                        f"|---|---|---|\n"
                        f"| **Baricentro ($G$)** | `({G_pt[0]:.4f}, {G_pt[1]:.4f})` | Intersección de las 3 medianas (centro de gravedad) |\n"
                        f"| **Incentro ($I$)** | `({I_pt[0]:.4f}, {I_pt[1]:.4f})` | Intersección de las 3 bisectrices internas |\n"
                        f"| **Circuncentro ($O$)** | `({O_pt[0]:.4f}, {O_pt[1]:.4f})` | Intersección de las 3 mediatrices |\n"
                        f"| **Ortocentro ($H$)** | `({H_pt[0]:.4f}, {H_pt[1]:.4f})` | Intersección de las 3 alturas |"
                    )
                    st.info(
                        f"**Relación en la Recta de Euler:** $d(O, G) = {d_OG:.4f}$, $d(G, H) = {d_GH:.4f}$ y $d(O, H) = {d_OH:.4f}$ "
                        "(se verifica exactamente $d(G, H) = 2\\,d(O, G)$)."
                    )

                with t_cir:
                    d_OI = float(np.linalg.norm(O_pt - I_pt))
                    c_cir1, c_cir2 = st.columns(2)
                    with c_cir1:
                        st.markdown("**Circunferencia Inscrita (Incentro $I$):**")
                        st.latex(f"(x - ({I_pt[0]:.3f}))^2 + (y - ({I_pt[1]:.3f}))^2 = {r_in**2:.4f}")
                        st.caption(f"Radio $r = A/s = {r_in:.4f}$ · Área = ${math.pi * r_in**2:.4f}$")
                    with c_cir2:
                        st.markdown("**Circunferencia Circunscrita (Circuncentro $O$):**")
                        st.latex(f"(x - ({O_pt[0]:.3f}))^2 + (y - ({O_pt[1]:.3f}))^2 = {R_circ**2:.4f}")
                        st.caption(f"Radio $R = abc/(4A) = {R_circ:.4f}$ · Área = ${math.pi * R_circ**2:.4f}$")
                    st.info(f"**Teorema de Euler para circunferencias:** $d(O, I) = \\sqrt{{R(R - 2r)}} = {d_OI:.4f}$.")

    elif modo_2d.startswith("Círculo"):
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.container(border=True):
                header_tarjeta("Parámetros Circulares")
                r_ext = st.number_input("Radio exterior (R):", min_value=0.1, value=5.0, step=0.5, key="cir_r")
                r_int = st.number_input(
                    "Radio interior (r, 0 = círculo lleno):",
                    min_value=0.0,
                    max_value=float(r_ext - 0.01) if r_ext > 0.05 else 0.0,
                    value=0.0,
                    step=0.5,
                    key="cir_rint",
                )
                theta_deg = st.slider("Ángulo del sector θ (grados):", min_value=1.0, max_value=360.0, value=90.0, step=1.0, key="cir_th")
                theta_rad = math.radians(theta_deg)

                area_total = math.pi * (r_ext**2 - r_int**2)
                perim_total = 2 * math.pi * r_ext
                area_sector = 0.5 * theta_rad * (r_ext**2 - r_int**2)
                long_arco = r_ext * theta_rad
                cuerda = 2 * r_ext * math.sin(theta_rad / 2.0)
                area_segmento = 0.5 * r_ext**2 * (theta_rad - math.sin(theta_rad))

                t_c1, t_c2 = st.tabs(["⭕ Círculo / Corona", "🍰 Sector y Segmento"])
                with t_c1:
                    st.metric("Área Total", f"{area_total:.4f}")
                    st.metric("Circunferencia Exterior (2πR)", f"{perim_total:.4f}")
                with t_c2:
                    st.markdown(
                        f"| Elemento ($\\theta = {theta_deg:.0f}^\\circ$) | Valor |\n"
                        f"|---|---|\n"
                        f"| **Área del sector** | `{area_sector:.4f}` |\n"
                        f"| **Longitud de arco ($R\\theta$)** | `{long_arco:.4f}` |\n"
                        f"| **Longitud de la cuerda** | `{cuerda:.4f}` |\n"
                        f"| **Área del segmento circular** | `{area_segmento:.4f}` |"
                    )
        with c2:
            with st.container(border=True):
                header_tarjeta("Representación Geométrica")
                fig, ax = _crear_fig_2d()
                ts = np.linspace(0, 2 * np.pi, 300)
                ax.plot(r_ext * np.cos(ts), r_ext * np.sin(ts), color=AZUL, lw=2.2, label=f"R = {r_ext:g}")
                if r_int > 0:
                    ax.plot(r_int * np.cos(ts), r_int * np.sin(ts), color=OSCURO, lw=1.6, ls="--", label=f"r = {r_int:g}")
                ts_sec = np.linspace(0, theta_rad, 120)
                x_poly = np.concatenate([r_ext * np.cos(ts_sec), r_int * np.cos(ts_sec[::-1])])
                y_poly = np.concatenate([r_ext * np.sin(ts_sec), r_int * np.sin(ts_sec[::-1])])
                ax.fill(x_poly, y_poly, color=NARANJA, alpha=0.28, label=f"Sector ({theta_deg:.0f}°)")
                ax.plot([r_ext, r_ext * math.cos(theta_rad)], [0, r_ext * math.sin(theta_rad)], color=VERDE, lw=1.8, ls=":", label=f"Cuerda = {cuerda:.2f}")
                lim = r_ext * 1.25
                ax.set_xlim(-lim, lim)
                ax.set_ylim(-lim, lim)
                ax.legend(loc="upper right", fontsize=8.5)
                mostrar_figura_segura(fig)

    elif modo_2d.startswith("Polígono"):
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.container(border=True):
                header_tarjeta("Polígono Regular de n Lados")
                n_lados = int(st.number_input("Número de lados (n):", min_value=3, max_value=30, value=6, step=1, key="pol_n"))
                longitud_l = st.number_input("Longitud del lado (L):", min_value=0.1, value=4.0, step=0.5, key="pol_l")

                ang_central = 360.0 / n_lados
                ang_interior = 180.0 * (n_lados - 2) / n_lados
                suma_ang = 180.0 * (n_lados - 2)
                apotema = longitud_l / (2.0 * math.tan(math.pi / n_lados))
                circunradio = longitud_l / (2.0 * math.sin(math.pi / n_lados))
                perim_pol = n_lados * longitud_l
                area_pol = 0.5 * perim_pol * apotema
                num_diagonales = n_lados * (n_lados - 3) // 2

                t_p1, t_p2 = st.tabs(["📏 Métricas y Radios", "📐 Ángulos y Diagonales"])
                with t_p1:
                    st.markdown(
                        f"| Propiedad | Valor |\n"
                        f"|---|---|\n"
                        f"| **Área ($P \\cdot a_p / 2$)** | `{area_pol:.4f}` |\n"
                        f"| **Perímetro ($nL$)** | `{perim_pol:.4f}` |\n"
                        f"| **Apotema ($a_p$)** | `{apotema:.4f}` |\n"
                        f"| **Circunradio ($R$)** | `{circunradio:.4f}` |"
                    )
                with t_p2:
                    st.markdown(
                        f"| Propiedad | Valor |\n"
                        f"|---|---|\n"
                        f"| **Ángulo interior** | `{ang_interior:.2f}°` |\n"
                        f"| **Ángulo central** | `{ang_central:.2f}°` |\n"
                        f"| **Suma de ángulos interiores** | `{suma_ang:.1f}°` |\n"
                        f"| **Total de diagonales** | `{num_diagonales}` |"
                    )
        with c2:
            with st.container(border=True):
                header_tarjeta(f"Polígono Regular (n = {n_lados})")
                fig, ax = _crear_fig_2d()
                angulos = np.linspace(0, 2 * np.pi, n_lados, endpoint=False) + np.pi / 2
                vx = circunradio * np.cos(angulos)
                vy = circunradio * np.sin(angulos)
                pol = Polygon(np.column_stack([vx, vy]), closed=True, fc=AZUL, alpha=0.18, ec=AZUL, lw=2.4)
                ax.add_patch(pol)
                ax.add_patch(Circle((0, 0), circunradio, fc="none", ec=NARANJA, ls=":", lw=1.4, label=f"Circunscrita (R={circunradio:.2f})"))
                ax.add_patch(Circle((0, 0), apotema, fc="none", ec=VERDE, ls="--", lw=1.4, label=f"Inscrita (ap={apotema:.2f})"))
                mx, my = (vx[0] + vx[1]) / 2, (vy[0] + vy[1]) / 2
                ax.plot([0, mx], [0, my], color=VERDE, lw=2.0)
                lim = circunradio * 1.25
                ax.set_xlim(-lim, lim)
                ax.set_ylim(-lim, lim)
                ax.legend(loc="upper right", fontsize=8.5)
                mostrar_figura_segura(fig)

    else:
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.container(border=True):
                header_tarjeta("Trapecio Simétrico")
                B_may = st.number_input("Base mayor (B):", min_value=0.1, value=8.0, step=0.5, key="trap_B")
                b_men = st.number_input("Base menor (b):", min_value=0.1, value=4.0, step=0.5, key="trap_b")
                h_trap = st.number_input("Altura (h):", min_value=0.1, value=3.5, step=0.5, key="trap_h")

                voladizo = (B_may - b_men) / 2.0
                lado_lat = math.hypot(voladizo, h_trap)
                perim_t = B_may + b_men + 2 * lado_lat
                area_t = 0.5 * (B_may + b_men) * h_trap
                mediana_t = 0.5 * (B_may + b_men)
                diag_t = math.hypot(B_may - voladizo, h_trap)

                st.markdown(
                    f"| Métrica | Valor |\n"
                    f"|---|---|\n"
                    f"| **Área ($\\frac{{B+b}}{{2}}h$)** | `{area_t:.4f}` |\n"
                    f"| **Perímetro** | `{perim_t:.4f}` |\n"
                    f"| **Lado oblicuo ($l$)** | `{lado_lat:.4f}` |\n"
                    f"| **Paralela media ($m$)** | `{mediana_t:.4f}` |\n"
                    f"| **Diagonal ($d$)** | `{diag_t:.4f}` |"
                )
        with c2:
            with st.container(border=True):
                header_tarjeta("Gráfica del Trapecio")
                fig, ax = _crear_fig_2d()
                pts_t = np.array([
                    [-B_may / 2, 0.0],
                    [B_may / 2, 0.0],
                    [b_men / 2, h_trap],
                    [-b_men / 2, h_trap],
                ])
                ax.add_patch(Polygon(pts_t, closed=True, fc=AZUL, alpha=0.18, ec=AZUL, lw=2.4))
                ax.plot([-mediana_t / 2, mediana_t / 2], [h_trap / 2, h_trap / 2], color=NARANJA, ls="--", lw=1.8, label=f"Paralela media = {mediana_t:.2f}")
                ax.plot([0, 0], [0, h_trap], color=ROJO, ls=":", lw=1.8, label=f"Altura h = {h_trap:.2f}")
                margen = max(B_may, h_trap) * 0.25 + 1.0
                ax.set_xlim(-B_may / 2 - margen, B_may / 2 + margen)
                ax.set_ylim(-1.0, h_trap + margen)
                ax.legend(loc="upper right", fontsize=8.5)
                mostrar_figura_segura(fig)


# ==============================================================================
# PESTAÑA 2: GEOMETRÍA ANALÍTICA PLANA (RECTAS Y CÓNICAS EN R^2)
# ==============================================================================
with tab_analitica_2d:
    sub_modo_a2 = st.radio(
        "Seleccione el tema de Geometría Analítica Plana:",
        [
            "📏 La Recta en ℝ² (Formas, Distancia Punto-Recta e Intersección)",
            "🎯 Secciones Cónicas Canónicas (Parábola, Elipse, Hipérbola)",
            "🔄 Ecuación General de 2.º Grado con Rotación de Ejes (Ax² + Bxy + Cy² + Dx + Ey + F = 0)",
        ],
        horizontal=True,
        key="geo_a2_modo",
    )

    st.divider()

    if sub_modo_a2.startswith("📏"):
        c_izq, c_der = st.columns([1.05, 1.25])
        with c_izq:
            with st.container(border=True):
                header_tarjeta("Recta Principal L₁ y Punto de Prueba P₀")
                st.caption("Forma general: $Ax + By + C = 0$")
                ca, cb, cc = st.columns(3)
                A1 = ca.number_input("A₁:", value=3.0, step=1.0, key="r1_A")
                B1 = cb.number_input("B₁:", value=-4.0, step=1.0, key="r1_B")
                C1 = cc.number_input("C₁:", value=-6.0, step=1.0, key="r1_C")

                subheader_tarjeta("Punto P₀(x₀, y₀) para distancia y proyección")
                cp1, cp2 = st.columns(2)
                x0_p = cp1.number_input("x₀:", value=2.0, step=0.5, key="r1_x0")
                y0_p = cp2.number_input("y₀:", value=4.0, step=0.5, key="r1_y0")

                comp_l2 = st.checkbox("Comparar con una segunda recta L₂ (A₂x + B₂y + C₂ = 0)", value=True, key="r2_chk")
                if comp_l2:
                    d1, d2, d3 = st.columns(3)
                    A2 = d1.number_input("A₂:", value=1.0, step=1.0, key="r2_A")
                    B2 = d2.number_input("B₂:", value=2.0, step=1.0, key="r2_B")
                    C2 = d3.number_input("C₂:", value=-4.0, step=1.0, key="r2_C")

        norm1 = math.hypot(A1, B1)
        if norm1 < 1e-12:
            st.error("⛔ Los coeficientes A₁ y B₁ no pueden ser ambos cero.")
        else:
            val_eval = A1 * x0_p + B1 * y0_p + C1
            dist_p0 = abs(val_eval) / norm1
            factor_proy = val_eval / (norm1**2)
            hx = x0_p - A1 * factor_proy
            hy = y0_p - B1 * factor_proy
            rx = 2 * hx - x0_p
            ry = 2 * hy - y0_p

            with c_der:
                with st.container(border=True):
                    header_tarjeta("Gráfica de L₁, Proyección Ortogonal y L₂")
                    fig, ax = _crear_fig_2d()
                    cx_graf = hx
                    cy_graf = hy
                    span = max(dist_p0 * 2.2, 6.0)
                    xs_l = np.linspace(cx_graf - span, cx_graf + span, 400)

                    if abs(B1) > 1e-9:
                        ys_l1 = (-A1 * xs_l - C1) / B1
                        ax.plot(xs_l, ys_l1, color=AZUL, lw=2.4, label=f"L₁: {A1:g}x + ({B1:g})y + ({C1:g}) = 0")
                    else:
                        x_fijo = -C1 / A1
                        ax.axvline(x_fijo, color=AZUL, lw=2.4, label=f"L₁: x = {x_fijo:.2f}")

                    ax.plot([x0_p, rx], [y0_p, ry], color=ROJO, ls="--", lw=1.6, label=f"d(P₀, L₁) = {dist_p0:.3f}")
                    _anotar_pt(ax, x0_p, y0_p, "P₀", ROJO, 10, 10)
                    _anotar_pt(ax, hx, hy, "Pie H", VERDE, 10, -20)
                    _anotar_pt(ax, rx, ry, "Reflejo P′", MORADO, 10, -18)

                    if comp_l2 and math.hypot(A2, B2) > 1e-12:
                        if abs(B2) > 1e-9:
                            ys_l2 = (-A2 * xs_l - C2) / B2
                            ax.plot(xs_l, ys_l2, color=NARANJA, lw=2.0, label=f"L₂: {A2:g}x + ({B2:g})y + ({C2:g}) = 0")
                        else:
                            ax.axvline(-C2 / A2, color=NARANJA, lw=2.0, label="L₂")
                        det_l = A1 * B2 - A2 * B1
                        if abs(det_l) > 1e-9:
                            ix = (B1 * C2 - B2 * C1) / det_l
                            iy = (C1 * A2 - C2 * A1) / det_l
                            _anotar_pt(ax, ix, iy, "Intersección", NARANJA, -30, 14)

                    ax.set_xlim(cx_graf - span, cx_graf + span)
                    ax.set_ylim(cy_graf - span, cy_graf + span)
                    ax.legend(loc="upper right", fontsize=8.0)
                    mostrar_figura_segura(fig)

            with st.container(border=True):
                subheader_tarjeta("Análisis de la Recta")
                t_r1, t_r2, t_r3 = st.tabs(["📏 Elementos de L₁", "📍 Distancia y Proyección de P₀", "🔀 Relación con L₂"])
                with t_r1:
                    pendiente_str = f"{-A1 / B1:.4f}" if abs(B1) > 1e-9 else "∞ (vertical)"
                    ang_inc = math.degrees(math.atan2(-A1, B1)) % 180.0
                    corte_x = f"({-C1 / A1:.4f}, 0)" if abs(A1) > 1e-9 else "No corta"
                    corte_y = f"(0, {-C1 / B1:.4f})" if abs(B1) > 1e-9 else "No corta"
                    st.markdown(
                        f"| Concepto | Valor |\n"
                        f"|---|---|\n"
                        f"| **Pendiente ($m$) y Ángulo ($\\alpha$)** | $m = {pendiente_str}$ · $\\alpha = {ang_inc:.2f}^\\circ$ |\n"
                        f"| **Vector normal $\\mathbf{{n}}$ y director $\\mathbf{{v}}$** | $\\mathbf{{n}} = ({A1:g}, {B1:g})$ · $\\mathbf{{v}} = ({-B1:g}, {A1:g})$ |\n"
                        f"| **Intersecciones con los ejes** | Eje X: `{corte_x}` · Eje Y: `{corte_y}` |"
                    )
                with t_r2:
                    m_d1, m_d2, m_d3 = st.columns(3)
                    m_d1.metric("Distancia d(P₀, L₁)", f"{dist_p0:.4f}")
                    m_d2.metric("Pie Perpendicular H", f"({hx:.3f}, {hy:.3f})")
                    m_d3.metric("Punto Simétrico P′", f"({rx:.3f}, {ry:.3f})")
                with t_r3:
                    if comp_l2 and math.hypot(A2, B2) > 1e-12:
                        det_l = A1 * B2 - A2 * B1
                        prod_n = A1 * A2 + B1 * B2
                        norm2 = math.hypot(A2, B2)
                        cos_th = min(1.0, abs(prod_n) / (norm1 * norm2))
                        ang_entre = math.degrees(math.acos(cos_th))
                        if abs(det_l) < 1e-9:
                            st.info("Las rectas $L_1$ y $L_2$ son **PARALELAS** ($\\theta = 0^\\circ$).")
                        else:
                            ix = (B1 * C2 - B2 * C1) / det_l
                            iy = (C1 * A2 - C2 * A1) / det_l
                            tipo_sec = "**PERPENDICULARES**" if abs(prod_n) < 1e-9 else "**SECANTES**"
                            st.success(f"Son {tipo_sec}. Se cortan en $I = ({ix:.4f}, {iy:.4f})$ con un ángulo agudo de **{ang_entre:.2f}°**.")
                    else:
                        st.info("Activa la casilla de segunda recta $L_2$ para comparar.")

    elif sub_modo_a2.startswith("🎯"):
        c_izq, c_der = st.columns([1.05, 1.25])
        with c_izq:
            with st.container(border=True):
                header_tarjeta("Parámetros de la Sección Cónica")
                tipo_con = st.selectbox("Seleccione la cónica:", ["Elipse", "Hipérbola", "Parábola"], key="con_tipo")
                orient = st.radio("Eje focal:", ["Horizontal (paralelo a X)", "Vertical (paralelo a Y)"], horizontal=True, key="con_ori")
                ch1, ch2 = st.columns(2)
                h_c = ch1.number_input("Centro / Vértice h (en X):", value=1.0, step=0.5, key="con_h")
                k_c = ch2.number_input("Centro / Vértice k (en Y):", value=-1.0, step=0.5, key="con_k")

                if tipo_con in ("Elipse", "Hipérbola"):
                    ca, cb = st.columns(2)
                    a_c = ca.number_input("Semieje principal (a):", min_value=0.2, value=4.0, step=0.5, key="con_a")
                    b_c = cb.number_input("Semieje secundario (b):", min_value=0.2, value=2.5, step=0.5, key="con_b")
                    if tipo_con == "Elipse" and b_c > a_c:
                        a_c, b_c = b_c, a_c
                        st.caption("ℹ️ Se ajustó $a \\ge b$ para el semieje mayor de la elipse.")
                else:
                    p_par = st.number_input("Parámetro focal p (distancia Vértice-Foco, ≠ 0):", value=2.0, step=0.5, key="con_p")
                    if abs(p_par) < 1e-6:
                        p_par = 1.0

        with c_der:
            with st.container(border=True):
                header_tarjeta(f"Gráfica de la {tipo_con}")
                fig, ax = _crear_fig_2d()
                es_horiz = orient.startswith("Horizontal")

                if tipo_con == "Elipse":
                    c_foc = math.sqrt(max(0.0, a_c**2 - b_c**2))
                    exc = c_foc / a_c
                    lr = 2 * (b_c**2) / a_c
                    t_p = np.linspace(0, 2 * np.pi, 400)
                    rx = a_c if es_horiz else b_c
                    ry = b_c if es_horiz else a_c
                    ax.plot(h_c + rx * np.cos(t_p), k_c + ry * np.sin(t_p), color=AZUL, lw=2.5, label="Elipse")
                    f1 = (h_c - c_foc, k_c) if es_horiz else (h_c, k_c - c_foc)
                    f2 = (h_c + c_foc, k_c) if es_horiz else (h_c, k_c + c_foc)
                    _anotar_pt(ax, h_c, k_c, "C", OSCURO, 6, 8)
                    _anotar_pt(ax, f1[0], f1[1], "F₁", ROJO, -20, -18)
                    _anotar_pt(ax, f2[0], f2[1], "F₂", ROJO, 8, -18)
                    m_v = max(rx, ry) * 1.4
                    ax.set_xlim(h_c - m_v, h_c + m_v)
                    ax.set_ylim(k_c - m_v, k_c + m_v)
                    eq_ltx = (
                        f"\\frac{{(x - ({h_c:g}))^2}}{{{rx**2:.3g}}} + \\frac{{(y - ({k_c:g}))^2}}{{{ry**2:.3g}}} = 1"
                    )
                    tabla_con = (
                        f"| Elemento | Valor |\n|---|---|\n"
                        f"| **Centro $C(h, k)$** | `({h_c:g}, {k_c:g})` |\n"
                        f"| **Focos $F_1, F_2$** | `({f1[0]:.3f}, {f1[1]:.3f})` y `({f2[0]:.3f}, {f2[1]:.3f})` |\n"
                        f"| **Distancia focal ($c$) y Excentricidad ($e$)** | $c = {c_foc:.4f}$ · $e = {exc:.4f}$ |\n"
                        f"| **Lado Recto ($2b^2/a$) y Área ($\\pi ab$)** | $LR = {lr:.4f}$ · $\\text{{Área}} = {math.pi * a_c * b_c:.4f}$ |"
                    )

                elif tipo_con == "Hipérbola":
                    c_foc = math.hypot(a_c, b_c)
                    exc = c_foc / a_c
                    lr = 2 * (b_c**2) / a_c
                    u_p = np.linspace(-2.0, 2.0, 300)
                    if es_horiz:
                        ax.plot(h_c + a_c * np.cosh(u_p), k_c + b_c * np.sinh(u_p), color=AZUL, lw=2.5, label="Hipérbola")
                        ax.plot(h_c - a_c * np.cosh(u_p), k_c + b_c * np.sinh(u_p), color=AZUL, lw=2.5)
                        xs_as = np.linspace(h_c - 3 * a_c, h_c + 3 * a_c, 100)
                        ax.plot(xs_as, k_c + (b_c / a_c) * (xs_as - h_c), color=ROJO, ls="--", lw=1.4, label="Asíntotas")
                        ax.plot(xs_as, k_c - (b_c / a_c) * (xs_as - h_c), color=ROJO, ls="--", lw=1.4)
                        f1, f2 = (h_c - c_foc, k_c), (h_c + c_foc, k_c)
                        eq_ltx = f"\\frac{{(x - ({h_c:g}))^2}}{{{a_c**2:.3g}}} - \\frac{{(y - ({k_c:g}))^2}}{{{b_c**2:.3g}}} = 1"
                    else:
                        ax.plot(h_c + b_c * np.sinh(u_p), k_c + a_c * np.cosh(u_p), color=AZUL, lw=2.5, label="Hipérbola")
                        ax.plot(h_c + b_c * np.sinh(u_p), k_c - a_c * np.cosh(u_p), color=AZUL, lw=2.5)
                        xs_as = np.linspace(h_c - 3 * b_c, h_c + 3 * b_c, 100)
                        ax.plot(xs_as, k_c + (a_c / b_c) * (xs_as - h_c), color=ROJO, ls="--", lw=1.4, label="Asíntotas")
                        ax.plot(xs_as, k_c - (a_c / b_c) * (xs_as - h_c), color=ROJO, ls="--", lw=1.4)
                        f1, f2 = (h_c, k_c - c_foc), (h_c, k_c + c_foc)
                        eq_ltx = f"\\frac{{(y - ({k_c:g}))^2}}{{{a_c**2:.3g}}} - \\frac{{(x - ({h_c:g}))^2}}{{{b_c**2:.3g}}} = 1"
                    _anotar_pt(ax, h_c, k_c, "C", OSCURO, 6, 8)
                    _anotar_pt(ax, f1[0], f1[1], "F₁", ROJO, -22, -16)
                    _anotar_pt(ax, f2[0], f2[1], "F₂", ROJO, 8, 8)
                    m_v = c_foc * 1.8
                    ax.set_xlim(h_c - m_v, h_c + m_v)
                    ax.set_ylim(k_c - m_v, k_c + m_v)
                    tabla_con = (
                        f"| Elemento | Valor |\n|---|---|\n"
                        f"| **Centro $C(h, k)$** | `({h_c:g}, {k_c:g})` |\n"
                        f"| **Focos $F_1, F_2$** | `({f1[0]:.3f}, {f1[1]:.3f})` y `({f2[0]:.3f}, {f2[1]:.3f})` |\n"
                        f"| **Distancia focal ($c$) y Excentricidad ($e$)** | $c = {c_foc:.4f}$ · $e = {exc:.4f}$ |\n"
                        f"| **Lado Recto ($2b^2/a$)** | $LR = {lr:.4f}$ |"
                    )

                else:
                    lr = abs(4.0 * p_par)
                    s_p = np.linspace(-2.5 * lr, 2.5 * lr, 300)
                    if es_horiz:
                        xs_p = h_c + (s_p**2) / (4.0 * p_par)
                        ys_p = k_c + s_p
                        foco = (h_c + p_par, k_c)
                        dir_val = h_c - p_par
                        ax.plot(xs_p, ys_p, color=AZUL, lw=2.5, label="Parábola")
                        ax.axvline(dir_val, color=VERDE, ls="--", lw=1.8, label=f"Directriz x = {dir_val:.2f}")
                        eq_ltx = f"(y - ({k_c:g}))^2 = {4*p_par:g}(x - ({h_c:g}))"
                    else:
                        xs_p = h_c + s_p
                        ys_p = k_c + (s_p**2) / (4.0 * p_par)
                        foco = (h_c, k_c + p_par)
                        dir_val = k_c - p_par
                        ax.plot(xs_p, ys_p, color=AZUL, lw=2.5, label="Parábola")
                        ax.axhline(dir_val, color=VERDE, ls="--", lw=1.8, label=f"Directriz y = {dir_val:.2f}")
                        eq_ltx = f"(x - ({h_c:g}))^2 = {4*p_par:g}(y - ({k_c:g}))"
                    _anotar_pt(ax, h_c, k_c, "V", OSCURO, 8, -18)
                    _anotar_pt(ax, foco[0], foco[1], "Foco", ROJO, 8, 10)
                    m_v = max(abs(p_par) * 4.5, 5.0)
                    ax.set_xlim(h_c - m_v, h_c + m_v)
                    ax.set_ylim(k_c - m_v, k_c + m_v)
                    tabla_con = (
                        f"| Elemento | Valor |\n|---|---|\n"
                        f"| **Vértice $V(h, k)$** | `({h_c:g}, {k_c:g})` |\n"
                        f"| **Foco $F$** | `({foco[0]:.3f}, {foco[1]:.3f})` |\n"
                        f"| **Recta Directriz** | `{'x' if es_horiz else 'y'} = {dir_val:.4f}` |\n"
                        f"| **Lado Recto ($\vert{}4p\vert{}$)** | `{lr:.4f}` |"
                    )

                ax.legend(loc="upper right", fontsize=8.5)
                mostrar_figura_segura(fig)

        with c_izq:
            with st.container(border=True):
                subheader_tarjeta("Ecuación Canónica y Elementos")
                st.latex(eq_ltx)
                st.markdown(tabla_con)

    else:
        c_izq, c_der = st.columns([1.05, 1.25])
        with c_izq:
            with st.container(border=True):
                header_tarjeta("Coeficientes de Ax² + Bxy + Cy² + Dx + Ey + F = 0")
                c1, c2, c3 = st.columns(3)
                Ag = c1.number_input("A (x²):", value=5.0, step=1.0, key="cg_A")
                Bg = c2.number_input("B (xy):", value=4.0, step=1.0, key="cg_B")
                Cg = c3.number_input("C (y²):", value=2.0, step=1.0, key="cg_C")
                c4, c5, c6 = st.columns(3)
                Dg = c4.number_input("D (x):", value=0.0, step=1.0, key="cg_D")
                Eg = c5.number_input("E (y):", value=0.0, step=1.0, key="cg_E")
                Fg = c6.number_input("F (indep.):", value=-6.0, step=1.0, key="cg_F")

                inv_I = Ag + Cg
                disc_2 = Bg**2 - 4 * Ag * Cg
                mat_3 = np.array([
                    [Ag, Bg / 2.0, Dg / 2.0],
                    [Bg / 2.0, Cg, Eg / 2.0],
                    [Dg / 2.0, Eg / 2.0, Fg],
                ])
                det_3 = float(np.linalg.det(mat_3))

                if abs(Bg) < 1e-12:
                    theta_rot = 0.0
                else:
                    theta_rot = 0.5 * math.atan2(Bg, Ag - Cg)
                theta_deg = math.degrees(theta_rot)
                c_t, s_t = math.cos(theta_rot), math.sin(theta_rot)
                Ap = Ag * c_t**2 + Bg * c_t * s_t + Cg * s_t**2
                Cp = Ag * s_t**2 - Bg * c_t * s_t + Cg * c_t**2
                Dp = Dg * c_t + Eg * s_t
                Ep = -Dg * s_t + Eg * c_t

                if disc_2 < -1e-9:
                    genero = "Elíptico"
                elif disc_2 > 1e-9:
                    genero = "Hiperbólico"
                else:
                    genero = "Parabólico"

                t_g1, t_g2 = st.tabs(["🔍 Invariantes Ortogonales", "🔄 Ecuación Rotada (x′, y′)"])
                with t_g1:
                    st.markdown(
                        f"| Invariante | Valor |\n"
                        f"|---|---|\n"
                        f"| **Traza ($I = A + C$)** | `{inv_I:.4f}` |\n"
                        f"| **Discriminante ($\\Delta_2 = B^2 - 4AC$)** | `{disc_2:.4f}` (Género **{genero}**) |\n"
                        f"| **Determinante cúbico ($\\Delta_3$)** | `{det_3:.4f}` ({'No degenerada' if abs(det_3) > 1e-7 else 'Degenerada'}) |"
                    )
                with t_g2:
                    st.metric("Ángulo de rotación θ", f"{theta_deg:.2f}°")
                    st.latex(f"{Ap:.3f}(x')^2 + ({Cp:.3f})(y')^2 + ({Dp:.3f})x' + ({Ep:.3f})y' + ({Fg:g}) = 0")

        with c_der:
            with st.container(border=True):
                header_tarjeta("Curva y Ejes Rotados (x′, y′)")
                fig, ax = _crear_fig_2d()
                xs_m = np.linspace(-6.0, 6.0, 300)
                X, Y = np.meshgrid(xs_m, xs_m)
                Z = Ag * X**2 + Bg * X * Y + Cg * Y**2 + Dg * X + Eg * Y + Fg
                if np.nanmin(Z) <= 0 <= np.nanmax(Z):
                    ax.contour(X, Y, Z, levels=[0], colors=[AZUL], linewidths=2.5)
                    ax.plot([], [], color=AZUL, lw=2.5, label="Lugar geométrico")
                else:
                    ax.text(0, 0, "Lugar geométrico vacío en [-6, 6]²", ha="center", color=ROJO)

                L_eje = 5.5
                ax.plot([-L_eje * c_t, L_eje * c_t], [-L_eje * s_t, L_eje * s_t], color=ROJO, ls="--", lw=1.4, label=f"Eje x′ (θ = {theta_deg:.1f}°)")
                ax.plot([L_eje * s_t, -L_eje * s_t], [-L_eje * c_t, L_eje * c_t], color=VERDE, ls=":", lw=1.4, label="Eje y′")
                ax.set_xlim(-6, 6)
                ax.set_ylim(-6, 6)
                ax.legend(loc="upper right", fontsize=8.5)
                mostrar_figura_segura(fig)


# ==============================================================================
# PESTAÑA 3: SÓLIDOS, PLANOS, RECTAS ALABEADAS Y CUÁDRICAS INTERACTIVAS EN R^3
# ==============================================================================
with tab_3d:
    modo_3d = st.radio(
        "Seleccione la herramienta de Geometría en el Espacio (ℝ³):",
        [
            "🏔️ 1. Superficies Cuádricas Interactivas (Parámetros y Cortes z = k)",
            "🧊 2. Sólidos Geométricos (Esfera, Cilindro, Cono, Toroide, Ortoedro)",
            "🛩️ 3. Planos y Distancia entre Rectas en ℝ³ (Secantes, Paralelas, Alabeadas)",
            "🌐 4. Conversor de Coordenadas 3D (Cartesianas ↔ Cilíndricas ↔ Esféricas)",
        ],
        horizontal=True,
        key="geo_3d_modo",
    )

    st.divider()

    if modo_3d.startswith("🏔️"):
        col_c_in, col_c_out = st.columns([1.05, 1.3])
        with col_c_in:
            with st.container(border=True):
                header_tarjeta("Configuración de la Superficie Cuádrica")
                cuadrica = st.selectbox(
                    "Tipo de superficie cuádrica:",
                    [
                        "1. Elipsoide",
                        "2. Paraboloide Elíptico",
                        "3. Paraboloide Hiperbólico (Silla de montar)",
                        "4. Hiperboloide de Una Hoja",
                        "5. Hiperboloide de Dos Hojas",
                        "6. Cono Elíptico",
                    ],
                    key="cuad_tipo_sel",
                )

                subheader_tarjeta("Semiejes / Parámetros de Escala (a, b, c)")
                s1, s2, s3 = st.columns(3)
                a_q = s1.number_input("Semieje a (en X):", min_value=0.2, max_value=15.0, value=2.0, step=0.5, key="q_a")
                b_q = s2.number_input("Semieje b (en Y):", min_value=0.2, max_value=15.0, value=1.5, step=0.5, key="q_b")
                c_q = s3.number_input("Parámetro c (en Z):", min_value=0.2, max_value=15.0, value=1.5, step=0.5, key="q_c")

                subheader_tarjeta("Centro / Vértice (x₀, y₀, z₀)")
                o1, o2, o3 = st.columns(3)
                x0_q = o1.number_input("x₀:", value=0.0, step=0.5, key="q_x0")
                y0_q = o2.number_input("y₀:", value=0.0, step=0.5, key="q_y0")
                z0_q = o3.number_input("z₀:", value=0.0, step=0.5, key="q_z0")

                subheader_tarjeta("Plano de corte horizontal (Traza z = k)")
                mostrar_corte = st.checkbox("Mostrar plano de corte z = k en 3D y traza 2D", value=True, key="q_chk_corte")
                k_corte = st.slider("Altura del corte k (en Z):", min_value=float(z0_q - 3 * c_q), max_value=float(z0_q + 3 * c_q), value=float(z0_q + 0.8 * c_q), step=0.2, key="q_k_val")

        with col_c_out:
            with st.container(border=True):
                tab_v3d, tab_v2d, tab_prop = st.tabs([
                    "🧊 Superficie 3D",
                    "🔪 Traza en el Plano z = k (2D)",
                    "📐 Ecuación y Propiedades",
                ])

                with tab_v3d:
                    fig3, ax3 = _crear_fig_3d(titulo=cuadrica.split(".")[1].strip())
                    u_ang = np.linspace(0, 2 * np.pi, 48)
                    r_max = max(a_q, b_q, c_q) * 2.2

                    if cuadrica.startswith("1."):
                        v_ang = np.linspace(0, np.pi, 32)
                        U, V = np.meshgrid(u_ang, v_ang)
                        X_s = x0_q + a_q * np.cos(U) * np.sin(V)
                        Y_s = y0_q + b_q * np.sin(U) * np.sin(V)
                        Z_s = z0_q + c_q * np.cos(V)
                        ax3.plot_surface(X_s, Y_s, Z_s, cmap="viridis", alpha=0.82)
                        eq_cuad = f"\\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} + \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}} + \\frac{{(z - ({z0_q:g}))^2}}{{{c_q**2:.3g}}} = 1"
                    elif cuadrica.startswith("2."):
                        r_m = np.linspace(0, 1.8, 30)
                        U, R = np.meshgrid(u_ang, r_m)
                        X_s = x0_q + a_q * R * np.cos(U)
                        Y_s = y0_q + b_q * R * np.sin(U)
                        Z_s = z0_q + c_q * (R**2)
                        ax3.plot_surface(X_s, Y_s, Z_s, cmap="viridis", alpha=0.82)
                        eq_cuad = f"\\frac{{z - ({z0_q:g})}}{{{c_q:g}}} = \\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} + \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}}"
                    elif cuadrica.startswith("3."):
                        s_m = np.linspace(-2.0, 2.0, 42)
                        U_m, V_m = np.meshgrid(s_m, s_m)
                        X_s = x0_q + a_q * U_m
                        Y_s = y0_q + b_q * V_m
                        Z_s = z0_q + c_q * (U_m**2 - V_m**2)
                        ax3.plot_surface(X_s, Y_s, Z_s, cmap="coolwarm", alpha=0.85)
                        eq_cuad = f"\\frac{{z - ({z0_q:g})}}{{{c_q:g}}} = \\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} - \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}}"
                    elif cuadrica.startswith("4."):
                        w_m = np.linspace(-1.4, 1.4, 34)
                        U, W = np.meshgrid(u_ang, w_m)
                        X_s = x0_q + a_q * np.cosh(W) * np.cos(U)
                        Y_s = y0_q + b_q * np.cosh(W) * np.sin(U)
                        Z_s = z0_q + c_q * np.sinh(W)
                        ax3.plot_surface(X_s, Y_s, Z_s, cmap="plasma", alpha=0.82)
                        eq_cuad = f"\\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} + \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}} - \\frac{{(z - ({z0_q:g}))^2}}{{{c_q**2:.3g}}} = 1"
                    elif cuadrica.startswith("5."):
                        w_m = np.linspace(0, 1.35, 26)
                        U, W = np.meshgrid(u_ang, w_m)
                        X_s = x0_q + a_q * np.sinh(W) * np.cos(U)
                        Y_s = y0_q + b_q * np.sinh(W) * np.sin(U)
                        Z_sup = z0_q + c_q * np.cosh(W)
                        Z_inf = z0_q - c_q * np.cosh(W)
                        ax3.plot_surface(X_s, Y_s, Z_sup, cmap="magma", alpha=0.82)
                        ax3.plot_surface(X_s, Y_s, Z_inf, cmap="magma", alpha=0.82)
                        eq_cuad = f"\\frac{{(z - ({z0_q:g}))^2}}{{{c_q**2:.3g}}} - \\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} - \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}} = 1"
                    else:
                        w_m = np.linspace(-1.8, 1.8, 34)
                        U, W = np.meshgrid(u_ang, w_m)
                        X_s = x0_q + a_q * np.abs(W) * np.cos(U)
                        Y_s = y0_q + b_q * np.abs(W) * np.sin(U)
                        Z_s = z0_q + c_q * W
                        ax3.plot_surface(X_s, Y_s, Z_s, cmap="viridis", alpha=0.82)
                        eq_cuad = f"\\frac{{(z - ({z0_q:g}))^2}}{{{c_q**2:.3g}}} = \\frac{{(x - ({x0_q:g}))^2}}{{{a_q**2:.3g}}} + \\frac{{(y - ({y0_q:g}))^2}}{{{b_q**2:.3g}}}"

                    if mostrar_corte:
                        xp_m, yp_m = np.meshgrid(
                            [x0_q - r_max, x0_q + r_max],
                            [y0_q - r_max, y0_q + r_max],
                        )
                        ax3.plot_surface(xp_m, yp_m, np.full_like(xp_m, k_corte), color=ROJO, alpha=0.25)

                    mostrar_figura_segura(fig3)

                with tab_v2d:
                    fig2, ax2 = _crear_fig_2d()
                    span2 = max(a_q, b_q) * 2.5
                    xm2 = np.linspace(x0_q - span2, x0_q + span2, 300)
                    ym2 = np.linspace(y0_q - span2, y0_q + span2, 300)
                    X2, Y2 = np.meshgrid(xm2, ym2)
                    u_x = (X2 - x0_q) / a_q
                    u_y = (Y2 - y0_q) / b_q
                    u_z = (k_corte - z0_q) / c_q

                    if cuadrica.startswith("1."):
                        F_corte = u_x**2 + u_y**2 - (1.0 - u_z**2)
                    elif cuadrica.startswith("2."):
                        F_corte = u_x**2 + u_y**2 - u_z
                    elif cuadrica.startswith("3."):
                        F_corte = u_x**2 - u_y**2 - u_z
                    elif cuadrica.startswith("4."):
                        F_corte = u_x**2 + u_y**2 - (1.0 + u_z**2)
                    elif cuadrica.startswith("5."):
                        F_corte = u_x**2 + u_y**2 - (u_z**2 - 1.0)
                    else:
                        F_corte = u_x**2 + u_y**2 - u_z**2

                    if np.nanmin(F_corte) <= 0 <= np.nanmax(F_corte):
                        ax2.contour(X2, Y2, F_corte, levels=[0], colors=[ROJO], linewidths=2.5)
                        ax2.plot([], [], color=ROJO, lw=2.5, label=f"Traza en z = {k_corte:.2f}")
                    else:
                        ax2.text(x0_q, y0_q, f"El plano z = {k_corte:.2f} no corta a la superficie\n(intersección vacía en los reales)", ha="center", color=ROJO)

                    _anotar_pt(ax2, x0_q, y0_q, "Centro", OSCURO, 8, 8)
                    ax2.set_xlim(x0_q - span2, x0_q + span2)
                    ax2.set_ylim(y0_q - span2, y0_q + span2)
                    ax2.legend(loc="upper right", fontsize=8.5)
                    mostrar_figura_segura(fig2)

                with tab_prop:
                    st.markdown("**Ecuación Canónica con tus parámetros:**")
                    st.latex(eq_cuad)
                    if cuadrica.startswith("1."):
                        vol_elip = (4.0 / 3.0) * math.pi * a_q * b_q * c_q
                        p_th = 1.6075
                        area_elip = 4.0 * math.pi * (((a_q**p_th * b_q**p_th + a_q**p_th * c_q**p_th + b_q**p_th * c_q**p_th) / 3.0) ** (1.0 / p_th))
                        st.markdown(
                            f"| Propiedad del Elipsoide | Valor |\n|---|---|\n"
                            f"| **Volumen exacto ($\\frac{{4}}{{3}}\\pi abc$)** | `{vol_elip:.4f}` |\n"
                            f"| **Área superficial (Knud Thomsen)** | `{area_elip:.4f}` |\n"
                            f"| **Trazas coordenadas** | Elipses en los 3 planos coordenados |"
                        )
                    else:
                        st.markdown(
                            f"| Plano de Corte | Tipo de Curva (Traza) |\n|---|---|\n"
                            f"| **Paralelo a XY ($z = k$)** | {'Elipse' if not cuadrica.startswith('3.') else 'Hipérbola (o 2 rectas si k = z₀)'} |\n"
                            f"| **Paralelo a XZ ($y = y_0$)** | {'Parábola' if 'Paraboloide' in cuadrica else 'Hipérbola / Rectas'} |\n"
                            f"| **Paralelo a YZ ($x = x_0$)** | {'Parábola' if 'Paraboloide' in cuadrica else 'Hipérbola / Rectas'} |"
                        )

    elif modo_3d.startswith("🧊"):
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.container(border=True):
                header_tarjeta("Selección de Sólido 3D")
                solido = st.selectbox(
                    "Cuerpo geométrico:",
                    ["Cilindro Circular Recto", "Cono Circular Recto", "Esfera", "Toroide (Dona)", "Ortoedro (Caja Rectangular)"],
                    key="sol_tipo",
                )

                if solido in ("Cilindro Circular Recto", "Cono Circular Recto"):
                    r_s = st.number_input("Radio de la base (r):", min_value=0.2, value=3.0, step=0.5, key="sol_r")
                    h_s = st.number_input("Altura (h):", min_value=0.2, value=5.0, step=0.5, key="sol_h")
                    if solido.startswith("Cilindro"):
                        a_base = math.pi * r_s**2
                        a_lat = 2 * math.pi * r_s * h_s
                        a_tot = 2 * a_base + a_lat
                        vol = a_base * h_s
                        st.markdown(
                            f"| Métrica | Fórmula | Valor |\n|---|---|---|\n"
                            f"| **Área de una base** | $\\pi r^2$ | `{a_base:.4f}` |\n"
                            f"| **Área lateral** | $2\\pi r h$ | `{a_lat:.4f}` |\n"
                            f"| **Área total (con 2 tapas)** | $2\\pi r(r + h)$ | `{a_tot:.4f}` |\n"
                            f"| **Volumen** | $\\pi r^2 h$ | `{vol:.4f}` |"
                        )
                    else:
                        gen = math.hypot(r_s, h_s)
                        a_base = math.pi * r_s**2
                        a_lat = math.pi * r_s * gen
                        a_tot = a_base + a_lat
                        vol = (a_base * h_s) / 3.0
                        st.markdown(
                            f"| Métrica | Fórmula | Valor |\n|---|---|---|\n"
                            f"| **Generatriz ($g$)** | $\\sqrt{{r^2+h^2}}$ | `{gen:.4f}` |\n"
                            f"| **Área lateral** | $\\pi r g$ | `{a_lat:.4f}` |\n"
                            f"| **Área total** | $\\pi r(r + g)$ | `{a_tot:.4f}` |\n"
                            f"| **Volumen** | $\\frac{{1}}{{3}}\\pi r^2 h$ | `{vol:.4f}` |"
                        )
                elif solido == "Esfera":
                    r_s = st.number_input("Radio (r):", min_value=0.2, value=3.5, step=0.5, key="esf_r")
                    a_tot = 4 * math.pi * r_s**2
                    vol = (4.0 / 3.0) * math.pi * r_s**3
                    st.metric("Área Superficial (4πr²)", f"{a_tot:.4f}")
                    st.metric("Volumen (4/3 πr³)", f"{vol:.4f}")
                elif solido.startswith("Toroide"):
                    R_may = st.number_input("Radio mayor (R):", min_value=1.0, value=4.0, step=0.5, key="tor_R")
                    r_men = st.number_input("Radio del tubo (r < R):", min_value=0.2, max_value=float(R_may - 0.1), value=1.2, step=0.2, key="tor_r")
                    a_tot = 4 * (math.pi**2) * R_may * r_men
                    vol = 2 * (math.pi**2) * R_may * (r_men**2)
                    st.metric("Área Superficial (4π²Rr)", f"{a_tot:.4f}")
                    st.metric("Volumen (2π²Rr²)", f"{vol:.4f}")
                else:
                    lx_o = st.number_input("Largo (a):", min_value=0.2, value=4.0, step=0.5, key="ort_a")
                    ly_o = st.number_input("Ancho (b):", min_value=0.2, value=3.0, step=0.5, key="ort_b")
                    lz_o = st.number_input("Alto (c):", min_value=0.2, value=2.5, step=0.5, key="ort_c")
                    a_tot = 2 * (lx_o * ly_o + lx_o * lz_o + ly_o * lz_o)
                    vol = lx_o * ly_o * lz_o
                    diag_esp = math.sqrt(lx_o**2 + ly_o**2 + lz_o**2)
                    st.metric("Área Total (6 caras)", f"{a_tot:.4f}")
                    st.metric("Volumen (abc)", f"{vol:.4f}")
                    st.metric("Diagonal Espacial", f"{diag_esp:.4f}")

        with c2:
            with st.container(border=True):
                header_tarjeta(f"Visualización 3D: {solido}")
                fig, ax = _crear_fig_3d(titulo=solido)
                u = np.linspace(0, 2 * np.pi, 45)
                if solido.startswith("Cilindro"):
                    z_v = np.linspace(0, h_s, 25)
                    U, Z = np.meshgrid(u, z_v)
                    ax.plot_surface(r_s * np.cos(U), r_s * np.sin(U), Z, color=AZUL, alpha=0.65)
                    rad_m, ang_m = np.meshgrid(np.linspace(0, r_s, 12), u)
                    X_t = rad_m * np.cos(ang_m)
                    Y_t = rad_m * np.sin(ang_m)
                    ax.plot_surface(X_t, Y_t, np.zeros_like(X_t), color=NARANJA, alpha=0.75)
                    ax.plot_surface(X_t, Y_t, np.full_like(X_t, h_s), color=NARANJA, alpha=0.75)
                    m_lim = max(r_s, h_s / 2) * 1.2
                    ax.set_xlim(-m_lim, m_lim)
                    ax.set_ylim(-m_lim, m_lim)
                    ax.set_zlim(0, h_s * 1.15)
                elif solido.startswith("Cono"):
                    v_c = np.linspace(0, 1, 25)
                    U, V = np.meshgrid(u, v_c)
                    ax.plot_surface(r_s * (1 - V) * np.cos(U), r_s * (1 - V) * np.sin(U), h_s * V, color=AZUL, alpha=0.68)
                    rad_m, ang_m = np.meshgrid(np.linspace(0, r_s, 12), u)
                    ax.plot_surface(rad_m * np.cos(ang_m), rad_m * np.sin(ang_m), np.zeros_like(rad_m), color=NARANJA, alpha=0.75)
                    m_lim = max(r_s, h_s / 2) * 1.2
                    ax.set_xlim(-m_lim, m_lim)
                    ax.set_ylim(-m_lim, m_lim)
                    ax.set_zlim(0, h_s * 1.15)
                elif solido == "Esfera":
                    v_e = np.linspace(0, np.pi, 30)
                    U, V = np.meshgrid(u, v_e)
                    ax.plot_surface(r_s * np.cos(U) * np.sin(V), r_s * np.sin(U) * np.sin(V), r_s * np.cos(V), color=AZUL, alpha=0.7)
                    ax.set_box_aspect((1, 1, 1))
                elif solido.startswith("Toroide"):
                    U, V = np.meshgrid(u, u)
                    X = (R_may + r_men * np.cos(V)) * np.cos(U)
                    Y = (R_may + r_men * np.cos(V)) * np.sin(U)
                    Z = r_men * np.sin(V)
                    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)
                    lim_t = R_may + r_men
                    ax.set_xlim(-lim_t, lim_t)
                    ax.set_ylim(-lim_t, lim_t)
                    ax.set_zlim(-lim_t, lim_t)
                else:
                    X_c, Y_c = np.meshgrid([0, lx_o], [0, ly_o])
                    ax.plot_surface(X_c, Y_c, np.zeros_like(X_c), color=AZUL, alpha=0.55)
                    ax.plot_surface(X_c, Y_c, np.full_like(X_c, lz_o), color=AZUL, alpha=0.55)
                    X_c2, Z_c2 = np.meshgrid([0, lx_o], [0, lz_o])
                    ax.plot_surface(X_c2, np.zeros_like(X_c2), Z_c2, color=NARANJA, alpha=0.55)
                    ax.plot_surface(X_c2, np.full_like(X_c2, ly_o), Z_c2, color=NARANJA, alpha=0.55)
                    Y_c3, Z_c3 = np.meshgrid([0, ly_o], [0, lz_o])
                    ax.plot_surface(np.zeros_like(Y_c3), Y_c3, Z_c3, color=VERDE, alpha=0.55)
                    ax.plot_surface(np.full_like(Y_c3, lx_o), Y_c3, Z_c3, color=VERDE, alpha=0.55)
                mostrar_figura_segura(fig)

    elif modo_3d.startswith("🛩️"):
        c_izq, c_der = st.columns([1.05, 1.25])
        with c_izq:
            with st.container(border=True):
                header_tarjeta("Posición Relativa y Distancia entre 2 Rectas en ℝ³")
                st.caption("Recta $L_1: \\mathbf{p}_1 + t\\,\\mathbf{v}_1$ y Recta $L_2: \\mathbf{p}_2 + s\\,\\mathbf{v}_2$")
                p1_str = st.text_input("Punto P₁ de L₁ (x, y, z):", value="1, 0, -1", key="l3_p1")
                v1_str = st.text_input("Vector director v₁ de L₁:", value="2, 1, 1", key="l3_v1")
                p2_str = st.text_input("Punto P₂ de L₂ (x, y, z):", value="0, 2, 1", key="l3_p2")
                v2_str = st.text_input("Vector director v₂ de L₂:", value="1, -1, 2", key="l3_v2")

        try:
            P1 = np.array([float(x.strip()) for x in p1_str.split(",")], dtype=float)
            V1 = np.array([float(x.strip()) for x in v1_str.split(",")], dtype=float)
            P2 = np.array([float(x.strip()) for x in p2_str.split(",")], dtype=float)
            V2 = np.array([float(x.strip()) for x in v2_str.split(",")], dtype=float)
            if len(P1) != 3 or len(V1) != 3 or len(P2) != 3 or len(V2) != 3:
                raise ValueError("Cada punto y vector debe tener exactamente 3 coordenadas.")
            if np.linalg.norm(V1) < 1e-12 or np.linalg.norm(V2) < 1e-12:
                raise ValueError("Los vectores directores no pueden ser el vector cero.")

            cruz_v = np.cross(V1, V2)
            norm_cruz = float(np.linalg.norm(cruz_v))
            dif_p = P2 - P1
            cos_ang = np.clip(abs(np.dot(V1, V2)) / (np.linalg.norm(V1) * np.linalg.norm(V2)), 0.0, 1.0)
            ang_rectas = math.degrees(math.acos(cos_ang))

            if norm_cruz < 1e-9:
                dist_min = float(np.linalg.norm(np.cross(dif_p, V1)) / np.linalg.norm(V1))
                pos_rel = "COINCIDENTES" if dist_min < 1e-9 else "PARALELAS"
                Q1, Q2 = P1, P2 - (np.dot(dif_p, V1) / np.dot(V1, V1)) * V1
            else:
                prod_mixto = float(np.dot(dif_p, cruz_v))
                dist_min = abs(prod_mixto) / norm_cruz
                pos_rel = "SECANTES (se cortan)" if dist_min < 1e-8 else "ALABEADAS (se cruzan sin cortarse)"
                n1 = np.cross(V1, cruz_v)
                n2 = np.cross(V2, cruz_v)
                t_opt = np.dot(dif_p, n2) / np.dot(V1, n2)
                s_opt = np.dot(-dif_p, n1) / np.dot(V2, n1)
                Q1 = P1 + t_opt * V1
                Q2 = P2 + s_opt * V2

            with c_izq:
                with st.container(border=True):
                    subheader_tarjeta("Diagnóstico Espacial")
                    st.success(f"**Posición relativa:** {pos_rel}")
                    st.markdown(
                        f"| Métrica | Valor |\n|---|---|\n"
                        f"| **Distancia mínima $d(L_1, L_2)$** | `{dist_min:.4f}` |\n"
                        f"| **Ángulo entre directores** | `{ang_rectas:.2f}°` |\n"
                        f"| **Punto más cercano en $L_1$ ($Q_1$)** | `({Q1[0]:.3f}, {Q1[1]:.3f}, {Q1[2]:.3f})` |\n"
                        f"| **Punto más cercano en $L_2$ ($Q_2$)** | `({Q2[0]:.3f}, {Q2[1]:.3f}, {Q2[2]:.3f})` |"
                    )

            with c_der:
                with st.container(border=True):
                    header_tarjeta("Gráfica 3D de L₁, L₂ y Perpendicular Común")
                    fig, ax = _crear_fig_3d(titulo=f"Rectas {pos_rel.split()[0]}")
                    ts = np.linspace(-3.5, 3.5, 100)
                    l1_pts = Q1[:, None] + V1[:, None] * ts
                    l2_pts = Q2[:, None] + V2[:, None] * ts
                    ax.plot(l1_pts[0], l1_pts[1], l1_pts[2], color=AZUL, lw=2.5, label="Recta L₁")
                    ax.plot(l2_pts[0], l2_pts[1], l2_pts[2], color=NARANJA, lw=2.5, label="Recta L₂")
                    ax.plot([Q1[0], Q2[0]], [Q1[1], Q2[1]], [Q1[2], Q2[2]], color=ROJO, ls="--", lw=2.2, label=f"d mín = {dist_min:.3f}")
                    ax.scatter([Q1[0], Q2[0]], [Q1[1], Q2[1]], [Q1[2], Q2[2]], color=ROJO, s=50)
                    ax.legend(loc="upper left", fontsize=8.5)
                    mostrar_figura_segura(fig)
        except Exception as err_l3:
            st.error(f"Error en los datos: {err_l3}")

    else:
        c_conv1, c_conv2 = st.columns([1.05, 1.25])
        with c_conv1:
            with st.container(border=True):
                header_tarjeta("Conversor de Coordenadas en ℝ³")
                sis_origen = st.selectbox(
                    "Sistema de entrada:",
                    ["Cartesianas (x, y, z)", "Cilíndricas (ρ, θ°, z)", "Esféricas (r, θ°, φ°)"],
                    key="conv_sis",
                )
                k1, k2, k3 = st.columns(3)
                if sis_origen.startswith("Cart"):
                    x_c = k1.number_input("x:", value=3.0, step=0.5, key="cx_x")
                    y_c = k2.number_input("y:", value=4.0, step=0.5, key="cx_y")
                    z_c = k3.number_input("z:", value=5.0, step=0.5, key="cx_z")
                elif sis_origen.startswith("Cil"):
                    rho_in = k1.number_input("ρ (≥ 0):", min_value=0.0, value=5.0, step=0.5, key="cl_rho")
                    th_in = k2.number_input("θ (grados):", value=53.13, step=5.0, key="cl_th")
                    z_c = k3.number_input("z:", value=5.0, step=0.5, key="cl_z")
                    x_c = rho_in * math.cos(math.radians(th_in))
                    y_c = rho_in * math.sin(math.radians(th_in))
                else:
                    r_in = k1.number_input("r (≥ 0):", min_value=0.0, value=7.071, step=0.5, key="es_r")
                    th_in = k2.number_input("θ acimutal (°):", value=53.13, step=5.0, key="es_th")
                    phi_in = k3.number_input("φ colatitud (0°..180°):", min_value=0.0, max_value=180.0, value=45.0, step=5.0, key="es_phi")
                    x_c = r_in * math.sin(math.radians(phi_in)) * math.cos(math.radians(th_in))
                    y_c = r_in * math.sin(math.radians(phi_in)) * math.sin(math.radians(th_in))
                    z_c = r_in * math.cos(math.radians(phi_in))

                rho_f = math.hypot(x_c, y_c)
                r_f = math.sqrt(x_c**2 + y_c**2 + z_c**2)
                theta_f = math.degrees(math.atan2(y_c, x_c))
                phi_f = math.degrees(math.acos(z_c / r_f)) if r_f > 1e-12 else 0.0

                st.markdown(
                    f"| Sistema | Coordenadas Equivalentes |\n"
                    f"|---|---|\n"
                    f"| **Cartesianas $(x, y, z)$** | `({x_c:.4f}, {y_c:.4f}, {z_c:.4f})` |\n"
                    f"| **Cilíndricas $(\\rho, \\theta, z)$** | `ρ = {rho_f:.4f}`, `θ = {theta_f:.2f}°`, `z = {z_c:.4f}` |\n"
                    f"| **Esféricas $(r, \\theta, \\varphi)$** | `r = {r_f:.4f}`, `θ = {theta_f:.2f}°`, `φ = {phi_f:.2f}°` |"
                )
        with c_conv2:
            with st.container(border=True):
                header_tarjeta("Ubicación del Punto P en ℝ³")
                fig, ax = _crear_fig_3d(titulo=f"P({x_c:.2f}, {y_c:.2f}, {z_c:.2f})")
                ax.quiver(0, 0, 0, x_c, y_c, z_c, color=AZUL, lw=2.5, arrow_length_ratio=0.12, label=f"r = {r_f:.2f}")
                ax.plot([0, x_c], [0, y_c], [0, 0], color=NARANJA, ls="--", lw=1.8, label=f"ρ = {rho_f:.2f}")
                ax.plot([x_c, x_c], [y_c, y_c], [0, z_c], color=VERDE, ls=":", lw=1.8, label=f"z = {z_c:.2f}")
                ax.scatter([x_c], [y_c], [z_c], color=ROJO, s=60)
                lim_p = max(abs(x_c), abs(y_c), abs(z_c), 2.0) * 1.3
                ax.set_xlim(-lim_p, lim_p)
                ax.set_ylim(-lim_p, lim_p)
                ax.set_zlim(-lim_p, lim_p)
                ax.legend(loc="upper left", fontsize=8.5)
                mostrar_figura_segura(fig)
