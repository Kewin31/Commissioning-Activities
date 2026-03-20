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
                return False, "Token inválido ou expirado"
            elif e.status == 404:
                return False, f"Repositório '{repo_name}' não encontrado"
            else:
                return False, f"Erro GitHub: {e.status}"
        
    except GithubException as e:
        if e.status == 401:
            return False, "Token inválido ou expirado"
        return False, f"Erro de conexão: {str(e)}"
    except Exception as e:
        return False, f"Erro: {str(e)}"

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
            return None
                
    except Exception as e:
        return None

def atualizar_dados_github(arquivo_upload, branch="main"):
    """Atualiza o arquivo no GitHub"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            return False
        
        if arquivo_upload is None:
            return False
        
        g = Github(token)
        
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
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
                return False
        
        return True
        
    except Exception as e:
        return False

# ============================================
# CSS PERSONALIZADO - ESTILO ENERGISA
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: #f3f4f6;
    }
    
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
    
    .fluxo-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
    }
    
    .fluxo-container:hover {
        box-shadow: 0 4px 12px rgba(0,89,115,0.1);
        border-color: #04d8d7;
    }
    
    .company-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
    }
    
    .company-card:hover {
        box-shadow: 0 4px 12px rgba(0,89,115,0.1);
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
        color: #6b7280;
        margin-top: 0.3rem;
    }
    
    .filter-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .footer {
        background: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-top: 3rem;
        box-shadow: 0 -1px 2px rgba(0,0,0,0.02);
        font-size: 0.85rem;
        color: #6b7280;
        border-top: 1px solid #e5e7eb;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #005973, #028a9f);
        color: white;
        border: none;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #006c84, #04d8d7);
    }
    
    .css-1d391kg, .css-1633s36 {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    
    /* Estilo para o popup de informações */
    .info-popup {
        background-color: #f8fafc;
        border-left: 4px solid #028a9f;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
        color: #1f2937;
    }
    
    .info-popup strong {
        color: #005973;
    }
    
    /* Estilo para métricas de destaque */
    .metric-highlight {
        background: linear-gradient(135deg, #f8fafc, #ffffff);
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    
    .metric-value-large {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CORES ENERGISA
# ============================================
CORES = {
    'Desenvolvido': '#2E7D32',
    'Comissionado': '#028a9f',
    'Validado': '#005973',
    'Necessário Revisão': '#F57C00',
    'Pendente': '#C62828',
    'EMT': '#028a9f',
    'ETO': '#005973',
}

# Ordem prioritária para status (críticos primeiro)
ORDEM_STATUS = ['Necessário Revisão', 'Pendente', 'Desenvolvido', 'Comissionado', 'Validado']

# ============================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================
def processar_dados(df):
    """Processa e padroniza os dados"""
    if df is None or df.empty:
        return df
    
    # Padronizar nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Mapeamento de colunas com os nomes EXATOS do seu CSV
    mapeamento_colunas = {
        'Cód. Equipamento': 'Codigo',
        'Cód.Equipamento': 'Codigo',
        'Título': 'Codigo',
        'Chamado Desenvolvimento': 'Chamado',
        'Tipo Equipamento': 'Tipo',
        'Empresa': 'Empresa',
        'Responsável Desenvolvimento': 'Resp_Dev',
        'Responsável Comissionamento': 'Resp_Com',
        'Responsável Auditoria': 'Resp_Audit',
        'Status': 'Status',
        'Criado': 'Criado',
        'Modificado': 'Modificado',
        'Modificado por': 'Modificado_por',
        'Revisões': 'Revisoes'
    }
    
    # Renomear colunas (silenciosamente, sem mensagens)
    for col_antiga, col_nova in mapeamento_colunas.items():
        if col_antiga in df.columns and col_nova not in df.columns:
            df.rename(columns={col_antiga: col_nova}, inplace=True)
    
    # Se a coluna Resp_Com não existir, criar fallback silencioso
    if 'Resp_Com' not in df.columns:
        if 'Modificado_por' in df.columns:
            df['Resp_Com'] = df.apply(
                lambda row: row['Modificado_por'] if row['Status'] in ['Comissionado', 'Validado'] else 'Não atribuído',
                axis=1
            )
        else:
            df['Resp_Com'] = 'Não atribuído'
    
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
            try:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y %H:%M', errors='coerce')
            except:
                try:
                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                except:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Criar colunas de tempo
    if 'Criado' in df.columns:
        df['Ano'] = df['Criado'].dt.year
        df['Mes'] = df['Criado'].dt.month
        df['Mes_Nome'] = df['Criado'].dt.month.map({
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        })
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
    else:
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
        df = load_data_from_github()
        
        if df is not None:
            return processar_dados(df), "github"
        
        caminho_local = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        if os.path.exists(caminho_local):
            df = pd.read_csv(caminho_local, encoding='utf-8-sig')
            return processar_dados(df), "local"
        
        # Dados de exemplo
        dados_exemplo = {
            'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 101)],
            'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 100),
            'Empresa': np.random.choice(['EMT', 'ETO'], 100),
            'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa'], 100),
            'Responsável Comissionamento': np.random.choice(['Carlos Lima', 'Ana Paula', 'Roberto Alves'], 100),
            'Responsável Auditoria': np.random.choice(['Fernando Costa', 'Lucia Santos'], 100),
            'Status': np.random.choice(['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão'], 100, 
                                      p=[0.5, 0.15, 0.25, 0.1]),
            'Criado': pd.date_range(start='2025-01-01', periods=100, freq='D').strftime('%d/%m/%Y %H:%M')
        }
        df = pd.DataFrame(dados_exemplo)
        return processar_dados(df), "exemplo"
        
    except Exception as e:
        return None, "erro"

# ============================================
# FUNÇÃO PARA LIMPAR FILTROS
# ============================================
def limpar_filtros():
    """Limpa todos os filtros do session_state"""
    for key in list(st.session_state.keys()):
        if key.startswith('filtro_'):
            del st.session_state[key]

# ============================================
# FUNÇÃO PARA POPUP DE INFORMAÇÕES
# ============================================
def mostrar_popup_calculos():
    """Mostra popup com explicação dos cálculos"""
    popup_html = """
    <div class="info-popup">
        <strong>📊 Como as taxas são calculadas:</strong><br><br>
        <strong>ETAPA 1 → 2:</strong> (Comissionados + Validados) / Desenvolvidos × 100<br>
        <em>Percentual do desenvolvimento que já passou pelo comissionamento</em><br><br>
        <strong>ETAPA 2 → 3:</strong> Validados / (Comissionados + Validados) × 100<br>
        <em>Percentual dos equipamentos comissionados que já foram validados</em><br><br>
        <strong>ETAPA 3:</strong> Validados / Total do Fluxo × 100<br>
        <em>Percentual de equipamentos validados sobre o total do fluxo</em><br><br>
        <strong>GARGALO:</strong> Em Revisão / Total do Fluxo × 100<br>
        <em>Percentual de equipamentos que necessitam de revisão</em><br><br>
        <strong>Legenda:</strong><br>
        • <span style="color:#2E7D32;">Desenvolvidos</span>: Aguardando comissionamento<br>
        • <span style="color:#028a9f;">Aguardando Validação</span>: Comissionados pendentes<br>
        • <span style="color:#005973;">Validados</span>: Processo concluído<br>
        • <span style="color:#F57C00;">Em Revisão</span>: Aguardando correções
    </div>
    """
    return popup_html

# ============================================
# FUNÇÃO PARA CRIAR GRÁFICO DE PIZZA MELHORADO
# ============================================
def criar_grafico_pizza_status(df_filtrado):
    """Cria gráfico de pizza com melhorias executivas"""
    
    # Contagem por status
    status_counts = df_filtrado['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    
    # Ordenação personalizada: críticos primeiro
    status_counts['Status'] = pd.Categorical(
        status_counts['Status'], 
        categories=ORDEM_STATUS, 
        ordered=True
    )
    status_counts = status_counts.sort_values('Status')
    
    # Calcular percentuais para anotações
    total_registros = status_counts['Quantidade'].sum()
    
    # Percentual de revisão (gargalo)
    pct_revisao = (
        status_counts[status_counts['Status'] == 'Necessário Revisão']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    # Percentual de pendentes
    pct_pendente = (
        status_counts[status_counts['Status'] == 'Pendente']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    # Percentual de validados (sucesso)
    pct_validado = (
        status_counts[status_counts['Status'] == 'Validado']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    # Definir quais fatias devem ser "explodidas" (destacadas)
    explode = [0.05 if status in ['Necessário Revisão', 'Pendente'] else 0 for status in status_counts['Status']]
    
    # Criar gráfico de pizza
    fig_status = px.pie(
        status_counts,
        values='Quantidade',
        names='Status',
        title='Distribuição por Status',
        color='Status',
        color_discrete_map=CORES,
        hole=0.4
    )
    
    # Configurar rótulos e aparência
    fig_status.update_traces(
        textposition='outside',
        textinfo='percent+label',
        texttemplate='%{label}<br>%{percent:.1%}',
        marker=dict(line=dict(color='white', width=2)),
        pull=explode,
        insidetextorientation='horizontal',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent:.1%}%<extra></extra>'
    )
    
    # Adicionar anotação principal com alerta de gargalo
    if pct_revisao > 10:
        msg_alerta = f"⚠️ ATENÇÃO: {pct_revisao:.1f}% dos equipamentos necessitam de revisão"
        cor_alerta = '#F57C00'
    elif pct_revisao > 5:
        msg_alerta = f"📌 Alerta: {pct_revisao:.1f}% em revisão - Acompanhar"
        cor_alerta = '#FFA726'
    else:
        msg_alerta = f"✅ Gargalo controlado: {pct_revisao:.1f}% em revisão"
        cor_alerta = '#2E7D32'
    
    fig_status.add_annotation(
        text=msg_alerta,
        x=0.5,
        y=-0.18,
        xref='paper',
        yref='paper',
        showarrow=False,
        font=dict(size=12, color=cor_alerta, weight='bold'),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor=cor_alerta,
        borderwidth=1,
        borderpad=4,
    )
    
    # Adicionar anotação secundária com resumo executivo
    resumo_texto = f"✓ {pct_validado:.1f}% concluídos | ⚠️ {pct_pendente:.1f}% pendentes"
    
    fig_status.add_annotation(
        text=resumo_texto,
        x=0.5,
        y=-0.28,
        xref='paper',
        yref='paper',
        showarrow=False,
        font=dict(size=10, color='#6b7280'),
        bgcolor='rgba(255,255,255,0.8)',
        borderwidth=0
    )
    
    # Configurar layout final
    fig_status.update_layout(
        showlegend=False,
        height=450,
        margin=dict(t=50, b=90, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font=dict(size=16, color='#1f2937'),
        title_x=0.5
    )
    
    return fig_status

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
            <h1>Monitoring Center</h1>
            <p>Acompanhamento de Comissionamento das unidades - EMT | ETO</p>
        </div>
        <div class="header-data">
            📅 {datetime.now().strftime('%d/%m/%Y')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR COM FILTROS
# ============================================

with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h3 style="color: #005973; margin-bottom: 0.5rem;">🎯 Filtros</h3>
        <p style="color: #6b7280; font-size: 0.85rem;">Selecione os critérios para análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FILTRO DE ANO
    st.markdown('<div class="filter-title">📅 Ano</div>', unsafe_allow_html=True)
    
    anos_disponiveis = sorted(df['Ano'].dropna().unique()) if 'Ano' in df.columns else []
    anos_opcoes = ["Todos os Anos"] + [int(ano) for ano in anos_disponiveis]
    
    ano_selecionado = st.selectbox(
        "Selecione o ano",
        options=anos_opcoes,
        index=0,
        label_visibility="collapsed",
        key="filtro_ano"
    )
    
    # FILTRO DE MÊS
    st.markdown('<div class="filter-title" style="margin-top: 1rem;">📆 Mês</div>', unsafe_allow_html=True)
    
    meses_nomes = ["Todos os Meses", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_selecionado = st.selectbox(
        "Selecione o mês",
        options=meses_nomes,
        index=0,
        label_visibility="collapsed",
        key="filtro_mes"
    )
    
    st.markdown("---")
    
    # FILTRO DE EMPRESA
    st.markdown('<div class="filter-title">🏢 Empresa</div>', unsafe_allow_html=True)
    
    empresas_opcoes = ["Todas"] + sorted(df['Empresa'].unique().tolist())
    empresa_selecionada = st.selectbox(
        "Selecione a empresa",
        options=empresas_opcoes,
        index=0,
        label_visibility="collapsed",
        key="filtro_empresa"
    )
    
    # FILTRO DE TIPO DE EQUIPAMENTO
    st.markdown('<div class="filter-title">🔧 Tipo Equipamento</div>', unsafe_allow_html=True)
    
    if 'Tipo' in df.columns:
        tipos_opcoes = ["Todos"] + sorted(df['Tipo'].unique().tolist())
        tipo_selecionado = st.selectbox(
            "Selecione o tipo",
            options=tipos_opcoes,
            index=0,
            label_visibility="collapsed",
            key="filtro_tipo"
        )
    else:
        tipo_selecionado = "Todos"
    
    # FILTRO DE STATUS
    st.markdown('<div class="filter-title">📊 Status</div>', unsafe_allow_html=True)
    
    status_opcoes = ["Todos"] + sorted(df['Status'].unique().tolist())
    status_selecionado = st.selectbox(
        "Selecione o status",
        options=status_opcoes,
        index=0,
        label_visibility="collapsed",
        key="filtro_status"
    )
    
    st.markdown("---")
    
    # Botão Limpar Filtros
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        limpar_filtros()
        st.rerun()

# ============================================
# APLICAR FILTROS
# ============================================

df_filtrado = df.copy()

if ano_selecionado != "Todos os Anos" and 'Ano' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_selecionado]

if mes_selecionado != "Todos os Meses" and 'Mes_Nome' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Mes_Nome'] == mes_selecionado]

if empresa_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_selecionada]

if tipo_selecionado != "Todos" and 'Tipo' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_selecionado]

if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Status'] == status_selecionado]

# ============================================
# ESTATÍSTICAS RÁPIDAS NA SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Visão Rápida")
    
    total_filtrado = len(df_filtrado)
    em_andamento = len(df_filtrado[df_filtrado['Status'].isin(['Desenvolvido', 'Comissionado'])])
    finalizados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])
    
    st.markdown(f"""
    <div style="background: white; padding: 1rem; border-radius: 12px; border-left: 4px solid #028a9f; border: 1px solid #e5e7eb;">
        <div style="display: flex; justify-content: space-between;">
            <span>📦 Total:</span> <strong>{total_filtrado}</strong>
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

# ============================================
# PAINEL PRINCIPAL
# ============================================

if not df_filtrado.empty:
    # Contagens por status
    qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
    qtd_aguardando_validacao = len(df_filtrado[df_filtrado['Status'] == 'Comissionado'])
    qtd_validados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    qtd_revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])
    
    # Total de equipamentos que já passaram pelo comissionamento
    total_comissionados = qtd_aguardando_validacao + qtd_validados
    
    # Total de itens no fluxo
    total_fluxo = qtd_desenvolvidos + qtd_aguardando_validacao + qtd_validados + qtd_revisao
    
    # Taxas de conversão
    taxa_desenv_para_comiss = (total_comissionados / qtd_desenvolvidos * 100) if qtd_desenvolvidos > 0 else 0
    taxa_comiss_para_valid = (qtd_validados / total_comissionados * 100) if total_comissionados > 0 else 0
    taxa_valid_sobre_total = (qtd_validados / total_fluxo * 100) if total_fluxo > 0 else 0
    taxa_revisao_sobre_total = (qtd_revisao / total_fluxo * 100) if total_fluxo > 0 else 0
    
    # VISUALIZAÇÃO DO FLUXO
    st.markdown("### 🔄 Progress Tracker")
    
    # Botão de informação com popup
    with st.expander("ℹ️ Detalhes dos cálculos", expanded=False):
        st.markdown(mostrar_popup_calculos(), unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Desenvolvido']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280;">ETAPA 1</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Desenvolvido']};">{qtd_desenvolvidos}</div>
                <div style="font-weight: 500;">Desenvolvidos</div>
                <div style="font-size: 0.85rem; color: #6b7280;">Aguardando comissionamento</div>
                <div style="margin-top: 0.5rem; background: #e0f7fa; border-radius: 20px; padding: 0.3rem;">
                    → {taxa_desenv_para_comiss:.1f}% já comissionados
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Comissionado']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280;">ETAPA 2</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Comissionado']};">{qtd_aguardando_validacao}</div>
                <div style="font-weight: 500;">Aguardando Validação</div>
                <div style="font-size: 0.85rem; color: #6b7280;">Comissionados pendentes</div>
                <div style="margin-top: 0.5rem; background: #e0f7fa; border-radius: 20px; padding: 0.3rem;">
                    → {taxa_comiss_para_valid:.1f}% já validados
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="fluxo-container" style="border-left: 4px solid {CORES['Validado']};">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280;">ETAPA 3</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Validado']};">{qtd_validados}</div>
                <div style="font-weight: 500;">Validados</div>
                <div style="font-size: 0.85rem; color: #6b7280;">Processo concluído</div>
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
                <div style="font-size: 0.9rem; color: #6b7280;">GARGALO</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {CORES['Necessário Revisão']};">{qtd_revisao}</div>
                <div style="font-weight: 500;">Em Revisão</div>
                <div style="font-size: 0.85rem; color: #6b7280;">Aguardando correções</div>
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
                    total_emp = len(df_emp)
                    aguardando_emp = len(df_emp[df_emp['Status'] == 'Comissionado'])
                    validados_emp = len(df_emp[df_emp['Status'] == 'Validado'])
                    comissionados_total_emp = aguardando_emp + validados_emp
                    
                    st.markdown(f"""
                    <div class="company-card">
                        <div class="company-title" style="color: {CORES[empresa]};">{empresa}</div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: #005973;">{total_emp}</div>
                                <div class="company-metric-label">Equipamentos cadastrados</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Comissionado']};">{comissionados_total_emp}</div>
                                <div class="company-metric-label">Comissionados no total</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Validado']};">{validados_emp}</div>
                                <div class="company-metric-label">Validados (concluídos)</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem;">
                            <div style="background: #e0f7fa; border-radius: 20px; padding: 0.5rem;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Progresso do fluxo:</span>
                                    <strong>{((comissionados_total_emp)/total_emp*100):.1f}%</strong>
                                </div>
                                <div style="width: 100%; background: #e5e7eb; height: 6px; border-radius: 3px; margin-top: 0.5rem;">
                                    <div style="width: {((comissionados_total_emp)/total_emp*100)}%; background: linear-gradient(90deg, #028a9f, #04d8d7); height: 6px; border-radius: 3px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Gráfico de distribuição - USANDO A FUNÇÃO MELHORADA
        st.markdown("### 📊 Distribuição do Portfólio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza melhorado com função dedicada
            fig_status = criar_grafico_pizza_status(df_filtrado)
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            if 'Tipo' in df_filtrado.columns:
                tipo_counts = df_filtrado['Tipo'].value_counts().head(8).reset_index()
                tipo_counts.columns = ['Tipo', 'Quantidade']
                
                fig_tipo = px.bar(
                    tipo_counts,
                    x='Quantidade',
                    y='Tipo',
                    orientation='h',
                    title='Tipos de Equipamento',
                    color='Quantidade',
                    color_continuous_scale=['#e0f7fa', '#028a9f', '#005973'],
                    text='Quantidade'
                )
                fig_tipo.update_traces(
                    textposition='outside',
                    texttemplate='%{text}',
                    hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
                )
                fig_tipo.update_layout(
                    height=450,
                    margin=dict(t=50, b=10, l=10, r=10),
                    xaxis_title="Quantidade",
                    yaxis_title="",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=14, color='#1f2937')
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
    
    with tab2:
        st.markdown("### 📈 Evolução do Fluxo")
        
        if 'Criado' in df_filtrado.columns:
            df_filtrado['Mes_Ano_Label'] = df_filtrado['Criado'].dt.strftime('%b/%Y')
            df_filtrado['Ano_Mes'] = df_filtrado['Criado'].dt.strftime('%Y-%m')
            
            evolucao = df_filtrado.groupby(['Ano_Mes', 'Mes_Ano_Label', 'Status']).size().reset_index(name='Quantidade')
            evolucao = evolucao.sort_values('Ano_Mes')
            
            fig_evolucao = px.line(
                evolucao,
                x='Mes_Ano_Label',
                y='Quantidade',
                color='Status',
                markers=True,
                title='Evolução Mensal por Status',
                color_discrete_map=CORES
            )
            fig_evolucao.update_traces(
                marker=dict(size=8),
                line=dict(width=2)
            )
            fig_evolucao.update_layout(
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade",
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
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
            fig_barras.update_traces(textposition='inside', texttemplate='%{text}')
            fig_barras.update_layout(
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_barras, use_container_width=True)
            
            st.markdown("### 📊 Taxas de Conversão")
            
            taxa_mensal = []
            for mes in evolucao['Ano_Mes'].unique():
                df_mes = df_filtrado[df_filtrado['Ano_Mes'] == mes]
                total_mes = len(df_mes)
                if total_mes > 0:
                    aguardando_mes = len(df_mes[df_mes['Status'] == 'Comissionado'])
                    validados_mes = len(df_mes[df_mes['Status'] == 'Validado'])
                    total_comiss_mes = aguardando_mes + validados_mes
                    
                    taxa_mensal.append({
                        'Mês': mes,
                        'Taxa Comissionamento': (total_comiss_mes / total_mes * 100) if total_mes > 0 else 0,
                        'Taxa Validação': (validados_mes / total_comiss_mes * 100) if total_comiss_mes > 0 else 0,
                        'Taxa Revisão': len(df_mes[df_mes['Status'] == 'Necessário Revisão']) / total_mes * 100 if total_mes > 0 else 0
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
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_taxas, use_container_width=True)
    
    with tab3:
        st.markdown("### 👥 Performance por Responsável")
        
        tipo_resp = st.radio(
            "Selecionar tipo:",
            options=['Desenvolvimento', 'Comissionamento', 'Auditoria'],
            horizontal=True,
            key='tipo_resp_tab'
        )
        
        mapa_colunas = {
            'Desenvolvimento': 'Resp_Dev',
            'Comissionamento': 'Resp_Com',
            'Auditoria': 'Resp_Audit'
        }
        
        col_resp = mapa_colunas[tipo_resp]
        
        if col_resp not in df_filtrado.columns:
            st.warning(f"⚠️ Coluna '{col_resp}' não encontrada nos dados.")
        else:
            df_resp = df_filtrado[df_filtrado[col_resp] != 'Não atribuído']
            
            if df_resp.empty:
                st.info(f"📌 Nenhum responsável de {tipo_resp} encontrado.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
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
                    fig_ranking.update_traces(
                        textposition='outside',
                        texttemplate='%{text}',
                        hovertemplate='<b>%{y}</b><br>Atividades: %{x}<extra></extra>'
                    )
                    fig_ranking.update_layout(
                        height=400,
                        xaxis_title="Quantidade de Atividades",
                        yaxis_title="",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_ranking, use_container_width=True)
                
                with col2:
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
                        fig_sucesso.update_traces(
                            textposition='outside',
                            texttemplate='%{text}',
                            hovertemplate='<b>%{y}</b><br>Taxa de Sucesso: %{x:.1f}%<br>Validados: %{customdata[0]}/%{customdata[1]}<extra></extra>',
                            customdata=df_sucesso[['Validados', 'Total']].values
                        )
                        fig_sucesso.update_layout(
                            height=400,
                            xaxis_title="Taxa de Sucesso (%)",
                            xaxis_range=[0, 100],
                            yaxis_title="",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_sucesso, use_container_width=True)
                
                st.markdown(f"#### 📊 Distribuição de Status por {tipo_resp}")
                
                top_resp = ranking['Responsável'].head(8).tolist()
                df_top = df_resp[df_resp[col_resp].isin(top_resp)]
                
                dist_status = df_top.groupby([col_resp, 'Status']).size().reset_index(name='Quantidade')
                
                if not dist_status.empty:
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
                    fig_dist.update_traces(textposition='inside', texttemplate='%{text}')
                    fig_dist.update_layout(
                        height=450,
                        xaxis_tickangle=45,
                        xaxis_title="",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
    
    with tab4:
        st.markdown("### 📋 Detalhamento dos Registros")
        
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
            st.metric("Responsáveis Desenvolvimento", len(df_filtrado['Resp_Dev'].unique()))
        
        colunas_mostrar = ['Codigo', 'Tipo', 'Empresa', 'Status', 'Resp_Dev', 'Resp_Com', 'Resp_Audit']
        colunas_existentes = [c for c in colunas_mostrar if c in df_filtrado.columns]
        
        if colunas_existentes:
            df_display = df_filtrado[colunas_existentes].copy()
            st.dataframe(df_display, use_container_width=True)
        
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
            st.dataframe(status_counts, use_container_width=True)
            
            if 'Tipo' in df_filtrado.columns:
                st.markdown("**Distribuição por Tipo de Equipamento:**")
                tipo_counts = df_filtrado['Tipo'].value_counts().reset_index()
                tipo_counts.columns = ['Tipo', 'Quantidade']
                st.dataframe(tipo_counts.head(15), use_container_width=True)
    
    # FOOTER
    st.markdown(f"""
    <div class="footer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>⚡ Radar de Comissionamento SCADA</strong> • Versão 5.0 • Energisa
            </div>
            <div>
                Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
            <div style="color: #6b7280;">
                {len(df_filtrado)} registros • {fonte.upper()}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
