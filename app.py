import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard de Comissionamento", page_icon="⚡", layout="wide")
st.title("⚡ Dashboard de Acompanhamento de Comissionamento")

st.subheader("🔍 Diagnóstico de Arquivos")

# Listar TODOS os arquivos e pastas
st.write("**Conteúdo completo do repositório:**")
for root, dirs, files in os.walk('.'):
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 2 * level
    st.write(f"{indent}📁 {os.path.basename(root) or '.'}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        st.write(f"{subindent}📄 {file}")

# Caminhos alternativos para tentar
caminhos_tentar = [
    os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv'),
    os.path.join('Dados', 'Comissionamento AD - UNs.csv'),
    'Comissionamento AD - UNs.csv',
    os.path.join('data', 'Comissionamento AD - UNs.csv'),
]

st.subheader("🔎 Procurando arquivo CSV:")
arquivo_encontrado = None

for caminho in caminhos_tentar:
    st.write(f"Tentando: {caminho}")
    if os.path.exists(caminho):
        st.success(f"✅ ENCONTRADO: {caminho}")
        arquivo_encontrado = caminho
        break

if arquivo_encontrado:
    try:
        df = pd.read_csv(arquivo_encontrado, encoding='utf-8-sig')
        st.success(f"✅ CSV carregado! {len(df)} registros encontrados.")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Erro ao ler CSV: {e}")
else:
    st.error("❌ Arquivo CSV não encontrado em nenhum caminho!")
