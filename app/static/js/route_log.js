// Global object to store route data from log entries
const routeData = {};


/**
 * Renders the route table with filtered data based on a search term.
 * @param {string} [searchTerm=''] - Optional term to filter routes.
 */
function renderTable(searchTerm = '') {
    const tbody = document.querySelector('#route-table tbody');
    tbody.innerHTML = '';

    Object.values(routeData)
        .filter(entry => entry.route.toLowerCase().includes(searchTerm.toLowerCase()))
        .forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="collapsing">
                    <div class="ui checkbox">
                        <input type="checkbox" class="route-checkbox">
                        <label></label>
                    </div>
                </td>
                <td>${entry.route}</td>
                <td>${entry.endpoint}</td>
            `;
            tbody.appendChild(row);
        });

    $('.ui.checkbox').checkbox();
    updateMapButton();
}

/**
 * Updates the enabled state of the "Begin Mapping" button based on form inputs.
 * Requires a framework, app path, and at least one selected endpoint.
 */
function updateBeginMappingButton() {
    const framework = $('#framework-dropdown').dropdown('get value');
    const appPath = $('#app-path').val().trim();
    const hasEndpoints = $('#selected-endpoints-list .item').length > 0;

    $('#begin-mapping').prop('disabled', !(framework && appPath && hasEndpoints));
}

/**
 * Updates the list of selected endpoints in the mapping modal.
 * Populates the list with endpoints from checked rows in the route table.
 */
function updateSelectedEndpointsList() {
    const list = $('#selected-endpoints-list');
    list.empty();

    $('.route-checkbox:checked').each(function() {
        const endpoint = $(this).closest('tr').find('td:eq(2)').text();
        list.append(`<div class="item">${endpoint}</div>`);
    });
}

/**
 * Updates the enabled state of the "Map" button based on checkbox selections.
 */
function updateMapButton() {
    const hasSelected = $('.route-checkbox:checked').length > 0;
    $('#map-button').prop('disabled', !hasSelected);
}

// Initialize event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Semantic UI dropdowns
    $('.ui.dropdown').dropdown();

    // Handle search input to filter the route table
    $('#endpoint-search').on('input', function(e) {
        renderTable(e.target.value);
    });

    // Toggle all route checkboxes with the "Select All" checkbox
    $('#select-all').on('change', function() {
        const isChecked = this.checked;
        $('.route-checkbox').each(function() {
            $(this).prop('checked', isChecked);
        });
        updateMapButton();
    });

    // Show the mapping modal when the "Map" button is clicked
    $('#map-button').on('click', function() {
        updateSelectedEndpointsList();
        $('#mapping-modal').modal('show');
    });

    // Update "Begin Mapping" button state on framework and app path changes
    $('#framework-dropdown').dropdown({
        onChange: updateBeginMappingButton
    });

    $('#app-path').on('input', updateBeginMappingButton);

    // Handle "Begin Mapping" button click to start the mapping process
    $('#begin-mapping').on('click', async function() {
        const selectedEndpoints = [];

        // Collect selected endpoints from the modal list
        $('#selected-endpoints-list .item').each(function() {
            selectedEndpoints.push($(this).text());
        });

        const mappingData = {
            framework: $('#framework-dropdown').dropdown('get value'),
            app_path: $('#app-path').val().trim(),
            endpoints: selectedEndpoints
        };

        console.log('Mapping Data:', mappingData);

        try {
            const response = await fetch('/base-code-mapper/start-mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(mappingData)
            });

            const result = await response.json();
            console.log('Response:', result);
            if (result.status === 'success') {
                $('#mapping-modal').modal('hide');
                alert('Mapping process started successfully!');
            } else {
                alert('Error starting mapping process: ' + result.message);
            }
        } catch (error) {
            console.error('Error starting mapping:', error);
            alert('Error starting mapping process');
        }
    });

    // Update map button state when route checkboxes change
    $('#route-table').on('change', '.route-checkbox', function() {
        updateMapButton();
        updateBeginMappingButton();
    });

    // Start polling logs on page load
    pollLogs();
});
