$(document).ready(function () {
    // Initialize Semantic UI components
    $('#endpoint-dropdown').dropdown();
    $('#framework-dropdown').dropdown();
    $('#ai-template-dropdown').dropdown({
        onChange: updatePerformAnalysisButton
    });
    $('#semgrep-template-dropdown').dropdown({
        onChange: updatePerformAnalysisButton
    });

    $('.tabular.menu .item').tab();

    // Fetch mappings and populate dropdown on page load
    fetch('/endpoint-map/select-mapping')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const dropdown = $('#endpoint-dropdown');
                dropdown.find('.menu').empty();
                data.data.forEach(mapping => {
                    dropdown.find('.menu').append(
                        `<div class="item" data-value="${mapping.id}">${mapping.name}</div>`);
                });
                dropdown.dropdown('refresh');
            } else {
                showMessage('error', 'Failed to load mappings');
            }
        })
        .catch(error => showMessage('error', 'Error fetching mappings: ' + error));

    // Load endpoints button click handler
    $('#load-endpoints').on('click', function () {
        const selectedId = $('#endpoint-dropdown').dropdown('get value');
        if (!selectedId) {
            showMessage('error', 'Please select a mapping first');
            return;
        }
        fetch(`/endpoint-map/mappings/${selectedId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    populateEndpointsTable(JSON.parse(data.data.data));
                    showMessage('success', 'Endpoints loaded successfully');
                } else {
                    showMessage('error', 'Failed to load mapping data');
                }
            })
            .catch(error => showMessage('error', 'Error fetching mapping data: ' + error));
    });

    // Populate endpoints table
    function populateEndpointsTable(endpointsData) {
        const tableBody = $('#route-table tbody');
        tableBody.empty();
        Object.keys(endpointsData).forEach(endpoint => {
            const row = `
                <tr>
                    <td>
                        <div class="ui checkbox">
                            <input type="checkbox" class="endpoint-checkbox">
                            <label></label>
                        </div>
                    </td>
                    <td>${endpoint}</td>
                    <td>
                        <button class="ui button view-button" data-endpoint="${endpoint}">View</button>
                    </td>
                </tr>
            `;
            tableBody.append(row);
        });
        $('.view-button').on('click', function () {
            const endpoint = $(this).data('endpoint');
            openViewModal(endpoint, endpointsData[endpoint]);
        });
        $('#select-all').on('change', function () {
            const checked = $(this).prop('checked');
            $('.endpoint-checkbox').prop('checked', checked);
        });
    }

    // Open view modal
    function openViewModal(endpoint, endpointData) {
        $('#endpoint-title').text(endpoint);
        populateFilesTable(endpointData);
        fetchAnalysisTemplates();
        $('#view-endpoint-modal').modal('show');
    }

    // Populate files table in modal
    function populateFilesTable(endpointData) {
        const tableBody = $('#files-table tbody');
        tableBody.empty();
        if (endpointData.view_func) {
            tableBody.append(createFileRow('view_func', endpointData.view_func));
        }
        if (endpointData.template && endpointData.template !== 'none') {
            tableBody.append(createFileRow('template', endpointData.template));
        }
        if (endpointData.api_functions) {
            Object.entries(endpointData.api_functions).forEach(([api, file]) => {
                tableBody.append(createFileRow(`api_function: ${api}`, file));
            });
        }
        $('#select-all-files').on('change', function () {
            const checked = $(this).prop('checked');
            $('#files-table .file-checkbox').prop('checked', checked);
            updatePerformAnalysisButton();
        });
        $('#files-table .file-checkbox').on('change', updatePerformAnalysisButton);
    }

    // Create a file row for the files table
    function createFileRow(fileType, filePath) {
        const [path, lineRange] = filePath.split('#');
        const displayPath = lineRange ? `${path} #${lineRange}` : path;
        const [start, end] = lineRange ? lineRange.split('-').map(Number) : [null, null];
        return `
            <tr>
                <td>
                    <div class="ui checkbox">
                        <input type="checkbox" class="file-checkbox" data-file="${filePath}">
                        <label></label>
                    </div>
                </td>
                <td>${fileType}: ${displayPath}</td>
                <td>
                    <button class="ui button view-file-button" data-file="${path}" data-start="${start}" data-end="${end}">View</button>
                </td>
            </tr>
        `;
    }

    // Fetch and populate analysis templates
    function fetchAnalysisTemplates() {
        fetch('/endpoint-map/analysis-templates')
            .then(response => response.json())
            .then(data => {
                console.log('Templates data:', data);
                if (data.status === 'success') {
                    const aiDropdown = $('#ai-template-dropdown');
                    const semgrepDropdown = $('#semgrep-template-dropdown');
                    aiDropdown.find('.menu').empty();
                    semgrepDropdown.find('.menu').empty();
                    data.data.forEach(template => {
                        const item = `<div class="item" data-value="${template.id}">${template.name}</div>`;
                        if (template.type === 'ai') {
                            aiDropdown.find('.menu').append(item);
                        } else if (template.type === 'semgrep') {
                            semgrepDropdown.find('.menu').append(item);
                        }
                    });
                    aiDropdown.dropdown('refresh');
                    semgrepDropdown.dropdown('refresh');
                } else {
                    showMessage('error', 'Failed to load analysis templates');
                }
            })
            .catch(error => showMessage('error', 'Error fetching analysis templates: ' + error));
    }

    // View file contents with line numbers and highlighting
    $(document).on('click', '.view-file-button', function () {
        const filePath = $(this).data('file');
        const startLine = parseInt($(this).data('start')) || 1;
        const endLine = parseInt($(this).data('end')) || Infinity;
        console.log('Viewing file:', filePath, 'from line', startLine, 'to', endLine);

        const url =
            `/endpoint-map/file-contents?file_path=${encodeURIComponent(filePath)}&start_line=${startLine}&end_line=${endLine}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('File content response:', data);
                if (data.status === 'success') {
                    const content = data.data.content;
                    const formattedCode = addLineNumbers(content, startLine, endLine);
                    $('#code-content').html(formattedCode);
                    $('.tabular.menu .item').tab('change tab', 'code');
                } else {
                    showMessage('error', 'Failed to load file contents');
                }
            })
            .catch(error => showMessage('error', 'Error fetching file contents: ' + error));
    });

    // Function to add line numbers and highlighting
    function addLineNumbers(fullCode, start = 1, end = Infinity) {
        const lines = fullCode.split('\n');
        return lines.map((text, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = lineNum >= start && lineNum <= end;
            let lineHtml = `<span class="line-num">${lineNum}</span> `;
            lineHtml += isHighlighted ? `<span class="highlighted-line">${escapeHtml(text)}</span>` :
                `<span>${escapeHtml(text)}</span>`;
            return `<div class="code-line">${lineHtml}</div>`;
        }).join('');
    }

    // Function to escape HTML characters safely
    function escapeHtml(str) {
        return str
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    // Update Perform Analysis button state
    function updatePerformAnalysisButton() {
        const filesSelected = $('#files-table .file-checkbox:checked').length > 0;
        const aiSelected = $('#ai-template-dropdown').dropdown('get value') !== '';
        const semgrepSelected = $('#semgrep-template-dropdown').dropdown('get value') !== '';
        const hasSelectedTemplate = aiSelected || semgrepSelected;
        $('#perform-analysis').prop('disabled', !(filesSelected && hasSelectedTemplate));
    }

    // Perform Analysis button handler
    $('#perform-analysis').on('click', function () {
        const selectedFiles = $('#files-table .file-checkbox:checked').map(function () {
            return { path: $(this).data('file') };
        }).get();

        const aiTemplateId = $('#ai-template-dropdown').dropdown('get value');
        const semgrepTemplateId = $('#semgrep-template-dropdown').dropdown('get value');

        if (selectedFiles.length === 0) {
            showMessage('error', 'Please select at least one file');
            return;
        }

        if (!aiTemplateId && !semgrepTemplateId) {
            showMessage('error', 'Please select at least one template (AI or Semgrep)');
            return;
        }

        const scanData = {
            scan_name: `Analysis for endpoint ${$('#endpoint-title').text()}`,
            files: selectedFiles
        };

        if (aiTemplateId) {
            initiateScan('ai', aiTemplateId, scanData);
        }
        if (semgrepTemplateId) {
            initiateScan('semgrep', semgrepTemplateId, scanData);
        }

        $('#view-endpoint-modal').modal('hide');
    });

    // Function to initiate a scan
    function initiateScan(type, templateId, scanData) {
        const endpoint = `/endpoint-map/perform-analysis/${type}`;
        const data = { ...scanData, template: templateId };
        showMessage('success', `${type === 'ai' ? 'AI' : 'Semgrep'} scan initiated`);
        $.ajax({
            url: endpoint,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function (response) {
                console.log(`${type} scan request success:`, response);
            },
            error: function (xhr, status, error) {
                console.error(`${type} scan request error:`, error);
                showMessage('error', `Error initiating ${type} scan: ${error}`);
            }
        });
    }

    // Show message in message container
    function showMessage(type, message) {
        const container = $('#message-container');
        container.removeClass('hidden positive negative');
        container.addClass(type === 'success' ? 'positive' : 'negative');
        container.text(message);
        setTimeout(() => {
            container.addClass('hidden');
        }, 5000);
    }
});