# -*- coding: utf-8; -*-

from sys import stderr

from datetime import date

from sqlalchemy.exc import SQLAlchemyError

from medications import MedicationsDatabase, Medications


def main():
    try:
        url = MedicationsDatabase.construct_mysql_url('cse.unl.edu', 3306, 'kheyen', 'kheyen', 'AdJ:8w')
        medications_database = MedicationsDatabase(url)
        medications_database.ensure_tables_exist()
        print('Tables created.')
        session = medications_database.create_session()
        print('Records created.')
    except SQLAlchemyError as exception:
        print('Database setup failed!', file=stderr)
        print('Cause: {exception}'.format(exception=exception), file=stderr)
        exit(1)


if __name__ == '__main__':
    main()
