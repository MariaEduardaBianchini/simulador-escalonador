"""
Paleta de cores e estilos do ttk, num lugar so - assim a aparencia fica
consistente em toda a interface sem repetir a mesma cor em varios
arquivos. Nao usa nenhuma biblioteca externa, so tkinter/ttk mesmo.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ---- paleta ----------------------------------------------------------
BG = "#FFFFFF"            # fundo geral da janela - branco
BG_CARTAO = "#FFFFFF"     # fundo dos "cartoes" (LabelFrame, tabelas)
BORDA = "#E0E0E0"
TEXTO = "#222222"
TEXTO_MUTED = "#6B6B6B"

# cores dos botoes - mantidas como estavam
PRIMARIA = "#F472B6"       # rosa - acao principal (Simular, Adicionar)
PRIMARIA_HOVER = "#EC4899"
SECUNDARIA = "#FBCFE8"     # rosa bem claro - acoes auxiliares (sortear)
SECUNDARIA_HOVER = "#F9A8D4"
SUCESSO = "#4CAF7D"
SUCESSO_HOVER = "#3B9067"
PERIGO = "#E1618A"
PERIGO_HOVER = "#C94973"
NEUTRO = "#8C8C8C"
NEUTRO_HOVER = "#6B6B6B"

FONTE = "Arial"


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
    estilo.configure("TNotebook.Tab", background="#F0F0F0", foreground=TEXTO_MUTED,
                      padding=(16, 9), font=_fonte(10, "bold"), borderwidth=0)
    estilo.map("TNotebook.Tab",
               background=[("selected", BG_CARTAO)],
               foreground=[("selected", TEXTO)])

    estilo.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=BORDA, lightcolor=BORDA,
                      darkcolor=BORDA, padding=6, relief="solid", borderwidth=1)
    estilo.configure("TCombobox", fieldbackground="#FFFFFF", padding=5)
    estilo.configure("TCheckbutton", background=BG, font=_fonte(10))
    estilo.configure("TRadiobutton", background=BG, font=_fonte(10))

    estilo.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                      foreground=TEXTO, rowheight=28, font=_fonte(10), borderwidth=0)
    estilo.configure("Treeview.Heading", background="#F0F0F0", foreground=TEXTO,
                      font=_fonte(10, "bold"), relief="flat")
    estilo.map("Treeview", background=[("selected", "#E8E8E8")], foreground=[("selected", TEXTO)])

    # gera um estilo de botao colorido pra cada "papel" (primario, de
    # sucesso, de perigo etc) em vez de definir a cor em cada botao
    # individualmente na tela - cores dos botoes mantidas
    def _botao(nome, cor, cor_hover, fg="#FFFFFF"):
        estilo.configure(f"{nome}.TButton", background=cor, foreground=fg,
                          font=_fonte(10, "bold"), padding=(14, 8), borderwidth=0, focusthickness=0)
        estilo.map(f"{nome}.TButton",
                   background=[("active", cor_hover), ("pressed", cor_hover)],
                   foreground=[("disabled", "#CCCCCC")])

    _botao("Primaria", PRIMARIA, PRIMARIA_HOVER)
    _botao("Secundaria", SECUNDARIA, SECUNDARIA_HOVER, fg=TEXTO)
    _botao("Sucesso", SUCESSO, SUCESSO_HOVER)
    _botao("Perigo", PERIGO, PERIGO_HOVER)
    _botao("Neutro", NEUTRO, NEUTRO_HOVER)

    return estilo