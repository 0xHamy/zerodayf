let source = null;
let confirmAction = null;

// Create one xterm instance
const term = new Terminal({
    cursorBlink: true,
    fontSize: 15,
    fontFamily: 'Courier New, Courier, monospace',
    theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
    },
    scrollback: 10000,
});

function setupSource() {
    // Clear existing logs first
    term.clear();
    term.writeln('Starting log display...\n');

    // Close any existing EventSource
    cleanupSource();

    // Create new EventSource connection
    window.eventSource = new EventSource('/proxy/stream-logs');

    // Handle incoming messages
    window.eventSource.onmessage = function(event) {
        try {
            const logEntry = JSON.parse(event.data);
            term.writeln(`Route: ${logEntry.route}`);
            term.writeln(`Endpoint: ${logEntry.endpoint}`);
            term.writeln('-'.repeat(40));
        } catch (e) {
            console.error('Error parsing log:', e);
        }
    };

    window.eventSource.onerror = function(error) {
        // Only show error if we haven't cleaned up intentionally
        if (window.eventSource) {
            console.error('EventSource error:', error);
            term.writeln('Connection to log stream interrupted - will try to reconnect...');

            // Attempt to reconnect after a delay
            setTimeout(() => {
                if (window.eventSource) { // Only reconnect if we haven't cleaned up
                    setupSource();
                }
            }, 2000);
        }
    };
}

function cleanupSource() {
    if (window.eventSource) {
        window.eventSource.close();
        window.eventSource = null;
        term.writeln('Log stream closed.');
    }
}

function initPage() {
    // Open the terminal
    term.open(document.getElementById('terminal'));
    document.querySelector('.xterm').style.padding = '10px';
    term.writeln('Welcome to the Proxy Log Terminal!');
    term.writeln('Logs will appear here.\n');

    // Initialize dropdown
    $('.ui.dropdown').dropdown();

    // Setup modal confirm
    $('#confirm-modal .approve.button').click(function() {
        if (confirmAction) confirmAction();
    });

    // Check if proxy is running on page load
    checkIfRunning();
    // Load the proxy settings
    loadProxySettings();

    // Save button
    $('#save-btn').click(saveProxySettings);

    // Start/Stop buttons
    $('#proxy_start').click(handleStartClick);
    $('#proxy_stop').click(handleStopClick);
}

function checkIfRunning() {
    $.get('/proxy/is-running', function(data) {
        toggleButtons(data.is_running);
        if (data.is_running) {
            setupSource();
        }
    });
}

function loadProxySettings() {
    $.get('/proxy/get-proxy', function(data) {
        const proxyDetails = $('#proxy-status .proxy-details');
        if (data.ip && data.port) {
            const type = data.proxy_type === 'zerodayf_to_browser' ?
                'Zerodayf to Browser' :
                'Zerodayf to Burpsuite [' + data.burpsuite + ']';
            proxyDetails.html(`${data.ip}:${data.port} (${type})`);
        } else {
            proxyDetails.html('No proxy configured');
        }
    });
}

function saveProxySettings() {
    const $btn = $(this);
    $btn.addClass('loading');

    const ip = $('#ip').val().trim();
    const port = $('#port').val().trim();
    const proxyType = $('input[name="proxy_type"]').val();
    const burpsuite = $('#burpsuite').val().trim();

    // Basic validation
    if (!ip || !port || !proxyType) {
        showNotification('Please fill all fields', 'error');
        $btn.removeClass('loading');
        return;
    }

    const portNumber = parseInt(port, 10);
    if (isNaN(portNumber) || portNumber < 1 || portNumber > 65535) {
        showNotification('Invalid port number (1-65535)', 'error');
        $btn.removeClass('loading');
        return;
    }

    $.ajax({
        url: '/proxy/save-proxy',
        method: 'POST',
        data: {
            ip: ip,
            port: portNumber,
            proxy_type: proxyType,
            burpsuite: burpsuite
        },
        success: function(response) {
            showNotification(response.message, response.status);
            loadProxySettings();
        },
        error: function(xhr) {
            const msg = xhr.responseJSON?.detail || 'Failed to save proxy';
            showNotification(msg, 'error');
        },
        complete: function() {
            $btn.removeClass('loading');
        }
    });
}

function handleStartClick() {
    openConfirmModal(
        'Start Proxy',
        'Are you sure you want to start the proxy?',
        function() {
            term.clear();
            term.writeln('Starting the proxy...');

            $.ajax({
                url: '/proxy/start',
                method: 'POST',
                success: function(data) {
                    term.writeln(data.message);
                    setupSource();
                    toggleButtons(true);
                },
                error: function(xhr) {
                    term.writeln(
                        `Error: ${xhr.responseJSON?.message || 'An error occurred'}`
                    );
                }
            });
        }
    );
}

function handleStopClick() {
    openConfirmModal(
        'Stop Proxy',
        'Are you sure you want to stop the proxy?',
        function() {
            cleanupSource();
            
            term.clear();
            term.writeln('Stopping the proxy...');

            $.ajax({
                url: '/proxy/stop',
                method: 'POST',
                success: function(data) {
                    term.writeln(data.message);
                    toggleButtons(false);
                },
                error: function(xhr) {
                    term.writeln(
                        `Error: ${xhr.responseJSON?.message || 'An error occurred'}`
                    );
                }
            });
        }
    );
}

function openConfirmModal(header, message, onConfirm) {
    confirmAction = onConfirm;
    $('#confirm-header').text(header);
    $('#confirm-message').text(message);
    $('#confirm-modal').modal('show');
}

function toggleButtons(isRunning) {
    if (isRunning) {
        $('#proxy_start').hide();
        $('#proxy_stop').show();
    } else {
        $('#proxy_stop').hide();
        $('#proxy_start').show();
    }
}

function showNotification(message, type = 'success') {
    const notification = $('#notification');
    notification.find('.message')
        .removeClass('positive negative')
        .addClass(type === 'success' ? 'positive' : 'negative')
        .find('.notification-text').text(message);

    notification.show().delay(5000).fadeOut();
    notification.find('.close').off('click').click(() => notification.hide());
}

// Initialize on DOM ready
$(document).ready(initPage);
