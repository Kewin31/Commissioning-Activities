# pdf_generator.py - Versão Simplificada e Estável
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

def gerar_relatorio_empresa(df_filtrado, empresa):
    """
    Gera relatório PDF para uma empresa específica
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # Criar PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ============================================
    # PÁGINA 1 - RESUMO E ANÁLISE
    # ============================================
    pdf.add_page()
    
    # Título
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'RELATORIO COMISSIONAMENTO SCADA', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'UNIDADE {empresa}', 0, 1, 'C')
    pdf.ln(5)
    
    # Data
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
    pdf.ln(10)
    
    # ============================================
    # 1. MÉTRICAS PRINCIPAIS
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '1. METRICAS PRINCIPAIS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
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
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f'Total de Equipamentos: {total}', 0, 1)
    pdf.cell(0, 7, f'Desenvolvidos: {desenvolvidos} ({pct_desenv:.1f}%)', 0, 1)
    pdf.cell(0, 7, f'Comissionados: {comissionados} ({pct_comiss:.1f}%)', 0, 1)
    pdf.cell(0, 7, f'Validados: {validados} ({pct_valid:.1f}%)', 0, 1)
    pdf.cell(0, 7, f'Em Revisao: {revisao} ({pct_revisao:.1f}%)', 0, 1)
    pdf.cell(0, 7, f'Aguardando Validacao: {pendentes}', 0, 1)
    pdf.ln(5)
    
    # Barras simples
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, 'Progresso:', 0, 1)
    
    def draw_simple_bar(pdf, label, percent, y_pos):
        pdf.set_y(y_pos)
        pdf.set_x(10)
        pdf.set_font('Arial', '', 8)
        pdf.cell(35, 6, label, 0, 0)
        pdf.set_fill_color(200, 200, 200)
        pdf.rect(50, pdf.get_y(), 100, 5, 'F')
        pdf.set_fill_color(0, 100, 150)
        pdf.rect(50, pdf.get_y(), 100 * (percent / 100), 5, 'F')
        pdf.set_xy(155, pdf.get_y() - 2)
        pdf.cell(20, 6, f'{percent:.0f}%', 0, 1)
        return pdf.get_y()
    
    y = pdf.get_y()
    y = draw_simple_bar(pdf, 'Comissionados:', pct_comiss, y)
    y = draw_simple_bar(pdf, 'Validados:', pct_valid, y)
    y = draw_simple_bar(pdf, 'Em Revisao:', pct_revisao, y)
    pdf.ln(10)
    
    # ============================================
    # 2. DISTRIBUIÇÃO POR STATUS
    # ============================================
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '2. DISTRIBUICAO POR STATUS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
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
    pdf.cell(0, 8, '3. TIPOS DE EQUIPAMENTOS', 0, 1, 'L')
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
        pdf.cell(0, 6, 'Nao ha dados de tipos disponiveis.', 0, 1)
    
    pdf.ln(10)
    
    # ============================================
    # PÁGINA 2 - PROGRESS TRACKER
    # ============================================
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '4. PROGRESS TRACKER', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Etapas do fluxo
    pdf.set_font('Arial', 'B', 10)
    
    pdf.cell(50, 8, 'ETAPA 1', 0, 0, 'C')
    pdf.cell(70, 8, 'ETAPA 2', 0, 0, 'C')
    pdf.cell(50, 8, 'ETAPA 3', 0, 1, 'C')
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(50, 12, str(desenvolvidos), 0, 0, 'C')
    pdf.cell(70, 12, str(comissionados), 0, 0, 'C')
    pdf.cell(50, 12, str(validados), 0, 1, 'C')
    
    pdf.set_font('Arial', '', 8)
    pdf.cell(50, 5, 'Desenvolvidos', 0, 0, 'C')
    pdf.cell(70, 5, 'Comissionados', 0, 0, 'C')
    pdf.cell(50, 5, 'Validados', 0, 1, 'C')
    
    pdf.cell(50, 5, 'Aguardando', 0, 0, 'C')
    pdf.cell(70, 5, 'Aguardando', 0, 0, 'C')
    pdf.cell(50, 5, 'Concluido', 0, 1, 'C')
    
    pdf.cell(50, 5, 'comissionamento', 0, 0, 'C')
    pdf.cell(70, 5, 'validacao', 0, 0, 'C')
    pdf.cell(50, 5, '', 0, 1, 'C')
    
    pdf.ln(15)
    
    # Setas
    pdf.set_font('Arial', '', 12)
    pdf.set_x(55)
    pdf.cell(10, 10, '->', 0, 0)
    pdf.set_x(125)
    pdf.cell(10, 10, '->', 0, 1)
    
    pdf.ln(10)
    
    # Gargalo
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(200, 80, 0)
    pdf.cell(0, 8, 'GARGALO', 0, 1, 'L')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'{revisao} equipamentos em revisao', 0, 1, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f'{pct_revisao:.1f}% do total de equipamentos', 0, 1, 'L')
    
    pdf.ln(15)
    
    # ============================================
    # PÁGINA 3 - PERFORMANCE
    # ============================================
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '5. PERFORMANCE POR RESPONSAVEL', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    col_resp = 'Resp_Com'
    
    if col_resp in df_empresa.columns:
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            # Comissionados por responsável
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, 'Comissionados por Responsavel:', 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.cell(65, 7, 'Responsavel', 1, 0, 'C')
            pdf.cell(35, 7, 'Comissionados', 1, 0, 'C')
            pdf.cell(35, 7, 'Validados', 1, 0, 'C')
            pdf.cell(45, 7, 'Taxa Sucesso', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 8)
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
            
            pdf.ln(5)
            
            # Equipamentos em revisão
            df_revisao = df_empresa[df_empresa['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(200, 80, 0)
                pdf.cell(0, 7, 'Equipamentos em Revisao por Responsavel:', 0, 1)
                pdf.ln(2)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(65, 7, 'Responsavel', 1, 0, 'C')
                pdf.cell(35, 7, 'Em Revisao', 1, 0, 'C')
                pdf.cell(85, 7, 'Equipamentos', 1, 1, 'C')
                
                pdf.set_font('Arial', '', 7)
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
            pdf.cell(0, 7, 'Nao ha dados de responsaveis disponiveis.', 0, 1)
    else:
        pdf.cell(0, 7, 'Coluna de responsaveis nao encontrada.', 0, 1)
    
    # Rodapé simples
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f'Energisa - Comissionamento SCADA | Unidade {empresa}', 0, 0, 'C')
    
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
                
                st.success(f"Relatorio da {empresa} gerado!")
                
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
                st.error(f"Erro: {str(e)}")
