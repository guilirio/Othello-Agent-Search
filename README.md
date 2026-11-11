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

1. Estrutura e rastreabilidade dos requisitos (concluído).
2. Regras e histórico do Othello (concluído).
3. Heurística e ferramentas do ambiente (concluído).
4. Agente LLM com LangGraph.
5. Interface e modos Humano × Agente / Agente × Agente.
6. Experimentos, relatório e preparação da entrega.

Cada etapa recebe seu próprio commit e atualiza este README. Consulte
[os requisitos](docs/requirements.md) para distinguir exigências do enunciado e escolhas de implementação.

## Motor do jogo

`game.py` mantém um tabuleiro imutável com 64 casas. As coordenadas internas são `(linha, coluna)`,
de 0 a 7. Preto (`1`) inicia; branco é `-1` e vazio é `0`. Um passe é permitido apenas sem jogadas
legais; a partida termina quando nenhum jogador pode jogar, mesmo que existam casas vazias.
Cada ação válida acrescenta jogador, posição, placar e explicação ao histórico.

Para verificar as regras sem instalar dependências, defina `PYTHONPATH=src` e execute
`python -m unittest discover -s tests -v` na raiz do projeto.

## Estratégias e ferramentas

Os agentes `random` e `heuristic` usam o mesmo contrato: executar um turno válido pelo ambiente.
A heurística avalia o estado após cada jogada por diferença de cantos, mobilidade, peças e exposição
perto de cantos vazios. Os pesos do perfil `balanced` são `30, 5, 1, -10`; empates são resolvidos
por gerador pseudoaleatório com seed. Estados terminais recebem pontuação dominante de vitória/derrota.

`GameTools` oferece `get_board_state`, `get_valid_moves`, `make_move`, `get_game_status` e
`evaluate_moves`. Cada chamada registra argumentos, resultado/erro e duração. A execução valida
coordenadas, regras e posse do turno; uma instância não pode jogar duas vezes.
