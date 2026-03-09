import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestión Richard Zapata - BI Project", layout="wide")

# ESTILO CSS INSTITUCIONAL 
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f1f5f9; }
    .header-box {
        background-color: #ffffff; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 10px solid #1e3a8a;
        margin-bottom: 25px;
    }
    .thesis-title { color: #1e3a8a; font-size: 19px; font-weight: 700; line-height: 1.3; }
    .project-info { color: #475569; font-size: 13px; margin-top: 10px; }
    .stMetric { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 5px solid #1e3a8a;
    }
    .footer-min {
        margin-top: 60px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center;
    }
    .footer-grid { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; padding: 10px 0; }
    .footer-item { font-size: 12px; color: #64748b; text-align: left; }
    .footer-label { font-weight: 700; color: #1e3a8a; display: block; margin-bottom: 2px; }
    .copyright { font-size: 11px; color: #94a3b8; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS Y PERSISTENCIA 
@st.cache_data
def load_institutional_data():
    excel_file = 'Zapata Richard.xlsx'
    db_file = 'seguimiento_rzd.csv'
    if not os.path.exists(excel_file): return pd.DataFrame()
    try:
        df = pd.read_excel(excel_file)
        df.columns = [str(c).strip() for c in df.columns]
        
        cols_map = {
            'Item': 'Item', 
            'Familia': 'Familia', 
            'Descripción': 'Descripcion', 
            'Costo': 'Costo', 
            'Empresa': 'Empresa', 
            'Fase de Tesis': 'Fase',
            'Producto': 'Producto'
        }
        
        existing_cols = {k: v for k, v in cols_map.items() if k in df.columns}
        df_final = df[list(existing_cols.keys())].copy()
        df_final.rename(columns=existing_cols, inplace=True)
        
        df_final['Familia'] = df_final['Familia'].astype(str).str.strip()
        df_final = df_final[~df_final['Familia'].str.contains("Total|Subtotal|nan|0", case=False, na=False)]
        df_final['Costo'] = pd.to_numeric(df_final['Costo'], errors='coerce').fillna(0)
        df_final = df_final[df_final['Costo'] > 0]
        
        if 'Fase' not in df_final.columns: df_final['Fase'] = 'Sin asignar'
        if 'Producto' not in df_final.columns: df_final['Producto'] = 'Sin categoría'
        
        df_final['Estado'] = 'En proceso de solicitud de compra'
        df_final['Notas'] = ''
        if os.path.exists(db_file):
            df_saved = pd.read_csv(db_file)
            df_final = df_final.drop(columns=['Estado', 'Notas']).merge(
                df_saved[['Descripcion', 'Estado', 'Notas']], on='Descripcion', how='left'
            )
            df_final['Estado'] = df_final['Estado'].fillna('En proceso de solicitud de compra')
            df_final['Notas'] = df_final['Notas'].fillna('')
        return df_final
    except: return pd.DataFrame()

if 'df_pro' not in st.session_state:
    st.session_state.df_pro = load_institutional_data()

# 3. SIDEBAR (CON BLOQUEO DE CONTRASEÑA AGREGADO)
st.sidebar.title("🔐 Acceso de Editor")

# Definir la clave (puedes cambiar "rz2026" por lo que desees)
try:
    master_key = st.secrets["ADMIN_TOKEN"]
except:
    master_key = "rz2026" 

pass_input = st.sidebar.text_input("Ingresar Clave:", type="password")
es_admin = (pass_input == master_key)

if es_admin:
    st.sidebar.success("🔓 MODO EDITOR ACTIVO")
else:
    st.sidebar.info("👁️ MODO LECTURA")

st.sidebar.divider()
st.sidebar.title("🔍 Inteligencia de Datos")
termino = st.sidebar.text_input("Buscar ítem:", "")
familias = st.session_state.df_pro['Familia'].unique()
familia_sel = st.sidebar.multiselect("Filtrar por Familia:", familias, default=familias)

df_visible = st.session_state.df_pro.copy()
df_visible = df_visible[df_visible['Familia'].isin(familia_sel)]
if termino:
    df_visible = df_visible[df_visible['Descripcion'].str.contains(termino, case=False, na=False)]

# 4. ENCABEZADO
st.markdown(f"""
    <div class="header-box">
        <div class="thesis-title">Proyecto: Evaluación in vitro de la actividad antitumoral de moléculas sintéticas con potencial de reposicionamiento y compuestos fitoquímicos frente a mutaciones de resistencia en la proteína ALK</div>
        <div class="project-info">
            <b>PROCIENCIA - CONCYTEC</b> | <b>Contrato:</b> PE501092173-2024 / E077-2023-01-BM-V2<br>
            <b>Doctorando:</b> Richard Junior Zapata Dongo | <b>Actualizado:</b> {datetime.now().strftime('%d/%m/%Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. DASHBOARD BI
if not st.session_state.df_pro.empty:
    tot = st.session_state.df_pro['Costo'].sum()
    pagado = st.session_state.df_pro[st.session_state.df_pro['Estado'].str.contains('Comprado')]['Costo'].sum()

    col_gauge, col_m1 = st.columns([1.5, 2])
    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = pagado,
            title = {'text': "Ejecución Presupuestal (S/)", 'font': {'size': 16}},
            gauge = {'axis': {'range': [None, tot]}, 'bar': {'color': "#1e3a8a"},
                     'steps': [{'range': [0, tot*0.5], 'color': '#fee2e2'}, {'range': [tot*0.5, tot*0.8], 'color': '#fef3c7'}, {'range': [tot*0.8, tot], 'color': '#dcfce7'}]}))
        fig_gauge.update_layout(height=220, margin=dict(t=0, b=0, l=10, r=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_m1:
        k1, k2 = st.columns(2)
        k1.metric("PRESUPUESTO TOTAL", f"S/ {tot:,.2f}")
        k2.metric("PAGADO/COMPROMETIDO", f"S/ {pagado:,.2f}")
        k3, k4 = st.columns(2)
        k3.metric("SALDO DISPONIBLE", f"S/ {tot - pagado:,.2f}", delta_color="inverse")
        k4.metric("AVANCE %", f"{(pagado/tot*100):.1f}%")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📝 Gestión Administrativa", "📊 Análisis Financiero", "📊 Riesgos", 
        "🎯 Proyecciones", "🛡️ Auditoría y Eficiencia", "🔬 Avance por Fases de Tesis", "📦 Desglose por Producto"
    ])

    with tab1:
        st.subheader("Planilla de Control y Seguimiento")
        opciones = ["Comprado y entregado", "Comprado y en proceso de entrega", "En proceso de compra", "En proceso de Aprobación para Compra", "En proceso de solicitud de compra"]
        
        # EL EDITOR SE BLOQUEA SI NO ES ADMIN
        edited_df = st.data_editor(
            df_visible, 
            column_config={
                "Estado": st.column_config.SelectboxColumn("Estado", options=opciones, required=True), 
                "Costo": st.column_config.NumberColumn("Presupuesto", format="S/ %.2f"), 
                "Descripcion": st.column_config.TextColumn("Ítem", width="large")
            }, 
            disabled=["Item", "Familia", "Descripcion", "Costo"] if es_admin else df_visible.columns, 
            hide_index=True, 
            use_container_width=True
        )
        
        col_btn, col_exp = st.columns([1,1])
        with col_btn:
            # EL BOTÓN SOLO APARECE SI ES ADMIN
            if es_admin:
                if st.button("💾 GUARDAR CAMBIOS PERMANENTES"):
                    for _, row in edited_df.iterrows():
                        idx = st.session_state.df_pro[st.session_state.df_pro['Descripcion'] == row['Descripcion']].index
                        st.session_state.df_pro.loc[idx, 'Estado'] = row['Estado']
                    st.session_state.df_pro.to_csv('seguimiento_rzd.csv', index=False)
                    st.success("✅ Datos grabados.")
                    st.rerun()
            else:
                st.warning("⚠️ Ingrese la clave en la barra lateral para habilitar el guardado.")

        with col_exp:
            csv = st.session_state.df_pro.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte (CSV)", data=csv, file_name=f"Reporte_RZD_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')

    with tab2:
        color_map_tab2 = {"Comprado y entregado": "#064e3b", "Comprado y en proceso de entrega": "#10b981", "En proceso de compra": "#f59e0b", "En proceso de Aprobación para Compra": "#3b82f6", "En proceso de solicitud de compra": "#6366f1"}
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(st.session_state.df_pro, values='Costo', names='Estado', hole=0.5, color='Estado', color_discrete_map=color_map_tab2), use_container_width=True)
        with c2: st.plotly_chart(px.bar(st.session_state.df_pro, x='Familia', y='Costo', color='Estado', color_discrete_map=color_map_tab2, barmode='stack', text_auto='.2s'), use_container_width=True)
        st.plotly_chart(px.treemap(st.session_state.df_pro, path=['Familia', 'Descripcion'], values='Costo', color='Costo', color_continuous_scale='Blues'), use_container_width=True)

    with tab3:
        st.subheader("Análisis de Riesgos e Impacto")
        c1, c2 = st.columns(2)
        with c1:
            df_p = st.session_state.df_pro.sort_values(by='Costo', ascending=False).head(10)
            st.plotly_chart(px.bar(df_p, x='Costo', y='Descripcion', orientation='h', color='Costo', color_continuous_scale='Reds'), use_container_width=True)
        with c2:
            if 'Empresa' in st.session_state.df_pro.columns:
                df_emp = st.session_state.df_pro.groupby('Empresa')['Costo'].sum().reset_index()
                st.plotly_chart(px.funnel(df_emp.sort_values(by='Costo', ascending=False).head(10), x='Costo', y='Empresa'), use_container_width=True)

    with tab4:
        st.subheader("🎯 Proyecciones de Cierre Presupuestal")
        df_gap = st.session_state.df_pro.copy()
        df_gap['Falta'] = df_gap.apply(lambda x: x['Costo'] if 'Comprado' not in x['Estado'] else 0, axis=1)
        resumen_gap = df_gap.groupby('Familia').agg({'Costo': 'sum', 'Falta': 'sum'}).reset_index()
        resumen_gap['Avance %'] = ((1 - resumen_gap['Falta']/resumen_gap['Costo'])*100).round(1)
        st.table(resumen_gap.style.format({'Costo': 'S/ {:,.2f}', 'Falta': 'S/ {:,.2f}', 'Avance %': '{:.1f}%'}))
        
        st.plotly_chart(px.scatter(
            st.session_state.df_pro, 
            x="Costo", 
            y="Estado", 
            size="Costo", 
            color="Fase", 
            hover_name="Descripcion", 
            size_max=60,
            color_discrete_map={"Fase II": "#10b981", "Fase III": "#f59e0b", "Sin asignar": "#94a3b8"},
            title="Distribución de Carga Financiera por Fase y Estado"
        ), use_container_width=True)

    with tab5:
        st.subheader("🛡️ Auditoría y Eficiencia (Radar BI)")
        col_aud1, col_aud2 = st.columns(2)
        with col_aud1:
            res_fam = st.session_state.df_pro.groupby('Familia').agg({'Costo': 'sum'})
            pag_fam = st.session_state.df_pro[st.session_state.df_pro['Estado'].str.contains('Comprado')].groupby('Familia').agg({'Costo': 'sum'})
            eficiencia = (pag_fam / res_fam * 100).fillna(0)
            eficiencia.columns = ['% Eficiencia']
            st.dataframe(eficiencia.style.background_gradient(cmap='RdYlGn', vmin=0, vmax=100).format("{:.1f}%"))
        with col_aud2:
            st.write("**Equilibrio de Inversión por Producto**")
            res_prod_radar = st.session_state.df_pro.groupby('Producto')['Costo'].sum().reset_index()
            radar_close = pd.concat([res_prod_radar, res_prod_radar.iloc[[0]]])
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_close['Costo'], theta=radar_close['Producto'], fill='toself', line_color='#1e3a8a'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, showticklabels=True, tickfont=dict(size=9)),
                    angularaxis=dict(tickfont=dict(size=12, color='#1e3a8a'))
                ),
                showlegend=False, height=450, margin=dict(t=40, b=40, l=80, r=80)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with tab6:
        st.subheader("🔬 Coherencia de Gasto vs Avance de Tesis")
        df_fase = st.session_state.df_pro.copy()
        df_fase['Situación'] = df_fase['Estado'].apply(lambda x: 'Ejecutado' if 'Comprado' in x else 'Pendiente')
        c1, c2 = st.columns([1.5, 1])
        with c1: st.plotly_chart(px.bar(df_fase, x='Fase', y='Costo', color='Situación', barmode='group', color_discrete_map={'Ejecutado': '#064e3b', 'Pendiente': '#6366f1'}, text_auto='.2s'), use_container_width=True)
        with c2: 
            res_fase_tab = df_fase.pivot_table(index='Fase', columns='Situación', values='Costo', aggfunc='sum', fill_value=0).reset_index()
            st.table(res_fase_tab.style.format({'Ejecutado': 'S/ {:,.2f}', 'Pendiente': 'S/ {:,.2f}'}))
        
        st.divider()
        st.subheader("🚨 Detalle de Insumos Pendientes Segmentados por Fase")
        fases_list = sorted(df_fase['Fase'].unique())
        for f_item in fases_list:
            df_faltantes = df_fase[(df_fase['Fase'] == f_item) & (df_fase['Situación'] == 'Pendiente')].copy()
            if not df_faltantes.empty:
                with st.expander(f"🛒 PENDIENTES: {f_item.upper()}", expanded=(f_item == 'Fase II')):
                    st.dataframe(df_faltantes[['Producto', 'Descripcion', 'Costo', 'Estado']].sort_values(by='Costo', ascending=False), hide_index=True, use_container_width=True)
                    st.info(f"Subtotal crítico {f_item}: S/ {df_faltantes['Costo'].sum():,.2f}")

    with tab7:
        st.subheader("📦 Clasificación Presupuestal por Tipo de Producto")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(st.session_state.df_pro, values='Costo', names='Producto', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism), use_container_width=True)
        with c2: 
            df_prod_sum = st.session_state.df_pro.groupby('Producto')['Costo'].sum().reset_index().sort_values(by='Costo', ascending=True)
            st.plotly_chart(px.bar(df_prod_sum, x='Costo', y='Producto', orientation='h', color='Costo', color_continuous_scale='Viridis', text_auto='.2s'), use_container_width=True)
        st.plotly_chart(px.treemap(st.session_state.df_pro, path=['Familia', 'Producto', 'Descripcion'], values='Costo', color='Producto', color_discrete_sequence=px.colors.qualitative.Bold), use_container_width=True)

    # 6. FOOTER
    st.markdown("""
        <div class="footer-min">
            <div class="footer-grid">
                <div class="footer-item"><span class="footer-label">Asesor</span> Dr. Juan Pedro Rojas Armas</div>
                <div class="footer-item"><span class="footer-label">Coordinador Académico</span> Dr. Jaeson Calla</div>
                <div class="footer-item"><span class="footer-label">Coordinadora Administrativa</span> Viviana Pérez Orellana</div>
                <div class="footer-item"><span class="footer-label">Monitora Prociencia</span> Dra. Giuliana Díaz Pérez</div>
            </div>
            <div class="copyright">© 2026 Richard Junior Zapata Dongo | Gestión Institucional PROCIENCIA - UNMSM</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("Archivo 'Zapata Richard.xlsx' no detectado.")
