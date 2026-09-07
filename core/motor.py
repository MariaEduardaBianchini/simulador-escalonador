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
def _chave_fcfs(t: Tarefa, clock, alpha):
    # FCFS: só importa quem chegou primeiro (clock/alpha nao sao usados
    # aqui, mas a assinatura precisa ser igual pra todo mundo)
    return (t.chegada, t.id)


def _chave_sjf(t: Tarefa, clock, alpha):
    # SJF: quem tem a menor duracao TOTAL (tp) ganha
    return (t.tp, t.chegada, t.id)


def _chave_srtf(t: Tarefa, clock, alpha):
    # SRTF: parecido com SJF, mas usa o que FALTA rodar (restante),
    # nao o tp original -> por isso ele preempta no meio
    return (t.restante, t.chegada, t.id)

def _prioridade_efetiva(tarefa: Tarefa, clock, alpha) -> Fraction:
    # sem envelhecimento configurado, a prioridade efetiva e so a atual
    # (base, ou elevada por heranca/teto se for o caso)
    base = Fraction(tarefa.prioridade_atual())
    if not alpha:
        return base

    # ha quanto tempo essa tarefa esta esperando, sem ter recebido a CPU?
    # conta desde o ULTIMO despacho dela, ou desde a chegada se ela nunca
    # rodou (regra C10 do enunciado)
    desde = tarefa.ultimo_despacho if tarefa.ultimo_despacho is not None else tarefa.chegada
    decorrido = clock - desde
    if decorrido < 0:
        decorrido = ZERO
    return base + alpha * decorrido


def _chave_prioridade(t: Tarefa, clock, alpha):
    # quanto MAIOR a prioridade, mais cedo a tarefa deve rodar - mas a
    # nossa chave e "quem tem o menor valor ganha", entao inverte o sinal
    # (regra C2 do enunciado: prioridade maior = mais prioritaria)
    return (-_prioridade_efetiva(t, clock, alpha), t.chegada, t.id)


# tabela que junta cada sigla com sua chave de escolha e se ele
# pode interromper quem esta rodando (preemptivo) ou nao
ALGORITMOS_GENERICOS = {
    "FCFS": dict(nome="First-Come, First-Served", chave=_chave_fcfs, preemptivo=False, usa_recurso=False),
    "SJF": dict(nome="Shortest Job First", chave=_chave_sjf, preemptivo=False, usa_recurso=False),
    "SRTF": dict(nome="Shortest Remaining Time First", chave=_chave_srtf, preemptivo=True, usa_recurso=False),
    # cooperativa nao interrompe quem esta rodando; preemptiva interrompe
    # se uma tarefa de prioridade maior aparecer - a UNICA diferenca entre
    # as duas e essa flag
    "PRIOc": dict(nome="Prioridade Cooperativa", chave=_chave_prioridade, preemptivo=False, usa_recurso=False),
    "PRIOp": dict(nome="Prioridade Preemptiva", chave=_chave_prioridade, preemptivo=True, usa_recurso=True),
}


def _melhor(tarefas: List[Tarefa], clock, alpha, chave_fn) -> Tarefa:
    # pega a tarefa com a menor chave dentre as prontas
    return min(tarefas, key=lambda t: chave_fn(t, clock, alpha))


def _executar(tarefas: List[Tarefa], sigla: str, ttc: Fraction,
              protocolo_recurso: Optional[str] = None,
              alpha: Optional[Fraction] = None) -> ResultadoSimulacao:
    cfg = ALGORITMOS_GENERICOS[sigla]
    chave_fn = cfg["chave"]
    preemptivo = cfg["preemptivo"]

    # so ativa a logica de recurso se o algoritmo suportar (so o PRIOp) E
    # se pelo menos uma tarefa realmente declarou uma secao critica -
    # senao fica tudo igual a antes, sem custo nenhum
    usa_recurso = cfg["usa_recurso"] and any(t.tem_secao_critica for t in tarefas)

    for t in tarefas:
        t.reset()

    # teto do recurso (R7 / convencao C9): a MAIOR prioridade entre todas
    # as tarefas que declaram usar esse recurso, calculado uma vez so, no
    # comeco - nao importa se a disputa realmente vai acontecer ou nao
    teto_recurso = None
    if usa_recurso and protocolo_recurso == "teto":
        candidatos = [t.prioridade_base for t in tarefas if t.tem_secao_critica]
        if candidatos:
            teto_recurso = max(candidatos)

    pendentes = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    prontas: List[Tarefa] = []
    bloqueadas: List[Tarefa] = []   # tarefas suspensas esperando o recurso R
    detentor: Optional[Tarefa] = None   # quem esta segurando o recurso agora
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
                prontas.append(t)
            else:
                restam.append(t)
        pendentes = restam

    protecao = 0
    while concluidas < total:
        protecao += 1
        if protecao > 5_000_000:
            raise ErroSimulacao("Simulacao nao converge (verifique os dados de entrada).")

        admitir()

        if rodando is None and not prontas:
            if not pendentes:
                # ninguem pronto, ninguem vai chegar, e ainda falta gente
                # terminar -> so pode ser tarefa presa esperando o recurso
                # pra sempre (dado de entrada ruim)
                raise ErroSimulacao("Impasse: ha tarefas suspensas que nunca liberam o recurso.")
            clock = pendentes[0].chegada
            continue

        if rodando is None:
            rodando = _melhor(prontas, clock, alpha, chave_fn)
            prontas.remove(rodando)
        elif preemptivo:
            admitir()
            if prontas:
                candidata = _melhor(prontas, clock, alpha, chave_fn)
                if chave_fn(candidata, clock, alpha) < chave_fn(rodando, clock, alpha):
                    prontas.append(rodando)
                    prontas.remove(candidata)
                    rodando = candidata

        if rodando is not ultima_na_cpu:
            if ttc > 0:
                _acrescentar_periodo(rodando, clock, clock + ttc, "CTX")
                clock += ttc
            trocas_contexto += 1
            ultima_na_cpu = rodando
            rodando.ultimo_despacho = clock

        # ---------------------------------------------------------------
        # ponto novo: antes de rodar, confere se essa tarefa chegou
        # exatamente no instante em que ela precisa do recurso (progresso
        # bate com sc_inicio - regra C7, medido no progresso DELA, nao no
        # relogio geral)
        # ---------------------------------------------------------------
        if usa_recurso and rodando.tem_secao_critica and not rodando.tem_recurso \
                and rodando.progresso == rodando.sc_inicio:
            if detentor is None:
                # recurso livre -> ela pega e segue rodando normalmente
                detentor = rodando
                rodando.tem_recurso = True

                # ---- teto (R7): eleva a prioridade JA, no instante em
                # que pega o recurso - diferente da heranca, nao espera
                # ninguem disputar pra agir ----
                if protocolo_recurso == "teto" and teto_recurso is not None:
                    rodando.prioridade_override = max(rodando.prioridade_base, teto_recurso)
            else:
                # recurso ocupado -> essa tarefa fica SUSPENSA (sai do
                # conjunto de prontas de vez, nao importa a prioridade
                # dela - e literalmente o que o R5 pede)
                bloqueadas.append(rodando)

                # ---- heranca (R6): quem segura o recurso "pega
                # emprestada" a maior prioridade entre quem esta
                # esperando por ele, ate liberar ----
                if protocolo_recurso == "heranca":
                    detentor.prioridade_override = max(
                        detentor.prioridade_atual(), rodando.prioridade_base
                    )

                rodando = None
                ultima_na_cpu = None
                continue

        # executa 1 unidade de tempo
        passo = min(UM, rodando.restante)
        inicio_passo = clock
        _acrescentar_periodo(rodando, inicio_passo, inicio_passo + passo, "EXEC")
        clock += passo
        rodando.progresso += passo
        rodando.restante -= passo

        # ---------------------------------------------------------------
        # enquanto essa unidade rodava, quem estava bloqueado tambem
        # "viveu" esse tempo esperando - aqui a gente classifica esse
        # tempo de espera em dois tipos (R5 pede essa distincao):
        #   DIRETO    -> quem estava rodando era o proprio detentor do
        #                recurso (espera inevitavel, ele vai liberar em
        #                breve)
        #   INVERSAO  -> quem estava rodando NAO e o detentor - ou seja,
        #                uma tarefa de prioridade mais baixa que a
        #                bloqueada esta passando na frente dela so
        #                porque o detentor tambem foi preemptado
        # ---------------------------------------------------------------
        for tb in bloqueadas:
            tipo = "DIRETO" if rodando is detentor else "INVERSAO"
            if tb.bloqueios and tb.bloqueios[-1][2] == tipo and tb.bloqueios[-1][1] == inicio_passo:
                ini0, _, tp0 = tb.bloqueios[-1]
                tb.bloqueios[-1] = (ini0, clock, tp0)
            else:
                tb.bloqueios.append((inicio_passo, clock, tipo))
            _acrescentar_periodo(tb, inicio_passo, clock, "BLOQ")

        # ---------------------------------------------------------------
        # a secao critica termina quando o progresso dela bate em
        # sc_inicio + sc_duracao -> libera o recurso e desbloqueia quem
        # estava esperando (o de maior prioridade entre os que esperam)
        # ---------------------------------------------------------------
        if usa_recurso and detentor is rodando and rodando.progresso == rodando.sc_inicio + rodando.sc_duracao:
            # a heranca e temporaria: assim que libera o recurso, a
            # tarefa volta pra prioridade dela original (regra do R6:
            # "a heranca precisa ser revertida na liberacao")
            rodando.prioridade_override = None
            detentor = None
            if bloqueadas:
                bloqueadas.sort(key=lambda b: (-b.prioridade_base, b.chegada, b.id))
                liberada = bloqueadas.pop(0)
                prontas.append(liberada)

        if rodando.restante == 0:
            rodando.conclusao = clock
            concluidas += 1
            rodando = None

    return ResultadoSimulacao(
        algoritmo=cfg["nome"], sigla=sigla, tarefas=tarefas, ttc=ttc,
        protocolo_recurso=protocolo_recurso if usa_recurso else None,
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

def prioridade_cooperativa(tarefas, ttc=ZERO, alpha=None):
    # alpha e o "passo" do envelhecimento (R8) - quanto a prioridade
    # efetiva de uma tarefa parada na fila cresce por unidade de tempo
    a = para_fracao(alpha) if alpha not in (None, "", 0, "0") else None
    return _executar(tarefas, "PRIOc", para_fracao(ttc), alpha=a)


def prioridade_preemptiva(tarefas, ttc=ZERO, alpha=None, protocolo_recurso=None):
    a = para_fracao(alpha) if alpha not in (None, "", 0, "0") else None
    return _executar(tarefas, "PRIOp", para_fracao(ttc), protocolo_recurso=protocolo_recurso, alpha=a)

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