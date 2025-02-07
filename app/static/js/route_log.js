    /**
     * addLineNumbers: Returns HTML with line numbers and highlights the given range.
     */
    function addLineNumbers(fullCode, start = 1, end = Infinity) {
        const lines = fullCode.split('\n');
        const total = lines.length;
        const s = Math.max(1, Math.min(start, total));
        const e = Math.min(end, total);
        return lines.map((text, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = lineNum >= s && lineNum <= e;
            let lineHtml = `<span class="line-num">${lineNum}</span> `;
            lineHtml += isHighlighted ? `<span class="highlighted-line">${text}</span>` :
            `<span>${text}</span>`;
            return `<div class="code-line">${lineHtml}</div>`;
        }).join('');
    }

    /**
     * escapeHtml: Replaces HTML special characters with entities.
     */
    function escapeHtml(str) {
        return str
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    /**
     * generateRandomName: Returns a random string of the given length.
     * Default length is 10.
     * The string contains only alphabets.
    */
    function generateRandomName(length = 10) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
        let name = '';
        for (let i = 0; i < length; i++) {
            name += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return name;
    }

    /**
     * buildSingleFileSnippet: Returns a string with the file path and code snippet.
     * The code snippet is highlighted with line numbers.
     */ 
    function buildMultiFileSnippet(filePaths, codeSnippets) {
        let combined = "";
        for (let i = 0; i < filePaths.length; i++) {
            const filePath = filePaths[i];
            const snippet = codeSnippets[i];
            combined += `${filePath}\n\`\`\`\n${snippet}\n\`\`\`\n\n`;
        }
        return combined;
    }

    /**
     * buildSingleFileSnippet: Returns a string with the file path and code snippet.
     * The code snippet is highlighted with line numbers.
     */
    async function fetchFileContent(path) {
        const response = await fetch(`/proxy/get-file?path=${encodeURIComponent(path)}`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to fetch file "${path}": ${errorText}`);
        }
        const data = await response.json();
        return data.content || '';
    }

    /**
     * fetchTemplateData: Fetches the template data from the server.
     * The template data is used to render the template.
     */
    async function fetchTemplateData(templateName) {
        const response = await fetch(`/scan/get-template/${encodeURIComponent(templateName)}`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to fetch template "${templateName}": ${errorText}`);
        }
        const data = await response.json();
        return data.data || '';
    }
