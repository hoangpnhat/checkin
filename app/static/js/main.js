document.addEventListener('DOMContentLoaded', function() {
    // Show loading spinner during form submissions
    const forms = document.querySelectorAll('form');
    const loading = document.querySelector('.loading');
    
    if (forms.length && loading) {
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                loading.style.display = 'block';
            });
        });
    }
    
    // Automatically hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length) {
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 1s';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 1000);
            }, 5000);
        });
    }
    
    // Enable form validation
    const requiredInputs = document.querySelectorAll('input[required]');
    if (requiredInputs.length) {
        requiredInputs.forEach(input => {
            input.addEventListener('invalid', function(e) {
                e.preventDefault();
                this.classList.add('input-error');
            });
            
            input.addEventListener('input', function() {
                this.classList.remove('input-error');
            });
        });
    }
});

// Function to show confirmation dialog
function confirmAction(message) {
    return confirm(message);
}