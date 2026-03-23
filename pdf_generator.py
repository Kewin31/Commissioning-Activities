# ============================================
# 1. PANORAMA GERAL - CARDS CORRIGIDOS
# ============================================
y_pos = 55

pdf.set_y(y_pos)
pdf.set_font('Arial', 'B', 12)
pdf.set_text_color(0, 89, 115)
pdf.cell(0, 8, '1. PANORAMA GERAL', 0, 1, 'L')
pdf.set_draw_color(2, 138, 159)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())

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

# Cards em grid 3x2
card_y = 78

# Linha 1 - Card 1: TOTAL
pdf.set_fill_color(240, 248, 255)
pdf.rect(10, card_y, 58, 35, 'F')
pdf.set_xy(15, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(0, 89, 115)
pdf.cell(0, 5, 'TOTAL', 0, 1)
pdf.set_font('Arial', 'B', 22)
pdf.set_text_color(0, 89, 115)
pdf.cell(0, 10, str(total), 0, 1)

# Linha 1 - Card 2: DESENVOLVIDOS
pdf.set_fill_color(240, 248, 255)
pdf.rect(73, card_y, 58, 35, 'F')
pdf.set_xy(78, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 5, 'DESENVOLVIDOS', 0, 1)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, str(desenvolvidos), 0, 1)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 4, f'({pct_desenv:.0f}%)', 0, 1)

# Linha 1 - Card 3: COMISSIONADOS
pdf.set_fill_color(240, 248, 255)
pdf.rect(136, card_y, 58, 35, 'F')
pdf.set_xy(141, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 5, 'COMISSIONADOS', 0, 1)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 8, str(comissionados), 0, 1)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 4, f'({pct_comiss:.0f}%)', 0, 1)

# Linha 2 - Card 4: VALIDADOS
pdf.set_fill_color(240, 248, 255)
pdf.rect(10, card_y + 42, 58, 35, 'F')
pdf.set_xy(15, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 5, 'VALIDADOS', 0, 1)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 8, str(validados), 0, 1)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 4, f'({pct_valid:.0f}%)', 0, 1)

# Linha 2 - Card 5: EM REVISAO
pdf.set_fill_color(240, 248, 255)
pdf.rect(73, card_y + 42, 58, 35, 'F')
pdf.set_xy(78, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 5, 'EM REVISAO', 0, 1)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 8, str(revisao), 0, 1)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 4, f'({pct_revisao:.0f}%)', 0, 1)

# Linha 2 - Card 6: AGUARDANDO VALIDACAO
pdf.set_fill_color(240, 248, 255)
pdf.rect(136, card_y + 42, 58, 35, 'F')
pdf.set_xy(141, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 5, 'AGUARDANDO', 0, 1)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 8, str(pendentes), 0, 1)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 4, 'validacao', 0, 1)

# Continuar com as barras de progresso
bar_y = 165

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
