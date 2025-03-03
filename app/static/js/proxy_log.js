let source = null;
let confirmAction = null;

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

/**
 * Sets up an EventSource connection to stream logs into the terminal.
 */
function setupSource() {
    term.clear();
    term.writeln('Starting log display...\n');
    cleanupSource();
    window.eventSource = new EventSource('/proxy/stream-logs');
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
        if (window.eventSource) {
            console.error('EventSource error:', error);
            term.writeln('Connection to log stream interrupted - will try to reconnect...');
            setTimeout(() => {
                if (window.eventSource) {
                    setupSource();
                }
            }, 2000);
        }
    };
}

/**
 * Closes the existing EventSource connection and updates the terminal.
 */
function cleanupSource() {
    if (window.eventSource) {
        window.eventSource.close();
        window.eventSource = null;
        term.writeln('Log stream closed.');
    }
}

/**
 * Initializes the page: sets up terminal, UI components, and event listeners.
 */
function initPage() {
    term.open(document.getElementById('terminal'));
    document.querySelector('.xterm').style.padding = '10px';
    term.writeln('Welcome to the Proxy Log Terminal!');
    term.writeln('Logs will appear here.\n');

    $('.ui.dropdown').dropdown();

    $('#confirm-modal .approve.button').click(function() {
        if (confirmAction) confirmAction();
    });

    checkIfRunning();
    loadProxySettings();

    $('#save-btn').click(saveProxySettings);
    $('#proxy_start').click(handleStartClick);
    $('#proxy_stop').click(handleStopClick);
}

/**
 * Checks if the proxy is running and updates UI accordingly.
 */
function checkIfRunning() {
    $.get('/proxy/is-running', function(data) {
        toggleButtons(data.is_running);
        if (data.is_running) {
            setupSource();
        }
    });
}

/**
 * Loads and displays the current proxy settings.
 */
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

/**
 * Saves proxy settings to the server with validation.
 */
function saveProxySettings() {
    const $btn = $(this);
    $btn.addClass('loading');

    const ip = $('#ip').val().trim();
    const port = $('#port').val().trim();
    const proxyType = $('input[name="proxy_type"]').val();
    const burpsuite = $('#burpsuite').val().trim();

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

/**
 * Handles the proxy start button click with confirmation.
 */
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
                    term.writeln(`Error: ${xhr.responseJSON?.message || 'An error occurred'}`);
                }
            });
        }
    );
}

/**
 * Handles the proxy stop button click with confirmation.
 */
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
                    term.writeln(`Error: ${xhr.responseJSON?.message || 'An error occurred'}`);
                }
            });
        }
    );
}

/**
 * Opens a confirmation modal with the given header, message, and callback.
 */
function openConfirmModal(header, message, onConfirm) {
    confirmAction = onConfirm;
    $('#confirm-header').text(header);
    $('#confirm-message').text(message);
    $('#confirm-modal').modal('show');
}

/**
 * Toggles visibility of start/stop buttons based on proxy state.
 */
function toggleButtons(isRunning) {
    if (isRunning) {
        $('#proxy_start').hide();
        $('#proxy_stop').show();
    } else {
        $('#proxy_stop').hide();
        $('#proxy_start').show();
    }
}

/**
 * Displays a notification with the given message and type.
 */
function showNotification(message, type = 'success') {
    const notification = $('#notification');
    notification.find('.message')
        .removeClass('positive negative')
        .addClass(type === 'success' ? 'positive' : 'negative')
        .find('.notification-text').text(message);

    notification.show().delay(5000).fadeOut();
    notification.find('.close').off('click').click(() => notification.hide());
}

$(document).ready(initPage);
