from sqlalchemy import Column, Integer, String, Text

from backend.app.database.database import Base


class Candidate(Base):

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, nullable=True)

    target_roles = Column(Text, nullable=False)

    skills = Column(Text, nullable=False)

    preferred_location = Column(String, nullable=True)

    experience_level = Column(String, nullable=True)

    resume_filename = Column(String, nullable=True)