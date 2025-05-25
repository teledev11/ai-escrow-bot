"""
Social Proof and Trust Rating System for Escrow Bot
Implements user reputation, feedback, and trust scoring mechanisms
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()

class TrustLevel(Enum):
    UNVERIFIED = "unverified"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class UserProfile(Base):
    """Enhanced user profile with trust metrics"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    
    # Trust metrics
    trust_score = Column(Float, default=0.0)
    trust_level = Column(String, default=TrustLevel.UNVERIFIED.value)
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    
    # Verification status
    phone_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    id_verified = Column(Boolean, default=False)
    
    # Activity metrics
    join_date = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    response_time_avg = Column(Float, default=0.0)  # Average response time in hours
    
    # Feedback summary
    positive_feedback = Column(Integer, default=0)
    neutral_feedback = Column(Integer, default=0)
    negative_feedback = Column(Integer, default=0)
    
    # Relationships
    feedbacks_received = relationship("UserFeedback", foreign_keys="UserFeedback.receiver_id", back_populates="receiver")
    feedbacks_given = relationship("UserFeedback", foreign_keys="UserFeedback.giver_id", back_populates="giver")
    badges = relationship("UserBadge", back_populates="user")

class UserFeedback(Base):
    """User feedback and rating system"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(String, nullable=False)
    giver_id = Column(String, ForeignKey("user_profiles.telegram_id"), nullable=False)
    receiver_id = Column(String, ForeignKey("user_profiles.telegram_id"), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    feedback_type = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    
    # Specific ratings
    communication_rating = Column(Integer, nullable=True)
    delivery_rating = Column(Integer, nullable=True)
    quality_rating = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    giver = relationship("UserProfile", foreign_keys=[giver_id], back_populates="feedbacks_given")
    receiver = relationship("UserProfile", foreign_keys=[receiver_id], back_populates="feedbacks_received")

class BadgeType(Base):
    """Available badge types"""
    __tablename__ = "badge_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    requirement = Column(Text, nullable=False)
    
class UserBadge(Base):
    """User achievements and badges"""
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user_profiles.telegram_id"), nullable=False)
    badge_type_id = Column(Integer, ForeignKey("badge_types.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("UserProfile", back_populates="badges")
    badge_type = relationship("BadgeType")

class TrustMetrics(Base):
    """Daily trust metrics tracking"""
    __tablename__ = "trust_metrics"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user_profiles.telegram_id"), nullable=False)
    date = Column(DateTime, default=datetime.now)
    
    trades_completed = Column(Integer, default=0)
    disputes_resolved = Column(Integer, default=0)
    response_time = Column(Float, default=0.0)
    trust_score_change = Column(Float, default=0.0)

class TrustSystem:
    """Main trust system manager"""
    
    def __init__(self):
        self.engine = create_engine(os.environ.get("DATABASE_URL"))
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        self._initialize_badges()
    
    def create_tables(self):
        """Create trust system tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Trust system tables created successfully")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def _initialize_badges(self):
        """Initialize default badges"""
        session = self.get_session()
        
        default_badges = [
            {
                "name": "First Timer",
                "description": "Completed your first trade",
                "icon": "🎯",
                "requirement": "Complete 1 trade"
            },
            {
                "name": "Trusted Trader",
                "description": "Completed 10 successful trades",
                "icon": "⭐",
                "requirement": "Complete 10 trades"
            },
            {
                "name": "Elite Trader",
                "description": "Completed 50 successful trades",
                "icon": "🏆",
                "requirement": "Complete 50 trades"
            },
            {
                "name": "Fast Responder",
                "description": "Average response time under 2 hours",
                "icon": "⚡",
                "requirement": "Response time < 2 hours"
            },
            {
                "name": "Verified Pro",
                "description": "Completed full verification",
                "icon": "✅",
                "requirement": "Phone + Email + ID verified"
            },
            {
                "name": "Customer Champion",
                "description": "95% positive feedback rate",
                "icon": "💎",
                "requirement": "95%+ positive feedback"
            },
            {
                "name": "Dispute Resolver",
                "description": "Resolved disputes fairly",
                "icon": "⚖️",
                "requirement": "Resolve 5+ disputes"
            },
            {
                "name": "Community Helper",
                "description": "Active community member",
                "icon": "🤝",
                "requirement": "Help other users"
            }
        ]
        
        for badge_data in default_badges:
            existing = session.query(BadgeType).filter_by(name=badge_data["name"]).first()
            if not existing:
                badge = BadgeType(**badge_data)
                session.add(badge)
        
        session.commit()
        session.close()
    
    def get_or_create_user(self, telegram_id: str, username: str = None, first_name: str = "User") -> UserProfile:
        """Get or create user profile"""
        session = self.get_session()
        
        user = session.query(UserProfile).filter_by(telegram_id=str(telegram_id)).first()
        if not user:
            user = UserProfile(
                telegram_id=str(telegram_id),
                username=username,
                first_name=first_name
            )
            session.add(user)
            session.commit()
        
        session.close()
        return user
    
    def calculate_trust_score(self, user_id: str) -> float:
        """Calculate comprehensive trust score"""
        session = self.get_session()
        user = session.query(UserProfile).filter_by(telegram_id=str(user_id)).first()
        
        if not user:
            session.close()
            return 0.0
        
        score = 50.0  # Base score
        
        # Trading history (30% weight)
        if user.total_trades > 0:
            success_rate = user.successful_trades / user.total_trades
            score += success_rate * 30
        
        # Feedback ratings (25% weight)
        total_feedback = user.positive_feedback + user.neutral_feedback + user.negative_feedback
        if total_feedback > 0:
            positive_rate = user.positive_feedback / total_feedback
            score += positive_rate * 25
        
        # Verification status (20% weight)
        verification_score = 0
        if user.phone_verified:
            verification_score += 7
        if user.email_verified:
            verification_score += 7
        if user.id_verified:
            verification_score += 6
        score += verification_score
        
        # Activity and longevity (15% weight)
        days_active = (datetime.now() - user.join_date).days
        if days_active > 0:
            activity_score = min(days_active / 30, 1) * 15  # Max 15 points for 30+ days
            score += activity_score
        
        # Response time (10% weight)
        if user.response_time_avg > 0:
            # Better response time = higher score
            response_score = max(0, 10 - (user.response_time_avg / 2))
            score += response_score
        
        # Cap at 100
        score = min(score, 100.0)
        
        # Update user's trust score
        user.trust_score = score
        user.trust_level = self._get_trust_level(score).value
        session.commit()
        session.close()
        
        return score
    
    def _get_trust_level(self, score: float) -> TrustLevel:
        """Determine trust level based on score"""
        if score >= 90:
            return TrustLevel.DIAMOND
        elif score >= 80:
            return TrustLevel.PLATINUM
        elif score >= 70:
            return TrustLevel.GOLD
        elif score >= 60:
            return TrustLevel.SILVER
        elif score >= 50:
            return TrustLevel.BRONZE
        else:
            return TrustLevel.UNVERIFIED
    
    def add_feedback(self, trade_id: str, giver_id: str, receiver_id: str, 
                    rating: int, comment: str = None, 
                    communication: int = None, delivery: int = None, quality: int = None) -> bool:
        """Add user feedback"""
        session = self.get_session()
        
        # Check if feedback already exists for this trade
        existing = session.query(UserFeedback).filter_by(
            trade_id=trade_id, giver_id=str(giver_id), receiver_id=str(receiver_id)
        ).first()
        
        if existing:
            session.close()
            return False
        
        # Determine feedback type
        if rating >= 4:
            feedback_type = FeedbackType.POSITIVE
        elif rating >= 3:
            feedback_type = FeedbackType.NEUTRAL
        else:
            feedback_type = FeedbackType.NEGATIVE
        
        # Create feedback
        feedback = UserFeedback(
            trade_id=trade_id,
            giver_id=str(giver_id),
            receiver_id=str(receiver_id),
            rating=rating,
            feedback_type=feedback_type.value,
            comment=comment,
            communication_rating=communication,
            delivery_rating=delivery,
            quality_rating=quality
        )
        
        session.add(feedback)
        
        # Update receiver's feedback counts
        receiver = session.query(UserProfile).filter_by(telegram_id=str(receiver_id)).first()
        if receiver:
            if feedback_type == FeedbackType.POSITIVE:
                receiver.positive_feedback += 1
            elif feedback_type == FeedbackType.NEUTRAL:
                receiver.neutral_feedback += 1
            else:
                receiver.negative_feedback += 1
        
        session.commit()
        session.close()
        
        # Recalculate trust score
        self.calculate_trust_score(receiver_id)
        self._check_badges(receiver_id)
        
        return True
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        session = self.get_session()
        user = session.query(UserProfile).filter_by(telegram_id=str(user_id)).first()
        
        if not user:
            session.close()
            return {}
        
        # Get recent feedback
        recent_feedback = session.query(UserFeedback).filter_by(
            receiver_id=str(user_id)
        ).order_by(UserFeedback.created_at.desc()).limit(5).all()
        
        # Get badges
        user_badges = session.query(UserBadge).filter_by(user_id=str(user_id)).all()
        
        total_feedback = user.positive_feedback + user.neutral_feedback + user.negative_feedback
        
        stats = {
            "user_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "trust_score": round(user.trust_score, 1),
            "trust_level": user.trust_level,
            "total_trades": user.total_trades,
            "successful_trades": user.successful_trades,
            "success_rate": round((user.successful_trades / max(user.total_trades, 1)) * 100, 1),
            "total_feedback": total_feedback,
            "positive_feedback": user.positive_feedback,
            "neutral_feedback": user.neutral_feedback,
            "negative_feedback": user.negative_feedback,
            "positive_rate": round((user.positive_feedback / max(total_feedback, 1)) * 100, 1),
            "verification": {
                "phone": user.phone_verified,
                "email": user.email_verified,
                "id": user.id_verified
            },
            "join_date": user.join_date,
            "last_active": user.last_active,
            "response_time_avg": round(user.response_time_avg, 1),
            "recent_feedback": [
                {
                    "rating": f.rating,
                    "comment": f.comment,
                    "type": f.feedback_type,
                    "date": f.created_at
                } for f in recent_feedback
            ],
            "badges": [
                {
                    "name": badge.badge_type.name,
                    "icon": badge.badge_type.icon,
                    "description": badge.badge_type.description,
                    "earned_at": badge.earned_at
                } for badge in user_badges
            ]
        }
        
        session.close()
        return stats
    
    def _check_badges(self, user_id: str):
        """Check and award badges based on user activity"""
        session = self.get_session()
        user = session.query(UserProfile).filter_by(telegram_id=str(user_id)).first()
        
        if not user:
            session.close()
            return
        
        # Check for badges to award
        badge_checks = {
            "First Timer": user.total_trades >= 1,
            "Trusted Trader": user.total_trades >= 10,
            "Elite Trader": user.total_trades >= 50,
            "Fast Responder": user.response_time_avg > 0 and user.response_time_avg < 2,
            "Verified Pro": user.phone_verified and user.email_verified and user.id_verified,
            "Customer Champion": (user.positive_feedback / max(user.positive_feedback + user.neutral_feedback + user.negative_feedback, 1)) >= 0.95
        }
        
        for badge_name, earned in badge_checks.items():
            if earned:
                badge_type = session.query(BadgeType).filter_by(name=badge_name).first()
                if badge_type:
                    existing_badge = session.query(UserBadge).filter_by(
                        user_id=str(user_id), badge_type_id=badge_type.id
                    ).first()
                    
                    if not existing_badge:
                        new_badge = UserBadge(
                            user_id=str(user_id),
                            badge_type_id=badge_type.id
                        )
                        session.add(new_badge)
        
        session.commit()
        session.close()
    
    def update_trade_completion(self, user_id: str, successful: bool = True):
        """Update user trade statistics"""
        session = self.get_session()
        user = session.query(UserProfile).filter_by(telegram_id=str(user_id)).first()
        
        if user:
            user.total_trades += 1
            if successful:
                user.successful_trades += 1
            user.last_active = datetime.now()
            
            session.commit()
        
        session.close()
        
        # Recalculate trust score and check badges
        self.calculate_trust_score(user_id)
        self._check_badges(user_id)

# Global trust system instance
trust_system = TrustSystem()