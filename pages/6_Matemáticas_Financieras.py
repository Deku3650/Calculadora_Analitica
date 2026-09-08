import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import date

st.set_page_config(page_title="Matemáticas Financieras", layout="wide")

if 'mis_inversiones' not in st.session_state:
    st.session_state.mis_inversiones = {}

st.title("📈 Módulo de Matemáticas Financieras")
st.markdown("Plataforma actuarial de valuación, tasas equivalentes, escenarios dinámicos y cuadros de amortización.")

# Diccionarios de conversión de tiempo a base anual
factores_tiempo = {
    "Años": 1, "Semestres": 2, "Cuatrimestres": 3, "Trimestres": 4, 
    "Bimestres": 6, "Meses": 12, "Quincenas": 24, "Semanas": 52, "Días (Base 360)": 360, "Días (Base 365)": 365
}

tab_lab, tab_tasas, tab_fechas, tab_anualidades = st.tabs([
    "1. Laboratorio de Valuación y Curvas", 
    "2. Tasas Equivalentes e Inflación", 
    "3. Fechas Actuariales",
    "4. Anualidades y Amortización"
])

# ==============================================================================
# PESTAÑA 1: LABORATORIO DE VALUACIÓN Y CURVAS (Todo integrado)
# ==============================================================================
with tab_lab:
    st.subheader("Cálculo de Escenarios y Proyección Gráfica")
    
    col_reg, col_var = st.columns(2)
    with col_reg:
        regimen = st.radio("Régimen Financiero:", 
                           ["Interés Simple", "Interés Compuesto", "Interés Continuo", "Descuento Bancario", "Tasa Variable (Escalonada)"], 
                           horizontal=True)
    with col_var:
        if regimen == "Descuento Bancario":
            opciones_calc = ["Valor Nominal (M)", "Valor Efectivo (C)", "Tasa de Descuento (d)", "Tiempo (t)"]
        elif regimen == "Tasa Variable (Escalonada)":
            opciones_calc = ["Proyectar Monto Final (M)"]
        else:
            opciones_calc = ["Monto Final (M)", "Capital Inicial (C)", "Tasa de Interés (i)", "Tiempo (t)"]
        var_calc = st.selectbox("Variable a despejar:", opciones_calc)
        
    st.divider()
    
    # --------------------------------------------------------------------------
    # MODO: TASA VARIABLE
    # --------------------------------------------------------------------------
    if regimen == "Tasa Variable (Escalonada)":
        st.info("💡 **Modelo de Tasa Variable:** Ingrese el capital y defina los distintos periodos y tasas aplicables a lo largo del tiempo. Asume capitalización compuesta.")
        col_c_var, col_t_var = st.columns(2)
        with col_c_var:
            C_var = st.number_input("Capital Inicial (C):", min_value=0.01, value=1000.0, step=100.0)
        with col_t_var:
            unidad_t_var = st.selectbox("Unidad base de los periodos:", list(factores_tiempo.keys()), index=0, key="ut_var")

        st.write("Defina el calendario de tasas (Edite directamente la tabla):")
        df_tasas = pd.DataFrame([
            {"Periodos (Duración)": 1.0, "Tasa Aplicable (%)": 5.0},
            {"Periodos (Duración)": 2.0, "Tasa Aplicable (%)": 6.5},
            {"Periodos (Duración)": 1.5, "Tasa Aplicable (%)": 4.0}
        ])
        
        datos_tasas = st.data_editor(df_tasas, num_rows="dynamic", use_container_width=True, key="tabla_tasas")
        
        if st.button("Proyectar Crecimiento Variable"):
            saldo_var = C_var
            tiempo_acumulado = 0.0
            puntos_curva = [{"Tiempo": 0.0, "Monto": saldo_var}]
            
            for i, row in datos_tasas.iterrows():
                t_tramo = float(row["Periodos (Duración)"])
                tasa_tramo = float(row["Tasa Aplicable (%)"]) / 100
                saldo_var = saldo_var * (1 + tasa_tramo)**t_tramo
                tiempo_acumulado += t_tramo
                puntos_curva.append({"Tiempo": tiempo_acumulado, "Monto": saldo_var})
                
            st.success("Proyección escalonada completada.")
            st.metric("Monto Final Proyectado (M)", f"${saldo_var:,.2f}")
            
            st.write("### Evolución del Fondo con Tasa Variable")
            df_curva_var = pd.DataFrame(puntos_curva).set_index("Tiempo")
            st.line_chart(df_curva_var)

    # --------------------------------------------------------------------------
    # MODO: TASAS FIJAS
    # --------------------------------------------------------------------------
    else:
        with st.form("form_universal"):
            c1, c2, c3, c4 = st.columns(4)
            
            if "Monto" not in var_calc and "Nominal" not in var_calc:
                with c1: val_M = st.number_input("Monto / VN (M):", min_value=0.01, value=1500.0, step=100.0)
            if "Capital" not in var_calc and "Efectivo" not in var_calc:
                with c1 if ("Monto" in var_calc or "Nominal" in var_calc) else c2: 
                    val_C = st.number_input("Capital / VE (C):", min_value=0.01, value=1000.0, step=100.0)
            
            if "Tasa" not in var_calc:
                col_tasa = c2 if ("Monto" in var_calc or "Capital" in var_calc or "Nominal" in var_calc or "Efectivo" in var_calc) else c3
                with col_tasa: 
                    val_i_porc = st.number_input("Tasa (%)", value=10.0, step=0.5)
                    val_i = val_i_porc / 100
                    unidad_i = st.selectbox("Expresada en:", list(factores_tiempo.keys()), index=0)
            
            if "Tiempo" not in var_calc:
                with c3 if "Tasa" in var_calc else c4: 
                    val_t_raw = st.number_input("Tiempo (t):", min_value=0.01, value=1.0, step=0.5)
                    unidad_t = st.selectbox("Unidad de tiempo:", list(factores_tiempo.keys()), index=0)
            
            st.write("---")
            nom_custom = st.text_input("Nombre para la gráfica (Deje en blanco para auto-nombrar):", placeholder="Ej. Inversión Banco A")
            submit_uni = st.form_submit_button("Calcular y Graficar Escenario")
            
        if submit_uni:
            res = 0.0
            form_tex = ""
            
            if "Tasa" not in var_calc and "Tiempo" not in var_calc:
                factor_tasa = factores_tiempo[unidad_i]
                factor_tiempo = factores_tiempo[unidad_t]
                val_t_efectivo = val_t_raw * (factor_tasa / factor_tiempo)
            
            try:
                # INTERÉS SIMPLE
                if regimen == "Interés Simple":
                    if "Monto" in var_calc: res = val_C * (1 + val_i * val_t_efectivo); form_tex = r"M = C(1 + it)"
                    elif "Capital" in var_calc: res = val_M / (1 + val_i * val_t_efectivo); form_tex = r"C = \frac{M}{1 + it}"
                    elif "Tasa" in var_calc: res = ((val_M / val_C) - 1) / val_t_raw; form_tex = r"i = \frac{\frac{M}{C} - 1}{t}"
                    elif "Tiempo" in var_calc: res = ((val_M / val_C) - 1) / val_i; form_tex = r"t = \frac{\frac{M}{C} - 1}{i}"
                
                # INTERÉS COMPUESTO
                elif regimen == "Interés Compuesto":
                    if "Monto" in var_calc: res = val_C * (1 + val_i)**val_t_efectivo; form_tex = r"M = C(1 + i)^t"
                    elif "Capital" in var_calc: res = val_M / (1 + val_i)**val_t_efectivo; form_tex = r"C = \frac{M}{(1 + i)^t}"
                    elif "Tasa" in var_calc: res = (val_M / val_C)**(1 / val_t_raw) - 1; form_tex = r"i = \left(\frac{M}{C}\right)^{\frac{1}{t}} - 1"
                    elif "Tiempo" in var_calc: res = math.log(val_M / val_C) / math.log(1 + val_i); form_tex = r"t = \frac{\ln(M/C)}{\ln(1+i)}"
                    
                # INTERÉS CONTINUO
                elif regimen == "Interés Continuo":
                    if "Monto" in var_calc: res = val_C * math.exp(val_i * val_t_efectivo); form_tex = r"M = Ce^{it}"
                    elif "Capital" in var_calc: res = val_M * math.exp(-val_i * val_t_efectivo); form_tex = r"C = Me^{-it}"
                    elif "Tasa" in var_calc: res = math.log(val_M / val_C) / val_t_raw; form_tex = r"i = \frac{\ln(M/C)}{t}"
                    elif "Tiempo" in var_calc: res = math.log(val_M / val_C) / val_i; form_tex = r"t = \frac{\ln(M/C)}{i}"

                # DESCUENTO BANCARIO
                elif regimen == "Descuento Bancario":
                    if "Nominal" in var_calc: res = val_C / (1 - val_i * val_t_efectivo); form_tex = r"M = \frac{C}{1 - dt}"
                    elif "Efectivo" in var_calc: res = val_M * (1 - val_i * val_t_efectivo); form_tex = r"C = M(1 - dt)"
                    elif "Tasa" in var_calc: res = (1 - (val_C / val_M)) / val_t_raw; form_tex = r"d = \frac{1 - \frac{C}{M}}{t}"
                    elif "Tiempo" in var_calc: res = (1 - (val_C / val_M)) / val_i; form_tex = r"t = \frac{1 - \frac{C}{M}}{d}"

                st.success("Cálculo algebraico completado.")
                col_rm, col_rf = st.columns([1, 2])
                with col_rm:
                    if "Tasa" in var_calc: st.metric(var_calc, f"{res*100:,.4f} %")
                    elif "Tiempo" in var_calc: st.metric(var_calc, f"{res:,.4f} {unidad_i.lower()}")
                    else: st.metric(var_calc, f"${res:,.2f}")
                with col_rf:
                    st.write("**Fórmula aplicada:**")
                    st.latex(form_tex)
                    
                # Guardado inteligente y personalizado
                if "Tasa" not in var_calc and "Tiempo" not in var_calc:
                    tipo_corto = regimen.replace("Interés ", "").replace(" Bancario", "")
                    capital_graf = val_C if "Capital" not in var_calc and "Efectivo" not in var_calc else res
                    
                    nombre_auto = f"[{tipo_corto}] ${capital_graf:,.0f} al {val_i_porc}%"
                    nombre_final = nom_custom.strip() if nom_custom.strip() else nombre_auto
                    
                    st.session_state.mis_inversiones[nombre_final] = {
                        "C": capital_graf, "tipo": regimen, "i": val_i, 
                        "t_efectivo": val_t_efectivo, "unidades_t": val_t_efectivo 
                    }
                    
                # Restauración de la Tabla de Evolución
                if ("Tasa" not in var_calc) and ("Tiempo" not in var_calc) and ("Continuo" not in regimen):
                    t_iter = int(math.ceil(val_t_efectivo))
                    if t_iter <= 120:
                        with st.expander("📊 Ver tabla de evolución del escenario"):
                            M_iter = val_M if "Monto" not in var_calc and "Nominal" not in var_calc else res
                            C_iter = val_C if "Capital" not in var_calc and "Efectivo" not in var_calc else res
                            
                            tabla = []
                            saldo = C_iter
                            for k in range(1, t_iter + 1):
                                if regimen == "Interés Simple": int_gen = C_iter * val_i
                                elif regimen == "Interés Compuesto": int_gen = saldo * val_i
                                elif regimen == "Descuento Bancario": int_gen = M_iter * val_i
                                
                                saldo += int_gen
                                tabla.append({"Periodo": k, "Interés / Descuento": round(int_gen, 2), "Saldo Acumulado": round(saldo, 2)})
                            st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Tabla omitida para mantener el rendimiento (más de 120 periodos).")
            
            except ValueError:
                st.error("Error matemático. Verifique que el Capital sea menor al Monto o que los datos no generen logaritmos negativos.")
            except ZeroDivisionError:
                st.error("Error: División por cero.")

        # Módulo de Graficación Comparativa
        if st.session_state.mis_inversiones:
            st.divider()
            col_tit, col_btn = st.columns([4, 1])
            with col_tit: st.write("### Comparador Gráfico de Escenarios (Homologados en periodos de Tasa)")
            with col_btn: 
                if st.button("🗑️ Limpiar Gráfica"): st.session_state.mis_inversiones.clear(); st.rerun()
            
            t_max_global = max([d['unidades_t'] for d in st.session_state.mis_inversiones.values()])
            t_vector = np.linspace(0, t_max_global, 100)
            df_graf = pd.DataFrame({"Periodos Base": t_vector}).set_index("Periodos Base")
            
            for nombre, d in st.session_state.mis_inversiones.items():
                if d['tipo'] == "Interés Simple": curva = d['C'] * (1 + d['i'] * t_vector)
                elif d['tipo'] == "Interés Continuo": curva = d['C'] * np.exp(d['i'] * t_vector)
                elif d['tipo'] == "Interés Compuesto": curva = d['C'] * (1 + d['i'])**t_vector
                elif d['tipo'] == "Descuento Bancario": 
                    curva = d['C'] / (1 - d['i'] * t_vector)
                    curva = np.where(1 - d['i'] * t_vector <= 0, np.nan, curva)
                    
                df_graf[nombre] = curva
                
            st.line_chart(df_graf)

# ==============================================================================
# PESTAÑA 2: TASAS EQUIVALENTES E INFLACIÓN (Didáctico)
# ==============================================================================
with tab_tasas:
    st.subheader("Conversor Universal de Tasas Equivalentes")
    st.markdown("💡 *Dos tasas son equivalentes si, al aplicarse al mismo capital durante el mismo tiempo, generan el mismo interés. Complete la frase para convertir su tasa:*")
    
    with st.form("form_conversor_tasas"):
        # Interfaz de lectura natural
        st.write("### 🔹 Tasa de Origen (La que tienes)")
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            val_origen = st.number_input("1. Tengo un porcentaje del:", value=18.0, step=0.5, format="%.4f") / 100
        with c2:
            tipo_origen = st.selectbox("2. Que es una tasa de tipo:", 
                                       ["Nominal (Se capitaliza por partes)", "Efectiva (Se aplica directa)"])
        with c3:
            frec_origen = st.selectbox("3. Con una frecuencia:", list(frecuencias_m.keys()), index=1)
            
        st.write("### 🔸 Tasa Destino (La que buscas)")
        c4, c5 = st.columns([1.5, 1.5])
        with c4:
            tipo_destino = st.selectbox("4. Quiero convertirla a tipo:", 
                                        ["Nominal (Se capitaliza por partes)", "Efectiva (Se aplica directa)"])
        with c5:
            frec_destino = st.selectbox("5. Para una nueva frecuencia:", list(frecuencias_m.keys()), index=3)
            
        submit_tasas = st.form_submit_button("🔄 Calcular Equivalencia")
        
    if submit_tasas:
        m1 = frecuencias_m[frec_origen]
        m2 = frecuencias_m[frec_destino]
        
        # PASO 1: Puente Universal -> Convertir el Origen a Tasa Efectiva Anual (TEA)
        if "Nominal" in tipo_origen:
            tea_puente = (1 + val_origen / m1)**m1 - 1
            tex_origen = r"\frac{j_1}{m_1}"
            var_origen = "j_1"
        else:
            tea_puente = (1 + val_origen)**m1 - 1
            tex_origen = r"i_1"
            var_origen = "i_1"
            
        # PASO 2: Convertir la TEA a la Tasa Destino
        if "Nominal" in tipo_destino:
            tasa_final = m2 * ((1 + tea_puente)**(1 / m2) - 1)
            formula_tex = rf"j_2 = m_2 \left[ \left(1 + {tex_origen}\right)^{{\frac{{m_1}}{{m_2}}}} - 1 \right]"
            etiqueta_res = f"Tasa Nominal capitalizable {frec_destino.lower()}"
            explicacion = f"Significa que la tasa anual publicada será del **{tasa_final*100:,.4f}%**, pero el banco te aplicará un **{(tasa_final/m2)*100:,.4f}%** real cada {frec_destino.replace('al', '').replace('a', 'o').lower()}."
        else:
            tasa_final = (1 + tea_puente)**(1 / m2) - 1
            formula_tex = rf"i_2 = \left(1 + {tex_origen}\right)^{{\frac{{m_1}}{{m_2}}}} - 1"
            etiqueta_res = f"Tasa Efectiva {frec_destino.lower()}"
            explicacion = f"Significa que tu dinero crecerá un **{tasa_final*100:,.4f}%** real y directo cada {frec_destino.replace('al', '').replace('a', 'o').lower()}."

        # Despliegue de resultados
        st.success("¡Equivalencia calculada perfectamente!")
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            st.metric(etiqueta_res, f"{tasa_final*100:,.4f} %")
            st.write(explicacion)
        with col_r2:
            st.write("**Fórmula Matemática aplicada:**")
            st.latex(formula_tex)
            st.caption(f"*Nota: La Tasa Efectiva Anual (TEA) real de esta operación es de **{tea_puente*100:,.4f}%**.*")

    st.divider()
    
    # Mantenemos las funcionalidades de Fisher y Descuento intactas pero mejor presentadas
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### 📉 Tasa de Interés vs Tasa de Descuento")
        st.info("Útil para instrumentos que se cobran por adelantado (ej. CETES).")
        modo_int_desc = st.radio("Convertir:", ["De Interés (i) a Descuento (d)", "De Descuento (d) a Interés (i)"], horizontal=True)
        
        c_i1, c_i2 = st.columns(2)
        if "Interés" in modo_int_desc.split(" a ")[0]:
            with c_i1: tasa_i = st.number_input("Tasa Vencida ($i$) en %:", value=10.0) / 100
            with c_i2:
                if st.button("Calcular Descuento (d)"):
                    st.metric("Tasa de Descuento ($d$)", f"{(tasa_i / (1 + tasa_i))*100:,.4f} %")
                    st.latex(r"d = \frac{i}{1+i}")
        else:
            with c_i1: tasa_d2 = st.number_input("Tasa Anticipada ($d$) en %:", value=9.09) / 100
            with c_i2:
                if st.button("Calcular Interés (i)"):
                    if tasa_d2 >= 1: st.error("El descuento no puede ser del 100%.")
                    else:
                        st.metric("Tasa de Interés ($i$)", f"{(tasa_d2 / (1 - tasa_d2))*100:,.4f} %")
                        st.latex(r"i = \frac{d}{1-d}")

    with col_t2:
        st.markdown("### 🛒 Ecuación de Fisher (Inflación)")
        st.info("Descubre cuánto gana realmente tu dinero descontando la inflación.")
        modo_fisher = st.radio("Despejar:", ["Tasa Real ($r$)", "Tasa Aparente ($i$)"], horizontal=True)
        
        c_f1, c_f2 = st.columns(2)
        if modo_fisher == "Tasa Real ($r$)":
            with c_f1: 
                i_aparente = st.number_input("Tasa que paga el banco ($i$) %:", value=10.0) / 100
                inf = st.number_input("Inflación ($\pi$) en %:", value=4.5) / 100
            with c_f2:
                st.write("")
                if st.button("Calcular Tasa Real"):
                    r_real = (i_aparente - inf) / (1 + inf)
                    st.metric("Tasa Real ($r$)", f"{r_real*100:,.4f} %")
                    st.latex(r"r = \frac{i - \pi}{1 + \pi}")
        else:
            with c_f1:
                r_obj = st.number_input("Ganancia Real que deseas ($r$) %:", value=5.0) / 100
                inf_esp = st.number_input("Inflación Esperada ($\pi$) %:", value=4.5) / 100
            with c_f2:
                st.write("")
                if st.button("Calcular Tasa Aparente"):
                    i_req = r_obj + inf_esp + (r_obj * inf_esp)
                    st.metric("Tasa que debes buscar ($i$)", f"{i_req*100:,.4f} %")
                    st.latex(r"i = r + \pi + (r \cdot \pi)")

# ==============================================================================
# PESTAÑA 3: FECHAS ACTUARIALES
# ==============================================================================
with tab_fechas:
    st.subheader("Cálculo de Plazos y Fracciones de Año")
    c_f1, c_f2 = st.columns(2)
    with c_f1: fecha_inicio = st.date_input("Fecha Inicial:", value=date(2026, 1, 1))
    with c_f2: fecha_fin = st.date_input("Fecha Final:", value=date(2026, 12, 31))
    
    if fecha_inicio > fecha_fin: st.error("La Fecha Inicial debe ser menor o igual a la Fecha Final.")
    else:
        dias_exactos = (fecha_fin - fecha_inicio).days
        dias_360 = (fecha_fin.year - fecha_inicio.year) * 360 + (fecha_fin.month - fecha_inicio.month) * 30 + (fecha_fin.day - fecha_inicio.day)
        
        st.write("")
        col_res_f1, col_res_f2 = st.columns(2)
        with col_res_f1:
            st.metric("Días Exactos (Actual/Actual)", dias_exactos)
            st.caption(f"Fracción de año (Base 365): **{dias_exactos/365:,.6f}**")
        with col_res_f2:
            st.metric("Días Comerciales (Método 30/360)", dias_360)
            st.caption(f"Fracción de año (Base 360): **{dias_360/360:,.6f}**")

# ==============================================================================
# PESTAÑA 4: ANUALIDADES Y TABLAS DE AMORTIZACIÓN
# ==============================================================================
with tab_anualidades:
    st.subheader("Valuación de Flujos Constantes (Anualidades Ciertas)")
    
    col_ta, col_va = st.columns(2)
    with col_ta:
        tipo_anualidad = st.radio("Modalidad de Pago:", ["Vencida (Ordinaria)", "Anticipada"], horizontal=True)
    with col_va:
        var_anualidad = st.selectbox("Calcular:", ["Valor Presente (VP)", "Monto Futuro (M)", "Renta Periódica (R)", "Número de Pagos (n)"])

    st.divider()
    with st.form("form_anualidades"):
        ca1, ca2, ca3 = st.columns(3)
        
        if "Valor Presente" not in var_anualidad and "Monto" not in var_anualidad:
            with ca1: val_VP_M = st.number_input("Valor Presente o Monto Base:", min_value=0.01, value=10000.0, step=1000.0)
            es_base_VP = st.checkbox("¿El monto anterior es Valor Presente? (Desmárquelo si es Futuro)", value=True)
            
        if "Renta" not in var_anualidad:
            with ca1 if ("Valor" in var_anualidad or "Monto" in var_anualidad) else ca2:
                val_R = st.number_input("Renta o Pago Periódico (R):", min_value=0.01, value=1000.0, step=100.0)
                
        with ca2 if "Renta" not in var_anualidad else ca3: 
            val_i_an = st.number_input("Tasa de interés por periodo (%)", value=5.0) / 100
            
        if "Número" not in var_anualidad:
            with ca3: val_n_an = st.number_input("Número de periodos (n):", min_value=1, value=12, step=1)
            
        btn_anualidad = st.form_submit_button("Ejecutar Valuación")

    if btn_anualidad:
        res_an = 0.0
        try:
            if val_i_an == 0: st.warning("Con tasa 0%, las anualidades colapsan a simple aritmética (VP = R * n).")
            else:
                f_vencida = (1 - (1 + val_i_an)**(-val_n_an if 'val_n_an' in locals() else 0)) / val_i_an
                f_monto = ((1 + val_i_an)**(val_n_an if 'val_n_an' in locals() else 0) - 1) / val_i_an
                factor_anticipo = (1 + val_i_an) if tipo_anualidad == "Anticipada" else 1

                if var_anualidad == "Valor Presente (VP)":
                    res_an = val_R * f_vencida * factor_anticipo
                    st.latex(r"VP = R \left[ \frac{1 - (1+i)^{-n}}{i} \right]" + (r"(1+i)" if factor_anticipo != 1 else ""))
                    
                elif var_anualidad == "Monto Futuro (M)":
                    res_an = val_R * f_monto * factor_anticipo
                    st.latex(r"M = R \left[ \frac{(1+i)^n - 1}{i} \right]" + (r"(1+i)" if factor_anticipo != 1 else ""))
                    
                elif var_anualidad == "Renta Periódica (R)":
                    if es_base_VP: res_an = val_VP_M / (f_vencida * factor_anticipo)
                    else: res_an = val_VP_M / (f_monto * factor_anticipo)
                    
                elif var_anualidad == "Número de Pagos (n)":
                    if es_base_VP:
                        num = 1 - (val_VP_M * val_i_an) / (val_R * factor_anticipo)
                        if num <= 0: raise ValueError("El pago no cubre los intereses. La deuda crece infinitamente.")
                        res_an = -math.log(num) / math.log(1 + val_i_an)
                    else:
                        num = 1 + (val_VP_M * val_i_an) / (val_R * factor_anticipo)
                        res_an = math.log(num) / math.log(1 + val_i_an)

                st.metric(f"Resultado: {var_anualidad}", f"{res_an:,.4f}" if "Número" in var_anualidad else f"${res_an:,.2f}")

                # Generador de Tabla de Amortización (Solo aplica para Valor Presente)
                es_valido_amort = (var_anualidad == "Valor Presente (VP)") or (var_anualidad != "Valor Presente (VP)" and es_base_VP if 'es_base_VP' in locals() else False)
                if es_valido_amort and ('val_n_an' in locals() or 'res_an' in locals()):
                    st.divider()
                    st.write("### Tabla de Amortización Formal")
                    
                    VP_inicial = res_an if var_anualidad == "Valor Presente (VP)" else val_VP_M
                    R_fijo = res_an if var_anualidad == "Renta Periódica (R)" else val_R
                    n_redondeado = int(math.ceil(res_an)) if var_anualidad == "Número de Pagos (n)" else val_n_an
                    
                    if n_redondeado <= 120:
                        saldo_vivo = VP_inicial
                        tabla_amort = []
                        
                        if tipo_anualidad == "Anticipada":
                            tabla_amort.append({"Periodo": 0, "Pago": round(R_fijo, 2), "Interés": 0.0, "Amortizado": round(R_fijo, 2), "Saldo": round(saldo_vivo - R_fijo, 2)})
                            saldo_vivo -= R_fijo
                            rango_pagos = range(1, n_redondeado)
                        else:
                            tabla_amort.append({"Periodo": 0, "Pago": 0.0, "Interés": 0.0, "Amortizado": 0.0, "Saldo": round(saldo_vivo, 2)})
                            rango_pagos = range(1, n_redondeado + 1)
                            
                        for p in rango_pagos:
                            int_gen = saldo_vivo * val_i_an
                            if p == n_redondeado or (tipo_anualidad == "Anticipada" and p == n_redondeado - 1):
                                R_pago = saldo_vivo + int_gen
                            else:
                                R_pago = R_fijo
                                
                            amort_gen = R_pago - int_gen
                            saldo_vivo -= amort_gen
                            tabla_amort.append({
                                "Periodo": p, "Pago": round(R_pago, 2), 
                                "Interés": round(int_gen, 2), "Amortizado": round(amort_gen, 2), "Saldo": round(abs(saldo_vivo), 2)
                            })
                            
                        st.dataframe(pd.DataFrame(tabla_amort), use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Tabla de {n_redondeado} periodos omitida para evitar saturar el navegador.")
        
        except ValueError as ve:
            st.error(f"Error Matemático: {ve}")
