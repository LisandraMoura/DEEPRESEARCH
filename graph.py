"""
Construção do grafo LangGraph com Supervisor Pattern
"""
from langgraph.graph import StateGraph, START, END
from state import ResearchState
from config import Config


def build_supervisor_graph(llm, vectorstore, config: Config, use_web_search: bool = False):
    """
    Constrói grafo: Supervisor → Researchers/WebSearch → Synthesis
    """
    from agents.supervisor import create_supervisor_agent
    from agents.researcher import create_researcher_agent
    from agents.web_searcher import create_web_searcher_agent
    from agents.synthesis import create_synthesis_agent
    
    if config.verbose:
        print("\n Construindo grafo com Supervisor Pattern...")
        search_type = "Web Search" if use_web_search else "RAG Interno"
        print(f"Modo de pesquisa: {search_type}")
    
    # Criar agents
    supervisor = create_supervisor_agent(llm, config)
    synthesis = create_synthesis_agent(llm, config)

    if use_web_search:
        researcher = create_web_searcher_agent(llm, config)
        researcher_name = "web_searcher"
    else:
        researcher = create_researcher_agent(llm, vectorstore, config)
        researcher_name = "researcher"
    
    # Construir grafo
    graph = StateGraph(ResearchState)
    
    graph.add_node("supervisor", supervisor)
    graph.add_node(researcher_name, researcher)
    graph.add_node("synthesis", synthesis)
    
    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", researcher_name)
    graph.add_edge(researcher_name, "synthesis")
    graph.add_edge("synthesis", END)
    
    if config.verbose:
        print("Grafo construído")
    
    return graph.compile()