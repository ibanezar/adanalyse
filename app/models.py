from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # "image" or "video"
    product = Column(String, nullable=False, index=True)
    market = Column(String, nullable=True, index=True)
    outcome = Column(String, nullable=False)  # "winner" / "mid" / "loser"
    metric_note = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    features = relationship(
        "AdFeature", back_populates="ad", uselist=False, cascade="all, delete-orphan"
    )


class AdFeature(Base):
    __tablename__ = "ad_features"

    id = Column(Integer, primary_key=True)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=False, index=True)

    hook_type = Column(String, nullable=True)
    hook_description = Column(Text, nullable=True)
    first_3_sec_visual = Column(String, nullable=True)
    visual_style = Column(String, nullable=True)
    copy_structure = Column(String, nullable=True)
    cta_style = Column(String, nullable=True)
    pacing_notes = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)

    ad = relationship("Ad", back_populates="features")


class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True)
    product = Column(String, nullable=False, index=True)
    market = Column(String, nullable=True, index=True)
    pattern_summary = Column(Text, nullable=False)
    supporting_ad_ids = Column(String, nullable=False)  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)


class GeneratedPrompt(Base):
    __tablename__ = "generated_prompts"

    id = Column(Integer, primary_key=True)
    based_on_pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=False)
    target_product = Column(String, nullable=False)
    prompt_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
