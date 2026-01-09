"""
Script principal de execução
"""
import argparse
import os
from dotenv import load_dotenv
from config import Config
from models import initialize_llm, initialize_embeddings
from utils.document_loader import load_documents_from_data
from utils.file_saver import save_research_results, list_research_files
from vector_store import create_vector_store
from state import create_initial_state
from graph import build_supervisor_graph

load_dotenv()

def parse_arguments():
    """
    Parse argumentos da linha de comando
    """
    parser = argparse.ArgumentParser(
        description='Deep Research System - Supervisor Pattern',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Exemplos de uso:

        # Busca web com pergunta customizada
        python main.py --question "What are iPhone repair tools?"
        
        # Não salvar fontes web
        python main.py --question "Test query" --no-save-sources
        
        # Usar RAG interno
        python main.py --question "Como funciona OAuth?" --no-web
        
        # Listar pesquisas anteriores
        python main.py --list
        """
    )
    
    # Argumentos
    parser.add_argument('-q', '--question', type=str, default=None, help='Pergunta para pesquisar')
    parser.add_argument('--web', action='store_true', default=True, help='Usar busca web (padrão)')
    parser.add_argument('--no-web', action='store_true', help='Usar RAG interno')
    parser.add_argument('-s', '--subagents', type=int, default=3, help='Número de subtópicos (padrão: 3)')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso')
    parser.add_argument('--data-dir', type=str, default='data', help='Diretório de dados')
    parser.add_argument('--no-save', action='store_true', help='Não salvar resultado')
    parser.add_argument('--save-sources', action='store_true', default=True, help='Salvar fontes web (padrão: True)')
    parser.add_argument('--no-save-sources', action='store_true', help='Não salvar fontes web')
    parser.add_argument('--list', action='store_true', help='Listar pesquisas anteriores')
    parser.add_argument('--token', type=str, default=None, help='HuggingFace token')
    
    return parser.parse_args()

def show_previous_researches(data_dir: str = "data", limit: int = 10):
    """Exibe pesquisas anteriores"""
    print("="*70)
    print("📚 PESQUISAS ANTERIORES")
    print("="*70)
    
    files = list_research_files(data_dir, limit=limit)
    
    if not files:
        print("\nℹ️  Nenhuma pesquisa salva encontrada")
        return
    
    # Agrupar por base filename
    grouped = {}
    for file_info in files:
        base = file_info['filename'].rsplit('_', 3)[0]  # Remove timestamp
        if base not in grouped:
            grouped[base] = []
        grouped[base].append(file_info)
    
    print(f"\n🔍 {len(grouped)} pesquisas encontradas:\n")
    
    for i, (base, group) in enumerate(grouped.items(), 1):
        topic = group[0]['topic'].title()
        modified = group[0]['modified']
        
        print(f"{i}. {topic}")
        print(f"   📅 {modified.strftime('%d/%m/%Y %H:%M:%S')}")
        
        for file_info in group:
            if file_info['type'] == 'formatted':
                print(f"   📄 {file_info['filename']} (Relatório, {file_info['size']:,} bytes)")
            elif file_info['type'] == 'web_sources':
                print(f"   🌐 {file_info['filename']} (Fontes Web, {file_info['size']:,} bytes)")
        print()

def main():
    """Execução principal"""
    
    # Parse argumentos
    args = parse_arguments()
    
    # Se --list, mostrar pesquisas e sair
    if args.list:
        show_previous_researches(args.data_dir)
        return
    
    # Configurar
    USE_WEB_SEARCH = not args.no_web
    VERBOSE = not args.quiet
    SAVE_RESULTS = not args.no_save
    SAVE_SOURCES = args.save_sources and not args.no_save_sources  # ← CORREÇÃO
    
    if VERBOSE:
        print("="*70)
        print("DEEP RESEARCH - SUPERVISOR PATTERN")
        print("="*70)
    
    # === 1. CONFIGURAÇÃO ===
    hf_token = args.token or os.getenv('HF_TOKEN')
    config = Config(
        hf_token=hf_token,
        verbose=VERBOSE,
        max_subagents=args.subagents
    )
    
    if VERBOSE:
        print(f"\nModo: {'BUSCA WEB' if USE_WEB_SEARCH else 'RAG INTERNO'}")
        print(f"Subtópicos: {args.subagents}")
        print(f"Auto-save: {'Sim' if SAVE_RESULTS else 'Não'}")
        if SAVE_SOURCES:  # ← CORREÇÃO (era SAVE_RAW)
            print(f"Salvar fontes web: Sim")
    
    # === 2. INICIALIZAR MODELOS ===
    if VERBOSE:
        print("\nInicializando modelos...")
    
    llm = initialize_llm(config)
    
    # === 3. CARREGAR DOCUMENTOS E CRIAR VECTOR STORE ===
    if USE_WEB_SEARCH:
        embeddings = None
        vectorstore = None
        documents = []
        
        if VERBOSE:
            print("   Modo Web Search: RAG desabilitado")
    else:
        if VERBOSE:
            print(f"   Carregando documentos de: {args.data_dir}/")
        
        documents = load_documents_from_data(args.data_dir)
        
        if not documents:
            print(f"\n❌ ERRO: Nenhum documento encontrado em {args.data_dir}/")
            print(f"   Por favor, adicione arquivos .txt no diretório {args.data_dir}/")
            print(f"   Ou use --web para busca web")
            return
        
        embeddings = initialize_embeddings(config)
        vectorstore = create_vector_store(
            documents, 
            embeddings, 
            config, 
            data_dir=args.data_dir
        )
    
    # === 4. CONSTRUIR GRAFO ===
    graph = build_supervisor_graph(
        llm, 
        vectorstore, 
        config, 
        use_web_search=USE_WEB_SEARCH
    )
    
    # === 5. PERGUNTA ===
    if args.question:
        question = args.question
    else:
        question = "What are the tools I need to repair an iPhone 15 Pro Max?"
        if VERBOSE:
            print(f"\nℹ️  Usando pergunta padrão (use --question para customizar)")
    
    if VERBOSE:
        print("\n" + "="*70)
        print(f"PERGUNTA: {question}")
        print("="*70)
    
    # === 6. EXECUTAR ===
    initial_state = create_initial_state(question, documents)
    result = graph.invoke(initial_state)
    
    # === 7. SALVAR RESULTADOS ===
    if SAVE_RESULTS:
        try:
            saved_paths = save_research_results(
                question=result['user_question'],
                subtopics=result['subtopics'],
                subagent_results=result['subagent_results'],
                final_answer=result['final_answer'],
                output_dir=args.data_dir,
                save_web_sources=SAVE_SOURCES
            )
            
            if VERBOSE:
                print(f"\n💾 Resultados salvos:")
                print(f"   📄 Relatório: {saved_paths['formatted']}")
                if 'web_sources' in saved_paths:
                    print(f"   🌐 Fontes Web: {saved_paths['web_sources']}")
        except Exception as e:
            if VERBOSE:
                print(f"\n⚠️  Erro ao salvar: {str(e)}")
    
    # === 8. EXIBIR RESULTADO ===
    if VERBOSE:
        print("\n" + "="*70)
        print("RESULTADO FINAL")
        print("="*70)
        
        print(f"\nPergunta: {result['user_question']}")
        
        print(f"\nSubtópicos ({len(result['subtopics'])}):")
        for i, topic in enumerate(result['subtopics'], 1):
            print(f"   {i}. {topic}")
        
        print(f"\nPesquisas ({len(result['subagent_results'])}):")
        for res in result['subagent_results']:
            status = "✅" if res['status'] == 'completed' else "❌"
            print(f"   {status} {res['subtopic']}")
        
        print(f"\nRESPOSTA FINAL:")
        print("-" * 70)
    
    # Sempre exibir resposta final
    print(result['final_answer'])
    
    if VERBOSE:
        print("-" * 70)

if __name__ == "__main__":
    main()