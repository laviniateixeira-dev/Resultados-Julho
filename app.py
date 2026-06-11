import streamlit as st
import pandas as pd
import requests
import io
import time

import aba_resultados
import aba_regionais
import aba_antecedencia
import aba_historico

# ==========================================
# CONFIGURAÇÕES DO FERIADO
# ==========================================
feriado_atual = "julho_2026"
data_ancora_ida   = "2026-07-03"   # Sexta-feira
data_ancora_volta = "2026-07-26"   # Domingo

# ==========================================
# LINKS DOS 5 CSVs GERADOS PELO NOTEBOOK
# ==========================================
BASE = "https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data"
GITHUB_RAW_GERAL       = f"{BASE}/julho_2026_resultado_geral.csv"
GITHUB_RAW_DIA         = f"{BASE}/julho_2026_resultado_por_dia.csv"
GITHUB_RAW_ANTECEDENCIA= f"{BASE}/julho_2026_curva_antecedencia.csv"
GITHUB_RAW_ALTERACOES  = f"{BASE}/julho_2026_alteracoes_preco.csv"
GITHUB_RAW_REG_GERAL   = f"{BASE}/julho_2026_regional_slot.csv"

# ==========================================
# ESTILO
# ==========================================
st.set_page_config(page_title="Pricing · Julho", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');
:root { --bg-page:#0D0D0D; --bg-card:#171717; --ink:#FFFFFF; --ink-muted:#999999; --buser:#FF66A3; --buser-lt:#FFB3D1; --bdr:#2A2A2A; }
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html,body,[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],section[data-testid="stMain"]>div {
  background-color:var(--bg-page) !important; color:var(--ink) !important; font-family:'DM Sans',sans-serif !important; }
[data-testid="stSidebar"] { background-color:var(--bg-card) !important; border-right:1px solid var(--bdr) !important; }
.block-container { padding:3rem 4rem !important; max-width:100% !important; }
[data-testid="stTextInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"]>div {
  background-color:#26111A !important; border:1px solid #401B2B !important; border-radius:4px !important; color:var(--buser) !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom:2px solid var(--bdr) !important; gap:20px !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { color:var(--ink-muted) !important; font-weight:500 !important; border:none !important; border-bottom:3px solid transparent !important; }
[data-testid="stTabs"] [aria-selected="true"][data-baseweb="tab"] { color:var(--buser) !important; border-bottom-color:var(--buser) !important; }
.pg-header { display:flex; align-items:flex-end; justify-content:space-between; padding-bottom:1rem; margin-bottom:1rem; border-bottom:1px solid var(--bdr); }
.pg-eyebrow { font-size:.75rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:var(--buser); margin-bottom:8px; }
.pg-title { font-family:'DM Serif Display',serif; font-size:2.5rem; font-weight:400; line-height:1.1; }
.section-label { font-size:.7rem; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:var(--ink-muted); margin-bottom:10px; margin-top:2rem; }
.section-title { font-family:'DM Serif Display',serif; font-size:1.4rem; font-weight:400; margin-bottom:5px; }
[data-testid="stDataTable"] { border:1px solid var(--bdr) !important; border-radius:8px !important; overflow:hidden !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background-color:var(--bg-card) !important; border:1px solid var(--bdr) !important; border-radius:6px !important; }
[data-baseweb="option"] { background-color:var(--bg-card) !important; font-size:.85rem !important; color:var(--ink) !important; padding:10px 12px !important; }
[data-baseweb="option"]:hover,[aria-selected="true"][data-baseweb="option"] { background-color:#27272A !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data(ttl=60)
def load_data(url: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{url}?t={int(time.time())}", timeout=15)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {url}\n{e}")
        return pd.DataFrame()


def preparar_geral(df: pd.DataFrame) -> pd.DataFrame:
    """
    resultado_geral tem colunas: metrica, julho_2025, julho_2026
    aba_resultados espera: metrica, julho_2025, <feriado_atual>
    → feriado_atual='julho_2026' já existe como coluna, nada a renomear.
    """
    return df.copy() if not df.empty else df


def preparar_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    resultado_por_dia tem: data_atual, metrica, julho_2025, julho_2026
    aba_resultados espera coluna 'data' para os filtros.
    """
    if df.empty:
        return df
    out = df.copy()
    if 'data_atual' in out.columns:
        out.rename(columns={'data_atual': 'data'}, inplace=True)
    return out


def preparar_antecedencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    curva_antecedencia tem: data_julho_2026, eixo_sentido, rota_principal,
                            antecedencia, pax_atual, lf_atual, yield_atual,
                            ticket_medio_atual, pax_julho25, lf_julho25,
                            ticket_medio_julho25
    aba_antecedencia espera: data, sentido, rota_principal, antecedencia,
                             pax_atual, pax_julho25, lf_atual, lf_julho25,
                             yield_atual, ticket_medio_atual, ticket_medio_julho25
    """
    if df.empty:
        return df
    out = df.copy()
    out.rename(columns={
        'data_julho_2026': 'data',
        'eixo_sentido':    'sentido',
    }, inplace=True)
    return out


def preparar_regional(df: pd.DataFrame) -> pd.DataFrame:
    """
    regional_slot tem: regional, slot, metrica, julho_2025, atual
    aba_regionais espera colunas: regional, slot, metrica, <ref_col>, atual
    ref_col configurado na aba como 'julho_2025' → já existe. ✓
    """
    return df.copy() if not df.empty else df


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown('<div class="section-label" style="margin-top:0;">Controle de Dados</div>', unsafe_allow_html=True)
    if st.button("Atualizar Cache dos Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_geral_raw        = preparar_geral(load_data(GITHUB_RAW_GERAL))
    df_dia_raw          = preparar_dia(load_data(GITHUB_RAW_DIA))
    df_antecedencia_raw = preparar_antecedencia(load_data(GITHUB_RAW_ANTECEDENCIA))
    df_alteracoes_raw   = load_data(GITHUB_RAW_ALTERACOES)
    df_reg_geral_raw    = preparar_regional(load_data(GITHUB_RAW_REG_GERAL))
    df_reg_dia_raw      = pd.DataFrame()   # não usado pela aba_regionais
    df_reg_rota_raw     = df_antecedencia_raw  # aba_regionais usa o mesmo df para detalhamento por rota

# ==========================================
# ABAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Resultados",
    "Resultados Regionais",
    "Acompanhamento por Antecedência",
    "Histórico Alterações de Preço",
])

with tab1:
    aba_resultados.render_resultados(
        df_geral_raw, df_dia_raw,
        feriado_atual, data_ancora_ida, data_ancora_volta
    )

with tab2:
    aba_regionais.render_regionais(df_reg_geral_raw, df_reg_dia_raw, df_reg_rota_raw)

with tab3:
    aba_antecedencia.render_rota_antecedencia(df_antecedencia_raw)

with tab4:
    aba_historico.render_historico(df_alteracoes_raw)
