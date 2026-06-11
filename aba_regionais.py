import streamlit as st
import pandas as pd

CAPACIDADE_PADRAO = 44

def formatar_valor_metrica(val, metrica_nome):
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
    st.markdown('<div class="pg-header"><div class="pg-title">Performance Regional × Slots - Julho</div></div>', unsafe_allow_html=True)

    if df_geral.empty:
        st.warning("📊 Aguardando o carregamento das bases regionais...")
        return

    df_g = df_geral.copy()
    if 'metrica' in df_g.columns:
        df_g['metrica'] = df_g['metrica'].str.replace(r'^\d+\.\s*', '', regex=True).str.strip()

    # ── FILTROS ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Filtros de Visão</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        regionais = sorted(df_g['regional'].dropna().unique())
        reg_sel = st.selectbox("Selecione a Regional:", regionais)

    with c2:
        slots = sorted(df_g['slot'].dropna().unique())
        slot_sel = st.selectbox("Selecione o Slot de Ônibus:", slots)

    with c3:
        # A única referência disponível no CSV regional_slot é 'julho_2025'
        feriados_referencia = {"Julho 2025": "julho_2025"}
        ref_label = st.selectbox("Comparar 2026 contra:", list(feriados_referencia.keys()))
        ref_col = feriados_referencia[ref_label]

    df_g_filt = df_g[(df_g['regional'] == reg_sel) & (df_g['slot'] == slot_sel)]

    def puxar(df, metrica, coluna):
        try:
            linha = df[df['metrica'].str.lower() == metrica.lower()]
            return float(linha[coluna].values[0])
        except:
            return 0.0

    # ── KPI CARDS ────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Indicadores Consolidados do Período</div>', unsafe_allow_html=True)

    pax_26  = puxar(df_g_filt, "Pax Total",          "atual")
    pax_ref = puxar(df_g_filt, "Pax Total",          ref_col)
    pax_delta = ((pax_26 - pax_ref) / pax_ref * 100) if pax_ref > 0 else 0.0

    grupos_26  = puxar(df_g_filt, "Grupos Realizados", "atual")
    grupos_ref = puxar(df_g_filt, "Grupos Realizados", ref_col)

    ocup_26  = (pax_26  / (grupos_26  * CAPACIDADE_PADRAO)) if grupos_26  > 0 else 0.0
    ocup_ref = (pax_ref / (grupos_ref * CAPACIDADE_PADRAO)) if grupos_ref > 0 else 0.0
    ocup_delta = (ocup_26 - ocup_ref) * 100

    lf_26  = puxar(df_g_filt, "Load Factor",  "atual")
    lf_ref = puxar(df_g_filt, "Load Factor",  ref_col)
    lf_delta = (lf_26 - lf_ref) * 100

    tk_26  = puxar(df_g_filt, "Ticket Médio", "atual")
    tk_ref = puxar(df_g_filt, "Ticket Médio", ref_col)
    tk_delta = ((tk_26 - tk_ref) / tk_ref * 100) if tk_ref > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Passageiros Transportados", f"{pax_26:,.0f}",       f"{pax_delta:+.1f}% vs {ref_label}")
    k2.metric("Taxa de Ocupação Física",   f"{ocup_26*100:.1f}%",  f"{ocup_delta:+.1f} p.p. vs {ref_label}")
    k3.metric("Load Factor",               f"{lf_26*100:.1f}%",    f"{lf_delta:+.1f} p.p. vs {ref_label}")
    k4.metric("Ticket Médio",              f"R$ {tk_26:,.2f}",     f"{tk_delta:+.1f}% vs {ref_label}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABELA CONSOLIDADA ───────────────────────────────────────────
    with st.expander("📄 Ver Detalhes da Tabela Consolidada", expanded=True):
        df_g_clean = df_g_filt[['metrica', ref_col, 'atual']].copy()

        linha_ocup = pd.DataFrame([{'metrica': 'Taxa de Ocupação', ref_col: ocup_ref, 'atual': ocup_26}])
        df_g_final = pd.concat([df_g_clean, linha_ocup], ignore_index=True)

        df_g_final[ref_label]      = df_g_final.apply(lambda r: formatar_valor_metrica(r[ref_col], r['metrica']), axis=1)
        df_g_final["Atual (2026)"] = df_g_final.apply(lambda r: formatar_valor_metrica(r['atual'],  r['metrica']), axis=1)

        st.dataframe(df_g_final[['metrica', ref_label, 'Atual (2026)']], use_container_width=True, hide_index=True)

    # ── DETALHAMENTO POR ROTA (usa df_rota = curva_antecedencia) ────
    st.markdown('<div class="section-label">Detalhamento por Rota Principal</div>', unsafe_allow_html=True)

    if df_rota is not None and not df_rota.empty:
        # Filtra pelo regional se a coluna existir; senão mostra todas
        df_r_filt = df_rota.copy()
        if 'regional' in df_r_filt.columns:
            df_r_filt = df_r_filt[df_r_filt['regional'] == reg_sel]

        rotas = sorted(df_r_filt['rota_principal'].dropna().unique().tolist()) if 'rota_principal' in df_r_filt.columns else []

        if rotas:
            rota_sel2 = st.selectbox("Selecione uma Rota:", rotas, key="reg_rota_sel")
            df_rs = df_r_filt[df_r_filt['rota_principal'] == rota_sel2]

            if not df_rs.empty:
                linha = df_rs.sort_values('antecedencia', ascending=True).iloc[0]
                pax_r    = linha.get('pax_atual', 0.0) or 0.0
                grupos_r = linha.get('grupos_atual', 0.0) or 0.0
                ocup_r   = (pax_r / (grupos_r * CAPACIDADE_PADRAO)) if grupos_r > 0 else 0.0

                dados = [
                    {"Métrica": "Pax Total",            "2026": pax_r,                                  "tipo": "int"},
                    {"Métrica": "Grupos Realizados",    "2026": grupos_r,                               "tipo": "int"},
                    {"Métrica": "Ticket Médio",         "2026": linha.get('ticket_medio_atual', 0.0),   "tipo": "money"},
                    {"Métrica": "Taxa de Ocupação",     "2026": ocup_r,                                 "tipo": "pct"},
                    {"Métrica": "Load Factor",          "2026": linha.get('lf_atual', 0.0),             "tipo": "pct"},
                    {"Métrica": "GMV Capturado",        "2026": linha.get('gmv_atual', 0.0),            "tipo": "money"},
                ]

                def fmt(row):
                    v, t = row["2026"], row["tipo"]
                    if not v or pd.isna(v) or v == 0.0: return "-"
                    if t == "int":   return f"{v:,.0f}"
                    if t == "money": return f"R$ {v:,.2f}"
                    if t == "pct":   return f"{v*100:.1f}%"
                    return str(v)

                df_rm = pd.DataFrame(dados)
                df_rm["Atual (2026)"] = df_rm.apply(fmt, axis=1)
                st.dataframe(df_rm[["Métrica", "Atual (2026)"]], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma rota encontrada para a regional selecionada.")
    else:
        st.info("ℹ️ Dados por rota indisponíveis.")
