from sqlalchemy.orm import Session
from ..crud.crud_user import CRUD_USER
from ...core import AppSettings
from ..models import UserDb

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)

    user = CRUD_USER.get_by_email(db, email=AppSettings.DEFAULTS.FIRST_SUPERUSER)
    if not user:
        user_in = UserDb(
            email=AppSettings.DEFAULTS.FIRST_SUPERUSER,
            password=AppSettings.DEFAULTS.FIRST_SUPERUSER_PASSWORD,
            active=True,
        )
        user = CRUD_USER.create(db, obj_in=user_in)  # noqa: F841
