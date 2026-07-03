// Custom JavaScript for Food Waste Redistribution

// Function to confirm deletion
function confirmDelete(message) {
    return confirm(message);
}

// Function to show success alert
function showSuccessAlert(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').prepend(alertDiv);
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add confirmation to delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.display = 'none';
        }, 5000);
    });

    // Form validation (exclude login form)
    const forms = document.querySelectorAll('form:not([method="post"])');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'red';
                    isValid = false;
                } else {
                    field.style.borderColor = '#ccc';
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Enhanced confirmation alerts for actions
    const actionButtons = document.querySelectorAll('.btn-approve, .btn-reject, .btn-complete');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.classList.contains('btn-approve') ? 'approve' :
                          this.classList.contains('btn-reject') ? 'reject' : 'complete';
            if (!confirm(`Are you sure you want to ${action} this request?`)) {
                e.preventDefault();
            }
        });
    });
});
