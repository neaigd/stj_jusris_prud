# STJ Jurisprudência em Teses Viewer

## Visão Geral

Este projeto visa fornecer uma interface web amigável para visualizar, pesquisar e gerar relatórios a partir do feed "Jurisprudência em Teses" do Superior Tribunal de Justiça (STJ) do Brasil. O conteúdo do feed é processado, armazenado em um banco de dados local e disponibilizado através de uma página estática hospedada no GitHub Pages, com atualizações automáticas via GitHub Actions.

## Funcionalidades

*   **Processamento Automatizado de Feed:** Busca e processa o feed RSS do STJ ([https://scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed](https://scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed)).
*   **Armazenamento de Dados:** As teses e informações relacionadas são armazenadas em um banco de dados SQLite (`data/stj_jurisprudencia.db`).
*   **Interface Web Dinâmica:**
    *   Exibe as teses de jurisprudência em um layout moderno e organizado (tema escuro).
    *   Permite a busca por palavras-chave nos títulos e conteúdo das teses.
    *   Links para o "Índice/Tabela de Conteúdo" (TOC) e "Acórdãos" diretamente na página do STJ (quando disponíveis).
*   **Geração de Relatórios:**
    *   Permite o download de relatórios em formato Markdown, compatíveis com o Obsidian.
    *   Os relatórios incluem frontmatter YAML com título, data e tags (geradas a partir da área do direito e subárea).
    *   Os relatórios podem ser gerados para o conjunto completo de dados ou para os resultados de uma busca específica.
*   **Automação com GitHub Actions:**
    *   Atualiza o banco de dados e os arquivos de dados estáticos (JSON para o frontend, relatório Markdown principal) diariamente e a cada push na branch `main`.
    *   Realiza o deploy automático da aplicação no GitHub Pages.

## Arquitetura Técnica

*   **Backend (Scripts Python):**
    *   `src/processar_feed_stj.py`: Responsável por buscar o feed RSS, processar os dados e popular/atualizar o banco de dados SQLite. Inclui fallback para um arquivo XML local caso o feed ao vivo não esteja acessível.
    *   `src/app.py`:
        *   Pode rodar como um servidor Flask local para desenvolvimento e visualização da API.
        *   Possui um modo CLI (`--generate-json`) para gerar o arquivo `data/output/jurisprudencia.json` consumido pelo frontend.
    *   `src/report_generator.py`: Script CLI para gerar relatórios detalhados em Markdown a partir do banco de dados.
*   **Banco de Dados:** SQLite (`data/stj_jurisprudencia.db`).
*   **Frontend:** HTML (`docs/index.html`), CSS (`docs/style.css`), e JavaScript (`docs/script.js`) puros. Não utiliza frameworks complexos, garantindo leveza e fácil deploy no GitHub Pages.
*   **CI/CD:** GitHub Actions (`.github/workflows/data_processing_and_deploy.yml`) para automação do processamento de dados e deploy.

## Como Funciona

1.  **Coleta de Dados:** Um workflow do GitHub Actions executa `src/processar_feed_stj.py` periodicamente. Este script tenta buscar o feed RSS do STJ. Se falhar (e.g., devido a bloqueios), ele utiliza um arquivo XML local (`data/input/pesquisa_pronta_stj.xml`) como fonte de dados. As informações são salvas/atualizadas no banco de dados SQLite.
2.  **Geração de Dados Estáticos:** O mesmo workflow executa `src/app.py --generate-json` para criar o arquivo `data/output/jurisprudencia.json` e `src/report_generator.py` para criar `data/output/relatorio_jurisprudencia.md`.
3.  **Commit e Push:** As alterações nos arquivos de dados (banco de dados, JSON, relatório MD) são commitadas de volta ao repositório.
4.  **Deploy no GitHub Pages:** O workflow então realiza o deploy do conteúdo da pasta `docs/` e dos arquivos gerados em `data/output/` para o GitHub Pages.
5.  **Visualização:** O usuário acessa a URL do GitHub Pages, onde o HTML/CSS/JS carregam o `jurisprudencia.json` para exibir os dados e fornecer as funcionalidades de busca e geração de relatório.

## Configuração para Desenvolvimento Local

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/<SEU_USUARIO>/<NOME_DO_REPOSITORIO>.git
    cd <NOME_DO_REPOSITORIO>
    ```
2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate    # Windows
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute o processamento de dados (para popular o banco de dados localmente):**
    *   Certifique-se que `data/input/pesquisa_pronta_stj.xml` existe se o feed ao vivo estiver bloqueado.
    ```bash
    python src/processar_feed_stj.py
    ```
5.  **Gere o JSON para o frontend (opcional, se não for usar o servidor Flask para API):**
    ```bash
    python src/app.py --generate-json
    ```
6.  **Para rodar o servidor Flask localmente (API):**
    ```bash
    python src/app.py
    ```
    A API estará disponível em `http://127.0.0.1:5000/api/jurisprudencia`.
7.  **Para visualizar o frontend localmente:**
    *   Abra o arquivo `docs/index.html` diretamente no seu navegador.
    *   Para que o frontend funcione corretamente (buscando o `data/output/jurisprudencia.json`), certifique-se que este arquivo foi gerado (passo 5) ou que o servidor Flask (passo 6) está rodando e o JavaScript está configurado para buscar da API local (requereria alteração no `jsonPath` em `script.js` para desenvolvimento). A forma mais simples para visualização estática é garantir que `data/output/jurisprudencia.json` existe.

## Como Usar a Aplicação (Deployada)

*   **Acesse a URL:** Navegue para a URL do GitHub Pages fornecida na seção "About" ou "Deployments" do seu repositório (e.g., `https://<SEU_USUARIO>.github.io/<NOME_DO_REPOSITORIO>/`).
*   **Visualização:** As teses de jurisprudência serão listadas na página.
*   **Busca:** Utilize o campo de busca para filtrar as teses por palavras-chave. A busca é realizada em títulos, áreas do direito e subáreas.
*   **Gerar Relatório:** Clique no botão "Gerar Relatório" para baixar um arquivo Markdown (`.md`) contendo as teses atualmente visíveis (todas ou filtradas pela busca).

## Fonte dos Dados

*   Feed RSS "Jurisprudência em Teses" do STJ: [https://scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed](https://scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed)
*   Arquivo de fallback (exemplo): `data/input/pesquisa_pronta_stj.xml`

## Ajuda e Documentação Adicional

*   **GitHub Actions:** [Documentação Oficial](https://docs.github.com/en/actions)
*   **GitHub Pages:** [Documentação Oficial](https://docs.github.com/en/pages)
*   **Markdown (Obsidian):** [Guia de Formatação do Obsidian](https://help.obsidian.md/Editing+and+formatting/Basic+formatting+syntax)

## Possíveis Melhorias Futuras

*   Implementar testes automatizados.
*   Adicionar paginação no frontend para lidar com grandes volumes de dados.
*   Interface para gerenciamento de múltiplas fontes de feeds.
*   Opções avançadas de filtragem e ordenação no frontend.
*   Melhorar a extração de tags (e.g., usando NLP básico).
```
