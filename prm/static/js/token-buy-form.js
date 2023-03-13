const tokenInput = document.getElementById("id_token_amount");
const priceInput = document.getElementById('id_token_price_usd');
const unitPrice = document.getElementById('current_token_price').value;

tokenInput.addEventListener("input", (event) => {
    const amount = parseFloat(event.target.value);
    const totalPrice = amount * unitPrice;
    if (amount) {
        priceInput.value = totalPrice.toFixed(2) + " $";
    } else {
        priceInput.value = "";
    }
});
