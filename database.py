import os
from sqlmodel import create_engine, Session

DATABASE = os.getenv(
    "DATABASE_URL",
    "postgresql://USERNAME:PASSWORD@localhost:PORT/SmartHealthCare"
)

engine = create_engine(DATABASE, echo=True)

def get_session():
    with Session(engine) as session:

        yield session
