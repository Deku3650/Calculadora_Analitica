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
# PESTAÑA 1: SISTEMAS DINÁMICOS Y RETRATOS DE FASE (MIL VECES MÁS COMPLETO)
# ==============================================================================
with tab_sistemas:
    col_input, col_info = st.columns([1, 1.8])
    
    t_sym, x_sym, y_sym = sp.symbols('t x y')
    
    with col_input:
        st.subheader("Definición del Campo Vectorial")
        st.info("💡 Utilice 'x' e 'y' como variables de estado. Si el sistema depende del tiempo, agregue 't'.")
        
        fuente_matriz = st.radio("Método de ingreso:", ["Sistema de Ecuaciones (x', y')", "Matriz de Coeficientes", "Importar Matriz"])
        
        P_expr, Q_expr = None, None
        
        if fuente_matriz == "Sistema de Ecuaciones (x', y')":
            with st.form("form_ecuaciones"):
                str_P = st.text_input("dx/dt = P(x, y, t)", value="3*x")
                str_Q = st.text_input("dy/dt = Q(x, y, t)", value="2*x - y")
                submit_eq = st.form_submit_button("Analizar Sistema")
                
                if submit_eq:
                    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
                    transf = standard_transformations + (implicit_multiplication_application, convert_xor)
                    dicc_loc = {'x': x_sym, 'y': y_sym, 't': t_sym, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}
                    try:
                        P_expr = parse_expr(str_P, transformations=transf, local_dict=dicc_loc)
                        Q_expr = parse_expr(str_Q, transformations=transf, local_dict=dicc_loc)
                    except Exception as e:
                        st.error(f"Error de sintaxis: {e}")
                        
        elif fuente_matriz == "Matriz de Coeficientes":
            with st.form("form_matriz_sist"):
                st.latex(r"\begin{pmatrix} x' \\ y' \end{pmatrix} = \begin{pmatrix} a & b \\ c & d \end{pmatrix} \begin{pmatrix} x \\ y \end{pmatrix}")
                c1, c2 = st.columns(2)
                with c1: 
                    a11 = st.text_input("a:", value="-1")
                    a21 = st.text_input("c:", value="-1")
                with c2: 
                    a12 = st.text_input("b:", value="1")
                    a22 = st.text_input("d:", value="-1")
                if st.form_submit_button("Cargar Sistema"):
                    try:
                        P_expr = leer_expresion_st(a11)*x_sym + leer_expresion_st(a12)*y_sym
                        Q_expr = leer_expresion_st(a21)*x_sym + leer_expresion_st(a22)*y_sym
                    except: st.error("Error en las entradas de la matriz.")
                    
        elif fuente_matriz == "Importar Matriz":
            matrices_2x2 = {k: v for k, v in st.session_state.mis_matrices.items() if v.shape == (2, 2)}
            if not matrices_2x2:
                st.warning("No hay matrices $2 \times 2$ guardadas.")
            else:
                nombre_mat = st.selectbox("Seleccione Matriz:", list(matrices_2x2.keys()))
                mat = matrices_2x2[nombre_mat]
                imprimir_matriz_simbolica(mat)
                if st.button("Analizar Matriz Importada"):
                    P_expr = mat[0,0]*x_sym + mat[0,1]*y_sym
                    Q_expr = mat[1,0]*x_sym + mat[1,1]*y_sym

    # ================= PROCESAMIENTO MATEMÁTICO CENTRAL =================
    if P_expr is not None and Q_expr is not None:
        es_autonomo = not (P_expr.has(t_sym) or Q_expr.has(t_sym))
        
        with col_info:
            st.subheader("1. Ecuaciones del Sistema")
            st.latex(rf"\begin{{cases}} \frac{{dx}}{{dt}} = {sp.latex(P_expr)} \\ \frac{{dy}}{{dt}} = {sp.latex(Q_expr)} \end{{cases}}")
            
            # Si tiene 't', obligamos al usuario a "congelar" el tiempo para el análisis topológico local
            t_eval = 0
            if not es_autonomo:
                st.warning("El sistema es **NO Autónomo** (depende del tiempo 't'). El análisis cualitativo y el retrato de fase variarán en cada instante. Seleccione un valor $t_0$ para evaluar el estado instantáneo:")
                t_eval = st.slider("Evaluar en t_0 =", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)
                
            P_f = P_expr.subs(t_sym, t_eval)
            Q_f = Q_expr.subs(t_sym, t_eval)
            
            # Extracción universal de la Matriz A (Linealización vía Jacobiano en el origen)
            A_sym = sp.Matrix([
                [sp.diff(P_f, x_sym), sp.diff(P_f, y_sym)],
                [sp.diff(Q_f, x_sym), sp.diff(Q_f, y_sym)]
            ]).subs({x_sym: 0, y_sym: 0})
            
            st.write("**Matriz del Sistema (Linealización en el origen):**")
            imprimir_matriz_simbolica(A_sym)

            traza = sp.simplify(A_sym.trace())
            det = sp.simplify(A_sym.det())
            disc = sp.simplify(traza**2 - 4*det)
            
            c_eig1, c_eig2, c_eig3 = st.columns(3)
            with c_eig1: st.latex(rf"\text{{Traza }} (\tau) = {sp.latex(traza)}")
            with c_eig2: st.latex(rf"\text{{Determinante }} (\Delta) = {sp.latex(det)}")
            with c_eig3: st.latex(rf"\text{{Disc. }} = {sp.latex(disc)}")

            vectores_propios = A_sym.eigenvects()
            
            if det < 0:
                clasificacion = "Punto Silla (Inestable)"
            elif det > 0:
                if disc > 0: clasificacion = "Nodo Inestable" if traza > 0 else "Nodo Estable"
                elif disc < 0: clasificacion = "Foco Inestable (Espiral)" if traza > 0 else "Foco Estable (Espiral)"
                else: clasificacion = "Nodo Propio/Impropio " + ("Inestable" if traza > 0 else "Estable")
            else:
                clasificacion = "Puntos Críticos no aislados (Det = 0)"
            
            st.success(f"**Clasificación (Local):** {clasificacion}")
            
            st.write("**Eigenvalores ($\lambda$) y Eigenvectores ($v$):**")
            for val, mult, vects in vectores_propios:
                for v in vects: st.latex(rf"\lambda = {sp.latex(sp.simplify(val))} \implies v = {sp.latex(sp.simplify(v))}")
                    
        st.divider()
        col_sol, col_graf = st.columns([1.5, 2])
        
        with col_sol:
            st.subheader("2. Ecuación de las Curvas Solución (Órbitas)")
            st.latex(rf"\frac{{dy}}{{dx}} = \frac{{y'(t)}}{{x'(t)}} = \frac{{{sp.latex(Q_expr)}}}{{{sp.latex(P_expr)}}}")
            
            if st.button("Resolver Órbitas Analíticamente"):
                y_orb = sp.Function('y')(x_sym)
                try:
                    # Resolvemos dy/dx = Q/P
                    eq_orbita = sp.Eq(y_orb.diff(x_sym), Q_expr.subs(y_sym, y_orb) / P_expr.subs(y_sym, y_orb))
                    sol_orbita = sp.dsolve(eq_orbita, y_orb)
                    st.info("Solución de las trayectorias $y(x)$:")
                    st.latex(sp.latex(sol_orbita))
                except Exception:
                    st.error("La ecuación diferencial de la órbita no admite una solución cerrada explícita mediante los algoritmos estándar.")
                    
            st.write("**Isoclinas Cero:**")
            st.markdown(f"- **Flujo Vertical ($x'=0$):** ${sp.latex(P_f)} = 0$")
            st.markdown(f"- **Flujo Horizontal ($y'=0$):** ${sp.latex(Q_f)} = 0$")
            
            st.subheader("3. Solución Paramétrica del Sistema")
            if st.button("Extraer $x(t)$ y $y(t)$"):
                x_func = sp.Function('x')(t_sym)
                y_func = sp.Function('y')(t_sym)
                eq1 = sp.Eq(x_func.diff(t_sym), P_expr.subs({x_sym: x_func, y_sym: y_func}))
                eq2 = sp.Eq(y_func.diff(t_sym), Q_expr.subs({x_sym: x_func, y_sym: y_func}))
                try:
                    sol_param = sp.dsolve([eq1, eq2])
                    st.latex(sp.latex(sol_param[0]))
                    st.latex(sp.latex(sol_param[1]))
                except Exception:
                    st.error("El sistema requiere métodos numéricos o aproximaciones matriciales no cerradas.")
                    
        with col_graf:
            st.subheader(f"4. Retrato de Fase {'(Evaluado en t=' + str(t_eval) + ')' if not es_autonomo else ''}")
            
            if A_sym.free_symbols or A_sym.has(sp.I):
                st.warning("El campo vectorial requiere que los coeficientes evaluados sean números reales puros.")
            else:
                A_num = np.array(A_sym).astype(np.float64)
                eigen_info = []
                for val, mult, vects in vectores_propios:
                    val_num = complex(val)
                    if abs(val_num.imag) < 1e-9:
                        v_num = np.array(vects[0]).astype(np.float64).flatten()
                        eigen_info.append((val_num.real, v_num))

                @st.cache_data
                def generar_plano_fase_completo(matriz, e_info):
                    Y, X = np.mgrid[-10:10:30j, -10:10:30j]
                    U = matriz[0,0]*X + matriz[0,1]*Y
                    V = matriz[1,0]*X + matriz[1,1]*Y
                    
                    velocidad = np.sqrt(U**2 + V**2)
                    
                    fig, ax = plt.subplots(figsize=(7, 6))
                    ax.streamplot(X, Y, U, V, color=velocidad, cmap='inferno', linewidth=1, arrowsize=1.2, density=1.2)
                    
                    x_vals = np.linspace(-10, 10, 100)
                    a, b = matriz[0,0], matriz[0,1]
                    c, d = matriz[1,0], matriz[1,1]
                    
                    if b != 0: ax.plot(x_vals, (-a/b)*x_vals, 'r--', alpha=0.5, label="Isoclina x'=0")
                    elif a != 0: ax.axvline(0, color='r', linestyle='--', alpha=0.5, label="Isoclina x'=0")
                        
                    if d != 0: ax.plot(x_vals, (-c/d)*x_vals, 'b--', alpha=0.5, label="Isoclina y'=0")
                    elif c != 0: ax.axvline(0, color='b', linestyle='--', alpha=0.5, label="Isoclina y'=0")

                    for val_r, vec_r in e_info:
                        if vec_r[0] != 0:
                            m = vec_r[1] / vec_r[0]
                            ax.plot(x_vals, m*x_vals, 'g-', linewidth=2.5, label=f"Eigenvector (λ={val_r:.1f})")
                        else:
                            ax.axvline(0, color='g', linewidth=2.5, label=f"Eigenvector (λ={val_r:.1f})")

                    ax.set_xlim([-10, 10]); ax.set_ylim([-10, 10])
                    ax.axhline(0, color='black', linewidth=1); ax.axvline(0, color='black', linewidth=1)
                    ax.set_xlabel("x")
                    ax.set_ylabel("y")
                    
                    handles, labels = ax.get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize='small')
                    return fig

                st.pyplot(generar_plano_fase_completo(A_num, eigen_info))
                st.caption("🔴 **Líneas rojas:** Flujo estrictamente vertical. 🔵 **Líneas azules:** Flujo estrictamente horizontal. 🟢 **Líneas verdes:** Variedades invariantes (Eigenvectores).")

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
