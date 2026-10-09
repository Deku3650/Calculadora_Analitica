import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import math
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Importar estilos centralizados
from estilos import cargar_estilos_globales

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Geometría - MATHESIS", page_icon="📐", layout="wide")

# 2. CARGAR ESTILOS GLOBALES
cargar_estilos_globales()

# ==============================================================================
# FUNCIONES DE APOYO (Gráficas en estética azul)
# ==============================================================================
def graficar_cuadratica_st(a, b, c):
    x = np.linspace(-10, 10, 400)
    y = a*x**2 + b*x + c

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('#0f172a')  # Fondo oscuro elegante para el plano
    
    ax.plot(x, y, label=f"f(x) = {a}x² + {b}x + {c}", color='#38bdf8', linewidth=2.5)
    ax.axhline(0, color='#64748b', linewidth=1, linestyle='--')
    ax.axvline(0, color='#64748b', linewidth=1, linestyle='--')
    
    ax.set_title("Representación Gráfica de la Ecuación", fontsize=12, fontweight='bold', color='#f8fafc')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, linestyle=':', alpha=0.3, color='#334155')
    
    legend = ax.legend(facecolor='#1e293b', edgecolor='#0284c7')
    plt.setp(legend.get_texts(), color='#f8fafc')
    
    for spine in ax.spines.values():
        spine.set_color('#0284c7')
        spine.set_alpha(0.4)
        
    return fig

@st.cache_resource
def renderizar_figura_3d_st(figura, params):
    fig = plt.figure(figsize=(6, 6))
    fig.patch.set_alpha(0.0)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#0f172a')
    ax.set_box_aspect([1,1,1])

    color_cara = '#38bdf8'
    alfa = 0.55 

    if figura == 1: # Cilindro
        r, h = params['r'], params['h']
        z = np.linspace(0, h, 30)
        theta = np.linspace(0, 2*np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='#0284c7')
        ax.set_title(f"Cilindro (r={r}, h={h})", color='#f8fafc', fontweight='bold')

    elif figura == 2: # Esfera
        r = params['r']
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        x = r * np.outer(np.cos(u), np.sin(v))
        y = r * np.outer(np.sin(u), np.sin(v))
        z = r * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x, y, z, color=color_cara, alpha=alfa, edgecolor='#0284c7')
        ax.set_title(f"Esfera (r={r})", color='#f8fafc', fontweight='bold')

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

        z = np.linspace(0, h, 30)
        theta = np.linspace(0, 2*np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r_grid = r * (1 - z_grid/h) 
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=alfa, color=color_cara, edgecolor='#0284c7')
        ax.set_title(f"Cono (r={r}, h={h:.2f})", color='#f8fafc', fontweight='bold')

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
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='#38bdf8'))
        ax.set_xlim([-b, b]); ax.set_ylim([-b, b]); ax.set_zlim([0, h*1.2])
        ax.set_title("Pirámide Cuadrangular", color='#f8fafc', fontweight='bold')

    elif figura == 5: # Prisma rectangular
        l, w, h = params['l'], params['w'], params['h']
        Z = np.array([[-l/2, -w/2, 0], [l/2, -w/2, 0], [l/2, w/2, 0], [-l/2, w/2, 0],
                      [-l/2, -w/2, h], [l/2, -w/2, h], [l/2, w/2, h], [-l/2, w/2, h]])
        caras = [[Z[0],Z[1],Z[2],Z[3]], [Z[4],Z[5],Z[6],Z[7]], [Z[0],Z[1],Z[5],Z[4]],
                 [Z[2],Z[3],Z[7],Z[6]], [Z[1],Z[2],Z[6],Z[5]], [Z[4],Z[7],Z[3],Z[0]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='#38bdf8'))
        lim = max(l, w, h)
        ax.set_xlim([-lim, lim]); ax.set_ylim([-lim, lim]); ax.set_zlim([0, lim])
        ax.set_title("Prisma Rectangular", color='#f8fafc', fontweight='bold')

    elif figura == 6: # Prisma triangular
        b, l_tri, h = params['b'], params['l'], params['h']
        Z = np.array([[-b/2, 0, 0], [b/2, 0, 0], [0, l_tri, 0],
                      [-b/2, 0, h], [b/2, 0, h], [0, l_tri, h]])
        caras = [[Z[0],Z[1],Z[2]], [Z[3],Z[4],Z[5]], [Z[0],Z[1],Z[4],Z[3]],
                 [Z[1],Z[2],Z[5],Z[4]], [Z[2],Z[0],Z[3],Z[5]]]
        ax.add_collection3d(Poly3DCollection(caras, alpha=alfa, facecolors=color_cara, edgecolors='#38bdf8'))
        lim = max(b, l_tri, h)
        ax.set_xlim([-lim, lim]); ax.set_ylim([-lim, lim]); ax.set_zlim([0, lim])
        ax.set_title("Prisma Triangular", color='#f8fafc', fontweight='bold')

    ax.set_xlabel('Eje X', color='#94a3b8'); ax.set_ylabel('Eje Y', color='#94a3b8'); ax.set_zlabel('Eje Z', color='#94a3b8')
    ax.tick_params(colors='#64748b')
    return fig

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================

# ENCABEZADO CON BANNER PERSONALIZADO
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">📐 Módulo de Geometría</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Figuras 2D", "Geometría Analítica", "Figuras 3D (Áreas y Volúmenes)"])

# ---------------------------------------------------------
# PESTAÑA 1: FIGURAS 2D
# ---------------------------------------------------------
with tab1:
