import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# Importación estricta de nuestras herramientas de parseo e impresión
try:
    from utils import leer_expresion_st, imprimir_matriz_simbolica
except ImportError:
    st.error("Error crítico: No se pudo cargar el analizador matemático desde utils.py. Asegúrese de ejecutar la app desde la raíz.")
    st.stop()

st.set_page_config(page_title="Ecuaciones Diferenciales", layout="wide")

if 'mis_matrices' not in st.session_state:
    st.session_state.mis_matrices = {}

st.title("🌪️ Ecuaciones Diferenciales y Sistemas Dinámicos")
st.markdown("Análisis de campos vectoriales, retratos de fase en $\mathbb{R}^2$ y soluciones analíticas para modelos dinámicos continuos.")

tab_sistemas, tab_edo1 = st.tabs([
    "Sistemas Lineales y Plano Fase ($X' = AX$)",
    "Resolutor Analítico General (EDO 1er Orden)"
])

# ==============================================================================
# PESTAÑA 1: SISTEMAS LINEALES EN R2 Y RETRATOS DE FASE
# ==============================================================================
with tab_sistemas:
    st.subheader("Sistemas Autónomos Lineales bidimensionales")
    st.latex(r"X' = A X \implies \begin{pmatrix} x'(t) \\ y'(t) \end{pmatrix} = \begin{pmatrix} a & b \\ c & d \end{pmatrix} \begin{pmatrix} x(t) \\ y(t) \end{pmatrix}")
    
    col_input, col_info = st.columns([1, 1.5])
    
    with col_input:
        st.write("### Matriz de Coeficientes ($A$)")
        fuente_matriz = st.radio("Método de ingreso:", ["Ingreso Manual", "Importar del Módulo de Matrices"], horizontal=True)
        
        elementos_A = [[0, 0], [0, 0]]
        
        if fuente_matriz == "Importar del Módulo de Matrices":
            # Filtramos solo las matrices 2x2 almacenadas
            matrices_2x2 = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape == (2, 2)}
            if not matrices_2x2:
                st.warning("No hay matrices $2 \\times 2$ guardadas. Cambie a Ingreso Manual.")
                mat_seleccionada = None
            else:
                nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_2x2.keys()))
                mat_seleccionada = matrices_2x2[nombre_mat]
                imprimir_matriz_simbolica(mat_seleccionada)
                # Extraemos los elementos para poder plotear y operar
                elementos_A = [[mat_seleccionada[0,0], mat_seleccionada[0,1]], 
                               [mat_seleccionada[1,0], mat_seleccionada[1,1]]]
        else:
            with st.form("form_matriz_sist"):
                c1, c2 = st.columns(2)
                with c1: 
                    a11 = st.text_input("a11 (x'):", value="-1")
                    a21 = st.text_input("a21 (y'):", value="-1")
                with c2: 
                    a12 = st.text_input("a12 (x'):", value="1")
                    a22 = st.text_input("a22 (y'):", value="-1")
                submit_mat = st.form_submit_button("Cargar Sistema")
                
                if submit_mat:
                    try:
                        elementos_A = [[leer_expresion_st(a11), leer_expresion_st(a12)],
                                       [leer_expresion_st(a21), leer_expresion_st(a22)]]
                    except Exception:
                        st.error("Error al leer los valores. Use números o expresiones válidas.")
                        
    # Si tenemos una matriz válida cargada (ya sea manual o importada)
    if not any(None in fila for fila in elementos_A):
        A_sym = sp.Matrix(elementos_A)
        
        with col_info:
            st.write("### Clasificación del Punto Crítico (El Origen)")
            
            traza = sp.simplify(A_sym.trace())
            det = sp.simplify(A_sym.det())
            discriminante = sp.simplify(traza**2 - 4*det)
            
            st.latex(rf"\text{{Traza }} (\tau) = {sp.latex(traza)} \quad | \quad \text{{Determinante }} (\Delta) = {sp.latex(det)}")
            st.latex(rf"\text{{Discriminante }} (\tau^2 - 4\Delta) = {sp.latex(discriminante)}")
            
            # Clasificación topológica del sistema
            clasificacion = "Desconocido"
            if det < 0: clasificacion = "Punto Silla (Inestable)"
            elif det > 0:
                if discriminante > 0:
                    clasificacion = "Nodo Inestable (Fuente)" if traza > 0 else "Nodo Estable (Sumidero)"
                elif discriminante < 0:
                    clasificacion = "Foco Inestable (Espiral)" if traza > 0 else "Foco Estable (Espiral)"
                elif discriminante == 0:
                    clasificacion = "Nodo Propio/Impropio " + ("Inestable" if traza > 0 else "Estable")
            elif det == 0:
                clasificacion = "Línea de Puntos Ceros (No aislado)"
            
            st.success(f"**Topología del Sistema:** {clasificacion}")
            
            # Valores Propios (Conexión Lineal I -> Ecuaciones)
            st.write("**Valores Propios ($\lambda_1, \lambda_2$):**")
            eigenvals = list(A_sym.eigenvals().keys())
            for idx, val in enumerate(eigenvals):
                st.latex(rf"\lambda_{idx+1} = {sp.latex(sp.simplify(val))}")

        st.divider()
        col_sol, col_graf = st.columns([1.2, 1.5])
        
        with col_sol:
            st.write("### Solución Analítica General")
            if st.button("Generar Solución con SymPy"):
                t = sp.Symbol('t')
                x = sp.Function('x')(t)
                y = sp.Function('y')(t)
                
                # Ecuaciones acopladas
                eq1 = sp.Eq(x.diff(t), A_sym[0,0]*x + A_sym[0,1]*y)
                eq2 = sp.Eq(y.diff(t), A_sym[1,0]*x + A_sym[1,1]*y)
                
                try:
                    solucion = sp.dsolve([eq1, eq2])
                    st.info("💡 **Solución del sistema acoplado:**")
                    st.latex(sp.latex(solucion[0]))
                    st.latex(sp.latex(solucion[1]))
                except NotImplementedError:
                    st.error("SymPy no pudo encontrar una solución analítica cerrada para este sistema.")
                    
        with col_graf:
            st.write("### Retrato de Fase (Campo Vectorial)")
            
            # Para graficar, requerimos que la matriz no tenga variables simbólicas libres (como 'k' o 'x')
            if A_sym.free_symbols or A_sym.has(sp.I):
                st.warning("El campo vectorial solo puede graficarse si la matriz de coeficientes contiene valores reales puros (sin variables ni complejos).")
            else:
                try:
                    A_num = np.array(A_sym).astype(np.float64)
                    
                    @st.cache_data
                    def generar_plano_fase(matriz_numpy):
                        Y, X = np.mgrid[-10:10:30j, -10:10:30j]
                        U = matriz_numpy[0,0]*X + matriz_numpy[0,1]*Y
                        V = matriz_numpy[1,0]*X + matriz_numpy[1,1]*Y
                        
                        velocidad = np.sqrt(U**2 + V**2)
                        
                        fig, ax = plt.subplots(figsize=(6, 5))
                        ax.streamplot(X, Y, U, V, color=velocidad, cmap='inferno', linewidth=1.5, arrowsize=1.5)
                        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
                        ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
                        ax.set_title(f"Retrato de Fase: {clasificacion}", fontsize=10)
                        ax.set_xlabel("x(t)")
                        ax.set_ylabel("y(t)")
                        return fig

                    figura_fase = generar_plano_fase(A_num)
                    st.pyplot(figura_fase)
                    st.caption("Los colores más cálidos indican trayectorias con mayor velocidad instantánea.")
                    
                except Exception as e:
                    st.error(f"Error al generar la gráfica numérica: {e}")

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
