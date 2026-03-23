# pdf_generator.py - Versão com Layout Corrigido
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

def gerar_relatorio_empresa(df_filtrado, empresa):
    """
    Gera relatório PDF completo para uma empresa específica
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # Criar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # ============================================
    # CABEÇALHO
    # ============================================
    # Título principal
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, 'RELATORIO EXECUTIVO - COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    # Subtítulo
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 8, f'UNIDADE {empresa}', 0, 1, 'C')
    
    # Linha separadora
    pdf.set_draw_color(0, 89, 115)
    pdf.line(10, 40, 200, 40)
    
    # Data
    pdf.set_y(45)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'Data de emissao: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
    pdf.ln(8)
    
    # ============================================
    # 1. ANALISE DA EMPRESA
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, '1. ANALISE DA EMPRESA', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Métricas
    total = len(df_empresa)
    desenvolvidos = len(df_empresa[df_empresa['Status'] == 'Desenvolvido'])
    comissionados = len(df_empresa[df_empresa['Status'] == 'Comissionado'])
    validados = len(df_empresa[df_empresa['Status'] == 'Validado'])
    revisao = len(df_empresa[df_empresa['Status'] == 'Necessário Revisão'])
    pendentes = comissionados - validados
    
    pct_comiss = (comissionados / total * 100) if total > 0 else 0
    pct_valid = (validados / total * 100) if total > 0 else 0
    pct_revisao = (revisao / total * 100) if total > 0 else 0
    
    # Cards de métricas em grid 2x3
    pdf.set_font('Arial', 'B', 11)
    
    # Linha 1
    pdf.set_x(15)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(15, pdf.get_y(), 55, 25, 'F')
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Equipamentos', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, str(total), 0, 1)
    
    pdf.set_x(85)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(85, pdf.get_y() - 25, 55, 25, 'F')
    pdf.set_xy(90, pdf.get_y() - 20)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Comissionados', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 8, f'{comissionados} ({pct_comiss:.0f}%)', 0, 1)
    
    pdf.set_x(155)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(155, pdf.get_y() - 25, 40, 25, 'F')
    pdf.set_xy(160, pdf.get_y() - 20)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Validados', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 8, f'{validados} ({pct_valid:.0f}%)', 0, 1)
    
    pdf.ln(5)
    
    # Linha 2
    pdf.set_x(15)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(15, pdf.get_y(), 55, 25, 'F')
    pdf.set_xy(20, pdf.get_y() + 5)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Em Revisao', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 8, f'{revisao} ({pct_revisao:.0f}%)', 0, 1)
    
    pdf.set_x(85)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(85, pdf.get_y() - 25, 55, 25, 'F')
    pdf.set_xy(90, pdf.get_y() - 20)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Desenvolvidos', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, str(desenvolvidos), 0, 1)
    
    pdf.ln(20)
    
    # Barras de progresso
    def draw_progress_bar(pdf, x, y, label, value, percentage, color):
        pdf.set_y(y)
        pdf.set_x(x)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 8, label, 0, 0)
        
        pdf.set_fill_color(230, 230, 230)
        pdf.rect(x + 42, y + 1, 100, 6, 'F')
        
        pdf.set_fill_color(color[0], color[1], color[2])
        pdf.rect(x + 42, y + 1, 100 * (percentage / 100), 6, 'F')
        
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(x + 147, y)
        pdf.cell(20, 8, f'{value} ({percentage:.0f}%)', 0, 1)
        return y + 8
    
    y_pos = pdf.get_y()
    y_pos = draw_progress_bar(pdf, 15, y_pos, 'Comissionados:', comissionados, pct_comiss, (2, 138, 159))
    y_pos = draw_progress_bar(pdf, 15, y_pos, 'Validados:', validados, pct_valid, (46, 125, 50))
    y_pos = draw_progress_bar(pdf, 15, y_pos, 'Em Revisao:', revisao, pct_revisao, (245, 124, 0))
    
    pdf.ln(10)
    
    # ============================================
    # 2. DISTRIBUICAO DO PORTFOLIO
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, '2. DISTRIBUICAO DO PORTFOLIO', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, 'Distribuicao por Status:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    status_counts = df_empresa['Status'].value_counts()
    for status, qtd in status_counts.items():
        pct = (qtd / total * 100) if total > 0 else 0
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(0, 6, f'{status}: {qtd} ({pct:.1f}%)', 0, 1)
    
    pdf.ln(5)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, '3. TIPOS DE EQUIPAMENTOS', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if 'Tipo' in df_empresa.columns and not df_empresa['Tipo'].dropna().empty:
        pdf.set_font('Arial', '', 10)
        tipo_counts = df_empresa['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.cell(10, 6, '', 0, 0)
            pdf.cell(0, 6, f'{tipo}: {qtd} ({pct:.0f}%)', 0, 1)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, 'Nao ha dados de tipos de equipamento disponiveis.', 0, 1)
    
    pdf.ln(5)
    
    # ============================================
    # 4. PROGRESS TRACKER
    # ============================================
    # Nova página para o Progress Tracker
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, '4. PROGRESS TRACKER', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Cards do Progress Tracker
    start_y = pdf.get_y()
    
    # ETAPA 1 - Desenvolvidos
    pdf.set_x(15)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(15, start_y, 50, 55, 'F')
    pdf.set_xy(20, start_y + 8)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'ETAPA 1', 0, 1)
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, str(desenvolvidos), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'Desenvolvidos', 0, 1)
    pdf.cell(0, 4, 'Aguardando', 0, 1)
    pdf.cell(0, 4, 'comissionamento', 0, 1)
    
    # Seta
    pdf.set_xy(70, start_y + 25)
    pdf.set_font('Arial', '', 18)
    pdf.cell(10, 10, '->', 0, 1)
    
    # ETAPA 2 - Comissionados
    pdf.set_x(85)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(85, start_y, 50, 55, 'F')
    pdf.set_xy(90, start_y + 8)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'ETAPA 2', 0, 1)
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 10, str(comissionados), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'Comissionados', 0, 1)
    pdf.cell(0, 4, 'Aguardando', 0, 1)
    pdf.cell(0, 4, 'validacao', 0, 1)
    
    # Seta
    pdf.set_xy(140, start_y + 25)
    pdf.set_font('Arial', '', 18)
    pdf.cell(10, 10, '->', 0, 1)
    
    # ETAPA 3 - Validados
    pdf.set_x(155)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(155, start_y, 40, 55, 'F')
    pdf.set_xy(160, start_y + 8)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'ETAPA 3', 0, 1)
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 10, str(validados), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, 'Validados', 0, 1)
    pdf.cell(0, 4, 'Processo', 0, 1)
    pdf.cell(0, 4, 'concluido', 0, 1)
    
    pdf.ln(65)
    
    # GARGALO
    pdf.set_x(15)
    pdf.set_fill_color(255, 240, 230)
    pdf.rect(15, pdf.get_y(), 180, 40, 'F')
    pdf.set_xy(20, pdf.get_y() + 8)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 6, 'GARGALO', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{revisao} equipamentos em revisao', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'{pct_revisao:.1f}% do total de equipamentos', 0, 1)
    
    pdf.ln(15)
    
    # ============================================
    # 5. PERFORMANCE POR RESPONSAVEL
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, '5. PERFORMANCE POR RESPONSAVEL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    col_resp = 'Resp_Com'
    
    if col_resp in df_empresa.columns:
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 89, 115)
            pdf.cell(0, 8, 'Comissionados por Responsavel:', 0, 1)
            
            # Cabeçalho da tabela
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 240)
            pdf.cell(65, 8, 'Responsavel', 1, 0, 'C', 1)
            pdf.cell(35, 8, 'Comissionados', 1, 0, 'C', 1)
            pdf.cell(35, 8, 'Validados', 1, 0, 'C', 1)
            pdf.cell(45, 8, 'Taxa Sucesso', 1, 1, 'C', 1)
            
            pdf.set_font('Arial', '', 8)
            pdf.set_fill_color(255, 255, 255)
            
            top_resp = df_resp[col_resp].value_counts().head(8).index.tolist()
            for resp in top_resp:
                df_resp_item = df_resp[df_resp[col_resp] == resp]
                total_resp = len(df_resp_item)
                validados_resp = len(df_resp_item[df_resp_item['Status'] == 'Validado'])
                taxa = (validados_resp / total_resp * 100) if total_resp > 0 else 0
                
                pdf.cell(65, 7, str(resp)[:30], 1, 0, 'L')
                pdf.cell(35, 7, str(total_resp), 1, 0, 'C')
                pdf.cell(35, 7, str(validados_resp), 1, 0, 'C')
                pdf.cell(45, 7, f'{taxa:.0f}%', 1, 1, 'C')
            
            pdf.ln(5)
            
            # Equipamentos em revisão
            df_revisao = df_empresa[df_empresa['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(245, 124, 0)
                pdf.cell(0, 8, 'Equipamentos em Revisao por Responsavel:', 0, 1)
                
                # Cabeçalho da tabela
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(255, 220, 200)
                pdf.cell(65, 8, 'Responsavel', 1, 0, 'C', 1)
                pdf.cell(35, 8, 'Em Revisao', 1, 0, 'C', 1)
                pdf.cell(85, 8, 'Equipamentos', 1, 1, 'C', 1)
                
                pdf.set_font('Arial', '', 7)
                pdf.set_fill_color(255, 255, 255)
                
                revisao_por_resp = df_revisao[col_resp].value_counts().head(5)
                for resp, qtd in revisao_por_resp.items():
                    equipamentos = df_revisao[df_revisao[col_resp] == resp]['Codigo'].head(3).tolist()
                    equip_str = ', '.join([str(e) for e in equipamentos if pd.notna(e)])
                    if len(equipamentos) > 3:
                        equip_str += '...'
                    
                    pdf.cell(65, 7, str(resp)[:30], 1, 0, 'L')
                    pdf.cell(35, 7, str(qtd), 1, 0, 'C')
                    pdf.cell(85, 7, equip_str[:50], 1, 1, 'L')
        else:
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, 'Nao ha dados de responsaveis disponiveis.', 0, 1)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, 'Coluna de responsaveis nao encontrada.', 0, 1)
    
    # Gerar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name


def adicionar_botao_pdf_empresa(df_filtrado, empresa):
    """
    Adiciona botão no Streamlit para gerar e baixar o PDF da empresa selecionada
    """
    if st.button(f"📊 Gerar Relatório {empresa}", use_container_width=True, key=f"btn_pdf_{empresa}"):
        if df_filtrado.empty:
            st.warning("Nao ha dados para gerar o relatorio com os filtros selecionados.")
            return
        
        # Filtrar dados da empresa
        df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa]
        
        if df_empresa.empty:
            st.warning(f"Nao ha dados para a empresa {empresa} com os filtros selecionados.")
            return
        
        with st.spinner(f"Gerando relatorio da {empresa}... Aguarde um momento."):
            try:
                pdf_path = gerar_relatorio_empresa(df_filtrado, empresa)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                st.success(f"Relatorio da {empresa} gerado com sucesso!")
                
                st.download_button(
                    label=f"Baixar Relatorio {empresa}",
                    data=pdf_bytes,
                    file_name=f"relatorio_comissionamento_{empresa}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_download_{empresa}"
                )
                
                os.unlink(pdf_path)
                
            except ImportError:
                st.error("Biblioteca 'fpdf2' nao instalada.")
                st.code("pip install fpdf2", language="bash")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {str(e)}")
