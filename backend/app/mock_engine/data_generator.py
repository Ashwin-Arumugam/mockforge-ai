import uuid
import random
import time
from typing import Dict, Any, List, Optional

class SyntheticDataGenerator:
    """
    Automated Schema-Driven Synthetic Data Generator.
    Inspects OpenAPI request and response schemas and synthesizes 100% valid,
    schema-compliant, unique, and context-aware mock payloads.
    """
    @staticmethod
    def generate_payload(schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not schema or not isinstance(schema, dict):
            return {"id": f"id_{uuid.uuid4().hex[:8]}"}

        properties = schema.get("properties", {})
        required_fields = schema.get("required", list(properties.keys()))

        payload = {}
        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue
            payload[prop_name] = SyntheticDataGenerator._generate_field_value(prop_name, prop_schema)

        # Guarantee all required fields are populated
        for req_field in required_fields:
            if req_field not in payload:
                field_schema = properties.get(req_field, {"type": "string"})
                payload[req_field] = SyntheticDataGenerator._generate_field_value(req_field, field_schema)

        return payload

    @staticmethod
    def generate_response_payload(response_schema: Optional[Dict[str, Any]], req_payload: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Synthesizes a 100% OpenAPI compliant response payload for 2xx responses,
        populating assistant answers, vector embeddings, and task execution logs.
        """
        unique_suffix = uuid.uuid4().hex[:8]

        # 1. OpenAI Chat Completions Response Schema Detection
        if response_schema and ("choices" in response_schema.get("properties", {}) or "chat.completion" in str(response_schema)):
            user_prompt = "your request"
            if isinstance(req_payload, dict) and "messages" in req_payload:
                msgs = req_payload["messages"]
                if isinstance(msgs, list) and len(msgs) > 0 and isinstance(msgs[-1], dict):
                    user_prompt = msgs[-1].get("content", user_prompt)

            content_answer = SyntheticDataGenerator._generate_ai_answer(user_prompt)

            return {
                "id": f"chatcmpl_{unique_suffix}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req_payload.get("model", "gpt-4o-mini") if isinstance(req_payload, dict) else "gpt-4o-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content_answer
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": random.randint(10, 40),
                    "completion_tokens": random.randint(50, 150),
                    "total_tokens": random.randint(60, 190)
                }
            }

        # 2. Vector Embeddings Response Schema Detection
        if response_schema and ("embedding" in str(response_schema) or "data" in response_schema.get("properties", {})):
            return {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "index": 0,
                        "embedding": [round(random.uniform(-0.1, 0.1), 6) for _ in range(16)]
                    }
                ],
                "model": req_payload.get("model", "text-embedding-3-small") if isinstance(req_payload, dict) else "text-embedding-3-small"
            }

        # 3. AI Agent Task Execution Response Schema Detection
        if response_schema and ("status" in response_schema.get("properties", {}) or "agent" in entity_type.lower()):
            prompt_str = req_payload.get("prompt", "agent task") if isinstance(req_payload, dict) else "agent task"
            return {
                "id": f"task_{unique_suffix}",
                "user_id": req_payload.get("user_id", f"user_{unique_suffix[:6]}") if isinstance(req_payload, dict) else f"user_{unique_suffix[:6]}",
                "prompt": prompt_str,
                "agent_type": req_payload.get("agent_type", "coder") if isinstance(req_payload, dict) else "coder",
                "status": "COMPLETED",
                "result": f"Execution completed for '{prompt_str}'. Generated optimized pipeline code and passed all static analysis checks."
            }

        # 4. Standard Response Schema Fallback
        if response_schema and isinstance(response_schema, dict) and "properties" in response_schema:
            res = SyntheticDataGenerator.generate_payload(response_schema)
            if isinstance(req_payload, dict):
                for k, v in req_payload.items():
                    if k in res and v:
                        res[k] = v
            return res

        # 5. Fallback: Merge request payload with ID
        res_payload = dict(req_payload) if isinstance(req_payload, dict) else {}
        if "id" not in res_payload:
            prefix = entity_type.rstrip('s')
            res_payload["id"] = f"{prefix}_{unique_suffix[:6]}"
        return res_payload

    @staticmethod
    def _generate_ai_answer(prompt: str) -> str:
        p = prompt.lower()
        if "graphrag" in p or "graph" in p:
            return "GraphRAG combines Knowledge Graphs with vector search. It extracts entity-relation triples from source documents, constructs a graph index in Neo4j, and uses community detection algorithms (e.g. Leiden) to enable global reasoning over text corpora."
        elif "pytorch" in p or "model" in p or "training" in p:
            return "PyTorch pipeline initialized successfully. GPU device mapped to cuda:0. DataLoader batch size configured to 32 with AdamW optimizer (learning rate = 1e-4) and automatic mixed precision (AMP) enabled."
        elif "vector" in p or "embedding" in p:
            return "Dense vector embeddings generated using HNSW (Hierarchical Navigable Small World) index with Cosine similarity distance metric for fast nearest-neighbor retrieval."
        return f"Processed request: '{prompt}'. Synthesized context and validated compliance against OpenAPI specification."

    @staticmethod
    def _generate_field_value(field_name: str, field_schema: Dict[str, Any]) -> Any:
        unique_suffix = uuid.uuid4().hex[:6]
        field_type = field_schema.get("type", "string")

        # Enum property check
        if "enum" in field_schema and isinstance(field_schema["enum"], list) and len(field_schema["enum"]) > 0:
            return random.choice(field_schema["enum"])

        # Default property check
        if "default" in field_schema:
            return field_schema["default"]

        if field_type == "string":
            fn = field_name.lower()
            if "email" in fn:
                return f"user_{unique_suffix}@example.com"
            elif "name" in fn:
                return f"User_{unique_suffix.upper()}"
            elif "title" in fn:
                return f"Synthetic Title {unique_suffix}"
            elif "content" in fn or "prompt" in fn or "input" in fn:
                return f"Dynamic query prompt context {unique_suffix}"
            elif "id" in fn or fn.endswith("_id") or fn.endswith("id"):
                return f"{fn.replace('_id', '')}_{unique_suffix}"
            elif "role" in fn:
                return "user"
            return f"sample_{field_name}_{unique_suffix}"

        elif field_type in ["number", "integer"]:
            fn = field_name.lower()
            if "amount" in fn or "total" in fn or "price" in fn:
                return round(random.uniform(10.0, 500.0), 2)
            elif "quota" in fn:
                return 10000
            elif "temperature" in fn:
                return 0.7
            elif "created" in fn:
                return int(time.time())
            return random.randint(1, 100)

        elif field_type == "boolean":
            return True

        elif field_type == "array":
            fn = field_name.lower()
            items_schema = field_schema.get("items", {})

            if "embedding" in fn or "vector" in fn:
                return [round(random.uniform(-0.1, 0.1), 6) for _ in range(16)]

            if isinstance(items_schema, dict) and items_schema.get("type") == "object":
                item_obj = SyntheticDataGenerator.generate_payload(items_schema)
                return [item_obj]
            else:
                return [f"item_{unique_suffix}"]

        elif field_type == "object":
            return SyntheticDataGenerator.generate_payload(field_schema)

        return f"val_{unique_suffix}"
