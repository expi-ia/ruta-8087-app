import streamlit as st
import pandas as pd
import openpyxl

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ruta 8087", page_icon="🚛", layout="centered")

# --- CSS MAESTRO (PARA CLONAR TU DISEÑO) ---
st.markdown("""
    <style>
    /* 1. LIMPIEZA GENERAL */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f2f2f7; } /* Fondo Gris iPhone */
    
    /* 2. ESTILO DASHBOARD (TARJETA SUPERIOR) */
    .dashboard-card {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric-label { font-size: 10px; color: #8e8e93; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; }
    .metric-value { font-size: 28px; font-weight: 800; color: #000; margin-bottom: 5px; }
    .metric-green { color: #34c759; }
    
    /* 3. ESTILO LISTADO DE CLIENTES (TARJETAS) */
    /* Truco: Convertimos los botones normales en tarjetas con layout interno */
    div.stButton > button {
        background-color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px !important;
        text-align: left !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        margin-bottom: 8px !important;
        width: 100%;
        color: #000 !important;
        display: flex;
        flex-direction: column;
        transition: transform 0.1s;
    }
    div.stButton > button:active { transform: scale(0.98); }
    
    /* 4. ESTILO CUADRADOS DE PRODUCTOS (GRID) */
    /* Definimos clases visuales que aplicaremos con lógica */
    
    /* BOTÓN ROJO (FALTA) */
    .btn-red {
        background-color: #ff3b30; 
        color: white; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(255, 59, 48, 0.2);
        margin-bottom: 10px;
        cursor: pointer;
    }
    
    /* BOTÓN VERDE (STOCK) */
    .btn-green {
        background-color: #34c759; 
        color: white; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        font-weight: bold;
        opacity: 0.9;
        margin-bottom: 10px;
    }

    /* BOTÓN AZUL (VENDIDO HOY) */
    .btn-blue {
        background-color: #007aff; 
        color: white; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 122, 255, 0.3);
        margin-bottom: 10px;
        cursor: pointer;
    }

    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
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

if 'data' not in st.session_state:
    df_loaded, sheet_name = load_data()
    st.session_state.data = df_loaded
    st.session_state.sheet_name = sheet_name
    st.session_state.original = df_loaded.copy()
    st.session_state.current_client = None

# --- FUNCIONES ---
def save_data():
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

def toggle_producto(code, col, action):
    # Action: 'vender' (0->1), 'anular' (1->0)
    idx = st.session_state.data[st.session_state.data['Customer Code'] == code].index[0]
    
    if action == 'vender':
        st.session_state.data.at[idx, col] = 1
    elif action == 'anular':
        st.session_state.data.at[idx, col] = 0
        
    save_data()
    st.rerun()

def volver():
    st.session_state.current_client = None
    st.rerun()

# --- VISTA 1: LISTADO (HOME) ---
if st.session_state.current_client is None:
    
    # 1. BUSCADOR CON MICRO
    c_search, c_mic = st.columns([5, 1])
    with c_search:
        query = st.text_input("Buscador", placeholder="🔍 Buscar cliente, calle o ID...", label_visibility="collapsed")
    with c_mic:
        st.markdown("<div style='text-align:center; font-size:25px; margin-top:5px;'>🎙️</div>", unsafe_allow_html=True)

    # 2. DASHBOARD (TARJETA BLANCA)
    df = st.session_state.data
    prod_cols = [c for c in df.columns if 'Bits' in c]
    total_refs = len(prod_cols) * len(df)
    total_vendidos = df[prod_cols].sum().sum()
    cobertura = (total_vendidos / total_refs) * 100 if total_refs > 0 else 0
    ventas_hoy_num = total_vendidos - st.session_state.original[prod_cols].sum().sum()
    
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="display:flex; justify-content: space-between;">
            <div>
                <div class="metric-value">{len(df)}</div>
                <div class="metric-label">CLIENTES</div>
            </div>
            <div style="text-align:center;">
                <div class="metric-value" style="color:#007aff;">{int(ventas_hoy_num)}</div>
                <div class="metric-label">VENTAS HOY</div>
            </div>
        </div>
        <div style="margin-top: 20px;">
            <div class="metric-value metric-green">{int(cobertura)}%</div>
            <div class="metric-label">COBERTURA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. LISTA DE CLIENTES (TARJETAS LIMPIAS)
    if query:
        mask = df['Customer Full Name'].str.contains(query, case=False, na=False) | \
               df['Customer Code'].astype(str).str.contains(query, na=False)
        df_filtered = df[mask]
    else:
        df_filtered = df.head(50)

    for idx, row in df_filtered.iterrows():
        code = row['Customer Code']
        hechos = row[prod_cols].sum()
        total = len(prod_cols)
        
        # Truco Visual: Usamos espacios y caracteres invisibles para maquetar el botón
        # Streamlit no deja poner HTML dentro de botones, así que usamos un formato de texto ingenioso
        # Línea 1: #CODIGO (gris visualmente no se puede, pero lo ponemos pequeño)
        # Línea 2: NOMBRE
        # Línea 3: DIRECCION
        
        # BARRA DE PROGRESO TEXTUAL: ▇▇▇▇░░ 4/10
        progreso_int = int((hechos / total) * 10)
        barra = "▰" * progreso_int + "▱" * (10 - progreso_int)
        
        label = f"#{code}\n{row['Customer Full Name']}\n📍 {row['Address']}\n\n{barra}   {int(hechos)}/{total}"
        
        if st.button(label, key=code):
            st.session_state.current_client = code
            st.rerun()

# --- VISTA 2: DETALLE (CUADRADOS) ---
else:
    code = st.session_state.current_client
    row = st.session_state.data[st.session_state.data['Customer Code'] == code].iloc[0]
    prod_cols = [c for c in st.session_state.data.columns if 'Bits' in c]

    # CABECERA
    c_back, c_tit = st.columns([1, 5])
    with c_back:
        if st.button("⬅️", key="back_btn"):
            volver()
    with c_tit:
        st.markdown(f"### {row['Customer Full Name']}")
        st.caption(f"{row['Address']} | #{code}")

    st.write("---")

    # GRID DE PRODUCTOS (2 Columnas)
    cols = st.columns(2)
    
    for i, prod in enumerate(prod_cols):
        col_idx = i % 2
        with cols[col_idx]:
            # LÓGICA DE ESTADO
            val_actual = row[prod]
            val_orig = st.session_state.original[st.session_state.original['Customer Code'] == code].iloc[0][prod]
            
            name = prod.replace('Bits ', '').replace('0,50€', '0.5€')
            
            # 1. VERDE (STOCK ANTIGUO)
            if val_actual == 1 and val_orig == 1:
                # Botón visual que no hace nada (o avisa)
                st.markdown(f"""
                <div class="btn-green">
                    ✅<br>{name}<br><span style="font-size:10px">STOCK</span>
                </div>
                """, unsafe_allow_html=True)
                
            # 2. AZUL (VENDIDO HOY - CLICK PARA DESHACER)
            elif val_actual == 1 and val_orig == 0:
                # Usamos un botón transparente encima o un botón nativo Streamlit
                # Para máxima funcionalidad, usamos botón nativo con Emoji Azul
                if st.button(f"👍 {name}\nVENDIDO HOY", key=f"undo_{prod}", type="primary", use_container_width=True):
                    toggle_producto(code, prod, 'anular')
                
            # 3. ROJO (FALTA - CLICK PARA VENDER)
            else:
                # Botón Rojo (Primary en Streamlit suele ser rojo/rosa por defecto, 
                # si no, el CSS de arriba ayuda pero los botones nativos mandan)
                if st.button(f"🛒 {name}\nFALTA", key=f"sell_{prod}", type="secondary", use_container_width=True):
                    toggle_producto(code, prod, 'vender')
            
            # Espacio vertical entre filas
            st.write("")

