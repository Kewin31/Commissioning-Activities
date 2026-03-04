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
        # Caminho correto para o arquivo na pasta .Dados
        caminho_arquivo = os.path.join('.Dados', 'Comissionamento AD - UNs.csv')
        
        st.write(f"🔍 Procurando arquivo em: {caminho_arquivo}")
        
        # Verificar se a pasta existe
        if not os.path.exists('.Dados'):
            st.error(f"❌ Pasta '.Dados' não encontrada!")
            st.write("Pastas disponíveis:")
            for item in os.listdir('.'):
                if os.path.isdir(item):
                    st.write(f"📁 {item}")
            return None
        
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            st.error(f"❌ Arquivo não encontrado em: {caminho_arquivo}")
            st.write(f"Arquivos na pasta '.Dados':")
            if os.path.exists('.Dados'):
                for arquivo in os.listdir('.Dados'):
                    st.write(f"📄 {arquivo}")
            return None
        
        # Tentar diferentes encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=encoding)
                st.success(f"✅ Arquivo carregado com encoding: {encoding}")
                break
            except UnicodeDecodeError:
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
if df is not None:
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
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Equipamentos", len(df_filtrado))
    with col2:
        st.metric("EMT", len(df_filtrado[df_filtrado['Empresa'] == 'EMT']))
    with col3:
        st.metric("ETO", len(df_filtrado[df_filtrado['Empresa'] == 'ETO']))
    
    # Tabela
    st.subheader("📋 Registros")
    st.dataframe(
        df_filtrado[['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                    'Responsável Desenvolvimento', 'Status', 'Empresa']],
        use_container_width=True,
        hide_index=True
    )
    
else:
    st.warning("⚠️ Não foi possível carregar os dados. Verifique se o arquivo CSV está na pasta '.Dados'.")
