import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union
from sqlalchemy.orm import Session
from ..models.organization_setting import OrganizationSettingDb


def _to_uuid(val: Union[uuid.UUID, str]) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


class CRUDOrganizationSetting:
    def get(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> Optional[OrganizationSettingDb]:
        try:
            org_uuid = _to_uuid(organization_id)
            return (
                db.query(OrganizationSettingDb)
                .filter(
                    OrganizationSettingDb.organization_id == org_uuid,
                    OrganizationSettingDb.setting_key == setting_key.strip(),
                )
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get_multi(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrganizationSettingDb]:
        try:
            org_uuid = _to_uuid(organization_id)
            return (
                db.query(OrganizationSettingDb)
                .filter(OrganizationSettingDb.organization_id == org_uuid)
                .order_by(OrganizationSettingDb.setting_key.asc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except (ValueError, TypeError):
            return []

    def count(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
    ) -> int:
        try:
            org_uuid = _to_uuid(organization_id)
            return (
                db.query(OrganizationSettingDb)
                .filter(OrganizationSettingDb.organization_id == org_uuid)
                .count()
            )
        except (ValueError, TypeError):
            return 0

    def create_or_update(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
        setting_value: Optional[str],
    ) -> OrganizationSettingDb:
        org_uuid = _to_uuid(organization_id)
        now = datetime.now(timezone.utc)
        clean_key = setting_key.strip()

        db_obj = self.get(db, organization_id=org_uuid, setting_key=clean_key)
        if db_obj:
            db_obj.setting_value = setting_value
            db_obj.updated_at = now
        else:
            db_obj = OrganizationSettingDb(
                id=uuid.uuid4(),
                organization_id=org_uuid,
                setting_key=clean_key,
                setting_value=setting_value,
                created_at=now,
                updated_at=now,
            )
            db.add(db_obj)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        *,
        organization_id: Union[uuid.UUID, str],
        setting_key: str,
    ) -> Optional[OrganizationSettingDb]:
        db_obj = self.get(db, organization_id=organization_id, setting_key=setting_key)
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj


CRUD_ORGANIZATION_SETTING = CRUDOrganizationSetting()
