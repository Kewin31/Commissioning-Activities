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
# FUNÇÃO PARA HORÁRIOS EM TEMPO REAL
# ============================================
def get_horarios_regioes():
    """Retorna os horários atualizados das regiões onde a Energisa atua"""
    from datetime import datetime, timezone, timedelta
    
    # Horário atual em UTC
    utc_now = datetime.now(timezone.utc)
    
    # Definição das regiões com seus fusos horários
    regioes = {
        'Brasília, Brasil': {'offset': -3, 'descricao': ''},
        'Cuiabá, Brasil': {'offset': -4, 'descricao': 'Menos 1 h'},
        'Porto Velho, Brasil': {'offset': -4, 'descricao': 'Menos 1 h'},
        'Acre, Brasil': {'offset': -5, 'descricao': 'Menos 2 h'}
    }
    
    horarios = []
    for regiao, info in regioes.items():
        # Calcular horário local
        local_time = utc_now + timedelta(hours=info['offset'])
        
        # Formatar data em português
        dia_semana = local_time.strftime('%A').lower()
        dias_semana_pt = {
            'monday': 'segunda-feira', 'tuesday': 'terça-feira', 'wednesday': 'quarta-feira',
            'thursday': 'quinta-feira', 'friday': 'sexta-feira', 'saturday': 'sábado', 'sunday': 'domingo'
        }
        
        dia_semana_pt = dias_semana_pt.get(dia_semana, dia_semana)
        data_formatada = local_time.strftime(f'{dia_semana_pt}, %d/%m/%Y')
        hora_formatada = local_time.strftime('%H:%M')
        
        horarios.append({
            'regiao': regiao,
            'hora': hora_formatada,
            'descricao': info['descricao'],
            'data': data_formatada
        })
    
    return horarios

def criar_componente_horarios():
    """Cria o componente visual com os horários das regiões"""
    horarios = get_horarios_regioes()
    
    html = f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        margin-bottom: 1rem;
        margin-top: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.2rem;">🕐</span>
            <span style="font-weight: 600; color: #005973;">Horários em Tempo Real</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 1.5rem;">
    """
    
    for horario in horarios:
        # Só adiciona a descrição se ela não estiver vazia
        if horario['descricao']:
            descricao_html = f"{horario['descricao']}<br>"
        else:
            descricao_html = ""
        
        html += f"""
        <div style="text-align: center; min-width: 100px;">
            <div style="font-weight: 600; color: #1f2937; font-size: 0.85rem;">{horario['regiao']}</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #028a9f;">{horario['hora']}</div>
            <div style="font-size: 0.65rem; color: #6b7280; line-height: 1.3;">
                {descricao_html}{horario['data']}
            </div>
        </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html

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
        margin-top: 2rem;
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
        borderpad=4
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
    
