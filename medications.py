from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

__app_package__ = 'edu.sepsis'


Persisted = declarative_base()

class Medications(Persisted):
    __tablename__ = 'medications'
    medications_id = Column(Integer, primary_key=True)
    patient_id= Column(String(256), nullable=False)
    medications_name = Column(String(256), nullable=False)
    taking_date = Column(DateTime)

    def print_patient_name(self):
        print(self.patient_name)


class MedicationsDatabase(object):
    @staticmethod
    def construct_mysql_url(authority, port, database, username, password):
        return 'mysql+mysqlconnector://{username}:{password}@{authority}:{port}/{database}' \
            .format(authority=authority, port=port, database=database, username=username, password=password)

    @staticmethod
    def construct_in_memory_url():
        return 'sqlite:///'

    def __init__(self, url):
        self.engine = create_engine(url)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)

    def ensure_tables_exist(self):
        Persisted.metadata.create_all(self.engine)

    def create_session(self):
        return self.Session()



