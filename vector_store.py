"""
Sistema de Vector Store (FAISS + RAG) com cache
"""
from typing import List
import pickle
import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import Config

def get_cache_path(data_dir: str = "data") -> str:
    """Retorna caminho para o cache do vector store"""
    return os.path.join(data_dir, ".vectorstore_cache")

def should_rebuild_cache(data_dir: str = "data") -> bool:
    """
    Verifica se precisa reconstruir o cache
    
    Reconstrói se:
    - Cache não existe
    - Algum .txt foi modificado após a criação do cache
    """
    cache_path = get_cache_path(data_dir)
    
    # Se cache não existe, precisa construir
    if not os.path.exists(cache_path):
        return True
    
    # Pegar timestamp do cache
    cache_mtime = os.path.getmtime(cache_path)
    
    # Verificar se algum .txt é mais novo que o cache
    data_path = Path(data_dir)
    for txt_file in data_path.glob("*.txt"):
        if os.path.getmtime(txt_file) > cache_mtime:
            return True  # Arquivo modificado
    
    return False  # Cache está atualizado

def create_vector_store(documents: List[str], embeddings, config: Config, data_dir: str = "data"):
    """
    Cria ou carrega FAISS vector store (com cache)
    
    Args:
        documents: Lista de strings (documentos)
        embeddings: Modelo de embeddings
        config: Configurações
        data_dir: Pasta dos documentos
        
    Returns:
        FAISS: Vector store indexado
    """
    cache_path = get_cache_path(data_dir)
    
    # Verificar se pode usar cache
    if not should_rebuild_cache(data_dir) and os.path.exists(cache_path):
        if config.verbose:
            print(f"\nCarregando vector store do cache...")
        
        try:
            vectorstore = FAISS.load_local(
                cache_path, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            if config.verbose:
                print("Cache carregado com sucesso")
            
            return vectorstore
        except Exception as e:
            if config.verbose:
                print(f"Erro ao carregar cache: {e}")
                print("Reconstruindo vector store...")
    
    # Construir vector store do zero
    if config.verbose:
        print(f"\nCriando vector store...")
        print(f"   - {len(documents)} documentos")
    
    # Converter strings em Document objects
    docs = [Document(page_content=doc) for doc in documents]
    
    # Dividir em chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_documents(docs)
    
    if config.verbose:
        print(f"   - {len(chunks)} chunks criados")
    
    # Criar índice FAISS
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Salvar cache
    try:
        vectorstore.save_local(cache_path)
        if config.verbose:
            print(f"Cache salvo em: {cache_path}")
    except Exception as e:
        if config.verbose:
            print(f"Erro ao salvar cache: {e}")
    
    if config.verbose:
        print("Vector store criado")
    
    return vectorstore

def search_documents(vectorstore, query: str, k: int = 5) -> List[str]:
    """
    Busca documentos relevantes
    
    Args:
        vectorstore: FAISS vector store
        query: Pergunta/query
        k: Número de documentos a retornar
        
    Returns:
        List[str]: Documentos recuperados
    """
    docs = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]