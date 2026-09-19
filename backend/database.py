from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = "postgresql+psycopg://smartuser:smartpass@localhost:5432/smartvideo"


# Create database engine
engine = create_engine(DATABASE_URL)


# Create database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


def create_tables():
    # Import models here so SQLAlchemy knows about them
    from backend.models import CameraModel

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()