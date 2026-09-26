from sqlalchemy import Column, Integer, String, Text, DateTime
import datetime
from backend.app.database.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    external_job_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    job_url = Column(String, nullable=False)
    employment_type = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)
    posted_at = Column(String, nullable=True)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
