from unittest import TestCase, main
from main import RestApp
from datetime import *
from medications import Medications, MedicationsDatabase

class TestDatabase(TestCase):
       def test_create_workout_inserts_workout(self):
        url = MedicationsDatabase.construct_in_memory_url()
        medications_database = MedicationsDatabase(url)
        medications_database.ensure_tables_exist()
        session = medications_database.create_session()
        medication_list = []
        RestApp.check_heparin()
        result = session.query(Medications).delete

