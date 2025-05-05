import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup
import os # Para manipulação de caminhos de arquivo

# --- Configuração ---
# Certifique-se que este caminho está correto ou que o XML está no mesmo diretório
# Use o caminho absoluto que você mencionou se necessário.
# xml_file_path = '/media/peixoto/stuff/stj_juris_prud/pesquisa_pronta_stj.xml'
xml_file_path = 'pesquisa_pronta_stj.xml' # Assume que está no mesmo diretório

output_csv_path = 'stj_pesquisa_pronta.csv'
output_parquet_path = 'stj_pesquisa_pronta.parquet'

# --- Verificação do Arquivo ---
if not os.path.exists(xml_file_path):
    print(f"Erro: Arquivo XML não encontrado em '{xml_file_path}'")
    exit() # Sai do script se o arquivo não for encontrado

# --- Parsing e Extração ---
print(f"Lendo e processando o arquivo: {xml_file_path}")

# Namespace usado no feed Atom
namespaces = {'atom': 'http://www.w3.org/2005/Atom'}

extracted_data = []

try:
    # Analisa (parse) o arquivo XML
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    # Encontra todas as tags <entry> dentro do feed
    # Usamos o namespace 'atom' definido acima
    entries = root.xpath('//atom:entry', namespaces=namespaces)

    print(f"Encontradas {len(entries)} entradas no feed.")

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
    exit()
except Exception as e:
    print(f"Ocorreu um erro inesperado durante o processamento: {e}")
    exit()


# --- Criação do DataFrame ---
if extracted_data:
    df = pd.DataFrame(extracted_data)

    # --- Limpeza e Conversão de Tipos (Pós-Criação) ---
    # Converter a data de atualização para datetime (se necessário)
    df['data_atualizacao'] = pd.to_datetime(df['data_atualizacao_str'], errors='coerce') # 'coerce' transforma erros em NaT (Not a Time)
    # Remover a coluna de string original se a conversão foi bem-sucedida e desejado
    # df = df.drop(columns=['data_atualizacao_str']) # Opcional

    # Reordenar colunas para melhor visualização (opcional)
    df = df[[
        'id_pesquisa',
        'titulo',
        'area_direito',
        'sub_area',
        'link_acordaos',
        'link_toc',
        'data_atualizacao',
        'data_atualizacao_str' # Mantendo a string original para referência
    ]]


    print("\n--- DataFrame Criado ---")
    print(df.info())
    print("\n--- Primeiras 5 linhas ---")
    print(df.head())
    print("\n--- Últimas 5 linhas ---")
    print(df.tail())


    # --- Salvando o DataFrame (Opcional) ---
    try:
        df.to_csv(output_csv_path, index=False, encoding='utf-8-sig') # utf-8-sig é bom para compatibilidade com Excel
        print(f"\nDataFrame salvo com sucesso em CSV: {output_csv_path}")
    except Exception as e:
        print(f"\nErro ao salvar o DataFrame em CSV: {e}")

    try:
        # Parquet é geralmente mais eficiente para armazenamento e leitura posterior
        df.to_parquet(output_parquet_path, index=False)
        print(f"DataFrame salvo com sucesso em Parquet: {output_parquet_path}")
    except Exception as e:
        print(f"Erro ao salvar o DataFrame em Parquet: {e}")


else:
    print("\nNenhum dado foi extraído do arquivo XML.")

print("\nProcessamento concluído.")