document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('jurisprudencia-container');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const downloadReportButton = document.getElementById('download-report-button');

    let allFetchedData = []; // Para armazenar todos os dados da carga inicial

    // Função de Filtro
    function filterData(data, term) {
        if (!term) {
            return data; // Retorna todos os dados se não houver termo de busca
        }
        const lowerCaseTerm = term.toLowerCase();
        return data.filter(item => {
            return (item.titulo && item.titulo.toLowerCase().includes(lowerCaseTerm)) ||
                   (item.area_direito && item.area_direito.toLowerCase().includes(lowerCaseTerm)) ||
                   (item.sub_area && item.sub_area.toLowerCase().includes(lowerCaseTerm));
        });
    }

    // Função para formatar data (simplificada)
    function formatDateForDisplay(dateString) {
        if (!dateString) return 'Data não disponível';
        try {
            // Tenta formatar a data assumindo que é uma string ISO 8601
            return new Date(dateString).toLocaleDateString('pt-BR', {
                year: 'numeric', month: 'long', day: 'numeric',
                hour: '2-digit', minute: '2-digit', timeZone: 'UTC' // Ajuste o timezone se necessário
            });
        } catch (e) {
            console.warn("Erro ao formatar data para exibição:", dateString, e);
            return dateString; // Usa a string original se a formatação falhar
        }
    }


    async function fetchAndDisplayJurisprudencia(searchTerm = '') {
        // Path adjusted assuming 'docs' is served as root, and 'data/output' is at the same level as 'docs' in the repo,
        // but the artifact uploads 'data/output' to the root of the deployment.
        const jsonPath = 'data/output/jurisprudencia.json';

        try {
            if (allFetchedData.length === 0) { // Busca inicial
                const response = await fetch(jsonPath);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} ao buscar ${jsonPath}`);
                }
                allFetchedData = await response.json();
            }

            const itemsToDisplay = filterData(allFetchedData, searchTerm);
            container.innerHTML = ''; // Limpa conteúdo

            if (itemsToDisplay.length === 0) {
                container.innerHTML = `<p>Nenhuma jurisprudência encontrada ${searchTerm ? 'para o termo "' + searchTerm + '"' : ''}.</p>`;
                return;
            }

            itemsToDisplay.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.classList.add('jurisprudencia-item');

                const title = document.createElement('h2');
                title.textContent = item.titulo || 'Título não disponível';
                itemDiv.appendChild(title);

                const area = document.createElement('p');
                area.innerHTML = `<strong>Área do Direito:</strong> ${item.area_direito || 'Não especificada'}`;
                itemDiv.appendChild(area);

                const subArea = document.createElement('p');
                subArea.innerHTML = `<strong>Subárea:</strong> ${item.sub_area || 'Não especificada'}`;
                itemDiv.appendChild(subArea);

                const dataAtualizacao = document.createElement('p');
                let dataFormatada = formatDateForDisplay(item.data_atualizacao_str || item.data_atualizacao);
                dataAtualizacao.innerHTML = `<strong>Atualizado em:</strong> ${dataFormatada}`;
                itemDiv.appendChild(dataAtualizacao);

                const linksDiv = document.createElement('div');
                linksDiv.classList.add('item-links');

                if (item.link_toc) {
                    const tocLink = document.createElement('a');
                    tocLink.href = item.link_toc;
                    tocLink.textContent = 'Ver Tabela de Conteúdo (TOC)';
                    tocLink.target = '_blank'; // Abrir em nova aba
                    linksDiv.appendChild(tocLink);
                }

                if (item.link_acordaos) {
                    const acordaosLink = document.createElement('a');
                    acordaosLink.href = item.link_acordaos;
                    acordaosLink.textContent = 'Ver Acórdãos';
                    acordaosLink.target = '_blank'; // Abrir em nova aba
                    linksDiv.appendChild(acordaosLink);
                }

                if (linksDiv.hasChildNodes()) {
                    itemDiv.appendChild(linksDiv);
                }

                container.appendChild(itemDiv);
            });

        } catch (error) {
            console.error('Erro ao buscar ou processar jurisprudências:', error);
            container.innerHTML = `<p style="color: red;">Erro ao carregar dados: ${error.message}. Verifique o console para mais detalhes.</p>`;
        }
    }

    // Event Listener para o botão de busca
    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            const searchTerm = searchInput.value.trim();
            fetchAndDisplayJurisprudencia(searchTerm);
        });
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                searchButton.click();
            }
        });
    } else {
        console.warn("Elementos de busca (searchInput ou searchButton) não encontrados.");
    }

    // --- Funcionalidade de Geração e Download de Relatório ---

    function generateMarkdownContent(items, reportTitle) {
        const currentDate = new Date().toISOString().split('T')[0];

        let tags = ["jurisprudencia", "stj"];
        const uniqueAreas = new Set();
        const uniqueSubAreas = new Set();

        items.forEach(item => {
            if (item.area_direito) {
                uniqueAreas.add(item.area_direito.toLowerCase().replace(/\s+/g, '_').replace(/\//g, '_'));
            }
            if (item.sub_area) {
                uniqueSubAreas.add(item.sub_area.toLowerCase().replace(/\s+/g, '_').replace(/\//g, '_'));
            }
        });

        tags = tags.concat(Array.from(uniqueAreas), Array.from(uniqueSubAreas));
        tags = [...new Set(tags)].sort(); // Remove duplicadas e ordena

        const yamlTags = tags.map(tag => `  - "${tag}"`).join('\n');

        const frontmatter = `---
title: "${reportTitle}"
date: "${currentDate}"
tags:
${yamlTags}
---
`;
        let reportBody = `\n# ${reportTitle}\n\n`;
        reportBody += `Relatório gerado em: ${new Date().toLocaleString('pt-BR')}\n\n`;
        reportBody += `Total de teses: ${items.length}\n\n---\n`;

        if (items.length === 0) {
            reportBody += "Nenhuma tese encontrada para os critérios fornecidos.\n";
        } else {
            items.forEach(item => {
                reportBody += `\n## ${item.titulo || 'Título não disponível'}\n\n`;
                reportBody += `- **ID da Pesquisa:** ${item.id_pesquisa || 'N/A'}\n`;
                reportBody += `- **Área do Direito:** ${item.area_direito || 'N/A'}\n`;
                if (item.sub_area) {
                    reportBody += `- **Subárea:** ${item.sub_area}\n`;
                }
                // Usar a string original da data_atualizacao_str para consistência com o gerador Python
                reportBody += `- **Data de Atualização (original):** ${item.data_atualizacao_str || 'N/A'}\n`;

                if (item.link_toc) {
                    reportBody += `- **Link TOC:** [Acessar Tabela de Conteúdo](${item.link_toc})\n`;
                }
                if (item.link_acordaos) {
                    reportBody += `- **Link Acórdãos:** [Ver Acórdãos Relacionados](${item.link_acordaos})\n`;
                }
                reportBody += "\n---\n";
            });
        }
        return frontmatter + "\n" + reportBody;
    }

    function downloadFile(content, fileName, contentType) {
        const blob = new Blob([content], { type: contentType });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
    }

    if (downloadReportButton) {
        downloadReportButton.addEventListener('click', () => {
            const searchTerm = searchInput.value.trim();
            const itemsForReport = filterData(allFetchedData, searchTerm);

            if (itemsForReport.length === 0) {
                alert("Nenhum item para incluir no relatório com os filtros atuais.");
                return;
            }

            const reportTitle = searchTerm
                ? `Relatório de Jurisprudência STJ - Busca: ${searchTerm}`
                : "Relatório Completo de Jurisprudência STJ";

            const markdownContent = generateMarkdownContent(itemsForReport, reportTitle);
            downloadFile(markdownContent, "relatorio_stj.md", "text/markdown;charset=utf-8");
        });
    } else {
        console.warn("Botão de download de relatório (downloadReportButton) não encontrado.");
    }

    fetchAndDisplayJurisprudencia(); // Carga inicial de todos os dados
});
