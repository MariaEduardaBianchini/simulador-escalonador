# Simulador de Escalonamento de Tarefas

Projeto prático da disciplina de Sistemas Operacionais, ministrada por
Prof. Dr.  Vinícius S. Borges. Oitavo Semestre do Curso de Engenharia de Computação.

## Autoria

- Alex Akio Nishimura Junior
- Maria Eduarda Ferreira Bianchini
- Pedro Henrique Rodrigues de Assis


## Descrição

Simulador de escalonamento de tarefas em um processador, escrito em Python.
Implementa os seis algoritmos estudados em sala — FCFS, SJF, SRTF,
Round-Robin, prioridade cooperativa e prioridade preemptiva —, tratando
recursos de uso exclusivo e reproduzindo o fenômeno da inversão de
prioridades, com os dois mecanismos de correção (herança e teto de
prioridade) e o envelhecimento de prioridade para eliminar inanição.

A arquitetura separa mecanismo (o laço que avança o relógio, mantém a
fila de prontas e cobra a troca de contexto) de política (a escolha de
qual tarefa recebe o processador), de modo que cinco dos seis algoritmos
compartilham o mesmo laço de simulação e diferem apenas no critério de
escolha.

## Como executar

Baixe o projeto .zip e descompacte na pasta de preferência. Depois, clique duas vezes em `SimuladorEscalonamento.exe`, dentro da pasta `dist/`.
Não é necessário instalar nada.

Se o executável ainda não tiver sido gerado, veja a seção
[Gerando o executável](#gerando-o-executável) mais abaixo — o processo
leva menos de um minuto e não exige nenhuma configuração além de ter o
Python instalado.

Alternativamente, com o Python instalado, o programa também abre direto
pelo código-fonte, sem gerar o executável:

```
python3 main.py
```

## Estrutura do repositório

```
simulador-escalonador/
├── main.py                        Ponto de entrada do programa (sem argumentos de linha de comando)
├── requirements.txt                Dependencia unica, so para gerar o executavel (PyInstaller)
├── SimuladorEscalonamento.spec     Receita do PyInstaller
├── .gitignore
├── README.md
├── core/                           Codigo-fonte do simulador (mecanismo, algoritmos, dados)
│   ├── modelo.py
│   ├── motor.py
│   ├── validacao.py
│   └── geracao.py
├── gui/                            Interface grafica (tkinter)
│   ├── app.py
│   ├── tema.py
│   └── gantt.py
├── testes/                         Testes automaticos
│   └── test_validacao_enunciado.py
├── exemplos/                       Cenarios de exemplo em JSON
└── docs/                           Tutoriais e documentacao tecnica
    ├── tutorial_execucao.md
    ├── tutorial_uso.md
    ├── documentacao_tecnica.md
    └── imagens/
```

## Arquivos de código

- `main.py` — ponto de entrada; só chama a interface gráfica, sem receber argumentos.
- `core/modelo.py` — estrutura de dados de uma tarefa, de um período de tempo e do resultado de uma simulação.
- `core/motor.py` — o mecanismo de simulação (laço único, comum a cinco dos seis algoritmos) e o Round-Robin (mecanismo próprio); implementa os seis algoritmos, o recurso exclusivo, a herança e o teto de prioridade, e o envelhecimento.
- `core/validacao.py` — validação dos dados digitados, com mensagens de erro claras.
- `core/geracao.py` — sorteio de cenários aleatórios e salvar/carregar um cenário em JSON.
- `gui/app.py` — janela principal e as quatro abas da interface (sobre o projeto, tarefas, simulação, comparação em lote).
- `gui/tema.py` — paleta de cores e estilos visuais compartilhados pela interface.
- `gui/gantt.py` — desenho do diagrama de tempo (Gantt), em `tkinter.Canvas` puro.
- `testes/test_validacao_enunciado.py` — reproduz numericamente os cenários de referência do enunciado (seção 4 do PDF) e confere se os valores batem.

## Requisitos de ambiente

- Para executar o projeto, é necessário o Python 3.10 ou superior.
- Nenhuma biblioteca externa em tempo de execução — o programa usa apenas
  a biblioteca padrão do Python (`tkinter`, `fractions`, `json`, `random`).
- A única dependência do projeto (`pyinstaller`, listada em
  `requirements.txt`) é usada exclusivamente para **gerar** o executável
  de distribuição; não é necessária para rodar `python3 main.py`.

## Funcionalidades

| O que faz | Onde |
|---|---|
| Os seis algoritmos de escalonamento | `core/motor.py` |
| Aba explicativa do projeto e dos algoritmos | `gui/app.py` (aba "1 · Sobre o projeto") |
| Entrada digitada ou sorteada, com validação e salvar/recarregar cenário | `core/validacao.py`, `core/geracao.py`, `gui/app.py` (aba "2 · Tarefas") |
| Métricas por tarefa e em média (tt, tp, tw, 1ª execução) | `core/modelo.py` |
| Quantum e custo de troca configuráveis, com validação e eficiência | `core/validacao.py`, `core/motor.py` (Round-Robin) |
| Recurso exclusivo e inversão de prioridades | `core/motor.py` (bloco de gerenciamento do recurso) |
| Herança de prioridade | `core/motor.py` (`protocolo_recurso="heranca"`) |
| Teto de prioridade | `core/motor.py` (`protocolo_recurso="teto"`) |
| Envelhecimento de prioridade | `core/motor.py` (`_prioridade_efetiva`) |
| Comparação de algoritmos em lote de cenários sorteados | `gui/app.py` (aba "4 · Comparar em lote") |
| Diagrama de tempo | `gui/gantt.py` |

## Gerando o executável

```
pip install -r requirements.txt
python3 -m PyInstaller SimuladorEscalonamento.spec
```

O executável final fica em `dist/SimuladorEscalonamento.exe`. Rode esse
comando na mesma máquina/sistema operacional em que o programa vai ser
usado.

## Documentação

- [Tutorial de execução](./docs/tutorial_execucao.md)
- [Tutorial de uso](./docs/tutorial_uso.md)
- [Documentação técnica](./docs/documentacao_tecnica.md)

## Por onde começar

1. Abra o programa e siga o [tutorial de execução](./docs/tutorial_execucao.md).
2. Reproduza um cenário de exemplo pelo [tutorial de uso](./docs/tutorial_uso.md).
3. Consulte a [documentação técnica](./docs/documentacao_tecnica.md) para entender o funcionamento interno.
