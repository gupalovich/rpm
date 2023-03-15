
function formatPhone(input) {
    // Remove non-digit characters
    let phone = input.value.replace(/\D/g, '');
    // Check if the phone number is long enough to format
    if (phone.length >= 3) {
        // Format the phone number for this format - 8 (999) 999-99-99
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


// Invite link copy
const inviteLinkButton = document.querySelector('#invite_link');
if (inviteLinkButton) {
    inviteLinkButton.addEventListener('click', (event) => {
        event.preventDefault();

        // Copy the referral link to clipboard
        const referralLink = inviteLinkButton.dataset.referralLink;
        navigator.clipboard.writeText(referralLink);

        // Add "animate" class to the button
        inviteLinkButton.classList.add('animate');

        // Remove the "animate" class after the animation is complete
        setTimeout(() => {
            inviteLinkButton.classList.remove('animate');
        }, 3000);
    });
}
