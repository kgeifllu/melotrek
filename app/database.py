from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Файл базы данных melotrek.db создастся сам рядом с проектом
engine = create_engine(
    "sqlite:///./melotrek.db",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Функция, которая выдаёт соединение с базой для каждого запроса
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
