import sqlite3
import datetime
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stj_jurisprudencia.db')
OUTPUT_MD_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'output', 'relatorio_jurisprudencia.md')

def get_data_from_db(db_path, search_term=None):
    """
    Busca dados no banco de dados SQLite.
    Permite filtrar por um termo de busca nos campos titulo, area_direito e sub_area.
    """
    conn = None
    try:
        if not os.path.exists(db_path):
            print(f"Erro: Arquivo de banco de dados não encontrado em '{db_path}'")
            return []

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        cursor = conn.cursor()

        base_query = "SELECT id_pesquisa, titulo, area_direito, sub_area, link_acordaos, link_toc, data_atualizacao_str FROM jurisprudencia"
        params = []

        if search_term:
            like_term = f"%{search_term}%"
            base_query += " WHERE (titulo LIKE ? OR area_direito LIKE ? OR sub_area LIKE ?)"
            params.extend([like_term, like_term, like_term])

        base_query += " ORDER BY data_atualizacao_str DESC" # Idealmente seria por data_atualizacao (tipo DATE)

        cursor.execute(base_query, params)
        rows = cursor.fetchall()

        data_items = [dict(row) for row in rows]
        return data_items

    except sqlite3.Error as e:
        print(f"Erro no banco de dados ao buscar dados: {e}")
        return []
    except Exception as e:
        print(f"Erro inesperado ao buscar dados do banco: {e}")
        return []
    finally:
        if conn:
            conn.close()

def generate_markdown_report(data_items, report_title="Relatório de Jurisprudência STJ"):
    """
    Gera um relatório em formato Markdown a partir dos dados fornecidos.
    """
    current_date = datetime.date.today().isoformat()

    tags = ["jurisprudencia", "stj"]
    unique_areas = set()
    unique_sub_areas = set()

    for item in data_items:
        if item.get('area_direito'):
            cleaned_area = item['area_direito'].lower().replace(' ', '_').replace('/', '_')
            unique_areas.add(cleaned_area)
        if item.get('sub_area'):
            cleaned_sub_area = item['sub_area'].lower().replace(' ', '_').replace('/', '_')
            unique_sub_areas.add(cleaned_sub_area)

    tags.extend(list(unique_areas))
    tags.extend(list(unique_sub_areas))
    # Garantir que não haja tags duplicadas e remover possíveis None/empty se existirem antes de adicionar
    final_tags = sorted(list(set(tag for tag in tags if tag)))


    # Construir a lista de tags YAML manualmente para garantir o formato correto
    yaml_tags_list = "\n".join([f"  - {tag}" for tag in final_tags])

    frontmatter = f"""---
title: "{report_title}"
date: "{current_date}"
tags:
{yaml_tags_list}
---
"""
    report_body = f"\n# {report_title}\n\n"
    report_body += f"Relatório gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    report_body += f"Total de teses encontradas: {len(data_items)}\n\n"
    report_body += "---\n"

    if not data_items:
        report_body += "Nenhuma tese encontrada para os critérios fornecidos.\n"
        return frontmatter + report_body

    for item in data_items:
        report_body += f"\n## {item.get('titulo', 'Título não disponível')}\n\n"
        report_body += f"- **ID da Pesquisa:** {item.get('id_pesquisa', 'N/A')}\n"
        report_body += f"- **Área do Direito:** {item.get('area_direito', 'N/A')}\n"
        if item.get('sub_area'): # Só adiciona sub_area se existir
            report_body += f"- **Subárea:** {item.get('sub_area')}\n"

        data_str = item.get('data_atualizacao_str', 'N/A')
        # Tentar formatar a data se for uma string ISO compatível
        try:
            if data_str and data_str != 'N/A':
                parsed_date = datetime.datetime.fromisoformat(data_str.replace('Z', '+00:00')) # Lida com 'Z'
                data_formatada = parsed_date.strftime('%d/%m/%Y %H:%M:%S %Z')
            else:
                data_formatada = 'N/A'
        except ValueError:
            data_formatada = data_str # Usa a string original se não puder parsear

        report_body += f"- **Data de Atualização (original):** {data_formatada}\n"

        if item.get('link_toc'):
            report_body += f"- **Link TOC:** [Acessar Tabela de Conteúdo]({item['link_toc']})\n"
        if item.get('link_acordaos'):
            report_body += f"- **Link Acórdãos:** [Ver Acórdãos Relacionados]({item['link_acordaos']})\n"

        report_body += "\n---\n"

    return frontmatter + "\n" + report_body

if __name__ == '__main__':
    print(f"Iniciando geração de relatório...")
    # Usar os caminhos definidos no início do script
    # db_file = 'data/stj_jurisprudencia.db' # Relativo ao root do projeto
    # output_md_file = 'data/output/relatorio_jurisprudencia.md' # Relativo ao root

    # Criar o diretório de output se não existir
    output_dir = os.path.dirname(OUTPUT_MD_PATH)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Diretório '{output_dir}' criado.")
        except OSError as e:
            print(f"Erro ao criar diretório '{output_dir}': {e}")
            exit()

    try:
        # Exemplo de busca com termo (pode ser None para buscar todos)
        # search_query = "RECURSOS"
        search_query = None # Para relatório geral

        print(f"Buscando dados no banco: {DATABASE_PATH}")
        if search_query:
            print(f"Termo de busca: '{search_query}'")

        all_data = get_data_from_db(DATABASE_PATH, search_term=search_query)

        if all_data:
            report_title_dinamico = "Relatório de Jurisprudência STJ"
            if search_query:
                report_title_dinamico += f" (Busca: {search_query})"

            print(f"Gerando relatório Markdown com {len(all_data)} itens...")
            markdown_content = generate_markdown_report(all_data, report_title=report_title_dinamico)

            with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Relatório salvo com sucesso em: {OUTPUT_MD_PATH}")
        else:
            print("Nenhum dado encontrado para gerar o relatório.")
            # Mesmo sem dados, podemos gerar um relatório vazio com frontmatter
            markdown_content = generate_markdown_report([], report_title="Relatório de Jurisprudência STJ (Vazio)")
            with open(OUTPUT_MD_PATH, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Relatório vazio salvo em: {OUTPUT_MD_PATH}")

    except FileNotFoundError as e: # Especificamente para o get_db_connection caso o DB não exista
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Ocorreu um erro geral durante a geração do relatório: {e}")
