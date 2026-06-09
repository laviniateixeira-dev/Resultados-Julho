import streamlit as st
import pandas as pd

def render_resultados(df_g_raw: pd.DataFrame, df_d_raw: pd.DataFrame, feriado_atual: str, data_ancora_ida: str, data_ancora_volta: str):
    st.markdown("""
    <div class="pg-header">
     <div>
      <div class="pg-eyebrow">Performance</div>
      <div class="pg-title">Resultados de Julho</div>
     </div>
    </div>
    """, unsafe_allow_html=True)
      
    if df_g_raw.empty or df_d_raw.empty:
        st.info("Nenhum dado encontrado para a aba Resultados.")
        return

    df_g = df_g_raw.copy()
    df_d = df_d_raw.copy()
      
    if feriado_atual in df_g.columns: df_g.rename(columns={feriado_atual: 'atual'}, inplace=True)
    if feriado_atual in df_d.columns: df_d.rename(columns={feriado_atual: 'atual'}, inplace=True)
        
    if 'metrica' in df_g.columns:
        df_g['metrica'] = df_g['metrica'].str.replace(r' \(Capacidade x Km\)', '', regex=True).str.replace(r' \(Pax x Km\)', '', regex=True)
    if 'metrica' in df_d.columns:
        df_d['metrica'] = df_d['metrica'].str.replace(r' \(Capacidade x Km\)', '', regex=True).str.replace(r' \(Pax x Km\)', '', regex=True)

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
        opcoes_data = ["Consolidado Mês", "Ida e Volta Forte", "Dias Fracos"]
        if 'data' in df_d.columns:
            opcoes_data.extend(sorted(df_d['data'].dropna().unique()))
          
        filtro_data = st.selectbox(
            "Filtro de Data:", options=opcoes_data, 
            format_func=lambda x: pd.to_datetime(x).strftime('%d/%m/%Y') if x not in ["Consolidado Mês", "Ida e Volta Forte", "Dias Fracos"] else x,
            label_visibility="collapsed"
        )
    with col_f2:
        opcoes_dropdown = ["Julho 2025"]
        ref_nome = st.selectbox("Comparar com (Ref):", opcoes_dropdown, key="res_ref_sel", label_visibility="collapsed")
        mapa_ref = {"Julho 2025": "julho_2025"}
        ref_sel = mapa_ref.get(ref_nome, "julho_2025") 

    with col_t:
        mapa_datas_fortes = {
            "Julho 2025": "04/07 e 27/07"
        }
        atual_fortes = "03/07 e 26/07"

        # Lógica para montar o subtítulo
        if filtro_data == "Consolidado Mês":
            texto_sub = f"(Todo o Período) vs ({ref_nome})"
        elif filtro_data == "Ida e Volta Forte":
            texto_sub = f"({atual_fortes}) vs ({mapa_datas_fortes.get(ref_nome, '')})"
        elif filtro_data == "Dias Fracos":
            texto_sub = f"(Dias Fracos) vs (Dias Fracos - {ref_nome})"
        else:
            # Pega o mesmo dia na âncora do ano anterior (+1 dia)
            dt_obj = pd.to_datetime(filtro_data)
            texto_data = dt_obj.strftime('%d/%m')
            
            # Cálculo automático do dia equivalente (ex: 03/07/26 vira 04/07/25)
            if ref_nome == "Julho 2025":
                dia_equivalente = (dt_obj + pd.Timedelta(days=1)).strftime('%d/%m')
            else:
                dia_equivalente = f"Eq. {ref_nome}"
                
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
      
    if filtro_data == "Consolidado Mês":
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
