"""
Advanced Dispute Resolution System for Telegram Escrow Bot
Handles conflicts between buyers and sellers with professional moderation
"""

import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Dispute(Base):
    """Dispute cases in the escrow system"""
    __tablename__ = "disputes"
    
    id = Column(String(16), primary_key=True)
    transaction_id = Column(String(16), nullable=False)
    trade_title = Column(String(200), nullable=False)
    
    # Parties involved
    buyer_id = Column(String(20), nullable=False)
    buyer_username = Column(String(64), nullable=True)
    seller_id = Column(String(20), nullable=False) 
    seller_username = Column(String(64), nullable=True)
    
    # Dispute details
    dispute_type = Column(String(50), nullable=False)  # service_not_delivered, payment_not_received, quality_issue, etc.
    opened_by = Column(String(10), nullable=False)  # buyer or seller
    dispute_reason = Column(Text, nullable=False)
    evidence_provided = Column(Text, nullable=True)
    
    # Financial details
    dispute_amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    
    # Status and resolution
    status = Column(String(20), nullable=False, default="open")  # open, investigating, awaiting_response, resolved, closed
    priority = Column(String(10), nullable=False, default="normal")  # low, normal, high, urgent
    
    # Moderator assignment
    assigned_moderator = Column(String(20), nullable=True)
    moderator_username = Column(String(64), nullable=True)
    
    # Timeline
    created_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution details
    resolution_type = Column(String(30), nullable=True)  # refund_buyer, release_to_seller, partial_refund, mediated_agreement
    resolution_notes = Column(Text, nullable=True)
    moderator_decision = Column(Text, nullable=True)
    
    # Additional data
    dispute_data = Column(JSONB, nullable=True)
    
    def __repr__(self):
        return f"<Dispute {self.id}: {self.dispute_type} - {self.status}>"

class DisputeMessage(Base):
    """Messages and communications within a dispute case"""
    __tablename__ = "dispute_messages"
    
    id = Column(String(36), primary_key=True)
    dispute_id = Column(String(16), nullable=False)
    
    # Message details
    sender_id = Column(String(20), nullable=False)
    sender_username = Column(String(64), nullable=True)
    sender_role = Column(String(20), nullable=False)  # buyer, seller, moderator, system
    
    message_type = Column(String(30), nullable=False)  # text, evidence, decision, system_update
    message_content = Column(Text, nullable=False)
    attachments = Column(JSONB, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, default=datetime.now)
    read_by_buyer = Column(Boolean, default=False)
    read_by_seller = Column(Boolean, default=False)
    read_by_moderator = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<DisputeMessage {self.id}: {self.sender_role} in {self.dispute_id}>"

class Moderator(Base):
    """Moderators who handle dispute resolution"""
    __tablename__ = "moderators"
    
    id = Column(String(20), primary_key=True)
    username = Column(String(64), nullable=False)
    full_name = Column(String(100), nullable=False)
    
    # Moderator details
    role_level = Column(String(20), nullable=False, default="junior")  # junior, senior, lead, admin
    specialization = Column(String(100), nullable=True)  # crypto_disputes, service_disputes, high_value, etc.
    languages = Column(String(200), nullable=True)
    
    # Performance metrics
    cases_handled = Column(Integer, default=0)
    cases_resolved = Column(Integer, default=0)
    average_resolution_time = Column(Float, default=0.0)  # hours
    satisfaction_rating = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    current_case_load = Column(Integer, default=0)
    max_case_load = Column(Integer, default=10)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Moderator {self.username}: {self.role_level} - {self.cases_handled} cases>"

class DisputeSystem:
    """Main dispute resolution system"""
    
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize default moderators if none exist
        self._initialize_moderators()
    
    def _initialize_moderators(self):
        """Initialize default moderators"""
        existing_moderators = self.session.query(Moderator).count()
        if existing_moderators == 0:
            default_moderators = [
                {
                    'id': '001', 'username': 'admin_alex', 'full_name': 'Alex Rodriguez',
                    'role_level': 'admin', 'specialization': 'High-value disputes, Complex cases',
                    'languages': 'English, Spanish', 'max_case_load': 15
                },
                {
                    'id': '002', 'username': 'mod_sarah', 'full_name': 'Sarah Chen',
                    'role_level': 'senior', 'specialization': 'Crypto disputes, Technical issues',
                    'languages': 'English, Chinese', 'max_case_load': 12
                },
                {
                    'id': '003', 'username': 'mod_mike', 'full_name': 'Mike Johnson',
                    'role_level': 'senior', 'specialization': 'Service disputes, Quality issues',
                    'languages': 'English, French', 'max_case_load': 10
                },
                {
                    'id': '004', 'username': 'mod_emma', 'full_name': 'Emma Davis',
                    'role_level': 'junior', 'specialization': 'General disputes, First response',
                    'languages': 'English, German', 'max_case_load': 8
                }
            ]
            
            for mod_data in default_moderators:
                moderator = Moderator(**mod_data)
                self.session.add(moderator)
            
            self.session.commit()
    
    def open_dispute(self, transaction_id, trade_title, buyer_id, buyer_username, 
                    seller_id, seller_username, dispute_type, opened_by, 
                    dispute_reason, evidence, dispute_amount, currency):
        """Open a new dispute case"""
        dispute_id = f"DSP-{str(uuid.uuid4())[:8].upper()}"
        
        # Determine priority based on amount and dispute type
        priority = self._calculate_priority(dispute_amount, dispute_type)
        
        # Assign moderator
        assigned_moderator = self._assign_moderator(dispute_type, priority)
        
        dispute = Dispute(
            id=dispute_id,
            transaction_id=transaction_id,
            trade_title=trade_title,
            buyer_id=str(buyer_id),
            buyer_username=buyer_username,
            seller_id=str(seller_id),
            seller_username=seller_username,
            dispute_type=dispute_type,
            opened_by=opened_by,
            dispute_reason=dispute_reason,
            evidence_provided=evidence,
            dispute_amount=dispute_amount,
            currency=currency,
            priority=priority,
            assigned_moderator=assigned_moderator.id if assigned_moderator else None,
            moderator_username=assigned_moderator.username if assigned_moderator else None
        )
        
        self.session.add(dispute)
        
        # Create initial system message
        self._add_system_message(
            dispute_id, 
            f"Dispute opened by {opened_by}. Assigned to moderator @{assigned_moderator.username if assigned_moderator else 'pending'}."
        )
        
        # Update moderator case load
        if assigned_moderator:
            assigned_moderator.current_case_load += 1
            
        self.session.commit()
        return dispute
    
    def _calculate_priority(self, amount, dispute_type):
        """Calculate dispute priority based on amount and type"""
        if amount >= 0.1:  # 0.1 BTC or equivalent
            return "urgent"
        elif amount >= 0.05:
            return "high"
        elif dispute_type in ["payment_not_received", "service_not_delivered"]:
            return "high"
        else:
            return "normal"
    
    def _assign_moderator(self, dispute_type, priority):
        """Assign best available moderator for the dispute"""
        # Filter available moderators
        available_mods = self.session.query(Moderator).filter(
            Moderator.is_active == True,
            Moderator.is_available == True,
            Moderator.current_case_load < Moderator.max_case_load
        ).all()
        
        if not available_mods:
            return None
        
        # Prioritize by specialization and role level
        best_mod = None
        for mod in available_mods:
            if dispute_type.lower() in mod.specialization.lower():
                best_mod = mod
                break
        
        # If no specialist found, assign by role level and case load
        if not best_mod:
            available_mods.sort(key=lambda m: (m.current_case_load, m.role_level != 'admin'))
            best_mod = available_mods[0]
        
        return best_mod
    
    def add_dispute_message(self, dispute_id, sender_id, sender_username, sender_role, 
                           message_type, message_content, attachments=None):
        """Add a message to the dispute"""
        message_id = str(uuid.uuid4())
        
        message = DisputeMessage(
            id=message_id,
            dispute_id=dispute_id,
            sender_id=str(sender_id),
            sender_username=sender_username,
            sender_role=sender_role,
            message_type=message_type,
            message_content=message_content,
            attachments=attachments
        )
        
        self.session.add(message)
        
        # Update dispute last_updated
        dispute = self.session.query(Dispute).filter_by(id=dispute_id).first()
        if dispute:
            dispute.last_updated = datetime.now()
        
        self.session.commit()
        return message
    
    def _add_system_message(self, dispute_id, content):
        """Add a system message to the dispute"""
        return self.add_dispute_message(
            dispute_id, "system", "EscrowBot", "system", "system_update", content
        )
    
    def resolve_dispute(self, dispute_id, moderator_id, resolution_type, 
                       resolution_notes, moderator_decision):
        """Resolve a dispute case"""
        dispute = self.session.query(Dispute).filter_by(id=dispute_id).first()
        if not dispute:
            return None
        
        # Update dispute status
        dispute.status = "resolved"
        dispute.resolved_at = datetime.now()
        dispute.resolution_type = resolution_type
        dispute.resolution_notes = resolution_notes
        dispute.moderator_decision = moderator_decision
        
        # Add resolution message
        self._add_system_message(
            dispute_id,
            f"Dispute resolved by moderator. Resolution: {resolution_type}"
        )
        
        # Update moderator stats
        moderator = self.session.query(Moderator).filter_by(id=moderator_id).first()
        if moderator:
            moderator.current_case_load -= 1
            moderator.cases_resolved += 1
            
            # Calculate resolution time
            time_diff = dispute.resolved_at - dispute.created_at
            resolution_hours = time_diff.total_seconds() / 3600
            
            # Update average resolution time
            if moderator.cases_resolved == 1:
                moderator.average_resolution_time = resolution_hours
            else:
                current_avg = moderator.average_resolution_time
                moderator.average_resolution_time = (current_avg * (moderator.cases_resolved - 1) + resolution_hours) / moderator.cases_resolved
        
        self.session.commit()
        return dispute
    
    def get_dispute_by_id(self, dispute_id):
        """Get dispute details by ID"""
        return self.session.query(Dispute).filter_by(id=dispute_id).first()
    
    def get_user_disputes(self, user_id):
        """Get all disputes for a user"""
        return self.session.query(Dispute).filter(
            (Dispute.buyer_id == str(user_id)) | (Dispute.seller_id == str(user_id))
        ).order_by(Dispute.created_at.desc()).all()
    
    def get_dispute_messages(self, dispute_id):
        """Get all messages for a dispute"""
        return self.session.query(DisputeMessage).filter_by(
            dispute_id=dispute_id
        ).order_by(DisputeMessage.sent_at.asc()).all()
    
    def get_moderator_disputes(self, moderator_id):
        """Get all disputes assigned to a moderator"""
        return self.session.query(Dispute).filter_by(
            assigned_moderator=moderator_id
        ).order_by(Dispute.created_at.desc()).all()
    
    def get_active_disputes(self):
        """Get all active disputes"""
        return self.session.query(Dispute).filter(
            Dispute.status.in_(["open", "investigating", "awaiting_response"])
        ).order_by(Dispute.priority.desc(), Dispute.created_at.asc()).all()
    
    def get_moderator_stats(self, moderator_id):
        """Get moderator performance statistics"""
        moderator = self.session.query(Moderator).filter_by(id=moderator_id).first()
        if not moderator:
            return None
        
        return {
            'username': moderator.username,
            'full_name': moderator.full_name,
            'role_level': moderator.role_level,
            'cases_handled': moderator.cases_handled,
            'cases_resolved': moderator.cases_resolved,
            'success_rate': (moderator.cases_resolved / max(moderator.cases_handled, 1)) * 100,
            'average_resolution_time': round(moderator.average_resolution_time, 2),
            'current_case_load': moderator.current_case_load,
            'satisfaction_rating': moderator.satisfaction_rating,
            'specialization': moderator.specialization
        }

# Global dispute system instance
dispute_system = DisputeSystem()