from web3 import Web3
import json
import os
import requests  # For sending alert to company

# Load contract-info.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "contract-info.json"), "r") as f:
    data = json.load(f)

RPC_URL = data["rpc_url"]
CONTRACT_ADDRESS = data["contract_address"]
ABI = data["abi"]
PRIVATE_KEY = data["private_key"]
ACCOUNT_ADDRESS = data["account_address"]

# Connect Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Contract instance
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)


def send_to_company(driver_id, driver_name, alert_type, alert_count, tx_hash):
    """
    Sends the alert info to the company API.
    """
    try:
        url = "http://127.0.0.1:5001/receive-alert"  # mock company API
        payload = {
            "driver_id": driver_id,
            "driver_name": driver_name,
            "alert_type": alert_type,
            "alert_count": alert_count,
            "tx_hash": tx_hash,
        }
        res = requests.post(url, json=payload)
        return f"Company server response: {res.json()}"
    except Exception as e:
        return f"Company server error: {str(e)}"


def log_alert(driver_id, alert_type, alert_count, driver_name):
    """
    Sends an alert summary to the blockchain and then notifies the company.
    """
    try:
        nonce = web3.eth.get_transaction_count(ACCOUNT_ADDRESS)

        # Build transaction with extra params: alert_count and driver_name
        tx = contract.functions.logAlert(
            driver_id, alert_type, alert_count, driver_name
        ).build_transaction(
            {
                "from": ACCOUNT_ADDRESS,
                "gas": 500000,  # Increased gas, adjust as needed
                "nonce": nonce,
                "maxFeePerGas": web3.eth.gas_price,
                "maxPriorityFeePerGas": web3.eth.gas_price // 10,
            }
        )

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)

        # Web3.py v6 uses raw_transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_hex = web3.to_hex(tx_hash)
        print(f"Alert logged. Tx Hash: {tx_hex}")

        # Send alert to company API
        company_response = send_to_company(
            driver_id, driver_name, alert_type, alert_count, tx_hex
        )
        print(company_response)

        return f"Alert logged and company notified. Tx Hash: {tx_hex}"

    except Exception as e:
        return f"Error logging alert: {str(e)}"
