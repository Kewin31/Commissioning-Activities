import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import io
import requests
import base64
from github import Github
from github import GithubException
import tempfile
import time

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Desenvolvimentos/Comissionamentos | Fábrica SCADA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CONFIGURAÇÕES DO GITHUB
# ============================================
def get_github_config():
    """Obtém configurações do GitHub do Streamlit Secrets com validação"""
    try:
        # Verificar se os secrets existem
        if "GITHUB_TOKEN" not in st.secrets:
            st.error("❌ Token do GitHub não configurado. Configure no Streamlit Secrets.")
            return None, None, None
            
        token = st.secrets["GITHUB_TOKEN"]
        
        if "GITHUB_REPO" not in st.secrets:
            st.error("❌ Repositório do GitHub não configurado. Configure no Streamlit Secrets.")
            return token, None, None
            
        repo = st.secrets["GITHUB_REPO"]
        
        # Validar formato do repositório (deve ser "usuario/repo")
        if '/' not in repo:
            st.error("❌ Formato do repositório inválido. Use 'usuario/repo'")
            return token, None, None
            
        file_path = st.secrets.get("GITHUB_FILE_PATH", "data/Dados/Comissionamento AD - UNs.csv")
        
        return token, repo, file_path
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar configurações do GitHub: {str(e)}")
        return None, None, None

def test_github_connection():
    """Testa a conexão com o GitHub"""
    try:
        token, repo_name, _ = get_github_config()
        
        if not token or not repo_name:
            return False, "Configurações incompletas"
        
        # Testar conexão
        g = Github(token)
        user = g.get_user()
        
        # Tentar acessar o repositório
        repo = g.get_repo(repo_name)
        
        return True, f"Conectado como {user.login} | Repositório: {repo_name}"
        
    except GithubException as e:
        if e.status == 401:
            return False, "Token inválido ou expirado. Gere um novo token no GitHub."
        elif e.status == 404:
            return False, f"Repositório '{repo_name}' não encontrado."
        else:
            return False, f"Erro GitHub: {e.status} - {e.data.get('message', 'Erro desconhecido')}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def atualizar_dados_github(arquivo_upload, branch="main"):
    """Atualiza o arquivo no GitHub com o novo arquivo enviado"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            st.error("❌ Configurações do GitHub incompletas. Verifique o Streamlit Secrets.")
            return False
        
        # Validar arquivo
        if arquivo_upload is None:
            st.error("❌ Nenhum arquivo selecionado.")
            return False
        
        # Verificar se é CSV
        if not arquivo_upload.name.endswith('.csv'):
            st.error("❌ O arquivo deve ser do tipo CSV.")
            return False
        
        # Conectar ao GitHub
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
            if e.status == 401:
                st.error("❌ Token inválido ou expirado. Gere um novo token no GitHub.")
                st.info("🔑 Para gerar um novo token: GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)")
                return False
            elif e.status == 404:
                st.error(f"❌ Repositório '{repo_name}' não encontrado.")
                return False
            else:
                raise e
        
        # Ler o conteúdo do arquivo enviado
        file_content = arquivo_upload.read()
        
        # Validar se é um CSV válido
        try:
            # Tentar ler com pandas para validar
            df_temp = pd.read_csv(io.BytesIO(file_content), encoding='utf-8-sig')
            st.success(f"✅ CSV válido! {len(df_temp)} linhas, {len(df_temp.columns)} colunas")
        except Exception as e:
            st.error(f"❌ Arquivo CSV inválido: {str(e)}")
            return False
        
        # Verificar se o arquivo já existe no repositório
        try:
            contents = repo.get_contents(file_path, ref=branch)
            # Atualizar arquivo existente
            repo.update_file(
                path=file_path,
                message=f"📦 Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                content=file_content,
                sha=contents.sha,
                branch=branch
            )
            st.success(f"✅ Arquivo atualizado com sucesso no GitHub! ({branch})")
            
        except GithubException as e:
            if e.status == 404:
                # Criar novo arquivo
                try:
                    repo.create_file(
                        path=file_path,
                        message=f"📦 Criação inicial - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        content=file_content,
                        branch=branch
                    )
                    st.success(f"✅ Arquivo criado com sucesso no GitHub! ({branch})")
                except Exception as create_error:
                    st.error(f"❌ Erro ao criar arquivo: {str(create_error)}")
                    return False
            else:
                st.error(f"❌ Erro GitHub: {e.status} - {e.data.get('message', 'Erro desconhecido')}")
                return False
        
        # Limpar cache para carregar novos dados
        st.cache_data.clear()
        
        # Registrar no log
        st.info(f"📝 Commit: Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao atualizar GitHub: {str(e)}")
        return False

def load_data_from_github():
    """Carrega dados exclusivamente do GitHub"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            st.warning("⚠️ Configurações do GitHub incompletas. Usando modo offline.")
            return None
        
        # Conectar ao GitHub
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
            contents = repo.get_contents(file_path)
            
            # Decodificar conteúdo
            file_content = base64.b64decode(contents.content).decode('utf-8')
            
            # Salvar temporariamente para ler com pandas
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(file_content)
                temp_file = f.name
            
            df = pd.read_csv(temp_file, encoding='utf-8-sig')
            os.unlink(temp_file)  # Limpar arquivo temporário
            
            return df
            
        except GithubException as e:
            if e.status == 401:
                st.error("❌ Token GitHub inválido ou expirado.")
                return None
            elif e.status == 404:
                st.error(f"❌ Arquivo '{file_path}' não encontrado no repositório.")
                return None
            else:
                st.error(f"❌ Erro GitHub: {e.status}")
                return None
                
    except Exception as e:
        st.error(f"❌ Erro ao carregar do GitHub: {str(e)}")
        return None

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

# CSS personalizado
st.markdown("""
<style>
    /* Fontes e reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Cards de métrica */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid #edf2f7;
        transition: all 0.3s ease;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,40,100,0.1);
        border-color: #cbd5e0;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #2a5298, #4a7ab0);
    }
    
    /* Títulos de seção */
    .section-title {
        color: #0a1a3c;
        font-size: 1.4rem;
        font-weight: 600;
        margin: 1.8rem 0 1.2rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #e2e8f0;
        letter-spacing: -0.01em;
    }
    
    /* Sidebar melhorada */
    .css-1d391kg {
        background-color: #f7fafc;
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.8rem 1rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 1rem -1rem;
        text-align: center;
        color: white;
    }
    
    /* Botões e inputs */
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #15355e 0%, #1e3c72 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30,60,114,0.3);
    }
    
    /* Botões de atualização */
    .update-button > button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    }
    .update-button > button:hover {
        background: linear-gradient(135deg, #218838 0%, #1e7e34 100%);
    }
    
    .refresh-button > button {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    }
    .refresh-button > button:hover {
        background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
    }
    
    /* Status card */
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    .status-success {
        border-left: 4px solid #28a745;
    }
    
    .status-error {
        border-left: 4px solid #dc3545;
    }
    
    .status-warning {
        border-left: 4px solid #ffc107;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-weight: 500;
        color: #1e3c72;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f7fafc;
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    /* Rodapé */
    .footer {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Cards simples */
    .metric-card-simple {
        background-color: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        height: 100%;
        transition: transform 0.2s;
    }
    .metric-card-simple:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Função para criar cards de métrica
def metric_card(title, value, subtitle=None, icon="📊", color="#1e3c72", delta=None):
    if isinstance(value, (int, float)):
        value_str = f"{value:,.0f}".replace(",", ".")
    else:
        value_str = str(value)
    
    delta_html = ""
    if delta is not None:
        delta_color = "#28a745" if delta > 0 else "#dc3545"
        delta_html = f"<span style='color: {delta_color}; font-size:0.9rem; margin-left:8px;'>{delta:+.1f}%</span>"
    
    subtitle_html = ""
    if subtitle:
        subtitle_html = f"<div style='font-size:0.85rem; color:#718096; margin-top:4px;'>{subtitle}</div>"
    
    html = f"""
    <div class='metric-card'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom:8px;'>
            <span style='font-size: 1rem; color: #4a5568; font-weight: 500;'>{icon} {title}</span>
            {delta_html}
        </div>
        <div style='font-size: 2.2rem; font-weight: 700; color: {color}; line-height: 1.2;'>
            {value_str}
        </div>
        {subtitle_html}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def format_number(val):
    if pd.isna(val):
        return "0"
    if isinstance(val, (int, float)):
        return f"{val:,.0f}".replace(",", ".")
    return str(val)

def configurar_grafico_corporativo(fig, titulo, height=400):
    fig.update_layout(
        title={
            'text': titulo,
            'font': {'size': 16, 'family': 'Inter, sans-serif', 'color': '#0a1a3c', 'weight': 600},
            'x': 0.5,
            'xanchor': 'center'
        },
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Inter, sans-serif', 'size': 12, 'color': '#2d3748'},
        margin={'l': 50, 'r': 30, 't': 70, 'b': 50},
        height=height,
        hoverlabel={
            'bgcolor': 'white',
            'font_size': 12,
            'font_family': 'Inter, sans-serif'
        }
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f2f6',
        linecolor='#e2e8f0'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f2f6',
        linecolor='#e2e8f0'
    )
    
    return fig

# Função para carregar dados com opção de fonte
@st.cache_data(ttl=300)  # Cache de 5 minutos
def load_data(force_github=False):
    """Carrega dados do GitHub ou local"""
    try:
        df = None
        fonte = "local"
        
        # Se forçar GitHub ou não tiver dados locais, tenta GitHub
        if force_github:
            st.info("🔄 Carregando dados do GitHub...")
            df = load_data_from_github()
            if df is not None:
                fonte = "github"
                st.success("✅ Dados carregados do GitHub!")
        
        # Se não conseguiu do GitHub, tenta local
        if df is None:
            caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
            
            if os.path.exists(caminho_arquivo):
                df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
                st.info(f"📁 Dados carregados do arquivo local: {caminho_arquivo}")
            else:
                # Criar dados de exemplo
                st.warning("⚠️ Nenhum arquivo encontrado. Usando dados de exemplo.")
                dados_exemplo = {
                    'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 51)],
                    'Chamado Desenvolvimento': [f'CHAMADO-{i}' for i in range(1001, 1051)],
                    'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 50),
                    'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Souza', 'Não atribuído'], 50),
                    'Responsável Comissionamento': np.random.choice(['Roberto Lima', 'Carla Mendes', 'Paulo Ferreira', 'Não atribuído'], 50),
                    'Responsável Auditoria': np.random.choice(['Fernando Alves', 'Lucia Santos', 'Marcos Paulo', 'Não atribuído'], 50),
                    'Fase': np.random.choice(['DEV', 'COM', 'VAL', 'PEN'], 50, p=[0.3, 0.25, 0.2, 0.25]),
                    'Status': np.random.choice(['Desenvolvido', 'Em andamento', 'Pendente'], 50, p=[0.4, 0.35, 0.25]),
                    'Empresa': np.random.choice(['EMT', 'ETO'], 50),
                    'Criado': pd.date_range(start='2024-01-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M'),
                    'Modificado': pd.date_range(start='2024-02-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M')
                }
                df = pd.DataFrame(dados_exemplo)
        
        # Tratamento de dados
        if df is not None:
            # Colunas de responsáveis
            colunas_responsaveis = {
                'Responsável Desenvolvimento': 'Não atribuído',
                'Responsável Comissionamento': 'Não atribuído',
                'Responsável Auditoria': 'Não atribuído'
            }
            
            for col, valor_padrao in colunas_responsaveis.items():
                if col not in df.columns:
                    df[col] = valor_padrao
                else:
                    df[col] = df[col].fillna(valor_padrao)
            
            # Status
            if 'Status' in df.columns:
                df['Status'] = df['Status'].fillna('Pendente')
                df['Status'] = df['Status'].str.strip()
            
            # Status Detalhado
            if 'Status Detalhado' not in df.columns:
                if 'Fase' in df.columns:
                    mapa_fases = {
                        'DEV': 'Desenvolvido',
                        'COM': 'Comissionado',
                        'VAL': 'Validado',
                        'PEN': 'Pendente'
                    }
                    df['Status Detalhado'] = df['Fase'].map(mapa_fases).fillna('Pendente')
                else:
                    df['Status Detalhado'] = df['Status']
            
            # Datas
            if 'Criado' in df.columns:
                df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M', errors='coerce')
            if 'Modificado' in df.columns:
                df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        return df, fonte
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return None, "erro"

# Interface principal
st.markdown("""
<style>
    .header-unificado {
        background: linear-gradient(135deg, #0a1a3c 0%, #1e3c72 100%);
        border-radius: 16px;
        padding: 1rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 20px rgba(0,20,50,0.15);
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        gap: 1.5rem;
        width: 100%;
    }
    .header-logo {
        width: 70px;
        height: 70px;
        object-fit: contain;
        background: white;
        border-radius: 10px;
        padding: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .header-texto {
        flex: 1;
    }
    .header-texto h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
        color: white;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .header-texto p {
        margin: 0.2rem 0 0 0;
        color: rgba(255,255,255,0.9);
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# Carregar dados
if 'fonte_dados' not in st.session_state:
    st.session_state.fonte_dados = "auto"
if 'df' not in st.session_state:
    with st.spinner("🔄 Carregando dados..."):
        df, fonte = load_data(force_github=False)
        st.session_state.df = df
        st.session_state.fonte = fonte

df = st.session_state.df
fonte = st.session_state.fonte

if df is not None:
    # CABEÇALHO
    logo_base64, mime_type = get_logo_base64()
    
    if logo_base64:
        st.markdown(f"""
        <div class="header-unificado">
            <img src="data:{mime_type};base64,{logo_base64}" class="header-logo" alt="Logo Energisa">
            <div class="header-texto">
                <h1>Radar de Comissionamento/Desenvolvimento</h1>
                <p>EMT | ETO</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="header-unificado">
            <div style="background:white; width:70px; height:70px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:35px; box-shadow:0 2px 8px rgba(0,0,0,0.2);">⚡</div>
            <div class="header-texto">
                <h1>📊 Dashboard de Comissionamento</h1>
                <p>Acompanhamento de Desenvolvimentos e Comissionamentos • AD Energisa</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # SIDEBAR
    with st.sidebar:
        st.markdown("""
        <div class='sidebar-header'>
            <h3 style='margin:0; font-size:1.4rem; font-weight:600;'>🔍 Painel de Controle</h3>
            <p style='margin:0.3rem 0 0 0; opacity:0.9; font-size:0.9rem;'>Filtros e Configurações</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Status da fonte de dados
        st.markdown("### 📊 Fonte de Dados")
        
        if fonte == "github":
            st.success("✅ Conectado ao GitHub")
        elif fonte == "local":
            st.info("📁 Modo local (arquivo offline)")
        else:
            st.warning("⚠️ Dados de exemplo")
        
        # Testar conexão GitHub
        with st.expander("🔌 Status da Conexão GitHub", expanded=False):
            conectado, mensagem = test_github_connection()
            
            if conectado:
                st.success(f"✅ {mensagem}")
            else:
                st.error(f"❌ {mensagem}")
                
                st.markdown("""
                **🔑 Como gerar um token:**
                1. Acesse [GitHub Settings](https://github.com/settings/tokens)
                2. Clique em "Generate new token (classic)"
                3. Selecione escopo: `repo`
                4. Copie o token e adicione ao Streamlit Secrets
                """)
        
        # Botão para forçar atualização do GitHub
        st.markdown("### 🔄 Atualização de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="refresh-button">', unsafe_allow_html=True)
            if st.button("🔄 Sincronizar GitHub", use_container_width=True):
                with st.spinner("Carregando dados do GitHub..."):
                    df_novo, nova_fonte = load_data(force_github=True)
                    if df_novo is not None:
                        st.session_state.df = df_novo
                        st.session_state.fonte = nova_fonte
                        st.success("✅ Dados sincronizados!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Falha ao sincronizar")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("📥 Recarregar Local", use_container_width=True):
                st.cache_data.clear()
                with st.spinner("Recarregando dados..."):
                    df_novo, nova_fonte = load_data(force_github=False)
                    if df_novo is not None:
                        st.session_state.df = df_novo
                        st.session_state.fonte = nova_fonte
                        st.rerun()
        
        st.markdown("---")
        
        # Upload para GitHub
        with st.expander("📤 Upload para GitHub", expanded=True):
            st.markdown("""
            <p style='font-size:0.85rem; color:#718096; margin-bottom:10px;'>
                Envie um novo arquivo CSV para atualizar a base no GitHub.
            </p>
            """, unsafe_allow_html=True)
            
            # Branch selector
            branch = st.selectbox("🌿 Branch", ["main", "master"], index=0)
            
            arquivo_upload = st.file_uploader(
                "Selecionar arquivo CSV",
                type=['csv'],
                key="github_upload"
            )
            
            if arquivo_upload is not None:
                # Preview do arquivo
                try:
                    df_preview = pd.read_csv(io.BytesIO(arquivo_upload.getvalue()), 
                                            encoding='utf-8-sig', nrows=5)
                    st.info(f"📁 {arquivo_upload.name} | {len(df_preview)} colunas")
                    
                    with st.expander("Preview"):
                        st.dataframe(df_preview, use_container_width=True)
                except:
                    st.warning("Não foi possível ler o preview do arquivo")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown('<div class="update-button">', unsafe_allow_html=True)
                    if st.button("⬆️ Upload para GitHub", use_container_width=True):
                        with st.spinner("Enviando para o GitHub..."):
                            if atualizar_dados_github(arquivo_upload, branch):
                                st.success("✅ Upload concluído!")
                                time.sleep(2)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.rerun()
        
        st.markdown("---")
        
        # FILTROS
        st.markdown("### 📋 Filtros")
        
        # Inicializar variáveis
        empresas = []
        tipos_equip = []
        status_opcoes = []
        responsaveis_dev = []
        responsaveis_com = []
        responsaveis_audit = []
        data_inicio = None
        data_fim = None
        
        with st.expander("🏢 Empresas", expanded=True):
            empresas = st.multiselect(
                "Selecionar empresas",
                options=sorted(df['Empresa'].unique()),
                default=sorted(df['Empresa'].unique()),
                key="empresas_filter"
            )
        
        with st.expander("🔧 Equipamentos", expanded=True):
            tipos_equip = st.multiselect(
                "Tipos de equipamento",
                options=sorted(df['Tipo Equipamento'].unique()),
                default=sorted(df['Tipo Equipamento'].unique()),
                key="tipos_filter"
            )
        
        with st.expander("📊 Status", expanded=True):
            status_opcoes = st.multiselect(
                "Status",
                options=sorted(df['Status Detalhado'].unique()),
                default=sorted(df['Status Detalhado'].unique()),
                key="status_filter"
            )
        
        with st.expander("👥 Responsáveis"):
            responsaveis_dev = st.multiselect(
                "Desenvolvimento",
                options=sorted(df['Responsável Desenvolvimento'].unique()),
                default=[],
                key="resp_dev_filter"
            )
            
            if 'Responsável Comissionamento' in df.columns:
                responsaveis_com = st.multiselect(
                    "Comissionamento",
                    options=sorted(df['Responsável Comissionamento'].unique()),
                    default=[],
                    key="resp_com_filter"
                )
            
            if 'Responsável Auditoria' in df.columns:
                responsaveis_audit = st.multiselect(
                    "Auditoria",
                    options=sorted(df['Responsável Auditoria'].unique()),
                    default=[],
                    key="resp_audit_filter"
                )
        
        with st.expander("📅 Período"):
            if 'Criado' in df.columns and not df['Criado'].isna().all():
                data_min = df['Criado'].min().date()
                data_max = df['Criado'].max().date()
                
                data_inicio = st.date_input("Data inicial", data_min, key="data_inicio")
                data_fim = st.date_input("Data final", data_max, key="data_fim")
            else:
                st.info("Dados de data não disponíveis")
        
        st.markdown("---")
        
        # Progresso rápido
        if not df.empty:
            st.markdown("### 📊 Progresso")
            
            df_progresso = df.copy()
            if empresas:
                df_progresso = df_progresso[df_progresso['Empresa'].isin(empresas)]
            if tipos_equip:
                df_progresso = df_progresso[df_progresso['Tipo Equipamento'].isin(tipos_equip)]
            
            total = len(df_progresso)
            desenvolvidos = len(df_progresso[df_progresso['Status Detalhado'] == 'Desenvolvido'])
            comissionados = len(df_progresso[df_progresso['Status Detalhado'] == 'Comissionado'])
            validados = len(df_progresso[df_progresso['Status Detalhado'] == 'Validado'])
            concluidos = desenvolvidos + comissionados + validados
            progresso = (concluidos/total*100) if total > 0 else 0
            
            st.progress(progresso/100, text=f"Progresso: **{progresso:.1f}%**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total", total)
            with col2:
                st.metric("Concluídos", concluidos)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Limpar filtros", use_container_width=True):
                for key in ['empresas_filter', 'tipos_filter', 'status_filter', 
                           'resp_dev_filter', 'resp_com_filter', 'resp_audit_filter', 
                           'data_inicio', 'data_fim']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        with col2:
            if st.button("📥 Exportar", use_container_width=True):
                st.info("Função de exportação em desenvolvimento")

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if empresas:
        df_filtrado = df_filtrado[df_filtrado['Empresa'].isin(empresas)]
    if tipos_equip:
        df_filtrado = df_filtrado[df_filtrado['Tipo Equipamento'].isin(tipos_equip)]
    if status_opcoes:
        df_filtrado = df_filtrado[df_filtrado['Status Detalhado'].isin(status_opcoes)]
    if responsaveis_dev:
        df_filtrado = df_filtrado[df_filtrado['Responsável Desenvolvimento'].isin(responsaveis_dev)]
    if responsaveis_com:
        df_filtrado = df_filtrado[df_filtrado['Responsável Comissionamento'].isin(responsaveis_com)]
    if responsaveis_audit:
        df_filtrado = df_filtrado[df_filtrado['Responsável Auditoria'].isin(responsaveis_audit)]
    if data_inicio and data_fim and 'Criado' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['Criado'].dt.date >= data_inicio) &
            (df_filtrado['Criado'].dt.date <= data_fim)
        ]

    # MÉTRICAS PRINCIPAIS
    st.markdown("<div class='section-title'>📈 Visão Geral do Portfólio</div>", unsafe_allow_html=True)
    
    if not df_filtrado.empty:
        # Calcular métricas
        total_equip = len(df_filtrado)
        qtd_emt = len(df_filtrado[df_filtrado['Empresa'] == 'EMT'])
        qtd_eto = len(df_filtrado[df_filtrado['Empresa'] == 'ETO'])
        
        qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Desenvolvido'])
        qtd_comissionados = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Comissionado'])
        qtd_validados = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Validado'])
        qtd_pendentes = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Pendente'])
        
        percent_desenv = (qtd_desenvolvidos/total_equip*100) if total_equip > 0 else 0
        percent_comiss = (qtd_comissionados/total_equip*100) if total_equip > 0 else 0
        percent_valid = (qtd_validados/total_equip*100) if total_equip > 0 else 0
        percent_pend = (qtd_pendentes/total_equip*100) if total_equip > 0 else 0
        
        # Cards
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #1e3c72;">
                <div><span style="font-size:0.95rem; color:#4a5568;">📦 Total</span></div>
                <div style="font-size:2rem; font-weight:700; color:#1e3c72;">{total_equip}</div>
                <div style="font-size:0.8rem; color:#718096;">ativos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #2a5298;">
                <div><span style="font-size:0.95rem; color:#4a5568;">⚡ EMT</span></div>
                <div style="font-size:2rem; font-weight:700; color:#2a5298;">{qtd_emt}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_desenv:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #4a7ab0;">
                <div><span style="font-size:0.95rem; color:#4a5568;">🔧 ETO</span></div>
                <div style="font-size:2rem; font-weight:700; color:#4a7ab0;">{qtd_eto}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_eto:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #28a745;">
                <div><span style="font-size:0.95rem; color:#4a5568;">✅ Desenv.</span></div>
                <div style="font-size:1.5rem; font-weight:700; color:#28a745;">{qtd_desenvolvidos}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_desenv:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #17a2b8;">
                <div><span style="font-size:0.95rem; color:#4a5568;">🔧 Comiss.</span></div>
                <div style="font-size:1.5rem; font-weight:700; color:#17a2b8;">{qtd_comissionados}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_comiss:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #007bff;">
                <div><span style="font-size:0.95rem; color:#4a5568;">✅ Valid.</span></div>
                <div style="font-size:1.5rem; font-weight:700; color:#007bff;">{qtd_validados}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_valid:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #dc3545;">
                <div><span style="font-size:0.95rem; color:#4a5568;">⏳ Pend.</span></div>
                <div style="font-size:1.5rem; font-weight:700; color:#dc3545;">{qtd_pendentes}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_pend:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # TABS
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Visão Geral", 
            "📈 Análise de Desempenho", 
            "👥 Alocação de Recursos",
            "📋 Dados Completos"
        ])

        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza
                status_counts = df_filtrado['Status Detalhado'].dropna().value_counts().reset_index()
                status_counts.columns = ['Status', 'Quantidade']
                
                ordem_status = ['Desenvolvido', 'Comissionado', 'Validado', 'Pendente']
                status_counts = status_counts[status_counts['Status'].isin(ordem_status)]
                
                if not status_counts.empty:
                    status_counts['Status'] = pd.Categorical(
                        status_counts['Status'], 
                        categories=ordem_status, 
                        ordered=True
                    )
                    status_counts = status_counts.sort_values('Status')
                    
                    cores_status = {
                        'Desenvolvido': '#28a745',
                        'Comissionado': '#17a2b8',
                        'Validado': '#007bff',
                        'Pendente': '#dc3545'
                    }
                    
                    fig_status = px.pie(
                        status_counts, 
                        values='Quantidade', 
                        names='Status',
                        color='Status',
                        color_discrete_map=cores_status
                    )
                    
                    fig_status = configurar_grafico_corporativo(fig_status, "Distribuição por Status", 400)
                    fig_status.update_traces(
                        textposition='inside', 
                        textinfo='percent+label+value',
                        texttemplate='%{label}<br>%{percent}<br>(%{value})'
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                tipo_counts = df_filtrado['Tipo Equipamento'].value_counts().reset_index()
                tipo_counts.columns = ['Tipo Equipamento', 'Quantidade']
                tipo_counts = tipo_counts.sort_values('Quantidade', ascending=True)
                
                fig_tipo = px.bar(
                    tipo_counts, 
                    x='Quantidade', 
                    y='Tipo Equipamento',
                    orientation='h',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    text='Quantidade'
                )
                fig_tipo = configurar_grafico_corporativo(fig_tipo, "Distribuição por Tipo", 400)
                fig_tipo.update_traces(textposition='outside')
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            # Evolução temporal
            if 'Criado' in df_filtrado.columns and not df_filtrado['Criado'].isna().all():
                st.markdown("### 📅 Evolução Temporal")
                
                df_temp = df_filtrado.copy()
                df_temp['Mês'] = df_temp['Criado'].dt.to_period('M').astype(str)
                
                evolucao = df_temp.groupby(['Mês', 'Status Detalhado']).size().reset_index(name='Quantidade')
                evolucao = evolucao.sort_values('Mês')
                
                cores_status = {
                    'Desenvolvido': '#28a745',
                    'Comissionado': '#17a2b8',
                    'Validado': '#007bff',
                    'Pendente': '#dc3545'
                }
                
                if not evolucao.empty:
                    fig_evolucao = px.bar(
                        evolucao, 
                        x='Mês', 
                        y='Quantidade', 
                        color='Status Detalhado',
                        color_discrete_map=cores_status,
                        text='Quantidade',
                        barmode='stack'
                    )
                    
                    fig_evolucao.update_traces(textposition='inside')
                    fig_evolucao = configurar_grafico_corporativo(fig_evolucao, "Evolução por Mês", 450)
                    fig_evolucao.update_layout(xaxis_tickangle=45)
                    
                    st.plotly_chart(fig_evolucao, use_container_width=True)

        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                cross_tab = pd.crosstab(
                    df_filtrado['Empresa'], 
                    df_filtrado['Status Detalhado'],
                    margins=True,
                    margins_name='Total'
                )
                st.markdown("### 📊 Empresa vs Status")
                st.dataframe(cross_tab, use_container_width=True)
            
            with col2:
                cross_tab_tipo = pd.crosstab(
                    df_filtrado['Tipo Equipamento'], 
                    df_filtrado['Status Detalhado'],
                    margins=True,
                    margins_name='Total'
                )
                st.markdown("### 📊 Tipo vs Status")
                st.dataframe(cross_tab_tipo, use_container_width=True)

        with tab3:
            st.markdown("### 👥 Responsáveis")
            
            tab_resp1, tab_resp2, tab_resp3 = st.tabs([
                "👨‍💻 Desenvolvimento", 
                "🔧 Comissionamento", 
                "📋 Auditoria"
            ])
            
            with tab_resp1:
                if 'Responsável Desenvolvimento' in df_filtrado.columns:
                    df_dev = df_filtrado[df_filtrado['Responsável Desenvolvimento'] != 'Não atribuído']
                    
                    if not df_dev.empty:
                        resp_counts = df_dev['Responsável Desenvolvimento'].value_counts().head(10)
                        
                        fig = px.bar(
                            x=resp_counts.values,
                            y=resp_counts.index,
                            orientation='h',
                            title='Top 10 - Desenvolvimento',
                            color=resp_counts.values,
                            color_continuous_scale='Viridis',
                            text=resp_counts.values
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab_resp2:
                if 'Responsável Comissionamento' in df_filtrado.columns:
                    df_com = df_filtrado[df_filtrado['Responsável Comissionamento'] != 'Não atribuído']
                    
                    if not df_com.empty:
                        resp_counts = df_com['Responsável Comissionamento'].value_counts().head(10)
                        
                        fig = px.bar(
                            x=resp_counts.values,
                            y=resp_counts.index,
                            orientation='h',
                            title='Top 10 - Comissionamento',
                            color=resp_counts.values,
                            color_continuous_scale='Plasma',
                            text=resp_counts.values
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab_resp3:
                if 'Responsável Auditoria' in df_filtrado.columns:
                    df_aud = df_filtrado[df_filtrado['Responsável Auditoria'] != 'Não atribuído']
                    
                    if not df_aud.empty:
                        resp_counts = df_aud['Responsável Auditoria'].value_counts().head(10)
                        
                        fig = px.bar(
                            x=resp_counts.values,
                            y=resp_counts.index,
                            orientation='h',
                            title='Top 10 - Auditoria',
                            color=resp_counts.values,
                            color_continuous_scale='Magma',
                            text=resp_counts.values
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.markdown("### 📋 Dados")
            
            colunas_padrao = ['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                             'Responsável Desenvolvimento', 'Responsável Comissionamento',
                             'Responsável Auditoria', 'Status Detalhado', 'Empresa']
            
            colunas = st.multiselect(
                "Colunas",
                options=df_filtrado.columns.tolist(),
                default=[c for c in colunas_padrao if c in df_filtrado.columns]
            )
            
            if colunas:
                st.dataframe(df_filtrado[colunas], use_container_width=True, height=500)

                # RODAPÉ
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong>© 2026 Energisa</strong><br>
                Versão 2.0.0
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong>🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}</strong><br>
                Fonte: {fonte.upper()}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong>📊 Registros:</strong> {total_equip}<br>
                <strong>✅ Concluídos:</strong> {qtd_desenvolvidos + qtd_comissionados + qtd_validados}
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style='color:#4a5568; font-size:0.85rem; text-align:right;'>
                <strong>📞 Suporte</strong><br>
                kewin.ferreira@energisa.com.br
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")

else:
    st.error("❌ Não foi possível carregar os dados.")
    
    # Instruções de configuração
    with st.expander("🔧 Configuração do GitHub"):
        st.markdown("""
        ### Para configurar o GitHub:
        
        1. **Crie um token no GitHub:**
           - Acesse: https://github.com/settings/tokens
           - Clique em "Generate new token (classic)"
           - Selecione o escopo: `repo`
           - Copie o token gerado
        
        2. **Configure no Streamlit Cloud:**
           - Vá para seu app no Streamlit Cloud
           - Settings > Secrets
           - Adicione:
           ```toml
           GITHUB_TOKEN = "seu_token_aqui"
           GITHUB_REPO = "seu_usuario/seu_repositorio"
           GITHUB_FILE_PATH = "caminho/do/arquivo.csv"
