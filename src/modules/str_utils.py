#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias de texto

# Funções utilitárias para limpar texto
def wrap_label_by_words(text, max_line_length=20):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line + " " + word) <= max_line_length:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    return "<br>".join(lines)

# Função utilitária para truncar texto
def truncate_label(text, maxlen=40):
    if len(text) <= maxlen:
        return text
    truncated = text[:maxlen].rstrip()
    if " " not in truncated:
        return truncated[:maxlen-1] + "…"
    # Remove a última palavra cortada
    truncated = truncated[:truncated.rfind(" ")]
    return truncated + "…"