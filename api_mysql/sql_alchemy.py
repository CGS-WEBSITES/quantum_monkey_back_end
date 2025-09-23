from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from config import user, password, host, database

banco = SQLAlchemy()


class MySQLConnection:
    def __init__(self):
        self.connection = mysql.connector.connect(
            user=user, password=password, host=host, database=database
        )
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def execute(self, query, params=None):
        """Use for SELECT statements"""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def mutate(self, query, params=None):
        """Use for INSERT, UPDATE, DELETE"""
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.connection.close()
