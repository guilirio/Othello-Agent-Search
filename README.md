# Othello Agent Search

Agentes para Othello com LLM, ferramentas, memória de partida e avaliação experimental.
Projeto de portfólio desenvolvido a partir do TP05 de GCC128 — Inteligência Artificial.

## Arquitetura revisada

Python 3, LangGraph para orquestração, LangChain para integração com Ollama e Tkinter para interface desktop.
O motor do jogo é independente da LLM e da interface. A estratégia heurística fornece uma referência
experimental. O agente LLM deve observar, analisar alternativas, escolher, executar e verificar o resultado
por meio de ferramentas, mantendo o histórico completo da partida.

```text
Interface / experimentos → controlador da partida → agentes
                                                  ↓
                                     LangGraph → ferramentas → motor
```

## Desenvolvimento

1. Estrutura e rastreabilidade dos requisitos (atual).
2. Regras e histórico do Othello.
3. Heurística e ferramentas do ambiente.
4. Agente LLM com LangGraph.
5. Interface e modos Humano × Agente / Agente × Agente.
6. Experimentos, relatório e preparação da entrega.

Cada etapa recebe seu próprio commit e atualiza este README. Consulte
[os requisitos](docs/requirements.md) para distinguir exigências do enunciado e escolhas de implementação.
