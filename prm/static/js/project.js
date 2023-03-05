
function formatPhone(input) {
    // Remove non-digit characters
    let phone = input.value.replace(/\D/g, '');
    // Check if the phone number is long enough to format
    if (phone.length >= 3) {
        // Format the phone number
        phone = '8 (' + phone.substr(1, 3) + ') ' + phone.substr(4, 3) + '-' + phone.substr(7, 2) + '-' + phone.substr(9, 2);
        // Set the formatted phone number as the input value
        input.value = phone;
    }
}

// Get all input elements with type="tel"
const phoneInputs = document.querySelectorAll('input[type="tel"]');
// Add the formatPhone function as an oninput event listener to each input element
phoneInputs.forEach((input) => {
    input.addEventListener('input', () => {
        formatPhone(input);
    });
});
