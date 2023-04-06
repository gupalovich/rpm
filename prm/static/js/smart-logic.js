const getWeb3 = async () => {
    return new Promise(async (resolve, reject) => {
        const web3 = new Web3(window.ethereum)

        try {
            await window.ethereum.request({ method: "eth_requestAccounts" })
            resolve(web3)
        } catch (err) {
            reject(err)
        }
    })
}

const getContract = async (web3, ABI, address) => {
    return new web3.eth.Contract(ABI, address)
}

const buyTokens = async (contract, address, amount, gasPrice) => {
    contract.methods.buyToken(amount * 1000).send({
        from: address,
        gasPrice: gasPrice,
        value: amount   
    })
}

const approveTokens = async (contract_usdt, contract_address, amount, gasPrice, address) => {
    contract_usdt.methods.approve(contract_address, amount).send({
        from: address,
        gasPrice: gasPrice,
    })
}


document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("buyButton").addEventListener("click", async () => {
        const contract_address = "0x43564cf90f2ab020b30a95c8764ca67c45a9a6e7"
        const web3 = await getWeb3()
        const contract = await getContract(web3, window.ABI_CONTRACT, contract_address)
        const contract_usdt = await getContract(web3, window.ABI_USDT, "0x22991a49a77bc92295b75880f16c60029fea97e6")
        const walletAddress = await web3.eth.requestAccounts()
        const gasPrice = await web3.eth.getGasPrice()
        const amount = parseFloat(document.getElementById("id_token_amount").value)
        const unitPrice = document.getElementById('current_token_price').value

        approveTokens(contract_usdt, contract_address, amount*unitPrice, gasPrice, walletAddress[0]).then(() => {
            // Pool alowance?
            buyTokens(contract, walletAddress[0], amount*unitPrice)
        })
    })
})