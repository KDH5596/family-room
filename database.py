from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 데이터베이스 파일 경로 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 생성 (DB와 소통할 때 사용)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델을 정의할 때 사용할 기준 클래스
Base = declarative_base()


# 데이터베이스 세션을 가져오는 함수 (나중에 API에서 사용)
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()