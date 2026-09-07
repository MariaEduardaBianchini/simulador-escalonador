"""
Ponto de entrada do simulador.

Esse arquivo nao aceita nenhum argumento de linha de comando (R10): so
abrir com dois cliques (ou `python3 main.py`) que a janela grafica surge
e toda a interacao acontece dentro dela.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import iniciar_aplicacao

if __name__ == "__main__":
    iniciar_aplicacao()