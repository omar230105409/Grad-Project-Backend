from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from database import engine, get_session
from  ..Model import models


app = FastAPI(title="Smart Medicine Bottle API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Medicine API"}


@app.get("/users/")
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(models.User)).all()
    return users
