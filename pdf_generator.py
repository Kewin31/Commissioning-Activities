# pdf_generator.py - Versão com Acumulado até o Mês Selecionado
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
    """Calcula quantos estão aguardando comissionamento"""
    return len(df[df['Status'] == 'Desenvolvido'])

def calcular_aguardando_validacao(df):
    """Calcula quantos estão aguardando validação"""
    return len(df[df['Status'] == 'Comissionado'])

def calcular_em_revisao(df):
    """Calcula quantos estão em revisão"""
    return len(df[df['Status'] == 'Necessário Revisão'])

def get_horario_brasilia():
    """Retorna o horário atual de Brasília (UTC-3)"""
    utc_now = datetime.now(timezone.utc)
    brasilia_time = utc_now - timedelta(hours=3)
    return brasilia_time

def filtrar_dados_acumulados_ate_periodo(df, mes_selecionado=None, ano_selecionado=None):
    """
    Filtra dados acumulados até o período selecionado
    Se nenhum filtro for aplicado, retorna todos os dados
    """
    df_result = df.copy()
    
    # Se não há filtro de mês/ano, retorna todos os dados
    if (not mes_selecionado or mes_selecionado == "Todos os Meses") and \
       (not ano_selecionado or ano_selecionado == "Todos os Anos"):
        return df_result
    
    # Mapeamento de meses para números
    meses_map = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    
    # Se tem filtro de ano
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_result.columns:
            # Se tem filtro de mês também
            if mes_selecionado and mes_selecionado != "Todos os Meses":
                mes_num = meses_map.get(mes_selecionado, 0)
                if mes_num > 0 and 'Mes' in df_result.columns:
                    # Filtra até o mês/ano selecionado
                    df_result = df_result[
                        (df_result['Ano'] < ano_selecionado) |
                        ((df_result['Ano'] == ano_selecionado) & (df_result['Mes'] <= mes_num))
                    ]
                else:
                    # Filtra até o ano selecionado
                    df_result = df_result[df_result['Ano'] <= ano_selecionado]
            else:
                # Apenas filtro de ano - pega até o ano selecionado
                df_result = df_result[df_result['Ano'] <= ano_selecionado]
    else:
        # Apenas filtro de mês (sem ano específico) - não faz sentido acumular
        # Neste caso, mostra todos os dados
        pass
    
    return df_result

def gerar_grafico_barras_vertical(total, comissionados_acum, validados_acum, revisao, periodo_texto=""):
    """Gera gráfico de barras verticais para o acumulado"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    categorias = ['Comissionados\n(Acumulado)', 'Validados\n(Acumulado)', 'Em Revisão']
    valores = [comissionados_acum, validados_acum, revisao]
    cores = ['#028a9f', '#2E7D32', '#F57C00']
    
    bars = ax.bar(categorias, valores, color=cores, width=0.6, edgecolor='white', linewidth=1.5)
    
    for bar, val in zip(bars, valores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.02,
                f'{val}\n({val/total*100:.0f}%)' if total > 0 else '0',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_ylabel('Quantidade', fontsize=10)
    titulo = f'Total de Equipamentos Desenvolvidos: {total}'
    if periodo_texto:
        titulo += f'\n{periodo_texto}'
    ax.set_title(titulo, fontsize=11, fontweight='bold', pad=15)
    ax.set_ylim(0, max(valores) * 1.2 if max(valores) > 0 else 10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return fig

def gerar_relatorio_empresa(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """
    Gera relatório PDF executivo para uma empresa específica
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # ============================================
    # DADOS ACUMULADOS ATÉ O PERÍODO SELECIONADO
    # ============================================
    # Usa a função que filtra dados até o período selecionado
    df_empresa_acumulado = filtrar_dados_acumulados_ate_periodo(df_empresa, mes_selecionado, ano_selecionado)
    
    # ============================================
    # DADOS FILTRADOS (APENAS O PERÍODO SELECIONADO)
    # ============================================
    df_empresa_filtrado = df_empresa.copy()
    
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        if 'Mes_Nome' in df_empresa_filtrado.columns:
            df_empresa_filtrado = df_empresa_filtrado[df_empresa_filtrado['Mes_Nome'] == mes_selecionado]
    
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_empresa_filtrado.columns:
            df_empresa_filtrado = df_empresa_filtrado[df_empresa_filtrado['Ano'] == ano_selecionado]
    
    if df_empresa_filtrado.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa} com os filtros selecionados.")
    
    # ============================================
    # MÉTRICAS ACUMULADAS (DADOS FILTRADOS - PERÍODO SELECIONADO)
    # ============================================
    desenvolvidos_acum_filtrado = calcular_desenvolvidos_acumulado(df_empresa_filtrado)
    comissionados_acum_filtrado = calcular_comissionados_acumulado(df_empresa_filtrado)
    validados_acum_filtrado = calcular_validados_acumulado(df_empresa_filtrado)
    aguardando_comiss_filtrado = calcular_aguardando_comissionamento(df_empresa_filtrado)
    aguardando_valid_filtrado = calcular_aguardando_validacao(df_empresa_filtrado)
    revisao_filtrado = calcular_em_revisao(df_empresa_filtrado)
    
    total_filtrado = len(df_empresa_filtrado)
    
    # Percentuais sobre o total de DESENVOLVIDOS
    pct_comiss_filtrado = (comissionados_acum_filtrado / desenvolvidos_acum_filtrado * 100) if desenvolvidos_acum_filtrado > 0 else 0
    pct_valid_filtrado = (validados_acum_filtrado / desenvolvidos_acum_filtrado * 100) if desenvolvidos_acum_filtrado > 0 else 0
    pct_revisao_filtrado = (revisao_filtrado / desenvolvidos_acum_filtrado * 100) if desenvolvidos_acum_filtrado > 0 else 0
    pct_aguardando_comiss_filtrado = (aguardando_comiss_filtrado / desenvolvidos_acum_filtrado * 100) if desenvolvidos_acum_filtrado > 0 else 0
    
    # ============================================
    # MÉTRICAS ACUMULADAS (ATÉ O PERÍODO SELECIONADO)
    # ============================================
    desenvolvidos_acum_total = calcular_desenvolvidos_acumulado(df_empresa_acumulado)
    comissionados_acum_total = calcular_comissionados_acumulado(df_empresa_acumulado)
    validados_acum_total = calcular_validados_acumulado(df_empresa_acumulado)
    revisao_total = calcular_em_revisao(df_empresa_acumulado)
    
    pct_comiss_total = (comissionados_acum_total / desenvolvidos_acum_total * 100) if desenvolvidos_acum_total > 0 else 0
    pct_valid_total = (validados_acum_total / desenvolvidos_acum_total * 100) if desenvolvidos_acum_total > 0 else 0
    pct_revisao_total = (revisao_total / desenvolvidos_acum_total * 100) if desenvolvidos_acum_total > 0 else 0
    
    # Texto do período para o gráfico acumulado
    periodo_acumulado_texto = ""
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        periodo_acumulado_texto = f"Acumulado até {mes_selecionado}"
        if ano_selecionado and ano_selecionado != "Todos os Anos":
            periodo_acumulado_texto += f"/{ano_selecionado}"
    elif ano_selecionado and ano_selecionado != "Todos os Anos":
        periodo_acumulado_texto = f"Acumulado até {ano_selecionado}"
    else:
        periodo_acumulado_texto = "Acumulado Geral (Todos os períodos)"
    
    # Criar PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # ============================================
    # CABEÇALHO
    # ============================================
    # Logo
    try:
        for logo in ["Logo_Energisa.png", "logo_energisa.png", "energisa.png"]:
            if os.path.exists(logo):
                pdf.image(logo, x=10, y=8, w=25)
                break
    except:
        pass
    
    # Título
    pdf.set_y(15)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, 'RELATÓRIO DE COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    # Subtítulo
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 6, f'UNIDADE {empresa}', 0, 1, 'C')
    
    # Período (se houver filtro)
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        periodo_texto = f'Período: {mes_selecionado}'
        if ano_selecionado and ano_selecionado != "Todos os Anos":
            periodo_texto += f'/{ano_selecionado}'
        pdf.cell(0, 5, periodo_texto, 0, 1, 'C')
    
    # Linha
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, 45, 200, 45)
    
    # Data (horário de Brasília)
    brasilia_time = get_horario_brasilia()
    pdf.set_y(48)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'Emissão: {brasilia_time.strftime("%d/%m/%Y - %H:%M")} (Horário de Brasília)', 0, 1, 'R')
    
    # ============================================
    # TEXTO EXPLICATIVO
    # ============================================
    pdf.set_y(58)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, 'Este relatório tem como objetivo apresentar o status atual do processo de comissionamentos da unidade, fornecendo uma visão consolidada do progresso, identificando gargalos e apoiando a tomada de decisão para otimização dos recursos e prazos.')
    pdf.ln(3)
    
    # ============================================
    # PÁGINA 1 - PANORAMA, PROGRESSO, DISTRIBUIÇÃO, TIPOS
    # ============================================
    
    # 1. PANORAMA GERAL - 4 CARDS COM MÉTRICAS ACUMULADAS
    y_pos = pdf.get_y() + 5
    
    pdf.set_y(y_pos)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '1. PANORAMA GERAL (Acumulado no Período)', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # Posição inicial dos cards
    card_y = pdf.get_y() + 5
    
    # CARD 1: DESENVOLVIDOS (ACUMULADO)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, card_y, 45, 52, 'F')
    pdf.set_xy(12, card_y + 4)
    pdf.set_font('Arial', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'DESENVOLVIDOS', 0, 1)
    pdf.set_xy(12, card_y + 12)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, str(desenvolvidos_acum_filtrado), 0, 1)
    pdf.set_xy(12, card_y + 28)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f'Aguardando: {aguardando_comiss_filtrado}', 0, 1)
    pdf.set_xy(12, card_y + 35)
    pdf.set_font('Arial', 'I', 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 3, f'= Desenv+Comiss+Valid+Rev', 0, 1)
    pdf.set_xy(12, card_y + 40)
    pdf.cell(0, 3, f'({pct_aguardando_comiss_filtrado:.0f}% aguardando)', 0, 1)
    
    # CARD 2: COMISSIONADOS (ACUMULADO)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(60, card_y, 45, 52, 'F')
    pdf.set_xy(62, card_y + 4)
    pdf.set_font('Arial', 'B', 7)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 4, 'COMISSIONADOS', 0, 1)
    pdf.set_xy(62, card_y + 12)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 7, str(comissionados_acum_filtrado), 0, 1)
    pdf.set_xy(62, card_y + 28)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 4, f'Aguardando: {aguardando_valid_filtrado}', 0, 1)
    pdf.set_xy(62, card_y + 35)
    pdf.set_font('Arial', 'I', 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 3, f'= Comiss+Valid+Rev', 0, 1)
    pdf.set_xy(62, card_y + 40)
    pdf.cell(0, 3, f'({pct_comiss_filtrado:.0f}% dos desenvolvidos)', 0, 1)
    
    # CARD 3: VALIDADOS (ACUMULADO)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(110, card_y, 45, 52, 'F')
    pdf.set_xy(112, card_y + 4)
    pdf.set_font('Arial', 'B', 7)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 4, 'VALIDADOS', 0, 1)
    pdf.set_xy(112, card_y + 12)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 7, str(validados_acum_filtrado), 0, 1)
    pdf.set_xy(112, card_y + 28)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 4, 'Concluídos', 0, 1)
    pdf.set_xy(112, card_y + 35)
    pdf.set_font('Arial', 'I', 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 3, f'= Validados', 0, 1)
    pdf.set_xy(112, card_y + 40)
    pdf.cell(0, 3, f'({pct_valid_filtrado:.0f}% dos desenvolvidos)', 0, 1)
    
    # CARD 4: EM REVISÃO
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(160, card_y, 40, 52, 'F')
    pdf.set_xy(162, card_y + 4)
    pdf.set_font('Arial', 'B', 7)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 4, 'EM REVISÃO', 0, 1)
    pdf.set_xy(162, card_y + 12)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 7, str(revisao_filtrado), 0, 1)
    pdf.set_xy(162, card_y + 28)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 4, 'Gargalo', 0, 1)
    pdf.set_xy(162, card_y + 35)
    pdf.set_font('Arial', 'I', 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 3, f'= Necessário Revisão', 0, 1)
    pdf.set_xy(162, card_y + 40)
    pdf.cell(0, 3, f'({pct_revisao_filtrado:.0f}% dos desenvolvidos)', 0, 1)
    
    pdf.ln(20)
    
    # ============================================
    # PROGRESSO DO COMISSIONAMENTO (ACUMULADO)
    # ============================================
    bar_y = pdf.get_y() + 2
    
    pdf.set_y(bar_y)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'PROGRESSO DO COMISSIONAMENTO (Acumulado no Período)', 0, 1)
    
    # Barra Comissionados (sobre Desenvolvidos)
    pdf.set_y(bar_y + 7)
    pdf.set_font('Arial', '', 9)
    pdf.cell(55, 6, 'Comissionados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(65, bar_y + 7, 100, 5, 'F')
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(65, bar_y + 7, 100 * (pct_comiss_filtrado / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 5)
    pdf.cell(20, 6, f'{comissionados_acum_filtrado}/{desenvolvidos_acum_filtrado} ({pct_comiss_filtrado:.0f}%)', 0, 1)
    
    # Barra Validados (sobre Desenvolvidos)
    pdf.set_y(bar_y + 14)
    pdf.cell(55, 6, 'Validados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(65, bar_y + 14, 100, 5, 'F')
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(65, bar_y + 14, 100 * (pct_valid_filtrado / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 12)
    pdf.cell(20, 6, f'{validados_acum_filtrado}/{desenvolvidos_acum_filtrado} ({pct_valid_filtrado:.0f}%)', 0, 1)
    
    # Barra Em Revisão (sobre Desenvolvidos)
    pdf.set_y(bar_y + 21)
    pdf.cell(55, 6, 'Em Revisão:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(65, bar_y + 21, 100, 5, 'F')
    pdf.set_fill_color(245, 124, 0)
    pdf.rect(65, bar_y + 21, 100 * (pct_revisao_filtrado / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 19)
    pdf.cell(20, 6, f'{revisao_filtrado}/{desenvolvidos_acum_filtrado} ({pct_revisao_filtrado:.0f}%)', 0, 1)
    
    # Taxa de validação (Validados / Comissionados)
    taxa_valid_comiss = (validados_acum_filtrado / comissionados_acum_filtrado * 100) if comissionados_acum_filtrado > 0 else 0
    pdf.set_y(bar_y + 30)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, f'Taxa de validação sobre comissionados: {validados_acum_filtrado}/{comissionados_acum_filtrado} = {taxa_valid_comiss:.0f}%', 0, 1)
    
    pdf.ln(5)
    
    # ============================================
    # 2. DISTRIBUIÇÃO POR STATUS (Status Atual - Não Acumulado)
    # ============================================
    dist_y = pdf.get_y() + 2
    
    pdf.set_y(dist_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '2. DISTRIBUIÇÃO POR STATUS (Status Atual no Período)', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Arial', '', 10)
    status_counts = df_empresa_filtrado['Status'].value_counts()
    for status, qtd in status_counts.items():
        pct = (qtd / total_filtrado * 100) if total_filtrado > 0 else 0
        pdf.cell(15, 5, '', 0, 0)
        pdf.cell(0, 5, f'{status}: {qtd} ({pct:.1f}%)', 0, 1)
    
    pdf.ln(3)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS
    # ============================================
    tipo_y = pdf.get_y()
    
    pdf.set_y(tipo_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '3. TIPOS DE EQUIPAMENTOS (Período)', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('Arial', '', 10)
    y_offset = pdf.get_y() + 3
    
    if 'Tipo' in df_empresa_filtrado.columns and not df_empresa_filtrado['Tipo'].dropna().empty:
        tipo_counts = df_empresa_filtrado['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total_filtrado * 100) if total_filtrado > 0 else 0
            pdf.set_y(y_offset)
            pdf.cell(15, 5, '', 0, 0)
            pdf.cell(0, 5, f'{tipo}: {qtd} ({pct:.0f}%)', 0, 1)
            y_offset += 5
    else:
        pdf.set_y(y_offset)
        pdf.cell(0, 5, 'Não há dados de tipos de equipamento disponíveis.', 0, 1)
        y_offset += 5
    
    # ============================================
    # PÁGINA 2 - ACUMULADO ATÉ O PERÍODO SELECIONADO
    # ============================================
    pdf.add_page()
    
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, f'4. ACUMULADO {periodo_acumulado_texto.upper()}', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Gerar gráfico de barras com os dados ACUMULADOS ATÉ O PERÍODO
    fig = gerar_grafico_barras_vertical(
        desenvolvidos_acum_total, 
        comissionados_acum_total, 
        validados_acum_total, 
        revisao_total,
        periodo_acumulado_texto
    )
    
    # Salvar gráfico como imagem
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    fig.savefig(temp_img.name, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    # Adicionar imagem ao PDF
    pdf.image(temp_img.name, x=30, w=150)
    os.unlink(temp_img.name)
    
    pdf.ln(20)
    
    # Texto complementar do acumulado
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Resumo {periodo_acumulado_texto}:', 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Total de Equipamentos Desenvolvidos: {desenvolvidos_acum_total}', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Comissionados (Acumulado): {comissionados_acum_total} ({pct_comiss_total:.1f}% dos desenvolvidos)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Validados (Acumulado): {validados_acum_total} ({pct_valid_total:.1f}% dos desenvolvidos)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos em Revisão: {revisao_total} ({pct_revisao_total:.1f}% dos desenvolvidos)', 0, 1)
    
    # Taxa de validação sobre comissionados (total)
    taxa_valid_comiss_total = (validados_acum_total / comissionados_acum_total * 100) if comissionados_acum_total > 0 else 0
    pdf.ln(3)
    pdf.cell(0, 5, f'Taxa de validação sobre comissionados: {taxa_valid_comiss_total:.1f}%', 0, 1)
    
    pdf.ln(10)
    
    # ============================================
    # PÁGINA 3 - PERFORMANCE POR RESPONSÁVEL (DADOS DO PERÍODO)
    # ============================================
    pdf.add_page()
    
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '5. PERFORMANCE POR RESPONSÁVEL (Período)', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    col_resp = 'Resp_Com'
    y_offset = pdf.get_y() + 5
    
    if col_resp in df_empresa_filtrado.columns:
        df_resp = df_empresa_filtrado[df_empresa_filtrado[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Comissionados por Responsável:', 0, 1)
            y_offset += 6
            
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 240)
            pdf.cell(70, 7, 'Responsável', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Comissionados', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Validados', 1, 0, 'C', 1)
            pdf.cell(45, 7, 'Taxa Sucesso', 1, 1, 'C', 1)
            y_offset += 7
            
            pdf.set_font('Arial', '', 8)
            pdf.set_fill_color(255, 255, 255)
            
            top_resp = df_resp[col_resp].value_counts().head(8).index.tolist()
            for resp in top_resp:
                df_item = df_resp[df_resp[col_resp] == resp]
                total_resp = len(df_item)
                validados_resp = len(df_item[df_item['Status'] == 'Validado'])
                taxa = (validados_resp / total_resp * 100) if total_resp > 0 else 0
                
                nome = str(resp)[:30]
                pdf.set_y(y_offset)
                pdf.cell(70, 6, nome, 1, 0, 'L')
                pdf.cell(35, 6, str(total_resp), 1, 0, 'C')
                pdf.cell(35, 6, str(validados_resp), 1, 0, 'C')
                pdf.cell(45, 6, f'{taxa:.0f}%', 1, 1, 'C')
                y_offset += 6
            
            y_offset += 4
            
            # Equipamentos em revisão
            df_revisao = df_empresa_filtrado[df_empresa_filtrado['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_y(y_offset)
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(245, 124, 0)
                pdf.cell(0, 6, 'Equipamentos em Revisão por Responsável:', 0, 1)
                pdf.set_text_color(0, 0, 0)
                y_offset += 6
                
                pdf.set_y(y_offset)
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(255, 220, 200)
                pdf.cell(70, 7, 'Responsável', 1, 0, 'C', 1)
                pdf.cell(35, 7, 'Em Revisão', 1, 0, 'C', 1)
                pdf.cell(80, 7, 'Equipamentos', 1, 1, 'C', 1)
                y_offset += 7
                
                pdf.set_font('Arial', '', 7)
                pdf.set_fill_color(255, 255, 255)
                
                revisao_por_resp = df_revisao[col_resp].value_counts().head(8)
                for resp, qtd in revisao_por_resp.items():
                    equipamentos = df_revisao[df_revisao[col_resp] == resp]['Codigo'].head(3).tolist()
                    equip_str = ', '.join([str(e) for e in equipamentos if pd.notna(e)])
                    if len(equipamentos) > 3:
                        equip_str += '...'
                    
                    nome = str(resp)[:30]
                    pdf.set_y(y_offset)
                    pdf.cell(70, 6, nome, 1, 0, 'L')
                    pdf.cell(35, 6, str(qtd), 1, 0, 'C')
                    pdf.cell(80, 6, equip_str[:50], 1, 1, 'C')
                    y_offset += 6
        else:
            pdf.set_y(y_offset)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, 'Não há dados de responsáveis disponíveis.', 0, 1)
    else:
        pdf.set_y(y_offset)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, 'Coluna de responsáveis não encontrada.', 0, 1)
    
    # ============================================
    # PÁGINA 4 - EQUIPE RESPONSÁVEL (ASSINATURAS)
    # ============================================
    pdf.add_page()
    
    pdf.set_y(30)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '6. EQUIPE RESPONSÁVEL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Documento Elaborado por
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Documento Elaborado por:', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, 'Kewin Marcel Ramirez Ferreira - SRE', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'kewin.ferreira@energisa.com.br', 0, 1, 'L')
    pdf.ln(8)
    
    # Núcleo de Gestão
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Núcleo de Gestão:', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, 'Caio Alexandre da Silva Medeiros - Gestão', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'caio.medeiros@energisa.com.br', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, 'Ramiza Alves Irineu Seabra - BP', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'ramiza.irineu@energisa.com.br', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, 'Bruna Moura Maciel - BP', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'bruna.maciel@energisa.com.br', 0, 1, 'L')
    pdf.ln(8)
    
    # Aprovado por
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Aprovado por:', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, 'Mauricio Dias Avelino - Coord Tech Proj Sist Operativos', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'mauricio.avelino@energisa.com.br', 0, 1, 'L')
    pdf.ln(3)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, 'Cassio Fernando Bazana Nonenmacher - Ger Tecnologia Operativa', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'cassio.bazana@energisa.com.br', 0, 1, 'L')
    pdf.ln(3)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, 'Savio Ricardo Muniz Aires da Costa - Ger Automação Telecom', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'savio.ricardo@energisa.com.br', 0, 1, 'L')
    
    # Rodapé final
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Energisa - Comissionamento SCADA | Unidade {empresa} | Página {pdf.page_no()}', 0, 0, 'C')
    
    # Gerar arquivo
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name


def adicionar_botao_pdf_empresa(df_filtrado, empresa, mes_selecionado=None, ano_selecionado=None):
    """
    Adiciona botão no Streamlit para gerar e baixar o PDF da empresa selecionada
    """
    if st.button(f"📊 Gerar Relatório {empresa}", use_container_width=True, key=f"btn_pdf_{empresa}"):
        if df_filtrado.empty:
            st.warning("Não há dados para gerar o relatório.")
            return
        
        # Filtrar dados da empresa
        df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa]
        
        if df_empresa.empty:
            st.warning(f"Não há dados para a empresa {empresa} com os filtros selecionados.")
            return
        
        with st.spinner(f"Gerando relatório da {empresa}..."):
            try:
                pdf_path = gerar_relatorio_empresa(df_filtrado, empresa, mes_selecionado, ano_selecionado)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                # Criar nome do arquivo com período se houver filtro
                nome_arquivo = f"relatorio_{empresa}"
                if mes_selecionado and mes_selecionado != "Todos os Meses":
                    nome_arquivo += f"_{mes_selecionado}"
                if ano_selecionado and ano_selecionado != "Todos os Anos":
                    nome_arquivo += f"_{ano_selecionado}"
                nome_arquivo += f"_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                st.success(f"Relatório da {empresa} gerado com sucesso!")
                
                st.download_button(
                    label=f"Baixar Relatório {empresa}",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_download_{empresa}"
                )
                
                os.unlink(pdf_path)
                
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {str(e)}")
