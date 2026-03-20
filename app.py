import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
import io
import base64
from github import Github
from github import GithubException
import tempfile
import time
from dateutil.relativedelta import relativedelta

# Configuração da página
st.set_page_config(
    page_title="Dashboard Executivo | Fábrica SCADA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNÇÕES DE FORMATAÇÃO
# ============================================
def formatar_data_portugues(data, formato='completo'):
    """Formata datas em português"""
    if pd.isna(data):
        return ""
    
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    if formato == 'mes_ano':
        return f"{meses_pt[data.month]}/{data.year}"
    elif formato == 'ano_mes':
        return f"{data.year}/{data.month:02d}"
    else:
        return data.strftime('%d/%m/%Y')

def get_logo_base64():
    """Converte a logo para base64 para exibição"""
    possiveis_nomes = [
        "Logo_Energisa.png",
        "logo_energisa.png",
        "Logo_Energisa.gif",
        "Selo120_Azul_GIF_FundoTransparente novo.gif",
        "energisa.png"
    ]
    
    for logo_path in possiveis_nomes:
        try:
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_bytes = f.read()
                if logo_path.lower().endswith('.png'):
                    mime_type = "image/png"
                elif logo_path.lower().endswith('.gif'):
                    mime_type = "image/gif"
                else:
                    mime_type = "image/png"
                
                return base64.b64encode(logo_bytes).decode(), mime_type
        except:
            continue
    
    return None, None

# ============================================
# CONFIGURAÇÕES DO GITHUB
# ============================================
def get_github_config():
    """Obtém configurações do GitHub do Streamlit Secrets"""
    try:
        if "GITHUB_TOKEN" not in st.secrets:
            return None, None, None
            
        token = st.secrets["GITHUB_TOKEN"]
        
        if "GITHUB_REPO" not in st.secrets:
            return token, None, None
            
        repo = st.secrets["GITHUB_REPO"]
        
        if '/' not in repo:
            return token, None, None
            
        file_path = st.secrets.get("GITHUB_FILE_PATH", "data/Dados/Comissionamento AD - UNs.csv")
        
        return token, repo, file_path
        
    except Exception as e:
        return None, None, None

def test_github_connection():
    """Testa a conexão com o GitHub com tratamento de erro 401"""
    try:
        token, repo_name, _ = get_github_config()
        
        if not token or not repo_name:
            return False, "Configurações incompletas"
        
        g = Github(token)
        user = g.get_user()
        
        try:
            repo = g.get_repo(repo_name)
            return True, f"Conectado como {user.login}"
        except GithubException as e:
            if e.status == 401:
                return False, "❌ Token inválido ou expirado. Configure um novo token."
            elif e.status == 404:
                return False, f"❌ Repositório '{repo_name}' não encontrado."
            else:
                return False, f"❌ Erro GitHub: {e.status}"
        
    except GithubException as e:
        if e.status == 401:
            return False, "❌ Token inválido ou expirado. Configure um novo token."
        return False, f"❌ Erro de conexão: {str(e)}"
    except Exception as e:
        return False, f"❌ Erro: {str(e)}"

def load_data_from_github():
    """Carrega dados do GitHub com tratamento de erro 401"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            return None
        
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
            contents = repo.get_contents(file_path)
            
            file_content = base64.b64decode(contents.content).decode('utf-8')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(file_content)
                temp_file = f.name
            
            df = pd.read_csv(temp_file, encoding='utf-8-sig')
            os.unlink(temp_file)
            
            return df
            
        except GithubException as e:
            if e.status == 401:
                st.warning("⚠️ Token GitHub inválido. Usando dados locais.")
                return None
            elif e.status == 404:
                st.warning("⚠️ Arquivo não encontrado no GitHub. Usando dados locais.")
                return None
            else:
                st.warning(f"⚠️ Erro GitHub: {e.status}. Usando dados locais.")
                return None
                
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar do GitHub: {str(e)}. Usando dados locais.")
        return None

def atualizar_dados_github(arquivo_upload, branch="main"):
    """Atualiza o arquivo no GitHub"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            st.error("❌ Configurações do GitHub incompletas.")
            return False
        
        if arquivo_upload is None:
            st.error("❌ Nenhum arquivo selecionado.")
            return False
        
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
            if e.status == 401:
                st.error("❌ Token inválido ou expirado. Configure um novo token.")
                return False
            elif e.status == 404:
                st.error(f"❌ Repositório '{repo_name}' não encontrado.")
                return False
            else:
                st.error(f"❌ Erro GitHub: {e.status}")
                return False
        
        file_content = arquivo_upload.read()
        
        try:
            contents = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                path=file_path,
                message=f"📦 Atualização - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                content=file_content,
                sha=contents.sha,
                branch=branch
            )
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=file_path,
                    message=f"📦 Criação - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    content=file_content,
                    branch=branch
                )
            else:
                raise e
        
        st.success(f"✅ Arquivo atualizado no GitHub!")
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao atualizar GitHub: {str(e)}")
        return False

# ============================================
# CSS PERSONALIZADO - ESTILO ENERGISA
# ============================================
st.markdown("""
<style>
    /* Fontes e reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f0f9ff 0%, #e6f3f5 100%);
    }
    
    /* Header executivo com gradiente Energisa */
    .header-executivo {
        background: linear-gradient(135deg, #005973 0%, #028a9f 50%, #04d8d7 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 20px rgba(0,89,115,0.2);
    }
    
    .header-conteudo {
        display: flex;
        align-items: center;
        gap: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .header-logo {
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .header-logo img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
    
    .header-titulo h1 {
        color: white;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.02em;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .header-titulo p {
        color: rgba(255,255,255,0.9);
        margin: 0.2rem 0 0 0;
        font-size: 0.95rem;
    }
    
    .header-data {
        margin-left: auto;
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: 30px;
        color: white;
        font-size: 0.9rem;
        backdrop-filter: blur(5px);
    }
    
    /* Cards de métricas - Estilo Energisa */
    .metric-card-executivo {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,89,115,0.08);
        border: 1px solid rgba(4,216,215,0.2);
        transition: all 0.2s ease;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card-executivo:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,89,115,0.15);
        border-color: #04d8d7;
    }
    
    .metric-card-executivo::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #005973, #04d8d7);
    }
    
    .metric-titulo {
        color: #2c5f6b;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-valor {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.2;
        color: #005973;
    }
    
    .metric-sub {
        color: #5f8b94;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    
    .metric-tendencia {
        position: absolute;
        top: 1rem;
        right: 1rem;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .tendencia-positiva {
        background: #e0f7fa;
        color: #006c84;
    }
    
    .tendencia-negativa {
        background: #ffe6e6;
        color: #c62828;
    }
    
    /* Cards de fluxo */
    .fluxo-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,89,115,0.08);
        margin-bottom: 2rem;
        border: 1px solid rgba(4,216,215,0.2);
        transition: all 0.2s;
    }
    
    .fluxo-container:hover {
        box-shadow: 0 8px 25px rgba(0,89,115,0.12);
        border-color: #04d8d7;
    }
    
    /* Cards comparativos */
    .company-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,89,115,0.08);
        height: 100%;
        border: 1px solid rgba(4,216,215,0.2);
        transition: all 0.2s;
    }
    
    .company-card:hover {
        box-shadow: 0 8px 25px rgba(0,89,115,0.12);
        border-color: #04d8d7;
    }
    
    .company-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0f7fa;
    }
    
    .company-metric {
        text-align: center;
        padding: 0.5rem;
    }
    
    .company-metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .company-metric-label {
        font-size: 0.8rem;
        color: #5f8b94;
        margin-top: 0.3rem;
    }
    
    .badge-status {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-desenvolvido { background: #E8F5E9; color: #2E7D32; }
    .badge-comissionado { background: #E0F7FA; color: #006c84; }
    .badge-validado { background: #E8EAF6; color: #283593; }
    .badge-revisao { background: #FFF3E0; color: #F57C00; }
    .badge-pendente { background: #FFEBEE; color: #C62828; }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
        padding: 0.5rem 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #2c5f6b;
    }
    
    .stTabs [aria-selected="true"] {
        color: #005973;
        border-bottom-color: #04d8d7;
    }
    
    /* Footer */
    .footer {
        background: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-top: 3rem;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.02);
        font-size: 0.85rem;
        color: #5f8b94;
        border-top: 1px solid rgba(4,216,215,0.3);
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #005973, #028a9f);
        color: white;
        border: none;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #006c84, #04d8d7);
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1633s36 {
        background: linear-gradient(180deg, #f0f9ff 0%, #e6f3f5 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CORES ENERGISA OFICIAIS
# ============================================
CORES = {
    'Desenvolvido': '#2E7D32',      # Verde escuro
    'Comissionado': '#028a9f',      # Turquesa Energisa
    'Validado': '#005973',           # Azul escuro Energisa
    'Necessário Revisão': '#F57C00', # Laranja
    'Pendente': '#C62828',           # Vermelho
    'EMT': '#028a9f',                # Turquesa Energisa
    'ETO': '#005973',                # Azul escuro Energisa
    'background': '#f0f9ff',
    'card': 'white',
    'texto': '#2c5f6b',
    'texto_secundario': '#5f8b94',
    'gradient_start': '#005973',
    'gradient_mid': '#028a9f',
    'gradient_end': '#04d8d7'
}

# ============================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================
def processar_dados(df):
    """Processa e padroniza os dados"""
    if df is None or df.empty:
        return df
    
    # Padronizar nomes das colunas (remover acentos e espaços extras)
    df.columns = df.columns.str.strip()
    
    # Mapeamento de colunas
    mapeamento_colunas = {
        'Cód.Equipamento': 'Codigo',
        'Cód. Equipamento': 'Codigo',
        'Tipo Equipamento': 'Tipo',
        'Empresa': 'Empresa',
        'Chamado de Desenvolvimento': 'Chamado',
        'Responsável Desenvolvimento': 'Resp_Dev',
        'Responsável Comissionamento': 'Resp_Com',
        'Responsável Auditoria': 'Resp_Audit'
    }
    
    # Renomear colunas se existirem
    for col_antiga, col_nova in mapeamento_colunas.items():
        if col_antiga in df.columns and col_nova not in df.columns:
            df.rename(columns={col_antiga: col_nova}, inplace=True)
    
    # Preencher responsáveis não atribuídos
    for col in ['Resp_Dev', 'Resp_Com', 'Resp_Audit']:
        if col in df.columns:
            df[col] = df[col].fillna('Não atribuído')
        else:
            df[col] = 'Não atribuído'
    
    # Padronizar status
    status_map = {
        'desenvolvido': 'Desenvolvido',
        'desenv': 'Desenvolvido',
        'comissionado': 'Comissionado',
        'comiss': 'Comissionado',
        'validado': 'Validado',
        'valid': 'Validado',
        'revisão': 'Necessário Revisão',
        'revisao': 'Necessário Revisão',
        'revisar': 'Necessário Revisão',
        'necessario revisão': 'Necessário Revisão',
        'necessario revisao': 'Necessário Revisão',
        'pendente': 'Pendente',
        'pend': 'Pendente'
    }
    
    # Identificar coluna de status
    col_status = None
    for col in ['Status', 'Fase', 'Situação', 'Situacao']:
        if col in df.columns:
            col_status = col
            break
    
    if col_status:
        df[col_status] = df[col_status].astype(str).str.lower().str.strip()
        df['Status'] = df[col_status].map(lambda x: next(
            (v for k, v in status_map.items() if k in x), 
            'Pendente'
        ))
    else:
        df['Status'] = 'Pendente'
    
    # Processar datas
    for col in ['Criado', 'Modificado']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y %H:%M', errors='coerce')
    
    # Criar colunas de tempo
    if 'Criado' in df.columns:
        df['Ano'] = df['Criado'].dt.year
        df['Mes'] = df['Criado'].dt.month
        df['Mes_Ano'] = df['Criado'].dt.strftime('%Y-%m')
        df['Data'] = df['Criado'].dt.date
    
    return df

def calcular_tendencias(df, periodo='mes'):
    """Calcula tendências para os KPIs"""
    if df.empty or 'Criado' not in df.columns:
        return {}
    
    hoje = datetime.now()
    
    if periodo == 'mes':
        inicio_periodo = hoje - relativedelta(months=1)
        inicio_periodo_anterior = hoje - relativedelta(months=2)
    else:  # semana
        inicio_periodo = hoje - timedelta(days=7)
        inicio_periodo_anterior = hoje - timedelta(days=14)
    
    df_periodo = df[df['Criado'] >= inicio_periodo]
    df_anterior = df[
        (df['Criado'] >= inicio_periodo_anterior) & 
        (df['Criado'] < inicio_periodo)
    ]
    
    tendencias = {}
    
    for status in ['Desenvolvido', 'Comissionado', 'Validado']:
        qtd_periodo = len(df_periodo[df_periodo['Status'] == status])
        qtd_anterior = len(df_anterior[df_anterior['Status'] == status])
        
        if qtd_anterior > 0:
            variacao = ((qtd_periodo - qtd_anterior) / qtd_anterior) * 100
        else:
            variacao = 100 if qtd_periodo > 0 else 0
        
        tendencias[status] = {
            'atual': qtd_periodo,
            'anterior': qtd_anterior,
            'variacao': variacao
        }
    
    return tendencias

@st.cache_data(ttl=300)
def load_data():
    """Carrega dados do GitHub ou local"""
    try:
        # Tentar carregar do GitHub primeiro
        df = load_data_from_github()
        
        if df is not None:
            return processar_dados(df), "github"
        
        # Fallback para arquivo local
        caminho_local = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        if os.path.exists(caminho_local):
            df = pd.read_csv(caminho_local, encoding='utf-8-sig')
            return processar_dados(df), "local"
        
        # Dados de exemplo se nada funcionar
        st.info("📊 Usando dados de exemplo para demonstração.")
        
        dados_exemplo = {
            'Cód.Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 101)],
            'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 100),
            'Empresa': np.random.choice(['EMT', 'ETO'], 100),
            'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa'], 100),
            'Responsável Comissionamento': np.random.choice(['Carlos Lima', 'Ana Paula', 'Roberto Alves'], 100),
            'Responsável Auditoria': np.random.choice(['Fernando Costa', 'Lucia Santos'], 100),
            'Status': np.random.choice(['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão'], 100, 
                                      p=[0.3, 0.25, 0.25, 0.2]),
            'Criado': pd.date_range(start='2025-01-01', periods=100, freq='D').strftime('%d/%m/%Y %H:%M')
        }
        df = pd.DataFrame(dados_exemplo)
        return processar_dados(df), "exemplo"
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return None, "erro"

# ============================================
# INTERFACE PRINCIPAL
# ============================================

# Carregar dados
if 'df' not in st.session_state:
    with st.spinner("🔄 Carregando dados..."):
        df, fonte = load_data()
        st.session_state.df = df
        st.session_state.fonte = fonte
else:
    df = st.session_state.df
    fonte = st.session_state.fonte

if df is None or df.empty:
    st.error("❌ Não foi possível carregar os dados.")
    st.stop()

# HEADER EXECUTIVO COM LOGO
logo_base64, mime_type = get_logo_base64()

if logo_base64:
    header_logo_html = f'<img src="data:{mime_type};base64,{logo_base64}" alt="Logo Energisa">'
else:
    header_logo_html = '<div style="font-size: 35px;">⚡</div>'

st.markdown(f"""
<div class="header-executivo">
    <div class="header-conteudo">
        <div class="header-logo">
            {header_logo_html}
        </div>
        <div class="header-titulo">
            <h1>Radar de Comissionamento SCADA</h1>
            <p>Cliente é tudo pra gente • Acompanhamento Executivo • Desenvolvimento → Validação</p>
        </div>
        <div class="header-data">
            📅 {datetime.now().strftime('%d/%m/%Y')} • Fonte: {fonte.upper()}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("### 🎯 Painel de Controle")
    
    # Fonte de dados
    st.markdown("**📊 Conexão GitHub**")
    conectado, msg = test_github_connection()
    if conectado:
        st.success("✅ " + msg)
    else:
        st.warning("⚠️ " + msg)
        st.info("💡 O dashboard está funcionando com dados locais. Para conectar ao GitHub, configure o token nas Secrets.")
    
    st.markdown("---")
    
    # Filtros principais
    st.markdown("### 🔍 Filtros")
    
    # Período
    st.markdown("**📅 Período**")
    
    opcao_periodo = st.radio(
        "Selecionar período:",
        options=['Últimos 30 dias', 'Últimos 90 dias', 'Ano atual', 'Todos', 'Personalizado'],
        index=0,
        horizontal=True
    )
    
    data_inicio = None
    data_fim = None
    
    if opcao_periodo == 'Personalizado':
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("De", value=datetime.now() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Até", value=datetime.now())
    elif opcao_periodo == 'Últimos 30 dias':
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now()
    elif opcao_periodo == 'Últimos 90 dias':
        data_inicio = datetime.now() - timedelta(days=90)
        data_fim = datetime.now()
    elif opcao_periodo == 'Ano atual':
        data_inicio = datetime(datetime.now().year, 1, 1)
        data_fim = datetime.now()
    
    st.markdown("**🏢 Empresa**")
    empresas = st.multiselect(
        "Selecionar empresas:",
        options=sorted(df['Empresa'].unique()),
        default=sorted(df['Empresa'].unique())
    )
    
    st.markdown("**🔧 Tipo de Equipamento**")
    if 'Tipo' in df.columns:
        tipos = st.multiselect(
            "Selecionar tipos:",
            options=sorted(df['Tipo'].unique()),
            default=[]
        )
    else:
        tipos = []
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if empresas:
        df_filtrado = df_filtrado[df_filtrado['Empresa'].isin(empresas)]
    
    if tipos:
        df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(tipos)]
    
    if data_inicio and data_fim and 'Criado' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['Criado'].dt.date >= data_inicio.date()) &
            (df_filtrado['Criado'].dt.date <= data_fim.date())
        ]
    
    # Estatísticas rápidas
    st.markdown("---")
    st.markdown("### 📊 Visão Rápida")
    
    total = len(df_filtrado)
    em_andamento = len(df_filtrado[df_filtrado['Status'].isin(['Desenvolvido', 'Comissionado'])])
    finalizados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])
    
    st.markdown(f"""
    <div style="background: white; padding: 1rem; border-radius: 12px; border-left: 4px solid #028a9f;">
        <div style="display: flex; justify-content: space-between;">
            <span>📦 Total:</span> <strong>{total}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
            <span>⚙️ Em andamento:</span> <strong>{em_andamento}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
            <span>✅ Finalizados:</span> <strong>{finalizados}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
            <span>📝 Em revisão:</span> <strong>{revisao}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Limpar Filtros", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("📥 Exportar", use_container_width=True):
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📊 Download CSV",
                csv,
                f"dados_scada_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

# ============================================
# PAINEL PRINCIPAL
# ============================================

if not df_filtrado.empty:
    # Contagens por status
    qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
    qtd_comissionados = len(df_filtrado[df_filtrado['Status'] == 'Comissionado'])
    qtd_validados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    qtd_revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])
    
    # Total de itens no fluxo (excluindo pendentes)
    total_fluxo = qtd_desenvolvidos + qtd_comissionados + qtd_validados + qtd_revisao
    
    # Taxas de conversão CORRIGIDAS
    taxa_desenv_para_comiss = (qtd_comissionados / qtd_desenvolvidos * 100) if qtd_desenvolvidos > 0 else 0
    taxa_comiss_para_valid = (qtd_validados / qtd_comissionados * 100) if qtd_comissionados > 0 else 0
    taxa_valid_sobre_total = (qtd_validados / total_fluxo * 100) if total_fluxo > 0 else 0
    taxa_revisao_sobre_total = (qtd_revisao / total_fluxo * 100) if total_fluxo > 0 else 0
    
    # VISUALIZAÇÃO DO FLUXO
    st.markdown("### 🔄 Fluxo de Validação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Desenvolvido']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #5f8b94;">ETAPA 1</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Desenvolvido']};">{qtd_desenvolvidos}</div>
                <div style="font-weight: 500;">Desenvolvidos</div>
                <div style="font-size: 0.85rem; color: #5f8b94;">Aguardando comissionamento</div>
                <div style="margin-top: 0.5rem; background: #e0f7fa; border-radius: 20px; padding: 0.3rem;">
                    → {taxa_desenv_para_comiss:.1f}% para comissionar
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Comissionado']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #5f8b94;">ETAPA 2</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Comissionado']};">{qtd_comissionados}</div>
                <div style="font-weight: 500;">Comissionados</div>
                <div style="font-size: 0.85rem; color: #5f8b94;">Aguardando validação</div>
                <div style="margin-top: 0.5rem; background: #e0f7fa; border-radius: 20px; padding: 0.3rem;">
                    → {taxa_comiss_para_valid:.1f}% validados
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Validado']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #5f8b94;">ETAPA 3</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Validado']};">{qtd_validados}</div>
                <div style="font-weight: 500;">Validados</div>
                <div style="font-size: 0.85rem; color: #5f8b94;">Processo concluído</div>
                <div style="margin-top: 0.5rem; background: #e0f7fa; border-radius: 20px; padding: 0.3rem;">
                    ✓ {taxa_valid_sobre_total:.1f}% do total
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Necessário Revisão']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #5f8b94;">GARGALO</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Necessário Revisão']};">{qtd_revisao}</div>
                <div style="font-weight: 500;">Em Revisão</div>
                <div style="font-size: 0.85rem; color: #5f8b94;">Aguardando correções</div>
                <div style="margin-top: 0.5rem; background: #fff3e0; border-radius: 20px; padding: 0.3rem;">
                    ⚠️ {taxa_revisao_sobre_total:.1f}% em revisão
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # TABS PARA ANÁLISES DETALHADAS
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Visão Executiva", 
        "📈 Evolução Temporal",
        "👥 Performance por Responsável",
        "📋 Detalhamento"
    ])
    
    with tab1:
        st.markdown("### 📊 Análise Comparativa por Empresa")
        
        col1, col2 = st.columns(2)
        
        for idx, empresa in enumerate(['EMT', 'ETO']):
            with col1 if idx == 0 else col2:
                df_emp = df_filtrado[df_filtrado['Empresa'] == empresa]
                
                if not df_emp.empty:
                    # Contagens
                    total_emp = len(df_emp)
                    com_emp = len(df_emp[df_emp['Status'] == 'Comissionado'])
                    val_emp = len(df_emp[df_emp['Status'] == 'Validado'])
                    
                    st.markdown(f"""
                    <div class="company-card">
                        <div class="company-title" style="color: {CORES[empresa]};">{empresa}</div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: #005973;">{total_emp}</div>
                                <div class="company-metric-label">Equipamentos cadastrados</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Comissionado']};">{com_emp}</div>
                                <div class="company-metric-label">Aguardando validação</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Validado']};">{val_emp}</div>
                                <div class="company-metric-label">Processo concluído</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem;">
                            <div style="background: #e0f7fa; border-radius: 20px; padding: 0.5rem;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Progresso do fluxo:</span>
                                    <strong>{((com_emp+val_emp)/total_emp*100):.1f}%</strong>
                                </div>
                                <div style="width: 100%; background: #cbd5e0; height: 6px; border-radius: 3px; margin-top: 0.5rem;">
                                    <div style="width: {((com_emp+val_emp)/total_emp*100)}%; background: linear-gradient(90deg, #028a9f, #04d8d7); height: 6px; border-radius: 3px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Gráfico de distribuição
        st.markdown("### 📊 Distribuição do Portfólio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por status
            status_counts = df_filtrado['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            
            fig_status = px.pie(
                status_counts,
                values='Quantidade',
                names='Status',
                title='Distribuição por Status',
                color='Status',
                color_discrete_map=CORES,
                hole=0.4
            )
            fig_status.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                texttemplate='%{label}<br>%{percent:.1%}',
                marker=dict(line=dict(color='white', width=2))
            )
            fig_status.update_layout(
                showlegend=False,
                height=350,
                margin=dict(t=50, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Top tipos de equipamento
            if 'Tipo' in df_filtrado.columns:
                tipo_counts = df_filtrado['Tipo'].value_counts().head(8).reset_index()
                tipo_counts.columns = ['Tipo', 'Quantidade']
                
                fig_tipo = px.bar(
                    tipo_counts,
                    x='Quantidade',
                    y='Tipo',
                    orientation='h',
                    title='Top 8 Tipos de Equipamento',
                    color='Quantidade',
                    color_continuous_scale=['#e0f7fa', '#028a9f', '#005973'],
                    text='Quantidade'
                )
                fig_tipo.update_traces(textposition='outside')
                fig_tipo.update_layout(
                    height=350,
                    margin=dict(t=50, b=10, l=10, r=10),
                    xaxis_title="Quantidade",
                    yaxis_title="",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
    
    with tab2:
        st.markdown("### 📈 Evolução do Fluxo")
        
        if 'Criado' in df_filtrado.columns:
            # Agregação por mês
            df_filtrado['Mes_Ano_Label'] = df_filtrado['Criado'].dt.strftime('%b/%Y')
            df_filtrado['Ano_Mes'] = df_filtrado['Criado'].dt.strftime('%Y-%m')
            
            evolucao = df_filtrado.groupby(['Ano_Mes', 'Mes_Ano_Label', 'Status']).size().reset_index(name='Quantidade')
            evolucao = evolucao.sort_values('Ano_Mes')
            
            # Gráfico de linhas
            fig_evolucao = px.line(
                evolucao,
                x='Mes_Ano_Label',
                y='Quantidade',
                color='Status',
                markers=True,
                title='Evolução Mensal por Status',
                color_discrete_map=CORES
            )
            fig_evolucao.update_layout(
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade",
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
            # Gráfico de barras empilhadas
            fig_barras = px.bar(
                evolucao,
                x='Mes_Ano_Label',
                y='Quantidade',
                color='Status',
                title='Distribuição Mensal por Status',
                color_discrete_map=CORES,
                barmode='stack',
                text='Quantidade'
            )
            fig_barras.update_traces(textposition='inside')
            fig_barras.update_layout(
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_barras, use_container_width=True)
            
            # Taxas de conversão ao longo do tempo
            st.markdown("### 📊 Taxas de Conversão")
            
            # Calcular taxas por mês
            taxa_mensal = []
            for mes in evolucao['Ano_Mes'].unique():
                df_mes = df_filtrado[df_filtrado['Ano_Mes'] == mes]
                total_mes = len(df_mes)
                if total_mes > 0:
                    taxa_mensal.append({
                        'Mês': mes,
                        'Taxa Comissionamento': len(df_mes[df_mes['Status'] == 'Comissionado']) / total_mes * 100,
                        'Taxa Validação': len(df_mes[df_mes['Status'] == 'Validado']) / total_mes * 100,
                        'Taxa Revisão': len(df_mes[df_mes['Status'] == 'Necessário Revisão']) / total_mes * 100
                    })
            
            if taxa_mensal:
                df_taxas = pd.DataFrame(taxa_mensal)
                df_taxas = df_taxas.sort_values('Mês')
                
                fig_taxas = go.Figure()
                fig_taxas.add_trace(go.Scatter(
                    x=df_taxas['Mês'],
                    y=df_taxas['Taxa Comissionamento'],
                    name='Comissionamento',
                    line=dict(color=CORES['Comissionado'], width=3),
                    mode='lines+markers',
                    marker=dict(size=8)
                ))
                fig_taxas.add_trace(go.Scatter(
                    x=df_taxas['Mês'],
                    y=df_taxas['Taxa Validação'],
                    name='Validação',
                    line=dict(color=CORES['Validado'], width=3),
                    mode='lines+markers',
                    marker=dict(size=8)
                ))
                fig_taxas.add_trace(go.Scatter(
                    x=df_taxas['Mês'],
                    y=df_taxas['Taxa Revisão'],
                    name='Revisão',
                    line=dict(color=CORES['Necessário Revisão'], width=3),
                    mode='lines+markers',
                    marker=dict(size=8)
                ))
                
                fig_taxas.update_layout(
                    title='Evolução das Taxas de Conversão',
                    xaxis_title="Mês",
                    yaxis_title="Taxa (%)",
                    yaxis=dict(range=[0, 100]),
                    height=400,
                    hovermode='x unified',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_taxas, use_container_width=True)
    
    with tab3:
        st.markdown("### 👥 Performance por Responsável")
        
        tipo_resp = st.radio(
            "Selecionar tipo:",
            options=['Desenvolvimento', 'Comissionamento', 'Auditoria'],
            horizontal=True,
            key='tipo_resp'
        )
        
        mapa_colunas = {
            'Desenvolvimento': 'Resp_Dev',
            'Comissionamento': 'Resp_Com',
            'Auditoria': 'Resp_Audit'
        }
        
        col_resp = mapa_colunas[tipo_resp]
        
        if col_resp in df_filtrado.columns:
            df_resp = df_filtrado[df_filtrado[col_resp] != 'Não atribuído']
            
            if not df_resp.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Ranking de quantidade
                    ranking = df_resp[col_resp].value_counts().head(10).reset_index()
                    ranking.columns = ['Responsável', 'Quantidade']
                    
                    fig_ranking = px.bar(
                        ranking,
                        x='Quantidade',
                        y='Responsável',
                        orientation='h',
                        title=f'Top 10 Responsáveis - {tipo_resp}',
                        color='Quantidade',
                        color_continuous_scale=['#e0f7fa', '#028a9f', '#005973'],
                        text='Quantidade'
                    )
                    fig_ranking.update_traces(textposition='outside')
                    fig_ranking.update_layout(
                        height=400,
                        xaxis_title="Quantidade de Atividades",
                        yaxis_title="",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_ranking, use_container_width=True)
                
                with col2:
                    # Taxa de sucesso (itens que chegaram à validação)
                    sucesso = []
                    for resp in ranking['Responsável'].head(10):
                        df_resp_item = df_resp[df_resp[col_resp] == resp]
                        total = len(df_resp_item)
                        if total > 0:
                            sucesso_count = len(df_resp_item[df_resp_item['Status'] == 'Validado'])
                            taxa = (sucesso_count / total) * 100
                            sucesso.append({
                                'Responsável': resp,
                                'Taxa de Sucesso': taxa,
                                'Validados': sucesso_count,
                                'Total': total
                            })
                    
                    if sucesso:
                        df_sucesso = pd.DataFrame(sucesso).sort_values('Taxa de Sucesso', ascending=False)
                        
                        fig_sucesso = px.bar(
                            df_sucesso,
                            x='Taxa de Sucesso',
                            y='Responsável',
                            orientation='h',
                            title=f'Taxa de Sucesso por Responsável - {tipo_resp}',
                            color='Taxa de Sucesso',
                            color_continuous_scale=['#e8f5e9', '#2e7d32'],
                            text=df_sucesso['Taxa de Sucesso'].round(1).astype(str) + '%'
                        )
                        fig_sucesso.update_traces(textposition='outside')
                        fig_sucesso.update_layout(
                            height=400,
                            xaxis_title="Taxa de Sucesso (%)",
                            xaxis_range=[0, 100],
                            yaxis_title="",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_sucesso, use_container_width=True)
                
                # Distribuição de status por responsável
                st.markdown(f"#### 📊 Distribuição de Status por {tipo_resp}")
                
                top_resp = ranking['Responsável'].head(8).tolist()
                df_top = df_resp[df_resp[col_resp].isin(top_resp)]
                
                dist_status = df_top.groupby([col_resp, 'Status']).size().reset_index(name='Quantidade')
                
                fig_dist = px.bar(
                    dist_status,
                    x=col_resp,
                    y='Quantidade',
                    color='Status',
                    title=f'Distribuição de Status por Responsável de {tipo_resp}',
                    barmode='stack',
                    color_discrete_map=CORES,
                    text='Quantidade'
                )
                fig_dist.update_traces(textposition='inside')
                fig_dist.update_layout(
                    height=450,
                    xaxis_tickangle=45,
                    xaxis_title="",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.info(f"Nenhum responsável de {tipo_resp} encontrado com atividades.")
    
    with tab4:
        st.markdown("### 📋 Detalhamento dos Registros")
        
        # Métricas rápidas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", len(df_filtrado))
        with col2:
            st.metric("Empresas", len(df_filtrado['Empresa'].unique()))
        with col3:
            if 'Tipo' in df_filtrado.columns:
                st.metric("Tipos de Equipamento", len(df_filtrado['Tipo'].unique()))
            else:
                st.metric("Tipos de Equipamento", 0)
        with col4:
            st.metric("Responsáveis", len(df_filtrado['Resp_Dev'].unique()))
        
        # Tabela de dados
        colunas_mostrar = ['Codigo', 'Tipo', 'Empresa', 'Status', 'Resp_Dev', 'Resp_Com', 'Resp_Audit']
        colunas_existentes = [c for c in colunas_mostrar if c in df_filtrado.columns]
        
        if colunas_existentes:
            df_display = df_filtrado[colunas_existentes].copy()
            st.dataframe(df_display, use_container_width=True)
        
        # Estatísticas descritivas
        with st.expander("📊 Estatísticas Detalhadas"):
            st.markdown("**Distribuição por Status:**")
            status_counts = df_filtrado['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Quantidade']
            total_linhas = len(df_filtrado)
            
            percentuais = []
            for qtd in status_counts['Quantidade']:
                percentual = (qtd / total_linhas * 100) if total_linhas > 0 else 0
                percentuais.append(f"{percentual:.1f}%")
            
            status_counts['Percentual'] = percentuais
            st.dataframe(status_counts)
            
            if 'Tipo' in df_filtrado.columns:
                st.markdown("**Distribuição por Tipo de Equipamento:**")
                tipo_counts = df_filtrado['Tipo'].value_counts().reset_index()
                tipo_counts.columns = ['Tipo', 'Quantidade']
                st.dataframe(tipo_counts.head(15))
    
    # FOOTER
    st.markdown(f"""
    <div class="footer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>⚡ Radar de Comissionamento SCADA</strong> • Versão 4.1 • Energisa
            </div>
            <div>
                Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
            <div style="color: #5f8b94;">
                {len(df_filtrado)} registros • {fonte.upper()}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
