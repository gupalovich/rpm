function handleAvatarSelect() {
    const avatars = document.querySelectorAll('.avatar-img');
    const avatarForm = document.getElementById('avatar-form');
    const avatarFormData = new FormData(avatarForm);
    const errorBlock = document.getElementById('error-block');

    // Make an AJAX request to update the user's avatar
    const xhr = new XMLHttpRequest();
    xhr.open('POST', avatarForm.action, true);
    xhr.setRequestHeader('X-CSRFToken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // Update the preview of the avatar image
            const response = JSON.parse(xhr.responseText);
            avatars.forEach(avatar => {
                avatar.src = response.avatar_url;
            });
            errorBlock.innerHTML = '';
        } else if (xhr.readyState === 4 && xhr.status === 400) {
            // Handle json errors
            const response = JSON.parse(xhr.responseText);
            errorBlock.innerHTML = response.error.join('<br>');
            throw response.error;
        };
    };
    xhr.send(avatarFormData);
}
// Handle custom 'avatar upload button' clicks
document.getElementById('avatar-select').addEventListener('click', function () {
    document.getElementById('avatar-input').click();
});
