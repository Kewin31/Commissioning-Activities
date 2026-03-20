# pdf_generator.py - Versão Simplificada
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

class PDFRelatorio(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 89, 115)
        self.cell(0, 10, 'RELATORIO EXECUTIVO - COMISSIONAMENTO SCADA', 0, 1, 'C')
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Unidades EMT | ETO', 0, 1, 'C')
        
        self.line(10, 30, 200, 30)
        
        self.set_y(35)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Energisa - Pagina {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 89, 115)
        self.cell(0, 10, title, 0, 1, 'L')
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)
    
    def progress_bar(self, percent, width=150):
        x = self.get_x()
        y = self.get_y()
        
        self.set_fill_color(230, 230, 230)
        self.rect(x, y, width, 6, 'F')
        
        self.set_fill_color(2, 138, 159)
        self.rect(x, y, width * (percent / 100), 6, 'F')
        
        self.set_font('Arial', '', 8)
        self.set_xy(x + width + 5, y - 2)
        self.cell(20, 10, f'{percent:.1f}%', 0, 1)
        self.set_y(y + 10)


def gerar_relatorio_pdf(df):
    """Gera PDF com os dados"""
    if df.empty:
        raise ValueError("Sem dados")
    
    pdf = PDFRelatorio()
    pdf.add_page()
    
    # Resumo
    pdf.section_title('RESUMO EXECUTIVO')
    
    total = len(df)
    dev = len(df[df['Status'] == 'Desenvolvido'])
    com = len(df[df['Status'] == 'Comissionado'])
    val = len(df[df['Status'] == 'Validado'])
    rev = len(df[df['Status'] == 'Necessário Revisão'])
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f'Total de Equipamentos: {total}', 0, 1)
    pdf.cell(0, 8, f'Desenvolvidos: {dev}', 0, 1)
    pdf.cell(0, 8, f'Comissionados: {com}', 0, 1)
    pdf.cell(0, 8, f'Validados: {val}', 0, 1)
    pdf.cell(0, 8, f'Em Revisao: {rev}', 0, 1)
    pdf.ln(5)
    
    # Pontos Criticos
    pdf.section_title('PONTOS CRITICOS')
    
    df_criticos = df[df['Status'] == 'Necessário Revisão'].head(5)
    
    if not df_criticos.empty:
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(30, 8, 'Codigo', 1, 0, 'C')
        pdf.cell(50, 8, 'Tipo', 1, 0, 'C')
        pdf.cell(30, 8, 'Empresa', 1, 0, 'C')
        pdf.cell(50, 8, 'Responsavel', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 8)
        for _, row in df_criticos.iterrows():
            cod = str(row.get('Codigo', 'N/A'))[:10]
            tip = str(row.get('Tipo', 'N/A'))[:20]
            emp = str(row.get('Empresa', 'N/A'))[:15]
            resp = str(row.get('Resp_Dev', 'N/A'))[:20]
            
            pdf.cell(30, 7, cod, 1, 0)
            pdf.cell(50, 7, tip, 1, 0)
            pdf.cell(30, 7, emp, 1, 0)
            pdf.cell(50, 7, resp, 1, 1)
    else:
        pdf.cell(0, 8, 'Nenhum equipamento em revisao', 0, 1)
    
    # Recomendacoes
    pdf.ln(5)
    pdf.section_title('RECOMENDACOES')
    
    pdf.set_font('Arial', '', 10)
    if rev > 0:
        pdf.cell(0, 8, f'1. Priorizar correcao dos {rev} equipamentos em revisao', 0, 1)
    if com - val > 0:
        pdf.cell(0, 8, f'2. Acelerar validacao dos {com - val} equipamentos pendentes', 0, 1)
    
    # Temporario
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    return tmp.name


def adicionar_botao_pdf(df_filtrado):
    """Adiciona botao para gerar PDF"""
    
    if st.button("📄 Gerar Relatorio PDF", use_container_width=True):
        if df_filtrado.empty:
            st.warning("Sem dados para gerar relatorio")
            return
        
        with st.spinner("Gerando PDF..."):
            try:
                pdf_path = gerar_relatorio_pdf(df_filtrado)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                st.success("PDF gerado!")
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                os.unlink(pdf_path)
                
            except Exception as e:
                st.error(f"Erro: {str(e)}")
