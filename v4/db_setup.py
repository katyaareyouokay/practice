from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Не найдена переменная окружения DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# импортирую Base из models.py, чтобы использовать правильный metadata
from models import Base


def init_db():
   
    Base.metadata.create_all(bind=engine)


def get_session():
    
    return SessionLocal()


if __name__ == "__main__":
    init_db()
    print("Таблицы созданы (если их не было).")
