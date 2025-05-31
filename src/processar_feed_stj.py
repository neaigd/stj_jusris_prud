import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup
import os # Para manipulação de caminhos de arquivo
import requests # Para buscar o feed online
import sqlite3 # Para interagir com o banco de dados SQLite
import time # Para adicionar delays

# --- Configuração ---
feed_url = 'https://scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed'
local_xml_fallback_path = 'data/input/pesquisa_pronta_stj.xml' # Fallback local
output_csv_path = 'data/output/stj_pesquisa_pronta.csv'
db_path = 'data/stj_jurisprudencia.db' # Caminho para o banco de dados

# Lista de User-Agents para tentar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edge/91.0.864.59'
]

# Cabeçalhos comuns para as requisições
COMMON_HEADERS = {
    'Accept': 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,*/*;q=0.7',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# --- Funções do Banco de Dados ---
def inicializar_banco(db_file):
    """Cria o banco de dados e a tabela 'jurisprudencia' se não existirem."""
    conn = None
    try:
        # Garante que o diretório 'data' exista
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jurisprudencia (
                id_pesquisa TEXT PRIMARY KEY,
                titulo TEXT,
                area_direito TEXT,
                sub_area TEXT,
                link_acordaos TEXT,
                link_toc TEXT,
                data_atualizacao TEXT, -- Armazena como TEXT no formato ISO (YYYY-MM-DD HH:MM:SS)
                data_atualizacao_str TEXT -- String original do feed
            )
        ''')
        conn.commit()
        print(f"Banco de dados '{db_file}' inicializado com sucesso.")
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

def inserir_ou_substituir_dados(db_file, dados):
    """Insere ou substitui dados na tabela 'jurisprudencia'.
       'dados' deve ser uma lista de tuplas, cada tupla correspondendo a uma linha.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        # Usamos INSERT OR REPLACE para atualizar registros existentes com base na PRIMARY KEY (id_pesquisa)
        cursor.executemany('''
            INSERT OR REPLACE INTO jurisprudencia (
                id_pesquisa, titulo, area_direito, sub_area,
                link_acordaos, link_toc, data_atualizacao, data_atualizacao_str
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', dados)
        conn.commit()
        print(f"{cursor.rowcount} registros inseridos/atualizados no banco de dados.")
    except sqlite3.Error as e:
        print(f"Erro ao inserir/substituir dados no banco de dados: {e}")
    finally:
        if conn:
            conn.close()

# --- Lógica de Busca do Feed com Fallback ---
def fetch_feed_content():
    """Tenta buscar o feed de várias maneiras, com fallback para arquivo local."""
    xml_content_data = None
    session = requests.Session()

    for i, user_agent in enumerate(USER_AGENTS):
        headers = {**COMMON_HEADERS, 'User-Agent': user_agent}
        try:
            print(f"Tentativa {i+1}/{len(USER_AGENTS)}: Buscando feed de {feed_url} com User-Agent: {user_agent}")
            response = session.get(feed_url, headers=headers, timeout=20) # Timeout reduzido para tentativas
            response.raise_for_status()
            xml_content_data = response.content
            print("Feed baixado com sucesso da URL.")
            return xml_content_data # Retorna o conteúdo se sucesso
        except requests.exceptions.RequestException as e:
            print(f"Tentativa {i+1} falhou: {e}")
            if i < len(USER_AGENTS) - 1:
                print("Aguardando 2 segundos antes da próxima tentativa...")
                time.sleep(2) # Pausa entre tentativas

    # Se todas as tentativas de rede falharem
    print("\nTodas as tentativas de buscar o feed da URL falharam.")
    print(f"Tentando carregar do arquivo local: {local_xml_fallback_path}")
    try:
        if not os.path.exists(local_xml_fallback_path):
            print(f"Erro: Arquivo XML local de fallback não encontrado em '{local_xml_fallback_path}'")
            return None
        with open(local_xml_fallback_path, 'rb') as f: # 'rb' para ler como bytes
            xml_content_data = f.read()
        print(f"Feed carregado com sucesso do arquivo local: {local_xml_fallback_path}")
    except IOError as e:
        print(f"Erro ao ler o arquivo XML local: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar o arquivo XML local: {e}")
        return None

    return xml_content_data

# --- Parsing e Extração ---
xml_content = fetch_feed_content() # Chama a função para obter o conteúdo XML

# Namespace usado no feed Atom
namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
extracted_data = []

if xml_content:
    try:
        # Analisa (parse) o conteúdo XML (seja da web ou local)
        root = etree.fromstring(xml_content)
        entries = root.xpath('//atom:entry', namespaces=namespaces)
        print(f"\nEncontradas {len(entries)} entradas no XML.")

        for entry in entries:
            entry_data = {}

            # 1. ID da Pesquisa (extraindo de <id>)
            id_tag = entry.find('atom:id', namespaces)
            if id_tag is not None and id_tag.text and 'PP=' in id_tag.text:
                entry_data['id_pesquisa'] = id_tag.text.split('PP=')[-1]
            else:
                entry_data['id_pesquisa'] = None

            # 2. Título (<title>)
            title_tag = entry.find('atom:title', namespaces)
            entry_data['titulo'] = title_tag.text.strip() if title_tag is not None and title_tag.text else None

            # 3. Data de Atualização (<updated>)
            updated_tag = entry.find('atom:updated', namespaces)
            entry_data['data_atualizacao_str'] = updated_tag.text if updated_tag is not None else None

            # 4. Link TOC (<link href="...">) - Pega o primeiro link que NÃO tem rel="self"
            link_toc_tag = entry.find("atom:link[@rel!='self']", namespaces) # Procura link sem rel='self'
            if link_toc_tag is None:
                 # Fallback: tenta pegar o primeiro link se a busca específica falhar (pode ser o 'self')
                 link_toc_tag = entry.find("atom:link", namespaces)
            entry_data['link_toc'] = link_toc_tag.get('href') if link_toc_tag is not None else None


            # 5. Extração da Área, Subárea e Link dos Acórdãos (<summary>)
            summary_tag = entry.find('atom:summary', namespaces)
            area_direito = None
            sub_area = None
            link_acordaos = None

            if summary_tag is not None and summary_tag.text:
                # Usa BeautifulSoup para parsear o HTML dentro de <summary>
                soup = BeautifulSoup(summary_tag.text, 'lxml') # 'lxml' é um parser robusto

                # Extrai Área e Subárea de <strong>
                strong_tag = soup.find('strong')
                if strong_tag:
                     # Usa get_text com separador para lidar com <br> ou apenas texto
                    parts = strong_tag.get_text(separator='|', strip=True).split('|')
                    area_direito = parts[0].strip() if len(parts) > 0 else None
                    sub_area = parts[1].strip() if len(parts) > 1 else None # Pode não haver subárea

                # Extrai o link dos acórdãos de <a>
                a_tag = soup.find('a')
                if a_tag and a_tag.has_attr('href'):
                    link_acordaos = a_tag['href']

            entry_data['area_direito'] = area_direito
            entry_data['sub_area'] = sub_area
            entry_data['link_acordaos'] = link_acordaos

            # Adiciona os dados extraídos desta entrada à lista geral
            extracted_data.append(entry_data)

    except etree.XMLSyntaxError as e:
        print(f"Erro de sintaxe ao processar o XML: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processamento do XML: {e}")
    # Não sair do script aqui, pois podemos ter dados vazios e o script deve lidar com isso
else:
    print("Nenhum conteúdo XML para processar (feed online e fallback local falharam ou estavam vazios).")


# --- Criação do DataFrame e Banco de Dados ---
# Proceder mesmo se extracted_data estiver vazio, para que o CSV e BD sejam consistentes (vazios ou preenchidos)
if extracted_data:
    df = pd.DataFrame(extracted_data)

    # --- Limpeza e Conversão de Tipos (Pós-Criação) ---
    # Converter a data de atualização para datetime
    df['data_atualizacao'] = pd.to_datetime(df['data_atualizacao_str'], errors='coerce')
    # Formatar a coluna de data_atualizacao para o formato ISO para SQLite, mantendo NaT se houver erro
    df['data_atualizacao_sqlite'] = df['data_atualizacao'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else None)


    # Reordenar colunas para melhor visualização e para corresponder à ordem da tabela do BD
    df_final = df[[
        'id_pesquisa',
        'titulo',
        'area_direito',
        'sub_area',
        'link_acordaos',
        'link_toc',
        'data_atualizacao_sqlite', # Usar esta para o BD
        'data_atualizacao_str'
    ]]

    # DataFrame para CSV com a coluna de data original (datetime) e a string original
    df_display_csv = df[[
        'id_pesquisa', 'titulo', 'area_direito', 'sub_area', 'link_acordaos',
        'link_toc', 'data_atualizacao', 'data_atualizacao_str'
    ]]

    print("\n--- DataFrame Criado (Primeiras 5 linhas) ---")
    print(df_final.head())
    print(f"\n--- Total de {len(df_final)} registros processados ---")
else:
    print("\nNenhum dado foi extraído para o DataFrame (lista 'extracted_data' está vazia).")
    # Criar DataFrames vazios com as colunas esperadas
    df_final = pd.DataFrame(columns=[
        'id_pesquisa', 'titulo', 'area_direito', 'sub_area',
        'link_acordaos', 'link_toc', 'data_atualizacao_sqlite', 'data_atualizacao_str'
    ])
    df_display_csv = pd.DataFrame(columns=[
        'id_pesquisa', 'titulo', 'area_direito', 'sub_area',
        'link_acordaos', 'link_toc', 'data_atualizacao', 'data_atualizacao_str'
    ])


# --- Salvando em CSV (Opcional) ---
try:
    # Garante que o diretório de output exista
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    # Salva o DataFrame (pode estar vazio se nenhuma data foi extraída)
    df_display_csv.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\nDataFrame salvo com sucesso em CSV: {output_csv_path}")
except Exception as e:
    print(f"\nErro ao salvar o DataFrame em CSV: {e}")

# --- Inicializar e Inserir/Substituir no Banco de Dados ---
inicializar_banco(db_path) # Garante que a tabela exista

# Prepara os dados para inserção no banco de dados (pode ser uma lista vazia)
dados_para_db = [tuple(x) for x in df_final.to_numpy()]
inserir_ou_substituir_dados(db_path, dados_para_db)


print("\nProcessamento concluído.")