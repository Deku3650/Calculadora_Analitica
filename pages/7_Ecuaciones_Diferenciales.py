import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

try:
    from utils import leer_expresion_st, imprimir_matriz_simbolica
except ImportError:
    st.error("Error crítico: No se pudo cargar el analizador matemático desde utils.py. Asegúrese de ejecutar la app desde la raíz.")
    st.stop()

st.set_page_config(page_title="Ecuaciones Diferenciales", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🌪️ Ecuaciones Diferenciales y Sistemas Dinámicos")
st.markdown("Análisis topológico exhaustivo, órbitas, isoclinas y retrato de fase avanzado en $\mathbb{R}^2$.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas Autónomos ($X' = AX$)",
    "Resolutor Analítico General (EDO 1er Orden)"
])

# ==============================================================================
# PESTAÑA 1: SISTEMAS LINEALES EN R2 (MIL VECES MÁS COMPLETO)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 2])
    
    with col_input:
        st.subheader("Matriz del Sistema ($A$)")
        st.latex(r"X' = A X \implies \begin{cases} x' = ax + by \\ y' = cx + dy \end{cases}")
        
        fuente_matriz = st.radio("Método de ingreso:", ["Ingreso Manual", "Importar del Módulo de Matrices"])
        elementos_A = [[0, 0], [0, 0]]
        
        if fuente_matriz == "Importar del Módulo de Matrices":
            matrices_2x2 = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape == (2, 2)}
            if not matrices_2x2:
                st.warning("No hay matrices $2 \times 2$ guardadas.")
                mat_seleccionada = None
            else:
                nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_2x2.keys()))
                mat_seleccionada = matrices_2x2[nombre_mat]
                imprimir_matriz_simbolica(mat_seleccionada)
                elementos_A = [[mat_seleccionada[0,0], mat_seleccionada[0,1]], 
                               [mat_seleccionada[1,0], mat_seleccionada[1,1]]]
        else:
            with st.form("form_matriz_sist"):
                c1, c2 = st.columns(2)
                with c1: 
                    a11 = st.text_input("a (para x'):", value="-1")
                    a21 = st.text_input("c (para y'):", value="-1")
                with c2: 
                    a12 = st.text_input("b (para x'):", value="1")
                    a22 = st.text_input("d (para y'):", value="-1")
                submit_mat = st.form_submit_button("Cargar Sistema")
                
                if submit_mat:
                    try:
                        elementos_A = [[leer_expresion_st(a11), leer_expresion_st(a12)],
                                       [leer_expresion_st(a21), leer_expresion_st(a22)]]
                    except Exception:
                        st.error("Error matemático en las entradas.")
                        
    if not any(None in fila for fila in elementos_A):
        A_sym = sp.Matrix(elementos_A)
        
        with col_info:
            st.subheader("1. Análisis Espectral y Clasificación Topológica")
            
            traza = sp.simplify(A_sym.trace())
            det = sp.simplify(A_sym.det())
            disc = sp.simplify(traza**2 - 4*det)
            
            c_eig1, c_eig2, c_eig3 = st.columns(3)
            with c_eig1: st.latex(rf"\text{{Traza }} (\tau) = {sp.latex(traza)}")
            with c_eig2: st.latex(rf"\text{{Determinante }} (\Delta) = {sp.latex(det)}")
            with c_eig3: st.latex(rf"\text{{Disc. }} (\tau^2 - 4\Delta) = {sp.latex(disc)}")

            vectores_propios = A_sym.eigenvects()
            
            # Clasificación rigurosa basada en Eigenvalores
            if det < 0:
                clasificacion = "Punto Silla (Inestable)"
                razon = "Los valores propios son reales y de signos opuestos. Las trayectorias se acercan por una variedad y se alejan por la otra."
            elif det > 0:
                if disc > 0:
                    clasificacion = "Nodo Inestable (Fuente)" if traza > 0 else "Nodo Estable (Sumidero)"
                    razon = "Valores propios reales, distintos y del mismo signo."
                elif disc < 0:
                    clasificacion = "Foco Inestable (Espiral Hacia Afuera)" if traza > 0 else "Foco Estable (Espiral Hacia Adentro)"
                    razon = "Valores propios complejos conjugados. La parte real define la estabilidad, la imaginaria genera la rotación."
                else:
                    clasificacion = "Nodo Propio/Impropio " + ("Inestable" if traza > 0 else "Estable")
                    razon = "Raíz real repetida (Multiplicidad algebraica 2)."
            else:
                clasificacion = "Línea de Puntos Críticos (No aislado)"
                razon = "El determinante es 0. Existe al menos un eigenvalor nulo, generando infinidad de puntos de equilibrio."
            
            st.success(f"**Naturaleza del Origen:** {clasificacion}")
            st.caption(f"*Justificación:* {razon}")
            
            st.write("**Estructura de Eigenvalores ($\lambda$) y Eigenvectores ($v$):**")
            for val, mult, vects in vectores_propios:
                for v in vects:
                    st.latex(rf"\lambda = {sp.latex(sp.simplify(val))} \implies v = {sp.latex(sp.simplify(v))}")
                    
        st.divider()
        
        col_sol, col_graf = st.columns([1.5, 2])
        
        with col_sol:
            st.subheader("2. Ecuación de las Órbitas (Pendiente)")
            num = A_sym[1,0]*sp.Symbol('x') + A_sym[1,1]*sp.Symbol('y')
            den = A_sym[0,0]*sp.Symbol('x') + A_sym[0,1]*sp.Symbol('y')
            st.latex(rf"\frac{{dy}}{{dx}} = \frac{{y'(t)}}{{x'(t)}} = \frac{{{sp.latex(num)}}}{{{sp.latex(den)}}}")
            
            st.write("**Isoclinas Cero (Direcciones Ortogonales):**")
            st.markdown(f"- **Flujo estrictamente Vertical ($x'=0$):** Donde ${sp.latex(den)} = 0$")
            st.markdown(f"- **Flujo estrictamente Horizontal ($y'=0$):** Donde ${sp.latex(num)} = 0$")
            
            st.subheader("3. Solución Analítica Explícita")
            t = sp.Symbol('t')
            x = sp.Function('x')(t)
            y = sp.Function('y')(t)
            eq1 = sp.Eq(x.diff(t), A_sym[0,0]*x + A_sym[0,1]*y)
            eq2 = sp.Eq(y.diff(t), A_sym[1,0]*x + A_sym[1,1]*y)
            
            if st.button("Extraer Funciones Paramétricas $x(t), y(t)$"):
                try:
                    solucion = sp.dsolve([eq1, eq2])
                    st.latex(sp.latex(solucion[0]))
                    st.latex(sp.latex(solucion[1]))
                except Exception as e:
                    st.error("El sistema requiere integración numérica o posee una estructura no soportada analíticamente por la librería.")
                    
        with col_graf:
            st.subheader("4. Retrato de Fase Avanzado")
            
            if A_sym.free_symbols or A_sym.has(sp.I):
                st.warning("El campo vectorial numérico requiere que todos los coeficientes de la matriz sean números reales explícitos.")
            else:
                A_num = np.array(A_sym).astype(np.float64)
                
                # Extracción numérica de eigenvectores para graficarlos
                eigen_info = []
                for val, mult, vects in vectores_propios:
                    val_num = complex(val)
                    if abs(val_num.imag) < 1e-9: # Si es real
                        v_num = np.array(vects[0]).astype(np.float64).flatten()
                        eigen_info.append((val_num.real, v_num))

                @st.cache_data
                def generar_plano_fase_completo(matriz, e_info):
                    Y, X = np.mgrid[-10:10:30j, -10:10:30j]
                    U = matriz[0,0]*X + matriz[0,1]*Y
                    V = matriz[1,0]*X + matriz[1,1]*Y
                    
                    velocidad = np.sqrt(U**2 + V**2)
                    # Normalizamos para que las flechas tengan tamaño uniforme pero color por velocidad
                    U_norm = np.where(velocidad == 0, 0, U/velocidad)
                    V_norm = np.where(velocidad == 0, 0, V/velocidad)
                    
                    fig, ax = plt.subplots(figsize=(7, 6))
                    ax.streamplot(X, Y, U, V, color=velocidad, cmap='inferno', linewidth=1, arrowsize=1.2, density=1.2)
                    
                    # Rango para trazar rectas
                    x_vals = np.linspace(-10, 10, 100)
                    a, b = matriz[0,0], matriz[0,1]
                    c, d = matriz[1,0], matriz[1,1]
                    
                    # Trazado de Isoclina x'=0 (Flujo vertical, línea roja)
                    if b != 0: ax.plot(x_vals, (-a/b)*x_vals, 'r--', alpha=0.5, label="Isoclina x'=0")
                    elif a != 0: ax.axvline(0, color='r', linestyle='--', alpha=0.5, label="Isoclina x'=0")
                        
                    # Trazado de Isoclina y'=0 (Flujo horizontal, línea azul)
                    if d != 0: ax.plot(x_vals, (-c/d)*x_vals, 'b--', alpha=0.5, label="Isoclina y'=0")
                    elif c != 0: ax.axvline(0, color='b', linestyle='--', alpha=0.5, label="Isoclina y'=0")

                    # Trazado de Variedades Invariantes (Eigenvectores, líneas verdes)
                    for val_r, vec_r in e_info:
                        if vec_r[0] != 0:
                            m = vec_r[1] / vec_r[0]
                            ax.plot(x_vals, m*x_vals, 'g-', linewidth=2.5, label=f"Eigenvector (λ={val_r:.1f})")
                        else:
                            ax.axvline(0, color='g', linewidth=2.5, label=f"Eigenvector (λ={val_r:.1f})")

                    ax.set_xlim([-10, 10])
                    ax.set_ylim([-10, 10])
                    ax.axhline(0, color='black', linewidth=1)
                    ax.axvline(0, color='black', linewidth=1)
                    ax.set_xlabel("x(t)")
                    ax.set_ylabel("y(t)")
                    
                    # Evitar duplicados en la leyenda
                    handles, labels = ax.get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize='small')
                    
                    return fig

                figura = generar_plano_fase_completo(A_num, eigen_info)
                st.pyplot(figura)
                st.caption("🔴 **Líneas rojas:** Cruce estrictamente vertical. 🔵 **Líneas azules:** Cruce estrictamente horizontal. 🟢 **Líneas verdes sólidas:** Soluciones de línea recta (Variedades Invariantes).")

# ==============================================================================
# PESTAÑA 2: EDOs DE PRIMER ORDEN
# ==============================================================================
with tab_edo1:
    st.subheader("Resolutor de EDOs de 1er Orden")
    st.markdown("Resuelve ecuaciones de la forma $y'(x) = f(x, y)$ o combinaciones lineales de sus diferenciales.")
    
    st.info("💡 **Sintaxis del Motor (SymPy):** Escriba su ecuación usando `y` como la función, `x` como la variable independiente, y `diff(y, x)` para la derivada $y'$. Por ejemplo: `diff(y, x) + 2*y - exp(x)`")
    
    eq_str = st.text_input("Ingrese la expresión diferencial (asumiendo que está igualada a cero):", value="diff(y, x) + (2/x)*y - x**3")
    
    c_pvi1, c_pvi2 = st.columns(2)
    with c_pvi1:
        usar_pvi = st.checkbox("Resolver Problema de Valor Inicial (PVI)")
    
    x0_str = "1"
    y0_str = "0"
    if usar_pvi:
        with c_pvi2:
            st.write("Condición Inicial: $y(x_0) = y_0$")
            c_p1, c_p2 = st.columns(2)
            with c_p1: x0_str = st.text_input("x0:", value="1")
            with c_p2: y0_str = st.text_input("y0:", value="0")
            
    if st.button("Resolver Ecuación Diferencial"):
        x = sp.Symbol('x')
        y = sp.Function('y')(x)
        diccionario_edo = {'x': x, 'y': y, 'diff': sp.diff, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos}
        
        try:
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
            transformaciones = standard_transformations + (implicit_multiplication_application, convert_xor)
            
            eq_parseada = parse_expr(eq_str, transformations=transformaciones, local_dict=diccionario_edo)
            ecuacion_formal = sp.Eq(eq_parseada, 0)
            
            st.write("**Ecuación interpretada:**")
            st.latex(sp.latex(ecuacion_formal))
            
            if usar_pvi:
                x0_val = leer_expresion_st(x0_str)
                y0_val = leer_expresion_st(y0_str)
                ics_dict = {y.subs(x, x0_val): y0_val}
                sol = sp.dsolve(ecuacion_formal, y, ics=ics_dict)
                st.success("**Solución Particular (PVI):**")
            else:
                sol = sp.dsolve(ecuacion_formal, y)
                st.success("**Solución General:**")
                
            st.latex(sp.latex(sol))
            
        except Exception as e:
            st.error(f"Error de sintaxis o resolución. Asegúrese de que la ecuación sea separable, exacta o lineal. Detalle: {e}")
