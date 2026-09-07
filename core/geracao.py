"""
Gerador de cenarios aleatorios + salvar/recarregar de cenario em JSON.

A ideia do "salvar/recarregar" existe porque um sorteio interessante nao
pode se perder: se a pessoa sortear um cenario que mostra um bloqueio
legal ou uma inversao de prioridade bonitinha, ela precisa conseguir
gravar esse cenario especifico e trazer ele de volta depois, sem
depender de sortear tudo de novo na sorte.
"""
from __future__ import annotations

import json
import random
from fractions import Fraction
from typing import List, Optional

from .modelo import Tarefa


def gerar_tarefas(
    quantidade: int,
    chegada_max: int = 8,
    duracao_max: int = 6,
    prioridade_max: int = 5,
    permitir_secao_critica: bool = False,
    rng: Optional[random.Random] = None,
) -> List[Tarefa]:
    """
    Sorteia `quantidade` tarefas dentro das faixas passadas. As mesmas
    regras de validacao da entrada manual valem aqui (chegada >= 0,
    duracao >= 1, secao critica cabendo dentro da duracao) - so que em
    vez de recusar um valor invalido, a gente simplesmente nunca sorteia
    um valor fora da faixa.
    """
    if rng is None:
        rng = random.Random()
    if quantidade < 1:
        raise ValueError("A quantidade de tarefas deve ser pelo menos 1.")

    tarefas = []
    for i in range(1, quantidade + 1):
        chegada = rng.randint(0, max(0, chegada_max))
        duracao = rng.randint(1, max(1, duracao_max))
        prioridade = rng.randint(1, max(1, prioridade_max))

        sc_inicio = sc_duracao = None
        # so sorteia secao critica pra metade das tarefas, e so quando
        # faz sentido (duracao >= 2, senao nao cabe nada dentro dela)
        if permitir_secao_critica and duracao >= 2 and rng.random() < 0.5:
            sc_inicio = rng.randint(0, duracao - 1)
            sc_duracao = rng.randint(1, duracao - sc_inicio)

        tarefas.append(Tarefa(i, chegada, duracao, prioridade, sc_inicio, sc_duracao))
    return tarefas


def tarefas_para_dict(tarefas: List[Tarefa]) -> dict:
    # converte a lista de Tarefa pra um dicionario simples, pronto pra
    # virar JSON - guarda os numeros como texto (str) pra nao perder
    # precisao na hora de salvar/reabrir (Fraction vira string tipo "5/3")
    itens = []
    for t in tarefas:
        item = {
            "id": t.id,
            "chegada": str(t.chegada),
            "tp": str(t.tp),
            "prioridade": t.prioridade_base,
        }
        if t.sc_inicio is not None:
            item["sc_inicio"] = str(t.sc_inicio)
            item["sc_duracao"] = str(t.sc_duracao)
        itens.append(item)
    return {"versao": 1, "tarefas": itens}


def salvar_cenario(caminho: str, tarefas: List[Tarefa]):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(tarefas_para_dict(tarefas), f, ensure_ascii=False, indent=2)


def dict_para_tarefas(dados: dict) -> List[Tarefa]:
    tarefas = []
    for item in dados.get("tarefas", []):
        sc_i = item.get("sc_inicio")
        sc_d = item.get("sc_duracao")
        tarefas.append(Tarefa(
            id=int(item["id"]),
            chegada=Fraction(item["chegada"]),
            tp=Fraction(item["tp"]),
            prioridade_base=int(item["prioridade"]),
            sc_inicio=Fraction(sc_i) if sc_i is not None else None,
            sc_duracao=Fraction(sc_d) if sc_d is not None else None,
        ))
    if not tarefas:
        raise ValueError("Arquivo de cenario vazio ou em formato invalido.")
    return tarefas


def carregar_cenario(caminho: str) -> List[Tarefa]:
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dict_para_tarefas(dados)