"""
Modelo de dados do simulador: Tarefa, Periodo e o resultado de uma simulacao.

Todos os tempos internos usam fractions.Fraction para evitar erro de
arredondamento de ponto flutuante (importante porque tq e ttc podem ser
fracionarios). A conversao para float só acontece na hora de exibir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional


def para_fracao(valor) -> Fraction:
    """Converte int/float/str/Fraction para Fraction de forma segura."""
    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, int):
        return Fraction(valor)
    # str evita o ruido binario de float (Fraction(0.1) != Fraction("0.1"))
    return Fraction(str(valor))


@dataclass
class Periodo:
    """Um intervalo [inicio, fim) na linha do tempo de uma tarefa."""
    inicio: Fraction
    fim: Fraction
    tipo: str  # "EXEC", "CTX" (troca de contexto) ou "BLOQ" (suspensa por recurso)

    @property
    def duracao(self) -> Fraction:
        return self.fim - self.inicio


@dataclass(eq=False)
class Tarefa:
    id: int
    chegada: Fraction
    tp: Fraction                 # tempo de processamento total exigido
    prioridade_base: int
    sc_inicio: Optional[Fraction] = None   # progresso proprio em que pede o recurso
    sc_duracao: Optional[Fraction] = None  # por quanto tempo mantem o recurso

    # ---- estado mutavel durante uma simulacao (ver reset()) ----
    restante: Fraction = field(init=False)
    progresso: Fraction = field(init=False)
    periodos: list = field(init=False)
    conclusao: Optional[Fraction] = field(init=False, default=None)
    ultimo_despacho: Optional[Fraction] = field(init=False, default=None)
    tem_recurso: bool = field(init=False, default=False)
    prioridade_override: Optional[int] = field(init=False, default=None)
    bloqueios: list = field(init=False)  # lista de (inicio, fim, "DIRETO"/"INVERSAO")

    def __post_init__(self):
        self.chegada = para_fracao(self.chegada)
        self.tp = para_fracao(self.tp)
        if self.sc_inicio is not None:
            self.sc_inicio = para_fracao(self.sc_inicio)
            self.sc_duracao = para_fracao(self.sc_duracao)
        self.reset()

    def reset(self):
        """Restaura o estado antes de uma nova simulacao (mesmos dados de entrada)."""
        self.restante = self.tp
        self.progresso = Fraction(0)
        self.periodos = []
        self.conclusao = None
        self.ultimo_despacho = None
        self.tem_recurso = False
        self.prioridade_override = None
        self.bloqueios = []

    @property
    def tem_secao_critica(self) -> bool:
        return self.sc_inicio is not None

    def prioridade_atual(self) -> int:
        return self.prioridade_override if self.prioridade_override is not None else self.prioridade_base

    # ---- metricas (R3) ----
    def tempo_execucao(self) -> Optional[Fraction]:
        """tt = t_conclusao - t_ingresso"""
        if self.conclusao is None:
            return None
        return self.conclusao - self.chegada

    def tempo_espera(self) -> Optional[Fraction]:
        """tw = tt - tp  (convencao C8)"""
        tt = self.tempo_execucao()
        if tt is None:
            return None
        return tt - self.tp

    def primeira_execucao(self) -> Optional[Fraction]:
        """tempo ate a primeira execucao = t(1a exec) - t_ingresso"""
        for p in self.periodos:
            if p.tipo == "EXEC":
                return p.inicio - self.chegada
        return None

    def __repr__(self):
        return f"Tarefa(id={self.id}, chegada={self.chegada}, tp={self.tp}, prio={self.prioridade_base})"


@dataclass
class ResultadoSimulacao:
    algoritmo: str
    sigla: str
    tarefas: list
    ttc: Fraction
    tq: Optional[Fraction] = None
    protocolo_recurso: Optional[str] = None
    alpha_envelhecimento: Optional[Fraction] = None
    trocas_contexto: int = 0

    def media_tt(self) -> Fraction:
        vals = [t.tempo_execucao() for t in self.tarefas]
        return sum(vals) / len(vals)

    def media_tw(self) -> Fraction:
        vals = [t.tempo_espera() for t in self.tarefas]
        return sum(vals) / len(vals)

    def media_primeira_execucao(self) -> Fraction:
        vals = [t.primeira_execucao() for t in self.tarefas]
        return sum(vals) / len(vals)

    def eficiencia(self) -> Optional[Fraction]:
        """E = tq / (tq + ttc). So definida quando ha quantum (R4)."""
        if self.tq is None:
            return None
        return self.tq / (self.tq + self.ttc)

    def tempo_total(self) -> Fraction:
        fim = Fraction(0)
        for t in self.tarefas:
            for p in t.periodos:
                fim = max(fim, p.fim)
        return fim