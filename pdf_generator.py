# pdf_generator.py - Versão Definitiva
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

def gerar_relatorio_empresa(df_filtrado, empresa):
    """
    Gera relatório PDF executivo para uma empresa específica
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # Criar PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ============================================
    # PÁGINA 1 - TODOS OS DADOS
    # ============================================
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 10, 'RELATORIO DE COMISSIONAMENTO SCADA', 0, 1, 'C')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 6, f'UNIDADE {empresa}', 0, 1, 'C')
    
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, 38, 200, 38)
    
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f'Emissao: {datetime.now().strftime("%d/%m/%Y - %H:%M")}', 0, 1, 'R')
    pdf.ln(8)
    
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
    pct_desenv = (desenvolvidos / total * 100) if total > 0 else 0
    
    # ============================================
    # TÍTULO PANORAMA GERAL
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '1. PANORAMA GERAL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Cards em linha única
    pdf.set_font('Arial', 'B', 10)
    
    # Card Total
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, pdf.get_y(), 45, 28, 'F')
    pdf.set_xy(12, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'TOTAL', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 7, str(total), 0, 1)
    
    # Card Desenvolvidos
    pdf.set_xy(60, pdf.get_y() - 28)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(60, pdf.get_y(), 45, 28, 'F')
    pdf.set_xy(62, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'DESENVOLVIDOS', 0, 1)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 6, str(desenvolvidos), 0, 1)
    pdf.set_font('Arial', '', 6)
    pdf.cell(0, 3, f'({pct_desenv:.0f}%)', 0, 1)
    
    # Card Comissionados
    pdf.set_xy(110, pdf.get_y() - 28)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(110, pdf.get_y(), 45, 28, 'F')
    pdf.set_xy(112, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'COMISSIONADOS', 0, 1)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(2, 138, 159)
    pdf.cell(0, 6, str(comissionados), 0, 1)
    pdf.set_font('Arial', '', 6)
    pdf.cell(0, 3, f'({pct_comiss:.0f}%)', 0, 1)
    
    # Card Validados
    pdf.set_xy(160, pdf.get_y() - 28)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(160, pdf.get_y(), 40, 28, 'F')
    pdf.set_xy(162, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'VALIDADOS', 0, 1)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 6, str(validados), 0, 1)
    pdf.set_font('Arial', '', 6)
    pdf.cell(0, 3, f'({pct_valid:.0f}%)', 0, 1)
    
    pdf.ln(32)
    
    # Segunda linha de cards
    pdf.set_text_color(0, 0, 0)
    
    # Card Em Revisão
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(10, pdf.get_y(), 45, 28, 'F')
    pdf.set_xy(12, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'EM REVISAO', 0, 1)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(245, 124, 0)
    pdf.cell(0, 6, str(revisao), 0, 1)
    pdf.set_font('Arial', '', 6)
    pdf.cell(0, 3, f'({pct_revisao:.0f}%)', 0, 1)
    
    # Card Aguardando
    pdf.set_xy(60, pdf.get_y() - 28)
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(60, pdf.get_y(), 45, 28, 'F')
    pdf.set_xy(62, pdf.get_y() + 4)
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'AGUARDANDO', 0, 1)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(198, 40, 40)
    pdf.cell(0, 6, str(pendentes), 0, 1)
    pdf.set_font('Arial', '', 6)
    pdf.cell(0, 3, 'validacao', 0, 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(32)
    
    # Barras de progresso
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, 'PROGRESSO DO COMISSIONAMENTO', 0, 1)
    pdf.ln(2)
    
    # Barra Comissionados
    pdf.set_font('Arial', '', 9)
    pdf.cell(45, 6, 'Comissionados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, pdf.get_y(), 110, 5, 'F')
    pdf.set_fill_color(2, 138, 159)
    pdf.rect(55, pdf.get_y(), 110 * (pct_comiss / 100), 5, 'F')
    pdf.set_xy(170, pdf.get_y() - 2)
    pdf.cell(20, 6, f'{comissionados} ({pct_comiss:.0f}%)', 0, 1)
    
    # Barra Validados
    pdf.cell(45, 6, 'Validados:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, pdf.get_y(), 110, 5, 'F')
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(55, pdf.get_y(), 110 * (pct_valid / 100), 5, 'F')
    pdf.set_xy(170, pdf.get_y() - 2)
    pdf.cell(20, 6, f'{validados} ({pct_valid:.0f}%)', 0, 1)
    
    # Barra Em Revisão
    pdf.cell(45, 6, 'Em Revisao:', 0, 0)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(55, pdf.get_y(), 110, 5, 'F')
    pdf.set_fill_color(245, 124, 0)
    pdf.rect(55, pdf.get_y(), 110 * (pct_revisao / 100), 5, 'F')
    pdf.set_xy(170, pdf.get_y() - 2)
    pdf.cell(20, 6, f'{revisao} ({pct_revisao:.0f}%)', 0, 1)
    
    pdf.ln(8)
    
    # ============================================
    # 2. DISTRIBUIÇÃO POR STATUS
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '2. DISTRIBUICAO POR STATUS', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    status_counts = df_empresa['Status'].value_counts()
    for status, qtd in status_counts.items():
        pct = (qtd / total * 100) if total > 0 else 0
        pdf.cell(15, 6, '', 0, 0)
        pdf.cell(0, 6, f'{status}: {qtd} ({pct:.1f}%)', 0, 1)
    
    pdf.ln(5)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '3. TIPOS DE EQUIPAMENTOS', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if 'Tipo' in df_empresa.columns and not df_empresa['Tipo'].dropna().empty:
        pdf.set_font('Arial', '', 10)
        tipo_counts = df_empresa['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.cell(15, 6, '', 0, 0)
            pdf.cell(0, 6, f'{tipo}: {qtd} ({pct:.0f}%)', 0, 1)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, 'Nao ha dados de tipos de equipamento disponiveis.', 0, 1)
    
    pdf.ln(8)
    
    # ============================================
    # 4. PERFORMANCE (continua na mesma página se houver espaço)
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 89, 115)
    pdf.cell(0, 8, '4. PERFORMANCE POR RESPONSAVEL', 0, 1, 'L')
    pdf.set_draw_color(2, 138, 159)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    col_resp = 'Resp_Com'
    
    if col_resp in df_empresa.columns:
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            # Tabela de comissionados
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Comissionados por Responsavel:', 0, 1)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 240)
            pdf.cell(65, 7, 'Responsavel', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Comissionados', 1, 0, 'C', 1)
            pdf.cell(35, 7, 'Validados', 1, 0, 'C', 1)
            pdf.cell(45, 7, 'Taxa Sucesso', 1, 1, 'C', 1)
            
            pdf.set_font('Arial', '', 8)
            pdf.set_fill_color(255, 255, 255)
            
            top_resp = df_resp[col_resp].value_counts().head(8).index.tolist()
            for resp in top_resp:
                df_item = df_resp[df_resp[col_resp] == resp]
                total_resp = len(df_item)
                validados_resp = len(df_item[df_item['Status'] == 'Validado'])
                taxa = (validados_resp / total_resp * 100) if total_resp > 0 else 0
                
                nome = str(resp)[:30]
                pdf.cell(65, 6, nome, 1, 0, 'L')
                pdf.cell(35, 6, str(total_resp), 1, 0, 'C')
                pdf.cell(35, 6, str(validados_resp), 1, 0, 'C')
                pdf.cell(45, 6, f'{taxa:.0f}%', 1, 1, 'C')
            
            pdf.ln(4)
            
            # Equipamentos em revisão
            df_revisao = df_empresa[df_empresa['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(245, 124, 0)
                pdf.cell(0, 6, 'Equipamentos em Revisao por Responsavel:', 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(255, 220, 200)
                pdf.cell(65, 7, 'Responsavel', 1, 0, 'C', 1)
                pdf.cell(35, 7, 'Em Revisao', 1, 0, 'C', 1)
                pdf.cell(85, 7, 'Equipamentos', 1, 1, 'C', 1)
                
                pdf.set_font('Arial', '', 7)
                pdf.set_fill_color(255, 255, 255)
                
                revisao_por_resp = df_revisao[col_resp].value_counts().head(8)
                for resp, qtd in revisao_por_resp.items():
                    equipamentos = df_revisao[df_revisao[col_resp] == resp]['Codigo'].head(3).tolist()
                    equip_str = ', '.join([str(e) for e in equipamentos if pd.notna(e)])
                    if len(equipamentos) > 3:
                        equip_str += '...'
                    
                    nome = str(resp)[:30]
                    pdf.cell(65, 6, nome, 1, 0, 'L')
                    pdf.cell(35, 6, str(qtd), 1, 0, 'C')
                    pdf.cell(85, 6, equip_str[:50], 1, 1, 'L')
        else:
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, 'Nao ha dados de responsaveis disponiveis.', 0, 1)
    else:
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


def adicionar_botao_pdf_empresa(df_filtrado, empresa):
    """
    Adiciona botão no Streamlit para gerar e baixar o PDF
    """
    if st.button(f"📊 Gerar Relatório {empresa}", use_container_width=True, key=f"btn_pdf_{empresa}"):
        if df_filtrado.empty:
            st.warning("Nao ha dados para gerar o relatorio.")
            return
        
        df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa]
        
        if df_empresa.empty:
            st.warning(f"Nao ha dados para a empresa {empresa} com os filtros selecionados.")
            return
        
        with st.spinner(f"Gerando relatorio da {empresa}..."):
            try:
                pdf_path = gerar_relatorio_empresa(df_filtrado, empresa)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                st.success(f"Relatorio da {empresa} gerado com sucesso!")
                
                st.download_button(
                    label=f"Baixar Relatorio {empresa}",
                    data=pdf_bytes,
                    file_name=f"relatorio_{empresa}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_download_{empresa}"
                )
                
                os.unlink(pdf_path)
                
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {str(e)}")
