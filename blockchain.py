from web3 import Web3

# Free public Sepolia RPC provider (no Infura, no API key)
w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia.publicnode.com"))


# Contract Address (your deployed contract on Sepolia)
contract_address = Web3.to_checksum_address("0x0D275dE023172dFd03d8b2B7A89878B9Bdd9b5f8")

# Contract ABI (just the functions we're using)
contract_abi = [
    {
        "inputs": [{"internalType": "string", "name": "reportHash", "type": "string"}],
        "name": "storeHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "string", "name": "reportHash", "type": "string"}],
        "name": "verifyHash",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Set up contract connection
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
from eth_account import Account

def store_report_hash(report_hash, private_key):
    from time import time
    account = Account.from_key(private_key)
    print("🔑 Using account:", account.address)

    print("⚙️ Getting nonce...")
    nonce = w3.eth.get_transaction_count(account.address)
    print("🔁 Nonce:", nonce)

    txn = contract.functions.storeHash(report_hash).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.to_wei('10', 'gwei'),
    })

    print("🧾 Transaction built.")
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
    print("✍️ Transaction signed.")

    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    print("📤 Transaction sent!")

    return w3.to_hex(tx_hash)



def verify_report_hash(report_hash):
    try:
        print("🧪 Calling smart contract verifyHash()...")
        exists, uploader, timestamp = contract.functions.verifyHash(report_hash).call()
        print("✅ Blockchain returned:", exists, uploader, timestamp)
        return {
            "exists": exists,
            "uploader": uploader,
            "timestamp": timestamp
        }
    except Exception as e:
        print("❌ Error verifying hash:", str(e))
        return {
            "exists": False,
            "uploader": None,
            "timestamp": None,
            "error": str(e)
        }

        
