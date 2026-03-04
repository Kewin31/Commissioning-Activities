import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import sys

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Comissionamento",
    page_icon="⚡",
    layout="wide"
)

# Título
st.title("⚡ Dashboard de Acompanhamento de Comissionamento")

# Função para carregar os dados com tratamento de erro
@st.cache_data
def load_data():
    try:
        # Tentar diferentes encodings
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv('Comissionamento AD - UNs.csv', encoding=encoding)
                print(f"Arquivo lido com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        # Se não conseguir ler, mostrar erro
        if df is None:
            st.error("Não foi possível ler o arquivo CSV. Verifique o encoding.")
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
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

# Resto do seu código continua aqui...
# (Cole o resto do código que te passei anteriormente)
