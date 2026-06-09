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
