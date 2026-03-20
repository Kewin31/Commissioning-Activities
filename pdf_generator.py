# pdf_generator.py
"""
Módulo para geração de relatório PDF executivo do Comissionamento SCADA
"""

from fpdf import FPDF
import tempfile
import os
from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd

# Cores no formato RGB para o PDF
CORES_PDF = {
    'azul_energisa': (0, 89, 115),
    'azul_claro': (2, 138, 159),
    'verde': (46, 125, 50),
    'laranja': (245, 124, 0),
    'vermelho': (198, 40, 40),
    'cinza': (100, 100, 100),
    'cinza_claro': (230, 230, 230)
}

class PDFRelatorioExecutivo(FPDF):
    """Classe personalizada para o relatório executivo da Energisa"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        """Cabeçalho do relatório"""
        try:
            logo_path = "Logo_Energisa.png"
            if os.path.exists(logo_path):
                self.image(logo_path, x=10, y=8, w=25)
        except:
            pass
        
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*CORES_PDF['azul_energisa'])
        self.cell(0, 10, 'RELATÓRIO EXECUTIVO - COMISSIONAMENTO SCADA', 0, 1, 'C')
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*CORES_PDF['cinza'])
        self.cell(0, 5, 'Unidades EMT | ETO', 0, 1, 'C')
        
        self.set_draw_color(*CORES_PDF['azul_energisa'])
        self.line(10, 30, 200, 30)
        
        self.set_y(35)
        self.set_font('Arial', '', 9)
        self.set_text_color(*CORES_PDF['cinza'])
        self.cell(0, 5, f'Data de emissão: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
        
        self.ln(5)
    
    def footer(self):
        """Rodapé do relatório"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*CORES_PDF['cinza'])
        self.cell(0, 10, f'⚡ Energisa - Comissionamento SCADA | Página {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title, icon='📊'):
        """Título de seção"""
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*CORES_PDF['azul_energisa'])
        self.cell(0, 10, f'{icon} {title}', 0, 1, 'L')
        self.set_draw_color(*CORES_PDF['azul_energisa'])
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)
    
    def progress_bar(self, percentage, width=150, height=6):
        """Barra de progresso"""
        x = self.get_x()
        y = self.get_y()
        
        self.set_fill_color(*CORES_PDF['cinza_claro'])
        self.rect(x, y, width, height, 'F')
        
        self.set_fill_color(*CORES_PDF['azul_claro'])
        self.rect(x, y, width * (percentage / 100), height, 'F')
        
        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        self.set_xy(x + width + 5, y - 2)
        self.cell(20, 10, f'{percentage:.1f}%', 0, 1)
        
        self.set_y(y + height + 5)
    
    def metric_value(self, value, label):
        """Exibe um valor com label"""
        self.set_font('Arial', 'B', 20)
        self.set_text_color(*CORES_PDF['azul_energisa'])
        self.cell(45, 15, str(value), 0, 0, 'C')
        self.set_font('Arial', '', 8)
        self.set_text_color(*CORES_PDF['cinza'])
        self.cell(45, 15, label, 0, 1, 'C')


def gerar_relatorio_pdf(df_filtrado):
    """
    Gera o relatório PDF executivo a partir dos dados filtrados
    """
    
    if df_filtrado.empty:
        raise ValueError("Não há dados para gerar o relatório")
    
    pdf = PDFRelatorioExecutivo()
    pdf.add_page()
    
    # ============================================
    # 1. RESUMO EXECUTIVO
    # ============================================
    pdf.section_title('RESUMO EXECUTIVO', '📊')
    
    total = len(df_filtrado)
    desenvolvidos = len(df_filtrado[df_filtrado['Status'] == 'Desenvolvido'])
    comissionados = len(df_filtrado[df_filtrado['Status'] == 'Comissionado'])
    validados = len(df_filtrado[df_filtrado['Status'] == 'Validado'])
    revisao = len(df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'])
    
    # Exibir métricas
    pdf.set_font('Arial', '', 10)
    pdf.set_fill_color(245, 245, 245)
    
    pdf.set_x(10)
    pdf.metric_value(total, 'Total')
    pdf.metric_value(desenvolvidos, 'Desenvolvidos')
    pdf.metric_value(comissionados, 'Comissionados')
    pdf.metric_value(validados, 'Validados')
    pdf.metric_value(revisao, 'Em Revisão')
    
    pdf.ln(10)
    
    # Barras de progresso
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Desenvolvidos:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(15, 8, f'{desenvolvidos}', 0, 0)
    pdf.set_x(60)
    pdf.progress_bar((desenvolvidos / total * 100) if total > 0 else 0, 130)
    
    pdf.cell(40, 8, 'Comissionados:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(15, 8, f'{comissionados}', 0, 0)
    pdf.set_x(60)
    pdf.progress_bar((comissionados / total * 100) if total > 0 else 0, 130)
    
    pdf.cell(40, 8, 'Validados:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(15, 8, f'{validados}', 0, 0)
    pdf.set_x(60)
    pdf.progress_bar((validados / total * 100) if total > 0 else 0, 130)
    
    pdf.cell(40, 8, 'Em Revisão:', 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(15, 8, f'{revisao}', 0, 0)
    pdf.set_x(60)
    pdf.progress_bar((revisao / total * 100) if total > 0 else 0, 130)
    
    pdf.ln(10)
    
    # ============================================
    # 2. PONTOS CRÍTICOS
    # ============================================
    pdf.section_title('PONTOS CRÍTICOS', '⚠️')
    
    df_criticos = df_filtrado[df_filtrado['Status'] == 'Necessário Revisão'].copy()
    df_criticos = df_criticos.head(8)
    
    if not df_criticos.empty:
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(255, 240, 230)
        pdf.cell(25, 10, 'Código', 1, 0, 'C', 1)
        pdf.cell(45, 10, 'Tipo', 1, 0, 'C', 1)
        pdf.cell(25, 10, 'Empresa', 1, 0, 'C', 1)
        pdf.cell(45, 10, 'Responsável', 1, 0, 'C', 1)
        pdf.cell(40, 10, 'Status', 1, 1, 'C', 1)
        
        pdf.set_font('Arial', '', 8)
        pdf.set_fill_color(255, 255, 255)
        
        for _, row in df_criticos.iterrows():
            codigo = row.get('Codigo', 'N/A')[:12]
            tipo = row.get('Tipo', 'N/A')[:20]
            empresa = row.get('Empresa', 'N/A')[:12]
            responsavel = row.get('Resp_Dev', 'N/A')[:20]
            
            pdf.cell(25, 8, str(codigo), 1, 0, 'L')
            pdf.cell(45, 8, str(tipo), 1, 0, 'L')
            pdf.cell(25, 8, str(empresa), 1, 0, 'L')
            pdf.cell(45, 8, str(responsavel), 1, 0, 'L')
            pdf.cell(40, 8, 'Em Revisão', 1, 1, 'L')
        
        pdf.ln(5)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, '✅ Nenhum equipamento em revisão no momento.', 0, 1, 'L')
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(200, 80, 80)
    pdf.cell(0, 8, f'🔴 GARGALO: {revisao} equipamentos em revisão', 0, 1, 'L')
    
    if comissionados > 0:
        pendentes_validacao = comissionados - validados
        pct_pendentes = (pendentes_validacao / comissionados * 100) if comissionados > 0 else 0
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(200, 120, 50)
        pdf.cell(0, 8, f'🟠 ATENÇÃO: {pendentes_validacao} equipamentos aguardando validação ({pct_pendentes:.1f}% dos comissionados)', 0, 1, 'L')
    
    pdf.ln(10)
    
    # ============================================
    # 3. COMPARAÇÃO ENTRE UNIDADES
    # ============================================
    pdf.section_title('COMPARAÇÃO ENTRE UNIDADES', '🏢')
    
    for empresa in ['EMT', 'ETO']:
        df_emp = df_filtrado[df_filtrado['Empresa'] == empresa]
        
        if not df_emp.empty:
            total_emp = len(df_emp)
            comiss_emp = len(df_emp[df_emp['Status'] == 'Comissionado'])
            valid_emp = len(df_emp[df_emp['Status'] == 'Validado'])
            revis_emp = len(df_emp[df_emp['Status'] == 'Necessário Revisão'])
            pct_comiss = (comiss_emp / total_emp * 100) if total_emp > 0 else 0
            
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(*CORES_PDF['azul_energisa'])
            pdf.cell(0, 8, f'{empresa} - {total_emp} equipamentos', 0, 1, 'L')
            
            pdf.set_font('Arial', '', 9)
            pdf.cell(60, 6, f'Comissionados: {comiss_emp} ({pct_comiss:.0f}%)', 0, 0)
            pdf.cell(60, 6, f'Validados: {valid_emp}', 0, 0)
            pdf.cell(60, 6, f'Em Revisão: {revis_emp}', 0, 1)
            
            pdf.set_x(10)
            pdf.progress_bar(pct_comiss, 180)
            pdf.ln(5)
    
    pdf.ln(5)
    
    # ============================================
    # 4. RECOMENDAÇÕES
    # ============================================
    pdf.section_title('RECOMENDAÇÕES', '🎯')
    
    pdf.set_font('Arial', '', 10)
    
    recomendacoes = []
    
    if revisao > 0:
        recomendacoes.append(f'1. Priorizar correção dos {revisao} equipamentos em revisão')
    
    pendentes_validacao = comissionados - validados
    if pendentes_validacao > 0:
        recomendacoes.append(f'2. Acelerar validação dos {pendentes_validacao} equipamentos comissionados pendentes')
    
    df_eto = df_filtrado[df_filtrado['Empresa'] == 'ETO']
    df_emt = df_filtrado[df_filtrado['Empresa'] == 'EMT']
    pct_revisao_eto = (len(df_eto[df_eto['Status'] == 'Necessário Revisão']) / len(df_eto) * 100) if len(df_eto) > 0 else 0
    pct_revisao_emt = (len(df_emt[df_emt['Status'] == 'Necessário Revisão']) / len(df_emt) * 100) if len(df_emt) > 0 else 0
    
    if pct_revisao_eto > pct_revisao_emt and pct_revisao_eto > 5:
        recomendacoes.append('3. Foco especial na unidade ETO - maior índice de revisão')
    
    if len(recomendacoes) == 0:
        recomendacoes.append('✅ Todos os indicadores estão dentro da meta! Continue acompanhando.')
    
    for rec in recomendacoes:
        pdf.cell(0, 8, rec, 0, 1, 'L')
    
    pdf.ln(10)
    
    # ============================================
    # 5. HORÁRIOS EM TEMPO REAL
    # ============================================
    pdf.section_title('HORÁRIOS EM TEMPO REAL', '🕐')
    
    utc_now = datetime.now(timezone.utc)
    regioes = {
        'Brasília, Brasil': {'offset': -3, 'desc': ''},
        'Cuiabá, Brasil': {'offset': -4, 'desc': 'Menos 1 h'},
        'Porto Velho, Brasil': {'offset': -4, 'desc': 'Menos 1 h'},
        'Acre, Brasil': {'offset': -5, 'desc': 'Menos 2 h'}
    }
    
    pdf.set_font('Arial', '', 9)
    
    for regiao, info in regioes.items():
        local_time = utc_now + timedelta(hours=info['offset'])
        hora = local_time.strftime('%H:%M')
        data = local_time.strftime('%d/%m/%Y')
        
        pdf.set_x(10)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(45, 6, regiao, 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(20, 6, hora, 0, 0)
        if info['desc']:
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(25, 6, info['desc'], 0, 0)
        pdf.set_font('Arial', '', 8)
        pdf.cell(40, 6, data, 0, 1)
    
    pdf.ln(5)
    
    # ============================================
    # 6. TIPOS DE EQUIPAMENTO
    # ============================================
    if 'Tipo' in df_filtrado.columns:
        pdf.section_title('TIPOS DE EQUIPAMENTO', '🔧')
        
        tipo_counts = df_filtrado['Tipo'].value_counts().head(6)
        
        for tipo, qtd in tipo_counts.items():
            pct = (qtd / total * 100) if total > 0 else 0
            pdf.set_font('Arial', '', 10)
            pdf.cell(50, 8, str(tipo), 0, 0)
            pdf.cell(20, 8, f'{qtd} ({pct:.0f}%)', 0, 1)
            pdf.set_x(10)
            pdf.progress_bar(pct, 150)
            pdf.ln(2)
    
    # Gerar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name


def adicionar_botao_pdf(df_filtrado):
    """
    Adiciona botão no Streamlit para gerar e baixar o PDF
    """
    
    if st.button("📄 Gerar Relatório Executivo PDF", use_container_width=True, key="btn_gerar_pdf"):
        if df_filtrado.empty:
            st.warning("⚠️ Não há dados para gerar o relatório com os filtros selecionados.")
            return
        
        with st.spinner("🔄 Gerando relatório PDF... Aguarde um momento."):
            try:
                pdf_path = gerar_relatorio_pdf(df_filtrado)
                
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                st.success("✅ Relatório gerado com sucesso!")
                
                st.download_button(
                    label="📥 Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_comissionamento_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_download_pdf"
                )
                
                os.unlink(pdf_path)
                
            except ImportError:
                st.error("❌ Biblioteca 'fpdf2' não instalada.")
                st.code("pip install fpdf2", language="bash")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {str(e)}")
