"""
Agente Pesquisador - Pesquisa um subtópico específico
"""
from state import ResearchState, SubtopicState
from config import Config
from vector_store import search_documents

def create_researcher_agent(llm, vectorstore, config: Config):
    """
    Cria agente pesquisador que investiga um subtópico
    """
    
    RESEARCH_PROMPT = """You are an experienced researcher tasked with investigating a specific subtopic by consulting provided internal documents.

                        SUBTOPIC:
                        {subtopic}

                        DOCUMENTS RETRIEVED:
                        {context}

                        Your task: Extract all relevant information about the subtopic.
                        Respond objectively and directly. If no information is found, state clearly.

                        ANALYSIS:"""

    def researcher_node(state: ResearchState) -> dict:
        """
        Node pesquisador: pesquisa TODOS os subtópicos em paralelo
        
        Nota: Este node será executado UMA VEZ, mas processará todos subtópicos
        """
        if config.verbose:
            print("\n" + "="*70)
            print("RESEARCHERS - Pesquisando subtópicos")
            print("="*70)
        
        subtopics = state["subtopics"]
        results = []
        
        for i, subtopic in enumerate(subtopics, 1):
            if config.verbose:
                print(f"\nSubtópico {i}/{len(subtopics)}: {subtopic}")
            
            try:
                # Buscar documentos relevantes
                docs = search_documents(
                    vectorstore, 
                    subtopic, 
                    k=config.top_k_retrieval
                )
                
                context = "\n\n---\n\n".join([
                    f"Doc {j+1}:\n{doc[:500]}"  # Limitar tamanho
                    for j, doc in enumerate(docs)
                ])
                
                if config.verbose:
                    print(f"{len(docs)} documentos recuperados")
                
                # Analisar com LLM
                prompt = RESEARCH_PROMPT.format(
                    subtopic=subtopic,
                    context=context
                )
                
                response = llm.invoke(prompt)
                findings = response.content if hasattr(response, 'content') else str(response)
                
                if config.verbose:
                    print(f"Análise: {findings[:100]}...")
                
                # Adicionar resultado
                results.append({
                    "subtopic": subtopic,
                    "research_findings": findings,
                    "status": "completed"
                })
                
            except Exception as e:
                if config.verbose:
                    print(f"Erro: {str(e)}")
                
                results.append({
                    "subtopic": subtopic,
                    "research_findings": f"Erro na pesquisa: {str(e)}",
                    "status": "failed"
                })
        
        if config.verbose:
            print(f"\n{len(results)} subtópicos pesquisados")
        
        return {"subagent_results": results}
    
    return researcher_node

