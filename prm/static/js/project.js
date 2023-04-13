// Tippy
tippy('[data-tippy-content]', {
    placement: 'bottom',
    animation: 'scale',
});

// Menu
let burger = document.getElementById("burger");
let sidenav = document.getElementById("sidenav");
let main = document.getElementById("main");

if (burger) {
    function close_menu() {
        sidenav.classList.remove('_active');
    }

    main.onclick = close_menu;

    if (burger && sidenav) {
        burger.addEventListener("click", function (e) {
            sidenav.classList.toggle('_active');

        });
    }
}

// function to set cookie
function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// get select element and add event listener to save selected value into cookie
const children_select_size = document.getElementById("children_size");
if (children_select_size) {
    children_select_size.addEventListener("change", function () {
        var selectedValue = this.options[this.selectedIndex].value;
        setCookie("children_size", selectedValue, 365); // save value into cookie for 1 year
    });
}
// get select element and add event listener to save selected value into cookie
const transactions_select_size = document.getElementById("transactions_size");
if (transactions_select_size) {
    transactions_select_size.addEventListener("change", function () {
        var selectedValue = this.options[this.selectedIndex].value;
        setCookie("transactions_size", selectedValue, 365); // save value into cookie for 1 year
    });
}


// Format phone inputs
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
