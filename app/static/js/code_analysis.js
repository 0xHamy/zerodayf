// Show all scans
$(document).ready(function () {
    let allScans = [];

    // Initialize dropdown
    $('#typeFilter').dropdown();

    // Load initial data
    fetchScans();

    function fetchScans() {
        $.get('/analysis/code-scans')
            .done(function (response) {
                if (response.status === 'success') {
                    allScans = response.data;
                    renderTable(allScans);
                }
            })
            .fail(function (xhr) {
                console.error('Failed to fetch scans:', xhr);
            });
    }

    // Used to render the table with the provided scans
    function renderTable(scans) {
        const tbody = $('#scansTableBody');
        tbody.empty();

        scans.forEach(scan => {
            const row = `
                <tr data-id="${scan.id}">
                    <td><input type="checkbox" class="row-select"></td>
                    <td>${scan.id}</td>
                    <td>${scan.scan_name}</td>
                    <td>${scan.uid}</td>
                    <td>${scan.scan_type}</td>
                    <td>${new Date(scan.date).toLocaleString()}</td>
                    <td><a href="/analysis/report/${scan.uid}" class="ui button view-btn">View</a></td>
                </tr>
            `;
            tbody.append(row);
        });
    }

    // Function to show a message
    function showMessage(type, text) {
        const messageContainer = $('#messageContainer');
        messageContainer.empty(); // Clear previous messages

        const messageHtml = `
            <div class="ui ${type} message">
                <i class="close icon"></i>
                <div class="content">${text}</div>
            </div>
        `;
        messageContainer.append(messageHtml);

        // Add close functionality
        $('.message .close').on('click', function () {
            $(this).closest('.message').transition('fade');
        });

        // Auto-hide after 5 seconds
        setTimeout(() => {
            $('.message').transition('fade');
        }, 5000);
    }

    // Select all checkbox
    $('#selectAll').on('change', function () {
        $('.row-select').prop('checked', this.checked);
        toggleDeleteButton();
    });

    // Individual row selection
    $(document).on('change', '.row-select', function () {
        const allChecked = $('.row-select').length === $('.row-select:checked').length;
        $('#selectAll').prop('checked', allChecked);
        toggleDeleteButton();
    });

    // Delete button handling
    function toggleDeleteButton() {
        const hasSelected = $('.row-select:checked').length > 0;
        $('#deleteSelected').toggleClass('disabled', !hasSelected);
    }

    // Delete selected scans
    $('#deleteSelected').on('click', function () {
        if (!$(this).hasClass('disabled')) {
            const selectedRows = $('.row-select:checked').closest('tr');
            const scanNames = selectedRows.map((_, row) => $(row).find('td:eq(2)').text()).get();
            const scanIds = selectedRows.map((_, row) => parseInt($(row).attr('data-id'))).get();

            console.log('Selected IDs to delete:', scanIds);

            if (scanIds.length === 0) {
                console.log('No scans selected for deletion');
                return;
            }

            const confirmMessage =
                `Are you sure you want to delete ${scanIds.length} scan(s)?\n\nSelected scans:\n- ${scanNames.join('\n- ')}`;
            if (confirm(confirmMessage)) {
                console.log('Sending DELETE to /analysis/code-scans with payload:', {
                    scan_ids: scanIds
                });
                $.ajax({
                    url: '/analysis/code-scans',
                    method: 'DELETE',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        scan_ids: scanIds
                    }),
                    success: function (response) {
                        console.log('Delete response:', response);
                        if (response.status === 'success') {
                            showMessage('success', response.message);
                            fetchScans();
                        } else {
                            showMessage('error', 'Failed to delete scans');
                        }
                    },
                    error: function (xhr) {
                        console.error('Delete error:', xhr.responseText);
                        showMessage('error', 'Error occurred while deleting scans');
                    }
                });
            } else {
                console.log('Deletion cancelled by user');
            }
        }
    });

    // Search by name
    $('#searchName').on('input', function () {
        const searchTerm = this.value.toLowerCase();
        const filtered = allScans.filter(scan =>
            scan.scan_name.toLowerCase().includes(searchTerm)
        );
        renderTable(filtered);
    });

    // Filter by type
    $('#typeFilter').on('change', function () {
        const type = $(this).dropdown('get value');
        const filtered = type ?
            allScans.filter(scan => scan.scan_type === type) :
            allScans;
        renderTable(filtered);
    });
});
