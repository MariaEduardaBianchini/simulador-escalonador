"""
Desenha o diagrama de tempo (Gantt) de um resultado de simulacao usando
so tkinter.Canvas
"""
from __future__ import annotations

import tkinter as tk
from fractions import Fraction

# paleta (combinando com gui/tema.py)
COR_EXEC = "#4F46E5"          # indigo
COR_CTX = "#F59E0B"           # ambar
COR_BLOQ_DIRETO = "#FB923C"   # laranja
COR_BLOQ_INVERSAO = "#DC2626"  # vermelho
COR_TEXTO = "#1E293B"
COR_TEXTO_MUTED = "#64748B"
COR_GRADE = "#E2E8F0"
COR_FAIXA = "#F8FAFC"
COR_BORDA = "#CBD5E1"

ALTURA_LINHA = 38       # altura de cada linha (uma por tarefa)
MARGEM_ESQUERDA = 78    # espaco reservado pro rotulo "T1", "T2" etc
MARGEM_TOPO = 14
MARGEM_DIREITA = 150    # espaco reservado pras metricas (tt=.. tw=..)
ALTURA_EIXO = 22        # faixa dos numeros do eixo do tempo
ALTURA_LEGENDA = 30     # faixa da legenda - separada do eixo, pra nao sobrepor
MARGEM_BAIXO = ALTURA_EIXO + ALTURA_LEGENDA + 14


def _fmt(valor: Fraction) -> str:
    # mostra "5" em vez de "5.00" quando o numero e inteiro
    f = float(valor)
    if f == int(f):
        return str(int(f))
    return f"{f:.2f}".rstrip("0").rstrip(".")


def _arredondado(canvas, x0, y0, x1, y1, r, **kw):
    """Desenha um retangulo com cantos arredondados - o Canvas nao tem
    esse recurso pronto, entao monta um poligono com curva suavizada."""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    if r <= 0:
        canvas.create_rectangle(x0, y0, x1, y1, **kw)
        return
    pontos = [
        x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
        x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
        x0, y1, x0, y1 - r, x0, y0 + r, x0, y0,
    ]
    canvas.create_polygon(pontos, smooth=True, splinesteps=6, **kw)


def desenhar_gantt(canvas: tk.Canvas, resultado, escala_px: float = 28.0):
    """Redesenha `canvas` do zero com o diagrama de tempo de `resultado`."""
    canvas.delete("all")
    tarefas = sorted(resultado.tarefas, key=lambda t: t.id)
    if not tarefas:
        return

    tempo_max = resultado.tempo_total()
    tempo_max = max(tempo_max, Fraction(1))
    largura_util = float(tempo_max) * escala_px
    largura_total = MARGEM_ESQUERDA + largura_util + MARGEM_DIREITA
    altura_grafico = MARGEM_TOPO + ALTURA_LINHA * len(tarefas)
    altura_total = altura_grafico + MARGEM_BAIXO

    # scrollregion e o que faz as barras de rolagem funcionarem quando
    # o diagrama e maior que a area visivel
    canvas.config(scrollregion=(0, 0, largura_total, altura_total))

    def x(t):
        # converte um instante de tempo pra posicao horizontal em pixel
        return MARGEM_ESQUERDA + float(t) * escala_px

    # faixas de fundo alternadas, so pra facilitar acompanhar a linha
    # de cada tarefa com o olho (linha 1 branca, linha 2 cinza clarinho...)
    for idx in range(len(tarefas)):
        if idx % 2 == 1:
            y0 = MARGEM_TOPO + idx * ALTURA_LINHA
            canvas.create_rectangle(
                MARGEM_ESQUERDA, y0, largura_total - MARGEM_DIREITA, y0 + ALTURA_LINHA,
                fill=COR_FAIXA, outline="",
            )

    # grade vertical + numeros do eixo do tempo
    passo = 1 if tempo_max <= 40 else max(1, round(float(tempo_max) / 40))
    y_eixo = altura_grafico + ALTURA_EIXO - 6
    tt = 0
    while tt <= float(tempo_max) + 1e-9:
        xx = x(tt)
        canvas.create_line(xx, MARGEM_TOPO, xx, altura_grafico, fill=COR_GRADE)
        canvas.create_text(xx, y_eixo, text=str(tt), fill=COR_TEXTO_MUTED, font=("Segoe UI", 8))
        tt += passo
    canvas.create_line(MARGEM_ESQUERDA, altura_grafico, largura_total - MARGEM_DIREITA, altura_grafico, fill=COR_BORDA)

    # uma linha por tarefa, com as barras dela
    for idx, tarefa in enumerate(tarefas):
        y0 = MARGEM_TOPO + idx * ALTURA_LINHA
        y1 = y0 + ALTURA_LINHA
        ymeio = (y0 + y1) / 2
        canvas.create_text(10, ymeio, text=f"T{tarefa.id}", anchor="w", font=("Segoe UI", 10, "bold"), fill=COR_TEXTO)

        # periodos normais (execucao e troca de contexto) - o BLOQ e
        # desenhado a parte, porque a lista de bloqueios da tarefa tem
        # a informacao extra de "direto ou inversao" que o Periodo sozinho
        # nao guarda
        for periodo in tarefa.periodos:
            if periodo.tipo == "BLOQ":
                continue
            cor = COR_EXEC if periodo.tipo == "EXEC" else COR_CTX
            x0, x1 = x(periodo.inicio), x(periodo.fim)
            _arredondado(canvas, x0 + 1, y0 + 6, max(x1, x0 + 2) - 1, y1 - 6, 3, fill=cor, outline=cor)
            if periodo.tipo == "CTX" and (x1 - x0) > 14:
                canvas.create_text((x0 + x1) / 2, ymeio, text="ctx", font=("Segoe UI", 7), fill="#7C4A03")

        # bloqueios (R5): laranja = bloqueio direto, vermelho = inversao
        for inicio, fim, tipo in tarefa.bloqueios:
            cor = COR_BLOQ_DIRETO if tipo == "DIRETO" else COR_BLOQ_INVERSAO
            x0, x1 = x(inicio), x(fim)
            _arredondado(canvas, x0 + 1, y0 + 11, max(x1, x0 + 2) - 1, y1 - 11, 2, fill=cor, outline=cor)

        # numeros de tt/tw ao lado direito da barra
        tt_ = tarefa.tempo_execucao()
        tw_ = tarefa.tempo_espera()
        texto = f"tt = {_fmt(tt_)}    tw = {_fmt(tw_)}"
        canvas.create_text(largura_total - MARGEM_DIREITA + 10, ymeio, text=texto, anchor="w",
                            font=("Segoe UI", 9), fill=COR_TEXTO_MUTED)

    # legenda - fica na propria faixa, abaixo do eixo do tempo (nunca
    # em cima dele, foi um bug que ja corrigimos antes)
    ly = altura_grafico + ALTURA_EIXO + 8
    itens = [(COR_EXEC, "Execução"), (COR_CTX, "Troca de contexto"),
             (COR_BLOQ_DIRETO, "Bloqueio direto"), (COR_BLOQ_INVERSAO, "Inversão de prioridade")]
    lx = MARGEM_ESQUERDA
    for cor, rotulo in itens:
        canvas.create_rectangle(lx, ly, lx + 12, ly + 12, fill=cor, outline=cor)
        largura_rotulo = 7 * len(rotulo)
        canvas.create_text(lx + 17, ly + 6, text=rotulo, anchor="w", font=("Segoe UI", 9), fill=COR_TEXTO_MUTED)
        lx += 17 + largura_rotulo + 22