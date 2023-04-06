const priceInput = document.getElementById("id_token_price_usd");
const tokenInput = document.getElementById("id_token_amount");
const unitPrice = parseFloat(document.getElementById("current_token_price").value);

priceInput.addEventListener("input", (event) => {
    const priceValue = parseFloat(event.target.value);
    const totalAmount = priceValue / unitPrice;

    if (totalAmount >= 1000) {
        tokenInput.value = "Вы получите: " + totalAmount;
    } else {
        tokenInput.value = "";
    }
});
