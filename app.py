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

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Radar de Comissionamento | Fábrica SCADA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PALETA EXECUTIVA
# ============================================================
COR_PRIMARIA   = "#0F2044"   # Azul navy profundo
COR_ACCENT     = "#1A6BCC"   # Azul royal
COR_DEV        = "#0D7377"   # Teal — Desenvolvido
COR_COM        = "#1A6BCC"   # Azul — Comissionado
COR_REV        = "#E07B00"   # Âmbar — Revisão
COR_VAL        = "#16A34A"   # Verde — Validado
COR_PEN        = "#9B1C1C"   # Vermelho escuro — Pendente
COR_EMT        = "#0F2044"
COR_ETO        = "#1A6BCC"

MAPA_CORES = {
    "Desenvolvido":      COR_DEV,
    "Comissionado":      COR_COM,
    "Necessário Revisão": COR_REV,
    "Revisão":           COR_REV,
    "Validado":          COR_VAL,
    "Pendente":          COR_PEN,
    "EMT":               COR_EMT,
    "ETO":               COR_ETO,
}

STATUS_ORDEM = ["Desenvolvido", "Comissionado", "Necessário Revisão", "Validado", "Pendente"]

MESES_PT = {
    1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
    7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"
}

# ============================================================
# CSS EXECUTIVO
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #F5F7FA;
}

/* ---- HEADER ---- */
.exec-header {
    background: linear-gradient(135deg, #0F2044 0%, #1A3A6B 60%, #1A6BCC 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    box-shadow: 0 8px 32px rgba(15,32,68,0.18);
}
.exec-header-text h1 {
    font-family: 'Syne', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: white;
    margin: 0;
    letter-spacing: -0.03em;
}
.exec-header-text p {
    color: rgba(255,255,255,0.7);
    font-size: 0.88rem;
    margin: 0.3rem 0 0 0;
    font-weight: 400;
}
.exec-badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 0.3rem 0.8rem;
    color: rgba(255,255,255,0.85);
    font-size: 0.78rem;
    font-weight: 500;
    display: inline-block;
    margin-top: 0.5rem;
}

/* ---- PIPELINE BANNER ---- */
.pipeline-wrap {
    display: flex;
    align-items: stretch;
    gap: 0;
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(15,32,68,0.07);
    margin-bottom: 2rem;
}
.pipeline-step {
    flex: 1;
    padding: 1.4rem 1rem;
    text-align: center;
    position: relative;
    transition: background 0.2s;
}
.pipeline-step::after {
    content: '›';
    position: absolute;
    right: -10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.6rem;
    color: #CBD5E0;
    z-index: 2;
}
.pipeline-step:last-child::after { display: none; }
.pipeline-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }
.pipeline-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 700;
    color: #718096;
    margin-bottom: 0.3rem;
}
.pipeline-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
}
.pipeline-pct {
    font-size: 0.78rem;
    color: #718096;
    margin-top: 0.15rem;
}

/* ---- KPI CARDS ---- */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.4rem;
    box-shadow: 0 2px 12px rgba(15,32,68,0.06);
    border-top: 3px solid var(--c);
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}
.kpi-title { font-size: 0.78rem; font-weight: 600; color: #718096; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; color: var(--c); }
.kpi-sub { font-size: 0.78rem; color: #A0AEC0; }

/* ---- SECTION TITLE ---- */
.sec-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #0F2044;
    letter-spacing: -0.01em;
    margin: 1.8rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.sec-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E2E8F0;
    margin-left: 0.5rem;
}

/* ---- PROGRESS BAR ---- */
.prog-bar-outer {
    background: #EDF2F7;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.prog-bar-inner {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #0D7377, #16A34A);
    transition: width 0.5s ease;
}

/* ---- TABLE ---- */
.exec-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.exec-table th {
    background: #F7FAFC;
    color: #4A5568;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    padding: 0.75rem 1rem;
    border-bottom: 2px solid #E2E8F0;
    text-align: left;
}
.exec-table td { padding: 0.7rem 1rem; border-bottom: 1px solid #EDF2F7; color: #2D3748; }
.exec-table tr:hover td { background: #F7FAFC; }

/* ---- STATUS PILL ---- */
.pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    white-space: nowrap;
}
.pill-dev  { background:#E6F4F4; color:#0D7377; }
.pill-com  { background:#E8F1FB; color:#1A6BCC; }
.pill-rev  { background:#FEF3E2; color:#E07B00; }
.pill-val  { background:#DCFCE7; color:#16A34A; }
.pill-pen  { background:#FEE2E2; color:#9B1C1C; }

/* ---- SIDEBAR ---- */
[data-testid="stSidebar"] { background: #0F2044 !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stMultiSelect > div, 
[data-testid="stSidebar"] .stSelectbox > div { background: rgba(255,255,255,0.07) !important; border-radius: 8px; }
[data-testid="stSidebar"] h3 {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: rgba(255,255,255,0.4) !important;
    margin: 1.5rem 0 0.5rem 0;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.2) !important;
}

/* ---- PLOTLY override ---- */
.js-plotly-plot { border-radius: 14px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB HELPERS (mantidos do original)
# ============================================================
def get_github_config():
    try:
        if "GITHUB_TOKEN" not in st.secrets: return None, None, None
        token = st.secrets["GITHUB_TOKEN"]
        if "GITHUB_REPO" not in st.secrets: return token, None, None
        repo = st.secrets["GITHUB_REPO"]
        if '/' not in repo: return token, None, None
        file_path = st.secrets.get("GITHUB_FILE_PATH", "data/Dados/Comissionamento AD - UNs.csv")
        return token, repo, file_path
    except:
        return None, None, None

def test_github_connection():
    try:
        token, repo_name, _ = get_github_config()
        if not token or not repo_name: return False, "Configurações incompletas"
        g = Github(token)
        user = g.get_user()
        repo = g.get_repo(repo_name)
        return True, f"Conectado como {user.login}"
    except GithubException as e:
        if e.status == 401: return False, "Token inválido ou expirado"
        elif e.status == 404: return False, "Repositório não encontrado"
        else: return False, f"Erro GitHub: {e.status}"
    except Exception as e:
        return False, f"Erro: {str(e)}"

def load_data_from_github():
    try:
        token, repo_name, file_path = get_github_config()
        if not token or not repo_name: return None
        g = Github(token)
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(file_path)
        file_content = base64.b64decode(contents.content).decode('utf-8')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(file_content)
            temp_file = f.name
        df = pd.read_csv(temp_file, encoding='utf-8-sig')
        os.unlink(temp_file)
        return df
    except:
        return None

def atualizar_dados_github(arquivo_upload, branch="main"):
    try:
        token, repo_name, file_path = get_github_config()
        if not token or not repo_name: st.error("❌ Configurações do GitHub incompletas."); return False
        if arquivo_upload is None: st.error("❌ Nenhum arquivo selecionado."); return False
        if not arquivo_upload.name.endswith('.csv'): st.error("❌ O arquivo deve ser CSV."); return False
        g = Github(token)
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
            st.error(f"❌ Erro ao acessar repositório: {e.status}"); return False
        file_content = arquivo_upload.read()
        try:
            df_temp = pd.read_csv(io.BytesIO(file_content), encoding='utf-8-sig')
            st.success(f"✅ CSV válido com {len(df_temp)} linhas")
        except Exception as e:
            st.error(f"❌ Arquivo CSV inválido: {str(e)}"); return False
        try:
            contents = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                path=file_path,
                message=f"Atualização {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                content=file_content,
                sha=contents.sha,
                branch=branch
            )
        except GithubException as e:
            if e.status == 404:
                repo.create_file(path=file_path,
                    message=f"Criação {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    content=file_content, branch=branch)
            else:
                st.error(f"❌ Erro GitHub: {e.status}"); return False
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}"); return False

# ============================================================
# LÓGICA DE FLUXO DA ESTEIRA
# ============================================================
STATUS_VALIDOS = ["Desenvolvido", "Comissionado", "Necessário Revisão", "Validado", "Pendente"]

MAPA_FASES = {
    "DEV": "Desenvolvido",
    "COM": "Comissionado",
    "VAL": "Validado",
    "PEN": "Pendente",
    "REV": "Necessário Revisão",
}

def padronizar_status(valor):
    v = str(valor).strip()
    if v in MAPA_FASES:
        return MAPA_FASES[v]
    vl = v.lower()
    if "revisão" in vl or "revisao" in vl or "rev" == vl:
        return "Necessário Revisão"
    if "desenvolvido" in vl or "dev" == vl:
        return "Desenvolvido"
    if "comissionado" in vl or "com" == vl:
        return "Comissionado"
    if "validado" in vl or "val" == vl:
        return "Validado"
    if "pendente" in vl or "pen" == vl:
        return "Pendente"
    if v in STATUS_VALIDOS:
        return v
    return "Pendente"

# Ordem do pipeline para cálculo de progresso individual
PIPELINE_ORDEM = {"Pendente": 0, "Desenvolvido": 1, "Comissionado": 2, "Necessário Revisão": 2, "Validado": 3}

@st.cache_data(ttl=300)
def load_data(force_github=False):
    df = None
    fonte = "local"
    if force_github:
        df = load_data_from_github()
        if df is not None: fonte = "github"
    if df is None:
        caminho = os.path.join('data', 'Dados', 'Comissionamento AD - UNs.csv')
        if os.path.exists(caminho):
            df = pd.read_csv(caminho, encoding='utf-8-sig')
            fonte = "local"
        else:
            # Dados de exemplo para demonstração
            n = 150
            np.random.seed(42)
            status_pool = np.random.choice(
                ["Desenvolvido","Comissionado","Necessário Revisão","Validado","Pendente"],
                n, p=[0.20, 0.25, 0.15, 0.30, 0.10]
            )
            criados = pd.date_range("2025-01-01", periods=n, freq="3D")
            df = pd.DataFrame({
                "Cód. Equipamento":           [f"EQ{i:04d}" for i in range(1, n+1)],
                "Chamado Desenvolvimento":    [f"CHDEV-{1000+i}" for i in range(n)],
                "Tipo Equipamento":           np.random.choice(["Inversor","Transformador","Painel","Disjuntor","Relé","Medidor"], n),
                "Empresa":                    np.random.choice(["EMT","ETO"], n, p=[0.55,0.45]),
                "Fase":                       status_pool,
                "Responsável Desenvolvimento":np.random.choice(["João Silva","Maria Santos","Pedro Costa","Ana Oliveira","Carlos Souza"], n),
                "Responsável Comissionamento":np.random.choice(["Roberto Lima","Carla Mendes","Paulo Ferreira","Não atribuído"], n),
                "Responsável Auditoria":      np.random.choice(["Fernando Alves","Lucia Santos","Marcos Paulo","Não atribuído"], n),
                "Criado":                     criados.strftime("%d/%m/%Y %H:%M"),
                "Modificado":                 (criados + pd.to_timedelta(np.random.randint(1,30,n), unit="D")).strftime("%d/%m/%Y %H:%M"),
            })
            fonte = "exemplo"
    if df is not None:
        # Responsáveis padrão
        for col in ["Responsável Desenvolvimento","Responsável Comissionamento","Responsável Auditoria"]:
            if col not in df.columns: df[col] = "Não atribuído"
            else: df[col] = df[col].fillna("Não atribuído")
        # Empresa
        if "Empresa" not in df.columns: df["Empresa"] = "EMT"
        # Status
        col_status = next((c for c in ["Fase","Status","Status Detalhado"] if c in df.columns), None)
        if col_status:
            df["Status Detalhado"] = df[col_status].apply(padronizar_status)
        else:
            df["Status Detalhado"] = "Pendente"
        df.loc[~df["Status Detalhado"].isin(STATUS_VALIDOS), "Status Detalhado"] = "Pendente"
        # Datas
        for col in ["Criado","Modificado"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format="%d/%m/%Y %H:%M", errors="coerce")
        if "Criado" in df.columns:
            df["Ano"]    = df["Criado"].dt.year
            df["Mês"]    = df["Criado"].dt.month
            df["Mês/Ano"]= df["Criado"].dt.to_period("M").astype(str)
            df["Mês Nome"]= df["Criado"].dt.month.map(MESES_PT)
            df["Semana"] = df["Criado"].dt.isocalendar().week.astype(int)
            df["Dia"]    = df["Criado"].dt.date
        # Nível no pipeline
        df["Pipeline Nível"] = df["Status Detalhado"].map(PIPELINE_ORDEM).fillna(0)
    return df, fonte

# ============================================================
# HELPERS DE VISUALIZAÇÃO
# ============================================================
def layout_exec(fig, titulo="", height=380):
    fig.update_layout(
        title=dict(text=titulo, font=dict(family="Syne, sans-serif", size=14, color="#0F2044"), x=0.5, xanchor="center") if titulo else dict(text=""),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", size=12, color="#4A5568"),
        margin=dict(l=40, r=20, t=50 if titulo else 30, b=40),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="DM Sans, sans-serif"),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F0F4F8", linecolor="#E2E8F0", tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F0F4F8", linecolor="#E2E8F0", tickfont=dict(size=11))
    return fig

def pill_html(status):
    classes = {
        "Desenvolvido": "pill-dev",
        "Comissionado": "pill-com",
        "Necessário Revisão": "pill-rev",
        "Validado": "pill-val",
        "Pendente": "pill-pen",
    }
    cls = classes.get(status, "pill-pen")
    label = "Revisão" if status == "Necessário Revisão" else status
    return f"<span class='pill {cls}'>{label}</span>"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='padding:1.5rem 0 1rem 0; text-align:center;'>
        <div style='font-family:Syne,sans-serif; font-size:1.2rem; font-weight:800; color:white; letter-spacing:-0.02em;'>
            ⚡ Fábrica SCADA
        </div>
        <div style='font-size:0.75rem; color:rgba(255,255,255,0.45); margin-top:0.2rem;'>Radar de Comissionamento</div>
    </div>
    <hr style='border-color:rgba(255,255,255,0.1); margin-bottom:1rem;'>
    """, unsafe_allow_html=True)

    if "df" not in st.session_state:
        with st.spinner("Carregando..."):
            df_raw, fonte_raw = load_data()
            st.session_state.df   = df_raw
            st.session_state.fonte = fonte_raw

    df_all  = st.session_state.df
    fonte   = st.session_state.fonte

    st.markdown("### FONTE")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↻ GitHub", use_container_width=True):
            with st.spinner("Sincronizando..."):
                df_n, f_n = load_data(force_github=True)
                if df_n is not None:
                    st.session_state.df = df_n; st.session_state.fonte = f_n
                    st.rerun()
    with col2:
        if st.button("↻ Local", use_container_width=True):
            st.cache_data.clear()
            df_n, f_n = load_data()
            st.session_state.df = df_n; st.session_state.fonte = f_n
            st.rerun()

    fonte_icon = {"github":"🟢 GitHub","local":"🔵 Local","exemplo":"🟡 Demo"}.get(fonte, fonte)
    st.markdown(f"<div style='font-size:0.75rem; color:rgba(255,255,255,0.4); margin-bottom:1rem;'>{fonte_icon}</div>", unsafe_allow_html=True)

    with st.expander("📤 Upload CSV"):
        branch = st.selectbox("Branch", ["main","master"])
        arq = st.file_uploader("Arquivo CSV", type=["csv"])
        if arq and st.button("Enviar ao GitHub"):
            with st.spinner("Enviando..."):
                if atualizar_dados_github(arq, branch):
                    time.sleep(1); st.rerun()

    st.markdown("### FILTROS")

    if df_all is not None:
        empresas = st.multiselect("Empresa", sorted(df_all["Empresa"].unique()),
                                   default=sorted(df_all["Empresa"].unique()))
        tipos = st.multiselect("Tipo de Equipamento",
                                sorted(df_all["Tipo Equipamento"].unique()),
                                default=sorted(df_all["Tipo Equipamento"].unique()))
        status_opts = st.multiselect("Status",
                                      STATUS_VALIDOS, default=STATUS_VALIDOS)
        resp_dev = st.multiselect("Resp. Desenvolvimento",
                                   sorted(df_all["Responsável Desenvolvimento"].unique()), default=[])
        data_range = None
        if "Criado" in df_all.columns and not df_all["Criado"].isna().all():
            st.markdown("**Período**")
            d_min = df_all["Criado"].min().date()
            d_max = df_all["Criado"].max().date()
            d_ini = st.date_input("De", d_min)
            d_fim = st.date_input("Até", d_max)
            data_range = (d_ini, d_fim)

        if st.button("Limpar Filtros", use_container_width=True):
            st.rerun()

    st.markdown("""
    <hr style='border-color:rgba(255,255,255,0.1); margin:1.5rem 0 1rem 0;'>
    <div style='font-size:0.7rem; color:rgba(255,255,255,0.3); text-align:center;'>
        v4.0 · © 2026 Energisa
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# DADOS FILTRADOS
# ============================================================
if df_all is None:
    st.error("❌ Não foi possível carregar os dados.")
    st.stop()

df = df_all.copy()
if empresas:  df = df[df["Empresa"].isin(empresas)]
if tipos:     df = df[df["Tipo Equipamento"].isin(tipos)]
if status_opts: df = df[df["Status Detalhado"].isin(status_opts)]
if resp_dev:  df = df[df["Responsável Desenvolvimento"].isin(resp_dev)]
if data_range and "Criado" in df.columns:
    df = df[(df["Criado"].dt.date >= data_range[0]) & (df["Criado"].dt.date <= data_range[1])]

# ============================================================
# MÉTRICAS BASE
# ============================================================
total  = len(df)
n_dev  = len(df[df["Status Detalhado"] == "Desenvolvido"])
n_com  = len(df[df["Status Detalhado"] == "Comissionado"])
n_rev  = len(df[df["Status Detalhado"] == "Necessário Revisão"])
n_val  = len(df[df["Status Detalhado"] == "Validado"])
n_pen  = len(df[df["Status Detalhado"] == "Pendente"])

# Taxa de conclusão = Validados / Total
taxa_conclusao = (n_val / total * 100) if total > 0 else 0
# Taxa de comissionamento = (Comissionados + Validados) / Total
taxa_comiss    = ((n_com + n_val) / total * 100) if total > 0 else 0
# Em andamento = tudo menos Pendente
em_andamento   = n_dev + n_com + n_rev + n_val

pct = lambda v: f"{v/total*100:.1f}%" if total > 0 else "—"

# ============================================================
# HEADER
# ============================================================
data_ref = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="exec-header">
    <div style="background:rgba(255,255,255,0.15); border-radius:12px; width:64px; height:64px;
                display:flex; align-items:center; justify-content:center; font-size:2rem; flex-shrink:0;">⚡</div>
    <div class="exec-header-text">
        <h1>Radar de Comissionamento</h1>
        <p>Acompanhamento da Esteira de Desenvolvimento · Fábrica SCADA · EMT | ETO</p>
        <span class="exec-badge">📅 {data_ref} &nbsp;·&nbsp; {total} registros &nbsp;·&nbsp; {fonte.upper()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PIPELINE VISUAL — FLUXO DA ESTEIRA
# ============================================================
st.markdown("<div class='sec-title'>🔄 Fluxo da Esteira</div>", unsafe_allow_html=True)
st.markdown(f"""
<div class="pipeline-wrap">
    <div class="pipeline-step" style="background:#F0FAF9;">
        <div class="pipeline-icon">⚙️</div>
        <div class="pipeline-label">Desenvolvidos</div>
        <div class="pipeline-value" style="color:{COR_DEV};">{n_dev}</div>
        <div class="pipeline-pct">{pct(n_dev)}</div>
    </div>
    <div class="pipeline-step" style="background:#EBF4FF;">
        <div class="pipeline-icon">🔧</div>
        <div class="pipeline-label">Comissionados</div>
        <div class="pipeline-value" style="color:{COR_COM};">{n_com}</div>
        <div class="pipeline-pct">{pct(n_com)}</div>
    </div>
    <div class="pipeline-step" style="background:#FFF8ED;">
        <div class="pipeline-icon">🔁</div>
        <div class="pipeline-label">Em Revisão</div>
        <div class="pipeline-value" style="color:{COR_REV};">{n_rev}</div>
        <div class="pipeline-pct">{pct(n_rev)}</div>
    </div>
    <div class="pipeline-step" style="background:#F0FDF4;">
        <div class="pipeline-icon">✅</div>
        <div class="pipeline-label">Validados</div>
        <div class="pipeline-value" style="color:{COR_VAL};">{n_val}</div>
        <div class="pipeline-pct">{pct(n_val)}</div>
    </div>
    <div class="pipeline-step" style="background:#FFF5F5;">
        <div class="pipeline-icon">⏳</div>
        <div class="pipeline-label">Pendentes</div>
        <div class="pipeline-value" style="color:{COR_PEN};">{n_pen}</div>
        <div class="pipeline-pct">{pct(n_pen)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# BARRA DE PROGRESSO GLOBAL
# ============================================================
st.markdown(f"""
<div style="background:white; border-radius:14px; padding:1.4rem 1.8rem;
            box-shadow:0 2px 12px rgba(15,32,68,0.06); margin-bottom:1.5rem;">
    <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.6rem;">
        <span style="font-family:Syne,sans-serif; font-weight:700; color:#0F2044; font-size:0.95rem;">
            Progresso Geral da Esteira
        </span>
        <span style="font-family:Syne,sans-serif; font-weight:800; font-size:1.5rem; color:#16A34A;">
            {taxa_conclusao:.1f}%
        </span>
    </div>
    <div class="prog-bar-outer">
        <div class="prog-bar-inner" style="width:{taxa_conclusao:.1f}%;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:0.5rem; font-size:0.78rem; color:#A0AEC0;">
        <span>0%</span>
        <span style="color:#4A5568;">{n_val} de {total} equipamentos validados</span>
        <span>100%</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPI SECUNDÁRIOS
# ============================================================
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card" style="--c:{COR_ACCENT};">
        <div class="kpi-title">Total Cadastrado</div>
        <div class="kpi-value">{total}</div>
        <div class="kpi-sub">equipamentos na esteira</div>
    </div>
    <div class="kpi-card" style="--c:{COR_COM};">
        <div class="kpi-title">Taxa de Comissionamento</div>
        <div class="kpi-value">{taxa_comiss:.1f}%</div>
        <div class="kpi-sub">{n_com + n_val} comissionados ou validados</div>
    </div>
    <div class="kpi-card" style="--c:{COR_VAL};">
        <div class="kpi-title">Taxa de Validação</div>
        <div class="kpi-value">{taxa_conclusao:.1f}%</div>
        <div class="kpi-sub">{n_val} equipamentos concluídos</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ABAS PRINCIPAIS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Executiva",
    "📈 Evolução Temporal",
    "👥 Responsáveis",
    "🏢 Por Empresa",
])

# ──────────────────────────────────────────────
# TAB 1 — VISÃO EXECUTIVA
# ──────────────────────────────────────────────
with tab1:
    col_a, col_b = st.columns(2)

    # Donut — Distribuição geral
    with col_a:
        st.markdown("<div class='sec-title'>Distribuição por Status</div>", unsafe_allow_html=True)
        dist = df["Status Detalhado"].value_counts().reindex(STATUS_VALIDOS).dropna().reset_index()
        dist.columns = ["Status","Qtd"]
        fig_donut = go.Figure(go.Pie(
            labels=dist["Status"],
            values=dist["Qtd"],
            hole=0.55,
            marker_colors=[MAPA_CORES.get(s, "#CBD5E0") for s in dist["Status"]],
            textinfo="label+percent",
            textfont=dict(family="DM Sans, sans-serif", size=11),
            hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{total}</b><br><span style='font-size:10px'>Total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(family="Syne, sans-serif", size=20, color="#0F2044")
        )
        fig_donut = layout_exec(fig_donut, height=360)
        fig_donut.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_donut, use_container_width=True)

    # Barras — EMT vs ETO
    with col_b:
        st.markdown("<div class='sec-title'>EMT × ETO por Status</div>", unsafe_allow_html=True)
        comp = df.groupby(["Empresa","Status Detalhado"]).size().reset_index(name="Qtd")
        fig_comp = px.bar(
            comp, x="Empresa", y="Qtd", color="Status Detalhado",
            barmode="group",
            color_discrete_map=MAPA_CORES,
            text="Qtd",
            category_orders={"Status Detalhado": STATUS_VALIDOS},
        )
        fig_comp.update_traces(textposition="outside", textfont_size=11)
        fig_comp = layout_exec(fig_comp, height=360)
        fig_comp.update_layout(xaxis_title="", yaxis_title="Equipamentos", legend_title="")
        st.plotly_chart(fig_comp, use_container_width=True)

    # Funil do pipeline
    st.markdown("<div class='sec-title'>Funil do Pipeline de Validação</div>", unsafe_allow_html=True)
    # Funil acumulativo: cada etapa inclui os que passaram por ela
    funil_vals = [
        ("1. Cadastrados",          total,            COR_PRIMARIA),
        ("2. Desenvolvidos",        n_dev + n_com + n_rev + n_val, COR_DEV),
        ("3. Comissionados",        n_com + n_val,    COR_COM),
        ("4. Em Revisão",           n_rev,            COR_REV),
        ("5. Validados (Concluído)",n_val,             COR_VAL),
    ]
    fig_funil = go.Figure(go.Funnel(
        y=[f[0] for f in funil_vals],
        x=[f[1] for f in funil_vals],
        marker_color=[f[2] for f in funil_vals],
        textposition="inside",
        textinfo="value+percent initial",
        connector=dict(line=dict(color="#E2E8F0", dash="dot", width=1)),
    ))
    fig_funil = layout_exec(fig_funil, "Funil da Esteira — Progressão Acumulada", height=380)
    st.plotly_chart(fig_funil, use_container_width=True)

    # Tabela resumo por tipo de equipamento
    st.markdown("<div class='sec-title'>Resumo por Tipo de Equipamento</div>", unsafe_allow_html=True)
    if "Tipo Equipamento" in df.columns:
        tbl = df.groupby("Tipo Equipamento")["Status Detalhado"].value_counts().unstack(fill_value=0)
        for col in STATUS_VALIDOS:
            if col not in tbl.columns: tbl[col] = 0
        tbl = tbl[STATUS_VALIDOS]
        tbl["Total"] = tbl.sum(axis=1)
        tbl["% Validado"] = (tbl.get("Validado", 0) / tbl["Total"] * 100).round(1).astype(str) + "%"
        tbl = tbl.sort_values("Total", ascending=False).reset_index()
        st.dataframe(
            tbl.rename(columns={"Tipo Equipamento":"Tipo","Necessário Revisão":"Revisão"}),
            use_container_width=True, hide_index=True
        )

# ──────────────────────────────────────────────
# TAB 2 — EVOLUÇÃO TEMPORAL
# ──────────────────────────────────────────────
with tab2:
    if "Criado" not in df.columns or df["Criado"].isna().all():
        st.info("Dados de data não disponíveis.")
    else:
        col_ag, col_tp = st.columns([1,1])
        with col_ag:
            agregacao = st.radio("Agregação", ["Mês","Semana","Dia"], horizontal=True)
        with col_tp:
            tipo_viz = st.radio("Tipo", ["Barras","Linhas"], horizontal=True)

        col_map = {"Mês":"Mês/Ano","Semana":"Semana","Dia":"Dia"}
        p_col = col_map[agregacao]

        # Evolução por status
        st.markdown("<div class='sec-title'>Novos Cadastros por Período e Status</div>", unsafe_allow_html=True)
        evol = df.groupby([p_col,"Status Detalhado"]).size().reset_index(name="Qtd")
        evol = evol.sort_values(p_col)

        if tipo_viz == "Barras":
            fig_ev = px.bar(evol, x=p_col, y="Qtd", color="Status Detalhado",
                            barmode="stack", color_discrete_map=MAPA_CORES,
                            category_orders={"Status Detalhado": STATUS_VALIDOS})
            fig_ev.update_traces(textposition="inside")
        else:
            fig_ev = px.line(evol, x=p_col, y="Qtd", color="Status Detalhado",
                             markers=True, color_discrete_map=MAPA_CORES,
                             category_orders={"Status Detalhado": STATUS_VALIDOS})
        fig_ev = layout_exec(fig_ev, height=380)
        fig_ev.update_layout(xaxis_tickangle=30, xaxis_title="", yaxis_title="Equipamentos", legend_title="")
        st.plotly_chart(fig_ev, use_container_width=True)

        # Acumulado de validações
        st.markdown("<div class='sec-title'>Validações Acumuladas no Tempo</div>", unsafe_allow_html=True)
        df_val_temp = df[df["Status Detalhado"] == "Validado"].copy()
        if not df_val_temp.empty:
            val_grp = df_val_temp.groupby(p_col).size().reset_index(name="Validados")
            val_grp = val_grp.sort_values(p_col)
            val_grp["Acumulado"] = val_grp["Validados"].cumsum()

            fig_acum = go.Figure()
            fig_acum.add_trace(go.Bar(
                x=val_grp[p_col], y=val_grp["Validados"],
                name="No período", marker_color=COR_VAL, opacity=0.5,
                text=val_grp["Validados"], textposition="outside"
            ))
            fig_acum.add_trace(go.Scatter(
                x=val_grp[p_col], y=val_grp["Acumulado"],
                name="Acumulado", mode="lines+markers",
                line=dict(color=COR_PRIMARIA, width=2.5),
                marker=dict(size=7)
            ))
            fig_acum = layout_exec(fig_acum, height=360)
            fig_acum.update_layout(xaxis_tickangle=30, legend_title="")
            st.plotly_chart(fig_acum, use_container_width=True)
        else:
            st.info("Nenhum equipamento validado no período filtrado.")

        # Separado por empresa
        st.markdown("<div class='sec-title'>Evolução por Empresa</div>", unsafe_allow_html=True)
        evol_emp = df.groupby([p_col,"Empresa","Status Detalhado"]).size().reset_index(name="Qtd")
        evol_emp = evol_emp.sort_values(p_col)
        fig_emp = px.bar(evol_emp, x=p_col, y="Qtd", color="Status Detalhado",
                         facet_col="Empresa", barmode="stack",
                         color_discrete_map=MAPA_CORES,
                         category_orders={"Status Detalhado": STATUS_VALIDOS})
        fig_emp.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig_emp = layout_exec(fig_emp, height=360)
        fig_emp.update_layout(xaxis_tickangle=30, legend_title="")
        st.plotly_chart(fig_emp, use_container_width=True)

# ──────────────────────────────────────────────
# TAB 3 — RESPONSÁVEIS
# ──────────────────────────────────────────────
with tab3:
    tipo_resp = st.radio(
        "Visão por responsável de:",
        ["Desenvolvimento","Comissionamento","Auditoria"],
        horizontal=True
    )
    col_r = {
        "Desenvolvimento":"Responsável Desenvolvimento",
        "Comissionamento":"Responsável Comissionamento",
        "Auditoria":"Responsável Auditoria"
    }[tipo_resp]

    if col_r not in df.columns:
        st.info(f"Coluna '{col_r}' não encontrada.")
    else:
        df_r = df[df[col_r] != "Não atribuído"].copy()

        if df_r.empty:
            st.info("Nenhum responsável atribuído.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"<div class='sec-title'>Ranking — {tipo_resp}</div>", unsafe_allow_html=True)
                rank = df_r[col_r].value_counts().head(15).reset_index()
                rank.columns = ["Responsável","Total"]
                fig_rank = px.bar(rank, x="Total", y="Responsável", orientation="h",
                                  color="Total", color_continuous_scale=["#93C5FD","#1A6BCC","#0F2044"],
                                  text="Total")
                fig_rank.update_traces(textposition="outside")
                fig_rank = layout_exec(fig_rank, height=420)
                fig_rank.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
                st.plotly_chart(fig_rank, use_container_width=True)

            with col2:
                st.markdown(f"<div class='sec-title'>Status por Responsável</div>", unsafe_allow_html=True)
                top10 = rank.head(10)["Responsável"].tolist()
                dist_r = df_r[df_r[col_r].isin(top10)].groupby([col_r,"Status Detalhado"]).size().reset_index(name="Qtd")
                fig_dr = px.bar(dist_r, x=col_r, y="Qtd", color="Status Detalhado",
                                barmode="stack", color_discrete_map=MAPA_CORES,
                                category_orders={"Status Detalhado": STATUS_VALIDOS})
                fig_dr.update_traces(textposition="inside")
                fig_dr = layout_exec(fig_dr, height=420)
                fig_dr.update_layout(xaxis_tickangle=35, legend_title="", xaxis_title="")
                st.plotly_chart(fig_dr, use_container_width=True)

            # Taxa de sucesso
            st.markdown("<div class='sec-title'>Taxa de Conclusão por Responsável</div>", unsafe_allow_html=True)
            taxa_r = (
                df_r.groupby(col_r)
                .apply(lambda x: len(x[x["Status Detalhado"] == "Validado"]) / len(x) * 100)
                .reset_index(name="Taxa (%)")
                .sort_values("Taxa (%)", ascending=False)
                .head(15)
            )
            taxa_r.columns = ["Responsável","Taxa (%)"]
            fig_taxa = px.bar(taxa_r, x="Taxa (%)", y="Responsável", orientation="h",
                              color="Taxa (%)", color_continuous_scale=["#BBF7D0","#16A34A","#14532D"],
                              text=taxa_r["Taxa (%)"].round(1).astype(str) + "%")
            fig_taxa.update_traces(textposition="outside")
            fig_taxa = layout_exec(fig_taxa, height=400)
            fig_taxa.update_layout(yaxis=dict(autorange="reversed"),
                                   xaxis_range=[0, 105], coloraxis_showscale=False)
            st.plotly_chart(fig_taxa, use_container_width=True)

# ──────────────────────────────────────────────
# TAB 4 — POR EMPRESA
# ──────────────────────────────────────────────
with tab4:
    empresa_sel = st.selectbox("Empresa", sorted(df["Empresa"].unique()))
    df_e = df[df["Empresa"] == empresa_sel]

    if df_e.empty:
        st.info("Sem dados para esta empresa.")
    else:
        t_e   = len(df_e)
        n_dev_e = len(df_e[df_e["Status Detalhado"] == "Desenvolvido"])
        n_com_e = len(df_e[df_e["Status Detalhado"] == "Comissionado"])
        n_rev_e = len(df_e[df_e["Status Detalhado"] == "Necessário Revisão"])
        n_val_e = len(df_e[df_e["Status Detalhado"] == "Validado"])
        n_pen_e = len(df_e[df_e["Status Detalhado"] == "Pendente"])
        taxa_e  = (n_val_e / t_e * 100) if t_e > 0 else 0

        # Mini pipeline
        st.markdown(f"""
        <div class="pipeline-wrap" style="margin-top:1rem;">
            <div class="pipeline-step" style="background:#F0FAF9;">
                <div class="pipeline-icon">⚙️</div>
                <div class="pipeline-label">Desenvolvidos</div>
                <div class="pipeline-value" style="color:{COR_DEV};">{n_dev_e}</div>
            </div>
            <div class="pipeline-step" style="background:#EBF4FF;">
                <div class="pipeline-icon">🔧</div>
                <div class="pipeline-label">Comissionados</div>
                <div class="pipeline-value" style="color:{COR_COM};">{n_com_e}</div>
            </div>
            <div class="pipeline-step" style="background:#FFF8ED;">
                <div class="pipeline-icon">🔁</div>
                <div class="pipeline-label">Em Revisão</div>
                <div class="pipeline-value" style="color:{COR_REV};">{n_rev_e}</div>
            </div>
            <div class="pipeline-step" style="background:#F0FDF4;">
                <div class="pipeline-icon">✅</div>
                <div class="pipeline-label">Validados</div>
                <div class="pipeline-value" style="color:{COR_VAL};">{n_val_e}</div>
            </div>
            <div class="pipeline-step" style="background:#FFF5F5;">
                <div class="pipeline-icon">⏳</div>
                <div class="pipeline-label">Pendentes</div>
                <div class="pipeline-value" style="color:{COR_PEN};">{n_pen_e}</div>
            </div>
        </div>
        <div style="background:white; border-radius:12px; padding:1rem 1.5rem; margin:1rem 0 1.5rem 0;
                    box-shadow:0 2px 10px rgba(15,32,68,0.06);">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                <span style="font-family:Syne,sans-serif; font-weight:700; color:#0F2044;">
                    Progresso {empresa_sel}
                </span>
                <span style="font-family:Syne,sans-serif; font-weight:800; color:#16A34A;">{taxa_e:.1f}%</span>
            </div>
            <div class="prog-bar-outer">
                <div class="prog-bar-inner" style="width:{taxa_e:.1f}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='sec-title'>Distribuição de Status</div>", unsafe_allow_html=True)
            dist_e = df_e["Status Detalhado"].value_counts().reindex(STATUS_VALIDOS).dropna().reset_index()
            dist_e.columns = ["Status","Qtd"]
            fig_de = px.pie(dist_e, values="Qtd", names="Status", hole=0.5,
                            color="Status", color_discrete_map=MAPA_CORES)
            fig_de.update_traces(textinfo="label+percent", textfont_size=11)
            fig_de = layout_exec(fig_de, height=340)
            st.plotly_chart(fig_de, use_container_width=True)

        with col2:
            st.markdown("<div class='sec-title'>Taxa por Tipo de Equipamento</div>", unsafe_allow_html=True)
            if "Tipo Equipamento" in df_e.columns:
                taxa_tipo = (
                    df_e.groupby("Tipo Equipamento")
                    .apply(lambda x: len(x[x["Status Detalhado"].isin(["Comissionado","Validado"])]) / len(x) * 100)
                    .reset_index(name="Taxa Comissionamento (%)")
                    .sort_values("Taxa Comissionamento (%)", ascending=False)
                )
                taxa_tipo.columns = ["Tipo","Taxa (%)"]
                fig_tt = px.bar(taxa_tipo, x="Taxa (%)", y="Tipo", orientation="h",
                                color="Taxa (%)", color_continuous_scale=["#BFDBFE","#1A6BCC"],
                                text=taxa_tipo["Taxa (%)"].round(1).astype(str) + "%")
                fig_tt.update_traces(textposition="outside")
                fig_tt = layout_exec(fig_tt, height=340)
                fig_tt.update_layout(xaxis_range=[0, 105], coloraxis_showscale=False)
                st.plotly_chart(fig_tt, use_container_width=True)

        # Pendentes
        st.markdown("<div class='sec-title'>⚠️ Equipamentos Pendentes de Validação</div>", unsafe_allow_html=True)
        pendentes_e = df_e[df_e["Status Detalhado"] != "Validado"].sort_values("Pipeline Nível", ascending=False)
        if not pendentes_e.empty:
            cols_show = ["Cód. Equipamento","Tipo Equipamento","Status Detalhado",
                         "Responsável Desenvolvimento","Responsável Comissionamento"]
            cols_ok = [c for c in cols_show if c in pendentes_e.columns]
            st.warning(f"**{len(pendentes_e)}** equipamentos ainda não validados na {empresa_sel}.")
            st.dataframe(pendentes_e[cols_ok], use_container_width=True, hide_index=True)
        else:
            st.success(f"🎉 Todos os equipamentos de **{empresa_sel}** estão validados!")

# ============================================================
# RODAPÉ EXECUTIVO
# ============================================================
st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div style="font-size:0.78rem; color:#A0AEC0;">
        <strong style="color:#4A5568;">© 2026 Energisa</strong><br>
        Fábrica SCADA · v4.0
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div style="font-size:0.78rem; color:#A0AEC0; text-align:center;">
        <strong style="color:#4A5568;">🕒 {data_ref}</strong><br>
        Fonte: {fonte.upper()} · {total} registros
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div style="font-size:0.78rem; color:#A0AEC0; text-align:right;">
        <strong style="color:#4A5568;">📞 Suporte</strong><br>
        kewin.ferreira@energisa.com.br
    </div>""", unsafe_allow_html=True)
