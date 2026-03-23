# pdf_generator.py - Versão sem Emojis
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

def gerar_grafico_pizza(status_counts, total):
    """Gera gráfico de pizza usando matplotlib"""
    if status_counts.empty:
        return None
    
    # Cores para cada status
    cores = {
        'Desenvolvido': '#2E7D32',
        'Comissionado': '#028a9f',
        'Validado': '#005973',
        'Necessário Revisão': '#F57C00',
        'Pendente': '#C62828'
    }
    
    # Preparar dados
    labels = status_counts.index.tolist()
    values = status_counts.values.tolist()
    colors = [cores.get(status, '#CCCCCC') for status in labels]
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Criar pizza
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=[0.03] * len(labels),
        shadow=True,
        textprops={'fontsize': 10}
    )
    
    # Configurar textos
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_weight('bold')
    
    ax.set_title('Distribuicao por Status', fontsize=14, fontweight='bold', pad=20)
    
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
    
    # Aplicar filtro de mês e ano se selecionados
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        if 'Mes_Nome' in df_empresa.columns:
            df_empresa = df_empresa[df_empresa['Mes_Nome'] == mes_selecionado]
    
    if ano_selecionado and ano_selecionado != "Todos os Anos":
        if 'Ano' in df_empresa.columns:
            df_empresa = df_empresa[df_empresa['Ano'] == ano_selecionado]
    
    if df_empresa.empty:
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
    pdf.cell(0, 8, 'RELATORIO DE COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    # Subtítulo
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 6, f'UNIDADE {empresa}', 0, 1, 'C')
    
    # Período (se houver filtro)
    if mes_selecionado and mes_selecionado != "Todos os Meses":
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        periodo_texto = f'Periodo: {mes_selecionado}'
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
    pdf.cell(0, 5, f'Emissao: {brasilia_time.strftime("%d/%m/%Y - %H:%M")} (Horario de Brasilia)', 0, 1, 'R')
    
    # ============================================
    # MÉTRICAS
    # ============================================
    total = len(df_empresa)
    desenvolvidos = len(df_empresa[df_empresa['Status'] == 'Desenvolvido'])
    comissionados = len(df_empresa[df_empresa['Status'] == 'Comissionado'])
    validados = len(df_empresa[df_empresa['Status'] == 'Validado'])
    revisao = len(df_empresa[df_empresa['Status'] == 'Necessário Revisão'])
    pendentes = comissionados - validados
    
    pct_comiss = (comissionados / total * 100) if total > 0 else 0
    pct_valid = (validados / total * 100) if total > 0 else 0
    pct_revisao = (revisao / total * 100) if total > 0 else 0
    pct_desenv = (desenvolvidos / total * 100) if total > 0 else 0
    
    # ============================================
    # 1. PANORAMA GERAL - CARDS (SEM TOTAL)
    # ============================================
    y_pos = 63
    
    pdf.set_y(y_pos)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '1. PANORAMA GERAL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # Posição inicial dos cards (agora 5 cards)
    card_y = 86
    
    # ============================================
    # CARD 1: DESENVOLVIDOS
    # ============================================
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, card_y, 55, 35, 'F')
    pdf.set_xy(15, card_y + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'DESENVOLVIDOS', 0, 1)
    pdf.set_xy(15, card_y + 15)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, str(desenvolvidos), 0, 1)
    pdf.set_xy(15, card_y + 27)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f'({pct_desenv:.0f}%)', 0, 1)
    
    # ============================================
    # CARD 2: COMISSIONADOS
    # ============================================
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(70, card_y, 55, 35, 'F')
    pdf.set_xy(75, card_y + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 5, 'COMISSIONADOS', 0, 1)
    pdf.set_xy(75, card_y + 15)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 8, str(comissionados), 0, 1)
    pdf.set_xy(75, card_y + 27)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 4, f'({pct_comiss:.0f}%)', 0, 1)
    
    # ============================================
    # CARD 3: VALIDADOS
    # ============================================
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(130, card_y, 55, 35, 'F')
    pdf.set_xy(135, card_y + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 5, 'VALIDADOS', 0, 1)
    pdf.set_xy(135, card_y + 15)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 8, str(validados), 0, 1)
    pdf.set_xy(135, card_y + 27)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 4, f'({pct_valid:.0f}%)', 0, 1)
    
    # ============================================
    # CARD 4: EM REVISAO
    # ============================================
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, card_y + 42, 55, 35, 'F')
    pdf.set_xy(15, card_y + 47)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 5, 'EM REVISAO', 0, 1)
    pdf.set_xy(15, card_y + 57)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 8, str(revisao), 0, 1)
    pdf.set_xy(15, card_y + 69)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 4, f'({pct_revisao:.0f}%)', 0, 1)
    
    # ============================================
    # CARD 5: AGUARDANDO
    # ============================================
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(70, card_y + 42, 55, 35, 'F')
    pdf.set_xy(75, card_y + 47)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(198, 40, 40)
    pdf.cell(0, 5, 'AGUARDANDO', 0, 1)
    pdf.set_xy(75, card_y + 57)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(198, 40, 40)
    pdf.cell(0, 8, str(pendentes), 0, 1)
    pdf.set_xy(75, card_y + 69)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(198, 40, 40)
    pdf.cell(0, 4, 'validacao', 0, 1)
    
    # ============================================
    # BARRAS DE PROGRESSO
    # ============================================
    bar_y = 173
    
    pdf.set_y(bar_y)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, 'PROGRESSO DO COMISSIONAMENTO', 0, 1)
    
    # Barra Comissionados
    pdf.set_y(bar_y + 10)
    pdf.set_font('Arial', '', 9)
    pdf.cell(45, 6, 'Comissionados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 10, 110, 5, 'F')
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(55, bar_y + 10, 110 * (pct_comiss / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 8)
    pdf.cell(20, 6, f'{comissionados} ({pct_comiss:.0f}%)', 0, 1)
    
    # Barra Validados
    pdf.set_y(bar_y + 18)
    pdf.cell(45, 6, 'Validados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 18, 110, 5, 'F')
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(55, bar_y + 18, 110 * (pct_valid / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 16)
    pdf.cell(20, 6, f'{validados} ({pct_valid:.0f}%)', 0, 1)
    
    # Barra Em Revisão
    pdf.set_y(bar_y + 26)
    pdf.cell(45, 6, 'Em Revisao:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, bar_y + 26, 110, 5, 'F')
    pdf.set_fill_color(245, 124, 0)
    pdf.rect(55, bar_y + 26, 110 * (pct_revisao / 100), 5, 'F')
    pdf.set_xy(170, bar_y + 24)
    pdf.cell(20, 6, f'{revisao} ({pct_revisao:.0f}%)', 0, 1)
    
    pdf.ln(10)
    
    # ============================================
    # 2. DISTRIBUIÇÃO POR STATUS (COM GRÁFICO DE PIZZA)
    # ============================================
    dist_y = 208
    
    pdf.set_y(dist_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '2. DISTRIBUICAO POR STATUS', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Gerar gráfico de pizza
    status_counts = df_empresa['Status'].value_counts()
    fig_pizza = gerar_grafico_pizza(status_counts, total)
    
    if fig_pizza:
        # Salvar gráfico como imagem temporária
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig_pizza.savefig(temp_img.name, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig_pizza)
        
        # Adicionar imagem ao PDF
        pdf.image(temp_img.name, x=30, w=150)
        os.unlink(temp_img.name)
        pdf.ln(90)
    else:
        # Fallback: lista textual
        pdf.set_font('Arial', '', 10)
        for status, qtd in status_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.cell(15, 6, '', 0, 0)
            pdf.cell(0, 6, f'{status}: {qtd} ({pct:.1f}%)', 0, 1)
        pdf.ln(5)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS
    # ============================================
    tipo_y = pdf.get_y()
    
    pdf.set_y(tipo_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '3. TIPOS DE EQUIPAMENTOS', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font('Arial', '', 10)
    y_offset = pdf.get_y() + 5
    
    if 'Tipo' in df_empresa.columns and not df_empresa['Tipo'].dropna().empty:
        tipo_counts = df_empresa['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.set_y(y_offset)
            pdf.cell(15, 6, '', 0, 0)
            pdf.cell(0, 6, f'{tipo}: {qtd} ({pct:.0f}%)', 0, 1)
            y_offset += 6
    else:
        pdf.set_y(y_offset)
        pdf.cell(0, 6, 'Nao ha dados de tipos de equipamento disponiveis.', 0, 1)
        y_offset += 6
    
    # ============================================
    # 4. ACUMULADO DA UNIDADE (NOVA VISÃO)
    # ============================================
    acumulado_y = y_offset + 15
    
    # Verificar se precisa de nova página
    if acumulado_y > 250:
        pdf.add_page()
        acumulado_y = 30
    
    pdf.set_y(acumulado_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '4. ACUMULADO DA UNIDADE', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Fundo cinza claro
    pdf.set_fill_color(245, 245, 250)
    pdf.rect(10, pdf.get_y(), 190, 70, 'F')
    
    # Conteúdo do acumulado
    y_acum = pdf.get_y() + 5
    pdf.set_y(y_acum)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'RESUMO DA UNIDADE {empresa}', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Total de Equipamentos Cadastrados: {total}', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Comissionados: {comissionados} ({pct_comiss:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Validados: {validados} ({pct_valid:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos em Revisao: {revisao} ({pct_revisao:.1f}%)', 0, 1)
    pdf.cell(0, 5, f'Equipamentos Aguardando Validacao: {pendentes}', 0, 1)
    
    pdf.ln(3)
    
    # Meta e status (sem emojis)
    pdf.set_font('Arial', 'B', 9)
    meta_comiss = 80
    
    if pct_comiss < 30:
        status_comiss = "CRITICO"
        status_text = "CRITICO - Necessita acao imediata"
    elif pct_comiss < 50:
        status_comiss = "ATENCAO"
        status_text = "ATENCAO - Abaixo da meta"
    else:
        status_comiss = "OK"
        status_text = "OK - Dentro da meta"
    
    pdf.cell(0, 5, f'Meta de Comissionamento: {meta_comiss}% dos equipamentos', 0, 1)
    pdf.cell(0, 5, f'Status Atual: {pct_comiss:.1f}% comissionado - {status_text}', 0, 1)
    
    # ============================================
    # 5. PERFORMANCE POR RESPONSAVEL
    # ============================================
    perf_y = pdf.get_y() + 15
    
    if perf_y > 250:
        pdf.add_page()
        perf_y = 30
    
    pdf.set_y(perf_y)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '5. PERFORMANCE POR RESPONSAVEL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    col_resp = 'Resp_Com'
    y_offset = pdf.get_y() + 6
    
    if col_resp in df_empresa.columns:
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Comissionados por Responsavel:', 0, 1)
            y_offset += 8
            
            pdf.set_y(y_offset)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 240)
            pdf.cell(70, 7, 'Responsavel', 1, 0, 'C', 1)
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
            df_revisao = df_empresa[df_empresa['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_y(y_offset)
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(245, 124, 0)
                pdf.cell(0, 6, 'Equipamentos em Revisao por Responsavel:', 0, 1)
                pdf.set_text_color(0, 0, 0)
                y_offset += 8
                
                pdf.set_y(y_offset)
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(255, 220, 200)
                pdf.cell(70, 7, 'Responsavel', 1, 0, 'C', 1)
                pdf.cell(35, 7, 'Em Revisao', 1, 0, 'C', 1)
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
            pdf.cell(0, 6, 'Nao ha dados de responsaveis disponiveis.', 0, 1)
    else:
        pdf.set_y(y_offset)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, 'Coluna de responsaveis nao encontrada.', 0, 1)
    
    # Rodapé
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Energisa - Comissionamento SCADA | Unidade {empresa} | Pagina {pdf.page_no()}', 0, 0, 'C')
    
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
            st.warning("Nao ha dados para gerar o relatorio.")
            return
        
        # Filtrar dados da empresa
        df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa]
        
        if df_empresa.empty:
            st.warning(f"Nao ha dados para a empresa {empresa} com os filtros selecionados.")
            return
        
        with st.spinner(f"Gerando relatorio da {empresa}..."):
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
                
                st.success(f"Relatorio da {empresa} gerado com sucesso!")
                
                st.download_button(
                    label=f"Baixar Relatorio {empresa}",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_download_{empresa}"
                )
                
                os.unlink(pdf_path)
                
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {str(e)}")
