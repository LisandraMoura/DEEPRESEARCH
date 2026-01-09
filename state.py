from typing import TypedDict, List, Dict, Annotated
import operator

class SubtopicState(TypedDict):
    """Estado de um subtópico individual"""
    subtopic: str                    # Nome do subtópico
    research_findings: str           # O que foi encontrado
    status: str                      # "pending", "completed", "failed"

class ResearchState(TypedDict):
    """Estado global do sistema"""
    
    # === INPUT ===
    user_question: str               # Pergunta original
    documents: List[str]             # Documentos para pesquisar
    
    # === SUPERVISOR ===
    subtopics: List[str]             # Lista de subtópicos gerados
    
    # === RESEARCH (Paralelo) ===
    # Annotated com operator.add permite acumular resultados de múltiplos agentes
    subagent_results: Annotated[List[SubtopicState], operator.add]
    
    # === SYNTHESIS ===
    final_answer: str                # Resposta final compilada

def create_initial_state(question: str, documents: List[str]) -> ResearchState:
    """Cria estado inicial"""
    return {
        "user_question": question,
        "documents": documents,
        "subtopics": [],
        "subagent_results": [],
        "final_answer": ""
    }