import streamlit as st
import pandas as pd
import plotly.express as px

def render_rota_antecedencia(df_ra_raw: pd.DataFrame):
    st.markdown("""
    <div class="pg-header">
      <div>
        <div class="pg-eyebrow">Acompanhamento</div>
        <div class="pg-title">Curva por Antecedência - Julho</div>
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
        data_sel = st.selectbox(
            "Data da Viagem:",
            options=sorted(df_sentido['data'].dropna().unique()),
            format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y')
        )
    with col_f4:
        # Único período de referência disponível no CSV de Julho
        opcoes_ref = {"Julho 2025": "julho25"}
        ref_nome = st.selectbox("Comparar com (Ref):", list(opcoes_ref.keys()))
        sfx = opcoes_ref[ref_nome]

    df_filt = df_sentido[df_sentido['data'] == data_sel].copy()
    if df_filt.empty:
        st.warning("Sem dados para este corte exato.")
        return

    # Mapeia colunas históricas para nomes genéricos usados no gráfico
    rename_mapping = {
        f'pax_{sfx}':          'pax_referencia',
        f'lf_{sfx}':           'lf_referencia',
        f'yield_{sfx}':        'yield_referencia',
        f'ticket_medio_{sfx}': 'ticket_medio_referencia',
    }
    df_filt.rename(columns=rename_mapping, inplace=True)

    agg_dict = {}
    for c in ['pax_atual', 'pax_referencia']:
        if c in df_filt.columns: agg_dict[c] = 'sum'
    for c in ['lf_atual', 'lf_referencia', 'yield_atual', 'yield_referencia',
              'ticket_medio_atual', 'ticket_medio_referencia']:
        if c in df_filt.columns: agg_dict[c] = 'mean'

    df_plot = df_filt.groupby('antecedencia').agg(agg_dict).reset_index()

    st.markdown('<div class="section-label">Gráfico de Evolução</div>', unsafe_allow_html=True)
    metrica_grafico = st.radio(
        "Escolha o indicador:",
        options=["Passageiros (Pax)", "Load Factor", "Yield (R$)", "Ticket Médio (R$)"],
        horizontal=True
    )

    chart_df = df_plot.copy()
    if metrica_grafico == "Passageiros (Pax)":
        y_cols = [c for c in ['pax_atual', 'pax_referencia'] if c in chart_df.columns]
    elif metrica_grafico == "Load Factor":
        y_cols = [c for c in ['lf_atual', 'lf_referencia'] if c in chart_df.columns]
    elif metrica_grafico == "Yield (R$)":
        y_cols = [c for c in ['yield_atual', 'yield_referencia'] if c in chart_df.columns]
    else:
        y_cols = [c for c in ['ticket_medio_atual', 'ticket_medio_referencia'] if c in chart_df.columns]

    if not y_cols:
        st.warning(f"Colunas para '{metrica_grafico}' não encontradas para a referência {ref_nome}.")
    else:
        legend_rename = {y_cols[0]: "Cenário Atual"}
        if len(y_cols) > 1:
            legend_rename[y_cols[1]] = f"Ref ({ref_nome})"

        chart_df = chart_df[['antecedencia'] + y_cols].rename(columns=legend_rename)
        df_melt = chart_df.melt(id_vars='antecedencia', var_name='Cenário', value_name='Valor')

        fig = px.line(
            df_melt, x='antecedencia', y='Valor', color='Cenário',
            color_discrete_map={'Cenário Atual': '#FF66A3', f'Ref ({ref_nome})': '#FFFFFF'},
            markers=True
        )
        if metrica_grafico in ["Load Factor", "Yield (R$)"]:
            fig.update_yaxes(rangemode="tozero", title=metrica_grafico, showgrid=True, gridcolor="#2A2A2A")
        else:
            fig.update_yaxes(rangemode="tozero", title=metrica_grafico, showgrid=True, gridcolor="#2A2A2A")

        fig.update_layout(
            hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#999999", margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
        )
        fig.update_xaxes(title="Dias de Antecedência", tickformat="d", dtick=2, showgrid=True, gridcolor="#2A2A2A")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label" style="margin-top: 2.5rem;">Tabela de Acompanhamento (Dia a Dia)</div>', unsafe_allow_html=True)

    col_config = {
        "antecedencia":           st.column_config.NumberColumn("Dias Antec.", format="%d"),
        "pax_atual":              st.column_config.NumberColumn("Pax (Atual)"),
        "pax_referencia":         st.column_config.NumberColumn(f"Pax ({ref_nome})"),
        "ticket_medio_atual":     st.column_config.NumberColumn("Ticket Médio (Atual)", format="R$ %.2f"),
        "ticket_medio_referencia":st.column_config.NumberColumn(f"Ticket Médio ({ref_nome})", format="R$ %.2f"),
        "lf_atual":               st.column_config.NumberColumn("LF (Atual)", format="%.2f"),
        "lf_referencia":          st.column_config.NumberColumn(f"LF ({ref_nome})", format="%.2f"),
        "yield_atual":            st.column_config.NumberColumn("Yield (Atual)", format="R$ %.3f"),
        "yield_referencia":       st.column_config.NumberColumn(f"Yield ({ref_nome})", format="R$ %.3f"),
    }

    cols_to_show_raw = ["antecedencia", "pax_atual", "pax_referencia",
                        "ticket_medio_atual", "ticket_medio_referencia",
                        "lf_atual", "lf_referencia",
                        "yield_atual", "yield_referencia"]
    cols_to_show = [c for c in cols_to_show_raw if c in df_filt.columns]

    st.dataframe(
        df_filt.sort_values("antecedencia", ascending=False)[cols_to_show],
        use_container_width=True, hide_index=True, column_config=col_config
    )
