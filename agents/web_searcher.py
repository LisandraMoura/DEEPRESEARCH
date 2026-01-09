"""
Agente de Busca Web - Versão Simplificada
"""
from state import ResearchState
from config import Config

def search_web_simple(query: str, max_results: int = 3, verbose: bool = False) -> list:
    """
    Busca simples na web usando DDGS (DuckDuckGo)
    
    Returns:
        list: [{"title": str, "url": str, "snippet": str}, ...]
    """
    try:
        from ddgs import DDGS
        
        if verbose:
            print(f"Query: {query[:60]}...")
        
        results = []
        ddgs = DDGS()
        
        # Método correto: text(query, region='wt-wt', ...)
        search_results = ddgs.text(
            query,  # ← Apenas query como primeiro argumento
            region='wt-wt',  # Worldwide
            safesearch='moderate',
            max_results=max_results
        )
        
        # Processar resultados
        for result in search_results:
            results.append({
                "title": result.get("title", "Sem título"),
                "url": result.get("href", result.get("link", "")),
                "snippet": result.get("body", result.get("snippet", ""))
            })
            
            if len(results) >= max_results:
                break
        
        if verbose:
            print(f"{len(results)} resultados")
        
        return results
    
    except ImportError:
        print("ERRO: Pacote 'ddgs' não instalado")
        print("Execute: pip install ddgs")
        return []
    
    except Exception as e:
        if verbose:
            print(f"Erro na busca: {str(e)}")
        return []

def create_web_searcher_agent(llm, config: Config):
    """
    Cria agente que pesquisa na web (igual ao researcher, mas usa web search)
    """
    
    WEB_RESEARCH_PROMPT = """You are an experienced researcher tasked with investigating a specific subtopic using web search results.

            SUBTOPIC:
            {subtopic}

            WEB SEARCH RESULTS:
            {context}

            Your task: Extract all relevant information about the subtopic from the search results.
            Respond objectively and directly. Cite sources when relevant (Source 1, Source 2, etc).
            If no useful information is found, state clearly.

            ANALYSIS:"""

    def web_searcher_node(state: ResearchState) -> dict:
        """
        Node web searcher: pesquisa TODOS os subtópicos na web
        """
        if config.verbose:
            print("\n" + "="*70)
            print("WEB SEARCHERS - Pesquisando na Internet")
            print("="*70)
        
        subtopics = state["subtopics"]
        results = []
        
        for i, subtopic in enumerate(subtopics, 1):
            if config.verbose:
                print(f"\nSubtópico {i}/{len(subtopics)}: {subtopic}")
            
            try:
                # Buscar na web (3 primeiros resultados)
                if config.verbose:
                    print(f"   🌐 Buscando na web...")
                
                search_results = search_web_simple(
                    subtopic, 
                    max_results=3,
                    verbose=config.verbose
                )
                
                if not search_results:
                    if config.verbose:
                        print(f"Nenhum resultado encontrado")
                    
                    results.append({
                        "subtopic": subtopic,
                        "research_findings": "No information found on the web for this question.",
                        "web_sourcers": [],
                        "status": "completed"
                    })
                    continue
                
                # Construir contexto com os resultados
                context_parts = []
                for j, result in enumerate(search_results, 1):
                    context_parts.append(f"""
Source {j}:
Title: {result['title']}
URL: {result['url']}
Content: {result['snippet']}
""")
                
                context = "\n---\n".join(context_parts)
                
                if config.verbose:
                    print(f"{len(search_results)} resultados recuperados")
                
                # Analisar com LLM
                prompt = WEB_RESEARCH_PROMPT.format(
                    subtopic=subtopic,
                    context=context
                )
                
                response = llm.invoke(prompt)
                findings = response.content if hasattr(response, 'content') else str(response)
                
                if config.verbose:
                    findings_preview = findings[:100].replace('\n', ' ')
                    print(f"Análise: {findings_preview}...")
                
                # Adicionar resultado
                results.append({
                    "subtopic": subtopic,
                    "research_findings": findings,
                    "web_sources": search_results,
                    "status": "completed"
                })
                
            except Exception as e:
                if config.verbose:
                    print(f"Erro: {str(e)}")
                
                results.append({
                    "subtopic": subtopic,
                    "research_findings": f"Error in web search: {str(e)}",
                    "web_sources": [], 
                    "status": "failed"
                })
        
        if config.verbose:
            print(f"\n{len(results)} subtópicos pesquisados")
        
        return {"subagent_results": results}
    
    return web_searcher_node