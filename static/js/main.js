// Main JavaScript file for Shareholder Portal

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Minimal modal handling - let Bootstrap handle everything
    // Remove any conflicting JavaScript

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancements
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Number input formatting
    var numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                // Format number with commas for display (optional)
                var num = parseInt(this.value);
                if (num >= 1000) {
                    this.setAttribute('data-formatted', num.toLocaleString());
                }
            }
        });
    });

    // Confirm modal for important actions
    var confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Real-time percentage calculation in admin panel
    var stockInputs = document.querySelectorAll('input[name="stock_count"]');
    stockInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var totalStocksElement = document.querySelector('[data-total-stocks]');
            if (totalStocksElement) {
                var totalStocks = parseInt(totalStocksElement.getAttribute('data-total-stocks'));
                var currentStocks = parseInt(this.value) || 0;
                var percentage = totalStocks > 0 ? (currentStocks / totalStocks * 100) : 0;
                
                // Update percentage display if element exists
                var percentageDisplay = this.closest('form').querySelector('[data-percentage-display]');
                if (percentageDisplay) {
                    percentageDisplay.textContent = percentage.toFixed(3) + '%';
                }
            }
        });
    });

    // Smooth scroll for anchor links (completely exclude any modal-related elements)
    var anchorLinks = document.querySelectorAll('a[href^="#"]:not([data-bs-toggle]):not([data-toggle]):not([href*="Modal"])');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            var href = this.getAttribute('href');
            var target = document.querySelector(href);
            if (target && href !== '#' && !this.hasAttribute('data-bs-toggle')) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Loading states for forms
    var submitButtons = document.querySelectorAll('form button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.closest('form').addEventListener('submit', function() {
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
            button.disabled = true;
        });
    });

    // Dark mode toggle (if implemented)
    var darkModeToggle = document.querySelector('#darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });

        // Load dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }

    // Table sorting (basic implementation)
    var sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="bi bi-arrow-down-up text-muted"></i>';
        
        header.addEventListener('click', function() {
            var table = this.closest('table');
            var tbody = table.querySelector('tbody');
            var rows = Array.from(tbody.querySelectorAll('tr'));
            var index = Array.from(this.parentNode.children).indexOf(this);
            var isAscending = this.classList.contains('sort-asc');
            
            // Clear previous sort indicators
            sortableHeaders.forEach(function(h) {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            
            rows.sort(function(a, b) {
                var aVal = a.children[index].textContent.trim();
                var bVal = b.children[index].textContent.trim();
                
                // Try to parse as numbers
                if (!isNaN(aVal) && !isNaN(bVal)) {
                    aVal = parseFloat(aVal);
                    bVal = parseFloat(bVal);
                }
                
                if (isAscending) {
                    return aVal > bVal ? -1 : 1;
                } else {
                    return aVal < bVal ? -1 : 1;
                }
            });
            
            // Update sort indicator
            this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
            
            // Rebuild table
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
        });
    });

    // Copy to clipboard functionality
    var copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var textToCopy = this.getAttribute('data-copy');
            navigator.clipboard.writeText(textToCopy).then(function() {
                // Show success feedback
                var originalText = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = originalText;
                }, 2000);
            });
        });
    });

    // Print functionality
    var printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    console.log('Stockholder Portal JavaScript initialized');
});