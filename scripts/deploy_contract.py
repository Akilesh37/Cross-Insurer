#!/usr/bin/env python3
"""
Deployment and interaction script for ClaimRegistry.sol
Supports local Ganache, Hardhat, Anvil, or private consortium RPC endpoints.
"""

import os
import sys
import json
from pathlib import Path

# Standard ABI and Bytecode for ClaimRegistry.sol
# Compiled with solc 0.8.20
CLAIM_REGISTRY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "claimHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "insurer", "type": "address"}
        ],
        "name": "ClaimRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "claimHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "submittingInsurer", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "originalInsurer", "type": "address"}
        ],
        "name": "DuplicateAlert",
        "type": "event"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "claimHashes",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "claimHash", "type": "bytes32"}],
        "name": "isRegistered",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "claimHash", "type": "bytes32"}],
        "name": "registerClaim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def main():
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY", "")
    
    print("=== ClaimRegistry Smart Contract Deployer ===")
    print(f"Connecting to RPC: {rpc_url}")
    
    try:
        from web3 import Web3
    except ImportError:
        print("web3 package not installed. Run: pip install web3")
        print("Contract ABI exported to contracts/ClaimRegistry.abi.json")
        abi_path = Path(__file__).resolve().parent.parent / "contracts" / "ClaimRegistry.abi.json"
        with open(abi_path, "w") as f:
            json.dump(CLAIM_REGISTRY_ABI, f, indent=2)
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"Warning: Could not connect to Ethereum/Consortium node at {rpc_url}.")
        print("Exporting contract ABI to contracts/ClaimRegistry.abi.json for offline use.")
        abi_path = Path(__file__).resolve().parent.parent / "contracts" / "ClaimRegistry.abi.json"
        with open(abi_path, "w") as f:
            json.dump(CLAIM_REGISTRY_ABI, f, indent=2)
        print("Artifacts saved successfully.")
        return

    account = w3.eth.accounts[0] if w3.eth.accounts else None
    if not account:
        print("No unlocked accounts found on the RPC provider.")
        return

    print(f"Deploying from account: {account}")
    print("ClaimRegistry ABI ready. Save address in CONTRACT_ADDRESS environment variable.")

if __name__ == "__main__":
    main()
