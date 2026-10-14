import streamlit as st


def cargar_estilos_globales():
    """Aplica el diseño institucional unificado de MATHESIS (Azul/Índigo) a todas las páginas."""
    st.markdown("""
        <style>
        /* 0. VISIBILIDAD Y VARIABLES GLOBALES DE TEMA EN AZUL */
        #MainMenu { visibility: visible !important; }
        footer { visibility: hidden; }
        .block-container { padding-top: 1.5rem; }

        :root, html, body, [data-testid="stAppViewContainer"] {
            --primary-color: #0284c7 !important;
            --stConfig-primaryColor: #0284c7 !important;
        }

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

        /* 2. ESTILIZADO GLOBAL PARA SUBTÍTULOS (H2, H3, ST.HEADER, ST.SUBHEADER) */
        .stMarkdown h2, [data-testid="stHeader"] h2 {
            color: #38bdf8 !important;
            font-size: 1.35rem !important;
            font-weight: 800 !important;
            border-bottom: 2px solid rgba(56, 189, 248, 0.3) !important;
            padding-bottom: 6px !important;
            margin-top: 1.2rem !important;
            margin-bottom: 1.0rem !important;
            letter-spacing: -0.3px !important;
        }

        .stMarkdown h3, [data-testid="stSubheader"] h3 {
            color: #38bdf8 !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            border-left: 4px solid #0284c7 !important;
            padding-left: 10px !important;
            margin-top: 1rem !important;
            margin-bottom: 0.8rem !important;
        }

        /* 3. CONTENEDORES DE TARJETAS NATIVOS */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.32) !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.08) !important;
            transition: all 0.25s ease-in-out !important;
            margin-bottom: 1rem !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(56, 189, 248, 0.65) !important;
            box-shadow: 0 6px 18px rgba(2, 132, 199, 0.16) !important;
        }

        /* 4. TÍTULOS Y SUBTÍTULOS RESALTADOS DENTRO DE TARJETAS */
        .card-header-title {
            background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
            color: #ffffff !important;
            font-size: 17px;
            font-weight: 800;
            padding: 8px 16px;
            border-radius: 10px;
            display: inline-block;
            margin-bottom: 14px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }

        .card-subheader-title {
            color: #38bdf8 !important;
            font-size: 15px;
            font-weight: 700;
            border-bottom: 2px solid rgba(56, 189, 248, 0.3);
            padding-bottom: 6px;
            margin-top: 10px;
            margin-bottom: 12px;
        }

        /* 5. DISEÑO MODERNO DE PESTAÑAS (ST.TABS) */
        [data-baseweb="tab-list"] {
            gap: 10px !important;
            background-color: rgba(2, 132, 199, 0.05) !important;
            padding: 8px 10px !important;
            border-radius: 16px !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            margin-bottom: 20px !important;
        }

        button[data-baseweb="tab"] {
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            color: #94a3b8 !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            transition: all 0.25s ease-in-out !important;
        }

        button[data-baseweb="tab"]:hover {
            color: #38bdf8 !important;
            background: rgba(2, 132, 199, 0.12) !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
            border: 1px solid #38bdf8 !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span {
            color: #ffffff !important;
            font-weight: 800 !important;
        }

        [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* 6. BARRA LATERAL UNIFICADA Y RESPONSIVA */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            width: 100% !important;
            max-width: 290px !important;
            border-right: 1px solid rgba(2, 132, 199, 0.2) !important;
        }

        @media (max-width: 768px) {
            [data-testid="stSidebar"], section[data-testid="stSidebar"] {
                max-width: 240px !important;
            }
        }

        [data-testid="stSidebarNav"] ul li div a, [data-testid="stSidebarNav"] a {
            border-radius: 12px !important;
            padding: 10px 14px !important;
            margin: 4px 8px !important;
            border: 1px solid rgba(2, 132, 199, 0.18) !important;
            background-color: rgba(2, 132, 199, 0.03) !important;
            transition: all 0.25s ease-in-out !important;
            white-space: nowrap !important;
        }

        [data-testid="stSidebarNav"] ul li div a:hover, [data-testid="stSidebarNav"] a:hover {
            border-color: #0284c7 !important;
            background: rgba(2, 132, 199, 0.12) !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2) !important;
            transform: translateX(4px);
        }

        [data-testid="stSidebarNav"] ul li div a[aria-current="page"], [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.25) 0%, rgba(79, 70, 229, 0.25) 100%) !important;
            border: 1px solid #38bdf8 !important;
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
        }

        [data-testid="stSidebarNav"] ul li div a[aria-current="page"] span, [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: #38bdf8 !important;
            font-weight: 800 !important;
            letter-spacing: 0.3px !important;
        }

        [data-testid="stSidebarNav"] ul li div a span, [data-testid="stSidebarNav"] a span {
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        /* 7. ENLACES DE PÁGINA Y TARJETAS DE INICIO */
        [data-testid="stPageLink-NavLink"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        [data-testid="stPageLink-NavLink"] p {
            color: #0284c7 !important;
            font-size: 19px !important;
            font-weight: 800 !important;
        }

        [data-testid="stPageLink-NavLink"]:hover p {
            color: #38bdf8 !important;
            text-decoration: underline !important;
        }

        .module-badge {
            background: rgba(2, 132, 199, 0.12);
            color: #0284c7;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 8px;
            border: 1px solid rgba(2, 132, 199, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            display: inline-block;
            margin-bottom: 6px;
        }

        .menu-header-container {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 25px;
            margin-bottom: 20px;
        }

        .menu-header-title {
            background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
            color: #ffffff !important;
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 1.5px;
            padding: 8px 18px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
            text-transform: uppercase;
        }

        .menu-header-line {
            flex-grow: 1;
            height: 2px;
            background: linear-gradient(90deg, rgba(2, 132, 199, 0.4), transparent);
            border-radius: 2px;
        }

        .formal-card {
            background-color: rgba(2, 132, 199, 0.05);
            border: 1px solid rgba(2, 132, 199, 0.25);
            border-left: 4px solid #0284c7;
            padding: 20px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
        }

        .formal-title {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 14px;
            letter-spacing: 0.5px;
        }

        .author-card {
            background-color: rgba(2, 132, 199, 0.03);
            border: 1px solid rgba(2, 132, 199, 0.2);
            border-radius: 8px;
            padding: 18px 20px;
            height: 100%;
        }

        .author-name {
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .author-affiliation {
            font-size: 13px;
            opacity: 0.85;
            margin-bottom: 10px;
            line-height: 1.4;
        }

        .author-email {
            font-size: 13px;
            font-family: monospace;
        }
        </style>
    """, unsafe_allow_html=True)


def encabezado_pagina(titulo: str, subtitulo: str = ""):
    """Renderiza el banner superior institucional y un subtítulo opcional."""
    st.markdown(f"""
        <div class="title-container">
            <h1 class="title-text">{titulo}</h1>
        </div>
    """, unsafe_allow_html=True)
    if subtitulo:
        st.markdown(subtitulo)


def titulo_tarjeta(texto: str):
    """Renderiza un encabezado resaltado dentro de un st.container(border=True)."""
    st.markdown(f'<div class="card-header-title">{texto}</div>', unsafe_allow_html=True)


def subtitulo_tarjeta(texto: str):
    """Renderiza un subencabezado estilizado dentro de una tarjeta."""
    st.markdown(f'<div class="card-subheader-title">{texto}</div>', unsafe_allow_html=True)
