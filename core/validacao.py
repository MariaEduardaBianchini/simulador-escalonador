"""
Validacao de entrada (R2, R4).

A ideia e simples: cada funcao aqui tenta converter o texto que a pessoa
digitou pra um numero, e se nao der (ou o numero nao fizer sentido no
contexto), levanta um ValueError com uma mensagem em portugues, clara,
dizendo o que esta errado. Quem chama essas funcoes (a interface grafica,
mais pra frente) captura esse erro, mostra a mensagem numa caixinha, e
deixa a pessoa tentar de novo - sem derrubar o programa.
"""
from __future__ import annotations

from fractions import Fraction


def validar_inteiro_nao_negativo(texto: str, nome: str) -> int:
    texto = (texto or "").strip()
    try:
        valor = int(texto)
    except ValueError:
        # texto vazio, com letra, com virgula etc -> nao converte pra int
        raise ValueError(f"{nome} deve ser um numero inteiro.")
    if valor < 0:
        raise ValueError(f"{nome} nao pode ser negativo.")
    return valor


def validar_inteiro_positivo(texto: str, nome: str) -> int:
    # reaproveita a funcao de cima e so acrescenta a regra "maior que zero"
    valor = validar_inteiro_nao_negativo(texto, nome)
    if valor < 1:
        raise ValueError(f"{nome} deve ser maior que zero.")
    return valor


def validar_numero_nao_negativo(texto: str, nome: str) -> Fraction:
    # usado pra ttc/tq/alpha, que podem ser fracionarios (ex: 0.5)
    texto = (texto or "").strip().replace(",", ".")  # aceita virgula tambem
    try:
        valor = Fraction(texto)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"{nome} deve ser um numero.")
    if valor < 0:
        raise ValueError(f"{nome} nao pode ser negativo.")
    return valor


def validar_numero_positivo(texto: str, nome: str) -> Fraction:
    valor = validar_numero_nao_negativo(texto, nome)
    if valor <= 0:
        raise ValueError(f"{nome} deve ser maior que zero.")
    return valor


def validar_tarefa(chegada_txt, duracao_txt, prioridade_txt,
                    sc_inicio_txt="", sc_duracao_txt=""):
    """
    Confere os 5 campos de uma tarefa de uma vez so. Devolve uma tupla
    pronta pra criar a Tarefa: (chegada, duracao, prioridade,
    sc_inicio ou None, sc_duracao ou None).
    """
    # as regras aqui sao exatamente as que o enunciado pede (R2):
    # ingresso nao negativo, duracao positiva, secao critica contida
    # dentro da duracao da propria tarefa
    chegada = validar_inteiro_nao_negativo(chegada_txt, "Instante de ingresso")
    duracao = validar_inteiro_positivo(duracao_txt, "Tempo de processamento")
    prioridade = validar_inteiro_positivo(prioridade_txt, "Prioridade")

    sc_inicio_txt = (sc_inicio_txt or "").strip()
    sc_duracao_txt = (sc_duracao_txt or "").strip()
    sc_inicio = sc_duracao = None

    # a secao critica e opcional - so valida ela se a pessoa preencheu
    # pelo menos um dos dois campos
    if sc_inicio_txt or sc_duracao_txt:
        sc_inicio = validar_inteiro_nao_negativo(sc_inicio_txt, "Inicio da secao critica")
        sc_duracao = validar_inteiro_positivo(sc_duracao_txt, "Duracao da secao critica")
        if sc_inicio + sc_duracao > duracao:
            raise ValueError(
                "A secao critica precisa estar contida na duracao da tarefa "
                f"(inicio {sc_inicio} + duracao {sc_duracao} ultrapassa tp={duracao})."
            )
    return chegada, duracao, prioridade, sc_inicio, sc_duracao


def validar_quantum_e_ttc(tq_txt, ttc_txt):
    """Confere quantum e custo de troca juntos, porque a regra do R4
    (quantum > ttc) depende dos dois ao mesmo tempo."""
    ttc = validar_numero_nao_negativo(ttc_txt, "Custo da troca de contexto")
    tq = validar_numero_positivo(tq_txt, "Quantum")
    if tq <= ttc:
        raise ValueError(
            "O quantum precisa ser maior que o custo da troca de contexto "
            "(senao a troca consome a fatia inteira e nenhum trabalho util e feito)."
        )
    return tq, ttc