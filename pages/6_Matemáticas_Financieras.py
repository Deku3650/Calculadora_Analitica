import streamlit as st
import math
import numpy as np
import pandas as pd
from datetime import date

st.set_page_config(page_title="Matemáticas Financieras", layout="wide")

if 'mis_inversiones' not in st.session_state:
    st.session_state.mis_inversiones = {}

st.title("📈 Módulo de Matemáticas Financieras")
st.markdown("Calculadora universal, tablas de amortización, tasas equivalentes y laboratorio de curvas.")

# Diccionario interno para capitalizaciones (m)
frecuencias_m = {
    "Anual": 1, "Semestral": 2, "Cuatrimestral": 3, "Trimestral": 4, 
    "Bimestral": 6, "Mensual": 12, "Quincenal": 24, "Semanal": 52, "Diaria": 360
}

tab_universal, tab_lab, tab_tasas, tab_fechas, tab_anualidades = st.tabs([
    "1. Calculadora Universal (Despejes)", 
    "2. Laboratorio de Curvas", 
    "3. Tasas e Inflación", 
    "4. Fechas Actuariales",
    "5. Anualidades y Amortización"
])

# ==============================================================================
# PESTAÑA 1: CALCULADORA UNIVERSAL (El regreso de los despejes completos)
# ==============================================================================
with tab_universal:
    st.subheader("Valor del Dinero en el Tiempo")
    
    col_reg, col_var = st.columns(2)
    with col_reg:
        regimen = st.radio("Régimen Financiero:", ["Interés Simple", "Interés Compuesto", "Interés Continuo", "Descuento Bancario (Simple)"], horizontal=True)
    with col_var:
        # Si es descuento, cambiamos C por VP (Valor Presente o Efectivo) y M por VN (Valor Nominal)
        if regimen == "Descuento Bancario (Simple)":
            opciones_calc = ["Valor Nominal (VN / M)", "Valor Efectivo (VE / C)", "Tasa de Descuento (d)", "Tiempo (t)"]
        else:
            opciones_calc = ["Monto Final (M)", "Capital Inicial (C)", "Tasa de Interés (i)", "Tiempo (t)"]
        var_calc = st.selectbox("Variable a despejar:", opciones_calc)
        
    st.divider()
    
    with st.form("form_universal"):
        c1, c2, c3 = st.columns(3)
        
        # Inputs dinámicos
        if "Monto" not in var_calc and "Nominal" not in var_calc:
            with c1: val_M = st.number_input("Monto / Valor Nominal (M):", min_value=0.01, value=1500.0, step=100.0)
        if "Capital" not in var_calc and "Efectivo" not in var_calc:
            with c1 if ("Monto" in var_calc or "Nominal" in var_calc) else c2: 
                val_C = st.number_input("Capital / Valor Efectivo (C):", min_value=0.01, value=1000.0, step=100.0)
        if "Tasa" not in var_calc:
            col_tasa = c2 if ("Monto" in var_calc or "Capital" in var_calc or "Nominal" in var_calc or "Efectivo" in var_calc) else c3
            with col_tasa: 
                val_i_porc = st.number_input("Tasa (i o d) en %:", value=10.0, step=0.5)
                val_i = val_i_porc / 100
        if "Tiempo" not in var_calc:
            with c3: val_t = st.number_input("Tiempo (t):", min_value=0.01, value=1.0, step=0.25)
            
        submit_uni = st.form_submit_button("Calcular")
        
    if submit_uni:
        res = 0.0
        form_tex = ""
        try:
            # 1. INTERÉS SIMPLE
            if regimen == "Interés Simple":
                if "Monto" in var_calc: res = val_C * (1 + val_i * val_t); form_tex = r"M = C(1 + it)"
                elif "Capital" in var_calc: res = val_M / (1 + val_i * val_t); form_tex = r"C = \frac{M}{1 + it}"
                elif "Tasa" in var_calc: res = ((val_M / val_C) - 1) / val_t; form_tex = r"i = \frac{\frac{M}{C} - 1}{t}"
                elif "Tiempo" in var_calc: res = ((val_M / val_C) - 1) / val_i; form_tex = r"t = \frac{\frac{M}{C} - 1}{i}"
            
            # 2. INTERÉS COMPUESTO
            elif regimen == "Interés Compuesto":
                if "Monto" in var_calc: res = val_C * (1 + val_i)**val_t; form_tex = r"M = C(1 + i)^t"
                elif "Capital" in var_calc: res = val_M / (1 + val_i)**val_t; form_tex = r"C = \frac{M}{(1 + i)^t}"
                elif "Tasa" in var_calc: res = (val_M / val_C)**(1 / val_t) - 1; form_tex = r"i = \left(\frac{M}{C}\right)^{\frac{1}{t}} - 1"
                elif "Tiempo" in var_calc: res = math.log(val_M / val_C) / math.log(1 + val_i); form_tex = r"t = \frac{\ln(M/C)}{\ln(1+i)}"
                
            # 3. INTERÉS CONTINUO
            elif regimen == "Interés Continuo":
                if "Monto" in var_calc: res = val_C * math.exp(val_i * val_t); form_tex = r"M = Ce^{it}"
                elif "Capital" in var_calc: res = val_M * math.exp(-val_i * val_t); form_tex = r"C = Me^{-it}"
                elif "Tasa" in var_calc: res = math.log(val_M / val_C) / val_t; form_tex = r"i = \frac{\ln(M/C)}{t}"
                elif "Tiempo" in var_calc: res = math.log(val_M / val_C) / val_i; form_tex = r"t = \frac{\ln(M/C)}{i}"

            # 4. DESCUENTO BANCARIO
            elif regimen == "Descuento Bancario (Simple)":
                if "Nominal" in var_calc: res = val_C / (1 - val_i * val_t); form_tex = r"M = \frac{C}{1 - dt}"
                elif "Efectivo" in var_calc: res = val_M * (1 - val_i * val_t); form_tex = r"C = M(1 - dt)"
                elif "Tasa" in var_calc: res = (1 - (val_C / val_M)) / val_t; form_tex = r"d = \frac{1 - \frac{C}{M}}{t}"
                elif "Tiempo" in var_calc: res = (1 - (val_C / val_M)) / val_i; form_tex = r"t = \frac{1 - \frac{C}{M}}{d}"

            st.success("Cálculo algebraico completado.")
            col_rm, col_rf = st.columns([1, 2])
            with col_rm:
                if "Tasa" in var_calc: st.metric(var_calc, f"{res*100:,.4f} %")
                elif "Tiempo" in var_calc: st.metric(var_calc, f"{res:,.4f} periodos")
                else: st.metric(var_calc, f"${res:,.2f}")
            with col_rf:
                st.write("**Fórmula aplicada:**")
                st.latex(form_tex)

            # Mini-tabla de comprobación dinámica
            if ("Tasa" not in var_calc) and ("Tiempo" not in var_calc) and ("Continuo" not in regimen) and (val_t if 'val_t' in locals() else res) <= 120:
                with st.expander("Ver tabla de evolución del escenario"):
                    t_iter = int(val_t if "Tiempo" not in var_calc else res)
                    M_iter = val_M if "Monto" not in var_calc and "Nominal" not in var_calc else res
                    C_iter = val_C if "Capital" not in var_calc and "Efectivo" not in var_calc else res
                    i_iter = val_i if "Tasa" not in var_calc else res
                    
                    tabla = []
                    saldo = C_iter
                    for k in range(1, t_iter + 1):
                        if regimen == "Interés Simple": int_gen = C_iter * i_iter; saldo += int_gen
                        elif regimen == "Interés Compuesto": int_gen = saldo * i_iter; saldo += int_gen
                        elif regimen == "Descuento Bancario (Simple)": int_gen = M_iter * i_iter; saldo += int_gen
                        tabla.append({"Periodo": k, "Interés / Descuento": round(int_gen, 2), "Saldo": round(saldo, 2)})
                    st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)

        except ValueError:
            st.error("Error matemático de dominio (ej. Logaritmo de un número negativo). Verifique que el Capital sea menor al Monto.")
        except ZeroDivisionError:
            st.error("Error: División por cero.")

# ==============================================================================
# PESTAÑA 2: LABORATORIO DIDÁCTICO (Curvas de crecimiento)
# ==============================================================================
with tab_lab:
    st.subheader("Comparador Gráfico de Escenarios Financieros")
    st.info("Guarde diferentes configuraciones de inversión para visualizar el cruce de curvas (Simple vs Compuesto vs Continuo).")
    
    with st.form("form_guardar_escenario"):
        col_c, col_tasa, col_frec, col_t = st.columns(4)
        with col_c:
            tipo_int_lab = st.selectbox("Régimen:", ["Simple", "Compuesto", "Continuo"])
            C_lab = st.number_input("Capital Inicial ($):", min_value=0.01, value=1000.0, step=100.0, key="lab_C")
        with col_tasa:
            tasa_lab = st.number_input("Tasa Nominal (%):", value=12.0, step=0.5, key="lab_tasa")
        with col_frec:
            frec_str = st.selectbox("Capitalización:", ["Anual", "Semestral", "Trimestral", "Bimestral", "Mensual", "Diaria"])
            m_lab = frecuencias_m.get(frec_str, 1)
        with col_t:
            t_lab = st.number_input("Horizonte (Años):", min_value=0.1, value=10.0, step=1.0, key="lab_t")
            
        c_nom, c_btn = st.columns([3, 1])
        with c_nom: nom_escenario = st.text_input("Nombre de la curva:", value=f"{tipo_int_lab} al {tasa_lab}% {frec_str}")
        with c_btn: 
            st.write("")
            if st.form_submit_button("💾 Guardar y Graficar"):
                st.session_state.mis_inversiones[nom_escenario] = {
                    "C": C_lab, "tipo": tipo_int_lab, "i": tasa_lab/100, "m": m_lab, "t": t_lab
                }
                st.rerun()
                
    if st.session_state.mis_inversiones:
        t_max = max([d['t'] for d in st.session_state.mis_inversiones.values()])
        t_vector = np.linspace(0, t_max, 100)
        df_graf = pd.DataFrame({"Años": t_vector}).set_index("Años")
        
        for nombre, d in st.session_state.mis_inversiones.items():
            if d['tipo'] == "Simple": curva = d['C'] * (1 + d['i'] * t_vector)
            elif d['tipo'] == "Continuo": curva = d['C'] * np.exp(d['i'] * t_vector)
            else: curva = d['C'] * (1 + d['i']/d['m'])**(d['m'] * t_vector)
            df_graf[nombre] = curva
            
        st.line_chart(df_graf)
        
        if st.button("🗑️ Limpiar Gráfica"):
            st.session_state.mis_inversiones.clear(); st.rerun()

# ==============================================================================
# PESTAÑA 3: TASAS EQUIVALENTES E INFLACIÓN (Efecto Fisher)
# ==============================================================================
with tab_tasas:
    st.subheader("Análisis de Tasas de Rendimiento")
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**1. Tasa Efectiva $\\leftrightarrow$ Nominal**")
        modo_nom_efec = st.radio("Conversión:", ["Nominal a Efectiva", "Efectiva a Nominal"], horizontal=True)
        m_cap = st.number_input("Capitalizaciones por año ($m$):", min_value=1, value=12)
        
        if modo_nom_efec == "Nominal a Efectiva":
            j_tasa = st.number_input("Tasa Nominal ($j$) en %:", value=12.0) / 100
            if st.button("Calcular Tasa Efectiva ($i$)"):
                i_efec = (1 + j_tasa / m_cap)**m_cap - 1
                st.latex(r"i = \left(1 + \frac{j}{m}\right)^m - 1")
                st.metric("Tasa Efectiva Anual ($i$)", f"{i_efec*100:,.4f} %")
        else:
            i_tasa = st.number_input("Tasa Efectiva ($i$) en %:", value=12.68) / 100
            if st.button("Calcular Tasa Nominal ($j$)"):
                j_nom = m_cap * ((1 + i_tasa)**(1 / m_cap) - 1)
                st.latex(r"j = m \left[ (1 + i)^{\frac{1}{m}} - 1 \right]")
                st.metric("Tasa Nominal Anual ($j$)", f"{j_nom*100:,.4f} %")

    with col_t2:
        st.markdown("**2. Ecuación de Fisher (Tasa Real vs Inflación)**")
        st.info("💡 Determina la pérdida de poder adquisitivo descontando la inflación ($\pi$).")
        modo_fisher = st.radio("Despejar:", ["Tasa Real ($r$)", "Tasa Aparente ($i$)"], horizontal=True)
        
        if modo_fisher == "Tasa Real ($r$)":
            i_aparente = st.number_input("Tasa de Inversión Aparente ($i$) en %:", value=10.0) / 100
            inf = st.number_input("Inflación del periodo ($\pi$) en %:", value=4.5) / 100
            if st.button("Calcular Tasa Real"):
                r_real = (i_aparente - inf) / (1 + inf)
                st.latex(r"r = \frac{i - \pi}{1 + \pi}")
                st.metric("Tasa Real Neta ($r$)", f"{r_real*100:,.4f} %", delta=f"{r_real*100 - i_aparente*100:,.2f}% vs Aparente")
        else:
            r_obj = st.number_input("Tasa Real Objetivo ($r$) en %:", value=5.0) / 100
            inf_esp = st.number_input("Inflación Esperada ($\pi$) en %:", value=4.5) / 100
            if st.button("Calcular Tasa Aparente"):
                i_req = r_obj + inf_esp + (r_obj * inf_esp)
                st.latex(r"i = r + \pi + (r \cdot \pi)")
                st.metric("Tasa Aparente Requerida ($i$)", f"{i_req*100:,.4f} %")

# ==============================================================================
# PESTAÑA 4: FECHAS ACTUARIALES
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
# PESTAÑA 5: ANUALIDADES Y TABLAS DE AMORTIZACIÓN
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
                        
                        # Manejo especial para el periodo 0 si es anticipada
                        if tipo_anualidad == "Anticipada":
                            tabla_amort.append({"Periodo": 0, "Pago": round(R_fijo, 2), "Interés": 0.0, "Amortizado": round(R_fijo, 2), "Saldo": round(saldo_vivo - R_fijo, 2)})
                            saldo_vivo -= R_fijo
                            rango_pagos = range(1, n_redondeado)
                        else:
                            tabla_amort.append({"Periodo": 0, "Pago": 0.0, "Interés": 0.0, "Amortizado": 0.0, "Saldo": round(saldo_vivo, 2)})
                            rango_pagos = range(1, n_redondeado + 1)
                            
                        for p in rango_pagos:
                            int_gen = saldo_vivo * val_i_an
                            # Ajuste para el último pago (redondeo de centavos)
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
