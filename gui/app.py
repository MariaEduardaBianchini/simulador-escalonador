"""
Interface grafica do simulador - tkinter/ttk puro, sem dependencia
externa nenhuma.

A janela nunca fecha sozinha, nem diante de erro (R10) - por isso o
report_callback_exception la embaixo: qualquer erro que escape captura
vira uma caixinha de mensagem, em vez de derrubar o programa.
"""
from __future__ import annotations

import os
import sys
import traceback
import tkinter as tk
from fractions import Fraction
from tkinter import ttk, messagebox, filedialog

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from core.modelo import Tarefa
from core import validacao
from core.geracao import gerar_tarefas, salvar_cenario, carregar_cenario
from gui import tema


class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Escalonamento de Tarefas")
        self.geometry("1200x780")
        self.minsize(1000, 660)
        self.estilo = tema.aplicar_tema(self)

        # a lista de tarefas do cenario atual - as tres abas todas
        # compartilham essa mesma lista (por referencia)
        self.tarefas: list[Tarefa] = []

        self.report_callback_exception = self._tratar_excecao_tk

        cabecalho = ttk.Frame(self, padding=(20, 16, 20, 6))
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text="Simulador de Escalonamento", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            cabecalho,
            text="Aula 5/6 · FCFS · SJF · SRTF · Round-Robin · Prioridade cooperativa · Prioridade preemptiva",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.aba_tarefas = AbaTarefas(notebook, self)
        notebook.add(self.aba_tarefas, text="1 · Tarefas")
        # as abas "2 · Simular" e "3 · Comparar em lote" entram nos
        # proximos commits

    def _tratar_excecao_tk(self, exc, val, tb):
        traceback.print_exception(exc, val, tb)
        messagebox.showerror("Erro inesperado", f"{val}")

    def notificar_tarefas_alteradas(self):
        self.aba_tarefas.atualizar_lista()

    def proximo_id(self) -> int:
        # acha o menor id livre - assim, se voce remover a tarefa 2 e
        # adicionar outra, ela reusa o id 2 em vez de pular pro 6
        usados = {t.id for t in self.tarefas}
        candidato = 1
        while candidato in usados:
            candidato += 1
        return candidato


class AbaTarefas(ttk.Frame):
    """R2: entrada de tarefas (digitada ou sorteada) + salvar/recarregar."""

    def __init__(self, master, app: Aplicacao):
        super().__init__(master, padding=16)
        self.app = app
        self._indice_edicao = None
        self._montar()

    def _montar(self):
        cartao_form = ttk.LabelFrame(self, text="Nova tarefa / edição", padding=14)
        cartao_form.pack(fill="x", pady=(0, 12))
        ttk.Label(
            cartao_form,
            text="Ingresso, tempo de processamento e prioridade são obrigatórios. A seção crítica é\n"
                 "opcional e só é usada pela Prioridade preemptiva (início e duração do próprio processamento).",
            style="Subtitulo.TLabel", justify="left",
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        self.e_chegada = self._campo(cartao_form, "Ingresso", 1)
        self.e_duracao = self._campo(cartao_form, "Duração (tp)", 2)
        self.e_prioridade = self._campo(cartao_form, "Prioridade", 3)
        self.e_sc_inicio = self._campo(cartao_form, "Início SC (opc.)", 4)
        self.e_sc_duracao = self._campo(cartao_form, "Duração SC (opc.)", 5)

        botoes = ttk.Frame(cartao_form)
        botoes.grid(row=3, column=0, columnspan=6, sticky="w", pady=(12, 0))
        ttk.Button(botoes, text="+ Adicionar tarefa", style="Primaria.TButton",
                   command=self._adicionar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Salvar edição", style="Sucesso.TButton",
                   command=self._salvar_edicao).pack(side="left", padx=8)
        ttk.Button(botoes, text="Editar selecionada", style="Neutro.TButton",
                   command=self._carregar_para_edicao).pack(side="left", padx=8)
        ttk.Button(botoes, text="Remover selecionada", style="Perigo.TButton",
                   command=self._remover).pack(side="left", padx=8)
        ttk.Button(botoes, text="Limpar tudo", style="Neutro.TButton",
                   command=self._limpar).pack(side="left", padx=8)

        cartao_tabela = ttk.LabelFrame(self, text="Tarefas do cenário atual", padding=10)
        cartao_tabela.pack(fill="both", expand=True, pady=(0, 12))
        colunas = ("id", "chegada", "duracao", "prioridade", "sc")
        self.tabela = ttk.Treeview(cartao_tabela, columns=colunas, show="headings", height=9)
        for c, titulo, largura in [
            ("id", "ID", 60), ("chegada", "Ingresso", 100), ("duracao", "tp", 100),
            ("prioridade", "Prioridade", 100), ("sc", "Seção crítica", 200),
        ]:
            self.tabela.heading(c, text=titulo)
            self.tabela.column(c, width=largura, anchor="center")
        self.tabela.pack(fill="both", expand=True)

        rodape = ttk.Frame(self)
        rodape.pack(fill="x")
        ttk.Button(rodape, text="Sortear tarefas...", style="Secundaria.TButton",
                   command=self._abrir_sorteio).pack(side="left", padx=(0, 8))
        ttk.Button(rodape, text="Salvar cenário...", style="Neutro.TButton",
                   command=self._salvar_cenario).pack(side="left", padx=8)
        ttk.Button(rodape, text="Carregar cenário...", style="Neutro.TButton",
                   command=self._carregar_cenario).pack(side="left", padx=8)

    def _campo(self, parent, rotulo, col):
        ttk.Label(parent, text=rotulo).grid(row=1, column=col - 1, padx=6, sticky="w")
        e = ttk.Entry(parent, width=13, justify="center")
        e.grid(row=2, column=col - 1, padx=6, pady=(2, 0), sticky="w")
        return e

    def _limpar_formulario(self):
        for e in (self.e_chegada, self.e_duracao, self.e_prioridade, self.e_sc_inicio, self.e_sc_duracao):
            e.delete(0, tk.END)
        self._indice_edicao = None

    def _adicionar(self):
        try:
            chegada, duracao, prioridade, sc_i, sc_d = validacao.validar_tarefa(
                self.e_chegada.get(), self.e_duracao.get(), self.e_prioridade.get(),
                self.e_sc_inicio.get(), self.e_sc_duracao.get(),
            )
        except ValueError as e:
            messagebox.showerror("Valor inválido", str(e))
            return
        novo_id = self.app.proximo_id()
        self.app.tarefas.append(Tarefa(novo_id, chegada, duracao, prioridade, sc_i, sc_d))
        self._limpar_formulario()
        self.atualizar_lista()

    def _selecionada(self):
        sel = self.tabela.selection()
        if not sel:
            return None
        item_id = int(self.tabela.item(sel[0], "values")[0])
        for i, t in enumerate(self.app.tarefas):
            if t.id == item_id:
                return i
        return None

    def _carregar_para_edicao(self):
        idx = self._selecionada()
        if idx is None:
            messagebox.showinfo("Editar tarefa", "Selecione uma tarefa na tabela primeiro.")
            return
        t = self.app.tarefas[idx]
        self._limpar_formulario()
        self.e_chegada.insert(0, str(t.chegada))
        self.e_duracao.insert(0, str(t.tp))
        self.e_prioridade.insert(0, str(t.prioridade_base))
        if t.sc_inicio is not None:
            self.e_sc_inicio.insert(0, str(t.sc_inicio))
            self.e_sc_duracao.insert(0, str(t.sc_duracao))
        self._indice_edicao = idx

    def _salvar_edicao(self):
        if self._indice_edicao is None:
            messagebox.showinfo("Salvar edição", "Clique em \"Editar selecionada\" antes de salvar.")
            return
        try:
            chegada, duracao, prioridade, sc_i, sc_d = validacao.validar_tarefa(
                self.e_chegada.get(), self.e_duracao.get(), self.e_prioridade.get(),
                self.e_sc_inicio.get(), self.e_sc_duracao.get(),
            )
        except ValueError as e:
            messagebox.showerror("Valor inválido", str(e))
            return
        t = self.app.tarefas[self._indice_edicao]
        t.chegada = Fraction(chegada)
        t.tp = Fraction(duracao)
        t.prioridade_base = prioridade
        t.sc_inicio = Fraction(sc_i) if sc_i is not None else None
        t.sc_duracao = Fraction(sc_d) if sc_d is not None else None
        t.reset()
        self._limpar_formulario()
        self.atualizar_lista()

    def _remover(self):
        idx = self._selecionada()
        if idx is None:
            messagebox.showinfo("Remover tarefa", "Selecione uma tarefa na tabela primeiro.")
            return
        self.app.tarefas.pop(idx)
        self.atualizar_lista()

    def _limpar(self):
        if not self.app.tarefas:
            return
        if messagebox.askyesno("Limpar tudo", "Remover todas as tarefas do cenário atual?"):
            self.app.tarefas.clear()
            self.atualizar_lista()

    def atualizar_lista(self):
        self.tabela.delete(*self.tabela.get_children())
        for t in sorted(self.app.tarefas, key=lambda x: x.id):
            sc = f"[{t.sc_inicio}, {t.sc_inicio + t.sc_duracao})" if t.sc_inicio is not None else "—"
            self.tabela.insert("", "end", values=(t.id, t.chegada, t.tp, t.prioridade_base, sc))

    def _abrir_sorteio(self):
        JanelaSorteio(self, self.app)

    def _salvar_cenario(self):
        if not self.app.tarefas:
            messagebox.showinfo("Salvar cenário", "Não há tarefas para salvar.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar cenário", defaultextension=".json",
            filetypes=[("Cenário (JSON)", "*.json")],
        )
        if not caminho:
            return
        try:
            salvar_cenario(caminho, self.app.tarefas)
            messagebox.showinfo("Salvar cenário", "Cenário salvo com sucesso.")
        except OSError as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def _carregar_cenario(self):
        caminho = filedialog.askopenfilename(
            title="Carregar cenário", filetypes=[("Cenário (JSON)", "*.json")],
        )
        if not caminho:
            return
        try:
            tarefas = carregar_cenario(caminho)
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror("Erro ao carregar", f"Não foi possível carregar o cenário:\n{e}")
            return
        self.app.tarefas = tarefas
        self.atualizar_lista()


class JanelaSorteio(tk.Toplevel):
    def __init__(self, aba: AbaTarefas, app: Aplicacao):
        super().__init__(aba)
        self.aba = aba
        self.app = app
        self.title("Sortear tarefas")
        self.configure(bg=tema.BG)
        self.resizable(False, False)
        self.grab_set()  # trava a janela principal ate essa aqui fechar

        corpo = ttk.Frame(self, padding=18)
        corpo.pack(fill="both", expand=True)

        campos = [
            ("Quantidade de tarefas", "5"),
            ("Ingresso máximo", "8"),
            ("Duração máxima", "6"),
            ("Prioridade máxima", "5"),
        ]
        self.entradas = {}
        for i, (rotulo, padrao) in enumerate(campos):
            ttk.Label(corpo, text=rotulo).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=5)
            e = ttk.Entry(corpo, width=10, justify="center")
            e.insert(0, padrao)
            e.grid(row=i, column=1, pady=5)
            self.entradas[rotulo] = e

        self.var_sc = tk.BooleanVar(value=False)
        ttk.Checkbutton(corpo, text="Permitir seções críticas (para PRIOp)",
                        variable=self.var_sc).grid(row=len(campos), column=0, columnspan=2, sticky="w", pady=(6, 2))

        self.var_substituir = tk.BooleanVar(value=True)
        ttk.Checkbutton(corpo, text="Substituir as tarefas atuais",
                        variable=self.var_substituir).grid(row=len(campos) + 1, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Button(corpo, text="Sortear", style="Secundaria.TButton",
                   command=self._sortear).grid(row=len(campos) + 2, column=0, columnspan=2, pady=(14, 0))

    def _sortear(self):
        try:
            qtd = validacao.validar_inteiro_positivo(self.entradas["Quantidade de tarefas"].get(), "Quantidade de tarefas")
            cheg_max = validacao.validar_inteiro_nao_negativo(self.entradas["Ingresso máximo"].get(), "Ingresso máximo")
            dur_max = validacao.validar_inteiro_positivo(self.entradas["Duração máxima"].get(), "Duração máxima")
            prio_max = validacao.validar_inteiro_positivo(self.entradas["Prioridade máxima"].get(), "Prioridade máxima")
        except ValueError as e:
            messagebox.showerror("Valor inválido", str(e))
            return
        novas = gerar_tarefas(qtd, cheg_max, dur_max, prio_max, permitir_secao_critica=self.var_sc.get())
        if self.var_substituir.get():
            self.app.tarefas = novas
        else:
            base = self.app.proximo_id()
            for i, t in enumerate(novas):
                t.id = base + i
            self.app.tarefas.extend(novas)
        self.aba.atualizar_lista()
        self.destroy()


def iniciar_aplicacao():
    app = Aplicacao()
    app.mainloop()