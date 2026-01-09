"""
Utilitários para salvar resultados de pesquisa
"""
import os
import json
from datetime import datetime
from typing import Dict, List
import re

def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Sanitiza texto para usar como nome de arquivo"""
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'_+', '_', text)
    text = text.lower().strip('_')
    
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')
    
    return text

def generate_filename(topic: str, extension: str = "txt") -> str:
    """Gera nome de arquivo: topic_HHMMSS_DDMMYYYY.ext"""
    now = datetime.now()
    clean_topic = sanitize_filename(topic)
    time_str = now.strftime("%H%M%S")
    date_str = now.strftime("%d%m%Y")
    filename = f"{clean_topic}_{time_str}_{date_str}.{extension}"
    return filename

def save_web_sources_json(
    question: str,
    subtopics: List[str],
    subagent_results: List[Dict],
    output_dir: str = "data"
) -> str:
    """
    Salva APENAS as fontes web brutas em JSON (SNIPPETS COMPLETOS)
    
    ← RENOMEADO de save_web_sources para save_web_sources_json
    
    Args:
        question: Pergunta original
        subtopics: Lista de subtópicos
        subagent_results: Resultados com web_sources
        output_dir: Diretório de saída
        
    Returns:
        str: Caminho do arquivo salvo
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Gerar nome do arquivo
    filename = generate_filename(question, extension='json')
    filename = filename.replace('.json', '_web_sources.json')
    filepath = os.path.join(output_dir, filename)
    
    # Estrutura de dados
    web_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%d/%m/%Y'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'query': question
        },
        'subtopics': subtopics,
        'web_searches': []
    }
    
    # Extrair fontes web de cada pesquisa (COMPLETAS)
    for i, result in enumerate(subagent_results, 1):
        search_data = {
            'search_number': i,
            'subtopic': result['subtopic'],
            'status': result['status'],
            'sources': result.get('web_sources', [])
        }
        web_data['web_searches'].append(search_data)
    
    # Salvar JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    
    return filepath

def save_research_results(
    question: str,
    subtopics: List[str],
    subagent_results: List[Dict],
    final_answer: str,
    output_dir: str = "data",
    save_web_sources: bool = False  # ← Parâmetro booleano
) -> Dict[str, str]:
    """
    Salva resultados da pesquisa
    
    Args:
        question: Pergunta original
        subtopics: Lista de subtópicos
        subagent_results: Resultados dos subagentes
        final_answer: Resposta final compilada
        output_dir: Diretório de saída
        save_web_sources: Se True, salva fontes web em JSON separado
        
    Returns:
        Dict: {'formatted': path_txt, 'web_sources': path_json}
    """
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = generate_filename(question, extension='')
    base_filename = base_filename.rstrip('.')
    
    result_paths = {}
    
    # === 1. SALVAR RELATÓRIO FORMATADO (.txt) ===
    txt_filename = f"{base_filename}.txt"
    txt_filepath = os.path.join(output_dir, txt_filename)
    
    content = []
    content.append("="*70)
    content.append("DEEP RESEARCH REPORT")
    content.append("="*70)
    content.append("")
    
    # Metadados
    content.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    content.append(f"Pergunta: {question}")
    content.append("")
    
    # Subtópicos
    content.append("-"*70)
    content.append("SUBTÓPICOS PESQUISADOS")
    content.append("-"*70)
    for i, topic in enumerate(subtopics, 1):
        content.append(f"{i}. {topic}")
    content.append("")
    
    # Resultados individuais COM FONTES
    content.append("-"*70)
    content.append("RESULTADOS DETALHADOS")
    content.append("-"*70)
    for i, result in enumerate(subagent_results, 1):
        status = "✅ ENCONTRADO" if result['status'] == 'completed' else "❌ ERRO"
        content.append(f"\n### Pesquisa {i} - {status}")
        content.append(f"Pergunta: {result['subtopic']}")
        
        # ADICIONAR FONTES WEB (TRUNCADAS NO TXT)
        web_sources = result.get('web_sources', [])
        if web_sources:
            content.append(f"\nFontes Web ({len(web_sources)}):")
            for j, source in enumerate(web_sources, 1):
                content.append(f"  {j}. {source['title']}")
                content.append(f"     URL: {source['url']}")
                
                # Truncar snippet no TXT
                snippet = source['snippet']
                if len(snippet) > 200:
                    snippet_preview = snippet[:200] + "..."
                else:
                    snippet_preview = snippet
                
                content.append(f"     Snippet: {snippet_preview}")
        
        content.append(f"\nAnálise do LLM:")
        content.append(result['research_findings'])
        content.append("")
    
    # Resposta final
    content.append("="*70)
    content.append("RESPOSTA FINAL COMPILADA")
    content.append("="*70)
    content.append(final_answer)
    content.append("")
    
    # Nota sobre fontes completas
    if save_web_sources:
        content.append("="*70)
        content.append("NOTA: Snippets completos das fontes web estão salvos no arquivo")
        content.append(f"      {base_filename}_web_sources.json")
        content.append("="*70)
    
    content.append("")
    
    # Salvar TXT
    with open(txt_filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    result_paths['formatted'] = txt_filepath
    
    # === 2. SALVAR FONTES WEB EM JSON SEPARADO ===
    if save_web_sources:
        json_filepath = save_web_sources_json(  # ← CORREÇÃO: Chamar função renomeada
            question,
            subtopics,
            subagent_results,
            output_dir
        )
        result_paths['web_sources'] = json_filepath
    
    return result_paths

def list_research_files(data_dir: str = "data", limit: int = 10) -> List[Dict]:
    """Lista arquivos de pesquisa salvos"""
    if not os.path.exists(data_dir):
        return []
    
    files = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt') or filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            stat = os.stat(filepath)
            topic = filename.rsplit('_', 2)[0].replace('_', ' ')
            
            # Tipo de arquivo
            if filename.endswith('_web_sources.json'):
                file_type = 'web_sources'
            elif filename.endswith('.txt'):
                file_type = 'formatted'
            else:
                file_type = 'other'
            
            files.append({
                'filename': filename,
                'filepath': filepath,
                'topic': topic,
                'type': file_type,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files[:limit]