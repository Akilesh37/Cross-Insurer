from collections import defaultdict
from typing import Dict, List, Any
try:
    from .storage import claim_store
    from .models import Claim
except (ImportError, ValueError):
    from storage import claim_store
    from models import Claim

def mask_claimant(claimant_id: str) -> str:
    s = claimant_id.strip()
    if len(s) > 4:
        return f"***{s[-4:]}"
    return s

def build_fraud_network_graph() -> Dict[str, Any]:
    """
    Constructs a cross-insurer entity graph and detects collusive fraud rings,
    calculating node degree centralities and identifying high-risk syndicates.
    """
    claims: List[Claim] = claim_store.get_all_claims()
    
    nodes_dict: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    
    # Tracking indices for ring analysis
    claimant_insurers = defaultdict(set)
    claimant_claims = defaultdict(list)
    provider_insurers = defaultdict(set)
    provider_claims = defaultdict(list)
    insurer_claims = defaultdict(list)
    
    for c in claims:
        cid = c.claim_id
        ins = c.insurer_id
        clm = c.claimant_id.strip()
        prv = c.provider_id.strip()
        
        masked_clm = mask_claimant(clm)
        
        # 1. Add Insurer Node
        if ins not in nodes_dict:
            nodes_dict[ins] = {
                "id": ins,
                "label": ins,
                "type": "insurer",
                "risk": "LOW",
                "degree": 0,
                "details": f"Consortium Member Insurer ({ins})"
            }
            
        # 2. Add Claimant Node
        clm_node_id = f"clm_{clm}"
        if clm_node_id not in nodes_dict:
            nodes_dict[clm_node_id] = {
                "id": clm_node_id,
                "label": f"Claimant {masked_clm}",
                "type": "claimant",
                "risk": "LOW",
                "degree": 0,
                "raw_id": masked_clm,
                "details": f"Claimant Entity [Masked PII: {masked_clm}]"
            }
            
        # 3. Add Provider Node
        prv_node_id = f"prv_{prv}"
        if prv_node_id not in nodes_dict:
            nodes_dict[prv_node_id] = {
                "id": prv_node_id,
                "label": prv,
                "type": "provider",
                "risk": "LOW",
                "degree": 0,
                "raw_id": prv,
                "details": f"Healthcare / Repair Provider [{prv}]"
            }
            
        # 4. Add Claim Node
        claim_node_id = f"claim_{cid}"
        nodes_dict[claim_node_id] = {
            "id": claim_node_id,
            "label": f"Claim #{cid}",
            "type": "claim",
            "risk": "LOW",
            "degree": 0,
            "amount": c.claim_amount,
            "incident_date": c.incident_date,
            "policy_type": c.policy_type,
            "details": f"Claim #{cid} | ${c.claim_amount:,.2f} | {c.policy_type} | {c.incident_date}"
        }
        
        # Connect Claim -> Insurer
        edges.append({
            "id": f"e_{cid}_{ins}",
            "source": claim_node_id,
            "target": ins,
            "relationship": "FILED_AT",
            "label": "Filed At"
        })
        
        # Connect Claim -> Claimant
        edges.append({
            "id": f"e_{cid}_{clm_node_id}",
            "source": claim_node_id,
            "target": clm_node_id,
            "relationship": "CLAIMANT",
            "label": "Submitted By"
        })
        
        # Connect Claim -> Provider
        edges.append({
            "id": f"e_{cid}_{prv_node_id}",
            "source": claim_node_id,
            "target": prv_node_id,
            "relationship": "SERVICED_BY",
            "label": "Serviced By"
        })
        
        claimant_insurers[clm].add(ins)
        claimant_claims[clm].append(c)
        provider_insurers[prv].add(ins)
        provider_claims[prv].append(c)
        insurer_claims[ins].append(c)
        
    # Calculate degree centralities
    for e in edges:
        s = e["source"]
        t = e["target"]
        if s in nodes_dict:
            nodes_dict[s]["degree"] += 1
        if t in nodes_dict:
            nodes_dict[t]["degree"] += 1

    # --- Syndicate & Fraud Ring Detection ---
    fraud_rings: List[Dict[str, Any]] = []
    ring_counter = 1
    
    # 1. Detect Multi-Insurer Claimants
    for clm, ins_set in claimant_insurers.items():
        if len(ins_set) >= 2:
            clm_node_id = f"clm_{clm}"
            nodes_dict[clm_node_id]["risk"] = "CRITICAL"
            associated_claims = claimant_claims[clm]
            total_amt = sum(c.claim_amount for c in associated_claims)
            
            for c in associated_claims:
                nodes_dict[f"claim_{c.claim_id}"]["risk"] = "HIGH"
                
            fraud_rings.append({
                "ring_id": f"RING-{ring_counter:03d}",
                "name": f"Cross-Carrier Double-Dip Syndicate",
                "risk_level": "CRITICAL",
                "type": "MULTI_INSURER_CLAIMANT",
                "reason": f"Claimant {mask_claimant(clm)} submitted parallel claims to {len(ins_set)} competing insurers ({', '.join(ins_set)})",
                "member_count": len(associated_claims),
                "total_exposure": round(total_amt, 2),
                "insurers": list(ins_set),
                "primary_entity": mask_claimant(clm)
            })
            ring_counter += 1

    # 2. Detect Suspicious Provider Concentration
    for prv, ins_set in provider_insurers.items():
        if len(ins_set) >= 2 and len(provider_claims[prv]) >= 2:
            prv_node_id = f"prv_{prv}"
            if nodes_dict[prv_node_id]["risk"] != "CRITICAL":
                nodes_dict[prv_node_id]["risk"] = "HIGH"
                
            associated_claims = provider_claims[prv]
            total_amt = sum(c.claim_amount for c in associated_claims)
            
            fraud_rings.append({
                "ring_id": f"RING-{ring_counter:03d}",
                "name": f"Collusive Provider Hub [{prv}]",
                "risk_level": "HIGH",
                "type": "COLLUSIVE_PROVIDER",
                "reason": f"Provider {prv} is generating multiple claims across {len(ins_set)} carriers ({', '.join(ins_set)})",
                "member_count": len(associated_claims),
                "total_exposure": round(total_amt, 2),
                "insurers": list(ins_set),
                "primary_entity": prv
            })
            ring_counter += 1

    summary = {
        "total_claims": len(claims),
        "total_insurers": len(insurer_claims),
        "total_claimants": len(claimant_insurers),
        "total_providers": len(provider_insurers),
        "rings_detected": len(fraud_rings),
        "high_risk_entities": sum(1 for n in nodes_dict.values() if n["risk"] in ("CRITICAL", "HIGH"))
    }
    
    return {
        "nodes": list(nodes_dict.values()),
        "edges": edges,
        "fraud_rings": fraud_rings,
        "summary": summary
    }
