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

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        # Caminho correto para o arquivo na pasta Dados
        caminho_arquivo = os.path.join('Dados', 'Comissionamento AD - UNs.csv')
        
        st.write(f"🔍 Procurando arquivo em: {caminho_arquivo}")
        
        # Verificar se a pasta existe
        if not os.path.exists('Dados'):
            st.error(f"❌ Pasta 'Dados' não encontrada!")
            st.write("Pastas disponíveis na raiz:")
            for item in os.listdir('.'):
                if os.path.isdir(item):
                    st.write(f"📁 {item}")
            return None
        
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            st.error(f"❌ Arquivo não encontrado em: {caminho_arquivo}")
            st.write(f"Arquivos na pasta 'Dados':")
            if os.path.exists('Dados'):
                for arquivo in os.listdir('Dados'):
                    st.write(f"📄 {arquivo}")
            return None
        
        # Tentar diferentes encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=encoding)
                st.success(f"✅ Arquivo carregado com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                st.error(f"Erro com encoding {encoding}: {str(e)}")
                continue
        
        if df is None:
            st.error("❌ Não foi possível ler o arquivo com nenhum encoding")
            return None
            
        # Tratar campos vazios
        df['Responsável Desenvolvimento'] = df['Responsável Desenvolvimento'].fillna('Não atribuído')
        df['Responsável Auditoria'] = df['Responsável Auditoria'].fillna('Não atribuído')
        df['Status'] = df['Status'].fillna('Pendente')
        
        # Converter datas
        df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

# Se carregou com sucesso, mostrar o dashboard
if df is not None and not df.empty:
    st.success("✅ Dados carregados com sucesso!")
    st.write(f"Total de registros: {len(df)}")
    
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
    
    # Aplicar filtros
    df_filtrado = df[
        (df['Empresa'].isin(empresas)) &
        (df['Tipo Equipamento'].isin(tipos_equip)) &
        (df['Status'].isin(status_opcoes))
    ]
    
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
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza por Status
        status_counts = df_filtrado['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(status_counts, values='Quantidade', names='Status', 
                           title='Distribuição por Status')
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Gráfico de barras por Tipo
        tipo_counts = df_filtrado['Tipo Equipamento'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo Equipamento', 'Quantidade']
        fig_tipo = px.bar(tipo_counts, x='Tipo Equipamento', y='Quantidade',
                         title='Distribuição por Tipo de Equipamento')
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("📋 Detalhamento dos Registros")
    st.dataframe(
        df_filtrado[['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                    'Responsável Desenvolvimento', 'Status', 'Empresa', 'Criado']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Criado": st.column_config.DatetimeColumn("Criado", format="DD/MM/YYYY HH:mm")
        }
    )
    
else:
    st.warning("⚠️ Não foi possível carregar os dados. Verifique se:")
    st.warning("1. A pasta 'Dados' existe no repositório")
    st.warning("2. O arquivo 'Comissionamento AD - UNs.csv' está dentro da pasta 'Dados'")
    st.warning("3. O arquivo não está corrompido")
