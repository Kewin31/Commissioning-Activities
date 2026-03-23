# pdf_generator.py - Versão Corrigida (sem desempacotamento de tuplas)
import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

# Cores no formato RGB para o PDF
AZUL_ENERGISA = (0, 89, 115)
AZUL_CLARO = (2, 138, 159)
VERDE = (46, 125, 50)
LARANJA = (245, 124, 0)
VERMELHO = (198, 40, 40)
CINZA = (100, 100, 100)
CINZA_CLARO = (230, 230, 230)

# Cores para os status
CORES = {
    'Desenvolvido': '#2E7D32',
    'Comissionado': '#028a9f',
    'Validado': '#005973',
    'Necessário Revisão': '#F57C00',
    'Pendente': '#C62828',
}

class PDFRelatorioEmpresa(FPDF):
    """Classe personalizada para relatório por empresa"""
    
    def __init__(self, empresa):
        super().__init__()
        self.empresa = empresa
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """Cabeçalho do relatório"""
        # Tentar adicionar logo da Energisa
        try:
            for logo_path in ["Logo_Energisa.png", "logo_energisa.png", "energisa.png"]:
                if os.path.exists(logo_path):
                    self.image(logo_path, x=10, y=8, w=25)
                    break
        except:
            pass
        
        # Título
        self.set_font('Arial', 'B', 18)
        self.set_text_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
        self.cell(0, 10, 'RELATORIO EXECUTIVO - COMISSIONAMENTO SCADA', 0, 1, 'C')
        
        # Subtítulo com a empresa
        self.set_font('Arial', 'B', 14)
        self.set_text_color(AZUL_CLARO[0], AZUL_CLARO[1], AZUL_CLARO[2])
        self.cell(0, 8, f'UNIDADE {self.empresa}', 0, 1, 'C')
        
        # Linha separadora
        self.set_draw_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
        self.line(10, 40, 200, 40)
        
        # Data
        self.set_y(45)
        self.set_font('Arial', '', 9)
        self.set_text_color(CINZA[0], CINZA[1], CINZA[2])
        self.cell(0, 5, f'Data de emissao: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
        
        self.ln(5)
    
    def footer(self):
        """Rodapé do relatório"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(CINZA[0], CINZA[1], CINZA[2])
        self.cell(0, 10, f'Energisa - Comissionamento SCADA | Unidade {self.empresa} | Pagina {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        """Título de seção"""
        self.set_font('Arial', 'B', 12)
        self.set_text_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(AZUL_CLARO[0], AZUL_CLARO[1], AZUL_CLARO[2])
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)
    
    def metric_card(self, label, value, sublabel=None, color=None):
        """Card de métrica"""
        if color is None:
            color = AZUL_ENERGISA
        
        self.set_font('Arial', 'B', 20)
        self.set_text_color(color[0], color[1], color[2])
        self.cell(45, 15, str(value), 0, 0, 'C')
        self.set_font('Arial', '', 8)
        self.set_text_color(CINZA[0], CINZA[1], CINZA[2])
        self.cell(45, 15, label, 0, 0, 'C')
        if sublabel:
            self.set_font('Arial', 'I', 7)
            self.cell(45, 15, sublabel, 0, 1, 'C')
        else:
            self.cell(45, 15, '', 0, 1)
    
    def progress_bar(self, percentage, width=150, height=6, color=None):
        """Barra de progresso"""
        if color is None:
            color = AZUL_CLARO
        
        x = self.get_x()
        y = self.get_y()
        
        self.set_fill_color(CINZA_CLARO[0], CINZA_CLARO[1], CINZA_CLARO[2])
        self.rect(x, y, width, height, 'F')
        
        self.set_fill_color(color[0], color[1], color[2])
        self.rect(x, y, width * (percentage / 100), height, 'F')
        
        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        self.set_xy(x + width + 5, y - 2)
        self.cell(20, 10, f'{percentage:.1f}%', 0, 1)
        
        self.set_y(y + height + 5)
    
    def add_chart_text_alternative(self, title, data):
        """Adiciona alternativa textual para gráficos"""
        self.set_font('Arial', 'B', 9)
        self.set_text_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
        self.cell(0, 6, f'{title}:', 0, 1, 'L')
        self.set_font('Arial', '', 8)
        self.set_text_color(CINZA[0], CINZA[1], CINZA[2])
        
        for key, value in data.items():
            self.cell(0, 5, f'  • {key}: {value}', 0, 1, 'L')
        self.ln(5)


def gerar_relatorio_empresa(df_filtrado, empresa):
    """
    Gera relatório PDF para uma empresa específica
    """
    # Filtrar dados da empresa
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa].copy()
    
    if df_empresa.empty:
        raise ValueError(f"Nao ha dados para a empresa {empresa}")
    
    # Criar PDF
    pdf = PDFRelatorioEmpresa(empresa)
    pdf.add_page()
    
    # ============================================
    # 1. ANALISE DA EMPRESA
    # ============================================
    pdf.section_title('1. ANALISE DA EMPRESA')
    
    total = len(df_empresa)
    desenvolvidos = len(df_empresa[df_empresa['Status'] == 'Desenvolvido'])
    comissionados = len(df_empresa[df_empresa['Status'] == 'Comissionado'])
    validados = len(df_empresa[df_empresa['Status'] == 'Validado'])
    revisao = len(df_empresa[df_empresa['Status'] == 'Necessário Revisão'])
    pendentes = comissionados - validados
    
    pct_comiss = (comissionados / total * 100) if total > 0 else 0
    pct_valid = (validados / total * 100) if total > 0 else 0
    pct_revisao = (revisao / total * 100) if total > 0 else 0
    pct_pendentes = (pendentes / total * 100) if total > 0 else 0
    
    # Cards de métricas
    pdf.set_font('Arial', '', 10)
    
    # Primeira linha
    pdf.set_x(10)
    pdf.metric_card('Equipamentos', total)
    pdf.metric_card('Comissionados', comissionados, f'({pct_comiss:.0f}%)', AZUL_CLARO)
    
    pdf.set_x(10)
    pdf.metric_card('Validados', validados, f'({pct_valid:.0f}%)', VERDE)
    pdf.metric_card('Em Revisao', revisao, f'({pct_revisao:.0f}%)', LARANJA)
    
    pdf.set_x(10)
    pdf.metric_card('Aguardando', pendentes, f'({pct_pendentes:.0f}%)', VERMELHO)
    
    pdf.ln(10)
    
    # Barras de progresso
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Comissionados:', 0, 0)
    pdf.set_x(55)
    pdf.progress_bar(pct_comiss, 140, AZUL_CLARO)
    
    pdf.cell(40, 8, 'Validados:', 0, 0)
    pdf.set_x(55)
    pdf.progress_bar(pct_valid, 140, VERDE)
    
    pdf.cell(40, 8, 'Em Revisao:', 0, 0)
    pdf.set_x(55)
    pdf.progress_bar(pct_revisao, 140, LARANJA)
    
    pdf.ln(15)
    
    # ============================================
    # 2. DISTRIBUICAO DO PORTFOLIO
    # ============================================
    pdf.section_title('2. DISTRIBUICAO DO PORTFOLIO')
    
    # Versão textual dos dados
    status_data = df_empresa['Status'].value_counts().to_dict()
    pdf.add_chart_text_alternative('Distribuicao por Status', status_data)
    
    pdf.ln(5)
    
    # ============================================
    # 3. TIPOS DE EQUIPAMENTOS
    # ============================================
    pdf.section_title('3. TIPOS DE EQUIPAMENTOS')
    
    if 'Tipo' in df_empresa.columns and not df_empresa['Tipo'].dropna().empty:
        tipo_data = df_empresa['Tipo'].value_counts().head(8).to_dict()
        pdf.add_chart_text_alternative('Tipos de Equipamento', tipo_data)
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, 'Nao ha dados de tipos de equipamento disponiveis.', 0, 1)
    
    pdf.ln(10)
    
    # ============================================
    # 4. PROGRESS TRACKER
    # ============================================
    pdf.section_title('4. PROGRESS TRACKER')
    
    total_comissionados = comissionados + validados
    taxa_desenv_para_comiss = (total_comissionados / desenvolvidos * 100) if desenvolvidos > 0 else 0
    taxa_comiss_para_valid = (validados / total_comissionados * 100) if total_comissionados > 0 else 0
    
    # ETAPA 1 - Desenvolvidos
    pdf.set_x(10)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 45, 55, 'F')
    pdf.set_xy(12, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'ETAPA 1', 0, 1)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
    pdf.cell(0, 10, str(desenvolvidos), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(CINZA[0], CINZA[1], CINZA[2])
    pdf.cell(0, 4, 'Desenvolvidos', 0, 1)
    pdf.cell(0, 4, 'Aguardando', 0, 1)
    pdf.cell(0, 4, 'comissionamento', 0, 1)
    pdf.set_y(pdf.get_y() + 40)
    
    # Seta
    pdf.set_xy(60, pdf.get_y() - 45)
    pdf.set_font('Arial', '', 18)
    pdf.cell(10, 10, '->', 0, 1)
    
    # ETAPA 2 - Comissionados
    pdf.set_xy(75, pdf.get_y() - 55)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(75, pdf.get_y(), 45, 55, 'F')
    pdf.set_xy(77, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'ETAPA 2', 0, 1)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(AZUL_CLARO[0], AZUL_CLARO[1], AZUL_CLARO[2])
    pdf.cell(0, 10, str(comissionados), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(CINZA[0], CINZA[1], CINZA[2])
    pdf.cell(0, 4, 'Comissionados', 0, 1)
    pdf.cell(0, 4, 'Aguardando', 0, 1)
    pdf.cell(0, 4, 'validacao', 0, 1)
    pdf.set_y(pdf.get_y() + 40)
    
    # Seta
    pdf.set_xy(125, pdf.get_y() - 45)
    pdf.set_font('Arial', '', 18)
    pdf.cell(10, 10, '->', 0, 1)
    
    # ETAPA 3 - Validados
    pdf.set_xy(140, pdf.get_y() - 55)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(140, pdf.get_y(), 45, 55, 'F')
    pdf.set_xy(142, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'ETAPA 3', 0, 1)
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(VERDE[0], VERDE[1], VERDE[2])
    pdf.cell(0, 10, str(validados), 0, 1)
    pdf.set_font('Arial', '', 7)
    pdf.set_text_color(CINZA[0], CINZA[1], CINZA[2])
    pdf.cell(0, 4, 'Validados', 0, 1)
    pdf.cell(0, 4, 'Processo', 0, 1)
    pdf.cell(0, 4, 'concluido', 0, 1)
    
    pdf.ln(65)
    
    # GARGALO
    pdf.set_x(10)
    pdf.set_fill_color(255, 240, 230)
    pdf.rect(10, pdf.get_y(), 180, 45, 'F')
    pdf.set_xy(12, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(LARANJA[0], LARANJA[1], LARANJA[2])
    pdf.cell(0, 6, 'GARGALO', 0, 1)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 8, f'{revisao} equipamentos em revisao', 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(CINZA[0], CINZA[1], CINZA[2])
    pdf.cell(0, 4, f'{pct_revisao:.1f}% do total de equipamentos', 0, 1)
    pdf.ln(50)
    
    # ============================================
    # 5. PERFORMANCE POR RESPONSAVEL
    # ============================================
    pdf.section_title('5. PERFORMANCE POR RESPONSAVEL')
    
    col_resp = 'Resp_Com'
    
    if col_resp in df_empresa.columns:
        df_resp = df_empresa[df_empresa[col_resp] != 'Não atribuído']
        
        if not df_resp.empty:
            # Comissionados por responsável
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(AZUL_ENERGISA[0], AZUL_ENERGISA[1], AZUL_ENERGISA[2])
            pdf.cell(0, 8, 'Comissionados por Responsavel', 0, 1)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(60, 8, 'Responsavel', 1, 0, 'C', 1)
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
                
                pdf.cell(60, 7, str(resp)[:25], 1, 0, 'L')
                pdf.cell(35, 7, str(total_resp), 1, 0, 'C')
                pdf.cell(35, 7, str(validados_resp), 1, 0, 'C')
                pdf.cell(45, 7, f'{taxa:.1f}%', 1, 1, 'C')
            
            pdf.ln(5)
            
            # Equipamentos em revisão
            df_revisao = df_empresa[df_empresa['Status'] == 'Necessário Revisão']
            
            if not df_revisao.empty:
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(LARANJA[0], LARANJA[1], LARANJA[2])
                pdf.cell(0, 8, 'Equipamentos em Revisao por Responsavel', 0, 1)
                
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(60, 8, 'Responsavel', 1, 0, 'C', 1)
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
                    
                    pdf.cell(60, 7, str(resp)[:25], 1, 0, 'L')
                    pdf.cell(35, 7, str(qtd), 1, 0, 'C')
                    pdf.cell(85, 7, equip_str[:45], 1, 1, 'L')
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
