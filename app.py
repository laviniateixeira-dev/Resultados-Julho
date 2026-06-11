import streamlit as st
import pandas as pd
import requests
import io
import time

# Importando os arquivos de abas
import aba_resultados
import aba_regionais  
import aba_antecedencia
import aba_historico

# ==========================================
# CONFIGURAÇÕES DO FERIADO E LINKS
# ==========================================
feriado_atual = "julho_2026"

# DATAS ÂNCORA PARA A ABA DE RESULTADOS
data_ancora_ida = "2026-07-03"    # Sexta-feira
data_ancora_volta = "2026-07-26"  # Domingo

# ==========================================
# ÚNICO CSV UNIFICADO GERADO PELO NOTEBOOK
# ==========================================
GITHUB_RAW_UNIFIED = "https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-julho/main/data/julho_2026_resultados.csv"

# ==========================================

st.set_page_config(
    page_title="Pricing · Julho", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA CUSTOMIZADA ---
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

[data-testid="stTextInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background-color: #26111A !important; border: 1px solid #401B2B !important; border-radius: 4px !important; color: var(--buser) !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
  border-color: var(--buser) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom: 2px solid var(--bdr) !important; gap: 20px !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { color: var(--ink-muted) !important; font-weight: 500 !important; border: none !important; border-bottom: 3px solid transparent !important; }
[data-testid="stTabs"] [aria-selected="true"][data-baseweb="tab"] { color: var(--buser) !important; border-bottom-color: var(--buser) !important; }

.pg-header { display: flex; align-items: flex-end; justify-content: space-between; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid var(--bdr); }
.pg-eyebrow { font-size: .75rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: var(--buser); margin-bottom: 8px; }
.pg-title { font-family: 'DM Serif Display', serif; font-size: 2.5rem; font-weight: 400; line-height: 1.1; }
.section-label { font-size: .7rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 10px; margin-top: 2rem; }
.section-title { font-family: 'DM Serif Display', serif; font-size: 1.4rem; font-weight: 400; margin-bottom: 5px; }

[data-testid="stDataTable"] { border: 1px solid var(--bdr) !important; border-radius: 8px !important; overflow: hidden !important; }

[data-baseweb="popover"] [data-baseweb="menu"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--bdr) !important;
  border-radius: 6px !important;
}
[data-baseweb="option"] { background-color: var(--bg-card) !important; font-size: .85rem !important; color: var(--ink) !important; padding: 10px 12px !important; }
[data-baseweb="option"]:hover, [aria-selected="true"][data-baseweb="option"] { background-color: #27272A !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# CARREGAMENTO E SPLIT DO CSV UNIFICADO
# ==========================================
@st.cache_data(ttl=60)
def load_unified(url: str) -> pd.DataFrame:
    """Baixa o CSV unificado gerado pelo notebook e padroniza colunas."""
    try:
        cache_buster = f"{url}?t={int(time.time())}"
        r = requests.get(cache_buster, timeout=15)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [str(c).lower().strip() for c in df.columns]
        # NOTA: Removido o renomeamento em lote aqui para não criar colunas 'data' duplicadas.
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV unificado: {e}")
        return pd.DataFrame()


def split_dataframes(df: pd.DataFrame):
    if df.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty, empty, empty

    def filtra(granularidade_val):
        return df[df.get('granularidade', pd.Series(dtype=str)) == granularidade_val].copy()

    # Filtros base
    df_geral_raw      = filtra('consolidado')
    df_dia_raw        = filtra('dia_viagem')
    df_reg_geral_raw  = filtra('regional_slot')
    df_alteracoes_raw = filtra('precificacao')

    # Correção: Curva global e regional dividem a mesma granularidade no Databricks. 
    # Precisamos separá-las olhando se a coluna "regional" está nula ou não.
    df_curvas = filtra('rota_antecedencia')
    if 'regional' in df_curvas.columns:
        df_rota_raw = df_curvas[df_curvas['regional'].isna()].copy()
        df_reg_rota_raw = df_curvas[df_curvas['regional'].notna()].copy()
    else:
        df_rota_raw = df_curvas.copy()
        df_reg_rota_raw = pd.DataFrame()

    # Aplicação dos reshapes exatos
    df_geral      = _pivot_resultado(df_geral_raw)
    df_dia        = _pivot_resultado_dia(df_dia_raw)
    df_rota       = _reshape_antecedencia(df_rota_raw)
    df_reg_geral  = _pivot_regional_geral(df_reg_geral_raw)
    df_reg_dia    = pd.DataFrame()  # não usado pelas abas
    df_reg_rota   = _reshape_regional_rota(df_reg_rota_raw)
    df_alteracoes = _reshape_alteracoes(df_alteracoes_raw)

    return df_geral, df_dia, df_rota, df_reg_geral, df_reg_dia, df_reg_rota, df_alteracoes


# ── helpers de reshape ────────────────────────────────────────────────────────

def _pivot_resultado(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    out = df[['metrica', 'valor_historico', 'valor_atual']].copy()
    out.rename(columns={'valor_historico': 'julho_2025', 'valor_atual': 'atual'}, inplace=True)
    return out


def _pivot_resultado_dia(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    cols = ['data_atual', 'metrica', 'valor_historico', 'valor_atual']
    cols_ok = [c for c in cols if c in df.columns]
    out = df[cols_ok].copy()
    out.rename(columns={
        'data_atual': 'data',
        'valor_historico': 'julho_2025',
        'valor_atual': 'atual'
    }, inplace=True)
    return out


def _reshape_antecedencia(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    col_map = {
        'data_julho_2026': 'data', # ← O Databricks exporta com este nome
        'eixo_sentido': 'sentido',
        'pax_historico': 'pax_julho25',
        'lf_historico': 'lf_julho25',
        'yield_historico': 'yield_julho25',
        'ticket_medio_historico': 'ticket_medio_julho25'
    }
    out = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return out


def _pivot_regional_geral(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    cols = ['regional', 'slot', 'metrica', 'valor_historico', 'valor_atual']
    cols_ok = [c for c in cols if c in df.columns]
    out = df[cols_ok].copy()
    out.rename(columns={'valor_historico': 'julho_2025', 'valor_atual': 'atual'}, inplace=True)
    return out


def _reshape_regional_rota(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    col_map = {
        'eixo_sentido': 'sentido'
        # Nota: 'data' já vem com o nome correto do Databricks na query_regional_rota
    }
    out = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return out


def _reshape_alteracoes(df: pd.DataFrame) -> pd.DataFrame:
    # Retorna o df puro porque a aba_historico.py já faz a inteligência de procurar
    # as colunas com os nomes nativos do Databricks ('data_atual' e 'sentido').
    return df


# ==========================================
# SIDEBAR — controle de cache + carregamento
# ==========================================
with st.sidebar:
    st.markdown('<div class="section-label" style="margin-top:0;">Controle de Dados</div>', unsafe_allow_html=True)
    if st.button("Atualizar Cache dos Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.write("Linhas carregadas:", len(df_unified))
st.write(df_unified.head())
st.write(df_unified.columns.tolist())

    (
        df_geral_raw,
        df_dia_raw,
        df_rota_raw,
        df_reg_geral_raw,
        df_reg_dia_raw,
        df_reg_rota_raw,
        df_alteracoes_raw,
    ) = split_dataframes(df_unified)


# ==========================================
# ESTRUTURA DE ABAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Resultados", 
    "Resultados Regionais", 
    "Acompanhamento por Antecedência", 
    "Histórico Alterações de Preço"
])

with tab1: 
    aba_resultados.render_resultados(df_geral_raw, df_dia_raw, feriado_atual, data_ancora_ida, data_ancora_volta)

with tab2: 
    aba_regionais.render_regionais(df_reg_geral_raw, df_reg_dia_raw, df_reg_rota_raw)

with tab3: 
    aba_antecedencia.render_rota_antecedencia(df_rota_raw)

with tab4: 
    aba_historico.render_historico(df_alteracoes_raw)
