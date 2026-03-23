# pdf_generator.py - Versão Mínima para Teste
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

def gerar_relatorio_empresa(df_filtrado, empresa):
    """
    Gera relatório PDF para uma empresa específica - Versão Simplificada
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # Criar PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Configurar fonte
    pdf.set_font('Arial', 'B', 16)
    
    # Título
    pdf.cell(0, 10, f'RELATORIO - UNIDADE {empresa}', 0, 1, 'C')
    pdf.cell(0, 10, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Métricas
    total = len(df_empresa)
    desenvolvidos = len(df_empresa[df_empresa['Status'] == 'Desenvolvido'])
    comissionados = len(df_empresa[df_empresa['Status'] == 'Comissionado'])
    validados = len(df_empresa[df_empresa['Status'] == 'Validado'])
    revisao = len(df_empresa[df_empresa['Status'] == 'Necessário Revisão'])
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Total de Equipamentos: {total}', 0, 1)
    pdf.cell(0, 8, f'Desenvolvidos: {desenvolvidos}', 0, 1)
    pdf.cell(0, 8, f'Comissionados: {comissionados}', 0, 1)
    pdf.cell(0, 8, f'Validados: {validados}', 0, 1)
    pdf.cell(0, 8, f'Em Revisao: {revisao}', 0, 1)
    pdf.ln(10)
    
    # Distribuição por Status
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Distribuicao por Status:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    status_counts = df_empresa['Status'].value_counts()
    for status, qtd in status_counts.items():
        pdf.cell(0, 6, f'  - {status}: {qtd}', 0, 1)
    
    pdf.ln(10)
    
    # Tipos de Equipamento
    if 'Tipo' in df_empresa.columns:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Tipos de Equipamento:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        tipo_counts = df_empresa['Tipo'].value_counts().head(8)
        for tipo, qtd in tipo_counts.items():
            pdf.cell(0, 6, f'  - {tipo}: {qtd}', 0, 1)
    
    pdf.ln(10)
    
    # Performance por Responsável
    col_resp = 'Resp_Com'
    if col_resp in df_empresa.columns:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Performance por Responsavel:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        top_resp = df_resp[col_resp].value_counts().head(5)
        
        for resp, qtd in top_resp.items():
            pdf.cell(0, 6, f'  - {resp}: {qtd} comissionamentos', 0, 1)
    
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
