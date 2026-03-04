import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Comissionamento",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Dashboard de Acompanhamento de Comissionamento")
st.markdown("---")

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        # Caminho do arquivo (agora sabemos que funciona!)
        caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        
        # Ler o arquivo
        df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
        
        # Tratar campos vazios
        df['Responsável Desenvolvimento'] = df['Responsável Desenvolvimento'].fillna('Não atribuído')
        df['Responsável Auditoria'] = df['Responsável Auditoria'].fillna('Não atribuído')
        df['Status'] = df['Status'].fillna('Pendente')
        
        # Converter datas
        df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

if df is not None:
    # Sidebar - Filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtros na sidebar
    empresas = st.sidebar.multiselect(
        "Empresa",
        options=sorted(df['Empresa'].unique()),
        default=sorted(df['Empresa'].unique())
    )
    
    tipos_equip = st.sidebar.multiselect(
        "Tipo de Equipamento",
        options=sorted(df['Tipo Equipamento'].unique()),
        default=sorted(df['Tipo Equipamento'].unique())
    )
    
    status_opcoes = st.sidebar.multiselect(
        "Status",
        options=sorted(df['Status'].unique()),
        default=sorted(df['Status'].unique())
    )
    
    responsaveis_dev = st.sidebar.multiselect(
        "Responsável Desenvolvimento",
        options=sorted(df['Responsável Desenvolvimento'].unique()),
        default=[]
    )
    
    # Aplicar filtros
    df_filtrado = df[
        (df['Empresa'].isin(empresas)) &
        (df['Tipo Equipamento'].isin(tipos_equip)) &
        (df['Status'].isin(status_opcoes))
    ]
    
    if responsaveis_dev:
        df_filtrado = df_filtrado[df_filtrado['Responsável Desenvolvimento'].isin(responsaveis_dev)]
    
    # Métricas principais
    st.subheader("📊 Visão Geral")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Equipamentos", len(df_filtrado))
    
    with col2:
        st.metric("EMT", len(df_filtrado[df_filtrado['Empresa'] == 'EMT']))
    
    with col3:
        st.metric("ETO", len(df_filtrado[df_filtrado['Empresa'] == 'ETO']))
    
    with col4:
        qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
        st.metric("Desenvolvidos", qtd_desenvolvidos)
    
    with col5:
        qtd_pendentes = len(df_filtrado[df_filtrado['Status'] != 'Desenvolvido'])
        st.metric("Pendentes", qtd_pendentes)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        status_counts = df_filtrado['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(status_counts, values='Quantidade', names='Status',
                           title='Distribuição por Status',
                           color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        tipo_counts = df_filtrado['Tipo Equipamento'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo Equipamento', 'Quantidade']
        fig_tipo = px.bar(tipo_counts, x='Tipo Equipamento', y='Quantidade',
                         title='Distribuição por Tipo de Equipamento',
                         color='Tipo Equipamento',
                         color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    # Gráfico de responsáveis
    st.subheader("👥 Desempenho por Responsável")
    resp_counts = df_filtrado['Responsável Desenvolvimento'].value_counts().reset_index()
    resp_counts.columns = ['Responsável', 'Quantidade']
    resp_counts = resp_counts[resp_counts['Responsável'] != 'Não atribuído']
    
    if not resp_counts.empty:
        fig_resp = px.bar(resp_counts.head(10), 
                         x='Quantidade', 
                         y='Responsável',
                         title='Top 10 Responsáveis',
                         orientation='h',
                         color='Quantidade',
                         color_continuous_scale='Viridis')
        st.plotly_chart(fig_resp, use_container_width=True)
    else:
        st.info("Nenhum responsável atribuído")
    
    st.markdown("---")
    
    # Tabela detalhada
    st.subheader("📋 Detalhamento dos Registros")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        colunas_padrao = ['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                         'Responsável Desenvolvimento', 'Status', 'Empresa']
        mostrar_colunas = st.multiselect(
            "Colunas para exibir",
            options=df_filtrado.columns.tolist(),
            default=[col for col in colunas_padrao if col in df_filtrado.columns]
        )
    
    with col2:
        search = st.text_input("🔍 Buscar por código do equipamento ou chamado")
    
    if search:
        df_filtrado = df_filtrado[
            df_filtrado['Cód. Equipamento'].astype(str).str.contains(search, case=False) |
            df_filtrado['Chamado Desenvolvimento'].astype(str).str.contains(search, case=False)
        ]
    
    if mostrar_colunas:
        st.dataframe(
            df_filtrado[mostrar_colunas],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YYYY HH:mm"),
                "Modificado": st.column_config.DatetimeColumn("Modificado", format="DD/MM/YYYY HH:mm")
            }
        )
    
    # Estatísticas adicionais
    st.markdown("---")
    st.subheader("📈 Estatísticas Detalhadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_filtrado.empty:
            cross_tab = pd.crosstab(df_filtrado['Empresa'], df_filtrado['Status'])
            st.write("**Distribuição Empresa vs Status**")
            st.dataframe(cross_tab, use_container_width=True)
    
    with col2:
        if not df_filtrado.empty:
            cross_tab_tipo = pd.crosstab(df_filtrado['Tipo Equipamento'], df_filtrado['Status'])
            st.write("**Distribuição Tipo vs Status**")
            st.dataframe(cross_tab_tipo, use_container_width=True)
    
    # Exportar dados
    st.markdown("---")
    st.subheader("📥 Exportar Dados")
    
    csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download dos dados filtrados (CSV)",
        data=csv,
        file_name=f"comissionamento_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

else:
    st.error("❌ Não foi possível carregar os dados")
