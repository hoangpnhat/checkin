from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date

# Create database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./competition.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    registration_date = Column(DateTime, default=datetime.now)

class CheckIn(Base):
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    check_in_date = Column(Date, default=date.today)
    check_in_time = Column(DateTime, default=datetime.now)
    score = Column(Float, default=0.0)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: Session, name: str, registration_date: datetime):
    user = User(name=name, registration_date=registration_date)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def has_checked_in_today(db: Session, name: str, today: date):
    check_in = db.query(CheckIn).filter(
        CheckIn.user_name == name,
        CheckIn.check_in_date == today
    ).first()
    return check_in is not None

def record_checkin(db: Session, name: str, check_in_time: datetime, score: float = 0.0):
    check_in = CheckIn(
        user_name=name,
        check_in_date=check_in_time.date(),
        check_in_time=check_in_time,
        score=score
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in