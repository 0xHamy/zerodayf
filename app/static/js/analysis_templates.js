class TemplateManager {
    /**
     * Initializes the TemplateManager.
     */
    constructor() {
        this.templates = [];
        this.initializeUI();
    }

    /**
     * Initializes the user interface components and event listeners.
     */
    async initializeUI() {
        $('.menu .item').tab();
        $('.ui.dropdown').dropdown();
        $('.menu .item[data-tab="preview"]').on('click', this.updateMarkdownPreview.bind(this));

        document.getElementById('addTemplateBtn').addEventListener('click', () =>
            this.openTemplateModal({
                name: '',
                data: '',
                template_type: ''
            }, 'Add Template', false));

        document.getElementById('modalCancelBtn').addEventListener('click', () =>
            $('#templateModal').modal('hide'));

        document.getElementById('modalSaveBtn').addEventListener('click', () =>
            this.saveTemplate());

        // Add these two lines here
        $('#load_ai_template').on('click', () => this.loadDefaultAITemplate());
        $('#load_semgrep_template').on('click', () => this.loadDefaultSemgrepTemplate());

        await this.loadTemplates();
    }

    /**
     * Loads templates from the server and renders them.
     */
    async loadTemplates() {
        try {
            const response = await fetch('/analysis-templates/');
            if (!response.ok) throw new Error(await response.text());

            this.templates = await response.json();
            this.renderTemplates();
        } catch (error) {
            this.showError('Failed to load templates', error);
        }
    }

    /**
     * Renders the templates in the table.
     */
    renderTemplates() {
        const tbody = document.querySelector('#templatesTable tbody');
        tbody.innerHTML = this.templates.length ?
            this.templates.map(template => this.createTemplateRow(template)).join('') :
            '<tr><td colspan="2" class="center aligned">No templates found</td></tr>';
    }

    /**
     * Creates an HTML row for a template.
     * @param {Object} template - The template object.
     * @returns {string} The HTML string for the row.
     */
    createTemplateRow(template) {
        const name = this.escapeHtml(template.name);
        const type = this.escapeHtml(template.template_type || 'N/A');
        const encodedName = encodeURIComponent(template.name);

        return `
            <tr>
                <td>${name}</td>
                <td>${type}</td>
                <td>
                    <button class="ui button tiny" onclick="templateManager.viewTemplate('${encodedName}')">
                        View
                    </button>
                    <button class="ui blue button tiny" onclick="templateManager.editTemplate('${encodedName}')" style="margin-left: 0.5em">
                        Edit
                    </button>
                    <button class="ui red button tiny" onclick="templateManager.deleteTemplate('${encodedName}')" style="margin-left: 0.5em">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * Views a template by loading it from the server and opening the modal in read-only mode.
     * @param {string} encodedName - The encoded name of the template.
     */
    async viewTemplate(encodedName) {
        try {
            const response = await fetch(`/analysis-templates/${encodedName}`);
            if (!response.ok) throw new Error(await response.text());

            const template = await response.json();
            this.openTemplateModal(template, 'View Template', true);
        } catch (error) {
            this.showError('Failed to load template', error);
        }
    }

    /**
     * Edits a template by loading it from the server and opening the modal in edit mode.
     * @param {string} encodedName - The encoded name of the template.
     */
    async editTemplate(encodedName) {
        try {
            const response = await fetch(`/analysis-templates/${encodedName}`);
            if (!response.ok) throw new Error(await response.text());

            const template = await response.json();
            this.openTemplateModal(template, 'Edit Template', false);
        } catch (error) {
            this.showError('Failed to load template', error);
        }
    }

    /**
     * Opens the template modal with the given template data.
     * @param {Object} template - The template object.
     * @param {string} header - The header text for the modal.
     * @param {boolean} readOnly - Whether the modal should be in read-only mode.
     */
    openTemplateModal(template, header, readOnly) {
        const modal = document.querySelector('#templateModal');

        modal.querySelector('#modalHeader').textContent = header;
        modal.querySelector('#templateName').value = template.name;
        modal.querySelector('#templateData').value = template.data;

        if (template.template_type) {
            $('#templateType').dropdown('set selected', template.template_type);
        } else {
            $('#templateType').dropdown('set selected', '');
        }

        const form = modal.querySelector('#templateForm');
        form.dataset.templateName = template.name;

        const inputs = modal.querySelectorAll('input, textarea');
        inputs.forEach(input => input.disabled = readOnly);
        modal.querySelector('#templateType').disabled = readOnly;

        modal.querySelector('#modalSaveBtn').style.display = readOnly ? 'none' : 'block';

        $('.menu .item').tab('change tab', 'edit');
        $(modal).modal({
            observeChanges: true,
            autofocus: false,
            closable: false
        }).modal('show');
    }

    /**
     * Saves the template to the server.
     */
    async saveTemplate() {
        const form = document.getElementById('templateForm');
        const originalName = form.dataset.templateName;
        const name = document.getElementById('templateName').value.trim();
        const data = document.getElementById('templateData').value.trim();
        const template_type = document.getElementById('templateType').value;

        console.log('Debugging saveTemplate:');
        console.log('name:', name);
        console.log('data:', data);
        console.log('template_type:', template_type);

        if (!name) {
            this.showError('Validation Error', new Error('Template name is required'));
            return;
        }
        if (!template_type) {
            this.showError('Validation Error', new Error('Please select a template type'));
            return;
        }

        const templateData = {
            name,
            data,
            template_type
        };
        console.log('Sending payload:', templateData);

        let url = '/analysis-templates/';
        let method = 'POST';

        if (originalName) {
            url += encodeURIComponent(originalName);
            method = 'PUT';
        }

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(templateData)
            });

            if (!response.ok) throw new Error(await response.text());

            $('#templateModal').modal('hide');
            await this.loadTemplates();
            this.showSuccess(`Template ${originalName ? 'updated' : 'created'} successfully`);
        } catch (error) {
            this.showError(`Failed to ${originalName ? 'update' : 'create'} template`, error);
        }
    }

    /**
     * Deletes a template after confirmation.
     * @param {string} encodedName - The encoded name of the template.
     */
    async deleteTemplate(encodedName) {
        const name = decodeURIComponent(encodedName);

        try {
            const confirmed = await this.showConfirmation(
                `Are you sure you want to delete the template "${name}"?`
            );

            if (!confirmed) return;

            const response = await fetch(`/analysis-templates/${encodedName}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error(await response.text());

            await this.loadTemplates();
            this.showSuccess('Template deleted successfully');
        } catch (error) {
            this.showError('Failed to delete template', error);
        }
    }

    /**
     * Updates the markdown preview based on the template data.
     */
    updateMarkdownPreview() {
        const text = document.getElementById('templateData').value || '';
        const converter = new showdown.Converter();
        const html = converter.makeHtml(text);
        document.getElementById('markdownPreview').innerHTML = html;
    }

    /**
     * Shows a confirmation modal with the given message.
     * @param {string} message - The message to display in the confirmation modal.
     * @returns {Promise<boolean>} A promise that resolves to true if confirmed, false otherwise.
     */
    showConfirmation(message) {
        return new Promise((resolve) => {
            $('#confirmationModal')
                .modal({
                    closable: false,
                    onApprove: () => resolve(true),
                    onDeny: () => resolve(false)
                })
                .modal('show');

            document.getElementById('confirmationMessage').textContent = message;
        });
    }

    /**
     * Shows an error notification.
     * @param {string} message - The error message.
     * @param {Error} error - The error object.
     */
    showError(message, error) {
        console.error(error);
        const errorMessage = error.message || String(error);
        this.showNotification(message + ': ' + errorMessage, 'error');
    }

    /**
     * Shows a success notification.
     * @param {string} message - The success message.
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Shows a notification with the given message and type.
     * @param {string} message - The notification message.
     * @param {string} [type='success'] - The type of notification ('success' or 'error').
     */
    showNotification(message, type = 'success') {
        const notification = $('#notification');
        notification
            .find('.message')
            .removeClass('positive negative')
            .addClass(type === 'success' ? 'positive' : 'negative')
            .find('.notification-text')
            .text(message);

        notification
            .show()
            .delay(5000)
            .fadeOut();

        notification.find('.close').off('click').click(() => notification.hide());
    }

    /**
     * Escapes HTML special characters in the given text.
     * @param {string} text - The text to escape.
     * @returns {string} The escaped text.
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    /**
     * Sends a request to load default AI template data into the database
     */
    async loadDefaultAITemplate() {
        $.ajax({
            url: '/analysis-templates/load-defaults/ai',
            method: 'POST',
            contentType: 'application/json',
            success: (response) => {
                if (response.status === 'success') {
                    this.showScanMessage(response.message, 'positive');
                    this.loadTemplates();
                } else {
                    this.showScanMessage(response.message, 'negative');
                }
            }
        });
    }

    /**
     * Sends a request to load default Semgrep template data into the database
     */
    async loadDefaultSemgrepTemplate() {
        $.ajax({
            url: '/analysis-templates/load-defaults/semgrep',
            method: 'POST',
            contentType: 'application/json',
            success: (response) => {
                if (response.status === 'success') {
                    this.showScanMessage(response.message, 'positive');
                    this.loadTemplates();
                } else {
                    this.showScanMessage(response.message, 'negative');
                }
            }
        });
    }

    /**
     * Displays a temporary message in the modal that hides after 5 seconds.
     * @param {string} message - The message to display.
     * @param {string} [type='positive'] - The type of message ('positive' or 'negative').
     */
    showScanMessage(message, type = 'positive') {
        const messageContainer = $('#scan-message');
        messageContainer.attr('class', `ui ${type} message`);
        messageContainer.html(message.replace(/\n/g, '<br>'));
        messageContainer.show();
        setTimeout(() => {
            messageContainer.hide();
        }, 5000);
    }

}

/**
 * Initializes the TemplateManager instance on page load.
 */
const templateManager = new TemplateManager();