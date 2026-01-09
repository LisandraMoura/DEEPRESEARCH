from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configurações do sistema de Deep Research"""
    
    # === MODELOS ===
    llm_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_token: Optional[str] = None
    
    # === RAG ===
    chunk_size: int = 1024
    chunk_overlap: int = 500
    top_k_retrieval: int = 5
    
    # === LLM ===
    temperature: float = 0.7
    max_tokens: int = 1024
    
    # === SUPERVISOR ===
    max_subagents: int = 3  # Máximo de pesquisas paralelas
    
    # === DEBUG ===
    verbose: bool = True
    
    def __post_init__(self):
        """Validações"""
        if self.hf_token is None:
            print("AVISO: HF_TOKEN não configurado")