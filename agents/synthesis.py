from state import ResearchState, SubtopicState
from config import Config

def create_synthesis_agent(llm, config: Config):
    """
    Cria agente de síntese que compila resultados em resposta única
    """
    
    SYNTHESIS_PROMPT = """You are an agent who answers complex questions by compiling results from multiple internal searches.
        Use all relevant information found to create a complete and coherent answer.

        USER QUESTION:
        {question}

        RESEARCH RESULTS:
        {research_results}

        Your task: Create a UNIQUE, COHERENT, and COMPLETE answer that addresses the user's original question.

        CRITICAL RULES:

        1. Write in FLUID PROSE (normal paragraphs), DO NOT use bullet points or lists.
        2. Integrate ALL relevant information into a continuous text.
        3. If any information was not found, mention it naturally in the text.
        4. Be OBJECTIVE and DIRECT.
        5. Use clear and accessible language.
        6. DO NOT repeat the structure of subtopics - create NEW text.
        7. DO NOT use excessive markdown formatting (no **, ###, etc.).

        ANSWER FORMAT:

        [Introductory paragraph directly answering the question]

        [Subsequent paragraphs with specific details found]

        [Final paragraph with conclusion or next steps, if applicable]

        ANSWER:"""

    def synthesis_node(state: ResearchState) -> dict:
        """
        Node de síntese: compila todos os resultados em resposta única
        """
        if config.verbose:
            print("\n" + "="*70)
            print("SYNTHESIS - Compilando resposta final")
            print("="*70)
        
        question = state["user_question"]
        subagent_results = state["subagent_results"]
        
        # Formatar resultados da pesquisa
        research_results = []
        
        for i, result in enumerate(subagent_results, 1):
            status = "ENCONTRADO" if result['status'] == 'completed' else "❌ ERRO"
            
            research_results.append(f"""
PESQUISA {i} - {status}
Pergunta: {result['subtopic']}
Resultado: {result['research_findings']}
""")
        
        research_text = "\n".join(research_results)
        
        if config.verbose:
            print(f"\nCompilando {len(subagent_results)} resultados...")
        
        try:
            # LLM compila resposta final
            prompt = SYNTHESIS_PROMPT.format(
                question=question,
                research_results=research_text
            )
            
            response = llm.invoke(prompt)
            final_answer = response.content if hasattr(response, 'content') else str(response)
            
            # Limpar resposta (remover markdown excessivo)
            final_answer = final_answer.strip()
            
            # Remover possíveis cabeçalhos que o LLM adicionar
            lines = final_answer.split('\n')
            clean_lines = []
            
            for line in lines:
                # Pular linhas que são apenas cabeçalhos markdown
                if line.strip().startswith('#'):
                    continue
                # Pular linhas vazias duplicadas
                if line.strip() == '' and clean_lines and clean_lines[-1].strip() == '':
                    continue
                clean_lines.append(line)
            
            final_answer = '\n'.join(clean_lines).strip()
            
            if config.verbose:
                print(f"\n✅ Resposta compilada ({len(final_answer)} caracteres)")
            
            return {"final_answer": final_answer}
            
        except Exception as e:
            if config.verbose:
                print(f"\n❌ Erro na síntese: {str(e)}")
            
            # Fallback: concatenação simples
            fallback = f"Com base na pesquisa sobre '{question}':\n\n"
            
            for result in subagent_results:
                if result['status'] == 'completed':
                    fallback += f"{result['research_findings']}\n\n"
            
            return {"final_answer": fallback}
    
    return synthesis_node