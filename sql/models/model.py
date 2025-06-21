# models.py

from sqlalchemy import create_engine, Column, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# 建議從 config 引入 DATABASE_URL，讓設定集中管理
# 確保您的 config.py 中有 DATABASE_URL = os.getenv("DATABASE_URL")
from config import DATABASE_URL

# 建立所有模型都會繼承的 Base class
Base = declarative_base()


class Department(Base):
    """
    部門模型
    """
    __tablename__ = 'departments'
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    # 建立與 User 模型的一對多關聯
    # 'users' 屬性可以讓我們從一個 Department 物件輕易地存取所有關聯的 User 物件
    users = relationship("User", back_populates="department")


class User(Base):
    """
    使用者/員工模型
    """
    __tablename__ = 'users'
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)

    # 建立與 Department 模型的多對一關聯
    department_id = Column(String, ForeignKey('departments.id'))
    department = relationship("Department", back_populates="users")


class GroupOrder(Base):
    """
    揪團訂單模型
    """
    __tablename__ = 'group_orders'
    id = Column(String, primary_key=True, index=True)
    restaurant_name = Column(String, nullable=False)
    form_url = Column(String, nullable=True)

    # 儲存 Google Sheet 回覆表的 ID，用於後續統計
    response_sheet_id = Column(String, nullable=True)

    deadline = Column(DateTime, nullable=False)
    status = Column(String, default='open', nullable=False)
    department_name = Column(String, nullable=True)


# --- 資料庫初始化 ---

# 根據 DATABASE_URL 建立資料庫引擎
# `connect_args` 是 SQLite 特有的設定，允許多執行緒共享同一個連接
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# 建立 SessionLocal class，之後我們會用它來建立資料庫 session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    初始化資料庫，建立所有定義好的資料表。
    """
    print("Initializing database...")
    # Base.metadata.create_all 會檢查所有繼承自 Base 的 class，並在資料庫中建立對應的資料表
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


# 如果您直接執行這個檔案，可以方便地進行資料庫初始化
if __name__ == '__main__':
    init_db()