import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Comissionamento",
    page_icon="⚡",
    layout="wide"
)

# Título principal
st.title("⚡ Dashboard de Acompanhamento de Comissionamento")
st.markdown("---")

# Função para carregar os dados
@st.cache_data
def load_data():
    # Carregar o arquivo CSV
    df = pd.read_csv('Comissionamento AD - UNs.csv', encoding='utf-8')
    
    # Tratar campos vazios
    df['Responsável Desenvolvimento'] = df['Responsável Desenvolvimento'].fillna('Não atribuído')
    df['Responsável Auditoria'] = df['Responsável Auditoria'].fillna('Não atribuído')
    df['Status'] = df['Status'].fillna('Pendente')
    
    # Converter datas
    df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M')
    df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M')
    
    return df

try:
    df = load_data()
    
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
    
    # Métricas principais em cards
    st.subheader("📊 Visão Geral")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Equipamentos", len(df_filtrado))
    
    with col2:
        st.metric("Equipamentos EMT", len(df_filtrado[df_filtrado['Empresa'] == 'EMT']))
    
    with col3:
        st.metric("Equipamentos ETO", len(df_filtrado[df_filtrado['Empresa'] == 'ETO']))
    
    with col4:
        qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
        st.metric("Desenvolvidos", qtd_desenvolvidos)
    
    with col5:
        qtd_pendentes = len(df_filtrado[df_filtrado['Status'] != 'Desenvolvido'])
        st.metric("Pendentes", qtd_pendentes)
    
    st.markdown("---")
    
    # Gráficos em duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza por Status
        status_counts = df_filtrado['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        
        fig_status = px.pie(
            status_counts, 
            values='Quantidade', 
            names='Status',
            title='Distribuição por Status',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Gráfico de barras por Tipo de Equipamento
        tipo_counts = df_filtrado['Tipo Equipamento'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo Equipamento', 'Quantidade']
        
        fig_tipo = px.bar(
            tipo_counts, 
            x='Tipo Equipamento', 
            y='Quantidade',
            title='Distribuição por Tipo de Equipamento',
            color='Tipo Equipamento',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    # Segunda linha de gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico por Responsável
        resp_counts = df_filtrado['Responsável Desenvolvimento'].value_counts().reset_index()
        resp_counts.columns = ['Responsável', 'Quantidade']
        resp_counts = resp_counts[resp_counts['Responsável'] != 'Não atribuído']
        
        fig_resp = px.bar(
            resp_counts.head(10), 
            x='Quantidade', 
            y='Responsável',
            title='Top 10 Responsáveis por Desenvolvimento',
            orientation='h',
            color='Quantidade',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_resp, use_container_width=True)
    
    with col2:
        # Gráfico de linha temporal
        df_filtrado['Data_Criacao'] = df_filtrado['Criado'].dt.date
        timeline = df_filtrado.groupby('Data_Criacao').size().reset_index(name='Quantidade')
        timeline = timeline.sort_values('Data_Criacao')
        
        fig_timeline = px.line(
            timeline, 
            x='Data_Criacao', 
            y='Quantidade',
            title='Registros por Dia',
            markers=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela detalhada
    st.subheader("📋 Detalhamento dos Registros")
    
    # Opções de visualização
    col1, col2 = st.columns([1, 3])
    with col1:
        mostrar_colunas = st.multiselect(
            "Colunas para exibir",
            options=df_filtrado.columns.tolist(),
            default=['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                    'Responsável Desenvolvimento', 'Status', 'Empresa']
        )
    
    with col2:
        search = st.text_input("🔍 Buscar por código do equipamento ou chamado")
    
    # Filtrar por busca
    if search:
        df_filtrado = df_filtrado[
            df_filtrado['Cód. Equipamento'].astype(str).str.contains(search, case=False) |
            df_filtrado['Chamado Desenvolvimento'].astype(str).str.contains(search, case=False)
        ]
    
    # Exibir tabela
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
        # Tabela cruzada Empresa vs Status
        cross_tab = pd.crosstab(df_filtrado['Empresa'], df_filtrado['Status'])
        st.write("**Distribuição Empresa vs Status**")
        st.dataframe(cross_tab, use_container_width=True)
    
    with col2:
        # Tabela cruzada Tipo vs Status
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

except FileNotFoundError:
    st.error("❌ Arquivo 'Comissionamento AD - UNs.csv' não encontrado. Verifique se o arquivo está no mesmo diretório do script.")
except Exception as e:
    st.error(f"❌ Erro ao carregar os dados: {str(e)}")
