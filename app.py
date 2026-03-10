import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os
import io
import base64

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Comissionamento | AD Energia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para estilo corporativo
st.markdown("""
<style>
    /* Fontes e reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Cabeçalho principal */
    .main-header {
        background: linear-gradient(135deg, #0a1a3c 0%, #1e3c72 100%);
        padding: 1.8rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 20px rgba(0,20,50,0.15);
        border: 1px solid rgba(255,255,255,0.1);
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
    
    /* Tabelas estilizadas */
    .dataframe-container {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 1rem;
        overflow-x: auto;
    }
    
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    
    .styled-table th {
        background-color: #f8fafc;
        color: #1e3c72;
        font-weight: 600;
        padding: 0.75rem;
        text-align: left;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .styled-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #edf2f7;
    }
    
    .styled-table tr:hover {
        background-color: #f7fafc;
    }
    
    /* Status colors */
    .status-desenvolvido {
        background-color: #d4edda;
        color: #155724;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-pendente {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-andamento {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-block;
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
    delta_html = f"<span style='color: {'#28a745' if delta and delta > 0 else '#dc3545'}; font-size:0.9rem;'>{delta:+.1f}%</span>" if delta is not None else ''
    
    st.markdown(f"""
    <div class='metric-card'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
            <span style='font-size: 1rem; color: #4a5568; font-weight: 500;'>{icon} {title}</span>
            {delta_html}
        </div>
        <div style='font-size: 2.2rem; font-weight: 700; color: {color}; margin: 0.3rem 0 0.2rem 0; line-height: 1.2;'>
            {value}
        </div>
        {f'<div style="font-size:0.85rem; color:#718096;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

# Função para criar tabela estilizada sem matplotlib
def criar_tabela_estilizada(df, titulo=None):
    if df.empty:
        st.info("Sem dados para exibir")
        return
    
    html = "<div class='dataframe-container'>"
    if titulo:
        html += f"<h4 style='margin-top:0; color:#1e3c72;'>{titulo}</h4>"
    
    html += "<table class='styled-table'><thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    for _, row in df.iterrows():
        html += "<tr>"
        for col in df.columns:
            valor = row[col]
            # Aplicar formatação especial para status
            if col == 'Status' or 'status' in str(col).lower():
                if valor == 'Desenvolvido':
                    html += f"<td><span class='status-desenvolvido'>{valor}</span></td>"
                elif valor == 'Pendente':
                    html += f"<td><span class='status-pendente'>{valor}</span></td>"
                elif valor == 'Em andamento':
                    html += f"<td><span class='status-andamento'>{valor}</span></td>"
                else:
                    html += f"<td>{valor}</td>"
            else:
                html += f"<td>{valor}</td>"
        html += "</tr>"
    
    html += "</tbody></table></div>"
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
            'xanchor': 'center',
            'y': 0.95
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
        },
        showlegend=True,
        legend={
            'bgcolor': 'rgba(255,255,255,0.9)',
            'bordercolor': '#e2e8f0',
            'borderwidth': 1,
            'font': {'size': 11},
            'yanchor': 'top',
            'y': 0.99,
            'xanchor': 'right',
            'x': 0.99
        }
    )
    
    # Configurar eixos
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f2f6',
        linecolor='#e2e8f0',
        tickfont={'size': 11}
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f2f6',
        linecolor='#e2e8f0',
        tickfont={'size': 11}
    )
    
    return fig

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        # Caminho do arquivo
        caminho_arquivo = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho_arquivo):
            st.warning(f"Arquivo não encontrado: {caminho_arquivo}")
            # Criar dados de exemplo para demonstração
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
            # Ler o arquivo real
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
    # HEADER PRINCIPAL COM LOGO
    col_logo, col_title, col_date = st.columns([1, 3, 1])
    
    with col_logo:
        # Para colocar a logo da empresa, descomente a linha abaixo e coloque o caminho da imagem
        # st.image("logo_empresa.png", width=120)
        
        # Enquanto não tem a logo, mostra um placeholder
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    width: 60px; height: 60px; border-radius: 12px; 
                    display: flex; align-items: center; justify-content: center;
                    font-size: 30px; color: white;'>
            ⚡
        </div>
        """, unsafe_allow_html=True)
    
    with col_title:
        st.markdown("""
        <div class='main-header'>
            <h1 style='margin:0; font-size:2.2rem; font-weight:600; letter-spacing:-0.02em;'>
                📊 Dashboard de Comissionamento
            </h1>
            <p style='margin:0.5rem 0 0 0; opacity:0.9; font-size:1rem;'>
                Acompanhamento de Desenvolvimentos e Comissionamentos • AD Energia
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_date:
        st.markdown(f"""
        <div style='text-align:right; padding:1rem; background: white; border-radius: 12px;
                    border: 1px solid #e2e8f0;'>
            <p style='color:#4a5568; margin:0; font-size:0.9rem; font-weight:500;'>
                {datetime.now().strftime('%d/%m/%Y')}
            </p>
            <p style='color:#1e3c72; font-weight:600; margin:0.2rem 0 0 0; font-size:1rem;'>
                ⏱️ {datetime.now().strftime('%H:%M')}
            </p>
            <p style='color:#718096; font-size:0.75rem; margin:0.2rem 0 0 0;'>
                dados em tempo real
            </p>
        </div>
        """, unsafe_allow_html=True)

    # SIDEBAR MELHORADA
    with st.sidebar:
        st.markdown("""
        <div class='sidebar-header'>
            <h3 style='margin:0; font-size:1.4rem; font-weight:600;'>🔍 Painel de Controle</h3>
            <p style='margin:0.3rem 0 0 0; opacity:0.9; font-size:0.9rem;'>Filtros e Configurações</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Filtros Principais")
        
        # Organizar filtros em expansores
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
        
        # Filtro de data
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
        
        # Indicadores rápidos
        if not df.empty:
            st.markdown("### 📊 Progresso Geral")
            
            # Aplicar filtros básicos para o progresso
            df_progresso = df[
                (df['Empresa'].isin(empresas)) &
                (df['Tipo Equipamento'].isin(tipos_equip)) &
                (df['Status'].isin(status_opcoes))
            ]
            
            total_filtrado = len(df_progresso)
            desenvolvidos = len(df_progresso[df_progresso['Status'] == 'Desenvolvido'])
            progresso = (desenvolvidos/total_filtrado*100) if total_filtrado > 0 else 0
            
            st.progress(progresso/100, text=f"Progresso: **{progresso:.1f}%**")
            
            # Mini estatísticas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total registros", total_filtrado)
            with col2:
                st.metric("Desenvolvidos", desenvolvidos)
        
        # Botões de ação
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
        
        # Calcular percentuais
        percent_desenv = (qtd_desenvolvidos/total_equip*100) if total_equip > 0 else 0
        percent_andamento = (qtd_andamento/total_equip*100) if total_equip > 0 else 0
        percent_pend = (qtd_pendentes/total_equip*100) if total_equip > 0 else 0
        
        # Layout de métricas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            metric_card("Total", format_number(total_equip), "ativos", "📦", "#1e3c72")
        
        with col2:
            percent_emt = (qtd_emt/total_equip*100) if total_equip > 0 else 0
            metric_card("EMT", format_number(qtd_emt), f"{percent_emt:.1f}% do total", "⚡", "#2a5298")
        
        with col3:
            percent_eto = (qtd_eto/total_equip*100) if total_equip > 0 else 0
            metric_card("ETO", format_number(qtd_eto), f"{percent_eto:.1f}% do total", "🔧", "#4a7ab0")
        
        with col4:
            metric_card("Desenvolvidos", format_number(qtd_desenvolvidos), f"{percent_desenv:.1f}%", "✅", "#28a745")
        
        with col5:
            metric_card("Em andamento", format_number(qtd_andamento), f"{percent_andamento:.1f}%", "🔄", "#ffc107")
        
        with col6:
            metric_card("Pendentes", format_number(qtd_pendentes), f"{percent_pend:.1f}%", "⏳", "#dc3545")

        # TABS PARA ORGANIZAR O CONTEÚDO
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Visão Geral", 
            "📈 Análise de Desempenho", 
            "👥 Alocação de Recursos",
            "📋 Dados Completos"
        ])

        with tab1:
            # GRÁFICOS PRINCIPAIS
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - Status
                status_counts = df_filtrado['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Quantidade']
                
                # Ordem personalizada
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
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Gráfico de barras - Tipo de Equipamento
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
                fig_tipo.update_traces(
                    hovertemplate='<b>%{y}</b><br>Quantidade: %{x}<extra></extra>'
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            # Gráfico de evolução temporal
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
            # ANÁLISE DE DESEMPENHO
            col1, col2 = st.columns(2)
            
            with col1:
                # Matriz Empresa vs Status
                cross_tab = pd.crosstab(
                    df_filtrado['Empresa'], 
                    df_filtrado['Status'],
                    margins=True,
                    margins_name='Total'
                )
                
                st.markdown("### 📊 Matriz Empresa vs Status")
                criar_tabela_estilizada(cross_tab)
            
            with col2:
                # Matriz Tipo vs Status
                cross_tab_tipo = pd.crosstab(
                    df_filtrado['Tipo Equipamento'], 
                    df_filtrado['Status'],
                    margins=True,
                    margins_name='Total'
                )
                
                st.markdown("### 📊 Matriz Tipo de Equipamento vs Status")
                criar_tabela_estilizada(cross_tab_tipo)
            
            # Indicadores de performance
            st.markdown("### 🎯 Indicadores de Performance")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Taxa de conclusão por empresa
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
                
                fig_taxas = configurar_grafico_corporativo(fig_taxas, "Taxa de Conclusão por Empresa", 300)
                st.plotly_chart(fig_taxas, use_container_width=True)
            
            with col2:
                # Top 5 tipos com maior desenvolvimento
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
                    fig_top = configurar_grafico_corporativo(fig_top, "Top 5 Tipos Mais Desenvolvidos", 300)
                    st.plotly_chart(fig_top, use_container_width=True)
                else:
                    st.info("Sem dados para exibir")
            
            with col3:
                # Tipos com mais pendências
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
                    fig_pend = configurar_grafico_corporativo(fig_pend, "Top 5 Tipos com Mais Pendências", 300)
                    st.plotly_chart(fig_pend, use_container_width=True)
                else:
                    st.info("Sem dados para exibir")

        with tab3:
            # ALOCAÇÃO DE RECURSOS
            st.markdown("### 👥 Desempenho por Responsável")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Responsáveis por desenvolvimento
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
                    fig_resp = configurar_grafico_corporativo(fig_resp, "Top 10 Responsáveis - Desenvolvimento", 400)
                    st.plotly_chart(fig_resp, use_container_width=True)
                else:
                    st.info("Nenhum responsável atribuído")
            
            with col2:
                # Responsáveis por auditoria
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
                        fig_audit = configurar_grafico_corporativo(fig_audit, "Top 10 Responsáveis - Auditoria", 400)
                        st.plotly_chart(fig_audit, use_container_width=True)
                    else:
                        st.info("Nenhum responsável de auditoria atribuído")
            
            # Gráfico de carga de trabalho
            st.markdown("### 📊 Carga de Trabalho por Responsável")
            
            # Criar DataFrame com contagem por status para cada responsável
            if 'Responsável Desenvolvimento' in df_filtrado.columns:
                carga_trabalho = pd.crosstab(
                    df_filtrado['Responsável Desenvolvimento'],
                    df_filtrado['Status']
                ).reset_index()
                
                if not carga_trabalho.empty and 'Responsável Desenvolvimento' in carga_trabalho.columns:
                    # Derreter para formato longo para o plotly
                    carga_long = carga_trabalho.melt(
                        id_vars=['Responsável Desenvolvimento'],
                        var_name='Status',
                        value_name='Quantidade'
                    )
                    carga_long = carga_long[carga_long['Responsável Desenvolvimento'] != 'Não atribuído']
                    
                    if not carga_long.empty:
                        fig_carga = px.bar(
                            carga_long,
                            x='Responsável Desenvolvimento',
                            y='Quantidade',
                            color='Status',
                            title='Distribuição de Status por Responsável',
                            barmode='stack',
                            color_discrete_map=cores_status
                        )
                        fig_carga = configurar_grafico_corporativo(fig_carga, "Distribuição de Status por Responsável", 450)
                        fig_carga.update_xaxis(tickangle=45)
                        st.plotly_chart(fig_carga, use_container_width=True)

        with tab4:
            # DADOS COMPLETOS
            st.markdown("### 📋 Detalhamento dos Registros")
            
            # Controles da tabela
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                colunas_padrao = ['Cód. Equipamento', 'Chamado Desenvolvimento', 'Tipo Equipamento', 
                                 'Responsável Desenvolvimento', 'Status', 'Empresa', 'Criado']
                colunas_disponiveis = [col for col in colunas_padrao if col in df_filtrado.columns]
                colunas_adicionais = [col for col in df_filtrado.columns if col not in colunas_padrao]
                
                mostrar_colunas = st.multiselect(
                    "📌 Colunas para exibir",
                    options=df_filtrado.columns.tolist(),
                    default=colunas_disponiveis if colunas_disponiveis else df_filtrado.columns[:5].tolist(),
                    key="colunas_table"
                )
            
            with col2:
                search = st.text_input("🔍 Buscar (código ou chamado)", placeholder="Digite para filtrar...")
            
            with col3:
                rows_per_page = st.selectbox("Linhas por página", [10, 25, 50, 100], index=1)
            
            # Aplicar busca
            df_display = df_filtrado.copy()
            if search:
                mask = pd.Series(False, index=df_display.index)
                if 'Cód. Equipamento' in df_display.columns:
                    mask |= df_display['Cód. Equipamento'].astype(str).str.contains(search, case=False, na=False)
                if 'Chamado Desenvolvimento' in df_display.columns:
                    mask |= df_display['Chamado Desenvolvimento'].astype(str).str.contains(search, case=False, na=False)
                df_display = df_display[mask]
            
            # Mostrar estatísticas da busca
            st.caption(f"📊 Mostrando {len(df_display)} de {len(df_filtrado)} registros")
            
            # Exibir tabela com formatação condicional
            if mostrar_colunas:
                # Criar uma cópia para exibição
                df_show = df_display[mostrar_colunas].copy()
                
                # Formatar datas se existirem
                for col in df_show.columns:
                    if 'data' in col.lower() or col in ['Criado', 'Modificado']:
                        if pd.api.types.is_datetime64_any_dtype(df_show[col]):
                            df_show[col] = df_show[col].dt.strftime('%d/%m/%Y %H:%M')
                
                # Exibir com st.dataframe (sem formatação condicional para evitar erro)
                st.dataframe(
                    df_show,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, 100 + len(df_display) * 35)
                )

        # EXPORTAÇÃO DE DADOS
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.markdown("### 📥 Exportar Dados")
        
        with col2:
            # Escolher formato
            formato_export = st.selectbox("Formato", ["CSV", "Excel", "JSON"], key="formato_export")
        
        with col3:
            # Nome do arquivo
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
                # Criar buffer para Excel
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
            
            else:  # JSON
                json_str = df_filtrado.to_json(orient='records', date_format='iso', indent=2, force_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"{nome_arquivo}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            # Botão para copiar para área de transferência
            if st.button("📋 Copiar resumo", use_container_width=True):
                resumo = f"""Resumo do Dashboard - {datetime.now().strftime('%d/%m/%Y %H:%M')}
                
Total de Registros: {format_number(total_equip)}
EMT: {format_number(qtd_emt)}
ETO: {format_number(qtd_eto)}
Desenvolvidos: {format_number(qtd_desenvolvidos)} ({percent_desenv:.1f}%)
Em andamento: {format_number(qtd_andamento)} ({percent_andamento:.1f}%)
Pendentes: {format_number(qtd_pendentes)} ({percent_pend:.1f}%)"""
                st.code(resumo, language="text")
                st.success("✅ Resumo gerado! Copie o texto acima.")
        
        with col3:
            # Opção de relatório executivo
            if st.button("📄 Gerar Relatório Executivo", use_container_width=True):
                st.info("📊 Relatório executivo gerado com sucesso! (funcionalidade em desenvolvimento)")

        # RODAPÉ CORPORATIVO
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div style='color:#4a5568; font-size:0.85rem;'>
                <strong style='color:#1e3c72;'>© 2024 AD Energia</strong><br>
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
                dashboard@adenergia.com<br>
                Ramal: 1234
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")

else:
    st.error("❌ Não foi possível carregar os dados. Verifique o arquivo de origem.")
