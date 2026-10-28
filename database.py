import os
from sqlmodel import create_engine, Session

DATABASE = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:AS01284780876@localhost:5432/SmartHealthCare"
)

engine = create_engine(DATABASE, echo=True)

def get_session():
    with Session(engine) as session:

        yield session
