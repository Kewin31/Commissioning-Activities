import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import os
import io
import base64
from github import Github
from github import GithubException
import tempfile
import time
from dateutil.relativedelta import relativedelta

# Importar o gerador de PDF
from pdf_generator import adicionar_botao_pdf_empresa

# Configuração da página
st.set_page_config(
    page_title="Dashboard Executivo | Fábrica SCADA",
    page_icon=":material/bolt:",
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

# ============================================
# IDENTIDADE VISUAL (mesmo padrão do dashboard Esteira SRE)
# ============================================
COR_VERDE_ESCURO = "#2E7D32"
COR_AZUL_PETROLEO = "#028a9f"
COR_AZUL_ESCURO = "#005973"
COR_LARANJA = "#F57C00"
COR_VERMELHO = "#C62828"
COR_CINZA_FUNDO = "#F8F9FA"
COR_CINZA_BORDA = "#E9ECEF"
COR_CINZA_TEXTO = "#6C757D"
COR_BRANCO = "#FFFFFF"
COR_PRETO_SUAVE = "#212529"

TZ_BR = ZoneInfo('America/Sao_Paulo')


def agora():
    """Data/hora de Brasília (o servidor do Streamlit Cloud roda em UTC)."""
    return datetime.now(TZ_BR).replace(tzinfo=None)


# Ícones SVG (estilo Lucide) usados nos blocos HTML; nos widgets usamos :material/...:
ICONES = {
    'grafico': '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    'check': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    'lista': '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    'revisao': '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    'atividade': '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    'calendario': '<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    'ajustes': '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/>',
    'alvo': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    'alerta': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>',
    'empresa': '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
    'info': '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/>',
    'raio': '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    'codigo': '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    'ferramenta': '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    'escudo': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/>',
    'pacote': '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    'engrenagem': '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    'equipe': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'email': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
}


def icone(nome, tamanho=20, cor="currentColor", espessura=2):
    """Ícone SVG inline para os blocos HTML (cards, títulos, rodapé)."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="{espessura}" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:-0.18em; flex-shrink:0;">{ICONES[nome]}</svg>')


def fmt_milhar(valor):
    return f"{int(valor):,}".replace(",", ".")


def num_br(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def titulo_secao(texto, icone_nome):
    """Título de seção com barra verde + ícone (igual ao dashboard SRE)."""
    st.markdown(f'<div class="section-title">{icone(icone_nome, 20, COR_AZUL_ESCURO)}<span>{texto}</span></div>',
                unsafe_allow_html=True)


# Tema único para todos os gráficos Plotly
pio.templates["energisa"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, 'Segoe UI', sans-serif", size=12, color=COR_PRETO_SUAVE),
    colorway=[COR_AZUL_ESCURO, COR_VERDE_ESCURO, COR_LARANJA, COR_AZUL_PETROLEO,
              "#7E57C2", "#1E88E5", "#8D6E63", COR_VERMELHO],
    plot_bgcolor=COR_BRANCO, paper_bgcolor=COR_BRANCO,
    title=dict(font=dict(size=15, color=COR_AZUL_ESCURO)),
    xaxis=dict(gridcolor="#F1F3F5", linecolor=COR_CINZA_BORDA, zeroline=False, automargin=True),
    yaxis=dict(gridcolor="#F1F3F5", linecolor=COR_CINZA_BORDA, zeroline=False, automargin=True),
    hoverlabel=dict(bgcolor=COR_BRANCO, bordercolor=COR_CINZA_BORDA, font_size=12),
    legend=dict(bgcolor="rgba(255,255,255,0)"),
    separators=",.",
))
pio.templates.default = "plotly_white+energisa"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
    .stApp {{ background-color: {COR_CINZA_FUNDO}; }}

    /* Cabeçalho */
    .header-executivo {{
        background: linear-gradient(135deg, {COR_AZUL_PETROLEO} 0%, {COR_AZUL_ESCURO} 100%);
        padding: 1.3rem 2rem; margin-bottom: 1.5rem; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(2, 138, 159, 0.3);
    }}
    .header-conteudo {{ display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap; }}
    .header-logo {{
        background: {COR_BRANCO}; padding: 0.4rem; border-radius: 10px; width: 64px; height: 64px;
        display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }}
    .header-logo img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
    .header-titulo h1 {{
        color: {COR_BRANCO}; font-size: 1.6rem; font-weight: 600; margin: 0; letter-spacing: -0.3px;
        display: inline-flex; align-items: center; gap: 10px;
    }}
    .header-titulo p {{ color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.85rem; }}
    .header-data {{ margin-left: auto; text-align: right; color: rgba(255,255,255,0.9); font-size: 0.8rem; line-height: 1.5; }}

    /* Títulos de seção */
    .section-title {{
        color: {COR_AZUL_ESCURO}; border-left: 4px solid {COR_VERDE_ESCURO}; padding-left: 1rem;
        margin: 1.2rem 0 1rem 0; font-size: 1.1rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; display: flex; align-items: center; gap: 10px;
    }}

    /* Cards do fluxo (Progress Tracker) */
    .fluxo-container {{
        background: {COR_BRANCO}; border-radius: 8px; padding: 1.1rem 1rem; height: 100%; min-height: 230px;
        border: 1px solid {COR_CINZA_BORDA}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex; flex-direction: column; text-align: left; transition: all 0.3s ease; margin-bottom: 0.5rem;
    }}
    .fluxo-container:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,89,115,0.1); border-color: {COR_AZUL_PETROLEO}; }}
    .fluxo-container .etapa-cabecalho {{ display: flex; align-items: center; gap: 12px; margin-bottom: 0.6rem; }}
    .fluxo-container .etapa-icone {{
        width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .fluxo-container .etapa-titulo {{ font-size: 0.72rem; color: {COR_CINZA_TEXTO}; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
    .fluxo-container .valor-titulo {{ font-weight: 600; font-size: 0.92rem; color: {COR_PRETO_SUAVE}; }}
    .fluxo-container .valor-numero {{ font-size: 2rem; font-weight: 700; line-height: 1.15; margin: 0.2rem 0; }}
    .fluxo-container .info-texto {{ font-size: 0.8rem; color: {COR_CINZA_TEXTO}; margin: 0.3rem 0; flex-grow: 1; }}
    .fluxo-container .percentual-box {{ border-radius: 6px; padding: 0.45rem 0.6rem; font-size: 0.8rem; margin-top: 0.5rem; }}

    /* Cards por empresa */
    .company-card {{
        background: {COR_BRANCO}; border-radius: 8px; padding: 1.3rem; height: 100%;
        border: 1px solid {COR_CINZA_BORDA}; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s ease;
    }}
    .company-card:hover {{ box-shadow: 0 4px 12px rgba(0,89,115,0.1); border-color: {COR_AZUL_PETROLEO}; }}
    .company-title {{
        font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; padding-bottom: 0.5rem;
        border-bottom: 2px solid {COR_CINZA_BORDA}; display: flex; align-items: center; gap: 8px;
    }}
    .company-metric {{ text-align: center; padding: 0.5rem; }}
    .company-metric-value {{ font-size: 1.9rem; font-weight: 700; }}
    .company-metric-label {{ font-size: 0.78rem; color: {COR_CINZA_TEXTO}; margin-top: 0.3rem; font-weight: 500; }}

    /* Blocos informativos */
    .info-popup {{
        background: linear-gradient(135deg, {COR_BRANCO}, #E0F7FA); border-left: 4px solid {COR_AZUL_PETROLEO};
        padding: 1rem 1.2rem; border-radius: 8px; margin: 0.5rem 0; font-size: 0.86rem; color: {COR_PRETO_SUAVE}; line-height: 1.55;
    }}
    .info-popup strong {{ color: {COR_AZUL_ESCURO}; }}
    .indicador-box {{
        background: {COR_BRANCO}; border-radius: 8px; padding: 1.1rem 1.4rem; margin: 0.8rem 0;
        border: 1px solid {COR_CINZA_BORDA}; border-left: 4px solid {COR_AZUL_PETROLEO}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .indicador-box-emt {{ border-left-color: {COR_AZUL_PETROLEO}; }}
    .indicador-box-eto {{ border-left-color: {COR_AZUL_ESCURO}; }}
    .indicador-linha {{ display: flex; gap: 10px; align-items: flex-start; margin: 0.35rem 0; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background: {COR_BRANCO}; border-right: 1px solid {COR_CINZA_BORDA}; }}
    .sidebar-resumo div {{ display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid {COR_CINZA_BORDA}; font-size: 0.88rem; }}
    .sidebar-resumo div:last-child {{ border-bottom: none; }}
    .sidebar-resumo span {{ display: inline-flex; align-items: center; gap: 6px; color: {COR_CINZA_TEXTO}; }}

    /* Rodapé */
    .footer {{
        text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 2px solid {COR_CINZA_BORDA};
        color: {COR_CINZA_TEXTO}; font-size: 0.85rem;
    }}

    /* Widgets nativos no mesmo padrão */
    [data-testid="stMetric"] {{
        background: {COR_BRANCO}; padding: 0.9rem 1rem; border-radius: 8px;
        border: 1px solid {COR_CINZA_BORDA}; box-shadow: 0 2px 8px rgba(0,0,0,0.04); transition: all 0.3s ease;
    }}
    [data-testid="stMetric"]:hover {{ border-color: {COR_AZUL_PETROLEO}; box-shadow: 0 4px 12px rgba(0,89,115,0.1); }}
    [data-testid="stMetricValue"] {{ color: {COR_AZUL_ESCURO}; font-weight: 700; }}
    [data-testid="stMetricLabel"] p {{ color: {COR_CINZA_TEXTO}; font-weight: 600; }}
    .stButton > button, .stDownloadButton > button {{
        background: {COR_AZUL_ESCURO}; color: {COR_BRANCO}; border: none; border-radius: 6px; font-weight: 500; transition: all 0.3s ease;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: {COR_AZUL_PETROLEO}; color: {COR_BRANCO}; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,89,115,0.3);
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 0.4rem; }}
    .stTabs [data-baseweb="tab"] {{ font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ color: {COR_AZUL_ESCURO}; }}
    [data-testid="stPlotlyChart"] {{ background: {COR_BRANCO}; border: 1px solid {COR_CINZA_BORDA}; border-radius: 8px; padding: 6px; }}
    [data-testid="stExpander"] {{ background: {COR_BRANCO}; border-radius: 8px; }}
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

ORDEM_STATUS = ['Necessário Revisão', 'Pendente', 'Desenvolvido', 'Comissionado', 'Validado']

# ============================================
# META DE COMISSIONAMENTO 2026
# ============================================
META_2026 = {
    'EMT': 1489,  # Energisa Mato Grosso
    'ETO': None   # Energisa Tocantins - Não disponível
}

# ============================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================
def processar_dados(df):
    """Processa e padroniza os dados"""
    if df is None or df.empty:
        return df
    
    df.columns = df.columns.str.strip()
    
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
        'Revisões': 'Revisoes',
        'Motivo Revisão': 'Motivo_Revisao',
        'MotivoRevisao': 'Motivo_Revisao',
        'motivo_revisao': 'Motivo_Revisao'
    }
    
    for col_antiga, col_nova in mapeamento_colunas.items():
        if col_antiga in df.columns and col_nova not in df.columns:
            df.rename(columns={col_antiga: col_nova}, inplace=True)
    
    if 'Resp_Com' not in df.columns:
        if 'Modificado_por' in df.columns:
            df['Resp_Com'] = df.apply(
                lambda row: row['Modificado_por'] if row['Status'] in ['Comissionado', 'Validado'] else 'Não atribuído',
                axis=1
            )
        else:
            df['Resp_Com'] = 'Não atribuído'
    
    for col in ['Resp_Dev', 'Resp_Com', 'Resp_Audit']:
        if col in df.columns:
            df[col] = df[col].fillna('Não atribuído')
        else:
            df[col] = 'Não atribuído'
    
    # Garantir que a coluna Motivo_Revisao existe
    if 'Motivo_Revisao' not in df.columns:
        df['Motivo_Revisao'] = ''
    
    status_map = {
        'desenvolvido': 'Desenvolvido', 'desenv': 'Desenvolvido',
        'comissionado': 'Comissionado', 'comiss': 'Comissionado',
        'validado': 'Validado', 'valid': 'Validado',
        'revisão': 'Necessário Revisão', 'revisao': 'Necessário Revisão',
        'revisar': 'Necessário Revisão',
        'necessario revisão': 'Necessário Revisão',
        'necessario revisao': 'Necessário Revisão',
        'pendente': 'Pendente', 'pend': 'Pendente'
    }
    
    col_status = None
    for col in ['Status', 'Fase', 'Situação', 'Situacao']:
        if col in df.columns:
            col_status = col
            break
    
    if col_status:
        df[col_status] = df[col_status].astype(str).str.lower().str.strip()
        df['Status'] = df[col_status].map(lambda x: next(
            (v for k, v in status_map.items() if k in x), 'Pendente'))
    else:
        df['Status'] = 'Pendente'
    
    for col in ['Criado', 'Modificado']:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y %H:%M', errors='coerce')
            except:
                try:
                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                except:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
    
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
        # Tentar carregar do GitHub
        df = load_data_from_github()
        
        if df is not None:
            return processar_dados(df), "github"
        
        # Tentar carregar do local
        caminho_local = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        if os.path.exists(caminho_local):
            df = pd.read_csv(caminho_local, encoding='utf-8-sig')
            return processar_dados(df), "local"
        
        # Usar dados de exemplo
        dados_exemplo = {
            'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 101)],
            'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 100),
            'Empresa': np.random.choice(['EMT', 'ETO'], 100),
            'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa'], 100),
            'Responsável Comissionamento': np.random.choice(['Carlos Lima', 'Ana Paula', 'Roberto Alves'], 100),
            'Responsável Auditoria': np.random.choice(['Fernando Costa', 'Lucia Santos'], 100),
            'Status': np.random.choice(['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão'], 100, 
                                      p=[0.5, 0.15, 0.25, 0.1]),
            'Criado': pd.date_range(start='2025-01-01', periods=100, freq='D').strftime('%d/%m/%Y %H:%M'),
            'Motivo Revisão': np.random.choice(['E-MAIL NÃO ENVIADO', 'SEM APR NO E-MAIL', 'IMPEDITIVO NA APR', ''], 100,
                                               p=[0.1, 0.05, 0.05, 0.8])
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
# FUNÇÃO PARA LIMPAR CACHE E RECARREGAR DADOS
# ============================================
def limpar_cache_e_recarregar():
    """Limpa o cache e força o recarregamento dos dados"""
    load_data.clear()
    if 'df' in st.session_state:
        del st.session_state['df']
    if 'fonte' in st.session_state:
        del st.session_state['fonte']
    st.session_state.ultima_atualizacao = datetime.now()

# ============================================
# FUNÇÃO PARA POPUP DE INFORMAÇÕES (CORRIGIDA)
# ============================================
def mostrar_popup_calculos():
    """Mostra popup com explicação dos cálculos"""
    popup_html = """
    <div class="info-popup">
        <strong>Como as taxas são calculadas (ACUMULADO):</strong><br><br>
        <strong>ETAPA 1 - DESENVOLVIDOS:</strong> Desenvolvido + Comissionado + Validado + Necessário Revisão<br>
        <em>Total de equipamentos que já iniciaram o fluxo de desenvolvimento</em><br><br>
        <strong>ETAPA 2 - COMISSIONADOS:</strong> Comissionado + Validado + Necessário Revisão<br>
        <em>Total de equipamentos que já passaram pelo comissionamento</em><br><br>
        <strong>ETAPA 3 - VALIDADOS:</strong> Validados<br>
        <em>Total de equipamentos com processo concluído e validado</em><br><br>
        <strong>GARGALO - TOTAL DE REVISÃO:</strong> Equipamentos com motivo de revisão preenchido<br>
        <em>Total acumulado de equipamentos que passaram por revisão. Percentual calculado sobre o total de comissionados</em><br><br>
        <strong>ETAPA 1 → 2 (já comissionados):</strong> Comissionados / Desenvolvidos × 100<br>
        <em>Percentual dos desenvolvidos que avançaram para comissionamento</em><br><br>
        <strong>ETAPA 2 → 3 (já validados):</strong> Validados / Comissionados × 100<br>
        <em>Percentual dos comissionados que foram validados</em><br><br>
        <strong>GARGALO (% dos comissionados):</strong> Total de Revisão / Comissionados × 100<br>
        <em>Percentual dos comissionados que passaram por revisão</em><br><br>
        <strong>Legenda:</strong><br>
        • <span style="color:#2E7D32;">Desenvolvidos</span>: Já iniciaram o fluxo<br>
        • <span style="color:#028a9f;">Comissionados</span>: Já passaram pelo comissionamento<br>
        • <span style="color:#005973;">Validados</span>: Processo concluído<br>
        • <span style="color:#F57C00;">Total de Revisão</span>: Equipamentos que passaram por revisão com motivo registrado
    </div>
    """
    return popup_html

# ============================================
# FUNÇÃO PARA CRIAR GRÁFICO DE PIZZA MELHORADO
# ============================================
def criar_grafico_pizza_status(df_filtrado):
    """Cria gráfico de pizza com melhorias executivas"""
    
    status_counts = df_filtrado['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Quantidade']
    
    status_counts['Status'] = pd.Categorical(
        status_counts['Status'], 
        categories=ORDEM_STATUS, 
        ordered=True
    )
    status_counts = status_counts.sort_values('Status')
    
    total_registros = status_counts['Quantidade'].sum()
    
    pct_revisao = (
        status_counts[status_counts['Status'] == 'Necessário Revisão']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    pct_pendente = (
        status_counts[status_counts['Status'] == 'Pendente']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    pct_validado = (
        status_counts[status_counts['Status'] == 'Validado']['Quantidade'].sum() / total_registros * 100 
        if total_registros > 0 else 0
    )
    
    explode = [0.05 if status in ['Necessário Revisão', 'Pendente'] else 0 for status in status_counts['Status']]
    
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
        textposition='outside',
        textinfo='percent+label',
        texttemplate='%{label}<br>%{percent:.1%}',
        marker=dict(line=dict(color='white', width=2)),
        pull=explode,
        insidetextorientation='horizontal',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent:.1%}%<extra></extra>'
    )
    
    if pct_revisao > 10:
        msg_alerta = f"ATENÇÃO: {pct_revisao:.1f}% dos equipamentos necessitam de revisão"
        cor_alerta = '#F57C00'
    elif pct_revisao > 5:
        msg_alerta = f"Alerta: {pct_revisao:.1f}% em revisão - Acompanhar"
        cor_alerta = '#FFA726'
    else:
        msg_alerta = f"Gargalo controlado: {pct_revisao:.1f}% em revisão"
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
        borderpad=4
    )
    
    resumo_texto = f"{pct_validado:.1f}% concluídos  ·  {pct_pendente:.1f}% pendentes"
    
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
    
    fig_status.update_layout(
        showlegend=False,
        height=450,
        margin=dict(t=50, b=90, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_x=0.02
    )
    
    return fig_status

# ============================================
# FUNÇÕES DE CÁLCULO ACUMULADO
# ============================================
def calcular_desenvolvidos_acumulado(df):
    """Calcula o total acumulado de desenvolvidos"""
    status_incluidos = ['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_comissionados_acumulado(df):
    """Calcula o total acumulado de comissionados"""
    status_incluidos = ['Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_validados_acumulado(df):
    """Calcula o total acumulado de validados"""
    return len(df[df['Status'] == 'Validado'])

def calcular_aguardando_comissionamento(df):
    """Calcula quantos estão aguardando comissionamento (status Desenvolvido)"""
    return len(df[df['Status'] == 'Desenvolvido'])

def calcular_aguardando_validacao(df):
    """Calcula quantos estão aguardando validação (status Comissionado)"""
    return len(df[df['Status'] == 'Comissionado'])

def calcular_em_revisao(df):
    """Calcula quantos estão em revisão"""
    return len(df[df['Status'] == 'Necessário Revisão'])

def calcular_total_revisao(df):
    """Calcula o total acumulado de equipamentos que passaram por revisão (com motivo preenchido)"""
    return len(df[(df['Motivo_Revisao'].notna()) & 
                  (df['Motivo_Revisao'] != '') &
                  (df['Motivo_Revisao'] != 'N/A')])

def calcular_comissionados_2026(df):
    """Calcula quantos equipamentos foram comissionados em 2026"""
    status_comissionados = ['Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[(df['Status'].isin(status_comissionados)) & (df['Ano'] == 2026)])

def obter_data_primeiro_comissionamento(df):
    """Obtém a data do primeiro comissionamento"""
    status_comissionados = ['Comissionado', 'Validado', 'Necessário Revisão']
    df_comiss = df[df['Status'].isin(status_comissionados)]
    if df_comiss.empty or 'Criado' not in df_comiss.columns:
        return None
    data_min = df_comiss['Criado'].min()
    if pd.isna(data_min):
        return None
    return data_min

# ============================================
# FUNÇÕES DE ANÁLISE DE MOTIVOS DE REVISÃO
# ============================================
def analisar_motivos_revisao(df_filtrado):
    """Analisa os motivos de revisão registrados"""
    if 'Motivo_Revisao' not in df_filtrado.columns:
        return None
    
    df_motivos = df_filtrado[df_filtrado['Motivo_Revisao'].notna() & 
                              (df_filtrado['Motivo_Revisao'] != '') &
                              (df_filtrado['Motivo_Revisao'] != 'N/A')]
    
    if df_motivos.empty:
        return None
    
    return df_motivos

def criar_grafico_motivos_pizza(df_motivos):
    """Cria gráfico de pizza dos motivos de revisão"""
    motivos_count = df_motivos['Motivo_Revisao'].value_counts().reset_index()
    motivos_count.columns = ['Motivo', 'Quantidade']
    
    cores_motivos = {
        'E-MAIL NÃO ENVIADO': '#C62828',
        'E-MAIL FORA DO PADRÃO': '#D32F2F',
        'SEM APR NO E-MAIL': '#E53935',
        'IMPEDITIVO NA APR': '#F57C00',
        'AJUSTE NAS MEDIÇÕES ANALÓGICAS': '#6A1B9A',
        'EQUIPAMENTO ERRADO NA EVIDENCIA DO RELATÓRIO': '#1565C0',
        'CARD PREENCHIDO ERRADO': '#00838F',
        'CARD SEM RESPONSÁVEL PELO COMISSIONAMENTO': '#00695C',
        'NOME INCORRETO NO RELATÓRIO': '#2E7D32',
        'NOTA IMPEDITIVA NO EQUIPAMENTO': '#4527A0',
    }
    
    fig = px.pie(
        motivos_count,
        values='Quantidade',
        names='Motivo',
        title='Distribuição dos Motivos de Revisão',
        hole=0.4,
        color='Motivo',
        color_discrete_map=cores_motivos
    )
    
    fig.update_traces(
        textposition='outside',
        textinfo='percent+label',
        texttemplate='%{label}<br>%{percent:.1%} (%{value})',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent:.1%}%<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font=dict(size=16, color='#1f2937')
    )
    
    return fig

def criar_grafico_motivos_empresa(df_motivos):
    """Cria gráfico de motivos por empresa"""
    motivos_empresa = df_motivos.groupby(['Empresa', 'Motivo_Revisao']).size().reset_index(name='Quantidade')
    
    fig = px.bar(
        motivos_empresa,
        x='Empresa',
        y='Quantidade',
        color='Motivo_Revisao',
        title='Motivos de Revisão por Empresa',
        barmode='group',
        text='Quantidade',
        labels={'Motivo_Revisao': 'Motivo'}
    )
    
    fig.update_traces(textposition='outside', texttemplate='%{text}')
    fig.update_layout(
        height=400,
        xaxis_title="Empresa",
        yaxis_title="Quantidade",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def criar_tabela_motivos_detalhada(df_motivos):
    """Mostra tabela detalhada dos equipamentos com motivo de revisão"""
    motivos_agrupados = df_motivos.groupby('Motivo_Revisao').agg(
        Quantidade=('Codigo', 'count'),
        Equipamentos=('Codigo', lambda x: ', '.join(x.head(5))),
        Empresas=('Empresa', lambda x: ', '.join(x.unique()))
    ).reset_index()
    
    motivos_agrupados['Percentual'] = (motivos_agrupados['Quantidade'] / len(df_motivos) * 100).round(1)
    motivos_agrupados['Percentual'] = motivos_agrupados['Percentual'].astype(str) + '%'
    motivos_agrupados = motivos_agrupados.sort_values('Quantidade', ascending=False)
    
    return motivos_agrupados

def mostrar_resumo_motivos(df_motivos):
    """Mostra cards de resumo dos motivos"""
    categorias = {
        'E-MAIL': ['E-MAIL NÃO ENVIADO', 'E-MAIL FORA DO PADRÃO', 'SEM APR NO E-MAIL'],
        'APR': ['IMPEDITIVO NA APR'],
        'MEDIÇÕES': ['AJUSTE NAS MEDIÇÕES ANALÓGICAS'],
        'DOCUMENTAÇÃO': ['NOME INCORRETO NO RELATÓRIO', 'CARD PREENCHIDO ERRADO', 
                           'CARD SEM RESPONSÁVEL PELO COMISSIONAMENTO', 
                           'EQUIPAMENTO ERRADO NA EVIDENCIA DO RELATÓRIO'],
        'EQUIPAMENTO': ['NOTA IMPEDITIVA NO EQUIPAMENTO']
    }
    
    contagem_categorias = {}
    for cat, motivos in categorias.items():
        count = len(df_motivos[df_motivos['Motivo_Revisao'].isin(motivos)])
        contagem_categorias[cat] = count
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(":material/mail: E-mail", contagem_categorias.get('E-MAIL', 0))
    with col2:
        st.metric(":material/assignment_late: APR", contagem_categorias.get('APR', 0))
    with col3:
        st.metric(":material/description: Documentação", contagem_categorias.get('DOCUMENTAÇÃO', 0))
    with col4:
        st.metric(":material/straighten: Medições", contagem_categorias.get('MEDIÇÕES', 0))
    with col5:
        st.metric(":material/build: Equipamento", contagem_categorias.get('EQUIPAMENTO', 0))

def mostrar_analise_motivos(df_filtrado):
    """Interface completa de análise de motivos de revisão"""
    titulo_secao("Análise de Motivos de Revisão", "revisao")
    
    df_motivos = analisar_motivos_revisao(df_filtrado)
    
    if df_motivos is None:
        st.info("Nenhum motivo de revisão registrado nos dados filtrados.", icon=":material/info:")
        return
    
    # Resumo em cards
    st.markdown("##### :material/category: Resumo por Categoria")
    mostrar_resumo_motivos(df_motivos)
    
    st.markdown("---")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(":material/rate_review: Total de Revisão", fmt_milhar(len(df_motivos)))
    with col2:
        motivos_unicos = df_motivos['Motivo_Revisao'].nunique()
        st.metric(":material/list: Motivos Diferentes", motivos_unicos)
    with col3:
        empresas_afetadas = df_motivos['Empresa'].nunique()
        st.metric(":material/apartment: Empresas Afetadas", empresas_afetadas)
    with col4:
        motivo_top = df_motivos['Motivo_Revisao'].value_counts().index[0] if len(df_motivos) > 0 else "N/A"
        st.metric(":material/target: Motivo Mais Frequente", motivo_top[:30] + "..." if len(str(motivo_top)) > 30 else str(motivo_top),
                  help=str(motivo_top))
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pizza = criar_grafico_motivos_pizza(df_motivos)
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        if 'Tipo' in df_motivos.columns:
            motivos_tipo = df_motivos.groupby(['Tipo', 'Motivo_Revisao']).size().reset_index(name='Quantidade')
            
            fig_tipo = px.bar(
                motivos_tipo,
                x='Tipo',
                y='Quantidade',
                color='Motivo_Revisao',
                title='Motivos por Tipo de Equipamento',
                barmode='stack',
                text='Quantidade',
                labels={'Motivo_Revisao': 'Motivo', 'Tipo': 'Tipo de Equipamento'}
            )
            fig_tipo.update_layout(
                height=500,
                xaxis_title="Tipo de Equipamento",
                yaxis_title="Quantidade",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_tipo, use_container_width=True)
        else:
            fig_empresa = criar_grafico_motivos_empresa(df_motivos)
            st.plotly_chart(fig_empresa, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela detalhada
    st.markdown("##### :material/table_chart: Detalhamento dos Motivos")
    
    df_tabela = criar_tabela_motivos_detalhada(df_motivos)
    
    st.dataframe(
        df_tabela,
        column_config={
            "Motivo_Revisao": "Motivo",
            "Quantidade": st.column_config.NumberColumn("Qtd", format="%d"),
            "Percentual": "Percentual",
            "Equipamentos": st.column_config.TextColumn("Equipamentos (amostra)", width="large"),
            "Empresas": "Empresas"
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Filtro por motivo específico
    st.markdown("##### :material/search: Filtrar por Motivo Específico")
    
    motivo_selecionado = st.selectbox(
        "Selecione o motivo para ver os equipamentos:",
        options=['Todos'] + sorted(df_motivos['Motivo_Revisao'].unique().tolist()),
        key="filtro_motivo_especifico"
    )
    
    if motivo_selecionado != 'Todos':
        df_filtrado_motivo = df_motivos[df_motivos['Motivo_Revisao'] == motivo_selecionado]
    else:
        df_filtrado_motivo = df_motivos
    
    colunas_exibir = ['Codigo', 'Empresa', 'Tipo', 'Status', 'Motivo_Revisao', 'Resp_Com', 'Resp_Audit']
    colunas_disponiveis = [c for c in colunas_exibir if c in df_filtrado_motivo.columns]
    
    if colunas_disponiveis:
        df_display = df_filtrado_motivo[colunas_disponiveis].rename(columns={'Motivo_Revisao': 'Motivo Revisão'})
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Botão para exportar análise
    csv = df_filtrado_motivo.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Exportar Análise de Motivos (CSV)",
        icon=":material/download:",
        data=csv,
        file_name=f'analise_motivos_revisao_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

# ============================================
# FUNÇÃO PARA MOSTRAR INDICADORES DE COMISSIONAMENTO
# ============================================
def mostrar_indicadores_comissionamento(df_filtrado, empresa_selecionada):
    """Mostra os indicadores de comissionamento por empresa"""
    
    if empresa_selecionada == "Todas":
        # Mostrar para cada empresa individualmente
        for empresa in ['EMT', 'ETO']:
            df_emp = df_filtrado[df_filtrado['Empresa'] == empresa]
            if not df_emp.empty:
                _mostrar_indicador_empresa(df_emp, empresa)
            else:
                st.info(f"Sem dados disponíveis para {empresa}", icon=":material/info:")
    else:
        df_emp = df_filtrado[df_filtrado['Empresa'] == empresa_selecionada]
        if not df_emp.empty:
            _mostrar_indicador_empresa(df_emp, empresa_selecionada)
        else:
            st.info(f"Sem dados disponíveis para {empresa_selecionada}", icon=":material/info:")

def _mostrar_indicador_empresa(df_emp, empresa):
    """Mostra o indicador para uma empresa específica"""
    
    # Data do primeiro comissionamento
    data_primeiro = obter_data_primeiro_comissionamento(df_emp)
    
    # Total comissionados em 2026
    comissionados_2026 = calcular_comissionados_2026(df_emp)
    
    # Meta 2026
    meta = META_2026.get(empresa)
    
    # Nome da empresa por extenso
    nome_empresa = "Energisa Mato Grosso" if empresa == "EMT" else "Energisa Tocantins"
    
    # Classe CSS específica
    classe_css = "indicador-box-emt" if empresa == "EMT" else "indicador-box-eto"
    
    cor_emp = CORES.get(empresa, COR_AZUL_PETROLEO)

    def linha(nome_icone, cor, texto):
        return (f'<div class="indicador-linha">{icone(nome_icone, 18, cor)}'
                f'<div>{texto}</div></div>')

    linhas = []
    if data_primeiro is not None:
        data_formatada = formatar_data_portugues(data_primeiro)
        linhas.append(linha('calendario', cor_emp,
                            f"Os comissionamentos realizados pela unidade <strong>{empresa} ({nome_empresa})</strong> "
                            f"tiveram início em <strong>{data_formatada}</strong>."))
    else:
        linhas.append(linha('calendario', cor_emp,
                            f"Ainda não há registros de comissionamentos para a unidade <strong>{empresa} ({nome_empresa})</strong>."))

    if meta is not None:
        # EMT tem meta definida
        percentual_meta = (comissionados_2026 / meta * 100) if meta > 0 else 0
        linhas.append(linha('alvo', COR_AZUL_ESCURO,
                            f"<strong>Previsão de equipamentos</strong> a serem comissionados durante o ano de 2026: "
                            f"<strong>{fmt_milhar(meta)} Religadores/Reguladores</strong>."))
        linhas.append(linha('check', COR_VERDE_ESCURO,
                            f"<strong>Já foram comissionados {fmt_milhar(comissionados_2026)} equipamentos</strong> "
                            f"(Religadores/Reguladores) em 2026, representando <strong>{num_br(percentual_meta)}%</strong> "
                            f"da meta prevista para o ano."))
        barra = (f'<div style="margin-top:0.7rem;"><div style="display:flex; justify-content:space-between; font-size:0.78rem; '
                 f'color:{COR_CINZA_TEXTO};"><span>Progresso da meta 2026</span><strong style="color:{COR_AZUL_ESCURO};">'
                 f'{num_br(percentual_meta)}%</strong></div><div style="background:{COR_CINZA_BORDA}; height:8px; '
                 f'border-radius:4px; margin-top:4px;"><div style="width:{min(percentual_meta, 100):.1f}%; height:8px; '
                 f'border-radius:4px; background:linear-gradient(90deg, {COR_AZUL_PETROLEO}, {COR_AZUL_ESCURO});"></div></div></div>')
    else:
        # ETO não tem meta
        linhas.append(linha('alerta', COR_LARANJA,
                            "<strong>Previsão de equipamentos</strong> a serem comissionados em 2026: <strong>Não disponível</strong>."))
        linhas.append(linha('check', COR_VERDE_ESCURO,
                            f"<strong>Já foram comissionados {fmt_milhar(comissionados_2026)} equipamentos</strong> em 2026."))
        barra = ""

    st.markdown(
        f'<div class="indicador-box {classe_css}"><div style="font-size:0.92rem; line-height:1.55; color:{COR_PRETO_SUAVE};">'
        + "".join(linhas) + barra + '</div></div>', unsafe_allow_html=True)

# ============================================
# INTERFACE PRINCIPAL
# ============================================

# Carregar dados
if 'df' not in st.session_state:
    with st.spinner("Carregando dados..."):
        df, fonte = load_data()
        st.session_state.df = df
        st.session_state.fonte = fonte
        st.session_state.ultima_atualizacao = datetime.now()
else:
    df = st.session_state.df
    fonte = st.session_state.fonte

if df is None or df.empty:
    st.error("Não foi possível carregar os dados.", icon=":material/error:")
    st.stop()

# HEADER EXECUTIVO COM LOGO
logo_base64, mime_type = get_logo_base64()

if logo_base64:
    header_logo_html = f'<img src="data:{mime_type};base64,{logo_base64}" alt="Logo Energisa">'
else:
    header_logo_html = icone('raio', 34, COR_AZUL_ESCURO, 2.2)

st.markdown(f"""
<div class="header-executivo">
    <div class="header-conteudo">
        <div class="header-logo">{header_logo_html}</div>
        <div class="header-titulo">
            <h1>{icone('atividade', 26, COR_BRANCO, 2.4)} Monitoring Center</h1>
            <p>Radar de Comissionamento SCADA das unidades · EMT | ETO</p>
        </div>
        <div class="header-data">
            <strong>Dashboard Executivo</strong><br>
            Fábrica SCADA · v5.1<br>
            <span style="opacity:0.8;">{agora().strftime('%d/%m/%Y')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR COM FILTROS
# ============================================

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:0.6rem 0 0.4rem 0;">
        <h3 style="color:{COR_AZUL_ESCURO}; margin:0; display:inline-flex; align-items:center; gap:8px;">
            {icone('ajustes', 22, COR_AZUL_ESCURO)} Painel de Controle</h3>
        <p style="color:{COR_CINZA_TEXTO}; margin:0.2rem 0 0 0; font-size:0.85rem;">Selecione os critérios para análise</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**:material/filter_alt: Filtros de Análise**")

        anos_disponiveis = sorted(df['Ano'].dropna().unique()) if 'Ano' in df.columns else []
        anos_opcoes = ["Todos os Anos"] + [int(ano) for ano in anos_disponiveis]
        ano_selecionado = st.selectbox(":material/calendar_month: Ano", options=anos_opcoes, index=0, key="filtro_ano")

        meses_nomes = ["Todos os Meses", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_selecionado = st.selectbox(":material/date_range: Mês", options=meses_nomes, index=0, key="filtro_mes")

        empresas_opcoes = ["Todas"] + sorted(df['Empresa'].dropna().unique().tolist())
        empresa_selecionada = st.selectbox(":material/apartment: Empresa", options=empresas_opcoes, index=0,
                                           key="filtro_empresa")

        if 'Tipo' in df.columns:
            tipos_opcoes = ["Todos"] + sorted(df['Tipo'].dropna().unique().tolist())
            tipo_selecionado = st.selectbox(":material/category: Tipo Equipamento", options=tipos_opcoes, index=0,
                                            key="filtro_tipo")
        else:
            tipo_selecionado = "Todos"

        status_opcoes = ["Todos"] + sorted(df['Status'].unique().tolist())
        status_selecionado = st.selectbox(":material/flag: Status", options=status_opcoes, index=0, key="filtro_status")

    with st.container(border=True):
        st.markdown("**:material/sync: Controles de Atualização**")
        if st.button("Atualizar dados", icon=":material/refresh:", use_container_width=True,
                     help="Força a leitura da base de dados do GitHub"):
            with st.spinner("Atualizando dados do GitHub..."):
                limpar_cache_e_recarregar()
                st.rerun()
        if st.button("Limpar filtros", icon=":material/filter_alt_off:", use_container_width=True,
                     help="Limpar todos os filtros"):
            limpar_filtros()
            st.rerun()

        # Informação da fonte dos dados
        if fonte == "github":
            st.success("Dados carregados do GitHub", icon=":material/cloud_done:")
        elif fonte == "local":
            st.info("Dados carregados localmente", icon=":material/folder:")
        elif fonte == "exemplo":
            st.warning("Usando dados de exemplo", icon=":material/warning:")

        if 'ultima_atualizacao' in st.session_state:
            st.caption(f"Última atualização: {st.session_state.ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}")

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
# ADICIONAR BOTÕES DO PDF COM FILTRO DE MÊS
# ============================================
with st.sidebar:
    with st.container(border=True):
        st.markdown("**:material/picture_as_pdf: Exportar Relatório**")

        anos_disponiveis = sorted(df['Ano'].dropna().unique()) if 'Ano' in df.columns else []
        anos_opcoes_rel = ["Todos os Anos"] + [int(ano) for ano in anos_disponiveis]
        ano_relatorio = st.selectbox(":material/calendar_month: Ano do relatório", options=anos_opcoes_rel, index=0,
                                     key="filtro_ano_relatorio")

        meses_opcoes_rel = ["Todos os Meses", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_relatorio = st.selectbox(":material/date_range: Mês do relatório", options=meses_opcoes_rel, index=0,
                                     key="filtro_mes_relatorio")

        # Botão para gerar relatório EMT
        adicionar_botao_pdf_empresa(df_filtrado, "EMT", mes_relatorio, ano_relatorio)

        # Botão para gerar relatório ETO
        adicionar_botao_pdf_empresa(df_filtrado, "ETO", mes_relatorio, ano_relatorio)

# ============================================
# ESTATÍSTICAS RÁPIDAS NA SIDEBAR
# ============================================

with st.sidebar:
    total_filtrado = len(df_filtrado)
    em_andamento = len(df_filtrado[df_filtrado['Status'].isin(['Desenvolvido', 'Comissionado'])])
    finalizados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])

    with st.container(border=True):
        st.markdown("**:material/dashboard: Visão Rápida**")
        st.markdown(f"""
        <div class="sidebar-resumo">
            <div><span>{icone('pacote', 15, COR_AZUL_ESCURO)} Total</span><strong>{fmt_milhar(total_filtrado)}</strong></div>
            <div><span>{icone('engrenagem', 15, COR_AZUL_PETROLEO)} Em andamento</span><strong>{fmt_milhar(em_andamento)}</strong></div>
            <div><span>{icone('check', 15, COR_VERDE_ESCURO)} Finalizados</span><strong>{fmt_milhar(finalizados)}</strong></div>
            <div><span>{icone('revisao', 15, COR_LARANJA)} Em revisão</span><strong>{fmt_milhar(revisao)}</strong></div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# PAINEL PRINCIPAL
# ============================================

if not df_filtrado.empty:
    # Cálculos acumulados
    qtd_desenvolvidos_acum = calcular_desenvolvidos_acumulado(df_filtrado)
    qtd_comissionados_acum = calcular_comissionados_acumulado(df_filtrado)
    qtd_validados_acum = calcular_validados_acumulado(df_filtrado)
    qtd_aguardando_comiss = calcular_aguardando_comissionamento(df_filtrado)
    qtd_aguardando_valid = calcular_aguardando_validacao(df_filtrado)
    qtd_revisao = calcular_em_revisao(df_filtrado)
    
    # Total de revisão acumulado (todos que passaram por revisão com motivo)
    qtd_total_revisao = calcular_total_revisao(df_filtrado)
    
    # Taxas
    taxa_desenv_para_comiss = (qtd_comissionados_acum / qtd_desenvolvidos_acum * 100) if qtd_desenvolvidos_acum > 0 else 0
    taxa_comiss_para_valid = (qtd_validados_acum / qtd_comissionados_acum * 100) if qtd_comissionados_acum > 0 else 0
    # Percentual do total de revisão sobre comissionados
    taxa_revisao_sobre_comiss = (qtd_total_revisao / qtd_comissionados_acum * 100) if qtd_comissionados_acum > 0 else 0
    
    # VISUALIZAÇÃO DO FLUXO
    titulo_secao("Progress Tracker (Acumulado)", "atividade")

    with st.expander("Detalhes dos cálculos", expanded=False, icon=":material/info:"):
        st.markdown(mostrar_popup_calculos(), unsafe_allow_html=True)

    def card_fluxo(etapa, titulo, valor, cor, nome_icone, info, rodape, fundo_rodape):
        return f"""
        <div class="fluxo-container" style="border-left: 4px solid {cor};">
            <div class="etapa-cabecalho">
                <div class="etapa-icone" style="background: {cor}14;">{icone(nome_icone, 24, cor)}</div>
                <div><div class="etapa-titulo">{etapa}</div><div class="valor-titulo">{titulo}</div></div>
            </div>
            <div class="valor-numero" style="color: {cor};">{fmt_milhar(valor)}</div>
            <div class="info-texto">{info}</div>
            <div class="percentual-box" style="background: {fundo_rodape};">{rodape}</div>
        </div>
        """

    col1, col2, col3, col4 = st.columns(4)

    # ETAPA 1: DESENVOLVIDOS
    with col1:
        if empresa_selecionada == "EMT":
            # EMT tem meta definida de 1489
            meta_emt = META_2026.get('EMT', 1489)
            percentual_meta = (qtd_desenvolvidos_acum / meta_emt * 100) if meta_emt > 0 else 0
            rodape_1 = (f"<strong>Meta: {fmt_milhar(meta_emt)}</strong> · Progresso: "
                        f"<strong>{num_br(percentual_meta)}%</strong>")
            fundo_1 = "#E8F5E9"
        else:
            # ETO ou "Todas": sem quantidade total definida
            rodape_1 = "Sem definição da quantidade total"
            fundo_1 = "#FFF3E0" if empresa_selecionada == "ETO" else COR_CINZA_FUNDO
        st.markdown(card_fluxo("Etapa 1", "Desenvolvidos", qtd_desenvolvidos_acum, CORES['Desenvolvido'], 'codigo',
                               f"Aguardando comissionamento: <strong>{fmt_milhar(qtd_aguardando_comiss)}</strong>",
                               rodape_1, fundo_1), unsafe_allow_html=True)

    # ETAPA 2: COMISSIONADOS
    with col2:
        st.markdown(card_fluxo("Etapa 2", "Comissionados", qtd_comissionados_acum, CORES['Comissionado'], 'ferramenta',
                               f"Aguardando validação: <strong>{fmt_milhar(qtd_aguardando_valid)}</strong>",
                               f"<strong>{num_br(taxa_desenv_para_comiss)}%</strong> dos desenvolvidos já comissionados",
                               "#E0F7FA"), unsafe_allow_html=True)

    # ETAPA 3: VALIDADOS
    with col3:
        st.markdown(card_fluxo("Etapa 3", "Validados", qtd_validados_acum, CORES['Validado'], 'escudo',
                               "Processo concluído",
                               f"<strong>{num_br(taxa_comiss_para_valid)}%</strong> dos comissionados já validados",
                               "#E0F7FA"), unsafe_allow_html=True)

    # GARGALO - TOTAL DE REVISÃO ACUMULADO
    with col4:
        if qtd_total_revisao > 10:
            fundo_4 = "#FFF3E0"
        elif qtd_total_revisao > 5:
            fundo_4 = "#FFF8E1"
        else:
            fundo_4 = "#E8F5E9"
        st.markdown(card_fluxo("Gargalo", "Total de Revisão", qtd_total_revisao, CORES['Necessário Revisão'], 'alerta',
                               f"{fmt_milhar(qtd_total_revisao)} equipamentos passaram por revisão",
                               f"<strong>{num_br(taxa_revisao_sobre_comiss)}%</strong> dos comissionados",
                               fundo_4), unsafe_allow_html=True)

    # TABS PARA ANÁLISES DETALHADAS
    st.write("")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":material/dashboard: Visão Executiva",
        ":material/show_chart: Evolução Temporal",
        ":material/groups: Performance por Responsável",
        ":material/table_rows: Detalhamento",
        ":material/fact_check: Motivos Revisão"
    ])
    
    # ============================================
    # TAB 1: VISÃO EXECUTIVA
    # ============================================
    with tab1:
        titulo_secao("Análise Comparativa por Empresa (Acumulado)", "empresa")
        
        col1, col2 = st.columns(2)
        
        for idx, empresa in enumerate(['EMT', 'ETO']):
            with col1 if idx == 0 else col2:
                df_emp = df_filtrado[df_filtrado['Empresa'] == empresa]
                
                if not df_emp.empty:
                    desenvolvidos_emp = calcular_desenvolvidos_acumulado(df_emp)
                    comissionados_emp = calcular_comissionados_acumulado(df_emp)
                    validados_emp = calcular_validados_acumulado(df_emp)
                    
                    progresso_emp = (comissionados_emp / desenvolvidos_emp * 100) if desenvolvidos_emp > 0 else 0
                    
                    st.markdown(f"""
                    <div class="company-card">
                        <div class="company-title" style="color: {CORES[empresa]};">{icone('empresa', 20, CORES[empresa])} {empresa}</div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Desenvolvido']};">{fmt_milhar(desenvolvidos_emp)}</div>
                                <div class="company-metric-label">Desenvolvidos</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Comissionado']};">{fmt_milhar(comissionados_emp)}</div>
                                <div class="company-metric-label">Comissionados</div>
                            </div>
                            <div class="company-metric">
                                <div class="company-metric-value" style="color: {CORES['Validado']};">{fmt_milhar(validados_emp)}</div>
                                <div class="company-metric-label">Validados</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem;">
                            <div style="background: {COR_CINZA_FUNDO}; border-radius: 6px; padding: 0.6rem 0.8rem;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Progresso do fluxo:</span>
                                    <strong style="color: {COR_AZUL_ESCURO};">{num_br(progresso_emp)}%</strong>
                                </div>
                                <div style="width: 100%; background: {COR_CINZA_BORDA}; height: 8px; border-radius: 4px; margin-top: 0.5rem;">
                                    <div style="width: {min(progresso_emp, 100):.1f}%; background: linear-gradient(90deg, {COR_AZUL_PETROLEO}, {COR_AZUL_ESCURO}); height: 8px; border-radius: 4px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        titulo_secao("Distribuição do Portfólio", "grafico")
        
        col1, col2 = st.columns(2)
        
        with col1:
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
                    coloraxis_showscale=False,
                    xaxis_title="Quantidade",
                    yaxis_title="",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title_font=dict(size=14, color='#1f2937')
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
        
        # ============================================
        # NOVA SEÇÃO: INDICADORES DE COMISSIONAMENTO
        # ============================================
        titulo_secao("Indicadores de Comissionamento por Unidade", "calendario")
        
        mostrar_indicadores_comissionamento(df_filtrado, empresa_selecionada)
    
    # ============================================
    # TAB 2: EVOLUÇÃO TEMPORAL
    # ============================================
    with tab2:
        titulo_secao("Evolução do Fluxo (Acumulado)", "atividade")
        
        if 'Criado' in df_filtrado.columns:
            df_filtrado['Ano_Mes'] = df_filtrado['Criado'].dt.strftime('%Y-%m')
            df_filtrado['Mes_Ano_Label'] = df_filtrado['Criado'].dt.strftime('%b/%Y')
            
            meses_ordenados = sorted(df_filtrado['Ano_Mes'].unique())
            
            evolucao_acum = []
            for mes in meses_ordenados:
                df_ate_mes = df_filtrado[df_filtrado['Ano_Mes'] <= mes]
                label_mes = df_filtrado[df_filtrado['Ano_Mes'] == mes]['Mes_Ano_Label'].iloc[0]
                
                desenvolvidos = calcular_desenvolvidos_acumulado(df_ate_mes)
                comissionados = calcular_comissionados_acumulado(df_ate_mes)
                validados = calcular_validados_acumulado(df_ate_mes)
                
                evolucao_acum.append({
                    'Ano_Mes': mes,
                    'Mes_Ano_Label': label_mes,
                    'Desenvolvidos': desenvolvidos,
                    'Comissionados': comissionados,
                    'Validados': validados
                })
            
            df_evolucao = pd.DataFrame(evolucao_acum)
            
            fig_evolucao = go.Figure()
            
            fig_evolucao.add_trace(go.Scatter(
                x=df_evolucao['Mes_Ano_Label'],
                y=df_evolucao['Desenvolvidos'],
                name='Desenvolvidos',
                line=dict(color=CORES['Desenvolvido'], width=3),
                mode='lines+markers',
                marker=dict(size=8)
            ))
            
            fig_evolucao.add_trace(go.Scatter(
                x=df_evolucao['Mes_Ano_Label'],
                y=df_evolucao['Comissionados'],
                name='Comissionados',
                line=dict(color=CORES['Comissionado'], width=3),
                mode='lines+markers',
                marker=dict(size=8)
            ))
            
            fig_evolucao.add_trace(go.Scatter(
                x=df_evolucao['Mes_Ano_Label'],
                y=df_evolucao['Validados'],
                name='Validados',
                line=dict(color=CORES['Validado'], width=3),
                mode='lines+markers',
                marker=dict(size=8)
            ))
            
            fig_evolucao.update_layout(
                title='Evolução Acumulada do Fluxo',
                height=400,
                xaxis_title="Mês",
                yaxis_title="Quantidade Acumulada",
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
            # Evolução mensal (não acumulada)
            evolucao_mensal = df_filtrado.groupby(['Ano_Mes', 'Mes_Ano_Label', 'Status']).size().reset_index(name='Quantidade')
            evolucao_mensal = evolucao_mensal.sort_values('Ano_Mes')
            
            fig_barras = px.bar(
                evolucao_mensal,
                x='Mes_Ano_Label',
                y='Quantidade',
                color='Status',
                title='Distribuição Mensal por Status (Não Acumulado)',
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
    
    # ============================================
    # TAB 3: PERFORMANCE POR RESPONSÁVEL
    # ============================================
    with tab3:
        titulo_secao("Performance por Responsável", "equipe")
        
        tipo_resp = st.radio(
            ":material/person_search: Selecionar tipo:",
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
            st.warning(f"Coluna '{col_resp}' não encontrada nos dados.", icon=":material/warning:")
        else:
            df_resp = df_filtrado[df_filtrado[col_resp] != 'Não atribuído']
            
            if df_resp.empty:
                st.info(f"Nenhum responsável de {tipo_resp} encontrado.", icon=":material/info:")
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
                        coloraxis_showscale=False,
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
                            coloraxis_showscale=False,
                            xaxis_title="Taxa de Sucesso (%)",
                            xaxis_range=[0, 100],
                            yaxis_title="",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_sucesso, use_container_width=True)
                
                st.markdown(f"##### :material/stacked_bar_chart: Distribuição de Status por {tipo_resp}")
                
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
                        text='Quantidade',
                        labels={col_resp: 'Responsável'}
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
    
    # ============================================
    # TAB 4: DETALHAMENTO
    # ============================================
    with tab4:
        titulo_secao("Detalhamento dos Registros", "lista")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(":material/inventory_2: Total de Registros", fmt_milhar(len(df_filtrado)))
        with col2:
            st.metric(":material/apartment: Empresas", len(df_filtrado['Empresa'].unique()))
        with col3:
            if 'Tipo' in df_filtrado.columns:
                st.metric(":material/category: Tipos de Equipamento", len(df_filtrado['Tipo'].unique()))
            else:
                st.metric(":material/category: Tipos de Equipamento", 0)
        with col4:
            st.metric(":material/engineering: Responsáveis Desenvolvimento", len(df_filtrado['Resp_Dev'].unique()))
        
        # Mostrar tabela com Motivo Revisão
        colunas_mostrar = ['Codigo', 'Tipo', 'Empresa', 'Status', 'Motivo_Revisao', 
                           'Resp_Dev', 'Resp_Com', 'Resp_Audit']
        colunas_existentes = [c for c in colunas_mostrar if c in df_filtrado.columns]
        
        if colunas_existentes:
            df_display = df_filtrado[colunas_existentes].copy()
            df_display = df_display.rename(columns={'Motivo_Revisao': 'Motivo Revisão'})
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        with st.expander("Estatísticas Detalhadas", icon=":material/analytics:"):
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
            
            st.markdown("---")
            st.markdown("##### :material/summarize: Resumo Acumulado")
            
            resumo_acum = pd.DataFrame({
                'Métrica': [
                    'Desenvolvidos (Acumulado)',
                    'Comissionados (Acumulado)',
                    'Validados (Acumulado)',
                    'Aguardando Comissionamento',
                    'Aguardando Validação',
                    'Total de Revisão (acumulado)'
                ],
                'Quantidade': [
                    qtd_desenvolvidos_acum,
                    qtd_comissionados_acum,
                    qtd_validados_acum,
                    qtd_aguardando_comiss,
                    qtd_aguardando_valid,
                    qtd_total_revisao
                ]
            })
            st.dataframe(resumo_acum, use_container_width=True, hide_index=True)
    
    # ============================================
    # TAB 5: MOTIVOS DE REVISÃO
    # ============================================
    with tab5:
        mostrar_analise_motivos(df_filtrado)
    
    # FOOTER
    st.markdown(f"""
    <div class="footer">
        <div style="margin-bottom: 0.6rem;">
            <p style="margin: 0; color: {COR_PRETO_SUAVE}; font-weight: 500; display:inline-flex; align-items:center; gap:6px;">
                {icone('raio', 16, COR_AZUL_ESCURO)} <span style="color: {COR_AZUL_ESCURO};">Radar de Comissionamento SCADA</span> · Energisa
            </p>
        </div>
        <p style="margin: 0; font-size: 0.75rem;">
            © {agora().year} Monitoring Center | Sistema proprietário - Energisa Group
        </p>
        <p style="margin: 0.2rem 0 0 0; font-size: 0.7rem;">
            Versão 5.1 · Última atualização: {st.session_state.get('ultima_atualizacao', agora()).strftime('%d/%m/%Y %H:%M')} · {fmt_milhar(len(df_filtrado))} registros · {fonte.upper()}
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Nenhum dado encontrado com os filtros selecionados.", icon=":material/search_off:")
    
    st.markdown(f"""
    <div class="footer">
        <div style="margin-bottom: 0.6rem;">
            <p style="margin: 0; color: {COR_PRETO_SUAVE}; font-weight: 500; display:inline-flex; align-items:center; gap:6px;">
                {icone('raio', 16, COR_AZUL_ESCURO)} <span style="color: {COR_AZUL_ESCURO};">Radar de Comissionamento SCADA</span> · Energisa
            </p>
        </div>
        <p style="margin: 0; font-size: 0.75rem;">
            © {agora().year} Monitoring Center | Sistema proprietário - Energisa Group
        </p>
        <p style="margin: 0.2rem 0 0 0; font-size: 0.7rem;">
            Versão 5.1 · Última atualização: {st.session_state.get('ultima_atualizacao', agora()).strftime('%d/%m/%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
