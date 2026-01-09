"""
Carregador simples de documentos TXT
"""
import os
from pathlib import Path
from typing import List

def load_documents_from_data(data_dir: str = "data", verbose: bool = True) -> List[str]:
    """
    Carrega TODOS os arquivos .txt da pasta data/
    
    Args:
        data_dir: Caminho para a pasta (padrão: "data")
        verbose: Mostrar logs
        
    Returns:
        List[str]: Lista com o conteúdo de cada arquivo
    """
    if verbose:
        print("\n" + "="*70)
        print("CARREGANDO DOCUMENTOS")
        print("="*70)
        print(f"Pasta: {data_dir}/")
    
    # Verificar se pasta existe
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"❌ Pasta não encontrada: {data_dir}/")
    
    # Buscar todos os .txt
    txt_files = sorted(data_path.glob("*.txt"))
    
    if not txt_files:
        raise ValueError(f"❌ Nenhum arquivo .txt encontrado em {data_dir}/")
    
    # Carregar cada arquivo
    documents = []
    
    for filepath in txt_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content:  # Apenas se não estiver vazio
                documents.append(content)
                
                if verbose:
                    filename = filepath.name
                    char_count = len(content)
                    line_count = content.count('\n') + 1
                    print(f"{filename:<30} ({char_count:>6} chars, {line_count:>4} linhas)")
            else:
                if verbose:
                    print(f"{filepath.name} (vazio, ignorado)")
                    
        except Exception as e:
            if verbose:
                print(f"{filepath.name}: Erro - {str(e)}")
    
    if not documents:
        raise ValueError(f"Nenhum documento válido carregado de {data_dir}/")
    
    if verbose:
        total_chars = sum(len(doc) for doc in documents)
        print(f"\nTotal: {len(documents)} documentos ({total_chars:,} caracteres)")
        print("="*70)
    
    return documents