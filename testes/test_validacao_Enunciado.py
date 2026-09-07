"""
Reproduz numericamente os cenarios de validacao do enunciado do PDF do professor.
Se esse arquivo passar, o motor de simulacao esta de acordo com a
especificacao.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fractions import Fraction as F
from core.modelo import Tarefa
from core.motor import fcfs, sjf, srtf, round_robin, prioridade_cooperativa, prioridade_preemptiva


def aprox(a, b, tol=F(6, 1000)):
    # compara com uma tolerancia pequena, so pra absorver arredondamento
    # de exibicao (o motor usa Fraction exato por dentro, mas o PDF
    # arredonda os valores pra 2 casas decimais nas tabelas dele)
    return abs(F(a) - F(b)) <= tol


def checar(nome, obtido, esperado):
    ok = aprox(obtido, esperado)
    status = "OK " if ok else "FALHOU"
    print(f"  [{status}] {nome}: obtido={float(obtido):.3f} esperado={float(esperado):.3f}")
    return ok


def tarefas_4_1():
    return [
        Tarefa(1, 0, 5, 2),
        Tarefa(2, 0, 2, 3),
        Tarefa(3, 1, 4, 1),
        Tarefa(4, 3, 1, 4),
        Tarefa(5, 5, 2, 5),
    ]


todos_ok = True


def secao(titulo):
    print(f"\n=== {titulo} ===")


# ---------------------------------------------------------------------
secao("4.1 Cenario da Aula 5 (sem custo de troca)")
casos = [
    ("FCFS", lambda ts: fcfs(ts), F(8, 1), F(52, 10)),
    ("SJF", lambda ts: sjf(ts), F(58, 10), F(30, 10)),
    ("SRTF", lambda ts: srtf(ts), F(54, 10), F(26, 10)),
    ("PRIOc", lambda ts: prioridade_cooperativa(ts), F(66, 10), F(38, 10)),
    ("PRIOp", lambda ts: prioridade_preemptiva(ts), F(56, 10), F(28, 10)),
]
for nome, fn, tt_esp, tw_esp in casos:
    r = fn(tarefas_4_1())
    ok1 = checar(f"{nome} Tt", r.media_tt(), tt_esp)
    ok2 = checar(f"{nome} Tw", r.media_tw(), tw_esp)
    todos_ok &= ok1 and ok2

r = round_robin(tarefas_4_1(), tq=2)
ok1 = checar("RR(q=2) Tt", r.media_tt(), F(84, 10))
ok2 = checar("RR(q=2) Tw", r.media_tw(), F(56, 10))
ok3 = checar("RR(q=2) 1a exec media", r.media_primeira_execucao(), F(28, 10))
todos_ok &= ok1 and ok2 and ok3

# ---------------------------------------------------------------------
secao("4.2 Aula 5 com custo de troca (c=1)")
r = fcfs(tarefas_4_1(), ttc=1)
ok1 = checar("FCFS(c=1) Tt", r.media_tt(), F(11, 1))
ok2 = checar("FCFS(c=1) Tw", r.media_tw(), F(82, 10))
todos_ok &= ok1 and ok2

r = round_robin(tarefas_4_1(), tq=4, ttc=1)
ok1 = checar("RR(q=4,c=1) Tt", r.media_tt(), F(134, 10))
ok2 = checar("RR(q=4,c=1) Tw", r.media_tw(), F(106, 10))
ok3 = checar("RR(q=4,c=1) Eficiencia", r.eficiencia(), F(4, 5))
todos_ok &= ok1 and ok2 and ok3

# ---------------------------------------------------------------------
secao("4.3 Inversao de prioridades (PRIOp, sem correcao)")


def tarefas_4_3():
    return [
        Tarefa(1, 0, 6, 1, sc_inicio=1, sc_duracao=4),
        Tarefa(2, 4, 4, 2),
        Tarefa(3, 6, 3, 3),
        Tarefa(4, 2, 3, 4, sc_inicio=1, sc_duracao=1),
    ]


r = prioridade_preemptiva(tarefas_4_3(), protocolo_recurso="nenhum")
por_id = {t.id: t for t in r.tarefas}
esperado_concl = {1: 16, 2: 11, 3: 9, 4: 15}
esperado_tw = {1: 10, 2: 3, 3: 0, 4: 10}
for i in (1, 2, 3, 4):
    ok1 = checar(f"t{i} conclusao", por_id[i].conclusao, esperado_concl[i])
    ok2 = checar(f"t{i} tw", por_id[i].tempo_espera(), esperado_tw[i])
    todos_ok &= ok1 and ok2
ok = checar("Tt medio", r.media_tt(), F(975, 100))
todos_ok &= ok
ok = checar("Tw medio", r.media_tw(), F(575, 100))
todos_ok &= ok

# ---------------------------------------------------------------------
secao("4.4 Heranca de prioridade")
r = prioridade_preemptiva(tarefas_4_3(), protocolo_recurso="heranca")
por_id = {t.id: t for t in r.tarefas}
esperado_concl = {1: 16, 2: 15, 3: 11, 4: 8}
esperado_tw = {1: 10, 2: 7, 3: 2, 4: 3}
for i in (1, 2, 3, 4):
    ok1 = checar(f"t{i} conclusao", por_id[i].conclusao, esperado_concl[i])
    ok2 = checar(f"t{i} tw", por_id[i].tempo_espera(), esperado_tw[i])
    todos_ok &= ok1 and ok2
ok = checar("Tt medio", r.media_tt(), F(95, 10))
todos_ok &= ok
ok = checar("Tw medio", r.media_tw(), F(55, 10))
todos_ok &= ok

# ---------------------------------------------------------------------
secao("4.5 Teto de prioridade")
r = prioridade_preemptiva(tarefas_4_3(), protocolo_recurso="teto")
por_id = {t.id: t for t in r.tarefas}
esperado_concl = {1: 16, 2: 15, 3: 11, 4: 8}
esperado_tw = {1: 10, 2: 7, 3: 2, 4: 3}
for i in (1, 2, 3, 4):
    ok1 = checar(f"t{i} conclusao", por_id[i].conclusao, esperado_concl[i])
    ok2 = checar(f"t{i} tw", por_id[i].tempo_espera(), esperado_tw[i])
    todos_ok &= ok1 and ok2
ok = checar("Tt medio", r.media_tt(), F(95, 10))
todos_ok &= ok
ok = checar("Tw medio", r.media_tw(), F(55, 10))
todos_ok &= ok

secao("4.5b Teto - segundo exemplo (disputa que nunca ocorre)")


def tarefas_4_5b():
    return [
        Tarefa(1, 0, 6, 1, sc_inicio=1, sc_duracao=4),
        Tarefa(2, 2, 3, 2),
        Tarefa(4, 12, 2, 4, sc_inicio=0, sc_duracao=1),
    ]


r = prioridade_preemptiva(tarefas_4_5b(), protocolo_recurso="teto")
por_id = {t.id: t for t in r.tarefas}
ok = checar("t2 tw (teto)", por_id[2].tempo_espera(), 3)
todos_ok &= ok
r2 = prioridade_preemptiva(tarefas_4_5b(), protocolo_recurso="heranca")
por_id2 = {t.id: t for t in r2.tarefas}
ok = checar("t2 tw (heranca)", por_id2[2].tempo_espera(), 0)
todos_ok &= ok

# ---------------------------------------------------------------------
secao("4.6 Inanicao e envelhecimento (PRIOc)")


def tarefas_4_6():
    return [
        Tarefa(1, 0, 4, 1),
        Tarefa(2, 0, 2, 5),
        Tarefa(3, 2, 2, 5),
        Tarefa(4, 4, 2, 5),
        Tarefa(5, 6, 2, 5),
        Tarefa(6, 8, 2, 5),
    ]


r = prioridade_cooperativa(tarefas_4_6())
por_id = {t.id: t for t in r.tarefas}
ok1 = checar("sem envelh. tw(t1)", por_id[1].tempo_espera(), 10)
ok2 = checar("sem envelh. Tw", r.media_tw(), F(167, 100))
todos_ok &= ok1 and ok2

r = prioridade_cooperativa(tarefas_4_6(), alpha=1)
por_id = {t.id: t for t in r.tarefas}
ok1 = checar("alpha=1 tw(t1)", por_id[1].tempo_espera(), 4)
ok2 = checar("alpha=1 Tw", r.media_tw(), F(267, 100))
todos_ok &= ok1 and ok2

r = prioridade_cooperativa(tarefas_4_6(), alpha=2)
por_id = {t.id: t for t in r.tarefas}
ok1 = checar("alpha=2 tw(t1)", por_id[1].tempo_espera(), 2)
ok2 = checar("alpha=2 Tw", r.media_tw(), F(3, 1))
todos_ok &= ok1 and ok2

print("\n" + "=" * 60)
if todos_ok:
    print("TODOS OS CENARIOS DE VALIDACAO PASSARAM.")
else:
    print("HA DIVERGENCIAS - revisar o motor.")
sys.exit(0 if todos_ok else 1)