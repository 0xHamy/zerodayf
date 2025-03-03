 // Initialize dropdowns for selecting AI and Semgrep templates
 $('.ui.dropdown').dropdown();


 // Load templates for dropdowns
 function loadTemplates() {
     $.ajax({
         url: '/analysis/templates-by-type',
         method: 'GET',
         success: function (response) {
             if (response.status === 'success') {
                 const aiDropdown = $('#ai-template-dropdown');
                 const semgrepDropdown = $('#semgrep-template-dropdown');

                 // Clear existing options except the default
                 aiDropdown.find('option:not(:first)').remove();
                 semgrepDropdown.find('option:not(:first)').remove();

                 response.data.forEach(template => {
                     const option = `<option value="${template.name}">${template.name}</option>`;
                     if (template.template_type === 'ai') {
                         aiDropdown.append(option);
                     } else if (template.template_type === 'semgrep') {
                         semgrepDropdown.append(option);
                     }
                 });
             }
         }
     });
 }

 // Update the updateAnalyzeButton function
 function updateAnalyzeButton() {
     const hasCheckedFiles = $('.file-checkbox:checked').length > 0;
     const aiSelected = $('#ai-template-dropdown').dropdown('get value') !== '';
     const semgrepSelected = $('#semgrep-template-dropdown').dropdown('get value') !== '';
     const hasSelectedTemplate = aiSelected || semgrepSelected;
     $('#analyze-selected').prop('disabled', !(hasCheckedFiles && hasSelectedTemplate));
 }

 // Bind dropdown change events
 $('#ai-template-dropdown, #semgrep-template-dropdown').on('change', function () {
     updateAnalyzeButton();
 });

 // Call loadTemplates on initialization
 loadTemplates();


 $(document).ready(function () {
     $('.menu .item').tab();

     function loadMappings() {
         $.ajax({
             url: '/code-map/mappings',
             method: 'GET',
             success: function (response) {
                 if (response.status === 'success') {
                     const tbody = $('#mappings-table-body');
                     tbody.empty();

                     response.data.forEach(mapping => {
                         const status = mapping.scan_status || 'running';
                         tbody.append(`
                         <tr data-id="${mapping.id}">
                             <td><input type="checkbox" class="mapping-checkbox"></td>
                             <td>${mapping.id}</td>
                             <td>${mapping.endpoint}</td>
                             <td>
                                 <button class="ui button view-code-map" 
                                         data-id="${mapping.id}">
                                     View Code Map
                                 </button>
                             </td>
                             <td>
                                 <div class="ui label ${status === 'completed' ? 'green' : 'yellow'}">
                                     ${status}
                                 </div>
                             </td>
                             <td>${new Date(mapping.date).toLocaleString()}</td>
                         </tr>
                     `);
                     });
                 }
             }
         });
     }

     $(document).on('click', '.view-code-map', function () {
         const mappingId = $(this).data('id');

         $.ajax({
             url: `/code-map/mappings/${mappingId}`,
             method: 'GET',
             success: function (response) {
                 if (response.status === 'success') {
                     const data = JSON.parse(response.data.code_file_paths);
                     $('#code-map-modal-title').text(
                         `Code Map for: ${data.endpoint} | ID: ${mappingId}`);

                     const tbody = $('#files-table-body');
                     tbody.empty();

                     // Add template file if exists
                     if (data.template) {
                         tbody.append(buildFileRow('template', data.template));
                     }

                     // Add view function file
                     tbody.append(buildFileRow('view_function', data.view_function));

                     // Add API call files
                     if (Array.isArray(data.api_call)) {
                         data.api_call.forEach(path => {
                             tbody.append(buildFileRow('api_call', path));
                         });
                     }

                     $('#code-map-modal').modal('show');
                 }
             }
         });
     });

     function buildFileRow(fileType, fullPathWithLines) {
         const [filePath, lineStr] = fullPathWithLines.split('#');

         return `
 <tr>
     <td><input type="checkbox" class="file-checkbox"></td>
     <td>${fileType}</td>
     <td>${fullPathWithLines}</td>
     <td>
         <button class="ui button view-code"
                 data-path="${filePath}"
                 data-lines="${lineStr || ''}">
             View Code
         </button>
     </td>
 </tr>
 `;
     }

     // File checkbox handling
     $('#select-all-files').on('change', function () {
         $('.file-checkbox').prop('checked', this.checked);
         updateAnalyzeButton();
     });

     $(document).on('change', '.file-checkbox', function () {
         updateAnalyzeButton();
     });

     $('#select-all').on('change', function () {
         $('.mapping-checkbox').prop('checked', this.checked);
     });

     // Add this to your existing JavaScript
     $('#delete-selected').click(function () {
         const selectedIds = $('.mapping-checkbox:checked').map(function () {
             return $(this).closest('tr').data('id');
         }).get();

         if (selectedIds.length === 0) {
             return;
         }

         if (confirm('Are you sure you want to delete the selected mappings?')) {
             $.ajax({
                 url: '/code-map/mappings',
                 method: 'DELETE',
                 contentType: 'application/json',
                 data: JSON.stringify({
                     mapping_ids: selectedIds
                 }),
                 success: function (response) {
                     if (response.status === 'success') {
                         loadMappings();
                     } else {
                         alert('Failed to delete mappings');
                     }
                 },
                 error: function () {
                     alert('Error occurred while deleting mappings');
                 }
             });
         }
     });


     // Analyze selected files
     $('#analyze-selected').click(function () {
         // Gather selected files
         const selectedFiles = $('.file-checkbox:checked').closest('tr').map(function () {
             const type = $(this).find('td:nth-child(2)').text();
             const fullPathWithLines = $(this).find('td:nth-child(3)').text();
             return {
                 type: type,
                 path: fullPathWithLines // Pass the full path with #start-end
             };
         }).get();

         // Get selected templates
         const aiTemplate = $('#ai-template-dropdown').dropdown('get value');
         const semgrepTemplate = $('#semgrep-template-dropdown').dropdown('get value');
         const scan_name = $('#scan-name').val();

         // Validation
         if (selectedFiles.length === 0) {
             showScanMessage('Please select at least one file', 'negative');
             return;
         }

         if (!aiTemplate && !semgrepTemplate) {
             showScanMessage('Please select at least one template (AI or Semgrep)', 'negative');
             return;
         }

         // Build array of requests based on selected templates
         const requests = [];

         try {
             if (aiTemplate) {
                 requests.push($.ajax({
                     url: '/analysis/perform-analysis/ai',
                     method: 'POST',
                     contentType: 'application/json',
                     data: JSON.stringify({
                         scan_name: scan_name,
                         files: selectedFiles,
                         template: aiTemplate
                     })
                 }));
             }

             if (semgrepTemplate) {
                 requests.push($.ajax({
                     url: '/analysis/perform-analysis/semgrep',
                     method: 'POST',
                     contentType: 'application/json',
                     data: JSON.stringify({
                         scan_name: scan_name,
                         files: selectedFiles,
                         template: semgrepTemplate
                     })
                 }));
             }

             // If we reach here, requests are queued successfully
             let message = 'Starting scans: ';
             if (aiTemplate && semgrepTemplate) {
                 message += 'AI and Semgrep scans initiated';
             } else if (aiTemplate) {
                 message += 'AI scan initiated';
             } else if (semgrepTemplate) {
                 message += 'Semgrep scan initiated';
             }
             showScanMessage(message, 'positive');
         } catch (error) {
             // Immediate failure to start (e.g., JSON.stringify error, invalid URL)
             showScanMessage('Failed to start scans: ' + error.message, 'negative');
             console.error('Scan start error:', error);
             return;
         }

         // Execute all requests concurrently, no messaging on completion
         Promise.all(requests)
             .then(responses => {
                 // Do nothing on success
             })
             .catch(error => {
                 // Log server-side or network errors silently
                 console.error('Scan completion error:', error);
             });
     });


     $(document).on('click', '.view-code', function () {
         const filePath = $(this).data('path');
         const lines = $(this).data('lines');

         $.ajax({
             url: '/utils/file-read',
             method: 'GET',
             data: {
                 path: filePath
             },
             success: function (response) {
                 if (response.content) {
                     let content = response.content;
                     let start = 1,
                         end = Infinity;

                     if (lines) {
                         [start, end] = lines.split('-').map(Number);
                     }

                     const escapedContent = escapeHtml(content);
                     const formattedCode = addLineNumbers(escapedContent, start, end);

                     $('#code-content').html(formattedCode);
                     $('.menu .item[data-tab="code-viewer"]').tab('change tab',
                         'code-viewer');
                 }
             }
         });
     });

     // View code file content
     $(document).on('click', '.view-code', function () {
         const filePath = $(this).data('path');
         const lines = $(this).data('lines');

         $.ajax({
             url: '/utils/file-read',
             method: 'GET',
             data: {
                 path: filePath
             },
             success: function (response) {
                 if (response.content) {
                     let content = response.content;
                     let start = 1,
                         end = Infinity;

                     if (lines) {
                         [start, end] = lines.split('-').map(Number);
                     }

                     const escapedContent = escapeHtml(content);
                     const formattedCode = addLineNumbers(escapedContent, start, end);

                     $('#code-content').html(formattedCode);
                     $('.menu .item[data-tab="code-viewer"]').tab('change tab',
                         'code-viewer');
                 }
             }
         });
     });

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

     function escapeHtml(str) {
         return str
             .replaceAll('&', '&amp;')
             .replaceAll('<', '&lt;')
             .replaceAll('>', '&gt;')
             .replaceAll('"', '&quot;')
             .replaceAll("'", '&#39;');
     }

     /**
      * Displays a temporary message in the modal that hides after 5 seconds.
      * @param {string} message - The message to display.
      * @param {string} [type='positive'] - The type of message ('positive' or 'negative').
      */
     function showScanMessage(message, type = 'positive') {
         const messageContainer = $('#scan-message');
         messageContainer.attr('class', `ui ${type} message`);
         messageContainer.html(message.replace(/\n/g, '<br>'));
         messageContainer.show();
         setTimeout(() => {
             messageContainer.hide();
         }, 5000);
     }
     // Initialize
     loadMappings();
 });