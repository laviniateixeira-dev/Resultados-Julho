eu tenho esse codigo no git de um feriado passado
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

aba antecedencia
import streamlit as st
import pandas as pd
import plotly.express as px

def render_rota_antecedencia(df_ra_raw: pd.DataFrame):
    st.markdown("""
    <div class="pg-header">
      <div>
        <div class="pg-eyebrow">Acompanhamento</div>
        <div class="pg-title">Curva por Antecedência</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if df_ra_raw.empty:
        st.info("Nenhum dado encontrado para acompanhamento de rotas.")
        return

    df_ra = df_ra_raw.copy()
        
    if 'data' not in df_ra.columns or 'rota_principal' not in df_ra.columns or 'sentido' not in df_ra.columns:
        st.error(f"Colunas essenciais não encontradas. Temos: {list(df_ra.columns)}")
        return

    df_ra['data'] = pd.to_datetime(df_ra['data'], errors='coerce')
    
    st.markdown('<div class="section-label" style="margin-top: 0.5rem;">Selecione o Corte</div>', unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
    
    with col_f1: 
        rota_sel = st.selectbox("Rota Principal:", options=sorted(df_ra['rota_principal'].dropna().unique()))
    with col_f2:
        df_rota = df_ra[df_ra['rota_principal'] == rota_sel]
        sentido_sel = st.selectbox("Sentido:", options=sorted(df_rota['sentido'].dropna().unique()))
    with col_f3:
        df_sentido = df_rota[df_rota['sentido'] == sentido_sel]
        data_sel = st.selectbox("Data da Viagem:", options=sorted(df_sentido['data'].dropna().unique()), format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y'))
    with col_f4:
        # Filtro Dinâmico de Referência para a Curva
        opcoes_ref = {"Páscoa 2026": "pascoa26", "Corpus 2025": "corpus25", "Maio 2026": "maio26"}
        ref_nome = st.selectbox("Comparar com (Ref):", list(opcoes_ref.keys()))
        sfx = opcoes_ref[ref_nome]

    df_filt = df_sentido[df_sentido['data'] == data_sel].copy()
    if df_filt.empty:
        st.warning("Sem dados para este corte exato.")
        return

    # Mapeando os nomes para os nomes padrão que o gráfico usa
    rename_mapping = {
        f'pax_{sfx}': 'pax_referencia',
        f'lf_{sfx}': 'lf_referencia',
        f'yield_{sfx}': 'yield_referencia',
        f'ticket_medio_{sfx}': 'ticket_medio_referencia'
    }
    df_filt.rename(columns=rename_mapping, inplace=True)

    agg_dict = {}
    for c in ['pax_atual', 'pax_referencia']:
        if c in df_filt.columns: agg_dict[c] = 'sum'
    for c in ['lf_atual', 'lf_referencia', 'yield_atual', 'yield_referencia', 'ticket_medio_atual', 'ticket_medio_referencia']:
        if c in df_filt.columns: agg_dict[c] = 'mean'

    df_plot = df_filt.groupby('antecedencia').agg(agg_dict).reset_index()

    st.markdown('<div class="section-label">Gráfico de Evolução</div>', unsafe_allow_html=True)
    metrica_grafico = st.radio("Escolha o indicador:", options=["Passageiros (Pax)", "Load Factor", "Yield (R$)", "Ticket Médio (R$)"], horizontal=True)

    chart_df = df_plot.copy()
    y_cols = []
    
    if metrica_grafico == "Passageiros (Pax)": y_cols = [c for c in ['pax_atual', 'pax_referencia'] if c in chart_df.columns]
    elif metrica_grafico == "Load Factor": y_cols = [c for c in ['lf_atual', 'lf_referencia'] if c in chart_df.columns]
    elif metrica_grafico == "Yield (R$)": y_cols = [c for c in ['yield_atual', 'yield_referencia'] if c in chart_df.columns]
    else: y_cols = [c for c in ['ticket_medio_atual', 'ticket_medio_referencia'] if c in chart_df.columns]

    if len(y_cols) == 0:
        st.warning(f"As colunas para {metrica_grafico} não estão presentes na base de dados para a referência {ref_nome}.")
    else:
        legend_rename = {y_cols[0]: "Cenário Atual"}
        if len(y_cols) > 1: legend_rename[y_cols[1]] = f"Ref ({ref_nome})"
        
        chart_df = chart_df[['antecedencia'] + y_cols].rename(columns=legend_rename)
        df_melt = chart_df.melt(id_vars='antecedencia', var_name='Cenário', value_name='Valor')

        fig = px.line(
            df_melt, x='antecedencia', y='Valor', color='Cenário',
            color_discrete_map={'Cenário Atual': '#FF66A3', f'Ref ({ref_nome})': '#FFFFFF'}, markers=True
        )

        if metrica_grafico in ["Load Factor", "Yield (R$)"]: fig.update_yaxes(range=[0, 1], title=metrica_grafico, showgrid=True, gridcolor="#2A2A2A")
        else: fig.update_yaxes(rangemode="tozero", title=metrica_grafico, showgrid=True, gridcolor="#2A2A2A")

        fig.update_layout(
            hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#999999", margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
        )
        fig.update_xaxes(title="Dias de Antecedência", tickformat="d", dtick=2, showgrid=True, gridcolor="#2A2A2A")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label" style="margin-top: 2.5rem;">Tabela de Acompanhamento (Dia a Dia)</div>', unsafe_allow_html=True)
    
    col_config = {
        "antecedencia": st.column_config.NumberColumn("Dias Antec.", format="%d"),
        "pax_atual": st.column_config.NumberColumn("Pax (Atual)"),
        "pax_referencia": st.column_config.NumberColumn(f"Pax ({ref_nome})"),
        "ticket_medio_atual": st.column_config.NumberColumn("Ticket Médio (Atual)", format="R$ %.2f"),
        "ticket_medio_referencia": st.column_config.NumberColumn(f"Ticket Médio ({ref_nome})", format="R$ %.2f"),
        "lf_atual": st.column_config.NumberColumn("LF (Atual)", format="%.2f"),
        "lf_referencia": st.column_config.NumberColumn(f"LF ({ref_nome})", format="%.2f"),
        "yield_atual": st.column_config.NumberColumn("Yield (Atual)", format="R$ %.3f"),
        "yield_referencia": st.column_config.NumberColumn(f"Yield ({ref_nome})", format="R$ %.3f")
    }
    
    cols_to_show_raw = ["antecedencia", "pax_atual", "pax_referencia", "ticket_medio_atual", "ticket_medio_referencia", "lf_atual", "lf_referencia", "yield_atual", "yield_referencia"]
    cols_to_show = [c for c in cols_to_show_raw if c in df_filt.columns]
    
    st.dataframe(
        df_filt.sort_values("antecedencia", ascending=False)[cols_to_show], 
        use_container_width=True, hide_index=True, column_config=col_config
    )

aba historico
import streamlit as st
import pandas as pd

def render_historico(df_raw: pd.DataFrame):
    st.markdown("""
    <div class="pg-header">
      <div>
        <div class="pg-eyebrow">Acompanhamento</div>
        <div class="pg-title">Histórico Alterações de Preço</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    if df_raw.empty:
        st.info("Nenhum dado encontrado.")
        return

    df = df_raw.copy()
    
    if 'data' in df.columns and 'data_atual' not in df.columns:
        df.rename(columns={'data': 'data_atual'}, inplace=True)
        
    rename_map = {
        'preco_cenario_atual': 'preco_atual',
        'mult_atual_aplicado': 'mult_atual'
    }
    df.rename(columns=rename_map, inplace=True)
    
    cols_desejadas = [
        'data_atual', 'dia_da_semana', 'antecedencia', 'rota_principal', 
        'sentido', 'tipo_assento', 'turno', 'tkm_atual', 'preco_atual', 
        'mult_atual', 'data_atualizacao'
    ]
    
    cols_disponiveis = [c for c in cols_desejadas if c in df.columns]
    df = df[cols_disponiveis]
    
    st.markdown('<div class="section-label" style="margin-top:0;">Filtros de Pesquisa</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'rota_principal' in df.columns:
            rotas = ["Todas"] + sorted(df['rota_principal'].dropna().unique().tolist())
            rota_sel = st.selectbox("Rota Principal:", rotas)
            if rota_sel != "Todas": df = df[df['rota_principal'] == rota_sel]
            
    with col2:
        if 'sentido' in df.columns:
            sentidos = ["Todos"] + sorted(df['sentido'].dropna().unique().tolist())
            sentido_sel = st.selectbox("Sentido:", sentidos)
            if sentido_sel != "Todos": df = df[df['sentido'] == sentido_sel]
            
    with col3:
        if 'data_atual' in df.columns:
            datas = ["Todas"] + sorted(df['data_atual'].dropna().unique().tolist())
            data_sel = st.selectbox("Data da Viagem:", datas)
            if data_sel != "Todas": df = df[df['data_atual'] == data_sel]

    if 'data_atualizacao' in df.columns:
        df['data_atualizacao_dt'] = pd.to_datetime(df['data_atualizacao'], errors='coerce')
        df = df.sort_values(by='data_atualizacao_dt', ascending=False, na_position='last').drop(columns=['data_atualizacao_dt'])

    st.markdown('<div class="section-label" style="margin-top: 1.5rem;">Tabela Consolidada</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

aba regioanais
import streamlit as st
import pandas as pd

# ==========================================
# CONFIGURAÇÃO DE CAPACIDADE DA FROTA
# ==========================================
CAPACIDADE_PADRAO = 44  # Altere aqui para 48 ou 50 se necessário

def formatar_valor_metrica(val, metrica_nome):
    """Aplica formatação executiva para cada tipo de linha de métrica na tabela."""
    try:
        v = float(val)
        if pd.isna(v) or v == 0.0: 
            return "-"
        
        m = str(metrica_nome).lower()
        if "rask" in m or "yield" in m:
            return f"R$ {v:.4f}"
        elif "ticket" in m or "gmv" in m:
            return f"R$ {v:,.2f}"
        elif "load factor" in m or "taxa de ocupação" in m:
            return f"{v * 100:.1f}%"
        elif "grupos" in m or "pax" in m or "ask" in m or "rpk" in m:
            return f"{v:,.0f}"
        return f"{v}"
    except:
        return str(val)

def render_regionais(df_geral, df_dia, df_rota):
    """Renderiza a aba de Resultados Regionais com foco analítico e tabela de rota enxuta."""
    
    st.markdown('<div class="pg-header"><div class="pg-title">Performance Regional × Slots</div></div>', unsafe_allow_html=True)
    
    if df_geral.empty or df_dia.empty or df_rota.empty:
        st.warning("📊 Aguardando o carregamento completo das bases regionais...")
        return

    # Clonando os dados para evitar problemas de concorrência
    df_g = df_geral.copy()
    df_r = df_rota.copy()

    # ── LIMPEZA E PADRONIZAÇÃO DAS MÉTRICAS DE ORIGEM ────────────────────────
    for df_target in [df_g]:
        if 'metrica' in df_target.columns:
            df_target['metrica'] = df_target['metrica'].str.replace(r'^\d+\.\s*', '', regex=True).str.strip()

    # ==========================================
    # 1. BLOCO DE FILTROS DO TOPO
    # ==========================================
    st.markdown('<div class="section-label">Filtros de Visão</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        regionais = sorted(df_g['regional'].dropna().unique())
        reg_sel = st.selectbox("Selecione a Regional:", regionais)
        
    with c2:
        slots = sorted(df_g['slot'].dropna().unique())
        slot_sel = st.selectbox("Selecione o Slot de Ônibus:", slots)
        
    with c3:
        feriados_referencia = {
            "Corpus Christi 2025": "corpus_2025",
            "Páscoa 2026": "pascoa_2026",
            "Maio 2026": "maio_2026"
        }
        ref_label = st.selectbox("Comparar 2026 contra:", list(feriados_referencia.keys()))
        ref_col = feriados_referencia[ref_label]

    # Aplicando os filtros nos dataframes principais
    df_g_filt = df_g[(df_g['regional'] == reg_sel) & (df_g['slot'] == slot_sel)]
    df_r_filt = df_r[(df_r['regional'] == reg_sel) & (df_r['slot'] == slot_sel)]

    # Auxiliar para extrair valores das métricas brutas vindo do banco
    def puxar_valor_bruto(df, termo_metrica, coluna):
        try:
            linha = df[df['metrica'].str.lower() == termo_metrica.lower()]
            return float(linha[coluna].values[0])
        except:
            return 0.0

    # ==========================================
    # 2. VISÃO EXECUTIVA (KPI CARDS)
    # ==========================================
    st.markdown('<div class="section-label">Indicadores Consolidados do Feriado</div>', unsafe_allow_html=True)
    
    pax_26 = puxar_valor_bruto(df_g_filt, "Pax Total", "atual")
    pax_ref = puxar_valor_bruto(df_g_filt, "Pax Total", ref_col)
    pax_delta = ((pax_26 - pax_ref) / pax_ref * 100) if pax_ref > 0 else 0.0

    grupos_26 = puxar_valor_bruto(df_g_filt, "Grupos Realizados", "atual")
    grupos_ref = puxar_valor_bruto(df_g_filt, "Grupos Realizados", ref_col)

    # Cálculo da Taxa de Ocupação Física Percentual
    ocup_26 = (pax_26 / (grupos_26 * CAPACIDADE_PADRAO)) if grupos_26 > 0 else 0.0
    ocup_ref = (pax_ref / (grupos_ref * CAPACIDADE_PADRAO)) if grupos_ref > 0 else 0.0
    ocup_delta_p_p = (ocup_26 - ocup_ref) * 100

    # Load Factor puro vindo do banco
    lf_26 = puxar_valor_bruto(df_g_filt, "Load Factor", "atual")
    lf_ref = puxar_valor_bruto(df_g_filt, "Load Factor", ref_col)
    lf_delta_p_p = (lf_26 - lf_ref) * 100

    tk_26 = puxar_valor_bruto(df_g_filt, "Ticket Médio", "atual")
    tk_ref = puxar_valor_bruto(df_g_filt, "Ticket Médio", ref_col)
    tk_delta = ((tk_26 - tk_ref) / tk_ref * 100) if tk_ref > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Passageiros Transportados", f"{pax_26:,.0f}", f"{pax_delta:+.1f}% vs {ref_label}")
    k2.metric("Taxa de Ocupação Física", f"{ocup_26 * 100:.1f}%", f"{ocup_delta_p_p:+.1f} p.p. vs {ref_label}")
    k3.metric("Load Factor", f"{lf_26 * 100:.1f}%", f"{lf_delta_p_p:+.1f} p.p. vs {ref_label}")
    k4.metric("Ticket Médio", f"R$ {tk_26:,.2f}", f"{tk_delta:+.1f}% vs {ref_label}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 3. TABELA CONSOLIDADA GERAL
    # ==========================================
    with st.expander("📄 Ver Detalhes da Tabela Consolidada", expanded=True):
        df_g_clean = df_g_filt[['metrica', ref_col, 'atual']].copy()

        # Inserindo a linha de Taxa de Ocupação na tabela consolidada superior
        linha_ocup_media = pd.DataFrame([{
            'metrica': 'Taxa de Ocupação',
            ref_col: ocup_ref,
            'atual': ocup_26
        }])
        df_g_final = pd.concat([df_g_clean, linha_ocup_media], ignore_index=True)

        # Aplicando a máscara visual de formatação executiva nas duas colunas superiores
        df_g_final[ref_label] = df_g_final.apply(lambda r: formatar_valor_metrica(r[ref_col], r['metrica']), axis=1)
        df_g_final["Atual (2026)"] = df_g_final.apply(lambda r: formatar_valor_metrica(r['atual'], r['metrica']), axis=1)

        st.dataframe(
            df_g_final[['metrica', ref_label, 'Atual (2026)']], 
            use_container_width=True, 
            hide_index=True
        )

    # ==========================================
    # 4. DETALHAMENTO POR ROTA PRINCIPAL (FILTRADO & ENXUTO)
    # ==========================================
    st.markdown('<div class="section-label">Detalhamento por Rota Principal</div>', unsafe_allow_html=True)
    
    if not df_r_filt.empty:
        rotas_validas = df_r_filt['rota_principal'].dropna().unique()
        rotas = sorted([str(r) for r in rotas_validas])
        
        if rotas:
            rota_sel = st.selectbox("Selecione uma Rota para analisar os indicadores acumulados:", rotas)
            
            df_rota_sel = df_r_filt[df_r_filt['rota_principal'] == rota_sel]
            if not df_rota_sel.empty:
                # Pega a linha mais atualizada da rota (antecedência mais próxima de 0)
                linha_recente = df_rota_sel.sort_values(by="antecedencia", ascending=True).iloc[0]
                
                pax_r_26 = linha_recente.get("pax_atual", 0.0)
                grupos_r_26 = linha_recente.get("grupos_atual", 0.0)

                # Cálculo preciso da Ocupação Física para a rota selecionada
                ocup_r_26 = (pax_r_26 / (grupos_r_26 * CAPACIDADE_PADRAO)) if grupos_r_26 > 0 else 0.0

                # 🛠️ REMOÇÃO DA COLUNA DE REF: Mapeando apenas a métrica e o valor atual de 2026
                dados_rota_display = [
                    {"Métrica": "Pax Total", "2026": pax_r_26, "tipo": "int"},
                    {"Métrica": "Grupos Realizados", "2026": grupos_r_26, "tipo": "int"},
                    {"Métrica": "Ticket Médio", "2026": linha_recente.get("ticket_medio_atual", 0.0), "tipo": "money"},
                    {"Métrica": "Taxa de Ocupação Física", "2026": ocup_r_26, "tipo": "pct"},
                    {"Métrica": "Load Factor", "2026": linha_recente.get("lf_atual", 0.0), "tipo": "pct"},
                    {"Métrica": "GMV Capturado", "2026": linha_recente.get("gmv_atual", 0.0), "tipo": "money"},
                ]
                
                df_route_metrics = pd.DataFrame(dados_rota_display)
                
                def fmt_celula_rota(row, col_name):
                    val = row[col_name]
                    t = row["tipo"]
                    if pd.isna(val) or val == 0.0: return "-"
                    if t == "int": return f"{val:,.0f}"
                    if t == "money": return f"R$ {val:,.2f}"
                    if t == "pct": return f"{val * 100:.1f}%"
                    return str(val)
                
                df_route_metrics["Atual (2026)"] = df_route_metrics.apply(lambda r: fmt_celula_rota(r, "2026"), axis=1)
                
                # Exibindo estritamente a Métrica e o Ano Atual de 2026
                st.dataframe(
                    df_route_metrics[["Métrica", "Atual (2026)"]],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Nenhuma rota encontrada para os filtros selecionados.")
    else:
        st.info("ℹ️ Dados por rota indisponíveis para a combinação de filtros atual.")

aba resultados
import streamlit as st
import pandas as pd

def render_resultados(df_g_raw: pd.DataFrame, df_d_raw: pd.DataFrame, feriado_atual: str, data_ancora_ida: str, data_ancora_volta: str):
    st.markdown("""
    <div class="pg-header">
      <div>
        <div class="pg-eyebrow">Performance</div>
        <div class="pg-title">Resultados do Corpus Christi</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    if df_g_raw.empty or df_d_raw.empty:
        st.info("Nenhum dado encontrado para a aba Resultados.")
        return

    df_g = df_g_raw.copy()
    df_d = df_d_raw.copy()
    
    # Força a coluna do feriado atual a se chamar 'atual' para as contas funcionarem
    if feriado_atual in df_g.columns: df_g.rename(columns={feriado_atual: 'atual'}, inplace=True)
    if feriado_atual in df_d.columns: df_d.rename(columns={feriado_atual: 'atual'}, inplace=True)
        
    if 'metrica' in df_g.columns:
        df_g['metrica'] = df_g['metrica'].str.replace(' \(Capacidade x Km\)', '', regex=True).str.replace(' \(Pax x Km\)', '', regex=True)
    if 'metrica' in df_d.columns:
        df_d['metrica'] = df_d['metrica'].str.replace(' \(Capacidade x Km\)', '', regex=True).str.replace(' \(Pax x Km\)', '', regex=True)

    def format_kpi(metrica, valor):
        if pd.isna(valor): return "-"
        if "Load Factor" in metrica: return f"{valor*100:.1f}%"
        if "RASK" in metrica or "Yield" in metrica: return f"R$ {valor:.3f}".replace(".", ",")
        if "Ticket Médio" in metrica or "GMV" in metrica: return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{int(valor):,}".replace(",", ".")

    def format_delta(atual, passado):
        if pd.isna(atual) or pd.isna(passado) or passado == 0: return "-"
        var = (atual / passado) - 1
        return f"{'+' if var > 0 else ''}{var * 100:.1f}%"

    col_t, col_f1, col_f2 = st.columns([2, 1, 1])
    
    with col_f1:
        opcoes_data = ["Consolidado Feriado", "Ida e Volta Forte", "Dias Fracos"]
        if 'data' in df_d.columns:
            opcoes_data.extend(sorted(df_d['data'].dropna().unique()))
        
        filtro_data = st.selectbox(
            "Filtro de Data:", options=opcoes_data, 
            format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y') if x not in ["Consolidado Feriado", "Ida e Volta Forte", "Dias Fracos"] else x,
            label_visibility="collapsed"
        )
    with col_f2:
        opcoes_dropdown = ["Páscoa 2026", "Corpus 2025", "Maio 2026"]
        ref_nome = st.selectbox("Comparar com (Ref):", opcoes_dropdown, key="res_ref_sel", label_visibility="collapsed")
        mapa_ref = {"Páscoa 2026": "pascoa_2026", "Corpus 2025": "corpus_2025", "Maio 2026": "maio_2026"}
        ref_sel = mapa_ref.get(ref_nome, "pascoa_2026") 

    with col_t:
        # Mapeamento das datas âncora (Ida e Volta) de cada feriado
        mapa_datas_fortes = {
            "Páscoa 2026": "02/04 e 05/04",
            "Corpus 2025": "18/06 e 22/06",
            "Maio 2026": "30/04 e 03/05"
        }
        atual_fortes = "03/06 e 07/06"

        # Mapeamento Dia a Dia (baseado no seu de/para original do Databricks)
        mapa_dia_a_dia = {
            "Páscoa 2026": {
                "2026-06-02": "01/04", "2026-06-03": "02/04", "2026-06-04": "03/04",
                "2026-06-05": "04/04", "2026-06-06": "04/04", "2026-06-07": "05/04", "2026-06-08": "06/04"
            },
            "Corpus 2025": {
                "2026-06-02": "17/06", "2026-06-03": "18/06", "2026-06-04": "19/06",
                "2026-06-05": "20/06", "2026-06-06": "21/06", "2026-06-07": "22/06", "2026-06-08": "23/06"
            },
            "Maio 2026": {
                "2026-06-02": "29/04", "2026-06-03": "30/04", "2026-06-04": "01/05",
                "2026-06-05": "02/05", "2026-06-06": "02/05", "2026-06-07": "03/05", "2026-06-08": "04/05"
            }
        }

        # Lógica para montar o subtítulo de acordo com o filtro selecionado
        if filtro_data == "Consolidado Feriado":
            texto_sub = f"(Todo o Período) vs ({ref_nome})"
        elif filtro_data == "Ida e Volta Forte":
            texto_sub = f"({atual_fortes}) vs ({mapa_datas_fortes.get(ref_nome, '')})"
        elif filtro_data == "Dias Fracos":
            texto_sub = f"(Dias Fracos) vs (Dias Fracos - {ref_nome})"
        else:
            dt_obj = pd.to_datetime(filtro_data)
            texto_data = dt_obj.strftime('%d/%m')
            data_iso = dt_obj.strftime('%Y-%m-%d')
            dia_equivalente = mapa_dia_a_dia.get(ref_nome, {}).get(data_iso, f"Eq. {ref_nome}")
            texto_sub = f"({texto_data}) vs ({dia_equivalente})"
            
        titulo_html = f"""
        <div class="section-title">
            Visão Consolidada 
            <span style="font-size: 1.1rem; color: #FF66A3; font-family: 'DM Sans', sans-serif; font-weight: 500; margin-left: 8px;">
                {texto_sub}
            </span>
        </div>
        """
        st.markdown(titulo_html, unsafe_allow_html=True)
        
    st.write("") 
    
    if filtro_data == "Consolidado Feriado":
        df_view = df_g.copy()
    elif filtro_data in ["Ida e Volta Forte", "Dias Fracos"]:
        datas_fortes = [data_ancora_ida, data_ancora_volta]
        if filtro_data == "Ida e Volta Forte":
            df_filtrado = df_d[df_d['data'].isin(datas_fortes)].copy()
        else: 
            df_filtrado = df_d[~df_d['data'].isin(datas_fortes)].copy()

        if not df_filtrado.empty:
            df_filtrado['metrica_limpa'] = df_filtrado['metrica'].apply(lambda x: str(x).split('. ', 1)[-1].strip())
            df_piv = df_filtrado.pivot_table(index='data', columns='metrica_limpa', values=['atual', ref_sel], aggfunc='sum')
            somas = df_piv.sum() 
            
            def get_val(cenario, metrica):
                try: return float(somas[(cenario, metrica)])
                except: return 0.0

            rows = []
            for m_orig in df_g['metrica'].unique():
                m_limpa = str(m_orig).split('. ', 1)[-1].strip()
                if m_limpa == "Yield":
                    v_atual = get_val('atual', 'GMV') / get_val('atual', 'RPK') if get_val('atual', 'RPK') else 0
                    v_ref = get_val(ref_sel, 'GMV') / get_val(ref_sel, 'RPK') if get_val(ref_sel, 'RPK') else 0
                elif m_limpa == "Load Factor":
                    v_atual = get_val('atual', 'RPK') / get_val('atual', 'ASK') if get_val('atual', 'ASK') else 0
                    v_ref = get_val(ref_sel, 'RPK') / get_val(ref_sel, 'ASK') if get_val(ref_sel, 'ASK') else 0
                elif m_limpa == "Ticket Médio":
                    v_atual = get_val('atual', 'GMV') / get_val('atual', 'Pax Total') if get_val('atual', 'Pax Total') else 0
                    v_ref = get_val(ref_sel, 'GMV') / get_val(ref_sel, 'Pax Total') if get_val(ref_sel, 'Pax Total') else 0
                elif m_limpa == "RASK":
                    v_atual = get_val('atual', 'GMV') / get_val('atual', 'ASK') if get_val('atual', 'ASK') else 0
                    v_ref = get_val(ref_sel, 'GMV') / get_val(ref_sel, 'ASK') if get_val(ref_sel, 'ASK') else 0
                else:
                    v_atual = get_val('atual', m_limpa)
                    v_ref = get_val(ref_sel, m_limpa)
                rows.append({'metrica': m_orig, 'atual': v_atual, ref_sel: v_ref})
            df_view = pd.DataFrame(rows)
        else:
            df_view = df_g.copy() 
    else: 
        df_view = df_d[df_d['data'] == filtro_data].copy()
    
    cols = st.columns(5)
    for i, row in enumerate(df_view.to_dict('records')):
        nome = str(row.get('metrica', '')).split('. ', 1)[-1]
        cols[i % 5].metric(label=nome, value=format_kpi(nome, row.get('atual')), delta=format_delta(row.get('atual'), row.get(ref_sel)))

    st.markdown('<div class="section-label" style="margin-top: 0.5rem; margin-bottom: 0.5rem;">Comparativo Direto (Absolutos)</div>', unsafe_allow_html=True)
    df_tg = df_view.copy()
    df_tg['Métrica'] = df_tg['metrica'].apply(lambda x: str(x).split('. ', 1)[-1])
    df_tg[f'Ref ({ref_nome})'] = df_tg.apply(lambda row: format_kpi(row['Métrica'], row.get(ref_sel, 0)), axis=1)
    df_tg['Atual'] = df_tg.apply(lambda row: format_kpi(row['Métrica'], row.get('atual', 0)), axis=1)
    df_tg['Var %'] = df_tg.apply(lambda row: format_delta(row.get('atual', 0), row.get(ref_sel, 0)), axis=1)
    
    st.dataframe(df_tg[['Métrica', f'Ref ({ref_nome})', 'Atual', 'Var %']], use_container_width=True, hide_index=True)


aba app.py
import streamlit as st
import pandas as pd
import requests
import io

# Importando os arquivos de abas
import aba_resultados
import aba_regionais  # Nova aba conectada
import aba_antecedencia
import aba_historico

# ==========================================
# CONFIGURAÇÕES DO FERIADO E LINKS
# ==========================================
feriado_atual = "corpus_2026"
ref_1 = "pascoa_2026"

# DATAS ÂNCORA PARA A ABA DE RESULTADOS
data_ancora_ida = "2026-06-03" 
data_ancora_volta = "2026-06-07" 

# LINKS DO GITHUB PADRONIZADOS NO REPOSITÓRIO '123'
GITHUB_RAW_CURVA = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/curva_{feriado_atual}.csv"
GITHUB_RAW_GERAL = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_geral_{feriado_atual}.csv"
GITHUB_RAW_DIA = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_dia_{feriado_atual}.csv"
GITHUB_RAW_ROTA = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_rota_antecedencia_{feriado_atual}.csv"

# LINKS REGIONAIS DO SEU DATABRICKS NO REPOSITÓRIO '123'
GITHUB_RAW_REG_GERAL = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_regional_geral_{feriado_atual}.csv"
GITHUB_RAW_REG_DIA = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_regional_dia_{feriado_atual}.csv"
GITHUB_RAW_REG_ROTA = f"https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Corpus-Christi123/main/data/resultados_regional_rota_{feriado_atual}.csv"
# ==========================================

st.set_page_config(
    page_title="Pricing · Corpus Christi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA CUSTOMIZADA: PRETO, GRAFITE & ROSA BUSER ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {
  --bg-page:   #0D0D0D; 
  --bg-card:   #171717; 
  --ink:       #FFFFFF; 
  --ink-muted: #999999; 
  --buser:     #FF66A3; 
  --buser-lt:  #FFB3D1; 
  --bdr:       #2A2A2A; 
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


porem preciso adptar para um novo feriado q eu to fazneodq tem essas essas curvas
https://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data/julho_2026_resultado_geral.csvhttps://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data/julho_2026_resultado_por_dia.csvhttps://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data/julho_2026_curva_antecedencia.csvhttps://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data/julho_2026_alteracoes_preco.csvhttps://raw.githubusercontent.com/laviniateixeira-dev/Resultados-Julho/main/data/julho_2026_regional_slot.csv
