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
    """Obtém configurações do GitHub do Streamlit Secrets"""
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        file_path = st.secrets.get("GITHUB_FILE_PATH", "data/Dados/Comissionamento AD - UNs.csv")
        return token, repo, file_path
    except Exception as e:
        st.error(f"❌ Erro ao carregar configurações do GitHub: {str(e)}")
        return None, None, None

def atualizar_dados_github(arquivo_upload):
    """Atualiza o arquivo no GitHub com o novo arquivo enviado"""
    try:
        token, repo_name, file_path = get_github_config()
        
        if not token or not repo_name:
            st.error("Configurações do GitHub não encontradas. Configure o Streamlit Secrets.")
            return False
        
        # Conectar ao GitHub
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Ler o conteúdo do arquivo enviado
        file_content = arquivo_upload.read()
        
        # Verificar se o arquivo já existe no repositório
        try:
            contents = repo.get_contents(file_path)
            # Atualizar arquivo existente
            repo.update_file(
                path=file_path,
                message=f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                content=file_content,
                sha=contents.sha
            )
            st.success("✅ Arquivo atualizado com sucesso no GitHub!")
        except GithubException as e:
            if e.status == 404:
                # Criar novo arquivo
                repo.create_file(
                    path=file_path,
                    message=f"Criação inicial - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    content=file_content
                )
                st.success("✅ Arquivo criado com sucesso no GitHub!")
            else:
                raise e
        
        # Limpar cache para carregar novos dados
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao atualizar GitHub: {str(e)}")
        return False

def get_logo_base64():
    """Converte a logo para base64 para exibição"""
    # Lista de possíveis nomes de arquivo (priorizando PNG)
    possiveis_nomes = [
        "Logo_Energisa.png",  # Prioritário
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
                # Detectar tipo da imagem pela extensão
                if logo_path.lower().endswith('.png'):
                    mime_type = "image/png"
                elif logo_path.lower().endswith('.gif'):
                    mime_type = "image/gif"
                else:
                    mime_type = "image/png"  # padrão
                
                return base64.b64encode(logo_bytes).decode(), mime_type
        except:
            continue
    
    return None, None

# CSS personalizado para estilo corporativo
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
    
    /* Botão de atualização especial */
    .update-button > button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    }
    .update-button > button:hover {
        background: linear-gradient(135deg, #218838 0%, #1e7e34 100%);
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

# Função para formatar números
def format_number(val):
    if pd.isna(val):
        return "0"
    if isinstance(val, (int, float)):
        return f"{val:,.0f}".replace(",", ".")
    return str(val)

# Função para configurar gráficos com tema corporativo
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

# Função para carregar os dados
@st.cache_data(ttl=3600)  # Cache expira após 1 hora
def load_data():
    try:
        # Tenta carregar do GitHub primeiro
        token, repo_name, file_path = get_github_config()
        
        if token and repo_name:
            try:
                g = Github(token)
                repo = g.get_repo(repo_name)
                contents = repo.get_contents(file_path)
                
                # Decodificar conteúdo
                import base64
                file_content = base64.b64decode(contents.content).decode('utf-8')
                
                # Salvar temporariamente para ler com pandas
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    f.write(file_content)
                    temp_file = f.name
                
                df = pd.read_csv(temp_file, encoding='utf-8-sig')
                os.unlink(temp_file)  # Limpar arquivo temporário
                
                st.success("✅ Dados carregados do GitHub!")
                
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar do GitHub: {str(e)}. Tentando arquivo local...")
                # Fallback para arquivo local
                caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
                
                if not os.path.exists(caminho_arquivo):
                    # Criar dados de exemplo
                    dados_exemplo = {
                        'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 51)],
                        'Chamado Desenvolvimento': [f'CHAMADO-{i}' for i in range(1001, 1051)],
                        'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 50),
                        'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Souza', 'Não atribuído'], 50),
                        'Responsável Auditoria': np.random.choice(['Roberto Lima', 'Carla Mendes', 'Paulo Ferreira', 'Não atribuído'], 50),
                        'Status': np.random.choice(['Desenvolvido', 'Em andamento', 'Pendente'], 50, p=[0.4, 0.35, 0.25]),
                        'Empresa': np.random.choice(['EMT', 'ETO'], 50),
                        'Criado': pd.date_range(start='2024-01-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M'),
                        'Modificado': pd.date_range(start='2024-02-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M')
                    }
                    df = pd.DataFrame(dados_exemplo)
                else:
                    df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
        else:
            # Carregar do arquivo local
            caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
            
            if not os.path.exists(caminho_arquivo):
                # Criar dados de exemplo
                dados_exemplo = {
                    'Cód. Equipamento': [f'EQ{str(i).zfill(4)}' for i in range(1, 51)],
                    'Chamado Desenvolvimento': [f'CHAMADO-{i}' for i in range(1001, 1051)],
                    'Tipo Equipamento': np.random.choice(['Inversor', 'Transformador', 'Painel', 'Cabo', 'Disjuntor'], 50),
                    'Responsável Desenvolvimento': np.random.choice(['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Souza', 'Não atribuído'], 50),
                    'Responsável Auditoria': np.random.choice(['Roberto Lima', 'Carla Mendes', 'Paulo Ferreira', 'Não atribuído'], 50),
                    'Status': np.random.choice(['Desenvolvido', 'Em andamento', 'Pendente'], 50, p=[0.4, 0.35, 0.25]),
                    'Empresa': np.random.choice(['EMT', 'ETO'], 50),
                    'Criado': pd.date_range(start='2024-01-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M'),
                    'Modificado': pd.date_range(start='2024-02-01', periods=50, freq='D').strftime('%d/%m/%Y %H:%M')
                }
                df = pd.DataFrame(dados_exemplo)
            else:
                df = pd.read_csv(caminho_arquivo, encoding='utf-8-sig')
        
        # Tratar campos vazios
        df['Responsável Desenvolvimento'] = df['Responsável Desenvolvimento'].fillna('Não atribuído')
        df['Responsável Auditoria'] = df['Responsável Auditoria'].fillna('Não atribuído')
        df['Status'] = df['Status'].fillna('Pendente')
        
        # Converter datas
        if 'Criado' in df.columns:
            df['Criado'] = pd.to_datetime(df['Criado'], format='%d/%m/%Y %H:%M', errors='coerce')
        if 'Modificado' in df.columns:
            df['Modificado'] = pd.to_datetime(df['Modificado'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Carregar dados
df = load_data()

if df is not None:
    # CABEÇALHO UNIFICADO - VERSÃO PNG
    logo_base64, mime_type = get_logo_base64()
    
    col_esquerda, col_direita = st.columns([4, 1.2])
    
    with col_esquerda:
        if logo_base64:
            st.markdown(f"""
            <style>
            .header-unificado {{
                background: linear-gradient(135deg, #0a1a3c 0%, #1e3c72 100%);
                border-radius: 16px;
                padding: 1rem 2rem;
                box-shadow: 0 8px 20px rgba(0,20,50,0.15);
                border: 1px solid rgba(255,255,255,0.1);
                display: flex;
                align-items: center;
                gap: 1.5rem;
                height: 100%;
                min-height: 90px;
            }}
            .header-logo {{
                width: 70px;
                height: 70px;
                object-fit: contain;
                background: white;
                border-radius: 10px;
                padding: 5px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }}
            .header-texto {{
                flex: 1;
            }}
            .header-texto h1 {{
                margin: 0;
                font-size: 2rem;
                font-weight: 600;
                color: white;
                letter-spacing: -0.02em;
                line-height: 1.2;
            }}
            .header-texto p {{
                margin: 0.2rem 0 0 0;
                color: rgba(255,255,255,0.9);
                font-size: 0.95rem;
            }}
            </style>
            
            <div class="header-unificado">
                <img src="data:{mime_type};base64,{logo_base64}" class="header-logo" alt="Logo Energisa">
                <div class="header-texto">
                    <h1>Acompanhamento de Comissionamentos/Desenvolvimentos</h1>
                    <p>EMT | ETO • Fábrica SCADA - Energisa</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #0a1a3c 0%, #1e3c72 100%);
                        border-radius: 16px; padding: 1rem 2rem; display: flex; align-items: center; gap: 1.5rem;">
                <div style="background: white; width:70px; height:70px; border-radius:10px; display: flex; align-items: center; justify-content: center; font-size:35px;">
                    ⚡
                </div>
                <div>
                    <h1 style="margin:0; color:white; font-size:2rem;">📊 Dashboard de Comissionamento</h1>
                    <p style="margin:0.2rem 0 0 0; color:rgba(255,255,255,0.9);">Acompanhamento de Desenvolvimentos e Comissionamentos • AD Energisa</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_direita:
        st.markdown(f"""
        <style>
        .header-data {{
            background: white;
            border-radius: 16px;
            padding: 1rem 1.2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            text-align: center;
            height: 100%;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .header-data .data {{
            color: #1e3c72;
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
        }}
        .header-data .hora {{
            color: #4a5568;
            font-size: 1rem;
            font-weight: 500;
            margin: 0.2rem 0 0 0;
        }}
        .header-data .label {{
            color: #718096;
            font-size: 0.7rem;
            margin: 0.2rem 0 0 0;
        }}
        </style>
        
        <div class="header-data">
            <div class="data">{datetime.now().strftime('%d/%m/%Y')}</div>
            <div class="hora">⏱️ {datetime.now().strftime('%H:%M')}</div>
            <div class="label">dados em tempo real</div>
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
        
        st.markdown("### 📋 Filtros Principais")
        
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
                "Status do desenvolvimento",
                options=sorted(df['Status'].unique()),
                default=sorted(df['Status'].unique()),
                key="status_filter"
            )
        
        with st.expander("👥 Responsáveis"):
            responsaveis_dev = st.multiselect(
                "Responsáveis pelo desenvolvimento",
                options=sorted(df['Responsável Desenvolvimento'].unique()),
                default=[],
                key="resp_filter"
            )
            
            if 'Responsável Auditoria' in df.columns:
                responsaveis_audit = st.multiselect(
                    "Responsáveis pela auditoria",
                    options=sorted(df['Responsável Auditoria'].unique()),
                    default=[],
                    key="audit_filter"
                )
        
        with st.expander("📅 Período"):
            if 'Criado' in df.columns and not df['Criado'].isna().all():
                data_min = df['Criado'].min().date()
                data_max = df['Criado'].max().date()
                
                data_inicio = st.date_input("Data inicial", data_min)
                data_fim = st.date_input("Data final", data_max)
            else:
                st.info("Dados de data não disponíveis")
                data_inicio = None
                data_fim = None
        
        st.markdown("---")
        
        # ============================================
        # SEÇÃO DE ATUALIZAÇÃO DO GITHUB
        # ============================================
        st.markdown("### 🔄 Atualização de Dados")
        
        with st.expander("📤 Upload para GitHub", expanded=True):
            st.markdown("""
            <p style='font-size:0.85rem; color:#718096; margin-bottom:10px;'>
                Envie um novo arquivo CSV para atualizar a base de dados no GitHub.
            </p>
            """, unsafe_allow_html=True)
            
            arquivo_upload = st.file_uploader(
                "Selecionar arquivo CSV",
                type=['csv'],
                key="github_upload"
            )
            
            if arquivo_upload is not None:
                st.info(f"📁 Arquivo selecionado: {arquivo_upload.name}")
                st.info(f"📊 Tamanho: {round(arquivo_upload.size/1024, 2)} KB")
                
                # Botão de atualização com estilo especial
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown('<div class="update-button">', unsafe_allow_html=True)
                    if st.button("🔄 Atualizar GitHub", use_container_width=True):
                        with st.spinner("Enviando para o GitHub..."):
                            if atualizar_dados_github(arquivo_upload):
                                st.success("✅ Dados atualizados! Recarregando...")
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.rerun()
        
        st.markdown("---")
        
        # Indicadores rápidos
        if not df.empty:
            st.markdown("### 📊 Progresso Geral")
            
            df_progresso = df[
                (df['Empresa'].isin(empresas)) &
                (df['Tipo Equipamento'].isin(tipos_equip)) &
                (df['Status'].isin(status_opcoes))
            ]
            
            total_filtrado = len(df_progresso)
            desenvolvidos = len(df_progresso[df_progresso['Status'] == 'Desenvolvido'])
            progresso = (desenvolvidos/total_filtrado*100) if total_filtrado > 0 else 0
            
            st.progress(progresso/100, text=f"Progresso: **{progresso:.1f}%**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total registros", total_filtrado)
            with col2:
                st.metric("Desenvolvidos", desenvolvidos)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Limpar filtros", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("📥 Exportar", use_container_width=True):
                st.session_state['exportar'] = True

    # Aplicar filtros
    df_filtrado = df[
        (df['Empresa'].isin(empresas)) &
        (df['Tipo Equipamento'].isin(tipos_equip)) &
        (df['Status'].isin(status_opcoes))
    ]
    
    if responsaveis_dev:
        df_filtrado = df_filtrado[df_filtrado['Responsável Desenvolvimento'].isin(responsaveis_dev)]
    
    if 'responsaveis_audit' in locals() and responsaveis_audit:
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
        qtd_desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
        qtd_andamento = len(df_filtrado[df_filtrado['Status'] == 'Em andamento'])
        qtd_pendentes = len(df_filtrado[df_filtrado['Status'] == 'Pendente'])
        
        percent_desenv = (qtd_desenvolvidos/total_equip*100) if total_equip > 0 else 0
        percent_andamento = (qtd_andamento/total_equip*100) if total_equip > 0 else 0
        percent_pend = (qtd_pendentes/total_equip*100) if total_equip > 0 else 0
        percent_emt = (qtd_emt/total_equip*100) if total_equip > 0 else 0
        percent_eto = (qtd_eto/total_equip*100) if total_equip > 0 else 0
        
        # CSS adicional para os cards
        st.markdown("""
        <style>
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
        
        # Criar linhas de cards
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #1e3c72;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">📦 Total</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #1e3c72; line-height: 1.2; margin-bottom: 0.25rem;">
                    {total_equip}
                </div>
                <div style="font-size:0.8rem; color:#718096;">ativos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #2a5298;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">⚡ EMT</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #2a5298; line-height: 1.2; margin-bottom: 0.25rem;">
                    {qtd_emt}
                </div>
                <div style="font-size:0.8rem; color:#718096;">{percent_emt:.1f}% do total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #4a7ab0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">🔧 ETO</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #4a7ab0; line-height: 1.2; margin-bottom: 0.25rem;">
                    {qtd_eto}
                </div>
                <div style="font-size:0.8rem; color:#718096;">{percent_eto:.1f}% do total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #28a745;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">✅ Desenvolvidos</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #28a745; line-height: 1.2; margin-bottom: 0.25rem;">
                    {qtd_desenvolvidos}
                </div>
                <div style="font-size:0.8rem; color:#718096;">{percent_desenv:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #ffc107;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">🔄 Em andamento</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #ffc107; line-height: 1.2; margin-bottom: 0.25rem;">
                    {qtd_andamento}
                </div>
                <div style="font-size:0.8rem; color:#718096;">{percent_andamento:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="metric-card-simple" style="border-left: 4px solid #dc3545;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.95rem; color: #4a5568; font-weight: 500;">⏳ Pendentes</span>
                </div>
                <div style="font-size: 2rem; font-weight: 700; color: #dc3545; line-height: 1.2; margin-bottom: 0.25rem;">
                    {qtd_pendentes}
                </div>
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
                status_counts = df_filtrado['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Quantidade']
                
                ordem_status = ['Desenvolvido', 'Em andamento', 'Pendente']
                status_counts['Status'] = pd.Categorical(status_counts['Status'], categories=ordem_status, ordered=True)
                status_counts = status_counts.sort_values('Status')
                
                cores_status = {
                    'Desenvolvido': '#28a745',
                    'Em andamento': '#ffc107',
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
                    textinfo='percent+label'
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
                    title='Distribuição por Tipo de Equipamento',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    orientation='h'
                )
                
                fig_tipo = configurar_grafico_corporativo(fig_tipo, "Distribuição por Tipo de Equipamento", 400)
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            if 'Criado' in df_filtrado.columns and not df_filtrado['Criado'].isna().all():
                st.markdown("### 📅 Evolução Temporal")
                
                df_temp = df_filtrado.copy()
                df_temp['Mês'] = df_temp['Criado'].dt.to_period('M').astype(str)
                evolucao = df_temp.groupby(['Mês', 'Status']).size().reset_index(name='Quantidade')
                
                fig_evolucao = px.line(
                    evolucao, 
                    x='Mês', 
                    y='Quantidade', 
                    color='Status',
                    title='Evolução de Registros por Mês',
                    color_discrete_map=cores_status
                )
                
                fig_evolucao = configurar_grafico_corporativo(fig_evolucao, "Evolução de Registros por Mês", 450)
                st.plotly_chart(fig_evolucao, use_container_width=True)

        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                cross_tab = pd.crosstab(
                    df_filtrado['Empresa'], 
                    df_filtrado['Status'],
                    margins=True,
                    margins_name='Total'
                )
                
                st.markdown("### 📊 Matriz Empresa vs Status")
                st.dataframe(cross_tab, use_container_width=True)
            
            with col2:
                cross_tab_tipo = pd.crosstab(
                    df_filtrado['Tipo Equipamento'], 
                    df_filtrado['Status'],
                    margins=True,
                    margins_name='Total'
                )
                
                st.markdown("### 📊 Matriz Tipo de Equipamento vs Status")
                st.dataframe(cross_tab_tipo, use_container_width=True)
            
            st.markdown("### 🎯 Indicadores de Performance")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                taxa_emt = (len(df_filtrado[(df_filtrado['Empresa'] == 'EMT') & (df_filtrado['Status'] == 'Desenvolvido')]) / 
                           max(len(df_filtrado[df_filtrado['Empresa'] == 'EMT']), 1)) * 100
                
                taxa_eto = (len(df_filtrado[(df_filtrado['Empresa'] == 'ETO') & (df_filtrado['Status'] == 'Desenvolvido')]) / 
                           max(len(df_filtrado[df_filtrado['Empresa'] == 'ETO']), 1)) * 100
                
                fig_taxas = go.Figure()
                fig_taxas.add_trace(go.Bar(
                    name='EMT',
                    x=['Taxa de Conclusão'],
                    y=[taxa_emt],
                    marker_color='#2a5298',
                    text=[f'{taxa_emt:.1f}%'],
                    textposition='outside'
                ))
                fig_taxas.add_trace(go.Bar(
                    name='ETO',
                    x=['Taxa de Conclusão'],
                    y=[taxa_eto],
                    marker_color='#4a7ab0',
                    text=[f'{taxa_eto:.1f}%'],
                    textposition='outside'
                ))
                
                fig_taxas.update_layout(
                    title='Taxa de Conclusão por Empresa',
                    barmode='group',
                    showlegend=True,
                    height=300,
                    yaxis_title='Percentual (%)',
                    yaxis_range=[0, 100]
                )
                st.plotly_chart(fig_taxas, use_container_width=True)
            
            with col2:
                top_tipos = df_filtrado[df_filtrado['Status'] == 'Desenvolvido']['Tipo Equipamento'].value_counts().head(5)
                
                if not top_tipos.empty:
                    fig_top = px.bar(
                        x=top_tipos.values,
                        y=top_tipos.index,
                        orientation='h',
                        title='Top 5 Tipos Mais Desenvolvidos',
                        color=top_tipos.values,
                        color_continuous_scale='Greens'
                    )
                    fig_top.update_layout(height=300)
                    st.plotly_chart(fig_top, use_container_width=True)
            
            with col3:
                top_pendentes = df_filtrado[df_filtrado['Status'] == 'Pendente']['Tipo Equipamento'].value_counts().head(5)
                
                if not top_pendentes.empty:
                    fig_pend = px.bar(
                        x=top_pendentes.values,
                        y=top_pendentes.index,
                        orientation='h',
                        title='Top 5 Tipos com Mais Pendências',
                        color=top_pendentes.values,
                        color_continuous_scale='Reds'
                    )
                    fig_pend.update_layout(height=300)
                    st.plotly_chart(fig_pend, use_container_width=True)

        with tab3:
            st.markdown("### 👥 Desempenho por Responsável")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Responsável Desenvolvimento' in df_filtrado.columns:
                    resp_counts = df_filtrado['Responsável Desenvolvimento'].value_counts().reset_index()
                    resp_counts.columns = ['Responsável', 'Quantidade']
                    resp_counts = resp_counts[resp_counts['Responsável'] != 'Não atribuído']
                    
                    if not resp_counts.empty:
                        fig_resp = px.bar(
                            resp_counts.head(10), 
                            x='Quantidade', 
                            y='Responsável',
                            title='Top 10 Responsáveis - Desenvolvimento',
                            orientation='h',
                            color='Quantidade',
                            color_continuous_scale='Viridis'
                        )
                        fig_resp.update_layout(
                            title={'text': 'Top 10 Responsáveis - Desenvolvimento', 'x': 0.5},
                            xaxis_title="Quantidade",
                            yaxis_title="",
                            height=400
                        )
                        st.plotly_chart(fig_resp, use_container_width=True)
                    else:
                        st.info("Nenhum responsável atribuído")
            
            with col2:
                if 'Responsável Auditoria' in df_filtrado.columns:
                    audit_counts = df_filtrado['Responsável Auditoria'].value_counts().reset_index()
                    audit_counts.columns = ['Responsável', 'Quantidade']
                    audit_counts = audit_counts[audit_counts['Responsável'] != 'Não atribuído']
                    
                    if not audit_counts.empty:
                        fig_audit = px.bar(
                            audit_counts.head(10), 
                            x='Quantidade', 
                            y='Responsável',
                            title='Top 10 Responsáveis - Auditoria',
                            orientation='h',
                            color='Quantidade',
                            color_continuous_scale='Plasma'
                        )
                        fig_audit.update_layout(
                            title={'text': 'Top 10 Responsáveis - Auditoria', 'x': 0.5},
                            xaxis_title="Quantidade",
                            yaxis_title="",
                            height=400
                        )
                        st.plotly_chart(fig_audit, use_container_width=True)
                    else:
                        st.info("Nenhum responsável de auditoria atribuído")
            
            st.markdown("### 📊 Carga de Trabalho por Responsável")
            
            if 'Responsável Desenvolvimento' in df_filtrado.columns:
                df_carga = df_filtrado[df_filtrado['Responsável Desenvolvimento'] != 'Não atribuído'].copy()
                
                if not df_carga.empty:
                    dados_agrupados = df_carga.groupby(['Responsável Desenvolvimento', 'Status']).size().reset_index(name='Quantidade')
                    
                    if not dados_agrupados.empty:
                        cores_status = {
                            'Desenvolvido': '#28a745',
                            'Em andamento': '#ffc107',
                            'Pendente': '#dc3545'
                        }
                        
                        fig_carga = px.bar(
                            dados_agrupados,
                            x='Responsável Desenvolvimento',
                            y='Quantidade',
                            color='Status',
                            title='Distribuição de Status por Responsável',
                            barmode='stack',
                            color_discrete_map=cores_status,
                            text='Quantidade'
                        )
                        
                        fig_carga.update_layout(
                            title={'text': 'Distribuição de Status por Responsável', 'x': 0.5},
                            xaxis=dict(
                                title="Responsável",
                                tickangle=45,
                                tickfont=dict(size=10)
                            ),
                            yaxis=dict(
                                title="Quantidade",
                                tickfont=dict(size=10)
                            ),
                            height=450,
                            margin=dict(l=0, r=0, t=50, b=100),
                            bargap=0.2,
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        fig_carga.update_traces(
                            textposition='inside',
                            textfont=dict(color='white', size=10)
                        )
                        
                        st.plotly_chart(fig_carga, use_container_width=True)
                    else:
                        st.info("Sem dados agrupados para exibir")
                else:
                    st.info("Não há responsáveis atribuídos para análise de carga")

        with tab4:
            st.markdown("### 📋 Detalhamento dos Registros")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                colunas_padrao = ['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                                 'Responsável Desenvolvimento', 'Status', 'Empresa', 'Criado']
                colunas_disponiveis = [col for col in colunas_padrao if col in df_filtrado.columns]
                
                mostrar_colunas = st.multiselect(
                    "📌 Colunas para exibir",
                    options=df_filtrado.columns.tolist(),
                    default=colunas_disponiveis if colunas_disponiveis else df_filtrado.columns[:5].tolist(),
                    key="colunas_table"
                )
            
            with col2:
                search = st.text_input("🔍 Buscar", placeholder="Código ou chamado...")
            
            with col3:
                rows_per_page = st.selectbox("Linhas", [10, 25, 50, 100], index=1)
            
            df_display = df_filtrado.copy()
            if search:
                mask = pd.Series(False, index=df_display.index)
                if 'Cód. Equipamento' in df_display.columns:
                    mask |= df_display['Cód. Equipamento'].astype(str).str.contains(search, case=False, na=False)
                if 'Chamado Desenvolvimento' in df_display.columns:
                    mask |= df_display['Chamado Desenvolvimento'].astype(str).str.contains(search, case=False, na=False)
                df_display = df_display[mask]
            
            st.caption(f"📊 Mostrando {len(df_display)} de {len(df_filtrado)} registros")
            
            if mostrar_colunas:
                df_show = df_display[mostrar_colunas].copy()
                
                for col in df_show.columns:
                    if 'data' in col.lower() or col in ['Criado', 'Modificado']:
                        if pd.api.types.is_datetime64_any_dtype(df_show[col]):
                            df_show[col] = df_show[col].dt.strftime('%d/%m/%Y %H:%M')
                
                st.dataframe(
                    df_show,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, 100 + len(df_display) * 35)
                )

        # EXPORTAÇÃO
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.markdown("### 📥 Exportar Dados")
        
        with col2:
            formato_export = st.selectbox("Formato", ["CSV", "Excel", "JSON"], key="formato_export")
        
        with col3:
            nome_arquivo = f"comissionamento_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if formato_export == "CSV":
                csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{nome_arquivo}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            elif formato_export == "Excel":
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Dados')
                
                st.download_button(
                    label="📥 Download Excel",
                    data=output.getvalue(),
                    file_name=f"{nome_arquivo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            else:
                json_str = df_filtrado.to_json(orient='records', date_format='iso', indent=2, force_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"{nome_arquivo}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📋 Copiar resumo", use_container_width=True):
                resumo = f"""Resumo do Dashboard - {datetime.now().strftime('%d/%m/%Y %H:%M')}
                
Total de Registros: {format_number(total_equip)}
EMT: {format_number(qtd_emt)}
ETO: {format_number(qtd_eto)}
Desenvolvidos: {format_number(qtd_desenvolvidos)} ({percent_desenv:.1f}%)
Em andamento: {format_number(qtd_andamento)} ({percent_andamento:.1f}%)
Pendentes: {format_number(qtd_pendentes)} ({percent_pend:.1f}%)"""
                st.code(resumo, language="text")
                st.success("✅ Resumo gerado!")
        
        with col3:
            if st.button("📄 Relatório Executivo", use_container_width=True):
                st.info("📊 Funcionalidade em desenvolvimento")

        # RODAPÉ
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong style='color:#1e3c72;'>© 2026 Energisa</strong><br>
                Dashboard de Comissionamento<br>
                Versão 2.0.0
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong style='color:#1e3c72;'>🕒 Última atualização</strong><br>
                {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
                Dados em tempo real
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong style='color:#1e3c72;'>📊 Estatísticas</strong><br>
                Total registros: {format_number(total_equip)}<br>
                Taxa conclusão: {percent_desenv:.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style='color:#4a5568; font-size:0.85rem; text-align:right;'>
                <strong style='color:#1e3c72;'>📞 Suporte</strong><br>
                kewin.ferreira@energisa.com.br
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")

else:
    st.error("❌ Não foi possível carregar os dados. Verifique o arquivo de origem.")
