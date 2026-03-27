# pdf_generator.py - Versão com Texto Explicativo e Assinaturas
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

def get_horario_brasilia():
    """Retorna o horário atual de Brasília (UTC-3)"""
    utc_now = datetime.now(timezone.utc)
    brasilia_time = utc_now - timedelta(hours=3)
    return brasilia_time

def gerar_grafico_barras_vertical(total, comissionados, validados, revisao):
    """Gera gráfico de barras verticais para o acumulado"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    categorias = ['Comissionados\n+ Aguardando', 'Validados', 'Em Revisão']
    valores = [comissionados, validados, revisao]
    cores = ['#028a9f', '#2E7D32', '#F57C00']
    
    bars = ax.bar(categorias, valores, color=cores, width=0.6, edgecolor='white', linewidth=1.5)
    
    for bar, val in zip(bars, valores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.02,
                f'{val}\n({val/total*100:.0f}%)' if total > 0 else '0',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_ylabel('Quantidade', fontsize=10)
    ax.set_title(f'Total de Equipamentos: {total}', fontsize=11, fontweight='bold', pad=15)
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
    
    # IMPORTANTE: Para o acumulado, vamos usar TODOS os dados da empresa (sem filtro de período)
    df_acumulado = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    # Aplicar filtro de mês e ano apenas para os dados do período (não para o acumulado)
    df_periodo = df_empresa.copy()
    
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        if 'Mes_Nome' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Mes_Nome'] == mes_selecionado]
    
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_periodo.columns:
            df_periodo = df_periodo[df_periodo['Ano'] == ano_selecionado]
    
    if df_periodo.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa} com os filtros selecionados.")
    
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
    # TEXTO EXPLICATIVO (antes do Panorama Geral)
    # ============================================
    pdf.set_y(58)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, 'Este relatório tem como objetivo apresentar o status atual do processo de comissionamentos da unidade, fornecendo uma visão consolidada do progresso, identificando gargalos e apoiando a tomada de decisão para otimização dos recursos e prazos.')
    pdf.ln(3)
    
    # ============================================
    # MÉTRICAS DO PERÍODO
    # ============================================
    total_periodo = len(df_periodo)
    desenvolvidos_periodo = len(df_periodo[df_periodo['Status'] == 'Desenvolvido'])
    comissionados_periodo = len(df_periodo[df_periodo['Status'] == 'Comissionado'])
    validados_periodo = len(df_periodo[df_periodo['Status'] == 'Validado'])
    revisao_periodo = len(df_periodo[df_periodo['Status'] == 'Necessário Revisão'])
    
    pct_comiss_periodo = (comissionados_periodo / total_periodo * 100) if total_periodo > 0 else 0
    pct_valid_periodo = (validados_periodo / total_periodo * 100) if total_periodo > 0 else 0
    pct_revisao_periodo = (revisao_periodo / total_periodo * 100) if total_periodo > 0 else 0
    pct_desenv_periodo = (desenvolvidos_periodo / total_periodo * 100) if total_periodo > 0 else 0
    
    # ============================================
    # MÉTRICAS DO ACUMULADO (TODOS OS DADOS DA UNIDADE)
    # ============================================
    total_acumulado = len(df_acumulado)
    desenvolvidos_acumulado = len(df_acumulado[df_acumulado['Status'] == 'Desenvolvido'])
    comissionados_acumulado = len(df_acumulado[df_acumulado['Status'] == 'Comissionado'])
    validados_acumulado = len(df_acumulado[df_acumulado['Status'] == 'Validado'])
    revisao_acumulado = len(df_acumulado[df_acumulado['Status'] == 'Necessário Revisão'])
    
    pct_comiss_acumulado = (comissionados_acumulado / total_acumulado * 100) if total_acumulado > 0 else 0
    pct_valid_acumulado = (validados_acumulado / total_acumulado * 100) if total_acumulado > 0 else 0
    pct_revisao_acumulado = (revisao_acumulado / total_acumulado * 100) if total_acumulado > 0 else 0
    pct_desenv_acumulado = (desenvolvidos_acumulado / total_acumulado * 100) if total_acumulado > 0 else 0
    
    # ============================================
    # PÁGINA 1 - PANORAMA, PROGRESSO, DISTRIBUIÇÃO, TIPOS
    # ============================================
    
    # 1. PANORAMA GERAL - 4 CARDS EM UMA LINHA
    y_pos = pdf.get_y() + 5
    
    pdf.set_y(y_pos)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '1. PANORAMA GERAL - PERÍODO SELECIONADO', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # Posição inicial dos cards
    card_y = pdf.get_y() + 5
    
    # CARD 1: DESENVOLVIDOS
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, card_y, 45, 42, 'F')
    pdf.set_xy(15, card_y + 4)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'DESENVOLVIDOS', 0, 1)
    pdf.set_xy(15, card_y + 14)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, str(desenvolvidos_periodo), 0, 1)
    pdf.set_xy(15, card_y + 30)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f'({pct_desenv_periodo:.0f}%)', 0, 1)
    
    # CARD 2: COMISSIONADOS
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(60, card_y, 45, 42, 'F')
    pdf.set_xy(65, card_y + 4)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 4, 'COMISSIONADOS', 0, 1)
    pdf.set_xy(65, card_y + 14)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 7, str(comissionados_periodo), 0, 1)
    pdf.set_xy(65, card_y + 30)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 4, f'({pct_comiss_periodo:.0f}%)', 0, 1)
    
    # CARD 3: VALIDADOS
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(110, card_y, 45, 42, 'F')
    pdf.set_xy(115, card_y + 4)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 4, 'VALIDADOS', 0, 1)
    pdf.set_xy(115, card_y + 14)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 7, str(validados_periodo), 0, 1)
    pdf.set_xy(115, card_y + 30)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 4, f'({pct_valid_periodo:.0f}%)', 0, 1)
    
    # CARD 4: EM REVISÃO
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(160, card_y, 40, 42, 'F')
    pdf.set_xy(165, card_y + 4)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 4, 'EM REVISÃO', 0, 1)
    pdf.set_xy(165, card_y + 14)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 7, str(revisao_periodo), 0, 1)
    pdf.set_xy(165, card_y + 30)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 4, f'({pct_revisao_periodo:.0f}%)', 0, 1)
    
    pdf.ln(45)
    
    # ============================================
    # PROGRESSO DO COMISSIONAMENTO - PERÍODO
    # ============================================
    bar_y = pdf.get_y() + 2
    
    pdf.set_y(bar_y)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'PROGRESSO DO COMISSIONAMENTO - PERÍODO', 0, 1)
    
    # Barra Comissionados
    pdf.set_y(bar_y + 7)
    pdf.set_font('Arial', '', 9)
    pdf.cell(45, 6, 'Comissionados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 7, 110, 5, 'F')
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(55, bar_y + 7, 110 * (pct_comiss_periodo / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 5)
    pdf.cell(20, 6, f'{comissionados_periodo} ({pct_comiss_periodo:.0f}%)', 0, 1)
    
    # Barra Validados
    pdf.set_y(bar_y + 14)
    pdf.cell(45, 6, 'Validados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 14, 110, 5, 'F')
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(55, bar_y + 14, 110 * (pct_valid_periodo / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 12)
    pdf.cell(20, 6, f'{validados_periodo} ({pct_valid_periodo:.0f}%)', 0, 1)
    
    # Barra Em Revisão
    pdf.set_y(bar_y + 21)
    pdf.cell(45, 6, 'Em Revisão:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 21, 110, 5, 'F')
    pdf.set_fill_color(245, 124, 0)
    pdf.rect(55, bar_y + 21, 110 * (pct_revisao_periodo / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 19)
    pdf.cell(20, 6, f'{revisao_periodo} ({pct_revisao_periodo:.0f}%)', 0, 1)
    
    pdf.ln(8)
    
    # ============================================
    # 2. DISTRIBUIÇÃO POR STATUS - PERÍODO
    # ============================================
    dist_y = pdf.get_y() + 2
    
    pdf.set_y(dist_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '2. DISTRIBUIÇÃO POR STATUS - PERÍODO', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Arial', '', 10)
    status_counts = df_periodo['Status'].value_counts()
    for status, qtd in status_counts.items():
        pct = (qtd / total_periodo * 100) if total_periodo > 0 else 0
        pdf.cell(15, 5, '', 0, 0)
        pdf.cell(0, 5, f'{status}: {qtd} ({pct:.1f}%)', 0, 1)
    
    pdf.ln(3)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS - PERÍODO
    # ============================================
    tipo_y = pdf.get_y()
    
    pdf.set_y(tipo_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '3. TIPOS DE EQUIPAMENTOS - PERÍODO', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('Arial', '', 10)
    y_offset = pdf.get_y() + 3
    
    if 'Tipo' in df_periodo.columns and not df_periodo['Tipo'].dropna().empty:
        tipo_counts = df_periodo['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total_periodo * 100) if total_periodo > 0 else 0
            pdf.set_y(y_offset)
            pdf.cell(15, 5, '', 0, 0)
            pdf.cell(0, 5, f'{tipo}: {qtd} ({pct:.0f}%)', 0, 1)
            y_offset += 5
    else:
        pdf.set_y(y_offset)
        pdf.cell(0, 5, 'Não há dados de tipos de equipamento disponíveis.', 0, 1)
        y_offset += 5
    
    # ============================================
    # PÁGINA 2 - ACUMULADO DA UNIDADE (COM GRÁFICO)
    # ============================================
    pdf.add_page()
    
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '4. ACUMULADO DA UNIDADE', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Gerar gráfico de barras com dados ACUMULADOS
    fig = gerar_grafico_barras_vertical(total_acumulado, comissionados_acumulado, validados_acumulado, revisao_acumulado)
    
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
    pdf.cell(0, 6, 'Resumo da Unidade (Todos os Registros):', 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Total de Equipamentos Cadastrados: {total_acumulado}', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Comissionados e Aguardando Validação: {comissionados_acumulado} ({pct_comiss_acumulado:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Validados: {validados_acumulado} ({pct_valid_acumulado:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos em Revisão: {revisao_acumulado} ({pct_revisao_acumulado:.1f}%)', 0, 1)
    
    pdf.ln(10)
    
    # ============================================
    # PÁGINA 3 - PERFORMANCE POR RESPONSÁVEL
    # ============================================
    pdf.add_page()
    
    pdf.set_y(25)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '5. PERFORMANCE POR RESPONSÁVEL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    col_resp = 'Resp_Com'
    y_offset = pdf.get_y() + 5
    
    if col_resp in df_periodo.columns:
        df_resp = df_periodo[df_periodo[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Comissionados por Responsável (Período):', 0, 1)
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
            df_revisao = df_periodo[df_periodo['Status'] == 'Necessário Revisão']
            
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
    pdf.ln(6)
    
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
    pdf.ln(6)
    
    # Aprovado por
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'Aprovado por:', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, 'Mauricio Dias Avelino - Coord Tech Proj Sist Operativos', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'mauricio.avelino@energisa.com.br', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, 'Cassio Fernando Bazana Nonenmacher - Ger Tecnologia Operativa', 0, 1, 'L')
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'cassio.bazana@energisa.com.br', 0, 1, 'L')
    pdf.ln(2)
    
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
