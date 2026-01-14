# Deep Research System

Sistema de pesquisa profunda inspirado no **Open Deep Research** do LangChain, implementado usando o padrão Supervisor com LangGraph. O sistema é capaz de realizar pesquisas complexas dividindo perguntas em subtópicos independentes, pesquisando em paralelo (via RAG interno ou busca web), e sintetizando os resultados em uma resposta coerente.

## Inspiração

Este projeto foi inspirado no [Open Deep Research](https://www.blog.langchain.com/open-deep-research/) do LangChain, uma ferramenta que utiliza agentes para realizar pesquisas profundas e estruturadas. Nossa implementação adota o padrão Supervisor, onde um agente coordenador divide tarefas complexas em subtópicos que são investigados paralelamente por agentes especializados.

## Arquitetura

O sistema segue o padrão **Supervisor Pattern** com três tipos principais de agentes:

```
User Question
     ↓
[SUPERVISOR] → Divide em subtópicos
     ↓
[RESEARCHERS/WEB SEARCHERS] → Pesquisa paralela
     ↓
[SYNTHESIS] → Compila resposta final
```

## Estrutura de Arquivos

### Arquivos Principais

- **[main.py](main.py)** - Script principal de execução. Gerencia argumentos CLI, inicializa modelos e orquestra o fluxo completo de pesquisa.

- **[config.py](config.py)** - Configurações centralizadas do sistema (modelos LLM/embeddings, parâmetros RAG, temperatura, max_tokens, etc).

- **[state.py](state.py)** - Define os estados TypedDict do LangGraph (`ResearchState` e `SubtopicState`) que gerenciam o fluxo de dados entre os agentes.

- **[graph.py](graph.py)** - Construção do grafo LangGraph que conecta os agentes Supervisor → Researcher/WebSearcher → Synthesis.

- **[models.py](models.py)** - Inicialização dos modelos LLM (HuggingFace Endpoint) e embeddings (sentence-transformers).

- **[vector_store.py](vector_store.py)** - Gerenciamento do FAISS vector store com cache automático. Realiza chunking de documentos e busca por similaridade.

### Agentes

- **[agents/supervisor.py](agents/supervisor.py)** - Agente Supervisor que divide a pergunta do usuário em múltiplos subtópicos independentes para pesquisa paralela.

- **[agents/researcher.py](agents/researcher.py)** - Agente Pesquisador que utiliza RAG interno (busca em FAISS vector store) para responder subtópicos consultando documentos locais.

- **[agents/web_searcher.py](agents/web_searcher.py)** - Agente de Busca Web que pesquisa subtópicos na internet usando DuckDuckGo (via biblioteca `ddgs`).

- **[agents/synthesis.py](agents/synthesis.py)** - Agente de Síntese que compila todos os resultados das pesquisas em uma resposta final coerente e fluida.

### Utilitários

- **[utils/document_loader.py](utils/document_loader.py)** - Carrega todos os arquivos `.txt` da pasta `data/` para uso no RAG interno.

- **[utils/file_saver.py](utils/file_saver.py)** - Salva resultados de pesquisa em formato TXT formatado e opcionalmente as fontes web brutas em JSON separado.

## Instalação

### 1. Requisitos

- Python 3.8+
- Pip

### 2. Instalar Dependências

```bash
pip install langchain langchain-huggingface langchain-community
pip install faiss-cpu sentence-transformers
pip install python-dotenv ddgs
```

### 3. Configurar Variável de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
HF_TOKEN=sua_chave_huggingface_aqui
```

Para obter uma chave:
1. Acesse [HuggingFace](https://huggingface.co)
2. Faça login e vá em Settings → Access Tokens
3. Crie um novo token com permissão de leitura

## Uso

### Sintaxe Básica

```bash
python main.py --question "Sua pergunta aqui"
```

### Argumentos Disponíveis

| Argumento | Descrição | Padrão |
|-----------|-----------|--------|
| `-q, --question` | Pergunta para pesquisar | Pergunta padrão |
| `--web` | Usar busca web | `True` |
| `--no-web` | Usar RAG interno (documentos locais) | `False` |
| `-s, --subagents` | Número de subtópicos gerados | `3` |
| `--quiet` | Modo silencioso | `False` |
| `--data-dir` | Diretório dos documentos | `data` |
| `--no-save` | Não salvar resultados | `False` |
| `--save-sources` | Salvar fontes web | `True` |
| `--no-save-sources` | Não salvar fontes web | `False` |
| `--list` | Listar pesquisas anteriores | `False` |
| `--token` | HuggingFace token (sobrescreve .env) | Valor do `.env` |

### Exemplos de Uso

#### 1. Busca Web (Modo Padrão)

```bash
python main.py --question "What are the best tools to repair an iPhone 15?"
```

Este modo:
- Usa DuckDuckGo para buscar informações na web
- Divide a pergunta em subtópicos
- Busca 3 resultados web para cada subtópico
- Sintetiza uma resposta completa
- Salva relatório e fontes web

#### 2. RAG Interno (Documentos Locais)

```bash
python main.py --question "Como funciona OAuth?" --no-web
```

Este modo:
- Carrega documentos `.txt` da pasta `data/`
- Cria/carrega FAISS vector store (com cache)
- Busca nos documentos locais
- **Requer:** Arquivos `.txt` na pasta `data/`

#### 3. Customizar Número de Subtópicos

```bash
python main.py --question "Explain quantum computing" -s 5
```

Gera 5 subtópicos ao invés de 3.


## RAG (Retrieval-Augmented Generation)

### O que é RAG?

RAG combina recuperação de informações (IR) com geração de texto (LLM). O fluxo é:

1. **Indexação:** Documentos são divididos em chunks e vetorizados
2. **Busca:** Pergunta é vetorizada e busca-se chunks similares (top-k)
3. **Geração:** LLM recebe contexto relevante + pergunta e gera resposta

### Como Funciona no Projeto

#### Modo RAG Interno (`--no-web`)

1. **Carregar Documentos:** [utils/document_loader.py](utils/document_loader.py) lê todos os `.txt` da pasta `data/`
2. **Chunking:** [vector_store.py:87-93](vector_store.py#L87-L93) divide documentos em pedaços de 1024 tokens com overlap de 500
3. **Vetorização:** Chunks são convertidos em embeddings usando MiniLM-L6-v2
4. **Indexação FAISS:** Vetores são indexados para busca rápida por similaridade
5. **Cache:** Vector store é salvo em `data/.vectorstore_cache` para reuso
6. **Busca:** Para cada subtópico, recupera top-5 chunks mais similares ([config.py:16](config.py#L16))
7. **Análise:** LLM lê os chunks e responde a pergunta

**Parâmetros configuráveis** em [config.py](config.py):
- `chunk_size`: Tamanho dos pedaços (padrão: 1024)
- `chunk_overlap`: Sobreposição entre chunks (padrão: 500)
- `top_k_retrieval`: Quantos chunks recuperar (padrão: 5)

## Busca Web

### Como Funciona

Quando usa `--web` (padrão):

1. **Supervisor:** Divide pergunta em subtópicos
2. **Web Searcher:** Para cada subtópico:
   - Busca no DuckDuckGo usando biblioteca `ddgs`
   - Recupera 3 primeiros resultados (título, URL, snippet)
   - LLM analisa os snippets e extrai informações relevantes
3. **Synthesis:** Compila todas as análises em resposta única

### Biblioteca Utilizada

- **ddgs** (DuckDuckGo Search) - Busca sem necessidade de API key
- Configurado em [agents/web_searcher.py:7-55](agents/web_searcher.py#L7-L55)

### Salvamento de Fontes

Por padrão, salva dois arquivos:

1. **Relatório formatado** (`.txt`): Resposta completa com snippets truncados
2. **Fontes web completas** (`.json`): Metadados + snippets completos de todas as buscas


## Saída de Resultados

Os resultados são salvos na pasta `data/` com nomenclatura:

```
pergunta_customizada_HHMMSS_DDMMYYYY.txt           # Relatório
pergunta_customizada_HHMMSS_DDMMYYYY_web_sources.json  # Fontes web
```


## Limitações e Considerações

- **Busca Web:** Limitada a 3 resultados por subtópico (DuckDuckGo)
- **LLM:** Modelos menores (3B params) podem ter respostas menos precisas
- **RAG:** Qualidade depende dos documentos fornecidos em `data/`
- **Cache:** Vector store é reconstruído se arquivos `.txt` forem modificados
