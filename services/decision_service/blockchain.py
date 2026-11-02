import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Consortium Insurer Ethereum Wallet Addresses
INSURER_ADDRESSES = {
    "InsurerA": "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7",
    "InsurerB": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    "InsurerC": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
    "InsurerD": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
}
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

class BlockchainLedger:
    def __init__(self):
        self.block_height = 100
        self.registry: Dict[str, Dict[str, Any]] = {} # claim_hash -> {insurer_id, address, block, tx_hash}
        self.ledger: List[Dict[str, Any]] = []
        self._init_genesis()

    def _init_genesis(self):
        genesis_block = {
            "block_number": 100,
            "timestamp": "2026-10-28T00:00:00Z",
            "tx_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "event_type": "GenesisConsortiumDeployed",
            "contract_address": CONTRACT_ADDRESS,
            "claim_hash": "0x0",
            "submitting_insurer": "ConsortiumRoot",
            "submitting_address": "0x0000000000000000000000000000000000000000",
            "gas_used": 0,
            "status": "CONFIRMED"
        }
        self.ledger.append(genesis_block)

    def get_insurer_address(self, insurer_id: str) -> str:
        return INSURER_ADDRESSES.get(insurer_id, f"0x{hashlib.sha256(insurer_id.encode()).hexdigest()[:40]}")

    def record_claim_registration(self, claim_hash: str, insurer_id: str, claim_id: str) -> Dict[str, Any]:
        """Records a new unique claim hash onto the consortium smart contract registry."""
        self.block_height += 1
        addr = self.get_insurer_address(insurer_id)
        
        # Deterministic tx_hash based on block, insurer, and claim_hash
        raw_seed = f"{self.block_height}:{addr}:{claim_hash}:{time.time()}"
        tx_hash = "0x" + hashlib.sha256(raw_seed.encode()).hexdigest()
        
        tx_receipt = {
            "block_number": self.block_height,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tx_hash": tx_hash,
            "contract_address": CONTRACT_ADDRESS,
            "event_type": "ClaimRegistered",
            "claim_hash": claim_hash,
            "claim_id": claim_id,
            "submitting_insurer": insurer_id,
            "submitting_address": addr,
            "gas_used": 45210,
            "status": "CONFIRMED"
        }
        
        self.registry[claim_hash] = {
            "insurer_id": insurer_id,
            "address": addr,
            "block_number": self.block_height,
            "tx_hash": tx_hash
        }
        self.ledger.append(tx_receipt)
        return tx_receipt

    def record_duplicate_alert(self, claim_hash: str, submitting_insurer: str, claim_id: str) -> Dict[str, Any]:
        """Emits an on-chain DuplicateAlert event when an exact hash collision occurs."""
        self.block_height += 1
        submitting_addr = self.get_insurer_address(submitting_insurer)
        original_entry = self.registry.get(claim_hash, {})
        original_insurer = original_entry.get("insurer_id", "Unknown")
        original_addr = original_entry.get("address", "0x0000000000000000000000000000000000000000")
        
        raw_seed = f"{self.block_height}:{submitting_addr}:DUPLICATE:{claim_hash}:{time.time()}"
        tx_hash = "0x" + hashlib.sha256(raw_seed.encode()).hexdigest()
        
        tx_receipt = {
            "block_number": self.block_height,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tx_hash": tx_hash,
            "contract_address": CONTRACT_ADDRESS,
            "event_type": "DuplicateAlert",
            "claim_hash": claim_hash,
            "claim_id": claim_id,
            "submitting_insurer": submitting_insurer,
            "submitting_address": submitting_addr,
            "original_insurer": original_insurer,
            "original_address": original_addr,
            "gas_used": 28140,
            "status": "ALERT_TRIGGERED"
        }
        self.ledger.append(tx_receipt)
        return tx_receipt

    def get_ledger(self) -> List[Dict[str, Any]]:
        # Return most recent transactions first
        return list(reversed(self.ledger))

    def reset(self):
        self.block_height = 100
        self.registry.clear()
        self.ledger.clear()
        self._init_genesis()

blockchain_ledger = BlockchainLedger()
