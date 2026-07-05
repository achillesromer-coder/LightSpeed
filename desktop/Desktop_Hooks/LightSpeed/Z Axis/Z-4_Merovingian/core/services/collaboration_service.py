"""
Collaboration Service - AI Collaboration Backend
Merovingian Floor (Z-4) - Core Collaboration Infrastructure

Backend service managing Claude-Codex-User collaboration with M1-2/2-3 methodology.
Handles real-time synchronization, proposal management, and vote tracking.

Floor: Merovingian
Z-Level: -4
Author: LightSpeed Team
Version: 0.9.7
Date: 2026-01-12
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import threading
import logging
import time

logger = logging.getLogger(__name__)


class ParticipantRole(Enum):
    """Collaboration participant"""
    USER = "user"
    CLAUDE = "claude"
    CODEX = "codex"


class ProposalStatus(Enum):
    """M1-2/2-3 proposal status"""
    DRAFT = "draft"
    PENDING_M1 = "pending_m1"
    PENDING_M2 = "pending_m2"
    PENDING_M3 = "pending_m3"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class VoteType(Enum):
    """Vote type"""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    REQUEST_CHANGES = "request_changes"


@dataclass
class CollaborationEvent:
    """Collaboration event for tracking"""
    event_type: str  # message, proposal_created, vote_cast, status_change
    participant: ParticipantRole
    timestamp: str
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class M123Checkpoint:
    """M1-2/2-3 methodology checkpoint"""
    milestone: str  # M1, M2, or M3
    proposal_id: str
    votes: List[Dict[str, Any]]
    approval_score: float
    can_proceed: bool
    timestamp: str
    notes: str = ""


class CollaborationService:
    """
    Backend service for AI collaboration system

    Manages:
    - Real-time event synchronization
    - M1-2/2-3 proposal tracking
    - Vote aggregation and validation
    - Change audit trail
    - API integration points for Claude/Codex
    """

    def __init__(self, lightspeed_root: Path, event_bus: Optional[Any] = None):
        """Initialize collaboration service"""
        self.lightspeed_root = Path(lightspeed_root)
        self.event_bus = event_bus

        # Paths
        self.merovingian_dir = self.lightspeed_root / "Z Axis" / "Z-4_Merovingian"
        self.collab_dir = self.merovingian_dir / "data" / "collaboration"
        self.collab_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.proposals: Dict[str, Dict[str, Any]] = {}
        self.events: List[CollaborationEvent] = []
        self.checkpoints: List[M123Checkpoint] = []
        self.active_participants: Dict[ParticipantRole, bool] = {
            ParticipantRole.USER: True,
            ParticipantRole.CLAUDE: False,
            ParticipantRole.CODEX: False
        }

        # Voting weights
        self.voting_weights = {
            ParticipantRole.USER: 0.51,
            ParticipantRole.CLAUDE: 0.245,
            ParticipantRole.CODEX: 0.245
        }

        # Callbacks
        self.event_callbacks: List[Callable] = []

        # Load existing data
        self._load_state()

        # Start event processor
        self._running = True
        self._event_thread = threading.Thread(target=self._process_events, daemon=True)
        self._event_thread.start()

        logger.info("Collaboration Service initialized")

    def _load_state(self):
        """Load collaboration state from disk"""
        # Load proposals
        proposals_file = self.collab_dir / "proposals.json"
        if proposals_file.exists():
            with open(proposals_file, 'r', encoding='utf-8') as f:
                self.proposals = json.load(f)

        # Load events
        events_file = self.collab_dir / "events.json"
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
                self.events = [CollaborationEvent(**e) for e in event_data]

        # Load checkpoints
        checkpoints_file = self.collab_dir / "checkpoints.json"
        if checkpoints_file.exists():
            with open(checkpoints_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                self.checkpoints = [M123Checkpoint(**c) for c in checkpoint_data]

    def _save_state(self):
        """Save collaboration state to disk"""
        # Save proposals
        proposals_file = self.collab_dir / "proposals.json"
        with open(proposals_file, 'w', encoding='utf-8') as f:
            json.dump(self.proposals, f, indent=2)

        # Save events (keep last 10000)
        events_file = self.collab_dir / "events.json"
        with open(events_file, 'w', encoding='utf-8') as f:
            event_data = [asdict(e) for e in self.events[-10000:]]
            json.dump(event_data, f, indent=2)

        # Save checkpoints
        checkpoints_file = self.collab_dir / "checkpoints.json"
        with open(checkpoints_file, 'w', encoding='utf-8') as f:
            checkpoint_data = [asdict(c) for c in self.checkpoints]
            json.dump(checkpoint_data, f, indent=2)

    def record_event(
        self,
        event_type: str,
        participant: ParticipantRole,
        data: Dict[str, Any]
    ) -> CollaborationEvent:
        """
        Record collaboration event

        Parameters:
            event_type: Type of event
            participant: Who triggered the event
            data: Event data

        Returns:
            Created event
        """
        event = CollaborationEvent(
            event_type=event_type,
            participant=participant,
            timestamp=datetime.now().isoformat(),
            data=data
        )

        self.events.append(event)
        self._save_state()

        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

        # Publish to event bus
        if self.event_bus:
            self.event_bus.publish({
                'type': 'collaboration.event',
                'source': 'CollaborationService',
                'data': asdict(event)
            })

        logger.info(f"Event recorded: {event_type} by {participant.value}")
        return event

    def create_proposal(
        self,
        title: str,
        description: str,
        proposer: ParticipantRole,
        z_axis_floors: List[str],
        affected_files: List[str] = None,
        code_changes: Dict[str, str] = None
    ) -> str:
        """
        Create new M1-2/2-3 proposal

        Parameters:
            title: Proposal title
            description: Detailed description
            proposer: Who created the proposal
            z_axis_floors: Affected floors
            affected_files: Files to be changed
            code_changes: Code change details

        Returns:
            Proposal ID
        """
        proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        proposal = {
            'id': proposal_id,
            'title': title,
            'description': description,
            'proposer': proposer.value,
            'status': ProposalStatus.DRAFT.value,
            'created_at': datetime.now().isoformat(),
            'z_axis_floors': z_axis_floors,
            'affected_files': affected_files or [],
            'code_changes': code_changes or {},
            'votes': [],
            'approval_score': 0.0,
            'implementation_notes': ''
        }

        self.proposals[proposal_id] = proposal
        self._save_state()

        # Record event
        self.record_event(
            event_type='proposal_created',
            participant=proposer,
            data={'proposal_id': proposal_id, 'title': title}
        )

        logger.info(f"Proposal created: {proposal_id} - {title}")
        return proposal_id

    def cast_vote(
        self,
        proposal_id: str,
        participant: ParticipantRole,
        vote_type: VoteType,
        comment: str = ""
    ) -> bool:
        """
        Cast vote on proposal

        Parameters:
            proposal_id: Proposal to vote on
            participant: Who is voting
            vote_type: Type of vote
            comment: Optional comment

        Returns:
            True if vote accepted, False otherwise
        """
        if proposal_id not in self.proposals:
            logger.error(f"Proposal not found: {proposal_id}")
            return False

        proposal = self.proposals[proposal_id]

        # Determine milestone
        milestone = self._determine_milestone(proposal)

        # Create vote
        vote = {
            'participant': participant.value,
            'vote_type': vote_type.value,
            'weight': self.voting_weights[participant],
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
            'milestone': milestone
        }

        # Add vote
        proposal['votes'].append(vote)

        # Recalculate approval score
        self._update_proposal_status(proposal)

        # Save
        self._save_state()

        # Record event
        self.record_event(
            event_type='vote_cast',
            participant=participant,
            data={
                'proposal_id': proposal_id,
                'vote_type': vote_type.value,
                'milestone': milestone
            }
        )

        # Create checkpoint if milestone complete
        if self._is_milestone_complete(proposal, milestone):
            self._create_checkpoint(proposal, milestone)

        logger.info(f"Vote cast on {proposal_id}: {vote_type.value} by {participant.value}")
        return True

    def _determine_milestone(self, proposal: Dict[str, Any]) -> str:
        """Determine current M1-2/2-3 milestone"""
        status = proposal['status']

        if status in ['draft', 'pending_m1']:
            return 'M1'
        elif status == 'pending_m2':
            return 'M2'
        elif status == 'pending_m3':
            return 'M3'
        else:
            return 'M3'

    def _update_proposal_status(self, proposal: Dict[str, Any]):
        """Update proposal status based on votes"""
        # Calculate approval score
        approval_score = sum(
            v['weight'] for v in proposal['votes']
            if v['vote_type'] == 'approve'
        )
        proposal['approval_score'] = approval_score

        # Count participants who voted
        participants_voted = {v['participant'] for v in proposal['votes']}

        # Determine new status
        if approval_score >= 0.51:  # User must approve (51%)
            proposal['status'] = ProposalStatus.APPROVED.value
        elif len(participants_voted) >= 3 and approval_score > 0.5:
            proposal['status'] = ProposalStatus.PENDING_M3.value
        elif len([v for v in proposal['votes'] if v['vote_type'] == 'approve']) >= 2:
            proposal['status'] = ProposalStatus.PENDING_M2.value
        else:
            proposal['status'] = ProposalStatus.PENDING_M1.value

        # Record status change
        self.record_event(
            event_type='status_change',
            participant=ParticipantRole.USER,  # System event
            data={
                'proposal_id': proposal['id'],
                'new_status': proposal['status'],
                'approval_score': approval_score
            }
        )

    def _is_milestone_complete(self, proposal: Dict[str, Any], milestone: str) -> bool:
        """Check if milestone is complete"""
        milestone_votes = [
            v for v in proposal['votes']
            if v['milestone'] == milestone
        ]

        if milestone == 'M1':
            # M1: At least 2 approvals
            approvals = len([v for v in milestone_votes if v['vote_type'] == 'approve'])
            return approvals >= 2

        elif milestone == 'M2':
            # M2: All three participants voted
            participants = {v['participant'] for v in milestone_votes}
            return len(participants) >= 3

        elif milestone == 'M3':
            # M3: User approved (51%)
            user_approval = any(
                v['participant'] == 'user' and v['vote_type'] == 'approve'
                for v in milestone_votes
            )
            return user_approval and proposal['approval_score'] >= 0.51

        return False

    def _create_checkpoint(self, proposal: Dict[str, Any], milestone: str):
        """Create M1-2/2-3 checkpoint"""
        milestone_votes = [
            v for v in proposal['votes']
            if v['milestone'] == milestone
        ]

        checkpoint = M123Checkpoint(
            milestone=milestone,
            proposal_id=proposal['id'],
            votes=milestone_votes,
            approval_score=proposal['approval_score'],
            can_proceed=self._is_milestone_complete(proposal, milestone),
            timestamp=datetime.now().isoformat(),
            notes=f"{milestone} complete for proposal {proposal['title']}"
        )

        self.checkpoints.append(checkpoint)
        self._save_state()

        logger.info(f"Checkpoint created: {milestone} for {proposal['id']}")

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal by ID"""
        return self.proposals.get(proposal_id)

    def get_all_proposals(self) -> List[Dict[str, Any]]:
        """Get all proposals"""
        return list(self.proposals.values())

    def get_active_proposals(self) -> List[Dict[str, Any]]:
        """Get active (non-completed) proposals"""
        return [
            p for p in self.proposals.values()
            if p['status'] not in ['approved', 'rejected', 'implemented']
        ]

    def get_events(
        self,
        event_type: Optional[str] = None,
        participant: Optional[ParticipantRole] = None,
        limit: int = 100
    ) -> List[CollaborationEvent]:
        """
        Get collaboration events

        Parameters:
            event_type: Filter by event type
            participant: Filter by participant
            limit: Maximum events to return

        Returns:
            List of events
        """
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if participant:
            events = [e for e in events if e.participant == participant]

        return events[-limit:]

    def register_event_callback(self, callback: Callable):
        """Register callback for events"""
        self.event_callbacks.append(callback)

    def set_participant_active(self, participant: ParticipantRole, active: bool):
        """Set participant as active/inactive"""
        self.active_participants[participant] = active

        self.record_event(
            event_type='participant_status',
            participant=participant,
            data={'active': active}
        )

    def _process_events(self):
        """Background event processor"""
        while self._running:
            try:
                # Process any pending events
                # This could include:
                # - Checking for Claude/Codex responses
                # - Auto-advancing proposals through M1-2/2-3
                # - Sending notifications
                time.sleep(1)

            except Exception as e:
                logger.error(f"Event processor error: {e}")

    def stop(self):
        """Stop collaboration service"""
        self._running = False
        if self._event_thread.is_alive():
            self._event_thread.join(timeout=5)

        self._save_state()
        logger.info("Collaboration Service stopped")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    lightspeed_root = Path(__file__).parents[4]
    service = CollaborationService(lightspeed_root)

    # Create test proposal
    proposal_id = service.create_proposal(
        title="Test Proposal",
        description="Testing M1-2/2-3 system",
        proposer=ParticipantRole.CLAUDE,
        z_axis_floors=["Merovingian", "Neo"]
    )

    # Cast votes
    service.cast_vote(proposal_id, ParticipantRole.CLAUDE, VoteType.APPROVE)
    service.cast_vote(proposal_id, ParticipantRole.CODEX, VoteType.APPROVE)
    service.cast_vote(proposal_id, ParticipantRole.USER, VoteType.APPROVE)

    # Check status
    proposal = service.get_proposal(proposal_id)
    print(f"Proposal status: {proposal['status']}")
    print(f"Approval score: {proposal['approval_score']}")

    service.stop()
