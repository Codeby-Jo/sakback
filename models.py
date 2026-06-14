from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    education = Column(String(150), nullable=True)
    occupation = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # KYC Fields added from the feature/kyc branch
    kyc_status = Column(String, default="unverified")
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    is_banned = Column(Boolean, default=False)
    safety_status = Column(String(50), default="CLEAR")

    religious_details = relationship("ReligiousDetails", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("Preferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    kyc_records = relationship("KYCRecord", back_populates="user", cascade="all, delete-orphan")
    psychological_profile = relationship("PsychologicalProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class ReligiousDetails(Base):
    __tablename__ = "religious_details"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    prayer_level = Column(String(100), nullable=True)
    quran_reading_level = Column(String(100), nullable=True)
    islamic_knowledge = Column(String(255), nullable=True)
    hijab_status = Column(String(100), nullable=True)
    user = relationship("User", back_populates="religious_details")

class Preferences(Base):
    __tablename__ = "preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_age_min = Column(Integer, nullable=True)
    preferred_age_max = Column(Integer, nullable=True)
    preferred_city = Column(String(100), nullable=True)
    preferred_education = Column(String(150), nullable=True)
    preferred_religious_level = Column(String(100), nullable=True)
    location_flexibility = Column(String(50), nullable=True)
    marital_status = Column(String(100), nullable=True)
    work_outlook = Column(String(100), nullable=True)
    work_after_marriage = Column(String(100), nullable=True)
    tradition_pref = Column(String(100), nullable=True)
    tradition_strictness = Column(String(100), nullable=True)
    islamic_env_pref = Column(String(100), nullable=True)
    learning_pref = Column(String(100), nullable=True)
    reminder_style = Column(String(100), nullable=True)
    family_involvement = Column(String(100), nullable=True)
    marriage_timeline = Column(String(100), nullable=True)
    dealbreakers_text = Column(String, nullable=True)
    strict_age = Column(Boolean, default=False)
    strict_location = Column(Boolean, default=False)
    strict_tradition = Column(Boolean, default=False)
    strict_marital = Column(Boolean, default=False)
    no_match_confirmed = Column(Boolean, default=False)
    user = relationship("User", back_populates="preferences")

class PsychologicalProfile(Base):
    __tablename__ = "psychological_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    communication_style = Column(String(100), nullable=True)
    attachment_style = Column(String(100), nullable=True)
    marriage_readiness = Column(String(100), nullable=True)
    conflict_resolution = Column(String(100), nullable=True)
    financial_expectations = Column(String(150), nullable=True)
    living_arrangements = Column(String(150), nullable=True)
    anger_level = Column(String(100), nullable=True)
    boundary_strength = Column(String(100), nullable=True)
    emotional_steadiness = Column(String(100), nullable=True)
    financial_responsibility = Column(String(100), nullable=True)
    lifestyle_pattern = Column(String(100), nullable=True)
    disagreement_response = Column(String(200), nullable=True)
    family_pressure_response = Column(String(200), nullable=True)
    accountability_response = Column(String(200), nullable=True)
    personal_space_response = Column(String(200), nullable=True)
    user = relationship("User", back_populates="psychological_profile")

class KYCRecord(Base):
    __tablename__ = "kyc_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_type = Column(String)
    document_url = Column(String)
    selfie_url = Column(String)
    
    verification_status = Column(String, default="pending") # pending, verified, rejected
    verification_score = Column(Float, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="kyc_records")

class ConsideredSet(Base):
    __tablename__ = "considered_sets"
    id = Column(Integer, primary_key=True, index=True)
    considered_set_id = Column(String(100), unique=True, index=True)
    seeker_id = Column(Integer, ForeignKey("users.id"))
    candidate_ids = Column(JSON)
    nis_status = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    source = Column(String(50), default="NIS")

class CandidateInteraction(Base):
    __tablename__ = "candidate_interactions"
    id = Column(Integer, primary_key=True, index=True)
    seeker_id = Column(Integer, ForeignKey("users.id"))
    candidate_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50))  # SHOWN, PASS, INTEREST
    considered_set_id = Column(String(100), ForeignKey("considered_sets.considered_set_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), unique=True, index=True)
    seeker_a_id = Column(Integer, ForeignKey("users.id"))
    seeker_b_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matchflow_step = Column(String(50), default="INITIAL")
    unlocked_topics = Column(JSON, nullable=True)
    wali_present = Column(Boolean, default=False)
    photo_unlocked = Column(Boolean, default=False)
    source = Column(String(50), default="NIS_MUTUAL_INTEREST")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    msg_type = Column(String(20), default="text")  # text, system, image, video
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
