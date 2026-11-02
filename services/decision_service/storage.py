import os
import sqlite3
from typing import List, Set
try:
    from .models import Claim
except (ImportError, ValueError):
    from models import Claim

DATABASE_URL = os.getenv("DATABASE_URL", "")

class ClaimStore:
    def __init__(self):
        self.use_pg = False
        self.mock_registry: Set[str] = set()
        self.mock_claims: List[Claim] = []
        
        # Check if Postgres should be used
        if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS claims_registry (
                        hash VARCHAR(64) PRIMARY KEY,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS claims (
                        claim_id VARCHAR(100),
                        insurer_id VARCHAR(100),
                        policy_type VARCHAR(50),
                        claimant_id VARCHAR(100),
                        incident_date VARCHAR(50),
                        claim_amount NUMERIC,
                        provider_id VARCHAR(100),
                        diagnosis_or_incident_code VARCHAR(100),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                conn.close()
                self.use_pg = True
                print("Connected to PostgreSQL storage successfully.")
            except Exception as e:
                print(f"PostgreSQL unavailable ({e}). Using in-memory storage fallback.")
                self.use_pg = False

    def has_hash(self, exact_hash: str) -> bool:
        if self.use_pg:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM claims_registry WHERE hash = %s LIMIT 1;", (exact_hash,))
                row = cursor.fetchone()
                conn.close()
                return row is not None
            except Exception as e:
                print(f"DB Error checking hash: {e}")
        return exact_hash in self.mock_registry

    def add_hash(self, exact_hash: str):
        if self.use_pg:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO claims_registry (hash) VALUES (%s) ON CONFLICT DO NOTHING;", (exact_hash,))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"DB Error adding hash: {e}")
        self.mock_registry.add(exact_hash)

    def get_all_claims(self) -> List[Claim]:
        if self.use_pg:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT claim_id, insurer_id, policy_type, claimant_id,
                           incident_date, claim_amount, provider_id,
                           diagnosis_or_incident_code, description
                    FROM claims;
                """)
                rows = cursor.fetchall()
                conn.close()
                return [
                    Claim(
                        claim_id=r[0], insurer_id=r[1], policy_type=r[2],
                        claimant_id=r[3], incident_date=r[4], claim_amount=float(r[5]),
                        provider_id=r[6], diagnosis_or_incident_code=r[7], description=r[8]
                    )
                    for r in rows
                ]
            except Exception as e:
                print(f"DB Error fetching claims: {e}")
        return list(self.mock_claims)

    def add_claim(self, claim: Claim):
        if self.use_pg:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO claims (
                        claim_id, insurer_id, policy_type, claimant_id,
                        incident_date, claim_amount, provider_id,
                        diagnosis_or_incident_code, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    claim.claim_id, claim.insurer_id, claim.policy_type,
                    claim.claimant_id, claim.incident_date, claim.claim_amount,
                    claim.provider_id, claim.diagnosis_or_incident_code, claim.description
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"DB Error storing claim: {e}")
        self.mock_claims.append(claim)

    def reset(self):
        if self.use_pg:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("TRUNCATE TABLE claims_registry, claims;")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"DB Error resetting database: {e}")
        self.mock_registry.clear()
        self.mock_claims.clear()

claim_store = ClaimStore()
