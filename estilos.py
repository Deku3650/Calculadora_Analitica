import streamlit as st

def cargar_estilos_globales():
    """Aplica el diseño institucional de MATHESIS (Azul/Gris) a todas las páginas."""
    st.markdown("""
        <style>
        /* 0. FORZAR VARIABLES GLOBALES A TONOS AZULES */
        :root {
            --primary-color: #0284c7 !important;
            --stConfig-primaryColor: #0284c7 !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1.5rem;}
        
        /* 1. CONTENEDOR/BANNER DEL TÍTULO PRINCIPAL */
        .title-container {
            padding: 1.2rem 1.5rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.18) 0%, rgba(79, 70, 229, 0.18) 100%);
            border: 1px solid rgba(56, 189, 248, 0.35);
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.12);
        }
        
        .title-text {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -0.5px;
        }

        /* 2. ESTILIZACIÓN DE PESTAÑAS (ST.TABS) */
        div[data-baseweb="tab-list"] {
            gap: 8px !important;
        }

        button[data-baseweb="tab"] {
            border-radius: 12px 12px 0px 0px !important;
            padding: 10px 20px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            transition: all 0.25s ease-in-out !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            border-bottom: none !important;
            background: rgba(255, 255, 255, 0.02) !important;
        }
        
        /* Pestaña seleccionada / activa */
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
            border: 1px solid #38bdf8 !important;
            border-bottom: none !important;
            box-shadow: 0 -2px 10px rgba(56, 189, 248, 0.2) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span {
            color: #38bdf8 !important;
            font-weight: 800 !important;
        }

        /* Ocultar el indicador rojo por defecto */
        div[data-baseweb="tab-highlight"] {
            background-color: #38bdf8 !important;
            height: 3px !important;
        }

        /* 3. MENÚ LATERAL (SIDEBAR EN AZUL) */
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(2, 132, 199, 0.2) !important;
        }

        [data-testid="stSidebarNav"] ul li div a {
            border-radius: 12px !important;
            padding: 10px 14px !important;
            margin: 4px 8px !important;
            border: 1px solid rgba(2, 132, 199, 0.15) !important;
            transition: all 0.25s ease-in-out !important;
        }

        [data-testid="stSidebarNav"] ul li div a:hover {
            border-color: #0284c7 !important;
            background: rgba(2, 132, 199, 0.12) !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2) !important;
            transform: translateX(4px);
        }

        [data-testid="stSidebarNav"] ul li div a[aria-current="page"] {
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
            border: 1px solid #38bdf8 !important;
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
        }

        [data-testid="stSidebarNav"] ul li div a[aria-current="page"] span {
            color: #38bdf8 !important;
            font-weight: 800 !important;
        }

        /* 4. CONTENEDORES DE TARJETAS */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px !important;
            transition: all 0.25s ease-in-out !important;
            border: 1px solid rgba(2, 132, 199, 0.25) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        }
        </style>
    """, unsafe_allow_html=True)
