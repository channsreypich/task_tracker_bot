import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DB_URL = "sqlite+aiosqlite:///tasks.db"
engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    created_by = Column(String(255), nullable=False)
    assignee = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    due_date = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_by = Column(String(255), nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_task(chat_id: int, created_by: str, assignee: str, description: str, due_date: datetime.datetime):
    async with AsyncSessionLocal() as session:
        task = Task(
            chat_id=chat_id,
            created_by=created_by,
            assignee=assignee,
            description=description,
            due_date=due_date
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

async def get_active_tasks(chat_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.chat_id == chat_id, Task.is_completed == False)
        )
        return result.scalars().all()

async def complete_task(task_id: int, completed_by: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.is_completed = True
            task.completed_by = completed_by
            await session.commit()
            return task
        return None