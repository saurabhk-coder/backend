import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..models.role import RoleDb
from ..schemas.role import RoleCreate, RoleUpdate


def _to_uuid(val: Union[uuid.UUID, str]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


class CRUDRole:
    def get(self, db: Session, id: Union[uuid.UUID, str]) -> Optional[RoleDb]:
        try:
            role_uuid = _to_uuid(id)
            return db.query(RoleDb).filter(RoleDb.id == role_uuid).first()
        except (ValueError, TypeError):
            return None

    def get_by_name(self, db: Session, name: str) -> Optional[RoleDb]:
        return db.query(RoleDb).filter(func.lower(RoleDb.name) == func.lower(name.strip())).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[RoleDb]:
        query = db.query(RoleDb)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    RoleDb.name.ilike(pattern),
                    RoleDb.description.ilike(pattern),
                )
            )
        return query.order_by(RoleDb.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, db: Session, *, search: Optional[str] = None) -> int:
        query = db.query(func.count(RoleDb.id))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    RoleDb.name.ilike(pattern),
                    RoleDb.description.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(self, db: Session, *, obj_in: RoleCreate) -> RoleDb:
        now = datetime.now(timezone.utc)
        db_obj = RoleDb(
            id=uuid.uuid4(),
            name=obj_in.name.strip(),
            description=obj_in.description.strip() if obj_in.description else None,
            permissions_json=obj_in.permissions_json if obj_in.permissions_json is not None else {},
            created_at=now,
            updated_at=now,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: RoleDb,
        obj_in: Union[RoleUpdate, Dict[str, Any]],
    ) -> RoleDb:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] is not None:
            db_obj.name = update_data["name"].strip()
        if "description" in update_data:
            db_obj.description = update_data["description"].strip() if update_data["description"] else None
        if "permissions_json" in update_data:
            db_obj.permissions_json = update_data["permissions_json"]

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Union[uuid.UUID, str]) -> Optional[RoleDb]:
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def update_permissions(
        self,
        db: Session,
        *,
        db_obj: RoleDb,
        permissions: Any,
    ) -> RoleDb:
        db_obj.permissions_json = permissions
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


CRUD_ROLE = CRUDRole()
