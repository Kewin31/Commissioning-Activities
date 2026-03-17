import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import io
import base64
from github import Github
from github import GithubException
import tempfile
import time
import locale
from dateutil.relativedelta import relativedelta

# Tentar configurar locale para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except:
        pass

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Desenvolvimentos/Comissionamentos | Fábrica SCADA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNÇÕES DE FORMATAÇÃO DE DATA EM PORTUGUÊS
# ============================================
def formatar_data_portugues(data, formato='mes'):
    """Formata datas em português"""
    if pd.isna(data):
        return ""
    
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    dias_semana_pt = {
        0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
        3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
    }
    
    if formato == 'dia':
        return f"{dias_semana_pt[data.weekday()]}, {data.day} de {meses_pt[data.month]}"
    elif formato == 'mes':
        return f"{meses_pt[data.month]}/{data.year}"
    elif formato == 'ano':
        return f"{data.year}"
    else:
        return data.strftime('%d/%m/%Y')

# ============================================
# CONFIGURAÇÕES DO GITHUB
# ============================================
def get_github_config():
    """Obtém configurações do GitHub do Streamlit Secrets com validação"""
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
    """Testa a conexão com o GitHub"""
    try:
        token, repo_name, _ = get_github_config()
        
        if not token or not repo_name:
            return False, "Configurações incompletas"
        
        g = Github(token)
        user = g.get_user()
        repo = g.get_repo(repo_name)
        
        return True, f"Conectado como {user.login} | Repositório: {repo_name}"
        
    except GithubException as e:
        if e.status == 401:
            return False, "Token inválido ou expirado."
        elif e.status == 404:
            return False, f"Repositório '{repo_name}' não encontrado."
        else:
            return False, f"Erro GitHub: {e.status}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def atualizar_dados_github(arquivo_upload, branch="main"):
    """Atualiza o arquivo no GitHub com o novo arquivo enviado"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            st.error("❌ Configurações do GitHub incompletas.")
            return False
        
        if arquivo_upload is None:
            st.error("❌ Nenhum arquivo selecionado.")
            return False
        
        if not arquivo_upload.name.endswith('.csv'):
            st.error("❌ O arquivo deve ser do tipo CSV.")
            return False
        
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
            if e.status == 401:
                st.error("❌ Token inválido ou expirado.")
                return False
            elif e.status == 404:
                st.error(f"❌ Repositório '{repo_name}' não encontrado.")
                return False
            else:
                raise e
        
        file_content = arquivo_upload.read()
        
        try:
            df_temp = pd.read_csv(io.BytesIO(file_content), encoding='utf-8-sig')
            st.success(f"✅ CSV válido! {len(df_temp)} linhas")
        except Exception as e:
            st.error(f"❌ Arquivo CSV inválido: {str(e)}")
            return False
        
        try:
            contents = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                path=file_path,
                message=f"📦 Atualização - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                content=file_content,
                sha=contents.sha,
                branch=branch
            )
            st.success(f"✅ Arquivo atualizado no GitHub!")
            
        except GithubException as e:
            if e.status == 404:
                try:
                    repo.create_file(
                        path=file_path,
                        message=f"📦 Criação - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        content=file_content,
                        branch=branch
                    )
                    st.success(f"✅ Arquivo criado no GitHub!")
                except Exception as create_error:
                    st.error(f"❌ Erro ao criar arquivo: {str(create_error)}")
                    return False
            else:
                st.error(f"❌ Erro GitHub: {e.status}")
                return False
        
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao atualizar GitHub: {str(e)}")
        return False

def load_data_from_github():
    """Carrega dados exclusivamente do GitHub"""
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
                st.error("❌ Token GitHub inválido ou expirado.")
                return None
            elif e.status == 404:
                st.error(f"❌ Arquivo não encontrado.")
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
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
    
    .section-title {
        color: #0a1a3c;
        font-size: 1.4rem;
        font-weight: 600;
        margin: 1.8rem 0 1.2rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.8rem 1rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 1rem -1rem;
        text-align: center;
        color: white;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #15355e 0%, #1e3c72 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30,60,114,0.3);
    }
    
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
    
    .company-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-emt {
        background-color: #2a5298;
        color: white;
    }
    .badge-eto {
        background-color: #4a7ab0;
        color: white;
    }
    
    /* Estilo para as abas de filtro */
    .filtro-aba {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

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

# CORES EXECUTIVAS PARA OS GRÁFICOS - Atualizado com Necessário Revisão
cores_executivas = {
    'Desenvolvido': '#2E7D32',  # Verde escuro
    'Comissionado': '#1976D2',   # Azul
    'Validado': '#1565C0',       # Azul escuro
    'Revisão': '#FF8F00',        # Amarelo alaranjado (para exibição)
    'Necessário Revisão': '#FF8F00',  # Amarelo alaranjado (para correspondência)
    'Pendente': '#C62828',        # Vermelho escuro
    'EMT': '#1e3c72',             # Azul escuro corporativo
    'ETO': '#4a7ab0'              # Azul médio corporativo
}

# Cores para gráficos de linha
cores_linhas = {
    'Desenvolvido': '#2E7D32',
    'Comissionado': '#1976D2',
    'Validado': '#1565C0',
    'Revisão': '#FF8F00',
    'Necessário Revisão': '#FF8F00',
    'Pendente': '#C62828'
}

# Lista de status válidos para referência
STATUS_VALIDOS = ['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão', 'Pendente']
STATUS_PARA_EXIBICAO = {
    'Necessário Revisão': 'Revisão',  # Mapeia para exibição mais amigável
}

@st.cache_data(ttl=300)
def load_data(force_github=False):
    """Carrega dados do GitHub ou local"""
    try:
        df = None
        fonte = "local"
        
        if force_github:
            st.info("🔄 Carregando dados do GitHub...")
            df = load_data_from_github()
            if df is not None:
                fonte = "github"
                st.success("✅ Dados carregados do GitHub!")
        
        if df is None:
            caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
            
            if os.path.exists(caminho_arquivo):
                df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
                st.info(f"📁 Dados carregados do arquivo local")
            else:
                st.warning("⚠️ Nenhum arquivo encontrado. Usando dados de exemplo.")
                dados_exemplo = {
                    'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 101)],
                    'Chamado Desenvolvimento': [f'CHAMADO-{i}' for i in range(1001, 1101)],
                    'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor', 'Relé', 'Medidor'], 100),
                    'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Souza', 'Não atribuído'], 100),
                    'Responsável Comissionamento': np.random.choice(['Roberto Lima', 'Carla Mendes', 'Paulo Ferreira', 'Não atribuído'], 100),
                    'Responsável Auditoria': np.random.choice(['Fernando Alves', 'Lucia Santos', 'Marcos Paulo', 'Não atribuído'], 100),
                    'Fase': np.random.choice(['DEV', 'COM', 'VAL', 'PEN', 'REV'], 100, p=[0.25, 0.2, 0.15, 0.25, 0.15]),
                    'Status': np.random.choice(['Desenvolvido', 'Em andamento', 'Pendente', 'Necessário Revisão'], 100, p=[0.35, 0.3, 0.2, 0.15]),
                    'Empresa': np.random.choice(['EMT', 'ETO'], 100),
                    'Criado': pd.date_range(start='2024-01-01', periods=100, freq='D').strftime('%d/%m/%Y %H:%M'),
                    'Modificado': pd.date_range(start='2024-02-01', periods=100, freq='D').strftime('%d/%m/%Y %H:%M')
                }
                df = pd.DataFrame(dados_exemplo)
        
        if df is not None:
            # CORREÇÃO PRINCIPAL: Processar corretamente o status de revisão
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
            
            # CORREÇÃO: Identificar e padronizar a coluna de status
            # Primeiro, verificar qual coluna de status existe
            coluna_status_original = None
            for col in ['Status', 'Fase', 'Status Detalhado']:
                if col in df.columns:
                    coluna_status_original = col
                    break
            
            if coluna_status_original:
                # Limpar e padronizar a coluna de status
                df[coluna_status_original] = df[coluna_status_original].fillna('Pendente')
                df[coluna_status_original] = df[coluna_status_original].astype(str).str.strip()
                
                # CORREÇÃO: Mapear "Necessário Revisão" para o formato correto
                # Vamos manter o valor original mas criar uma coluna padronizada
                df['Status Original'] = df[coluna_status_original]
                
                # Mapear variações do status de revisão
                mapa_revisao = {
                    'Necessário Revisão': 'Necessário Revisão',
                    'Necessario Revisão': 'Necessário Revisão',
                    'Revisão': 'Necessário Revisão',
                    'Revisao': 'Necessário Revisão',
                    'REV': 'Necessário Revisão'
                }
                
                # Função para padronizar status
                def padronizar_status(valor):
                    valor_str = str(valor).strip()
                    
                    # Verificar se é um dos status de revisão
                    for chave in mapa_revisao:
                        if chave.lower() in valor_str.lower() or valor_str.lower() == chave.lower():
                            return 'Necessário Revisão'
                    
                    # Mapear Fases
                    mapa_fases = {
                        'DEV': 'Desenvolvido',
                        'COM': 'Comissionado',
                        'VAL': 'Validado',
                        'PEN': 'Pendente'
                    }
                    
                    if valor_str in mapa_fases:
                        return mapa_fases[valor_str]
                    
                    # Manter outros valores se forem válidos
                    if valor_str in STATUS_VALIDOS:
                        return valor_str
                    
                    # Valores comuns que podem aparecer
                    if 'desenvolv' in valor_str.lower():
                        return 'Desenvolvido'
                    elif 'comission' in valor_str.lower():
                        return 'Comissionado'
                    elif 'valid' in valor_str.lower():
                        return 'Validado'
                    elif 'pend' in valor_str.lower():
                        return 'Pendente'
                    
                    # Se não identificou, retornar original
                    return valor_str
                
                # Aplicar padronização
                df['Status Detalhado'] = df[coluna_status_original].apply(padronizar_status)
                
                # Garantir que todos os status estão na lista válida
                df.loc[~df['Status Detalhado'].isin(STATUS_VALIDOS), 'Status Detalhado'] = 'Pendente'
            
            else:
                # Se não tem coluna de status, criar uma padrão
                df['Status Detalhado'] = 'Pendente'
            
            # CORREÇÃO: Para exibição nos gráficos, podemos usar um nome mais curto
            df['Status Exibição'] = df['Status Detalhado'].apply(
                lambda x: 'Revisão' if x == 'Necessário Revisão' else x
            )
            
            # Processar datas
            if 'Criado' in df.columns:
                df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M', errors='coerce')
            if 'Modificado' in df.columns:
                df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            # Adicionar colunas auxiliares para análise
            if 'Criado' in df.columns:
                df['Ano'] = df['Criado'].dt.year
                df['Mês'] = df['Criado'].dt.month
                df['Mês/Ano'] = df['Criado'].dt.to_period('M').astype(str)
                df['Semana'] = df['Criado'].dt.strftime('%Y-%W')
                df['Dia'] = df['Criado'].dt.date
                df['Dia da Semana'] = df['Criado'].dt.day_name()
                df['Mês Nome'] = df['Criado'].dt.month.map({
                    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
                })
        
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
        
        st.markdown("### 📊 Fonte de Dados")
        
        if fonte == "github":
            st.success("✅ Conectado ao GitHub")
        elif fonte == "local":
            st.info("📁 Modo local")
        else:
            st.warning("⚠️ Dados de exemplo")
        
        with st.expander("🔌 Status da Conexão GitHub", expanded=False):
            conectado, mensagem = test_github_connection()
            
            if conectado:
                st.success(f"✅ {mensagem}")
            else:
                st.error(f"❌ {mensagem}")
        
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
        
        with st.expander("📤 Upload para GitHub", expanded=True):
            st.markdown("""
            <p style='font-size:0.85rem; color:#718096; margin-bottom:10px;'>
                Envie um novo arquivo CSV para atualizar a base no GitHub.
            </p>
            """, unsafe_allow_html=True)
            
            branch = st.selectbox("🌿 Branch", ["main", "master"], index=0)
            
            arquivo_upload = st.file_uploader(
                "Selecionar arquivo CSV",
                type=['csv'],
                key="github_upload"
            )
            
            if arquivo_upload is not None:
                try:
                    df_preview = pd.read_csv(io.BytesIO(arquivo_upload.getvalue()), 
                                            encoding='utf-8-sig', nrows=5)
                    st.info(f"📁 {arquivo_upload.name}")
                    
                    with st.expander("Preview"):
                        st.dataframe(df_preview, use_container_width=True)
                except:
                    st.warning("Não foi possível ler o preview")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown('<div class="update-button">', unsafe_allow_html=True)
                    if st.button("⬆️ Upload", use_container_width=True):
                        with st.spinner("Enviando..."):
                            if atualizar_dados_github(arquivo_upload, branch):
                                st.success("✅ Upload concluído!")
                                time.sleep(2)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 📋 Filtros")
        
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
            # Usar Status Exibição para filtros mais amigáveis
            opcoes_status = sorted(df['Status Exibição'].unique())
            status_opcoes = st.multiselect(
                "Status",
                options=opcoes_status,
                default=opcoes_status,
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
        
        if not df.empty:
            st.markdown("### 📊 Progresso")
            
            df_progresso = df.copy()
            if empresas:
                df_progresso = df_progresso[df_progresso['Empresa'].isin(empresas)]
            
            total = len(df_progresso)
            desenvolvidos = len(df_progresso[df_progresso['Status Detalhado'] == 'Desenvolvido'])
            comissionados = len(df_progresso[df_progresso['Status Detalhado'] == 'Comissionado'])
            validados = len(df_progresso[df_progresso['Status Detalhado'] == 'Validado'])
            revisao = len(df_progresso[df_progresso['Status Detalhado'] == 'Necessário Revisão'])
            concluidos = validados  # CORREÇÃO: Concluídos agora são apenas os validados
            progresso = (concluidos/total*100) if total > 0 else 0
            
            st.progress(progresso/100, text=f"Progresso: **{progresso:.1f}%**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total", total)
            with col2:
                st.metric("Validados", validados)  # CORREÇÃO: Mudado de Concluídos para Validados
        
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
        # Filtrar usando Status Exibição
        df_filtrado = df_filtrado[df_filtrado['Status Exibição'].isin(status_opcoes)]
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

    # MÉTRICAS PRINCIPAIS - CORRIGIDAS
    st.markdown("<div class='section-title'>📈 Visão Geral do Portfólio</div>", unsafe_allow_html=True)
    
    if not df_filtrado.empty:
        total_equip = len(df_filtrado)
        
        qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Desenvolvido'])
        qtd_comissionados = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Comissionado'])
        qtd_validados = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Validado'])
        qtd_revisao = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Necessário Revisão'])
        qtd_pendentes = len(df_filtrado[df_filtrado['Status Detalhado'] == 'Pendente'])
        
        percent_desenv = (qtd_desenvolvidos/total_equip*100) if total_equip > 0 else 0
        percent_comiss = (qtd_comissionados/total_equip*100) if total_equip > 0 else 0
        percent_valid = (qtd_validados/total_equip*100) if total_equip > 0 else 0
        percent_revisao = (qtd_revisao/total_equip*100) if total_equip > 0 else 0
        percent_pend = (qtd_pendentes/total_equip*100) if total_equip > 0 else 0
        
        # CORREÇÃO: Cards corrigidos para mostrar a hierarquia correta
        # Desenvolvido → Comissionado → Validado (Validado é o estágio final)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #1e3c72;">
                <div><span style="font-size:0.95rem; color:#4a5568;">📦 Total Cadastrado</span></div>
                <div style="font-size:2rem; font-weight:700; color:#1e3c72;">{total_equip}</div>
                <div style="font-size:0.8rem; color:#718096;">ativos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #2E7D32;">
                <div><span style="font-size:0.95rem; color:#4a5568;">⚙️ Desenvolvidos</span></div>
                <div style="font-size:2rem; font-weight:700; color:#2E7D32;">{qtd_desenvolvidos}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_desenv:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #1976D2;">
                <div><span style="font-size:0.95rem; color:#4a5568;">🔧 Comissionados</span></div>
                <div style="font-size:2rem; font-weight:700; color:#1976D2;">{qtd_comissionados}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_comiss:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #1565C0;">
                <div><span style="font-size:0.95rem; color:#4a5568;">✅ Validados</span></div>
                <div style="font-size:2rem; font-weight:700; color:#1565C0;">{qtd_validados}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_valid:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #FF8F00;">
                <div><span style="font-size:0.95rem; color:#4a5568;">📝 Em Revisão</span></div>
                <div style="font-size:2rem; font-weight:700; color:#FF8F00;">{qtd_revisao}</div>
                <div style="font-size:0.8rem; color:#718096;">{percent_revisao:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # TABS
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Visão Geral", 
            "📈 Evolução Temporal",
            "👥 Performance por Responsável",
            "🏢 Comissionamento por Empresa"
        ])

        with tab1:
            st.markdown("### 📊 Desenvolvimento e Comissionamento por Empresa")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### EMT")
                df_emt = df_filtrado[df_filtrado['Empresa'] == 'EMT']
                
                if not df_emt.empty:
                    # Usar Status Exibição para os gráficos
                    status_emt = df_emt['Status Exibição'].value_counts().reset_index()
                    status_emt.columns = ['Status', 'Quantidade']
                    
                    fig_emt = px.pie(
                        status_emt, 
                        values='Quantidade', 
                        names='Status',
                        color='Status',
                        color_discrete_map={
                            'Desenvolvido': cores_executivas['Desenvolvido'],
                            'Comissionado': cores_executivas['Comissionado'],
                            'Validado': cores_executivas['Validado'],
                            'Revisão': cores_executivas['Revisão'],
                            'Pendente': cores_executivas['Pendente']
                        }
                    )
                    fig_emt = configurar_grafico_corporativo(fig_emt, "EMT", 350)
                    fig_emt.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        texttemplate='%{label}<br>%{percent}'
                    )
                    st.plotly_chart(fig_emt, use_container_width=True)
                else:
                    st.info("Sem dados para EMT")
            
            with col2:
                st.markdown("#### ETO")
                df_eto = df_filtrado[df_filtrado['Empresa'] == 'ETO']
                
                if not df_eto.empty:
                    # Usar Status Exibição para os gráficos
                    status_eto = df_eto['Status Exibição'].value_counts().reset_index()
                    status_eto.columns = ['Status', 'Quantidade']
                    
                    fig_eto = px.pie(
                        status_eto, 
                        values='Quantidade', 
                        names='Status',
                        color='Status',
                        color_discrete_map={
                            'Desenvolvido': cores_executivas['Desenvolvido'],
                            'Comissionado': cores_executivas['Comissionado'],
                            'Validado': cores_executivas['Validado'],
                            'Revisão': cores_executivas['Revisão'],
                            'Pendente': cores_executivas['Pendente']
                        }
                    )
                    fig_eto = configurar_grafico_corporativo(fig_eto, "ETO", 350)
                    fig_eto.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        texttemplate='%{label}<br>%{percent}'
                    )
                    st.plotly_chart(fig_eto, use_container_width=True)
                else:
                    st.info("Sem dados para ETO")
            
            # Gráfico comparativo
            st.markdown("### 📊 Comparativo EMT vs ETO")
            
            # Usar Status Exibição para o comparativo
            comparativo = df_filtrado.groupby(['Empresa', 'Status Exibição']).size().reset_index(name='Quantidade')
            
            if not comparativo.empty:
                fig_comp = px.bar(
                    comparativo,
                    x='Empresa',
                    y='Quantidade',
                    color='Status Exibição',
                    barmode='group',
                    color_discrete_map={
                        'Desenvolvido': cores_executivas['Desenvolvido'],
                        'Comissionado': cores_executivas['Comissionado'],
                        'Validado': cores_executivas['Validado'],
                        'Revisão': cores_executivas['Revisão'],
                        'Pendente': cores_executivas['Pendente']
                    },
                    text='Quantidade'
                )
                fig_comp = configurar_grafico_corporativo(fig_comp, "Comparativo por Empresa", 400)
                fig_comp.update_traces(textposition='outside')
                fig_comp.update_layout(
                    legend_title_text='Status',
                    xaxis_title='Empresa',
                    yaxis_title='Quantidade'
                )
                st.plotly_chart(fig_comp, use_container_width=True)

        with tab2:
            st.markdown("### 📈 Evolução Temporal")
            
            if 'Criado' in df_filtrado.columns and not df_filtrado['Criado'].isna().all():
                # Abas para filtros
                filtro_temporal_tab, grafico_tipo_tab = st.tabs([
                    "📅 Agregação Temporal", 
                    "📊 Tipo de Gráfico"
                ])
                
                with filtro_temporal_tab:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        dia_selecionado = st.checkbox("Dia", value=False, key="filtro_dia")
                    with col2:
                        mes_selecionado = st.checkbox("Mês", value=True, key="filtro_mes")
                    with col3:
                        ano_selecionado = st.checkbox("Ano", value=False, key="filtro_ano")
                    
                    # Determinar agregação baseada nos checkboxes
                    if dia_selecionado:
                        agregacao = 'Dia'
                    elif mes_selecionado:
                        agregacao = 'Mês'
                    elif ano_selecionado:
                        agregacao = 'Ano'
                    else:
                        agregacao = 'Mês'  # Padrão
                        st.info("Selecione pelo menos uma opção de agregação")
                
                with grafico_tipo_tab:
                    tipo_grafico = st.radio(
                        "Tipo de visualização:",
                        options=['Barras Empilhadas', 'Linhas'],
                        index=0,
                        horizontal=True,
                        key='tipo_grafico'
                    )
                    
                    incluir_empresa = st.checkbox("Separar por empresa", value=True, key='separar_empresa')
                
                if agregacao == 'Dia':
                    periodo_col = 'Dia'
                    titulo_periodo = 'Dia'
                elif agregacao == 'Mês':
                    periodo_col = 'Mês/Ano'
                    titulo_periodo = 'Mês'
                else:
                    periodo_col = 'Ano'
                    titulo_periodo = 'Ano'
                
                # Preparar dados
                df_temp = df_filtrado.copy()
                
                # Usar Status Exibição para evolução
                if incluir_empresa:
                    evolucao = df_temp.groupby([periodo_col, 'Empresa', 'Status Exibição']).size().reset_index(name='Quantidade')
                else:
                    evolucao = df_temp.groupby([periodo_col, 'Status Exibição']).size().reset_index(name='Quantidade')
                
                # Ordenar
                if agregacao == 'Mês':
                    evolucao = evolucao.sort_values(periodo_col)
                elif agregacao == 'Semana':
                    evolucao['Ano_Semana'] = evolucao[periodo_col].apply(
                        lambda x: (int(str(x).split('-')[0]), int(str(x).split('-')[1])) if '-' in str(x) else (0, 0)
                    )
                    evolucao = evolucao.sort_values('Ano_Semana')
                else:
                    evolucao = evolucao.sort_values(periodo_col)
                
                if not evolucao.empty:
                    if tipo_grafico == 'Barras Empilhadas':
                        if incluir_empresa:
                            fig_evolucao = px.bar(
                                evolucao,
                                x=periodo_col,
                                y='Quantidade',
                                color='Status Exibição',
                                facet_col='Empresa',
                                barmode='stack',
                                color_discrete_map=cores_executivas,
                                text='Quantidade'
                            )
                            fig_evolucao.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
                        else:
                            fig_evolucao = px.bar(
                                evolucao,
                                x=periodo_col,
                                y='Quantidade',
                                color='Status Exibição',
                                barmode='stack',
                                color_discrete_map=cores_executivas,
                                text='Quantidade'
                            )
                        
                        fig_evolucao.update_traces(textposition='inside')
                        
                    else:  # Linhas
                        if incluir_empresa:
                            fig_evolucao = px.line(
                                evolucao,
                                x=periodo_col,
                                y='Quantidade',
                                color='Status Exibição',
                                line_dash='Empresa',
                                markers=True,
                                color_discrete_map=cores_linhas
                            )
                        else:
                            fig_evolucao = px.line(
                                evolucao,
                                x=periodo_col,
                                y='Quantidade',
                                color='Status Exibição',
                                markers=True,
                                color_discrete_map=cores_linhas
                            )
                    
                    titulo = f"Evolução por {agregacao}"
                    if incluir_empresa:
                        titulo += " - Separado por Empresa"
                    
                    fig_evolucao = configurar_grafico_corporativo(fig_evolucao, titulo, 500)
                    
                    if agregacao == 'Dia':
                        fig_evolucao.update_layout(xaxis_tickangle=45)
                    
                    st.plotly_chart(fig_evolucao, use_container_width=True)
                    
                    # Tabela resumo
                    with st.expander("📊 Ver dados detalhados"):
                        if incluir_empresa:
                            tabela = evolucao.pivot_table(
                                index=periodo_col,
                                columns=['Empresa', 'Status Exibição'],
                                values='Quantidade',
                                fill_value=0
                            ).reset_index()
                        else:
                            tabela = evolucao.pivot_table(
                                index=periodo_col,
                                columns='Status Exibição',
                                values='Quantidade',
                                fill_value=0
                            ).reset_index()
                        
                        st.dataframe(tabela, use_container_width=True)
            else:
                st.info("Dados de data não disponíveis para evolução temporal")

        with tab3:
            st.markdown("### 👥 Performance por Responsável")
            
            tipo_geral = st.radio(
                "Selecionar tipo de responsável:",
                options=['Desenvolvimento', 'Comissionamento', 'Auditoria'],
                horizontal=True,
                key='tipo_resp_geral'
            )
            
            if tipo_geral == 'Desenvolvimento':
                col_resp = 'Responsável Desenvolvimento'
                cor_gradiente = 'Viridis'
            elif tipo_geral == 'Comissionamento':
                col_resp = 'Responsável Comissionamento'
                cor_gradiente = 'Plasma'
            else:
                col_resp = 'Responsável Auditoria'
                cor_gradiente = 'Magma'
            
            if col_resp in df_filtrado.columns:
                df_resp_geral = df_filtrado[df_filtrado[col_resp] != 'Não atribuído']
                
                if not df_resp_geral.empty:
                    # Ranking geral
                    st.markdown(f"#### 📊 Ranking Geral - {tipo_geral}")
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        ranking = df_resp_geral[col_resp].value_counts().reset_index()
                        ranking.columns = ['Responsável', 'Total']
                        
                        fig_ranking = px.bar(
                            ranking.head(15),
                            x='Total',
                            y='Responsável',
                            orientation='h',
                            title=f'Top 15 - Quantidade de Atividades',
                            color='Total',
                            color_continuous_scale=cor_gradiente,
                            text='Total'
                        )
                        fig_ranking.update_traces(textposition='outside')
                        fig_ranking.update_layout(height=500)
                        st.plotly_chart(fig_ranking, use_container_width=True)
                    
                    with col2:
                        # Distribuição de status por responsável
                        # Usar Status Exibição
                        resp_status = df_resp_geral.groupby([col_resp, 'Status Exibição']).size().reset_index(name='Quantidade')
                        top_responsaveis = ranking.head(10)['Responsável'].tolist()
                        resp_status_top = resp_status[resp_status[col_resp].isin(top_responsaveis)]
                        
                        fig_dist = px.bar(
                            resp_status_top,
                            x=col_resp,
                            y='Quantidade',
                            color='Status Exibição',
                            title='Distribuição de Status por Responsável',
                            barmode='stack',
                            color_discrete_map=cores_executivas,
                            text='Quantidade'
                        )
                        fig_dist.update_traces(textposition='inside')
                        fig_dist.update_layout(
                            xaxis_tickangle=45,
                            height=500
                        )
                        st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # Comparativo por empresa
                    if tipo_geral in ['Desenvolvimento', 'Comissionamento'] and 'Empresa' in df_resp_geral.columns:
                        st.markdown(f"#### 🔄 Distribuição de {tipo_geral} por Empresa")
                        
                        comparativo_resp = df_resp_geral.groupby(['Empresa', col_resp]).size().reset_index(name='Quantidade')
                        
                        # Pegar top 10 responsáveis no total
                        top_resp_geral = ranking.head(10)['Responsável'].tolist()
                        comparativo_top = comparativo_resp[comparativo_resp[col_resp].isin(top_resp_geral)]
                        
                        fig_comp_resp = px.bar(
                            comparativo_top,
                            x=col_resp,
                            y='Quantidade',
                            color='Empresa',
                            barmode='group',
                            title=f'Top Responsáveis - Distribuição por Empresa',
                            color_discrete_map={
                                'EMT': cores_executivas['EMT'],
                                'ETO': cores_executivas['ETO']
                            },
                            text='Quantidade'
                        )
                        fig_comp_resp.update_traces(textposition='outside')
                        fig_comp_resp.update_layout(
                            xaxis_tickangle=45,
                            height=450
                        )
                        st.plotly_chart(fig_comp_resp, use_container_width=True)
                else:
                    st.info(f"Nenhum responsável de {tipo_geral} atribuído")

        with tab4:
            st.markdown("### 🏢 Comissionamento por Empresa")
            
            # Selecionar empresa para análise detalhada
            empresa_selecionada = st.selectbox(
                "Selecionar Empresa",
                options=['EMT', 'ETO'] if 'EMT' in df_filtrado['Empresa'].values else df_filtrado['Empresa'].unique(),
                key='empresa_comissionamento'
            )
            
            df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa_selecionada]
            
            if not df_empresa.empty:
                st.markdown(f"#### 📊 Status de Comissionamento - {empresa_selecionada}")
                
                # Métricas da empresa
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_emp = len(df_empresa)
                    st.metric("Total de Equipamentos", total_emp)
                
                with col2:
                    comiss_emp = len(df_empresa[df_empresa['Status Detalhado'] == 'Comissionado'])
                    st.metric("Comissionados", comiss_emp)
                
                with col3:
                    valid_emp = len(df_empresa[df_empresa['Status Detalhado'] == 'Validado'])
                    st.metric("Validados", valid_emp)
                
                with col4:
                    revisao_emp = len(df_empresa[df_empresa['Status Detalhado'] == 'Necessário Revisão'])
                    st.metric("Em Revisão", revisao_emp)
                
                # Gráficos de comissionamento
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribuição de status
                    # Usar Status Exibição
                    status_emp = df_empresa['Status Exibição'].value_counts().reset_index()
                    status_emp.columns = ['Status', 'Quantidade']
                    
                    fig_status_emp = px.pie(
                        status_emp,
                        values='Quantidade',
                        names='Status',
                        title=f'Distribuição de Status - {empresa_selecionada}',
                        color='Status',
                        color_discrete_map=cores_executivas
                    )
                    fig_status_emp.update_traces(textposition='inside', textinfo='percent+label')
                    fig_status_emp.update_layout(height=400)
                    st.plotly_chart(fig_status_emp, use_container_width=True)
                
                with col2:
                    # Progresso de comissionamento por tipo de equipamento
                    if 'Tipo Equipamento' in df_empresa.columns:
                        tipo_comiss = df_empresa.groupby('Tipo Equipamento').apply(
                            lambda x: (len(x[x['Status Detalhado'].isin(['Comissionado', 'Validado'])]) / len(x) * 100)
                        ).reset_index(name='Taxa de Comissionamento (%)')
                        
                        tipo_comiss = tipo_comiss.sort_values('Taxa de Comissionamento (%)', ascending=False)
                        
                        fig_taxa_tipo = px.bar(
                            tipo_comiss.head(10),
                            x='Taxa de Comissionamento (%)',
                            y='Tipo Equipamento',
                            orientation='h',
                            title='Taxa de Comissionamento por Tipo de Equipamento',
                            color='Taxa de Comissionamento (%)',
                            color_continuous_scale='Blues',
                            text=tipo_comiss['Taxa de Comissionamento (%)'].head(10).round(1).astype(str) + '%'
                        )
                        fig_taxa_tipo.update_traces(textposition='outside')
                        fig_taxa_tipo.update_layout(
                            height=400,
                            xaxis_range=[0, 100]
                        )
                        st.plotly_chart(fig_taxa_tipo, use_container_width=True)
                
                # Responsáveis pelo comissionamento
                st.markdown(f"#### 👥 Responsáveis pelo Comissionamento - {empresa_selecionada}")
                
                if 'Responsável Comissionamento' in df_empresa.columns:
                    df_resp_com = df_empresa[df_empresa['Responsável Comissionamento'] != 'Não atribuído']
                    
                    if not df_resp_com.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            resp_com_counts = df_resp_com['Responsável Comissionamento'].value_counts().reset_index()
                            resp_com_counts.columns = ['Responsável', 'Quantidade']
                            
                            fig_resp_com = px.bar(
                                resp_com_counts.head(10),
                                x='Quantidade',
                                y='Responsável',
                                orientation='h',
                                title='Top 10 Responsáveis',
                                color='Quantidade',
                                color_continuous_scale='Blues',
                                text='Quantidade'
                            )
                            fig_resp_com.update_traces(textposition='outside')
                            fig_resp_com.update_layout(height=400)
                            st.plotly_chart(fig_resp_com, use_container_width=True)
                        
                        with col2:
                            # Taxa de sucesso por responsável
                            sucesso_resp = df_resp_com.groupby('Responsável Comissionamento').apply(
                                lambda x: (len(x[x['Status Detalhado'].isin(['Comissionado', 'Validado'])]) / len(x) * 100)
                            ).reset_index(name='Taxa de Sucesso (%)')
                            
                            sucesso_resp = sucesso_resp.sort_values('Taxa de Sucesso (%)', ascending=False).head(10)
                            
                            fig_sucesso = px.bar(
                                sucesso_resp,
                                x='Taxa de Sucesso (%)',
                                y='Responsável Comissionamento',
                                orientation='h',
                                title='Taxa de Sucesso por Responsável',
                                color='Taxa de Sucesso (%)',
                                color_continuous_scale='Greens',
                                text=sucesso_resp['Taxa de Sucesso (%)'].round(1).astype(str) + '%'
                            )
                            fig_sucesso.update_traces(textposition='outside')
                            fig_sucesso.update_layout(
                                height=400,
                                xaxis_range=[0, 100]
                            )
                            st.plotly_chart(fig_sucesso, use_container_width=True)
                    else:
                        st.info("Nenhum responsável de comissionamento atribuído")
                
                # Equipamentos Pendentes de Comissionamento
                with st.expander("📋 Equipamentos Pendentes de Comissionamento"):
                    # Tudo que não é Validado é considerado pendente (inclui Comissionado, Revisão, Pendente, Desenvolvido)
                    pendentes = df_empresa[df_empresa['Status Detalhado'] != 'Validado']
                    
                    if not pendentes.empty:
                        # Mostrar contagem incluindo todos os status não validados
                        st.warning(f"**{len(pendentes)} equipamentos** pendentes de validação encontrados")
                        
                        cols_mostrar = ['Cód. Equipamento', 'Tipo Equipamento', 'Status Detalhado', 
                                       'Responsável Desenvolvimento', 'Responsável Comissionamento']
                        cols_existentes = [c for c in cols_mostrar if c in pendentes.columns]
                        
                        # Adicionar contagem por status
                        status_counts = pendentes['Status Detalhado'].value_counts()
                        status_counts_display = status_counts.rename(index={'Necessário Revisão': 'Revisão'})
                        st.info("Distribuição dos pendentes: " + ", ".join([f"{k}: {v}" for k, v in status_counts_display.items()]))
                        
                        st.dataframe(pendentes[cols_existentes], use_container_width=True)
                    else:
                        st.success("🎉 Todos os equipamentos estão validados!")

        # RODAPÉ
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                "<div style='color:#4a5568; font-size:0.85rem;'>"
                "<strong>© 2026 Energisa</strong><br>"
                "Versão 3.2.0"
                "</div>", 
                unsafe_allow_html=True
            )
        
        with col2:
            data_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
            st.markdown(
                f"<div style='color:#4a5568; font-size:0.85rem;'>"
                f"<strong>🕒 {data_hora}</strong><br>"
                f"Fonte: {fonte.upper()}"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"<div style='color:#4a5568; font-size:0.85rem;'>"
                f"<strong>📊 Registros:</strong> {total_equip}<br>"
                f"<strong>✅ Validados:</strong> {qtd_validados}"
                f"</div>", 
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                "<div style='color:#4a5568; font-size:0.85rem; text-align:right;'>"
                "<strong>📞 Suporte</strong><br>"
                "kewin.ferreira@energisa.com.br"
                "</div>", 
                unsafe_allow_html=True
            )

    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")

else:
    st.error("❌ Não foi possível carregar os dados.")
    
    with st.expander("🔧 Configuração do GitHub"):
        texto_instrucoes = (
            "### Para configurar o GitHub:\n\n"
            "1. **Crie um token no GitHub:**\n"
            "   - Acesse: https://github.com/settings/tokens\n"
            "   - Clique em \"Generate new token (classic)\"\n"
            "   - Selecione o escopo: `repo`\n"
            "   - Copie o token gerado\n\n"
            "2. **Configure no Streamlit Cloud:**\n"
            "   - Vá para seu app no Streamlit Cloud\n"
            "   - Settings > Secrets\n"
            "   - Adicione:\n"
            "   ```toml\n"
            "   GITHUB_TOKEN = \"seu_token_aqui\"\n"
            "   GITHUB_REPO = \"seu_usuario/seu_repositorio\"\n"
            "   GITHUB_FILE_PATH = \"caminho/do/arquivo.csv\"\n"
            "   ```\n\n"
            "3. **Ou use modo local:**\n"
            "   - Coloque o arquivo CSV em: `data/Dados/Comissionamento AD - UNs.csv`"
        )
        st.markdown(texto_instrucoes, unsafe_allow_html=True)
