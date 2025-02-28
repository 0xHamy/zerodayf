class TemplateManager {
    constructor() {
        this.templates = [];
        this.initializeUI();
    }

    async initializeUI() {
        // Initialize Semantic UI components
        $('.menu .item').tab();
        $('.ui.dropdown').dropdown(); // Ensure dropdown is initialized
        $('.menu .item[data-tab="preview"]').on('click', this.updateMarkdownPreview.bind(this));
        
        // Event listeners
        document.getElementById('addTemplateBtn').addEventListener('click', () => 
            this.openTemplateModal({ name: '', data: '', template_type: '' }, 'Add Template', false));
        
        document.getElementById('modalCancelBtn').addEventListener('click', () => 
            $('#templateModal').modal('hide'));
        
        document.getElementById('modalSaveBtn').addEventListener('click', () => 
            this.saveTemplate());
    
        // Load initial data
        await this.loadTemplates();
    }

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

    renderTemplates() {
        const tbody = document.querySelector('#templatesTable tbody');
        tbody.innerHTML = this.templates.length ?
            this.templates.map(template => this.createTemplateRow(template)).join('') :
            '<tr><td colspan="2" class="center aligned">No templates found</td></tr>';
    }


    createTemplateRow(template) {
        const name = this.escapeHtml(template.name);
        const type = this.escapeHtml(template.template_type || 'N/A'); // Handle missing type
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

    openTemplateModal(template, header, readOnly) {
        const modal = document.querySelector('#templateModal');
        
        modal.querySelector('#modalHeader').textContent = header;
        modal.querySelector('#templateName').value = template.name;
        modal.querySelector('#templateData').value = template.data;
        
        // Set dropdown value
        if (template.template_type) {
            $('#templateType').dropdown('set selected', template.template_type);
        } else {
            $('#templateType').dropdown('set selected', '');
        }
    
        const form = modal.querySelector('#templateForm');
        form.dataset.templateName = template.name;
    
        // Set read-only state
        const inputs = modal.querySelectorAll('input, textarea');
        inputs.forEach(input => input.disabled = readOnly);
        modal.querySelector('#templateType').disabled = readOnly;
        
        modal.querySelector('#modalSaveBtn').style.display = readOnly ? 'none' : 'block';
    
        // Show modal and reset to edit tab
        $('.menu .item').tab('change tab', 'edit');
        $(modal).modal({
            observeChanges: true,
            autofocus: false,
            closable: false
        }).modal('show');
    }

    async saveTemplate() {
        const form = document.getElementById('templateForm');
        const originalName = form.dataset.templateName;
        const name = document.getElementById('templateName').value.trim();
        const data = document.getElementById('templateData').value.trim();
        const template_type = document.getElementById('templateType').value; // Directly from <select>
    
        // Log values for debugging
        console.log('Debugging saveTemplate:');
        console.log('name:', name);
        console.log('data:', data);
        console.log('template_type:', template_type);
    
        // Validation
        if (!name) {
            this.showError('Validation Error', new Error('Template name is required'));
            return;
        }
        if (!template_type) {
            this.showError('Validation Error', new Error('Please select a template type'));
            return;
        }
    
        const templateData = { name, data, template_type };
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
                headers: { 'Content-Type': 'application/json' },
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

    updateMarkdownPreview() {
        const text = document.getElementById('templateData').value || '';
        const converter = new showdown.Converter();
        const html = converter.makeHtml(text);
        document.getElementById('markdownPreview').innerHTML = html;
    }

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

    showError(message, error) {
        console.error(error);
        const errorMessage = error.message || String(error);
        this.showNotification(message + ': ' + errorMessage, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
const templateManager = new TemplateManager();