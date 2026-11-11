# Rastreabilidade do TP05

Fonte: TP05-Trabalho_Pratico_05_Agentes_Jogo-Othello.pdf, duas páginas, fornecido pelo usuário.

| Exigência | Implementação planejada |
|---|---|
| Tabuleiro 8×8, captura, jogadas legais, término | Motor puro em `game.py`; passe quando sem jogada; término se ambos não jogam |
| Agente autônomo com LLM no fluxo de decisão | Grafo observar → analisar → decidir → executar → verificar |
| get_board_state, get_valid_moves, make_move, get_game_status | Ferramentas validadas e instrumentadas |
| Histórico como memória | Histórico integral no estado observado e log exportável |
| LangChain e/ou LangGraph | LangGraph + integração LangChain/Ollama |
| Critério de avaliação | Cantos, mobilidade, peças e penalidade de adjacência a cantos vazios |
| Tabuleiro visível e acompanhamento | Interface Tkinter com histórico e status |
| Humano × Agente e Agente × Agente | Seleção de participantes na interface |
| Comparar duas estratégias, várias partidas, números e análise | Executor com cores alternadas, seeds e exportação JSON/CSV |
| Relatório | Arquitetura, ferramentas, estratégia, experimentos, resultados, limitações e conclusão |
| Vídeo de 8–10 minutos | Roteiro e campo para link real; gravação pendente |
| ZIP nome1_nome2.zip com código, relatório, README e link | Empacotador validando nomes e link antes de gerar arquivo |

Minimax, Alpha-Beta e Monte Carlo são possibilidades, não obrigações. A versão inicial adota
heurística e análise pela LLM. Explicação de jogadas e métricas de chamadas são diferenciais implementáveis.
O torneio é opcional; sua pontuação é vitória=3, empate=1, derrota=0. Não há protocolo de integração especificado.

O enunciado não exige framework web nem uma linguagem adicional. Tkinter evita infraestrutura de servidor.
O modelo é configurável, pois o enunciado não determina provedor. Resultados de agentes clássicos
não substituem evidência de execução do agente LLM.
