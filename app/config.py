import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://jiwonjeong:postgres@localhost:5432/mydatabase"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = Config()