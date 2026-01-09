"""
Agente Supervisor - Divide pergunta em subtópicos
"""
from typing import List
from state import ResearchState
from config import Config

def create_supervisor_agent(llm, config: Config):
    """
    Cria o agente supervisor que divide a pergunta em subtópicos
    """
    
    SUPERVISOR_PROMPT = """You are an experienced research planner.

            Your task is to break down a complex question into multiple independent subtopics for parallel research,
            seeking to place concepts or keywords that are relevant to each subtopic.

            USER QUESTION:
            {question}

            Your task is to divide the user's question into {max_subagents} specific and independent questions that can be answered by consulting internal documents.
            RULES:
            1. Each subtopic must be completely INDEPENDENT
            2. Together, the subtopics must cover the ENTIRE question
            3. Subtopics must not overlap
            4. Each subtopic must be specific and verifiable

            ANSWER FORMAT (numbered list only, no explanations, exactly {max_subagents} lines):
            1. [Specific question]
            2. [Specific question]
            3. [Specific question]
            ...

            SUBTOPICS:
            """

    def supervisor_node(state: ResearchState) -> dict:
        """
        Node supervisor: divide pergunta em subtópicos
        """
        if config.verbose:
            print("\n" + "="*70)
            print("SUPERVISOR - Dividindo pergunta em subtópicos")
            print("="*70)
        
        question = state["user_question"]
        
        if config.verbose:
            print(f"\nPergunta: {question}")
            print(f"Gerando {config.max_subagents} subtópicos...")
        
        # LLM gera subtópicos
        prompt = SUPERVISOR_PROMPT.format(
            question=question,
            max_subagents=config.max_subagents
        )
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse subtópicos
        subtopics = []
        for line in response_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numeração
                item = line.split('.', 1)[-1].strip()
                item = item.lstrip('- ').strip()
                if item and len(subtopics) < config.max_subagents:
                    subtopics.append(item)
        
        # Garantir que temos exatamente max_subagents
        if len(subtopics) < config.max_subagents:
            print(f"Apenas {len(subtopics)} subtópicos gerados")
        
        if config.verbose:
            print(f"\nSubtópicos gerados:")
            for i, topic in enumerate(subtopics, 1):
                print(f"   {i}. {topic}")
        
        return {"subtopics": subtopics}
    
    return supervisor_node