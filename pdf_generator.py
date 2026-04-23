# pdf_generator.py - VERSÃO EXECUTIVA
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

# ============================================
# FUNÇÕES DE CÁLCULO
# ============================================
def calcular_desenvolvidos_acumulado(df):
    status_incluidos = ['Desenvolvido', 'Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_comissionados_acumulado(df):
    status_incluidos = ['Comissionado', 'Validado', 'Necessário Revisão']
    return len(df[df['Status'].isin(status_incluidos)])

def calcular_validados_acumulado(df):
    return len(df[df['Status'] == 'Validado'])

def calcular_aguardando_comissionamento(df):
    return len(df[df['Status'] == 'Desenvolvido'])

def calcular_aguardando_validacao(df):
    return len(df[df['Status'] == 'Comissionado'])

def calcular_em_revisao(df):
    return len(df[df['Status'] == 'Necessário Revisão'])

def get_horario_brasilia():
    utc_now = datetime.now(timezone.utc)
    return utc_now - timedelta(hours=3)

def filtrar_dados_acumulados_ate_periodo(df, mes_selecionado=None, ano_selecionado=None):
    df_result = df.copy()
    if (not mes_selecionado or mes_selecionado == "Todos os Meses") and \
       (not ano_selecionado or ano_selecionado == "Todos os Anos"):
        return df_result
    
    meses_map = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_result.columns:
            if mes_selecionado and mes_selecionado != "Todos os Meses":
                mes_num = meses_map.get(mes_selecionado, 0)
                if mes_num > 0 and 'Mes' in df_result.columns:
                    df_result = df_result[
                        (df_result['Ano'] < ano_selecionado) |
                        ((df_result['Ano'] == ano_selecionado) & (df_result['Mes'] <= mes_num))
                    ]
                else:
                    df_result = df_result[df_result['Ano'] <= ano_selecionado]
            else:
                df_result = df_result[df_result['Ano'] <= ano_selecionado]
    return df_result

# ============================================
# GRÁFICOS MELHORADOS
# ============================================
def gerar_grafico_barras_vertical(total, comissionados_acum, validados_acum, revisao, periodo_texto=""):
    """Gráfico de barras vertical melhorado"""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    categorias = ['Comissionados', 'Validados', 'Em Revisão']
    valores = [comissionados_acum, validados_acum, revisao]
    cores = ['#028a9f', '#2E7D32', '#F57C00']
    
    bars = ax.bar(categorias, valores, color=cores, width=0.5, edgecolor='white', linewidth=2)
    
    # Adicionar valores e %
    for bar, val in zip(bars, valores):
        height = bar.get_height()
        pct = (val / total * 100) if total > 0 else 0
        ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.03,
                f'{val}\n({pct:.0f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='#1f2937')
    
    ax.set_ylabel('Quantidade', fontsize=11, color='#374151')
    ax.set_title(f'Total: {total} equipamentos desenvolvidos\n{periodo_texto}', 
                 fontsize=13, fontweight='bold', color='#1f2937', pad=15)
    ax.set_ylim(0, max(valores) * 1.25 if max(valores) > 0 else 10)
    ax.grid(axis='y', alpha=0.2, linestyle='-', color='#d1d5db')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig

def gerar_grafico_motivos_donut(motivos_count, total_motivos):
    """Gráfico donut profissional para motivos"""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    
    cores = ['#C62828', '#D32F2F', '#E53935', '#F57C00', '#FF8F00',
             '#6A1B9A', '#1565C0', '#00838F', '#00695C', '#2E7D32']
    
    valores = motivos_count.values.tolist()
    
    # Criar labels curtas para o gráfico
    labels_curtas = []
    for nome in motivos_count.index:
        if len(nome) > 25:
            nome = nome[:22] + '...'
        labels_curtas.append(nome)
    
    # Donut
    wedges, texts = ax.pie(
        valores,
        labels=labels_curtas,
        colors=cores[:len(valores)],
        startangle=140,
        labeldistance=1.12,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2.5),
        textprops={'fontsize': 8, 'fontweight': 'bold', 'color': '#374151'}
    )
    
    # Círculo central
    centre_circle = plt.Circle((0, 0), 0.22, fc='white', linewidth=3, edgecolor='#005973')
    ax.add_artist(centre_circle)
    
    ax.text(0, 0.06, f'{total_motivos}', ha='center', va='center',
            fontsize=30, fontweight='bold', color='#005973')
    ax.text(0, -0.12, 'equipamentos', ha='center', va='center',
            fontsize=10, color='#6b7280')
    
    ax.set_title('Distribuição dos Motivos de Revisão',
                 fontsize=14, fontweight='bold', color='#1f2937', pad=25)
    
    plt.tight_layout(pad=2)
    return fig

def gerar_grafico_motivos_barras_horizontais(motivos_count, total_motivos):
    """Gráfico de barras horizontais para motivos"""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    motivos_sorted = motivos_count.sort_values(ascending=True)
    
    cores = ['#C62828', '#D32F2F', '#E53935', '#F57C00', '#FF8F00',
             '#6A1B9A', '#1565C0', '#00838F', '#00695C', '#2E7D32']
    
    bars = ax.barh(range(len(motivos_sorted)), motivos_sorted.values,
                    color=cores[:len(motivos_sorted)], height=0.6,
                    edgecolor='white', linewidth=1.5)
    
    for i, (motivo, qtd) in enumerate(zip(motivos_sorted.index, motivos_sorted.values)):
        pct = (qtd / total_motivos * 100) if total_motivos > 0 else 0
        ax.text(qtd + max(motivos_sorted.values)*0.02, i,
                f'{qtd} ({pct:.1f}%)',
                va='center', fontsize=9, fontweight='bold', color='#1f2937')
    
    # Encurtar labels
    labels_y = [m[:35] + '...' if len(m) > 35 else m for m in motivos_sorted.index]
    ax.set_yticks(range(len(motivos_sorted)))
    ax.set_yticklabels(labels_y, fontsize=8)
    ax.set_xlabel('Quantidade', fontsize=10, color='#6b7280')
    ax.set_title(f'Motivos de Revisão - Total: {total_motivos} equipamentos',
                 fontsize=13, fontweight='bold', color='#1f2937', pad=15)
    ax.set_xlim(0, max(motivos_sorted.values) * 1.3)
    ax.grid(axis='x', alpha=0.2, linestyle='-', color='#d1d5db')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig

# ============================================
# FUNÇÃO PRINCIPAL
# ============================================
def gerar_relatorio_empresa(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """Gera relatório executivo profissional"""
    
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para {empresa}")
    
    df_empresa_acumulado = filtrar_dados_acumulados_ate_periodo(df_empresa, mes_selecionado, ano_selecionado)
    
    df_empresa_filtrado = df_empresa.copy()
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        if 'Mes_Nome' in df_empresa_filtrado.columns:
            df_empresa_filtrado = df_empresa_filtrado[df_empresa_filtrado['Mes_Nome'] == mes_selecionado]
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_empresa_filtrado.columns:
            df_empresa_filtrado = df_empresa_filtrado[df_empresa_filtrado['Ano'] == ano_selecionado]
    
    if df_empresa_filtrado.empty:
        raise ValueError(f"Sem dados para o período")
    
    # Métricas
    dev = calcular_desenvolvidos_acumulado(df_empresa_filtrado)
    com = calcular_comissionados_acumulado(df_empresa_filtrado)
    val = calcular_validados_acumulado(df_empresa_filtrado)
    ag_com = calcular_aguardando_comissionamento(df_empresa_filtrado)
    ag_val = calcular_aguardando_validacao(df_empresa_filtrado)
    rev = calcular_em_revisao(df_empresa_filtrado)
    
    total = len(df_empresa_filtrado)
    
    pct_com = (com / dev * 100) if dev > 0 else 0
    pct_val = (val / dev * 100) if dev > 0 else 0
    pct_rev = (rev / dev * 100) if dev > 0 else 0
    
    # Acumulado total
    dev_t = calcular_desenvolvidos_acumulado(df_empresa_acumulado)
    com_t = calcular_comissionados_acumulado(df_empresa_acumulado)
    val_t = calcular_validados_acumulado(df_empresa_acumulado)
    rev_t = calcular_em_revisao(df_empresa_acumulado)
    
    # Motivos
    tem_motivos = False
    motivos_count = None
    total_mot = 0
    if 'Motivo_Revisao' in df_empresa_filtrado.columns:
        df_mot = df_empresa_filtrado[df_empresa_filtrado['Motivo_Revisao'].notna() & 
                                      (df_empresa_filtrado['Motivo_Revisao'] != '') &
                                      (df_empresa_filtrado['Motivo_Revisao'] != 'N/A')]
        if not df_mot.empty:
            tem_motivos = True
            motivos_count = df_mot['Motivo_Revisao'].value_counts()
            total_mot = len(df_mot)
    
    # Período
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        periodo = mes_selecionado
        if ano_selecionado and ano_selecionado != "Todos os Anos":
            periodo += f"/{ano_selecionado}"
    elif ano_selecionado and ano_selecionado != "Todos os Anos":
        periodo = str(ano_selecionado)
    else:
        periodo = "Todos os períodos"
    
    periodo_acum = f"Acumulado até {periodo}" if periodo != "Todos os períodos" else "Acumulado Geral"
    
    data_hora = get_horario_brasilia()
    
    # ============================================
    # CRIAR PDF
    # ============================================
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ============================================
    # CAPA EXECUTIVA
    # ============================================
    pdf.add_page()
    
    # Fundo azul escuro
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Faixa central mais clara
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(0, 75, 210, 130, 'F')
    
    # Linha decorativa superior
    pdf.set_draw_color(4, 216, 215)
    pdf.set_line_width(1.5)
    pdf.line(30, 85, 180, 85)
    
    # Título
    pdf.set_y(95)
    pdf.set_font('Arial', 'B', 26)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'RELATÓRIO EXECUTIVO', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 8, 'COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    # Linha decorativa inferior
    pdf.set_y(185)
    pdf.set_draw_color(4, 216, 215)
    pdf.line(30, 185, 180, 185)
    
    # Unidade
    pdf.set_y(200)
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(4, 216, 215)
    pdf.cell(0, 10, f'UNIDADE {empresa}', 0, 1, 'C')
    
    # Período
    pdf.set_y(218)
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, f'Período: {periodo}', 0, 1, 'C')
    
    # Data
    pdf.set_y(265)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 5, f'Emitido em: {data_hora.strftime("%d/%m/%Y as %H:%M")} (Horario de Brasilia)', 0, 1, 'C')
    pdf.cell(0, 5, 'CONFIDENCIAL - USO INTERNO ENERGISA', 0, 1, 'C')
    
    # ============================================
    # PÁGINA 2 - KPIs + PROGRESSO
    # ============================================
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(8)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, f'DASHBOARD EXECUTIVO - UNIDADE {empresa}', 0, 1, 'C')
    
    # 4 Cards KPIs
    y_cards = 38
    card_w = 42
    card_h = 40
    gap = 5
    x_start = 14
    
    cards = [
        ('DESENVOLVIDOS', dev, ag_com, 'Aguardando', CORES['card1'] if 'CORES' in dir() else '#2E7D32'),
        ('COMISSIONADOS', com, ag_val, 'Aguardando', CORES['card2'] if 'CORES' in dir() else '#028a9f'),
        ('VALIDADO', val, 0, 'Concluido', CORES['card3'] if 'CORES' in dir() else '#005973'),
        ('EM REVISÃO', rev, 0, 'Gargalo', CORES['card4'] if 'CORES' in dir() else '#F57C00'),
    ]
    
    cores_cards = ['#2E7D32', '#028a9f', '#005973', '#F57C00']
    
    for i, (titulo, valor, extra, extra_label, _) in enumerate(cards):
        x = x_start + i * (card_w + gap)
        
        # Fundo do card
        pdf.set_fill_color(249, 250, 251)
        pdf.set_draw_color(cores_cards[i])
        pdf.set_line_width(1.5)
        pdf.rect(x, y_cards, card_w, card_h, 'DF')
        
        # Título
        pdf.set_xy(x + 2, y_cards + 4)
        pdf.set_font('Arial', 'B', 7)
        pdf.set_text_color(cores_cards[i])
        pdf.cell(card_w - 4, 5, titulo, 0, 1, 'C')
        
        # Valor principal
        pdf.set_xy(x + 2, y_cards + 14)
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(card_w - 4, 10, str(valor), 0, 1, 'C')
        
        # Extra
        if extra > 0 and extra_label:
            pdf.set_xy(x + 2, y_cards + 29)
            pdf.set_font('Arial', '', 7)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(card_w - 4, 5, f'{extra_label}: {extra}', 0, 1, 'C')
    
    # Barra de progresso
    pdf.set_y(90)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, 'PROGRESSO DO FLUXO', 0, 1)
    
    bar_x, bar_y = 15, 102
    bar_w = 180
    bar_h = 12
    
    pdf.set_fill_color(229, 231, 235)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, 'F')
    
    if dev > 0:
        val_w = bar_w * (pct_val / 100)
        com_w = bar_w * (pct_com / 100)
        
        pdf.set_fill_color(46, 125, 50)
        if val_w > 0:
            pdf.rect(bar_x, bar_y, val_w, bar_h, 'F')
        
        pdf.set_fill_color(2, 138, 159)
        if com_w - val_w > 0:
            pdf.rect(bar_x + val_w, bar_y, com_w - val_w, bar_h, 'F')
        
        pdf.set_fill_color(245, 124, 0)
        rev_w = bar_w * (pct_rev / 100)
        if rev_w > 0:
            pdf.rect(bar_x + com_w, bar_y, rev_w, bar_h, 'F')
    
    # Labels da barra
    pdf.set_y(118)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 5, f'Validados: {val} ({pct_val:.0f}%)', 0, 0, 'L')
    pdf.cell(60, 5, f'Comissionados: {com} ({pct_com:.0f}%)', 0, 0, 'C')
    pdf.cell(60, 5, f'Em Revisão: {rev} ({pct_rev:.0f}%)', 0, 1, 'R')
    
    # Taxa de validação
    taxa_val = (val / com * 100) if com > 0 else 0
    pdf.set_y(128)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f'Taxa de Validação sobre Comissionados: {val}/{com} = {taxa_val:.0f}%', 0, 1)
    
    # Distribuição por Status
    pdf.set_y(140)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, 'DISTRIBUIÇÃO POR STATUS', 0, 1)
    pdf.set_draw_color(4, 216, 215)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    status_counts = df_empresa_filtrado['Status'].value_counts()
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(55, 65, 81)
    for status, qtd in status_counts.items():
        pct = (qtd / total * 100) if total > 0 else 0
        pdf.cell(8, 5, '', 0, 0)
        pdf.cell(80, 5, status, 0, 0)
        pdf.cell(30, 5, str(qtd), 0, 0)
        pdf.cell(0, 5, f'({pct:.1f}%)', 0, 1)
    
    # Tipos de Equipamento
    if 'Tipo' in df_empresa_filtrado.columns:
        pdf.set_y(pdf.get_y() + 5)
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 89, 115)
        pdf.cell(0, 8, 'TIPOS DE EQUIPAMENTO', 0, 1)
        pdf.set_draw_color(4, 216, 215)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)
        
        tipo_counts = df_empresa_filtrado['Tipo'].value_counts().head(8)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(55, 65, 81)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.cell(8, 5, '', 0, 0)
            pdf.cell(80, 5, tipo, 0, 0)
            pdf.cell(30, 5, str(qtd), 0, 0)
            pdf.cell(0, 5, f'({pct:.0f}%)', 0, 1)
    
    # ============================================
    # PÁGINA 3 - MOTIVOS DE REVISÃO
    # ============================================
    if tem_motivos:
        pdf.add_page()
        
        pdf.set_fill_color(0, 89, 115)
        pdf.rect(0, 0, 210, 30, 'F')
        pdf.set_y(8)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'ANÁLISE DE MOTIVOS DE REVISÃO', 0, 1, 'C')
        
        # Tabela
        pdf.set_y(40)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(0, 89, 115)
        pdf.cell(0, 6, f'Total: {total_mot} equipamentos com motivo registrado', 0, 1)
        pdf.ln(3)
        
        # Cabeçalho tabela
        pdf.set_fill_color(0, 89, 115)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(8, 7, '#', 1, 0, 'C', 1)
        pdf.cell(95, 7, 'Motivo', 1, 0, 'C', 1)
        pdf.cell(30, 7, 'Qtd', 1, 0, 'C', 1)
        pdf.cell(30, 7, '%', 1, 1, 'C', 1)
        
        pdf.set_font('Arial', '', 8)
        for i, (motivo, qtd) in enumerate(motivos_count.items(), 1):
            pct = (qtd / total_mot * 100) if total_mot > 0 else 0
            
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
            
            pdf.cell(8, 6, str(i), 1, 0, 'C', 1)
            pdf.cell(95, 6, motivo[:55], 1, 0, 'L', 1)
            pdf.cell(30, 6, str(qtd), 1, 0, 'C', 1)
            pdf.cell(30, 6, f'{pct:.1f}%', 1, 1, 'C', 1)
        
        pdf.set_text_color(0, 0, 0)
        
        # Gráfico em nova página
        pdf.add_page()
        
        pdf.set_fill_color(0, 89, 115)
        pdf.rect(0, 0, 210, 30, 'F')
        pdf.set_y(8)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'DISTRIBUIÇÃO DOS MOTIVOS DE REVISÃO', 0, 1, 'C')
        
        # Gerar gráfico donut
        fig_motivos = gerar_grafico_motivos_donut(motivos_count, total_mot)
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig_motivos.savefig(temp_img.name, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig_motivos)
        
        pdf.image(temp_img.name, x=10, y=38, w=190)
        os.unlink(temp_img.name)
    
    # ============================================
    # PÁGINA - ACUMULADO
    # ============================================
    pdf.add_page()
    
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(8)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, f'ACUMULADO: {periodo_acum.upper()}', 0, 1, 'C')
    
    fig = gerar_grafico_barras_vertical(dev_t, com_t, val_t, rev_t, periodo_acum)
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    fig.savefig(temp_img.name, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    pdf.image(temp_img.name, x=20, y=40, w=170)
    os.unlink(temp_img.name)
    
    pdf.set_y(180)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Resumo {periodo_acum}:', 0, 1)
    pdf.set_font('Arial', '', 9)
    pct_com_t = (com_t / dev_t * 100) if dev_t > 0 else 0
    pct_val_t = (val_t / dev_t * 100) if dev_t > 0 else 0
    pct_rev_t = (rev_t / dev_t * 100) if dev_t > 0 else 0
    taxa_val_t = (val_t / com_t * 100) if com_t > 0 else 0
    
    pdf.cell(0, 5, f'Desenvolvidos: {dev_t}', 0, 1)
    pdf.cell(0, 5, f'Comissionados: {com_t} ({pct_com_t:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Validados: {val_t} ({pct_val_t:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Em Revisão: {rev_t} ({pct_rev_t:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Taxa de Validação: {taxa_val_t:.1f}%', 0, 1)
    
    # ============================================
    # PÁGINA - PERFORMANCE
    # ============================================
    pdf.add_page()
    
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(8)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'PERFORMANCE POR RESPONSÁVEL', 0, 1, 'C')
    
    y_offset = 40
    
    col_resp = 'Resp_Com'
    if col_resp in df_empresa_filtrado.columns:
        df_resp = df_empresa_filtrado[df_empresa_filtrado[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 9)
            pdf.set_text_color(0, 89, 115)
            pdf.cell(0, 6, 'Comissionados por Responsável:', 0, 1)
            y_offset += 8
            
            # Cabeçalho
            pdf.set_fill_color(0, 89, 115)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_y(y_offset)
            pdf.cell(70, 7, 'Responsável', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Total', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Validados', 1, 0, 'C', 1)
            pdf.cell(45, 7, 'Taxa Sucesso', 1, 1, 'C', 1)
            y_offset += 7
            
            top_resp = df_resp[col_resp].value_counts().head(8).index.tolist()
            pdf.set_font('Arial', '', 8)
            
            for resp in top_resp:
                df_item = df_resp[df_resp[col_resp] == resp]
                total_r = len(df_item)
                val_r = len(df_item[df_item['Status'] == 'Validado'])
                taxa_r = (val_r / total_r * 100) if total_r > 0 else 0
                
                pdf.set_fill_color(249, 250, 251)
                pdf.set_text_color(55, 65, 81)
                pdf.set_y(y_offset)
                pdf.cell(70, 6, str(resp)[:30], 1, 0, 'L', 1)
                pdf.cell(35, 6, str(total_r), 1, 0, 'C', 1)
                pdf.cell(35, 6, str(val_r), 1, 0, 'C', 1)
                
                if taxa_r >= 80:
                    pdf.set_text_color(46, 125, 50)
                elif taxa_r >= 50:
                    pdf.set_text_color(245, 124, 0)
                else:
                    pdf.set_text_color(198, 40, 40)
                
                pdf.cell(45, 6, f'{taxa_r:.0f}%', 1, 1, 'C', 1)
                y_offset += 6
    
    # ============================================
    # PÁGINA - EQUIPE
    # ============================================
    pdf.add_page()
    
    pdf.set_fill_color(0, 89, 115)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_y(8)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, 'EQUIPE RESPONSÁVEL', 0, 1, 'C')
    
    equipe = [
        ('Kewin Marcel Ramirez Ferreira', 'SRE - Elaboração', 'kewin.ferreira@energisa.com.br'),
        ('Caio Alexandre da Silva Medeiros', 'Gestão', 'caio.medeiros@energisa.com.br'),
        ('Ramiza Alves Irineu Seabra', 'BP', 'ramiza.irineu@energisa.com.br'),
        ('Bruna Moura Maciel', 'BP', 'bruna.maciel@energisa.com.br'),
        ('Mauricio Dias Avelino', 'Coord Tech Proj Sist Operativos', 'mauricio.avelino@energisa.com.br'),
        ('Cassio Fernando Bazana Nonenmacher', 'Ger Tecnologia Operativa', 'cassio.bazana@energisa.com.br'),
        ('Savio Ricardo Muniz Aires da Costa', 'Ger Automação Telecom', 'savio.ricardo@energisa.com.br'),
    ]
    
    y = 45
    for nome, cargo, email in equipe:
        pdf.set_fill_color(249, 250, 251)
        pdf.set_draw_color(2, 138, 159)
        pdf.rect(20, y, 170, 22, 'DF')
        
        pdf.set_xy(25, y + 3)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 89, 115)
        pdf.cell(0, 6, nome, 0, 1)
        
        pdf.set_x(25)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f'{cargo} | {email}', 0, 1)
        
        y += 28
    
    # Rodapé
    pdf.set_y(-20)
    pdf.set_font('Arial', 'I', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Energisa - Comissionamento SCADA | {data_hora.strftime("%d/%m/%Y %H:%M")} | Pagina {pdf.page_no()}/{{nb}}', 0, 0, 'C')
    
    # Salvar
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name


def adicionar_botao_pdf_empresa(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """Botão Streamlit"""
    if st.button(f"📊 Gerar Relatório {empresa}", use_container_width=True, key=f"btn_pdf_{empresa}"):
        if df_filtrado.empty:
            st.warning("Sem dados.")
            return
        
        with st.spinner(f"Gerando relatório executivo da {empresa}..."):
            try:
                pdf_path = gerar_relatorio_empresa(df_filtrado, empresa, mes_selecionado, ano_selecionado)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                nome = f"Relatorio_{empresa}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                st.success(f"✅ Relatório da {empresa} gerado com sucesso!")
                st.download_button("📥 Baixar PDF", pdf_bytes, nome, "application/pdf", use_container_width=True)
                
                os.unlink(pdf_path)
            except Exception as e:
                st.error(f"Erro: {str(e)}")
