import streamlit as st
import pandas as pd

# ==========================================
# CONFIGURAÇÃO DE CAPACIDADE DA FROTA
# ==========================================
CAPACIDADE_PADRAO = 44 # Altere aqui para 48 ou 50 se necessário

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
      
    st.markdown('<div class="pg-header"><div class="pg-title">Performance Regional × Slots - Julho</div></div>', unsafe_allow_html=True)
      
    if df_geral.empty or df_dia.empty or df_rota.empty:
        st.warning(":bar_chart: Aguardando o carregamento completo das bases regionais...")
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
        # Simplificado para apenas Julho de 2025
        feriados_referencia = {
            "Julho 2025": "julho_2025"
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
    st.markdown('<div class="section-label">Indicadores Consolidados do Período</div>', unsafe_allow_html=True)
      
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
    with st.expander(":page_facing_up: Ver Detalhes da Tabela Consolidada", expanded=True):
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
                  
                st.dataframe(
                    df_route_metrics[["Métrica", "Atual (2026)"]],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Nenhuma rota encontrada para os filtros selecionados.")
    else:
        st.info(":information_source: Dados por rota indisponíveis para a combinação de filtros atual.")
