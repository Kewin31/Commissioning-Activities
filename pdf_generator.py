# pdf_generator.py - VERSÃO EXECUTIVA PROFISSIONAL
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

# ============================================
# CONFIGURAÇÃO DE ESTILO GLOBAL
# ============================================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'

CORES_ENERGISA = {
    'primary': '#005973',
    'secondary': '#028a9f',
    'accent': '#04d8d7',
    'success': '#2E7D32',
    'warning': '#F57C00',
    'danger': '#C62828',
    'dark': '#1f2937',
    'gray': '#6b7280',
    'light': '#f3f4f6',
    'white': '#ffffff'
}

CORES_MOTIVOS = {
    'E-MAIL': '#C62828',
    'APR': '#F57C00',
    'MEDIÇÃO': '#6A1B9A',
    'DOCUMENTAÇÃO': '#1565C0',
    'EQUIPAMENTO': '#00838F',
    'OUTROS': '#6b7280'
}

# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def get_horario_brasilia():
    utc_now = datetime.now(timezone.utc)
    return utc_now - timedelta(hours=3)

def calcular_desenvolvidos_acumulado(df):
    status_incluidos = ['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_comissionados_acumulado(df):
    status_incluidos = ['Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_validados_acumulado(df):
    return len(df[df['Status'] == 'Validado'])

def calcular_em_revisao(df):
    return len(df[df['Status'] == 'Necessário Revisão'])

def criar_grafico_kpi_donut(valor, total, titulo, cor, subtitulo=""):
    """Cria um mini gráfico donut para KPIs"""
    fig, ax = plt.subplots(figsize=(2.5, 2.5))
    fig.patch.set_facecolor('white')
    
    pct = (valor / total * 100) if total > 0 else 0
    
    # Donut
    wedges, _ = ax.pie(
        [pct, 100-pct],
        colors=[cor, '#e5e7eb'],
        startangle=90,
        wedgeprops=dict(width=0.3, edgecolor='white', linewidth=2)
    )
    
    # Texto central
    ax.text(0, 0.15, f'{valor}', ha='center', va='center', fontsize=18, fontweight='bold', color=cor)
    ax.text(0, -0.1, f'de {total}', ha='center', va='center', fontsize=8, color='#6b7280')
    if subtitulo:
        ax.text(0, -0.28, subtitulo, ha='center', va='center', fontsize=7, color='#9ca3af')
    
    ax.set_title(titulo, fontsize=9, fontweight='bold', color='#1f2937', pad=10)
    return fig

def criar_grafico_barras_progresso(categorias, valores, cores, titulo):
    """Cria gráfico de barras horizontal estilizado"""
    fig, ax = plt.subplots(figsize=(8, 2.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    y_pos = [0]
    left = 0
    
    for i, (cat, val, cor) in enumerate(zip(categorias, valores, cores)):
        if val > 0:
            bar = ax.barh(0, val, left=left, color=cor, height=0.6, edgecolor='white', linewidth=2)
            # Texto dentro da barra
            if val > 5:
                ax.text(left + val/2, 0, f'{cat}\n{val} ({val/sum(valores)*100:.0f}%)', 
                       ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            left += val
    
    ax.set_xlim(0, sum(valores))
    ax.set_ylim(-0.5, 0.5)
    ax.axis('off')
    ax.set_title(titulo, fontsize=10, fontweight='bold', color='#1f2937', pad=10, loc='left')
    
    return fig

def criar_grafico_motivos_executivo(motivos_count, total_motivos):
    """Gráfico de pizza executivo para motivos"""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    
    # Cores personalizadas
    cores = ['#C62828', '#E53935', '#F57C00', '#FF8F00', '#6A1B9A', 
             '#1565C0', '#00838F', '#00695C', '#2E7D32', '#558B2F']
    
    valores = motivos_count.values.tolist()
    
    # Criar labels com %
    labels = []
    for motivo, qtd in zip(motivos_count.index, valores):
        pct = (qtd / total_motivos * 100) if total_motivos > 0 else 0
        nome = motivo[:30] + '...' if len(motivo) > 30 else motivo
        labels.append(f'{nome}\n{qtd} ({pct:.1f}%)')
    
    # Pizza
    wedges, texts = ax.pie(
        valores,
        labels=labels,
        colors=cores[:len(valores)],
        startangle=140,
        labeldistance=1.15,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=3),
        textprops={'fontsize': 7, 'fontweight': 'bold', 'color': '#374151'}
    )
    
    # Destacar fatias pequenas
    for i, (wedge, val) in enumerate(zip(wedges, valores)):
        pct = (val / total_motivos * 100) if total_motivos > 0 else 0
        if pct < 5:
            wedge.set_edgecolor('#f3f4f6')
            wedge.set_linewidth(1)
    
    # Círculo central
    centre_circle = plt.Circle((0, 0), 0.25, fc='white', linewidth=3, edgecolor=CORES_ENERGISA['primary'])
    ax.add_artist(centre_circle)
    
    ax.text(0, 0.08, f'{total_motivos}', ha='center', va='center', 
            fontsize=26, fontweight='bold', color=CORES_ENERGISA['primary'])
    ax.text(0, -0.10, 'equipamentos\ncom revisão', ha='center', va='center', 
            fontsize=8, color='#6b7280')
    
    ax.set_title('Distribuição dos Motivos de Revisão', fontsize=13, fontweight='bold', 
                 color=CORES_ENERGISA['dark'], pad=25)
    
    plt.tight_layout(pad=2)
    return fig

# ============================================
# FUNÇÃO PRINCIPAL DE GERAÇÃO DO RELATÓRIO
# ============================================
def gerar_relatorio_executivo(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """Gera relatório PDF executivo profissional"""
    
    # Filtrar dados
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    if df_empresa.empty:
        raise ValueError(f"Sem dados para {empresa}")
    
    # Aplicar filtros de período
    df_periodo = df_empresa.copy()
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        if 'Mes_Nome' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Mes_Nome'] == mes_selecionado]
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Ano'] == ano_selecionado]
    
    if df_periodo.empty:
        raise ValueError(f"Sem dados para o período selecionado")
    
    # Métricas
    total_dev = calcular_desenvolvidos_acumulado(df_periodo)
    total_com = calcular_comissionados_acumulado(df_periodo)
    total_val = calcular_validados_acumulado(df_periodo)
    total_rev = calcular_em_revisao(df_periodo)
    
    pct_com = (total_com / total_dev * 100) if total_dev > 0 else 0
    pct_val = (total_val / total_dev * 100) if total_dev > 0 else 0
    pct_rev = (total_rev / total_dev * 100) if total_dev > 0 else 0
    
    # Motivos
    tem_motivos = False
    motivos_count = None
    total_com_motivo = 0
    
    if 'Motivo_Revisao' in df_periodo.columns:
        df_motivos = df_periodo[df_periodo['Motivo_Revisao'].notna() & 
                                 (df_periodo['Motivo_Revisao'] != '') &
                                 (df_periodo['Motivo_Revisao'] != 'N/A')]
        if not df_motivos.empty:
            tem_motivos = True
            motivos_count = df_motivos['Motivo_Revisao'].value_counts()
            total_com_motivo = len(df_motivos)
    
    # Data/hora
    data_hora = get_horario_brasilia()
    
    # ============================================
    # CRIAR PDF
    # ============================================
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # ============================================
    # CAPA
    # ============================================
    pdf.add_page()
    
    # Fundo da capa
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Faixa decorativa
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(0, 80, 210, 120, 'F')
    
    # Linha accent
    pdf.set_draw_color(4, 216, 215)
    pdf.set_line_width(2)
    pdf.line(20, 85, 190, 85)
    
    # Título principal
    pdf.set_y(95)
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, 'RELATÓRIO EXECUTIVO', 0, 1, 'C')
    
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    # Linha accent
    pdf.line(20, 190, 190, 190)
    
    # Unidade
    pdf.set_y(200)
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(4, 216, 215)
    pdf.cell(0, 10, f'UNIDADE {empresa}', 0, 1, 'C')
    
    # Período
    pdf.set_y(215)
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(255, 255, 255)
    periodo_str = f"{mes_selecionado}/{ano_selecionado}" if mes_selecionado and mes_selecionado != "Todos os Meses" else f"{ano_selecionado}" if ano_selecionado and ano_selecionado != "Todos os Anos" else "Período Completo"
    pdf.cell(0, 8, periodo_str, 0, 1, 'C')
    
    # Data
    pdf.set_y(260)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 6, f'Emitido em: {data_hora.strftime("%d/%m/%Y as %H:%M")} (Brasilia)', 0, 1, 'C')
    pdf.cell(0, 6, 'Confidencial - Uso Interno Energisa', 0, 1, 'C')
    
    # ============================================
    # PÁGINA 2 - SUMÁRIO EXECUTIVO
    # ============================================
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 35, 'F')
    
    pdf.set_y(10)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'SUMÁRIO EXECUTIVO', 0, 1, 'C')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Unidade {empresa} | {periodo_str}', 0, 1, 'C')
    
    # Métricas principais em cards
    pdf.set_y(45)
    
    # Card 1 - Progresso
    pdf.set_fill_color(240, 248, 255)
    pdf.set_draw_color(2, 138, 159)
    pdf.rect(15, 45, 85, 40, 'DF')
    pdf.set_xy(20, 50)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 6, 'PROGRESSO DO FLUXO', 0, 1)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 10, f'{pct_com:.1f}%', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'{total_com}/{total_dev} comissionados', 0, 1)
    
    # Card 2 - Validação
    pdf.set_fill_color(232, 245, 233)
    pdf.set_draw_color(46, 125, 50)
    pdf.rect(110, 45, 85, 40, 'DF')
    pdf.set_xy(115, 50)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 6, 'TAXA DE VALIDAÇÃO', 0, 1)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(46, 125, 50)
    taxa_val = (total_val / total_com * 100) if total_com > 0 else 0
    pdf.cell(0, 10, f'{taxa_val:.1f}%', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'{total_val} equipamentos validados', 0, 1)
    
    # Card 3 - Gargalo
    pdf.set_fill_color(255, 243, 224)
    pdf.set_draw_color(245, 124, 0)
    pdf.rect(15, 95, 85, 40, 'DF')
    pdf.set_xy(20, 100)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 6, 'GARGALO - EM REVISÃO', 0, 1)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 10, f'{pct_rev:.1f}%', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'{total_rev} equipamentos', 0, 1)
    
    # Card 4 - Motivos
    pdf.set_fill_color(243, 229, 245)
    pdf.set_draw_color(106, 27, 154)
    pdf.rect(110, 95, 85, 40, 'DF')
    pdf.set_xy(115, 100)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(106, 27, 154)
    pdf.cell(0, 6, 'MOTIVOS REGISTRADOS', 0, 1)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(106, 27, 154)
    pdf.cell(0, 10, str(total_com_motivo) if tem_motivos else '0', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'equipamentos com motivo', 0, 1)
    
    # Barra de progresso visual
    pdf.set_y(150)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, 'CADEIA DE VALOR DO COMISSIONAMENTO', 0, 1)
    
    # Barra horizontal
    bar_x, bar_y, bar_w, bar_h = 20, 165, 170, 15
    
    # Fundo
    pdf.set_fill_color(229, 231, 235)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, 'F')
    
    # Preenchimento
    if total_dev > 0:
        dev_w = bar_w * (total_dev / total_dev)
        com_w = bar_w * (pct_com / 100)
        val_w = bar_w * (pct_val / 100)
        
        pdf.set_fill_color(46, 125, 50)
        pdf.rect(bar_x, bar_y, val_w, bar_h, 'F')
        
        pdf.set_fill_color(2, 138, 159)
        pdf.rect(bar_x + val_w, bar_y, com_w - val_w, bar_h, 'F')
    
    # Labels
    pdf.set_y(185)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(55, 5, f'Desenvolvidos: {total_dev}', 0, 0, 'L')
    pdf.cell(55, 5, f'Comissionados: {total_com} ({pct_com:.0f}%)', 0, 0, 'C')
    pdf.cell(55, 5, f'Validados: {total_val} ({pct_val:.0f}%)', 0, 1, 'R')
    
    # Insights
    pdf.set_y(200)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, 'PRINCIPAIS INSIGHTS', 0, 1)
    pdf.set_draw_color(4, 216, 215)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    # Gerar insights automaticamente
    insights = []
    
    if pct_val >= 80:
        insights.append(f"✅ Excelente taxa de validação: {taxa_val:.0f}% dos comissionados foram validados com sucesso.")
    elif pct_val >= 50:
        insights.append(f"📌 Taxa de validação moderada: {taxa_val:.0f}%. Há oportunidades de melhoria no processo.")
    else:
        insights.append(f"⚠️ Atenção: Apenas {taxa_val:.0f}% dos comissionados foram validados. Necessário investigar gargalos.")
    
    if tem_motivos:
        motivo_top = motivos_count.index[0]
        qtd_top = motivos_count.values[0]
        insights.append(f"🔍 Principal motivo de revisão: '{motivo_top}' com {qtd_top} ocorrências ({qtd_top/total_com_motivo*100:.0f}% dos casos).")
    
    if pct_rev > 10:
        insights.append(f"⚠️ Alerta: {pct_rev:.1f}% dos equipamentos estão em revisão. Recomenda-se ação imediata.")
    
    improvements = [
        "💡 Recomendação: Implementar checklist de verificação pré-comissionamento.",
        "💡 Recomendação: Realizar treinamento sobre documentação padrão.",
        "💡 Recomendação: Automatizar validação de dados nos relatórios."
    ]
    
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(55, 65, 81)
    
    for insight in insights:
        pdf.set_x(25)
        pdf.multi_cell(160, 6, insight, 0, 'L')
        pdf.ln(1)
    
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 6, 'RECOMENDAÇÕES ESTRATÉGICAS', 0, 1)
    
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(55, 65, 81)
    for imp in improvements:
        pdf.set_x(25)
        pdf.cell(160, 6, imp, 0, 1)
    
    # ============================================
    # PÁGINA 3 - MOTIVOS DE REVISÃO (se houver)
    # ============================================
    if tem_motivos:
        pdf.add_page()
        
        # Cabeçalho
        pdf.set_fill_color(0, 89, 115)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_y(10)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'ANÁLISE DE MOTIVOS DE REVISÃO', 0, 1, 'C')
        
        # Tabela
        pdf.set_y(45)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 89, 115)
        pdf.cell(0, 8, f'Total: {total_com_motivo} equipamentos com motivo registrado', 0, 1)
        
        # Cabeçalho da tabela
        pdf.set_fill_color(0, 89, 115)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(10, 8, '#', 1, 0, 'C', 1)
        pdf.cell(95, 8, 'Motivo', 1, 0, 'C', 1)
        pdf.cell(35, 8, 'Qtd', 1, 0, 'C', 1)
        pdf.cell(35, 8, '%', 1, 1, 'C', 1)
        
        # Dados
        pdf.set_font('Arial', '', 8)
        for i, (motivo, qtd) in enumerate(motivos_count.items(), 1):
            pct = (qtd / total_com_motivo * 100) if total_com_motivo > 0 else 0
            
            # Cor por tipo
            if 'E-MAIL' in motivo.upper():
                pdf.set_text_color(198, 40, 40)
            elif 'APR' in motivo.upper():
                pdf.set_text_color(245, 124, 0)
            elif 'MEDIÇÃO' in motivo.upper():
                pdf.set_text_color(106, 27, 154)
            elif 'EQUIPAMENTO' in motivo.upper():
                pdf.set_text_color(21, 101, 192)
            elif 'CARD' in motivo.upper() or 'RELATÓRIO' in motivo.upper():
                pdf.set_text_color(0, 131, 143)
            else:
                pdf.set_text_color(55, 65, 81)
            
            pdf.set_fill_color(249, 250, 251) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(10, 7, str(i), 1, 0, 'C', 1)
            pdf.cell(95, 7, motivo[:55], 1, 0, 'L', 1)
            pdf.cell(35, 7, str(qtd), 1, 0, 'C', 1)
            pdf.cell(35, 7, f'{pct:.1f}%', 1, 1, 'C', 1)
        
        # Gráfico em página separada
        pdf.add_page()
        
        pdf.set_fill_color(0, 89, 115)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_y(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'DISTRIBUICAO DOS MOTIVOS DE REVISAO', 0, 1, 'C')
        
        fig_motivos = criar_grafico_motivos_executivo(motivos_count, total_com_motivo)
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig_motivos.savefig(temp_img.name, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig_motivos)
        
        pdf.image(temp_img.name, x=10, y=40, w=190)
        os.unlink(temp_img.name)
    
    # ============================================
    # PÁGINA FINAL - EQUIPE
    # ============================================
    pdf.add_page()
    
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_y(10)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'EQUIPE RESPONSÁVEL', 0, 1, 'C')
    
    # Cards da equipe
    equipe = [
        {'nome': 'Kewin Marcel Ramirez Ferreira', 'cargo': 'SRE - Elaboração', 'email': 'kewin.ferreira@energisa.com.br'},
        {'nome': 'Caio Alexandre da Silva Medeiros', 'cargo': 'Gestão', 'email': 'caio.medeiros@energisa.com.br'},
        {'nome': 'Mauricio Dias Avelino', 'cargo': 'Coord Tech Proj Sist Operativos', 'email': 'mauricio.avelino@energisa.com.br'},
        {'nome': 'Cassio Fernando Bazana Nonenmacher', 'cargo': 'Ger Tecnologia Operativa', 'email': 'cassio.bazana@energisa.com.br'},
    ]
    
    y = 60
    for membro in equipe:
        pdf.set_fill_color(249, 250, 251)
        pdf.set_draw_color(2, 138, 159)
        pdf.rect(25, y, 160, 25, 'DF')
        
        pdf.set_xy(30, y + 3)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 89, 115)
        pdf.cell(0, 6, membro['nome'], 0, 1)
        
        pdf.set_x(30)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"{membro['cargo']} | {membro['email']}", 0, 1)
        
        y += 30
    
    # Rodapé
    pdf.set_y(270)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Energisa - Comissionamento SCADA | {data_hora.strftime("%d/%m/%Y %H:%M")} | Pagina {pdf.page_no()}', 0, 0, 'C')
    
    # Salvar
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name


def adicionar_botao_pdf_empresa(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """Botão para gerar relatório executivo"""
    if st.button(f"📊 Relatório {empresa}", use_container_width=True, key=f"btn_pdf_{empresa}"):
        if df_filtrado.empty:
            st.warning("Sem dados.")
            return
        
        with st.spinner(f"Gerando relatório executivo da {empresa}..."):
            try:
                pdf_path = gerar_relatorio_executivo(df_filtrado, empresa, mes_selecionado, ano_selecionado)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                nome = f"Relatorio_Executivo_{empresa}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                st.success(f"✅ Relatório executivo da {empresa} pronto!")
                st.download_button("📥 Baixar PDF", pdf_bytes, nome, "application/pdf", use_container_width=True)
                
                os.unlink(pdf_path)
            except Exception as e:
                st.error(f"Erro: {str(e)}")
