import streamlit as st
import pandas as pd
import openpyxl

# --- CONFIGURACIÓN DE PÁGINA (LOOK IPHONE) ---
st.set_page_config(page_title="Ruta 8087", page_icon="🚛", layout="centered")

# --- CSS AVANZADO PARA CLONAR TU DISEÑO ---
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo general gris claro como en la foto */
    .stApp {
        background-color: #f2f2f7;
    }

    /* ESTILO TARJETA DASHBOARD (Arriba) */
    .dashboard-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .big-num { font-size: 24px; font-weight: bold; color: #000; }
    .label { font-size: 11px; color: #8e8e93; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-green { color: #34c759; font-size: 24px; font-weight: bold; }
    .stat-blue { color: #007aff; font-size: 24px; font-weight: bold; }

    /* ESTILO TARJETA CLIENTE */
    div.stButton > button {
        background-color: white;
        border: none;
        border-radius: 0; /* Recto para parecer lista */
        border-bottom: 1px solid #e5e5ea;
        padding: 15px 5px;
        text-align: left;
        width: 100%;
        transition: background-color 0.2s;
    }
    div.stButton > button:active {
        background-color: #e5e5ea;
    }
    div.stButton > button p {
        font-size: 16px;
        color: #000;
        margin: 0;
    }
    
    /* Estilo para los botones de Venta (Rojo/Verde) */
    .btn-vender { border-radius: 8px !important; margin-bottom: 8px; }

    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DATOS ---
FILE_PATH = 'Copia de LISTADO ACCIONES Q1.xlsx'

@st.cache_data
def load_data():
    try:
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        sheet_found = next((k for k in all_sheets.keys() if 'BIT' in k.upper()), list(all_sheets.keys())[0])
        df = all_sheets[sheet_found]
        if 'Route' in df.columns:
            df = df[df['Route'] == 8087].copy()
        return df, sheet_found
    except:
        return pd.DataFrame(), ""

# --- GESTIÓN ESTADO ---
if 'data' not in st.session_state:
    df_loaded, sheet_name = load_data()
    st.session_state.data = df_loaded
    st.session_state.sheet_name = sheet_name
    st.session_state.original = df_loaded.copy()
    st.session_state.current_client = None

def save_data():
    """Guarda en Excel Real"""
    try:
        all_sheets = pd.read_excel(FILE_PATH, sheet_name=None, engine='openpyxl')
        df_full = all_sheets[st.session_state.sheet_name]
        df_act = st.session_state.data
        
        df_full.set_index('Customer Code', inplace=True)
        df_act.set_index('Customer Code', inplace=True)
        df_full.update(df_act)
        df_full.reset_index(inplace=True)
        df_act.reset_index(inplace=True)
        
        all_sheets[st.session_state.sheet_name] = df_full
        with pd.ExcelWriter(FILE_PATH, engine='openpyxl') as writer:
            for sheet, data in all_sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
    except:
        pass

def toggle_venta(code, col):
    idx = st.session_state.data[st.session_state.data['Customer Code'] == code].index[0]
    st.session_state.data.at[idx, col] = 1
    save_data()
    st.rerun()

def volver():
    st.session_state.current_client = None
    st.rerun()

# --- INTERFAZ PRINCIPAL ---

# 1. PANTALLA LISTADO (Como tu foto)
if st.session_state.current_client is None:
    st.markdown("### Ruta 8087")
    
    # BUSCADOR ESTILO IPHONE
    col_search, col_mic = st.columns([6, 1])
    with col_search:
        query = st.text_input("Buscar", placeholder="🔍 Buscar cliente o ID...", label_visibility="collapsed")
    with col_mic:
        st.markdown("🎙️") # Icono visual, el usuario usa el teclado

    # CÁLCULOS DASHBOARD
    df = st.session_state.data
    prod_cols = [c for c in df.columns if 'Bits' in c]
    total_refs = len(prod_cols) * len(df)
    total_vendidos = df[prod_cols].sum().sum()
    cobertura = (total_vendidos / total_refs) * 100 if total_refs > 0 else 0
    ventas_hoy = total_vendidos - st.session_state.original[prod_cols].sum().sum() # Aprox

    # DASHBOARD HTML (Igual a tu foto)
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content: space-between;">
            <div>
                <div class="big-num">{len(df)}</div>
                <div class="label">CLIENTES</div>
            </div>
            <div style="text-align:center;">
                <div class="stat-blue">{int(ventas_hoy)}</div>
                <div class="label">VENTAS HOY</div>
            </div>
        </div>
        <div style="margin-top: 15px;">
            <div class="stat-green">{int(cobertura)}%</div>
            <div class="label">COBERTURA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # FILTRADO
    if query:
        mask = df['Customer Full Name'].str.contains(query, case=False, na=False) | \
               df['Customer Code'].astype(str).str.contains(query, na=False)
        df_filtered = df[mask]
    else:
        df_filtered = df.head(50) # Cargar solo 50 para velocidad

    # LISTA DE CLIENTES
    for idx, row in df_filtered.iterrows():
        # Cálculos individuales
        hechos = row[prod_cols].sum()
        total = len(prod_cols)
        code = row['Customer Code']
        
        # Tarjeta contenedora blanca
        with st.container():
            # Usamos columnas para maquetar: Texto Izq | Progreso Der
            c1, c2 = st.columns([3, 1])
            
            with c1:
                # El botón invisible es difícil, usamos botón con nombre
                label = f"#{code}\n{row['Customer Full Name']}\n{row['Address']}"
                if st.button(label, key=code):
                    st.session_state.current_client = code
                    st.rerun()
            
            with c2:
                # Barra de progreso visual
                st.write("") # Espacio para bajar
                st.caption(f"{int(hechos)}/{total}")
                progreso = hechos / total if total > 0 else 0
                
                # Color barra según progreso
                color = "green" if progreso > 0.7 else "orange" if progreso > 0.3 else "red"
                st.progress(progreso)

# 2. PANTALLA DETALLE (Ficha Cliente)
else:
    code = st.session_state.current_client
    row = st.session_state.data[st.session_state.data['Customer Code'] == code].iloc[0]
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]

    # Cabecera con botón volver
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️"):
            volver()
    with c_title:
        st.markdown(f"**{row['Customer Full Name']}**")

    st.info(f"📍 {row['Address']} | 🆔 {code}")

    # Pestañas
    tab1, tab2 = st.tabs(["🔴 FALTAN", "✅ TIENE"])

    with tab1:
        st.write("")
        faltan = [p for p in prod_cols if row[p] == 0]
        if not faltan:
            st.success("¡Cliente Completo! 🏆")
        
        # Grid de botones
        cols = st.columns(2)
        for i, prod in enumerate(faltan):
            col_idx = i % 2
            with cols[col_idx]:
                name = prod.replace('Bits ', '').replace('0,50€', '0.5€')
                if st.button(f"🛒 {name}", key=f"v_{prod}", type="primary", use_container_width=True):
                    toggle_venta(code, prod)

    with tab2:
        st.write("")
        tiene = [p for p in prod_cols if row[p] == 1]
        for prod in tiene:
            name = prod.replace('Bits ', '')
            orig_val = st.session_state.original[st.session_state.original['Customer Code'] == code].iloc[0][prod]
            
            if orig_val == 0:
                st.markdown(f'<div style="background:#e3f2fd;padding:10px;border-radius:8px;margin-bottom:5px;color:#0d47a1"><b>🔵 {name}</b> (Vendido hoy)</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#e8f5e9;padding:10px;border-radius:8px;margin-bottom:5px;color:#1b5e20"><b>🟢 {name}</b></div>', unsafe_allow_html=True)
