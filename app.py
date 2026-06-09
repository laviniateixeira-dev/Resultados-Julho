import streamlit as st
import pandas as pd
import requests
import io

# Importando os arquivos de abas
import aba_resultados
import aba_regionais  # Nova aba conectada
import aba_antecedencia
import aba_historico

# ==========================================
# CONFIGURAÇÕES DO FERIADO E LINKS
# ==========================================
feriado_atual = "julho_2026"

# DATAS ÂNCORA PARA A ABA DE RESULTADOS
data_ancora_ida = "2026-07-03"    # Sexta-feira
data_ancora_volta = "2026-07-26"  # Domingo

# Nome exato do repositório onde os dados de Julho foram salvos
NOME_REPO = "Resultados-Julho"

# LINKS DO GITHUB PADRONIZADOS
GITHUB_RAW_CURVA = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/curva_{feriado_atual}.csv"
GITHUB_RAW_GERAL = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_geral_{feriado_atual}.csv"
GITHUB_RAW_DIA = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_dia_{feriado_atual}.csv"
GITHUB_RAW_ROTA = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_rota_antecedencia_{feriado_atual}.csv"

# LINKS REGIONAIS DO SEU DATABRICKS
GITHUB_RAW_REG_GERAL = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_regional_geral_{feriado_atual}.csv"
GITHUB_RAW_REG_DIA = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_regional_dia_{feriado_atual}.csv"
GITHUB_RAW_REG_ROTA = f"https://raw.githubusercontent.com/laviniateixeira-dev/{NOME_REPO}/main/data/resultados_regional_rota_{feriado_atual}.csv"
# ==========================================

st.set_page_config(
    page_title="Pricing · Julho", # Atualizei o título da aba do navegador também!
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA CUSTOMIZADA: PRETO, GRAFITE & ROSA BUSER ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {
  --bg-page:   #0D0D0D; 
  --bg-card:   #171717; 
  --ink:       #FFFFFF; 
  --ink-muted: #999999; 
  --buser:     #FF66A3; 
  --buser-lt:  #FFB3D1; 
  --bdr:       #2A2A2A; 
}

*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], section[data-testid="stMain"] > div {
  background-color: var(--bg-page) !important; color: var(--ink) !important; font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] { background-color: var(--bg-card) !important; border-right: 1px solid var(--bdr) !important; }
.block-container { padding: 3rem 4rem !important; max-width: 100% !important; }

/* Inputs Padrão */
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background-color: #26111A !important; border: 1px solid #401B2B !important; border-radius: 4px !important; color: var(--buser) !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
  border-color: var(--buser) !important;
}

/* Abas */
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 2px solid var(--bdr) !important; gap: 20px !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { color: var(--ink-muted) !important; font-weight: 500 !important; border: none !important; border-bottom: 3px solid transparent !important; }
[data-testid="stTabs"] [aria-selected="true"][data-baseweb="tab"] { color: var(--buser) !important; border-bottom-color: var(--buser) !important; }

/* Tipografia */
.pg-header { display: flex; align-items: flex-end; justify-content: space-between; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid var(--bdr); }
.pg-eyebrow { font-size: .75rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: var(--buser); margin-bottom: 8px; }
.pg-title { font-family: 'DM Serif Display', serif; font-size: 2.5rem; font-weight: 400; line-height: 1.1; }
.section-label { font-size: .7rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 10px; margin-top: 2rem; }
.section-title { font-family: 'DM Serif Display', serif; font-size: 1.4rem; font-weight: 400; margin-bottom: 5px; }

[data-testid="stDataTable"] { border: 1px solid var(--bdr) !important; border-radius: 8px !important; overflow: hidden !important; }

/* Dropdowns abertos */
[data-baseweb="popover"] [data-baseweb="menu"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--bdr) !important;
  border-radius: 6px !important;
}
[data-baseweb="option"] { background-color: var(--bg-card) !important; font-size: .85rem !important; color: var(--ink) !important; padding: 10px 12px !important; }
[data-baseweb="option"]:hover, [aria-selected="true"][data-baseweb="option"] { background-color: #27272A !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO PADRONIZADA DE CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def load_data(url: str) -> pd.DataFrame:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [str(c).lower().strip() for c in df.columns]
        for col_date in ['data_atual', 'data_viagem', 'dt_ida', 'date_ida', f'data_{feriado_atual}']:
            if col_date in df.columns:
                df.rename(columns={col_date: 'data'}, inplace=True)
        if 'eixo_sentido' in df.columns:
            df.rename(columns={'eixo_sentido': 'sentido'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro na url: {url} | Detalhe: {e}")
        return pd.DataFrame()

# --- SIDEBAR (CONTROLE DE CACHE) ---
with st.sidebar:
    st.markdown('<div class="section-label" style="margin-top:0;">Controle de Dados</div>', unsafe_allow_html=True)
    if st.button("Atualizar Cache dos Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Carregamento das bases globais
    df_curva_raw = load_data(GITHUB_RAW_CURVA)
    df_geral_raw = load_data(GITHUB_RAW_GERAL)
    df_dia_raw = load_data(GITHUB_RAW_DIA)
    df_rota_raw = load_data(GITHUB_RAW_ROTA)
    
    # Carregamento das novas bases regionais
    df_reg_geral_raw = load_data(GITHUB_RAW_REG_GERAL)
    df_reg_dia_raw = load_data(GITHUB_RAW_REG_DIA)
    df_reg_rota_raw = load_data(GITHUB_RAW_REG_ROTA)

# --- ESTRUTURA DE ABAS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Resultados", 
    "Resultados Regionais", 
    "Acompanhamento por Antecedência", 
    "Histórico Alterações de Preço"
])

# --- RENDERIZAÇÃO DAS ABAS ---
with tab1: 
    aba_resultados.render_resultados(df_geral_raw, df_dia_raw, feriado_atual, data_ancora_ida, data_ancora_volta)

with tab2: 
    aba_regionais.render_regionais(df_reg_geral_raw, df_reg_dia_raw, df_reg_rota_raw)

with tab3: 
    aba_antecedencia.render_rota_antecedencia(df_rota_raw)

with tab4: 
    aba_historico.render_historico(df_curva_raw)
