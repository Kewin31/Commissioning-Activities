import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os

st.set_page_config(page_title="Dashboard de Comissionamento", page_icon="⚡", layout="wide")
st.title("⚡ Dashboard de Acompanhamento de Comissionamento")

@st.cache_data
def load_data():
    try:
        # Caminho ajustado para sua estrutura atual
        caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        
        st.write(f"🔍 Procurando arquivo em: {caminho_arquivo}")
        
        # Debug: listar diretórios
        st.write("📁 Estrutura de diretórios:")
        for root, dirs, files in os.walk('.'):
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 2 * level
            st.write(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Mostra só os primeiros 5 arquivos
                st.write(f"{subindent}{file}")
        
        if not os.path.exists(caminho_arquivo):
            st.error(f"❌ Arquivo não encontrado!")
            return None
        
        # Tentar ler o arquivo
        df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
        st.success("✅ Arquivo carregado com sucesso!")
        
        # Processar dados
        df['Responsável Desenvolvimento'] = df['Responsável Desenvolvimento'].fillna('Não atribuído')
        df['Status'] = df['Status'].fillna('Pendente')
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        return None

df = load_data()

if df is not None:
    st.write(f"Total de registros: {len(df)}")
    st.dataframe(df.head())
else:
    st.warning("⚠️ Arquivo não encontrado. Verifique o caminho.")
