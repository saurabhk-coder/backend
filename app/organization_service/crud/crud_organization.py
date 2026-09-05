import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.organization import OrganizationDb
from ..schemas.organization import OrganizationCreate, OrganizationUpdate
from app.user_service.models.user import UsersDb


def _to_uuid(val: Union[uuid.UUID, str]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


def generate_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", cleaned)


class CRUDOrganization:
    def get(self, db: Session, id: Union[uuid.UUID, str]) -> Optional[OrganizationDb]:
        try:
            org_uuid = _to_uuid(id)
            return db.query(OrganizationDb).filter(OrganizationDb.id == org_uuid).first()
        except (ValueError, TypeError):
            return None

    def get_by_slug(self, db: Session, slug: str) -> Optional[OrganizationDb]:
        return (
            db.query(OrganizationDb)
            .filter(func.lower(OrganizationDb.slug) == func.lower(slug.strip()))
            .first()
        )

    def get_by_name(self, db: Session, name: str) -> Optional[OrganizationDb]:
        return (
            db.query(OrganizationDb)
            .filter(func.lower(OrganizationDb.name) == func.lower(name.strip()))
            .first()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[OrganizationDb]:
        query = db.query(OrganizationDb)
        if status:
            query = query.filter(func.lower(OrganizationDb.status) == func.lower(status.strip()))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    OrganizationDb.name.ilike(pattern),
                    OrganizationDb.slug.ilike(pattern),
                    OrganizationDb.email.ilike(pattern),
                    OrganizationDb.city.ilike(pattern),
                    OrganizationDb.country.ilike(pattern),
                )
            )
        return query.order_by(OrganizationDb.created_at.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        query = db.query(func.count(OrganizationDb.id))
        if status:
            query = query.filter(func.lower(OrganizationDb.status) == func.lower(status.strip()))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    OrganizationDb.name.ilike(pattern),
                    OrganizationDb.slug.ilike(pattern),
                    OrganizationDb.email.ilike(pattern),
                    OrganizationDb.city.ilike(pattern),
                    OrganizationDb.country.ilike(pattern),
                )
            )
        return query.scalar() or 0

    def create(self, db: Session, *, obj_in: OrganizationCreate) -> OrganizationDb:
        now = datetime.now(timezone.utc)
        slug = obj_in.slug.strip() if obj_in.slug else generate_slug(obj_in.name)

        # Check for slug collision and append random suffix if needed
        existing = self.get_by_slug(db, slug)
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        db_obj = OrganizationDb(
            id=uuid.uuid4(),
            name=obj_in.name.strip(),
            slug=slug,
            email=obj_in.email.strip() if obj_in.email else None,
            phone=obj_in.phone.strip() if obj_in.phone else None,
            address=obj_in.address.strip() if obj_in.address else None,
            city=obj_in.city.strip() if obj_in.city else None,
            state=obj_in.state.strip() if obj_in.state else None,
            country=obj_in.country.strip() if obj_in.country else None,
            postal_code=obj_in.postal_code.strip() if obj_in.postal_code else None,
            status=obj_in.status.strip() if obj_in.status else "active",
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
        db_obj: OrganizationDb,
        obj_in: Union[OrganizationUpdate, Dict[str, Any]],
    ) -> OrganizationDb:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in [
            "name",
            "slug",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "status",
        ]:
            if field in update_data:
                val = update_data[field]
                setattr(db_obj, field, val.strip() if isinstance(val, str) else val)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def deactivate(self, db: Session, *, db_obj: OrganizationDb) -> OrganizationDb:
        db_obj.status = "inactive"
        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_user_counts(
        self,
        db: Session,
        organization_id: Union[uuid.UUID, str],
    ) -> Tuple[int, int]:
        try:
            org_uuid = _to_uuid(organization_id)
            total_users = (
                db.query(func.count(UsersDb.id))
                .filter(UsersDb.organization_id == org_uuid)
                .scalar()
                or 0
            )
            active_users = (
                db.query(func.count(UsersDb.id))
                .filter(
                    UsersDb.organization_id == org_uuid,
                    or_(
                        UsersDb.status == "active",
                        UsersDb.status.is_(None),
                    ),
                )
                .scalar()
                or 0
            )
            return total_users, active_users
        except Exception:
            return 0, 0


CRUD_ORGANIZATION = CRUDOrganization()
