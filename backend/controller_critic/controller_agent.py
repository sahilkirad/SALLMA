# controller_agent.py

import ray
import requests
from typing import Dict, Any
from datetime import datetime

from gcs_interface import GCSContextManager

AUDIT_LOGGER_URL = "http://localhost:8000/log"
GCS_BUCKET_NAME = "your-gcs-bucket-name"  # ← change this

class ControllerAgent:
    def __init__(self):
        self.decision_thresholds = {
            "fraud": 0.7,
            "sla": 0.5,
            "compliance": 1.0
        }
        self.gcs = GCSContextManager(bucket_name=GCS_BUCKET_NAME)

    def evaluate(self, txn_id: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        decision_log = []
        flags = []

        for agent_name, result in agent_results.items():
            score = result.get("score", 0.0)
            verdict = result.get("verdict", "unknown")

            if score >= self.decision_thresholds.get(agent_name, 1.0):
                flags.append(agent_name)

            decision_log.append({
                "agent": agent_name,
                "score": score,
                "verdict": verdict
            })

        if "fraud" in flags:
            final_decision = "REJECT"
        elif "compliance" in flags:
            final_decision = "HOLD"
        else:
            final_decision = "APPROVE"

        result = {
            "txn_id": txn_id,
            "decision": final_decision,
            "timestamp": datetime.utcnow().isoformat(),
            "agents_considered": list(agent_results.keys()),
            "log": decision_log
        }

        # 1. Log to AuditLogger
        self.send_to_audit_logger(result)

        # 2. Store context to GCS
        self.gcs.put_context(txn_id, result)

        return result

    def send_to_audit_logger(self, data: Dict[str, Any]) -> None:
        try:
            response = requests.post(AUDIT_LOGGER_URL, json=data, timeout=3)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[AuditLogger Error] Failed to log decision: {e}")


@ray.remote
class ControllerActor:
    def __init__(self):
        self.agent = ControllerAgent()

    def process(self, txn_id: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        return self.agent.evaluate(txn_id, agent_results)
