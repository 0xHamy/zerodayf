window.deleteAPI = (apiId) => {
    /** Opens the delete confirmation modal for the specified API ID. */
    $('#delete-confirm-modal')
        .data('apiId', apiId)
        .modal('show');
};

/** Handles the delete confirmation approval action. */
$('#delete-confirm-modal .approve.button').on('click', async function() {
    const apiId = $('#delete-confirm-modal').data('apiId');

    try {
        const response = await fetch(`/api/delete-api/${apiId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadAPIs();
            showMessage('API deleted successfully', 'positive');
        } else {
            const error = await response.json();
            showMessage(error.message, 'negative');
        }
    } catch (error) {
        showMessage('Error deleting API', 'negative');
    } finally {
        $('#delete-confirm-modal').modal('hide');
    }
});

/** Initializes page elements and event listeners on DOM ready. */
$(document).ready(function() {
    $('#provider-dropdown').dropdown();
    loadAPIs();

    $('#check-btn').click(async function() {
        const { name, provider, token, dataModel, max_tokens } = getFormData();
        if (!validateForm()) return;
        try {
            const response = await fetch('/api/check-api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    provider,
                    token,
                    model: dataModel,
                    max_tokens
                })
            });
            const result = await response.json();
            showMessage(result.message, result.valid ? 'positive' : 'negative');
            if (result.valid) {
                $('#check-btn').hide();
                $('#save-btn').show();
            }
        } catch (error) {
            showMessage('Validation service error', 'negative');
        }
    });

    $('#save-btn').click(async () => {
        const { name, provider, token, dataModel, max_tokens } = getFormData();
        try {
            const response = await fetch('/api/save-api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    provider,
                    token,
                    model: dataModel,
                    max_tokens
                })
            });
            if (response.ok) {
                resetForm();
                await loadAPIs();
                showMessage('API saved successfully', 'positive');
                $('#save-btn').hide();
                $('#check-btn').show();
            } else {
                const error = await response.json();
                showMessage(error.message, 'negative');
            }
        } catch (error) {
            showMessage('Error saving API', 'negative');
        }
    });

    $('#activate-btn').click(handleActivation);
});

async function handleActivation() {
    /** Toggles the activation state of an API by name. */
    const apiName = $('#activate-api-name').val().trim();
    if (!apiName) {
        showMessage('Please enter an API name', 'negative');
        return;
    }

    try {
        const response = await fetch(`/api/toggle-api/${encodeURIComponent(apiName)}`, {
            method: 'POST'
        });
        const result = await response.json();
        if (response.ok) {
            await loadAPIs();
            showMessage(result.message, 'positive');
            $('#activate-api-name').val('');
        } else {
            showMessage(result.detail || 'Activation failed', 'negative');
        }
    } catch (error) {
        showMessage('Error activating API', 'negative');
    }
}

async function loadAPIs() {
    /** Fetches and renders the list of APIs into the table. */
    try {
        const response = await fetch('/api/get-apis');
        const apis = await response.json();

        const rows = apis.map(api => {
            const masked = '*'.repeat(api.token.length);
            return `
                <tr>
                    <td>${api.name}</td>
                    <td>
                        <span 
                            id="token-span-${api.id}"
                            data-is-masked="true"
                        >
                            ${masked}
                        </span>
                        <i 
                            class="eye icon"
                            style="cursor: pointer; margin-left:5px;"
                            onclick="toggleToken(${api.id}, '${api.token}')"
                        ></i>
                    </td>
                    <td>${api.model || ''}</td>
                    <td>${api.provider}</td>
                    <td>${api.max_tokens}</td>
                    <td>
                        ${api.is_active
                            ? '<i class="green check circle icon"></i> Active'
                            : '<i class="grey times circle icon"></i> Inactive'
                        }
                    </td>
                    <td>
                        <button class="ui small red button" onclick="deleteAPI(${api.id})">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');

        $('#api-table').html(
            rows.length ?
            rows :
            '<tr><td colspan="6" class="center aligned">No APIs found</td></tr>'
        );
    } catch (error) {
        showMessage('Error loading APIs', 'negative');
    }
}

function toggleToken(apiId, realToken) {
    /** Toggles between showing the masked or real token value. */
    const span = document.getElementById(`token-span-${apiId}`);
    const isMasked = (span.dataset.isMasked === 'true');

    if (isMasked) {
        span.textContent = realToken;
        span.dataset.isMasked = 'false';
    } else {
        span.textContent = '*'.repeat(realToken.length);
        span.dataset.isMasked = 'true';
    }
}

function getFormData() {
    /** Retrieves form input values as an object. */
    return {
        name: $('input[name="name"]').val(),
        provider: $('input[name="provider"]').val(),
        token: $('input[name="token"]').val(),
        dataModel: $('input[name="dataModel"]').val(),
        max_tokens: $('input[name="max_tokens"]').val()
    };
}

function validateForm() {
    /** Validates that required form fields are filled. */
    const { name, provider, token } = getFormData();
    if (!name || !provider || !token) {
        showMessage('All fields are required', 'negative');
        return false;
    }
    return true;
}

function resetForm() {
    /** Clears all form fields and resets the provider dropdown. */
    $('input[name="name"]').val('');
    $('input[name="token"]').val('');
    $('input[name="dataModel"]').val('');
    $('input[name="max_tokens"]').val('');
    $('#provider-dropdown').dropdown('clear');
}

function showMessage(message, type) {
    /** Displays a temporary message with the specified type (positive/negative). */
    const container = $('#message-container');
    container.removeClass('positive negative hidden')
        .addClass(`${type} visible`)
        .html(message);
    setTimeout(() => {
        container.addClass('hidden').removeClass('visible positive negative');
    }, 5000);
}
