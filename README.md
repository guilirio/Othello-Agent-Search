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
4. Agente LLM com LangGraph (implementado; execução real requer Ollama).
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

## Agente LLM

O grafo realiza `observe → plan → analyze → decide → execute → verify`. A primeira chamada à LLM
escolhe um perfil heurístico; `evaluate_moves` calcula as alternativas. A segunda chamada compara
essas alternativas e escolhe a ação com justificativa curta. `make_move` valida e executa; o estado
é consultado novamente. A LLM recebe o histórico completo da partida em cada turno, inclusive as
jogadas adversárias. Não existe memória compartilhada entre partidas.

Respostas JSON inválidas ou jogadas ilegais permitem uma correção por etapa. Falhas de conexão
ou duas respostas inválidas interrompem o turno com erro explícito, sem substituição silenciosa por
um agente clássico. Passes obrigatórios dispensam chamada ao modelo.

Instalação sugerida (Python 3.11 ou superior):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Instale [Ollama](https://ollama.com/download), execute `ollama pull qwen2.5:3b` e mantenha o serviço
ativo (`ollama serve`, quando necessário). Configure `OTHELLO_MODEL` para outro modelo local e
`OLLAMA_HOST` para outro endpoint. O padrão é `http://127.0.0.1:11434`, temperatura 0 e timeout de
120 segundos por chamada. A qualidade e o consumo de memória dependem do modelo e do hardware.

Referências de implementação: [StateGraph](https://reference.langchain.com/python/langgraph/graph/state)
e [ChatOllama](https://reference.langchain.com/python/langchain-ollama/langchain_ollama/chat_models/ChatOllama).
Os testes do grafo usam respostas simuladas; eles não comprovam a força de jogo de uma LLM real.
