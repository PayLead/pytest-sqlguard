from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///books.db", echo=True)


def get_session() -> Session:
    with Session(bind=engine, autoflush=True) as session:
        yield session
        session.commit()  # Autocommit for demonstration purposes


DB = Annotated[Session, Depends(get_session)]
