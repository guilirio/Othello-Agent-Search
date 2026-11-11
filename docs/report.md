# Relatório técnico — Othello Agent Search

STATUS: DRAFT

Versão de desenvolvimento, 11/11/2026. Experimentos com LLM real e vídeo ainda pendentes.

## Arquitetura

A aplicação Python separa regras, ferramentas, estratégias, orquestração, apresentação e experimentos.
`game.py` contém um tabuleiro imutável e o estado mutável da partida; nenhum módulo de regras depende
de LangChain ou Tkinter. `tools.py` limita ações ao turno atual. `agents.py` implementa referências
clássicas; `llm_agent.py` compila um `StateGraph`. `matches.py` unifica partidas automatizadas,
`gui.py` oferece interação desktop e `experiments.py` organiza comparações.

O fluxo do agente LLM é observar → planejar → avaliar alternativas → decidir → executar → verificar.
A LLM escolhe um perfil de avaliação, recebe os resultados da ferramenta correspondente e decide
uma jogada válida. Essa decisão pode divergir do maior score; o modelo participa efetivamente da
política. O controlador repete o fluxo até a condição terminal. Cada partida mantém seu próprio
histórico integral de ações, passes, placares e justificativas, fornecido ao modelo a cada turno.

## Ferramentas

| Ferramenta | Responsabilidade |
|---|---|
| get_board_state | Tabuleiro, jogador e histórico |
| get_valid_moves | Lista de posições legais |
| get_game_status | Placar, vez, passe, término e vencedor |
| evaluate_moves | Avaliação de todas as jogadas por perfil selecionado |
| make_move | Validação e aplicação de exatamente uma ação |

As ferramentas são chamadas explicitamente pelos nós do grafo. A seleção do perfil e da ação é
feita pela LLM por JSON validado; não dependemos do suporte nativo a tool calling do modelo.
Chamadas registram argumentos, resultados, falhas e duração. Respostas inválidas permitem uma
correção por etapa. Não há fallback automático para heurística quando a LLM falha.

## Estratégia

Para cada ação válida, calcula-se o tabuleiro sucessor e quatro diferenças entre jogador e adversário:
cantos ocupados, quantidade de jogadas legais, quantidade de peças e ocupação das casas adjacentes
a cantos vazios. O perfil balanced usa pesos 30, 5, 1 e -10; mobility usa 25, 10, 1 e -10; corners usa
50, 4, 1 e -15. Vitória/derrota terminal recebe ±100000 mais a diferença de peças; empate recebe zero.

O agente heurístico maximiza balanced, com desempate pseudoaleatório. O agente aleatório escolhe
uniformemente entre jogadas legais. A LLM adapta o perfil e decide com base nas avaliações e histórico.
Não há Minimax, Alpha-Beta ou busca em profundidade nesta versão: a avaliação considera um sucessor
por ação. Essas técnicas são opções do enunciado, não requisitos. O nome do projeto descreve a
exploração de ações; não implica implementação de um algoritmo específico de busca.

## Método experimental

Foram executadas 40 partidas de heuristic × random, com 20 partidas por cor para cada estratégia.
As seeds base foram de 42 a 61, uma por par de partidas. Os geradores de cada cor usam seed e seed+1.
Comando: `othello experiment --a heuristic --b random --games 40 --seed 42 --output artifacts/baseline`.
As versões e plataforma estão em [results/baseline.json](results/baseline.json).

## Resultados observados

| Agente | Vitórias | Derrotas | Empates | Taxa de vitória | Pontos | Tempo médio por turno |
|---|---:|---:|---:|---:|---:|---:|
| Heurístico | 39 | 1 | 0 | 97,5% | 117 | 3,170 ms |
| Aleatório | 1 | 39 | 0 | 2,5% | 3 | 0,194 ms |

Todas as 40 partidas terminaram sem falhas. O heurístico realizou 1230 jogadas e 1 passe;
o aleatório realizou 1165 jogadas e 65 passes. Houve, respectivamente, 3692 e 2460 chamadas
às ferramentas. Nenhuma chamada à LLM ocorreu neste experimento.

## Análise qualitativa

A vantagem observada é compatível com o uso de critérios posicionais frente a uma política sem
avaliação estratégica. A diferença de passes indica que o heurístico deixou o adversário sem
ações com maior frequência nessa amostra. Esse resultado não isola o efeito de cada componente:
seriam necessárias ablações dos pesos para atribuir causalidade a cantos ou mobilidade.
A heurística consome mais tempo por turno por construir e avaliar cada sucessor.

## Limitações e experimento LLM pendente

O serviço Ollama não estava disponível no ambiente de desenvolvimento. O grafo foi verificado com
respostas simuladas, inclusive recuperação de JSON inválido e rejeição de jogadas ilegais, mas isso
não mede desempenho ou qualidade de uma LLM real. Antes da entrega acadêmica é necessário executar
LLM × heuristic com cores alternadas, registrar modelo e configuração, analisar falhas, latências,
chamadas e exemplos de decisões, e incorporar os resultados aqui.

Os resultados clássicos pertencem a uma amostra de 40 partidas contra um oponente fraco; não
demonstram desempenho em torneio. Tempos dependem do hardware. A LLM pode falhar no formato JSON
ou consumir contexto excessivo em partidas com explicações longas. Os perfis usam pesos fixos,
sem otimização ou busca profunda. Métricas agregadas contam apenas partidas concluídas; falhas
devem ser analisadas separadamente. A interface não oferece retomada de partidas exportadas.

## Conclusão provisória

O motor, as ferramentas, a memória, os modos de jogo e a infraestrutura experimental foram
implementados. A avaliação inicial estabelece uma referência clássica reproduzível. A conclusão
sobre a contribuição da LLM depende da execução real e da análise desse segundo experimento.
