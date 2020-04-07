import pytest
from hotline.database import create_tables, highlevel
from hotline.database import models as db


@pytest.fixture
def database(tmpdir):
    db_file = tmpdir.join("database.sqlite")
    highlevel.initialize_db(database=f"sqlite:///{db_file}")

    create_tables.create_tables()

    with db.db:
        yield db
