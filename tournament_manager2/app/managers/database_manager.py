from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base


class DataBaseManager:
    def __init__(self, data_dir, db_name):
        self.engine = create_engine('sqlite:///{}'.format(f'{data_dir}/{db_name}'))
        Base.metadata.create_all(self.engine)
        self.session_local = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.session_local()