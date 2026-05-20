import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import math
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

st.set_page_config(page_title="Geometría", layout="wide")

# ==============================================================================
# FUNCIONES DE APOYO (Gráficas)
# ==============================================================================
def graficar_cuadratica_st(a, b, c):
    x = np.linspace(-10, 10, 400)
    y = a*x**2 + b*x + c

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y, label=f"{a}x² + {b}x + {c}", color='blue')
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_title("Representación Gráfica de la Ecuación")
    ax.grid(True, linestyle='--')
    ax.legend()
    return fig

def renderizar_figura_3d_st(figura, params):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect([1,1,1])

    color_cara = 'cyan'
    alfa = 0.5 

    if figura == 1: # Cilindro
        r, h = params['r'], params['h']
        z = np.linspace(0, h, 50)
        theta = np.linspace(0, 2*np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='none')
        ax.set_title(f"Cilindro (r={r}, h={h})")

    elif figura == 2: # Esfera
        r = params['r']
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x, y, z, color=color_cara, alpha=alfa, edgecolor='none')
        ax.set_title(f"Esfera (r={r})")

    elif figura == 3: # Cono
        r = params['r']
        if 'h' in params:
            h = params['h']
        else:
            s = params['s']
            if s <= r:
                st.error("Error: La generatriz debe ser mayor al radio.")
                return None
            h = math.sqrt(s**2 - r**2)

        z = np.linspace(0, h, 50)
        theta = np.linspace(0, 2*np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r_grid = r * (1 - z_grid/h) 
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='none')
        ax.set_title(f"Cono (r={r}, h={h:.2f})")

    elif figura == 4: # Pirámide base cuadrada
        b = params['b']
        if 'h' in params:
            h = params['h']
        else:
            s = params['s']
            if s <= b/2:
                st.error("Error: Altura lateral muy corta para formar la pirámide.")
                return None
            h = math.sqrt(s**2 - (b/2)**2)

        Z = np.array([[-b/2, -b/2, 0], [b/2, -b/2, 0], [b/2, b/2, 0], [-b/2, b/2, 0], [0, 0, h]])
        caras = [[Z[0],Z[1],Z[2],Z[3]], [Z[0],Z[1],Z[4]], [Z[1],Z[2],Z[4]], [Z[2],Z[3],Z[4]], [Z[3],Z[0],Z[4]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        ax.set_xlim([-b, b]); ax.set_ylim([-b, b]); ax.set_zlim([0, h*1.2])
        ax.set_title("Pirámide Cuadrangular")

    elif figura == 5: # Prisma rectangular
        l, w, h = params['l'], params['w'], params['h']
        Z = np.array([[-l/2, -w/2, 0], [l/2, -w/2, 0], [l/2, w/2, 0], [-l/2, w/2, 0],
                      [-l/2, -w/2, h], [l/2, -w/2, h], [l/2, w/2, h], [-l/2, w/2, h]])
        caras = [[Z[0],Z[1],Z[2],Z[3]], [Z[4],Z[5],Z[6],Z[7]], [Z[0],Z[1],Z[5],Z[4]],
                 [Z[2],Z[3],Z[7],Z[6]], [Z[1],Z[2],Z[6],Z[5]], [Z[4],Z[7],Z[3],Z[0]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        lim = max(l, w, h)
        ax.set_xlim([-lim, lim]); ax.set_ylim([-lim, lim]); ax.set_zlim([0, lim])
        ax.set_title("Prisma Rectangular")

    elif figura == 6: # Prisma triangular
        b, l_tri, h = params['b'], params['l'], params['h']
        Z = np.array([[-b/2, 0, 0], [b/2, 0, 0], [0, l_tri, 0],
                      [-b/2, 0, h], [b/2, 0, h], [0, l_tri, h]])
        caras = [[Z[0],Z[1],Z[2]], [Z[3],Z[4],Z[5]], [Z[0],Z[1],Z[4],Z[3]],
                 [Z[1],Z[2],Z[5],Z[4]], [Z[2],Z[0],Z[3],Z[5]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='k'))
        lim = max(b, l_tri, h)
        ax.set_xlim([-lim, lim]); ax.set_ylim([-lim, lim]); ax.set_zlim([0, lim])
        ax.set_title("Prisma Triangular")

    ax.set_xlabel('Eje X'); ax.set_ylabel('Eje Y'); ax.set_zlabel('Eje Z')
    return fig

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================
st.header("📐 Módulo de Geometría")

tab1, tab2, tab3 = st.tabs(["Figuras 2D", "Geometría Analítica", "Figuras 3D (Áreas y Volúmenes)"])

# ---------------------------------------------------------
# PESTAÑA 1: FIGURAS 2D
# ---------------------------------------------------------
with tab1:
    st.subheader("Cálculo de Áreas 2D")
    figura_2d = st.selectbox("Seleccione la figura:", ["Cuadrado", "Rectángulo", "Círculo", "Triángulo"])
    
    if figura_2d == "Cuadrado":
        L = st.number_input("Lado del cuadrado:", min_value=0.0, value=1.0)
        st.success(f"**Área:** {L**2:.2f}")
        
    elif figura_2d == "Rectángulo":
        col1, col2 = st.columns(2)
        with col1:
            b_rect = st.number_input("Base:", min_value=0.0, value=1.0)
        with col2:
            h_rect = st.number_input("Altura:", min_value=0.0, value=1.0)
        st.success(f"**Área:** {b_rect*h_rect:.2f}")
        
    elif figura_2d == "Círculo":
        r_circ = st.number_input("Radio:", min_value=0.0, value=1.0)
        st.success(f"**Área:** {math.pi * (r_circ**2):.2f}")
        
    elif figura_2d == "Triángulo":
        metodo_tri = st.radio("Método de cálculo:", ["Base y Altura", "Tres lados (Fórmula de Herón)", "Ángulo y dos lados"])
        
        if metodo_tri == "Base y Altura":
            col1, col2 = st.columns(2)
            with col1: b_tri = st.number_input("Base (b):", min_value=0.0, value=1.0)
            with col2: h_tri = st.number_input("Altura (h):", min_value=0.0, value=1.0)
            st.success(f"**Área:** {(b_tri*h_tri)/2:.2f}")
            
        elif metodo_tri == "Tres lados (Fórmula de Herón)":
            c1, c2, c3 = st.columns(3)
            with c1: l1 = st.number_input("Lado 1:", min_value=0.001, value=1.0)
            with c2: l2 = st.number_input("Lado 2:", min_value=0.001, value=1.0)
            with c3: l3 = st.number_input("Lado 3:", min_value=0.001, value=1.0)
            
            if (l1 + l2 > l3) and (l1 + l3 > l2) and (l2 + l3 > l1):
                s_heron = (l1+l2+l3)/2
                area_heron = math.sqrt(s_heron*(s_heron-l1)*(s_heron-l2)*(s_heron-l3))
                st.success(f"**Área:** {area_heron:.2f}")
            else:
                st.error("Error: Esos lados violan la Desigualdad Triangular.")
                
        elif metodo_tri == "Ángulo y dos lados":
            c1, c2, c3 = st.columns(3)
            with c1: l1_ang = st.number_input("Lado 1:", min_value=0.0, value=1.0, key="ang_l1")
            with c2: l2_ang = st.number_input("Lado 2:", min_value=0.0, value=1.0, key="ang_l2")
            with c3: ang = st.number_input("Ángulo (grados):", min_value=0.0, max_value=179.9, value=90.0)
            
            area_ang = (l1_ang * l2_ang * math.sin(math.radians(ang))) / 2
            st.success(f"**Área:** {area_ang:.2f}")

# ---------------------------------------------------------
# PESTAÑA 2: GEOMETRÍA ANALÍTICA
# ---------------------------------------------------------
with tab2:
    st.subheader("Herramientas Analíticas")
    herramienta = st.selectbox("Seleccione la herramienta:", ["Ecuación Cuadrática", "Distancia entre 2 puntos"])
    
    if herramienta == "Ecuación Cuadrática":
        st.write("Ecuación de la forma: $$Ax^2 + Bx + C = 0$$")
        c1, c2, c3 = st.columns(3)
        with c1: a_coef = st.number_input("A:", value=1.0)
        with c2: b_coef = st.number_input("B:", value=0.0)
        with c3: c_coef = st.number_input("C:", value=0.0)
        
        if st.button("Calcular Raíces"):
            if a_coef == 0 and b_coef == 0:
                st.warning("No es una ecuación válida.")
            elif a_coef == 0:
                st.info(f"Es una ecuación lineal. Raíz: {-c_coef/b_coef:.3f}")
            else:
                d = (b_coef**2) - (4*a_coef*c_coef)
                if d >= 0:
                    x1 = (-b_coef + math.sqrt(d)) / (2*a_coef)
                    x2 = (-b_coef - math.sqrt(d)) / (2*a_coef)
                    st.success(f"**Raíces Reales:** $X_1 = {x1:.3f}$, $X_2 = {x2:.3f}$")
                else:
                    st.warning("Raíces Complejas conjugadas:")
                    ac = -b_coef / (2*a_coef)
                    bc = math.sqrt(-d) / (2*a_coef)
                    st.write(f"$X_1 = {ac:.3f} + {bc:.3f}i$")
                    st.write(f"$X_2 = {ac:.3f} - {bc:.3f}i$")
                
                st.pyplot(graficar_cuadratica_st(a_coef, b_coef, c_coef))
                
    elif herramienta == "Distancia entre 2 puntos":
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Punto A**")
            x1 = st.number_input("X1", value=0.0)
            y1 = st.number_input("Y1", value=0.0)
        with col2:
            st.write("**Punto B**")
            x2 = st.number_input("X2", value=1.0)
            y2 = st.number_input("Y2", value=1.0)
            
        dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        st.success(f"La distancia euclidiana es: **{dist:.3f}**")

# ---------------------------------------------------------
# PESTAÑA 3: FIGURAS 3D (Consolida Área y Volumen)
# ---------------------------------------------------------
with tab3:
    st.subheader("Cálculo Espacial 3D")
    figura_3d = st.selectbox("Figura:", ["Cilindro", "Esfera", "Cono", "Pirámide base cuadrada", "Prisma rectangular", "Prisma triangular"])
    operacion = st.radio("¿Qué desea calcular?", ["Volumen", "Área Superficial"], horizontal=True)
    
    params = {}
    result = 0
    
    if figura_3d == "Cilindro":
        c1, c2 = st.columns(2)
        with c1: params['r'] = st.number_input("Radio (r):", min_value=0.0, value=1.0, key="cil_r")
        with c2: params['h'] = st.number_input("Altura (h):", min_value=0.0, value=2.0, key="cil_h")
        
        if operacion == "Volumen": result = math.pi * (params['r']**2) * params['h']
        else: result = (2 * math.pi * params['r']**2) + (2 * math.pi * params['r'] * params['h'])
            
    elif figura_3d == "Esfera":
        params['r'] = st.number_input("Radio (r):", min_value=0.0, value=1.0, key="esf_r")
        if operacion == "Volumen": result = (4 * math.pi * params['r']**3) / 3
        else: result = 4 * math.pi * params['r']**2
            
    elif figura_3d == "Cono":
        c1, c2 = st.columns(2)
        with c1: params['r'] = st.number_input("Radio (r):", min_value=0.0, value=1.0, key="cono_r")
        if operacion == "Volumen":
            with c2: params['h'] = st.number_input("Altura (h):", min_value=0.0, value=2.0, key="cono_h")
            result = (math.pi * (params['r']**2) * params['h']) / 3
        else:
            with c2: params['s'] = st.number_input("Generatriz (s):", min_value=0.0, value=2.0, key="cono_s")
            result = (math.pi * params['r'] * params['s']) + (math.pi * params['r']**2)
            
    elif figura_3d == "Pirámide base cuadrada":
        c1, c2 = st.columns(2)
        with c1: params['b'] = st.number_input("Lado base (b):", min_value=0.0, value=1.0, key="pir_b")
        if operacion == "Volumen":
            with c2: params['h'] = st.number_input("Altura pirámide (h):", min_value=0.0, value=2.0, key="pir_h")
            result = ((params['b']**2) * params['h']) / 3
        else:
            with c2: params['s'] = st.number_input("Altura lateral (s):", min_value=0.0, value=2.0, key="pir_s")
            result = (2 * params['b'] * params['s']) + (params['b']**2)
            
    elif figura_3d == "Prisma rectangular":
        c1, c2, c3 = st.columns(3)
        with c1: params['l'] = st.number_input("Largo (l):", min_value=0.0, value=1.0, key="prect_l")
        with c2: params['w'] = st.number_input("Ancho (w):", min_value=0.0, value=1.0, key="prect_w")
        with c3: params['h'] = st.number_input("Altura (h):", min_value=0.0, value=2.0, key="prect_h")
        if operacion == "Volumen": result = params['l'] * params['w'] * params['h']
        else: result = 2 * ((params['w'] * params['h']) + (params['l'] * params['w']) + (params['l'] * params['h']))
            
    elif figura_3d == "Prisma triangular":
        c1, c2, c3, c4 = st.columns(4)
        with c1: params['b'] = st.number_input("Base Triángulo (b):", min_value=0.0, value=1.0, key="ptri_b")
        with c2: params['l'] = st.number_input("Altura Triángulo (l):", min_value=0.0, value=1.0, key="ptri_l")
        with c3: params['h'] = st.number_input("Altura Prisma (h):", min_value=0.0, value=2.0, key="ptri_h")
        
        if operacion == "Volumen":
            result = (params['b'] * params['l'] * params['h']) / 2
        else:
            with c4: 
                params['a'] = st.number_input("Lado 'a':", min_value=0.0, value=1.0, key="ptri_a")
                params['c'] = st.number_input("Lado 'c':", min_value=0.0, value=1.0, key="ptri_c")
            result = (params['a'] * params['h']) + (params['b'] * params['h']) + (params['c'] * params['h']) + (params['b'] * params['l'])

    st.success(f"**El {operacion.lower()} es:** {result:.2f}")
    
    if st.checkbox("Visualizar figura en 3D"):
        fig_idx = ["Cilindro", "Esfera", "Cono", "Pirámide base cuadrada", "Prisma rectangular", "Prisma triangular"].index(figura_3d) + 1
        fig = renderizar_figura_3d_st(fig_idx, params)
        if fig is not None:
            st.pyplot(fig)
