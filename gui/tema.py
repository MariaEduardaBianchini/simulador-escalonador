"""
Paleta de cores e estilos do ttk, num lugar so - assim a aparencia fica
consistente em toda a interface sem repetir a mesma cor em varios
arquivos. Nao usa nenhuma biblioteca externa, so tkinter/ttk mesmo.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ---- paleta ----------------------------------------------------------
BG = "#F4F6FB"            # fundo geral da janela
BG_CARTAO = "#FFFFFF"     # fundo dos "cartoes" (LabelFrame, tabelas)
BORDA = "#E2E8F0"
TEXTO = "#1E293B"
TEXTO_MUTED = "#64748B"

PRIMARIA = "#4F46E5"       # indigo - acao principal (Simular, Adicionar)
PRIMARIA_HOVER = "#4338CA"
SECUNDARIA = "#0EA5E9"     # azul-ceu - acoes auxiliares (sortear)
SECUNDARIA_HOVER = "#0284C7"
SUCESSO = "#16A34A"
SUCESSO_HOVER = "#15803D"
PERIGO = "#DC2626"
PERIGO_HOVER = "#B91C1C"
NEUTRO = "#64748B"
NEUTRO_HOVER = "#475569"

FONTE = "Segoe UI"


def _fonte(tam, peso="normal"):
    return (FONTE, tam, peso) if peso != "normal" else (FONTE, tam)


def aplicar_tema(root: tk.Tk):
    root.configure(bg=BG)
    estilo = ttk.Style(root)
    try:
        # "clam" e o tema base que mais aceita customizacao de cor no ttk -
        # o tema padrao do sistema (Windows/Mac) ignora boa parte disso
        estilo.theme_use("clam")
    except tk.TclError:
        pass

    estilo.configure(".", background=BG, foreground=TEXTO, font=_fonte(10))
    estilo.configure("TFrame", background=BG)
    estilo.configure("Cartao.TFrame", background=BG_CARTAO)

    estilo.configure("TLabelframe", background=BG, bordercolor=BORDA, relief="solid", borderwidth=1)
    estilo.configure("TLabelframe.Label", background=BG, foreground=TEXTO, font=_fonte(11, "bold"))
    estilo.configure("TLabel", background=BG, foreground=TEXTO, font=_fonte(10))
    estilo.configure("Titulo.TLabel", background=BG, foreground=TEXTO, font=_fonte(19, "bold"))
    estilo.configure("Subtitulo.TLabel", background=BG, foreground=TEXTO_MUTED, font=_fonte(10))
    estilo.configure("Resumo.TLabel", background=BG_CARTAO, foreground=TEXTO, font=_fonte(11, "bold"))
    estilo.configure("Nota.TLabel", background=BG, foreground=TEXTO_MUTED, font=(FONTE, 9, "italic"))

    estilo.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(4, 6, 4, 0))
    estilo.configure("TNotebook.Tab", background="#E2E8F0", foreground=TEXTO_MUTED,
                      padding=(16, 9), font=_fonte(10, "bold"), borderwidth=0)
    estilo.map("TNotebook.Tab",
               background=[("selected", BG_CARTAO)],
               foreground=[("selected", PRIMARIA)])

    estilo.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=BORDA, lightcolor=BORDA,
                      darkcolor=BORDA, padding=6, relief="solid", borderwidth=1)
    estilo.configure("TCombobox", fieldbackground="#FFFFFF", padding=5)
    estilo.configure("TCheckbutton", background=BG, font=_fonte(10))
    estilo.configure("TRadiobutton", background=BG, font=_fonte(10))

    estilo.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                      foreground=TEXTO, rowheight=28, font=_fonte(10), borderwidth=0)
    estilo.configure("Treeview.Heading", background="#EEF1F8", foreground=TEXTO,
                      font=_fonte(10, "bold"), relief="flat")
    estilo.map("Treeview", background=[("selected", "#E0E7FF")], foreground=[("selected", PRIMARIA)])

    # gera um estilo de botao colorido pra cada "papel" (primario, de
    # sucesso, de perigo etc) em vez de definir a cor em cada botao
    # individualmente na tela
    def _botao(nome, cor, cor_hover, fg="#FFFFFF"):
        estilo.configure(f"{nome}.TButton", background=cor, foreground=fg,
                          font=_fonte(10, "bold"), padding=(14, 8), borderwidth=0, focusthickness=0)
        estilo.map(f"{nome}.TButton",
                   background=[("active", cor_hover), ("pressed", cor_hover)],
                   foreground=[("disabled", "#A0AEC0")])

    _botao("Primaria", PRIMARIA, PRIMARIA_HOVER)
    _botao("Secundaria", SECUNDARIA, SECUNDARIA_HOVER)
    _botao("Sucesso", SUCESSO, SUCESSO_HOVER)
    _botao("Perigo", PERIGO, PERIGO_HOVER)
    _botao("Neutro", NEUTRO, NEUTRO_HOVER)

    return estilo