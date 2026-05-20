# ==============================================================================
# 4. MÓDULO DE GEOMETRÍA (2D, 3D y Gráficos)
# ==============================================================================
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def graficar_cuadratica_st(a, b, c):
    """
    Versión adaptada para Streamlit.
    En lugar de plt.show(), devuelve el objeto 'fig' para incrustarlo en la web.
    """
    x = np.linspace(-10, 10, 400)
    y = a * x ** 2 + b * x + c

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, label=f"{a}x² + {b}x + {c}", color='blue')
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_title("Representación Gráfica de la Ecuación")
    ax.grid(True, linestyle='--')
    ax.legend()

    return fig


def renderizar_figura_3d_st(figura, params):
    """
    Motor gráfico 3D adaptado a Streamlit.
    Devuelve la figura en lugar de bloquear el hilo con plt.show().
    """
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect([1, 1, 1])

    color_cara = 'cyan'
    alfa = 0.5

    if figura == 1:  # Cilindro
        r, h = params['r'], params['h']
        z = np.linspace(0, h, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='none')
        ax.set_title(f"Cilindro (r={r}, h={h})")

    elif figura == 2:  # Esfera
        r = params['r']
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x, y, z, color=color_cara, alpha=alfa, edgecolor='none')
        ax.set_title(f"Esfera (r={r})")

    elif figura == 3:  # Cono
        r = params['r']
        if 'h' in params:
            h = params['h']
        else:
            s = params['s']
            if s <= r:
                st.error("Error: La generatriz debe ser mayor al radio.")
                return None
            h = math.sqrt(s ** 2 - r ** 2)

        z = np.linspace(0, h, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r_grid = r * (1 - z_grid / h)
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='none')
        ax.set_title(f"Cono (r={r}, h={h:.2f})")

    elif figura == 4:  # Pirámide base cuadrada
        b = params['b']
        if 'h' in params:
            h = params['h']
        else:
            s = params['s']
            if s <= b / 2:
                st.error("Error: Altura lateral muy corta para formar la pirámide.")
                return None
            h = math.sqrt(s ** 2 - (b / 2) ** 2)

        Z = np.array([[-b / 2, -b / 2, 0], [b / 2, -b / 2, 0], [b / 2, b / 2, 0], [-b / 2, b / 2, 0], [0, 0, h]])
        caras = [[Z[0], Z[1], Z[2], Z[3]], [Z[0], Z[1], Z[4]], [Z[1], Z[2], Z[4]], [Z[2], Z[3], Z[4]],
                 [Z[3], Z[0], Z[4]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        ax.set_xlim([-b, b]);
        ax.set_ylim([-b, b]);
        ax.set_zlim([0, h * 1.2])
        ax.set_title(f"Pirámide Cuadrangular")

    elif figura == 5:  # Prisma rectangular
        l, w, h = params['l'], params['w'], params['h']
        Z = np.array([[-l / 2, -w / 2, 0], [l / 2, -w / 2, 0], [l / 2, w / 2, 0], [-l / 2, w / 2, 0],
                      [-l / 2, -w / 2, h], [l / 2, -w / 2, h], [l / 2, w / 2, h], [-l / 2, w / 2, h]])
        caras = [[Z[0], Z[1], Z[2], Z[3]], [Z[4], Z[5], Z[6], Z[7]], [Z[0], Z[1], Z[5], Z[4]],
                 [Z[2], Z[3], Z[7], Z[6]], [Z[1], Z[2], Z[6], Z[5]], [Z[4], Z[7], Z[3], Z[0]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        lim = max(l, w, h)
        ax.set_xlim([-lim, lim]);
        ax.set_ylim([-lim, lim]);
        ax.set_zlim([0, lim])
        ax.set_title(f"Prisma Rectangular")

    elif figura == 6:  # Prisma triangular
        b, l_tri, h = params['b'], params['l'], params['h']
        Z = np.array([[-b / 2, 0, 0], [b / 2, 0, 0], [0, l_tri, 0],
                      [-b / 2, 0, h], [b / 2, 0, h], [0, l_tri, h]])
        caras = [[Z[0], Z[1], Z[2]], [Z[3], Z[4], Z[5]], [Z[0], Z[1], Z[4], Z[3]],
                 [Z[1], Z[2], Z[5], Z[4]], [Z[2], Z[0], Z[3], Z[5]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        lim = max(b, l_tri, h)
        ax.set_xlim([-lim, lim]);
        ax.set_ylim([-lim, lim]);
        ax.set_zlim([0, lim])
        ax.set_title(f"Prisma Triangular")

    ax.set_xlabel('Eje X');
    ax.set_ylabel('Eje Y');
    ax.set_zlabel('Eje Z')
    return fig


def Geometria_UI():
    """
    Interfaz principal para el módulo geométrico.
    Sustituye la navegación por menús de consola usando Pestañas (Tabs).
    """
    st.header("📐 Módulo de Geometría")

    # Creamos pestañas para agrupar las herramientas
    tab1, tab2, tab3 = st.tabs(["Figuras 2D", "Geometría Analítica", "Figuras 3D (Áreas y Volúmenes)"])

    # ---------------------------------------------------------
    # PESTAÑA 1: FIGURAS 2D
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Cálculo de Áreas 2D")
        figura_2d = st.selectbox("Seleccione la figura:", ["Cuadrado", "Rectángulo", "Círculo", "Triángulo"])

        if figura_2d == "Cuadrado":
            L = st.number_input("Lado del cuadrado:", min_value=0.0, value=1.0)
            st.success(f"**Área:** {L ** 2:.2f}")

        elif figura_2d == "Rectángulo":
            col1, col2 = st.columns(2)
            with col1:
                b = st.number_input("Base:", min_value=0.0, value=1.0)
            with col2:
                h = st.number_input("Altura:", min_value=0.0, value=1.0)
            st.success(f"**Área:** {b * h:.2f}")

        elif figura_2d == "Círculo":
            r = st.number_input("Radio:", min_value=0.0, value=1.0)
            st.success(f"**Área:** {math.pi * (r ** 2):.2f}")


        elif figura_2d == "Triángulo":

            metodo_tri = st.radio("Método de cálculo:",
                                  ["Base y Altura", "Tres lados (Fórmula de Herón)", "Ángulo y dos lados"])

            if metodo_tri == "Base y Altura":

                col1, col2 = st.columns(2)

                with col1:
                    b = st.number_input("Base (b):", min_value=0.0, value=1.0)

                with col2:
                    h = st.number_input("Altura (h):", min_value=0.0, value=1.0)

                st.success(f"**Área:** {(b * h) / 2:.2f}")


            elif metodo_tri == "Tres lados (Fórmula de Herón)":

                c1, c2, c3 = st.columns(3)

                with c1:
                    l1 = st.number_input("Lado 1:", min_value=0.001, value=1.0)

                with c2:
                    l2 = st.number_input("Lado 2:", min_value=0.001, value=1.0)

                with c3:
                    l3 = st.number_input("Lado 3:", min_value=0.001, value=1.0)

                if (l1 + l2 > l3) and (l1 + l3 > l2) and (l2 + l3 > l1):

                    s = (l1 + l2 + l3) / 2

                    area = math.sqrt(s * (s - l1) * (s - l2) * (s - l3))

                    st.success(f"**Área:** {area:.2f}")

                else:

                    st.error("Error: Esos lados violan la Desigualdad Triangular.")


            elif metodo_tri == "Ángulo y dos lados":

                c1, c2, c3 = st.columns(3)

                with c1:
                    l1 = st.number_input("Lado 1:", min_value=0.0, value=1.0, key="ang_l1")

                with c2:
                    l2 = st.number_input("Lado 2:", min_value=0.0, value=1.0, key="ang_l2")

                with c3:
                    ang = st.number_input("Ángulo (grados):", min_value=0.0, max_value=179.9, value=90.0)

                area = (l1 * l2 * math.sin(math.radians(ang))) / 2

                st.success(f"**Área:** {area:.2f}")