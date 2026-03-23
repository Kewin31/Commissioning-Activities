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

# Posição inicial dos cards
card_y = 78

# ============================================
# CARD 1: TOTAL
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(10, card_y, 58, 35, 'F')
# Título
pdf.set_xy(15, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(0, 89, 115)
pdf.cell(0, 5, 'TOTAL', 0, 1)
# Valor
pdf.set_xy(15, card_y + 15)
pdf.set_font('Arial', 'B', 22)
pdf.set_text_color(0, 89, 115)
pdf.cell(0, 10, str(total), 0, 1)
# Percentual
pdf.set_xy(15, card_y + 27)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 4, f'({pct_desenv:.0f}%)', 0, 1)

# ============================================
# CARD 2: DESENVOLVIDOS
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(73, card_y, 58, 35, 'F')
# Título
pdf.set_xy(78, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 5, 'DESENVOLVIDOS', 0, 1)
# Valor
pdf.set_xy(78, card_y + 15)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, str(desenvolvidos), 0, 1)
# Percentual
pdf.set_xy(78, card_y + 27)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 4, f'({pct_desenv:.0f}%)', 0, 1)

# ============================================
# CARD 3: COMISSIONADOS
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(136, card_y, 58, 35, 'F')
# Título
pdf.set_xy(141, card_y + 5)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 5, 'COMISSIONADOS', 0, 1)
# Valor
pdf.set_xy(141, card_y + 15)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 8, str(comissionados), 0, 1)
# Percentual
pdf.set_xy(141, card_y + 27)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(2, 138, 159)
pdf.cell(0, 4, f'({pct_comiss:.0f}%)', 0, 1)

# ============================================
# CARD 4: VALIDADOS (segunda linha)
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(10, card_y + 42, 58, 35, 'F')
# Título
pdf.set_xy(15, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 5, 'VALIDADOS', 0, 1)
# Valor
pdf.set_xy(15, card_y + 57)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 8, str(validados), 0, 1)
# Percentual
pdf.set_xy(15, card_y + 69)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(46, 125, 50)
pdf.cell(0, 4, f'({pct_valid:.0f}%)', 0, 1)

# ============================================
# CARD 5: EM REVISAO
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(73, card_y + 42, 58, 35, 'F')
# Título
pdf.set_xy(78, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 5, 'EM REVISAO', 0, 1)
# Valor
pdf.set_xy(78, card_y + 57)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 8, str(revisao), 0, 1)
# Percentual
pdf.set_xy(78, card_y + 69)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(245, 124, 0)
pdf.cell(0, 4, f'({pct_revisao:.0f}%)', 0, 1)

# ============================================
# CARD 6: AGUARDANDO
# ============================================
pdf.set_fill_color(240, 248, 255)
pdf.rect(136, card_y + 42, 58, 35, 'F')
# Título
pdf.set_xy(141, card_y + 47)
pdf.set_font('Arial', 'B', 9)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 5, 'AGUARDANDO', 0, 1)
# Valor
pdf.set_xy(141, card_y + 57)
pdf.set_font('Arial', 'B', 18)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 8, str(pendentes), 0, 1)
# Texto secundário
pdf.set_xy(141, card_y + 69)
pdf.set_font('Arial', '', 7)
pdf.set_text_color(198, 40, 40)
pdf.cell(0, 4, 'validacao', 0, 1)

# Continuar com as barras de progresso
bar_y = 165
