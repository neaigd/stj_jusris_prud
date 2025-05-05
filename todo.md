# TODO - Configuração do Projeto STJ Pesquisa Pronta

prompt: https://aistudio.google.com/app/prompts/12qguQ0Dw0OlIiXVfzMJbW_WjRpzSJjCb

Este arquivo guia a configuração inicial do ambiente de desenvolvimento.

1.  **Criar Diretório do Projeto:**
    ```bash
    mkdir -p /media/peixoto/stuff/stj_juris_prud
    cd /media/peixoto/stuff/stj_juris_prud
    ```

2.  **Criar e Ativar Ambiente Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # Para desativar depois: deactivate
    ```

3.  **Instalar Bibliotecas Iniciais:**
    *   `pandas`: Para manipulação de DataFrames.
    *   `lxml` ou `xml.etree.ElementTree`: Para parsing de XML (lxml é geralmente mais robusto).
    *   `requests`: (Opcional, se for buscar o feed diretamente da URL no futuro).
    *   `beautifulsoup4`: (Potencialmente útil para limpar o HTML dentro da tag `<summary>`).
    ```bash
    pip install pandas lxml beautifulsoup4 requests
    ```

4.  **Criar `requirements.txt`:**
    ```bash
    pip freeze > requirements.txt
    ```

5.  **Inicializar Git:**
    ```bash
    git init
    ```

6.  **Criar `.gitignore`:**
    Crie um arquivo chamado `.gitignore` e adicione conteúdo padrão para Python, como:
    ```
    # Virtual environment
    venv/
    */venv/
    .venv/
    */.venv/

    # Byte-compiled / optimized / DLL files
    __pycache__/
    *.py[cod]
    *$py.class

    # Distribution / packaging
    .Python
    build/
    develop-eggs/
    dist/
    downloads/
    eggs/
    .eggs/
    lib/
    lib64/
    parts/
    sdist/
    var/
    wheels/
    pip-wheel-metadata/
    share/python-wheels/
    *.egg-info/
    .installed.cfg
    *.egg
    MANIFEST

    # Jupyter Notebook checkpoints
    .ipynb_checkpoints

    # Environments
    .env
    .env.*

    # IDE files
    .idea/
    .vscode/
    *.suo
    *.ntvs*
    *.njsproj
    *.sln
    *.sw?

    # Secrets (add specific files if needed)
    # secrets.yaml
    # config.ini
    ```

7.  **Adicionar Arquivos ao Git:**
    ```bash
    git add .
    ```

8.  **Primeiro Commit:**
    ```bash
    git commit -m "Initial project setup with venv, git, requirements and gitignore"
    ```

9.  **Criar Repositório no GitHub e Enviar:**
    *   Certifique-se que o `gh` CLI está instalado e autenticado (`gh auth login`).
    *   Execute o comando (estando no diretório do projeto):
    ```bash
    gh repo create neaigd/stj_jusris_prud --public --source=. --remote=origin --push
    ```
    *Observação: Confirme se o nome do repositório `stj_jusris_prud` está correto conforme sua intenção.*
