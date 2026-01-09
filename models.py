from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEmbeddings
from config import Config

def initialize_llm(config: Config):
    """
    Inicializa o modelo LLM HuggingFace
    
    Returns:
        ChatHuggingFace: Modelo pronto para uso
    """
    if config.verbose:
        print(f"Carregando LLM: {config.llm_model}")
    
    endpoint = HuggingFaceEndpoint(
        repo_id=config.llm_model,
        huggingfacehub_api_token=config.hf_token,
        temperature=config.temperature,
        max_new_tokens=config.max_tokens,
        task="conversational"
    )
    
    llm = ChatHuggingFace(llm=endpoint)
    
    if config.verbose:
        print("LLM carregado")
    
    return llm

def initialize_embeddings(config: Config):
    """
    Inicializa modelo de embeddings MiniLM
    
    Returns:
        HuggingFaceEmbeddings: Modelo de embeddings
    """
    if config.verbose:
        print(f"Carregando embeddings: {config.embedding_model}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=config.embedding_model
    )
    
    if config.verbose:
        print("Embeddings carregados")
    
    return embeddings