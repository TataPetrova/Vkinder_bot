import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg2

DSN = "postgresql://postgres:@localhost:5432/vkinder"
Base = declarative_base()

def work_list(tablename):
    class User(Base):
        __tablename__ = tablename
        __table_args__ = {"schema": "vkinder_database", 'extend_existing': True}

        id_couple = sq.Column(sq.String(length=15), primary_key=True, unique=True)
        name_couple = sq.Column(sq.String(length=40))

        def __init__(self, id_couple, name_couple):
            self.id_couple = id_couple
            self.name_couple = name_couple
    return User


def work_table(engine):
    Base.metadata.create_all(engine)
