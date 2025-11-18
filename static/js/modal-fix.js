// Minimal modal fix - let Bootstrap handle modals naturally
document.addEventListener('DOMContentLoaded', function() {
    // Only add basic cleanup on modal hide
    document.addEventListener('hidden.bs.modal', function() {
        // Cleanup any stray backdrop elements
        var backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(function(backdrop) {
            if (!document.querySelector('.modal.show')) {
                backdrop.remove();
            }
        });
    });
});