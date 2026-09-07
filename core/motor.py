"""
Motor de simulacao - FCFS, SJF e SRTF.

Ideia central: os tres algoritmos usam o MESMO laco (a mesma funcao
_executar). O que muda de um pra outro e so o criterio de escolha da
proxima tarefa e se ela pode ser interrompida no meio. Por isso da pra
reaproveitar quase tudo.
"""
from __future__ import annotations

from fractions import Fraction
from typing import List, Optional

from .modelo import Periodo, ResultadoSimulacao, Tarefa, para_fracao

UM = Fraction(1)
ZERO = Fraction(0)


class ErroSimulacao(Exception):
    pass


# ---------------------------------------------------------------
# funcao auxiliar: acrescenta um periodo na tarefa, mas se o ultimo
# periodo ja for do mesmo tipo e "colar" com esse novo (sem buraco no
# meio), so estica o fim dele em vez de criar um pedaco novo. Isso e
# so pra nao ficar com o diagrama cheio de bloquinhos picados quando
# a tarefa roda varias unidades seguidas.
# ---------------------------------------------------------------
def _acrescentar_periodo(tarefa: Tarefa, inicio: Fraction, fim: Fraction, tipo: str):
    if tarefa.periodos and tarefa.periodos[-1].tipo == tipo and tarefa.periodos[-1].fim == inicio:
        tarefa.periodos[-1].fim = fim
    else:
        tarefa.periodos.append(Periodo(inicio, fim, tipo))


# ---------------------------------------------------------------
# aqui e onde cada algoritmo se diferencia dos outros: cada funcao
# devolve uma "chave" de comparacao. Quem tiver a MENOR chave e quem
# ganha a CPU. O desempate (chegada, id) e sempre o mesmo nos tres,
# porque e a regra C3 do enunciado.
# ---------------------------------------------------------------
def _chave_fcfs(t: Tarefa):
    # FCFS: só importa quem chegou primeiro
    return (t.chegada, t.id)


def _chave_sjf(t: Tarefa):
    # SJF: quem tem a menor duracao TOTAL (tp) ganha
    return (t.tp, t.chegada, t.id)


def _chave_srtf(t: Tarefa):
    # SRTF: parecido com SJF, mas usa o que FALTA rodar (restante),
    # nao o tp original -> por isso ele preempta no meio
    return (t.restante, t.chegada, t.id)


# tabela que junta cada sigla com sua chave de escolha e se ele
# pode interromper quem esta rodando (preemptivo) ou nao
ALGORITMOS_GENERICOS = {
    "FCFS": dict(nome="First-Come, First-Served", chave=_chave_fcfs, preemptivo=False),
    "SJF": dict(nome="Shortest Job First", chave=_chave_sjf, preemptivo=False),
    "SRTF": dict(nome="Shortest Remaining Time First", chave=_chave_srtf, preemptivo=True),
}


def _melhor(tarefas: List[Tarefa], chave_fn) -> Tarefa:
    # pega a tarefa com a menor chave dentre as prontas
    return min(tarefas, key=chave_fn)


def _executar(tarefas: List[Tarefa], sigla: str, ttc: Fraction) -> ResultadoSimulacao:
    cfg = ALGORITMOS_GENERICOS[sigla]
    chave_fn = cfg["chave"]
    preemptivo = cfg["preemptivo"]

    # zera o estado de simulacao de cada tarefa (progresso, periodos etc),
    # pra caso essas mesmas tarefas ja tenham rodado em outro algoritmo antes
    for t in tarefas:
        t.reset()

    # pendentes = ainda nao chegaram / prontas = ja chegaram e esperando a vez
    pendentes = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    prontas: List[Tarefa] = []
    rodando: Optional[Tarefa] = None
    ultima_na_cpu: Optional[Tarefa] = None   # serve pra saber se precisa cobrar troca de contexto
    concluidas = 0
    total = len(tarefas)
    trocas_contexto = 0
    clock = ZERO   # relogio da simulacao (comeca em 0)

    def admitir():
        # move da lista de "pendentes" pra "prontas" quem ja chegou (chegada <= clock)
        nonlocal pendentes
        restam = []
        for t in pendentes:
            if t.chegada <= clock:
                prontas.append(t)
            else:
                restam.append(t)
        pendentes = restam

    protecao = 0
    while concluidas < total:
        # trava de seguranca: se rodar demais e nao terminar, algo esta errado
        # nos dados de entrada -> avisa em vez de travar o programa pra sempre
        protecao += 1
        if protecao > 5_000_000:
            raise ErroSimulacao("Simulacao nao converge (verifique os dados de entrada).")

        admitir()

        # ninguem rodando e ninguem pronto -> nao adianta ficar girando o
        # laco sem fazer nada, entao pula o relogio direto pra proxima chegada
        if rodando is None and not prontas:
            if not pendentes:
                raise ErroSimulacao("Impasse: nao ha tarefas prontas nem futuras.")
            clock = pendentes[0].chegada
            continue

        if rodando is None:
            # ninguem rodando ainda -> escolhe a melhor tarefa pronta
            rodando = _melhor(prontas, chave_fn)
            prontas.remove(rodando)
        elif preemptivo:
            # ja tem alguem rodando, mas o algoritmo permite interromper:
            # confere se apareceu alguem "melhor" que quem esta rodando agora
            admitir()
            if prontas:
                candidata = _melhor(prontas, chave_fn)
                if chave_fn(candidata) < chave_fn(rodando):
                    prontas.append(rodando)      # devolve quem estava rodando pra fila
                    prontas.remove(candidata)
                    rodando = candidata          # e coloca a nova no lugar

        # troca de contexto: toda vez que a tarefa que vai rodar agora e
        # diferente da que rodou no passo anterior (regra C4, vale ate na
        # primeira vez que qualquer coisa roda)
        if rodando is not ultima_na_cpu:
            if ttc > 0:
                _acrescentar_periodo(rodando, clock, clock + ttc, "CTX")
                clock += ttc
            trocas_contexto += 1
            ultima_na_cpu = rodando
            rodando.ultimo_despacho = clock

        # executa 1 unidade de tempo (a unidade basica do enunciado, C1)
        passo = min(UM, rodando.restante)
        inicio_passo = clock
        _acrescentar_periodo(rodando, inicio_passo, inicio_passo + passo, "EXEC")
        clock += passo
        rodando.progresso += passo
        rodando.restante -= passo

        # se zerou o que faltava, a tarefa terminou
        if rodando.restante == 0:
            rodando.conclusao = clock
            concluidas += 1
            rodando = None

    return ResultadoSimulacao(
        algoritmo=cfg["nome"], sigla=sigla, tarefas=tarefas, ttc=ttc,
        trocas_contexto=trocas_contexto,
    )


# ---------------------------------------------------------------
# funcoes que a interface (e os testes) realmente chamam - cada uma
# so aciona o _executar com a sigla certa
# ---------------------------------------------------------------
def fcfs(tarefas, ttc=ZERO):
    return _executar(tarefas, "FCFS", para_fracao(ttc))


def sjf(tarefas, ttc=ZERO):
    return _executar(tarefas, "SJF", para_fracao(ttc))


def srtf(tarefas, ttc=ZERO):
    return _executar(tarefas, "SRTF", para_fracao(ttc))

# =================================================================
# ROUND-ROBIN
#
# Diferente dos tres de cima, o RR nao escolhe por "quem tem a menor
# chave" - ele so roda quem esta na frente de uma fila (fila circular:
# quando estoura o quantum, a tarefa vai pro FIM da fila de novo).
# Por isso ele nao reaproveita o _executar, tem o laco dele mesmo.
# =================================================================
def round_robin(tarefas: List[Tarefa], tq, ttc=ZERO) -> ResultadoSimulacao:
    tq = para_fracao(tq)
    ttc = para_fracao(ttc)

    # regra R4 do enunciado: se o quantum fosse menor (ou igual) ao
    # custo da troca, a troca consumiria a fatia inteira e a tarefa
    # nunca faria trabalho de verdade -> tem que recusar isso
    if tq <= ttc:
        raise ErroSimulacao(
            "O quantum precisa ser maior que o custo da troca de contexto "
            "(senao a troca consome a fatia inteira e nenhum trabalho util e feito)."
        )

    for t in tarefas:
        t.reset()

    pendentes = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    fila: List[Tarefa] = []          # a fila circular
    rodando: Optional[Tarefa] = None
    ultima_na_cpu: Optional[Tarefa] = None
    concluidas = 0
    total = len(tarefas)
    trocas_contexto = 0
    clock = ZERO

    def admitir():
        nonlocal pendentes
        restam = []
        for t in pendentes:
            if t.chegada <= clock:
                fila.append(t)
            else:
                restam.append(t)
        pendentes = restam

    protecao = 0
    while concluidas < total:
        protecao += 1
        if protecao > 5_000_000:
            raise ErroSimulacao("Simulacao nao converge (verifique os dados de entrada).")

        admitir()
        if rodando is None and not fila:
            if not pendentes:
                raise ErroSimulacao("Impasse no Round-Robin (verifique os dados de entrada).")
            clock = pendentes[0].chegada
            continue

        if rodando is None:
            # tira o primeiro da fila - e so isso, nao tem "melhor
            # candidato" no RR, e sempre quem esta na frente
            rodando = fila.pop(0)

        # troca de contexto: mesma regra C4 de antes
        houve_troca = rodando is not ultima_na_cpu
        if houve_troca:
            if ttc > 0:
                _acrescentar_periodo(rodando, clock, clock + ttc, "CTX")
                clock += ttc
            trocas_contexto += 1
            ultima_na_cpu = rodando
        rodando.ultimo_despacho = clock

        # aqui e o ponto mais delicado do RR (regra C5 do enunciado):
        # o custo da troca e DESCONTADO da fatia, nunca somado a ela.
        # entao se rodou com troca, sobra (tq - ttc) de trabalho util
        # nessa fatia; se nao teve troca (mesma tarefa de novo, sem
        # ninguem mais na fila), a fatia inteira (tq) e util.
        capacidade_util = (tq - ttc) if houve_troca else tq
        fatia = min(capacidade_util, rodando.restante)

        inicio_fatia = clock
        _acrescentar_periodo(rodando, inicio_fatia, inicio_fatia + fatia, "EXEC")
        clock += fatia
        rodando.progresso += fatia
        rodando.restante -= fatia

        if rodando.restante == 0:
            # terminou dentro dessa fatia -> acabou, nao volta pra fila
            rodando.conclusao = clock
            concluidas += 1
            rodando = None
        else:
            # estourou o quantum sem terminar -> volta pro FIM da fila,
            # mas so depois de admitir quem chegou exatamente agora
            # (regra C6: quem chegou nesse instante entra na fila antes
            # dela)
            admitir()
            fila.append(rodando)
            rodando = None

    return ResultadoSimulacao(
        algoritmo="Round-Robin", sigla="RR", tarefas=tarefas, ttc=ttc, tq=tq,
        trocas_contexto=trocas_contexto,
    )