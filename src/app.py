import sqlite3
from flask import Flask, jsonify
import os
import argparse
import sys
import json

app = Flask(__name__)

# Define o caminho base do projeto (um nível acima de 'src')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'stj_jurisprudencia.db')
JSON_OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data', 'output', 'jurisprudencia.json')


def get_db_connection(db_path=DATABASE_PATH):
    """Cria uma conexão com o banco de dados."""
    if not os.path.exists(db_path):
        # Raise FileNotFoundError only if the generate_static_json is not called,
        # as generate_static_json has its own check.
        # For the API, it's better to raise and let the endpoint handler catch it.
        if not (len(sys.argv) > 1 and sys.argv[1] == '--generate-json'):
             raise FileNotFoundError(f"Database not found at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Para acessar colunas por nome
    return conn

def generate_static_json():
    """Busca todos os dados do BD e os salva em um arquivo JSON."""
    print(f"Iniciando geração do arquivo JSON estático a partir de: {DATABASE_PATH}")

    if not os.path.exists(DATABASE_PATH):
        print(f"Erro: Arquivo de banco de dados não encontrado em '{DATABASE_PATH}'.")
        print("Por favor, execute o script 'src/processar_feed_stj.py' primeiro.")
        sys.exit(1)

    conn = None
    try:
        conn = get_db_connection(DATABASE_PATH) # Passando explicitamente o path
        cursor = conn.cursor()
        # Usar data_atualizacao para ordenação se for um tipo de data/datetime real no BD
        # Se data_atualizacao é TEXT e no formato ISO, a ordenação textual DESC funciona bem.
        cursor.execute("SELECT id_pesquisa, titulo, area_direito, sub_area, link_acordaos, link_toc, data_atualizacao, data_atualizacao_str FROM jurisprudencia ORDER BY data_atualizacao DESC")
        rows = cursor.fetchall()

        jurisprudencias = [dict(row) for row in rows]

        # Garante que o diretório de output exista
        output_dir = os.path.dirname(JSON_OUTPUT_PATH)
        os.makedirs(output_dir, exist_ok=True)

        with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(jurisprudencias, f, ensure_ascii=False, indent=4)

        print(f"Arquivo JSON gerado com sucesso com {len(jurisprudencias)} registros em: {JSON_OUTPUT_PATH}")

    except sqlite3.Error as e:
        print(f"Erro de banco de dados durante a geração do JSON: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Erro de I/O ao escrever o arquivo JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado durante a geração do JSON: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

@app.route('/api/jurisprudencia', methods=['GET'])
def get_jurisprudencia():
    """Endpoint para buscar todas as jurisprudências."""
    conn = None
    try:
        conn = get_db_connection() # Usa o DATABASE_PATH padrão
        cursor = conn.cursor()
        cursor.execute("SELECT id_pesquisa, titulo, area_direito, sub_area, link_acordaos, link_toc, data_atualizacao, data_atualizacao_str FROM jurisprudencia ORDER BY data_atualizacao DESC")
        rows = cursor.fetchall()

        jurisprudencias = [dict(row) for row in rows]
        return jsonify(jurisprudencias)

    except FileNotFoundError as e:
        app.logger.error(f"Database file not found: {e}")
        return jsonify({"error": "Database file not found. Please run the data processing script first."}), 404
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return jsonify({"error": f"Database query error: {e}"}), 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Servidor Flask para API de Jurisprudência STJ e gerador de JSON estático.")
    parser.add_argument(
        '--generate-json',
        action='store_true',
        help="Gera o arquivo JSON estático com os dados da jurisprudência e sai, em vez de iniciar o servidor Flask."
    )
    args = parser.parse_args()

    if args.generate_json:
        generate_static_json()
        sys.exit(0)
    else:
        # Verifica se o banco de dados existe antes de tentar iniciar o Flask
        # Esta verificação é mais para o modo servidor.
        if not os.path.exists(DATABASE_PATH):
            print(f"AVISO: O arquivo de banco de dados '{DATABASE_PATH}' não foi encontrado.")
            print("Por favor, execute o script 'src/processar_feed_stj.py' para criar e popular o banco de dados.")
            print("O servidor Flask pode não funcionar corretamente até que o banco de dados seja criado.")
            # Decide-se não sair aqui, permitindo que o endpoint /api/jurisprudencia retorne 404 se o BD não existir.

        print("Iniciando servidor Flask...")
        app.run(host='0.0.0.0', port=5000, debug=True)
