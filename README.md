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
5. Interface e modos Humano × Agente / Agente × Agente (implementado).
6. Experimentos (implementado), relatório e preparação da entrega.

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

## Executar

```powershell
othello gui
othello play --black heuristic --white random --seed 42 --json artifacts/partida.json
othello play --black llm --white heuristic --model qwen2.5:3b --json artifacts/llm.json
python -m unittest discover -s tests -v
```

Também é possível usar `python -m othello` no lugar de `othello`. Na interface, escolha os
participantes e clique em **Nova partida**. `human × llm` atende ao modo Humano × Agente;
`llm × heuristic` ou `llm × llm` permitem acompanhar agentes. Pontos indicam jogadas válidas.
Chamadas ao modelo são executadas em segundo plano; é possível pausar e reiniciar. Ao pausar,
uma ação já em processamento pode terminar. Uma nova partida descarta resultados da anterior.
Use **Exportar partida** para guardar histórico e métricas em JSON.

Tkinter acompanha as distribuições comuns de Python para Windows. No Linux pode ser necessário
instalar o pacote `python3-tk` da distribuição. O executor `play` funciona sem interface gráfica.

## Experimentos

```powershell
othello experiment --a heuristic --b random --games 40 --seed 42 --output artifacts/baseline
othello experiment --a llm --b heuristic --games 20 --seed 42 --model qwen2.5:3b --output artifacts/llm
```

As cores alternam a cada partida; cada par usa a mesma seed base. Os agentes clássicos usam
geradores independentes por cor. O executor exige quantidade par de partidas e exporta dados brutos,
resumo JSON e CSV: vitórias, empates, derrotas, taxa de vitória, pontos de torneio, jogadas, turnos,
tempo médio por turno (inclui passes), chamadas e latência média da LLM e chamadas às ferramentas.
Partidas com erro ficam registradas e são excluídas do denominador da taxa de vitória; o processo
retorna código 1 se houver falhas. Compare os números de falhas junto às taxas de vitória.

As seeds reproduzem os agentes clássicos; temperatura zero não garante reprodução exata de uma LLM.
O resultado registra modelo solicitado, versões das bibliotecas, Python e plataforma. Artefatos brutos
ficam em `artifacts/`, fora do Git; resumos selecionados podem ser versionados em `docs/results/`.

Testes gráficos são opcionais e precisam de um desktop com Tk instalado:
`$env:OTHELLO_UI_TESTS='1'; python -m unittest discover -s tests -p test_gui.py -v`.
Eles exercitam jogada humana, reinício durante trabalho anterior e uma partida completa com agentes.
Os metadados experimentais resolvem o modelo padrão e a variável `OTHELLO_MODEL`, mesmo sem `--model`.
