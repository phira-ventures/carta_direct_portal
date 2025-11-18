// Ultra-simple modal handler - no conflicts
(function() {
    'use strict';
    
    // Wait for DOM and Bootstrap to be ready
    document.addEventListener('DOMContentLoaded', function() {
        // Remove all existing modal event listeners to start clean
        
        // Force clear any stuck modals on page load
        var stuckModals = document.querySelectorAll('.modal.show');
        stuckModals.forEach(function(modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
        });
        
        var stuckBackdrops = document.querySelectorAll('.modal-backdrop');
        stuckBackdrops.forEach(function(backdrop) {
            backdrop.remove();
        });
        
        // Clean body classes
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });
})();