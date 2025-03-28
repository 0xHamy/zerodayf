from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, CheckConstraint, UniqueConstraint, Text, DateTime
from datetime import datetime
import pytz, tzlocal, os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/zerodayf"
)

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()


def get_time():
    system_timezone = tzlocal.get_localzone()
    return datetime.now(pytz.timezone(str(system_timezone)))


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    provider = Column(String(50))
    model = Column(String(255))
    token = Column(String)
    max_tokens = Column(Integer)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_time)


class AnalysisTemplates(Base):
    __tablename__ = "analysis_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    data = Column(Text, nullable=False)
    template_type = Column(String(255), nullable=False)
    date = Column(DateTime(timezone=True), default=get_time)


class EndpointMappings(Base):
    __tablename__ = "endpoint_mappings"
    id = Column(Integer, primary_key=True)
    name = Column(String(512), nullable=False, unique=True)
    app_path = Column(String(4096))
    data = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), default=get_time)


class CodeScans(Base):
    __tablename__ = "code_scans"

    id = Column(Integer, primary_key=True)
    scan_name = Column(String(255), nullable=False)
    uid = Column(String(255), nullable=False)
    scan_type = Column(String(255), nullable=False)
    scan_template = Column(Text, nullable=False)
    scan_result = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), default=get_time)


SessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def empty_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        yield session

