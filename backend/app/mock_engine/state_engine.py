import uuid
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.mock_state import MockRecord, Relationship

class StateEngine:
    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id

    def extract_entity_id(self, payload: Dict[str, Any], entity_type: str) -> str:
        """Extracts primary key ID from payload or generates a new UUID."""
        if not isinstance(payload, dict):
            return str(uuid.uuid4())
            
        possible_id_keys = ["id", "_id", f"{entity_type.rstrip('s')}_id", f"{entity_type.rstrip('s')}Id"]
        for key in possible_id_keys:
            if key in payload and payload[key]:
                return str(payload[key])
                
        # Generate prefix ID e.g. user_a1b2c3d4
        prefix = entity_type.rstrip('s')
        generated_id = f"{prefix}_{str(uuid.uuid4())[:8]}"
        payload["id"] = generated_id
        return generated_id

    def detect_foreign_keys(self, payload: Dict[str, Any], current_entity_type: str) -> List[Tuple[str, str, str]]:
        """
        Detects foreign key fields in payload e.g. 'user_id': 'usr_123' or 'customer_id': 'usr_123'.
        Returns list of tuples: (parent_entity_type, parent_entity_id, fk_field_name)
        """
        fks = []
        if not isinstance(payload, dict):
            return fks

        for key, val in payload.items():
            if not val or not isinstance(val, (str, int)):
                continue

            str_val = str(val)
            # Match fields ending in _id or Id, e.g. user_id, userId, customer_id
            if (key.endswith("_id") or (key.endswith("Id") and len(key) > 2)) and key not in ["id", "_id"]:
                parent_prefix = key[:-3] if key.endswith("_id") else key[:-2]
                # Pluralize parent entity type (e.g. user -> users, category -> categories)
                if parent_prefix.endswith("y") and not parent_prefix.endswith(("ay", "ey", "oy", "uy")):
                    parent_entity_type = parent_prefix[:-1] + "ies"
                elif parent_prefix.endswith("s"):
                    parent_entity_type = parent_prefix
                else:
                    parent_entity_type = parent_prefix + "s"

                # Don't self-link
                if parent_entity_type.lower() != current_entity_type.lower():
                    fks.append((parent_entity_type.lower(), str_val, key))

        return fks

    def create_record(self, entity_type: str, payload: Dict[str, Any], validate_fk: bool = False) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Handles POST: Creates a new mock record and registers foreign key relationships.
        Returns (created_data, optional_error_message).
        """
        entity_id = self.extract_entity_id(payload, entity_type)

        # 1. Foreign Key Relationship Detection & Validation
        fk_relationships = self.detect_foreign_keys(payload, entity_type)
        if validate_fk:
            for parent_type, parent_id, fk_name in fk_relationships:
                parent_exists = self.db.query(MockRecord).filter(
                    MockRecord.project_id == self.project_id,
                    MockRecord.entity_type == parent_type,
                    MockRecord.entity_id == parent_id
                ).first()
                if not parent_exists:
                    return {}, f"Foreign Key Error: Parent '{parent_type}' with ID '{parent_id}' (via field '{fk_name}') does not exist in state."

        # 2. Check if record already exists
        existing = self.db.query(MockRecord).filter(
            MockRecord.project_id == self.project_id,
            MockRecord.entity_type == entity_type,
            MockRecord.entity_id == entity_id
        ).first()

        if existing:
            existing.data = payload
            self.db.commit()
            self.db.refresh(existing)
            created_data = existing.data
        else:
            record = MockRecord(
                project_id=self.project_id,
                entity_type=entity_type,
                entity_id=entity_id,
                data=payload
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            created_data = record.data

        # 3. Index Relationships in Relationships table
        for parent_type, parent_id, fk_name in fk_relationships:
            # Avoid duplicate relationship entries
            rel_exists = self.db.query(Relationship).filter(
                Relationship.project_id == self.project_id,
                Relationship.parent_entity_type == parent_type,
                Relationship.parent_entity_id == parent_id,
                Relationship.child_entity_type == entity_type,
                Relationship.child_entity_id == entity_id
            ).first()
            if not rel_exists:
                rel = Relationship(
                    project_id=self.project_id,
                    parent_entity_type=parent_type,
                    parent_entity_id=parent_id,
                    child_entity_type=entity_type,
                    child_entity_id=entity_id,
                    foreign_key_name=fk_name
                )
                self.db.add(rel)
        self.db.commit()

        return created_data, None

    def get_record_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Handles GET /entity/{id}: Retrieves record by ID."""
        record = self.db.query(MockRecord).filter(
            MockRecord.project_id == self.project_id,
            MockRecord.entity_type == entity_type,
            MockRecord.entity_id == entity_id
        ).first()
        return record.data if record else None

    def list_records(
        self, 
        entity_type: str, 
        query_params: Optional[Dict[str, Any]] = None,
        parent_filter: Optional[Tuple[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Handles GET /entity & GET /parents/{parentId}/children: Lists and filters records.
        parent_filter tuple format: (parent_entity_type, parent_entity_id) e.g. ('users', 'usr_123')
        """
        if parent_filter:
            parent_type, parent_id = parent_filter

            # Check if parent entity exists in state
            parent_exists = self.db.query(MockRecord).filter(
                MockRecord.project_id == self.project_id,
                MockRecord.entity_type == parent_type,
                MockRecord.entity_id == parent_id
            ).first()

            if not parent_exists:
                return []

            # Query child IDs linked to parent via Relationship table
            relationships = self.db.query(Relationship).filter(
                Relationship.project_id == self.project_id,
                Relationship.parent_entity_type == parent_type,
                Relationship.parent_entity_id == parent_id,
                Relationship.child_entity_type == entity_type
            ).all()
            
            child_ids = [rel.child_entity_id for rel in relationships]
            
            records = self.db.query(MockRecord).filter(
                MockRecord.project_id == self.project_id,
                MockRecord.entity_type == entity_type,
                MockRecord.entity_id.in_(child_ids)
            ).all() if child_ids else []
            
            result = [r.data for r in records if isinstance(r.data, dict)]
            
            # Fallback: also check if child record has parent ID embedded directly in JSON
            if not result:
                all_children = self.db.query(MockRecord).filter(
                    MockRecord.project_id == self.project_id,
                    MockRecord.entity_type == entity_type
                ).all()
                for r in all_children:
                    data = r.data
                    if isinstance(data, dict):
                        # Match foreign key fields like user_id, userId
                        for k, v in data.items():
                            if (k.startswith(parent_type.rstrip('s')) or k == f"{parent_type.rstrip('s')}_id") and str(v) == str(parent_id):
                                if data not in result:
                                    result.append(data)
        else:
            records = self.db.query(MockRecord).filter(
                MockRecord.project_id == self.project_id,
                MockRecord.entity_type == entity_type
            ).all()
            result = [r.data for r in records if isinstance(r.data, dict)]

        # Apply general query parameter filtering (e.g. ?status=PAID)
        if query_params:
            for k, v in query_params.items():
                if k in ["limit", "offset", "page"]:
                    continue
                result = [item for item in result if str(item.get(k)) == str(v)]

        return result

    def put_record(self, entity_type: str, entity_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Handles PUT /entity/{id}: Full entity replacement update."""
        record = self.db.query(MockRecord).filter(
            MockRecord.project_id == self.project_id,
            MockRecord.entity_type == entity_type,
            MockRecord.entity_id == entity_id
        ).first()

        payload["id"] = entity_id

        if record:
            record.data = payload
            self.db.commit()
            self.db.refresh(record)
            # Re-index foreign keys
            fk_relationships = self.detect_foreign_keys(payload, entity_type)
            for parent_type, parent_id, fk_name in fk_relationships:
                rel_exists = self.db.query(Relationship).filter(
                    Relationship.project_id == self.project_id,
                    Relationship.parent_entity_type == parent_type,
                    Relationship.parent_entity_id == parent_id,
                    Relationship.child_entity_type == entity_type,
                    Relationship.child_entity_id == entity_id
                ).first()
                if not rel_exists:
                    rel = Relationship(
                        project_id=self.project_id,
                        parent_entity_type=parent_type,
                        parent_entity_id=parent_id,
                        child_entity_type=entity_type,
                        child_entity_id=entity_id,
                        foreign_key_name=fk_name
                    )
                    self.db.add(rel)
            self.db.commit()
            return record.data, False
        else:
            data, _ = self.create_record(entity_type, payload)
            return data, True

    def patch_record(self, entity_type: str, entity_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handles PATCH /entity/{id}: Partial field mutation update."""
        record = self.db.query(MockRecord).filter(
            MockRecord.project_id == self.project_id,
            MockRecord.entity_type == entity_type,
            MockRecord.entity_id == entity_id
        ).first()

        if not record:
            return None

        updated_data = dict(record.data) if isinstance(record.data, dict) else {}
        updated_data.update(payload)
        updated_data["id"] = entity_id

        record.data = updated_data
        self.db.commit()
        self.db.refresh(record)

        # Re-index relationships if new foreign keys added
        fk_relationships = self.detect_foreign_keys(payload, entity_type)
        for parent_type, parent_id, fk_name in fk_relationships:
            rel_exists = self.db.query(Relationship).filter(
                Relationship.project_id == self.project_id,
                Relationship.parent_entity_type == parent_type,
                Relationship.parent_entity_id == parent_id,
                Relationship.child_entity_type == entity_type,
                Relationship.child_entity_id == entity_id
            ).first()
            if not rel_exists:
                rel = Relationship(
                    project_id=self.project_id,
                    parent_entity_type=parent_type,
                    parent_entity_id=parent_id,
                    child_entity_type=entity_type,
                    child_entity_id=entity_id,
                    foreign_key_name=fk_name
                )
                self.db.add(rel)
        self.db.commit()

        return record.data

    def delete_record(self, entity_type: str, entity_id: str) -> bool:
        """Handles DELETE /entity/{id}: Removes record and associated relationship links."""
        record = self.db.query(MockRecord).filter(
            MockRecord.project_id == self.project_id,
            MockRecord.entity_type == entity_type,
            MockRecord.entity_id == entity_id
        ).first()

        if not record:
            return False

        # Clean up relationships where this entity is parent or child
        self.db.query(Relationship).filter(
            Relationship.project_id == self.project_id,
            ((Relationship.parent_entity_type == entity_type) & (Relationship.parent_entity_id == entity_id)) |
            ((Relationship.child_entity_type == entity_type) & (Relationship.child_entity_id == entity_id))
        ).delete(synchronize_session=False)

        self.db.delete(record)
        self.db.commit()
        return True
