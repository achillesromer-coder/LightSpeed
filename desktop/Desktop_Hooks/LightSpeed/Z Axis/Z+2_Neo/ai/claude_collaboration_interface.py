"""
Claude Collaboration Interface - Claude AI Integration
Neo Floor (Z+2) - Claude-Side Collaboration Tracking

Interface for Claude AI to participate in M1-2/2-3 collaboration system.
Tracks all changes, proposals, and votes made by Claude during development.

Floor: Neo
Z-Level: 2
Author: LightSpeed Team / Claude
Version: 0.9.7
Date: 2026-01-12
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import sys

# Add Merovingian to path for collaboration service
LIGHTSPEED_ROOT = Path(__file__).parents[3]
MEROVINGIAN_DIR = LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian"
if str(MEROVINGIAN_DIR) not in sys.path:
    sys.path.insert(0, str(MEROVINGIAN_DIR))

from core.services.collaboration_service import (
    CollaborationService,
    ParticipantRole,
    VoteType,
    ProposalStatus
)


@dataclass
class ClaudeAction:
    """Track Claude's actions during session"""
    action_type: str  # file_created, file_modified, proposal_made, vote_cast
    timestamp: str
    details: Dict[str, Any]
    session_id: str
    requires_approval: bool = True


class ClaudeCollaborationInterface:
    """
    Interface for Claude to participate in collaboration

    Responsibilities:
    - Track all file changes Claude makes
    - Create proposals for structural changes
    - Cast votes with 24.5% weight
    - Wait for M1-2/2-3 sign-off when required
    - Maintain audit trail of all actions
    """

    def __init__(self, lightspeed_root: Path):
        """Initialize Claude collaboration interface"""
        self.lightspeed_root = Path(lightspeed_root)
        self.neo_dir = self.lightspeed_root / "Z Axis" / "Z+2_Neo"
        self.claude_dir = self.neo_dir / "data" / "claude"
        self.claude_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.actions: List[ClaudeAction] = []
        self.pending_approvals: List[str] = []

        # Collaboration service
        self.collab_service = CollaborationService(lightspeed_root)
        self.collab_service.set_participant_active(ParticipantRole.CLAUDE, True)

        # Load session data
        self._load_session()

        print(f"[CLAUDE] Collaboration interface initialized - Session: {self.session_id}")

    def _load_session(self):
        """Load existing session data"""
        session_file = self.claude_dir / f"session_{self.session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.actions = [ClaudeAction(**a) for a in data.get('actions', [])]
                self.pending_approvals = data.get('pending_approvals', [])

    def _save_session(self):
        """Save session data"""
        session_file = self.claude_dir / f"session_{self.session_id}.json"
        data = {
            'session_id': self.session_id,
            'actions': [vars(a) for a in self.actions],
            'pending_approvals': self.pending_approvals
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def track_file_creation(
        self,
        file_path: Path,
        purpose: str,
        requires_approval: bool = False
    ):
        """
        Track file creation by Claude

        Parameters:
            file_path: Path to created file
            purpose: Why file was created
            requires_approval: Whether creation needs approval
        """
        action = ClaudeAction(
            action_type='file_created',
            timestamp=datetime.now().isoformat(),
            details={
                'file_path': str(file_path),
                'purpose': purpose,
                'file_type': file_path.suffix
            },
            session_id=self.session_id,
            requires_approval=requires_approval
        )

        self.actions.append(action)
        self._save_session()

        # Record in collaboration service
        self.collab_service.record_event(
            event_type='file_created',
            participant=ParticipantRole.CLAUDE,
            data=action.details
        )

        print(f"[CLAUDE] Tracked file creation: {file_path.name}")

        if requires_approval:
            print(f"[CLAUDE] ⚠️  Approval required for: {file_path.name}")

    def track_file_modification(
        self,
        file_path: Path,
        changes_description: str,
        requires_approval: bool = False
    ):
        """
        Track file modification by Claude

        Parameters:
            file_path: Path to modified file
            changes_description: What was changed
            requires_approval: Whether modification needs approval
        """
        action = ClaudeAction(
            action_type='file_modified',
            timestamp=datetime.now().isoformat(),
            details={
                'file_path': str(file_path),
                'changes': changes_description
            },
            session_id=self.session_id,
            requires_approval=requires_approval
        )

        self.actions.append(action)
        self._save_session()

        # Record in collaboration service
        self.collab_service.record_event(
            event_type='file_modified',
            participant=ParticipantRole.CLAUDE,
            data=action.details
        )

        print(f"[CLAUDE] Tracked file modification: {file_path.name}")

    def create_proposal(
        self,
        title: str,
        description: str,
        z_axis_floors: List[str],
        affected_files: List[str] = None,
        code_changes: Dict[str, str] = None
    ) -> str:
        """
        Create M1-2/2-3 proposal for structural changes

        Parameters:
            title: Proposal title
            description: Detailed description
            z_axis_floors: Floors affected
            affected_files: Files to be changed
            code_changes: Code changes

        Returns:
            Proposal ID
        """
        proposal_id = self.collab_service.create_proposal(
            title=title,
            description=description,
            proposer=ParticipantRole.CLAUDE,
            z_axis_floors=z_axis_floors,
            affected_files=affected_files or [],
            code_changes=code_changes or {}
        )

        # Track as action
        action = ClaudeAction(
            action_type='proposal_created',
            timestamp=datetime.now().isoformat(),
            details={
                'proposal_id': proposal_id,
                'title': title,
                'floors': z_axis_floors
            },
            session_id=self.session_id,
            requires_approval=True
        )

        self.actions.append(action)
        self.pending_approvals.append(proposal_id)
        self._save_session()

        print(f"[CLAUDE] Created proposal: {title}")
        print(f"[CLAUDE] Proposal ID: {proposal_id}")
        print(f"[CLAUDE] ⏳ Awaiting M1-2/2-3 sign-off...")

        return proposal_id

    def cast_vote(
        self,
        proposal_id: str,
        vote_type: VoteType,
        reasoning: str = ""
    ) -> bool:
        """
        Cast vote on proposal (24.5% weight)

        Parameters:
            proposal_id: Proposal to vote on
            vote_type: Vote type
            reasoning: Reasoning for vote

        Returns:
            True if vote accepted
        """
        success = self.collab_service.cast_vote(
            proposal_id=proposal_id,
            participant=ParticipantRole.CLAUDE,
            vote_type=vote_type,
            comment=reasoning
        )

        if success:
            # Track as action
            action = ClaudeAction(
                action_type='vote_cast',
                timestamp=datetime.now().isoformat(),
                details={
                    'proposal_id': proposal_id,
                    'vote_type': vote_type.value,
                    'reasoning': reasoning
                },
                session_id=self.session_id,
                requires_approval=False
            )

            self.actions.append(action)
            self._save_session()

            print(f"[CLAUDE] Cast vote: {vote_type.value} (24.5% weight)")
            print(f"[CLAUDE] Reasoning: {reasoning}")

        return success

    def check_proposal_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Check status of proposal

        Parameters:
            proposal_id: Proposal to check

        Returns:
            Proposal data or None
        """
        proposal = self.collab_service.get_proposal(proposal_id)

        if proposal:
            print(f"[CLAUDE] Proposal status: {proposal['status']}")
            print(f"[CLAUDE] Approval score: {proposal['approval_score']:.1%}")

            if proposal['status'] == 'approved':
                print(f"[CLAUDE] ✅ Proposal APPROVED - Can proceed with implementation")
                if proposal_id in self.pending_approvals:
                    self.pending_approvals.remove(proposal_id)
                    self._save_session()

        return proposal

    def wait_for_approval(self, proposal_id: str, timeout_seconds: int = 300) -> bool:
        """
        Wait for proposal approval (blocking)

        Parameters:
            proposal_id: Proposal to wait for
            timeout_seconds: Maximum wait time

        Returns:
            True if approved, False if timeout/rejected
        """
        import time

        print(f"[CLAUDE] ⏳ Waiting for approval of proposal {proposal_id}...")
        print(f"[CLAUDE] Timeout: {timeout_seconds}s")

        start_time = time.time()

        while (time.time() - start_time) < timeout_seconds:
            proposal = self.collab_service.get_proposal(proposal_id)

            if not proposal:
                print(f"[CLAUDE] ❌ Proposal not found")
                return False

            status = proposal['status']

            if status == 'approved':
                print(f"[CLAUDE] ✅ Proposal APPROVED!")
                if proposal_id in self.pending_approvals:
                    self.pending_approvals.remove(proposal_id)
                    self._save_session()
                return True

            elif status == 'rejected':
                print(f"[CLAUDE] ❌ Proposal REJECTED")
                if proposal_id in self.pending_approvals:
                    self.pending_approvals.remove(proposal_id)
                    self._save_session()
                return False

            # Check every 2 seconds
            time.sleep(2)

        print(f"[CLAUDE] ⏱️  Timeout waiting for approval")
        return False

    def get_pending_approvals(self) -> List[str]:
        """Get list of pending approval proposal IDs"""
        return self.pending_approvals.copy()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            'session_id': self.session_id,
            'total_actions': len(self.actions),
            'files_created': len([a for a in self.actions if a.action_type == 'file_created']),
            'files_modified': len([a for a in self.actions if a.action_type == 'file_modified']),
            'proposals_created': len([a for a in self.actions if a.action_type == 'proposal_created']),
            'votes_cast': len([a for a in self.actions if a.action_type == 'vote_cast']),
            'pending_approvals': len(self.pending_approvals),
            'actions': [vars(a) for a in self.actions]
        }

    def save_session_summary(self):
        """Save session summary report"""
        summary = self.get_session_summary()

        report_file = self.claude_dir / f"session_summary_{self.session_id}.md"

        report = f"""# Claude Collaboration Session Summary

**Session ID:** {self.session_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Session Statistics

- **Total Actions:** {summary['total_actions']}
- **Files Created:** {summary['files_created']}
- **Files Modified:** {summary['files_modified']}
- **Proposals Created:** {summary['proposals_created']}
- **Votes Cast:** {summary['votes_cast']}
- **Pending Approvals:** {summary['pending_approvals']}

## Actions Log

"""

        for i, action in enumerate(self.actions, 1):
            report += f"\n### {i}. {action.action_type.upper()}\n\n"
            report += f"**Timestamp:** {action.timestamp}\n\n"
            report += f"**Details:**\n```json\n{json.dumps(action.details, indent=2)}\n```\n\n"

            if action.requires_approval:
                report += "⚠️  **Requires Approval**\n\n"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[CLAUDE] Session summary saved: {report_file.name}")

    def cleanup(self):
        """Cleanup and save final state"""
        self.save_session_summary()
        self.collab_service.set_participant_active(ParticipantRole.CLAUDE, False)
        self.collab_service.stop()

        print(f"[CLAUDE] Session ended - {len(self.actions)} actions tracked")


# Usage example for Claude
if __name__ == "__main__":
    # Initialize Claude interface
    lightspeed_root = Path(__file__).parents[3]
    claude = ClaudeCollaborationInterface(lightspeed_root)

    # Example: Track file creation
    new_file = lightspeed_root / "test_file.py"
    claude.track_file_creation(
        file_path=new_file,
        purpose="Testing collaboration system",
        requires_approval=False
    )

    # Example: Create proposal
    proposal_id = claude.create_proposal(
        title="Add New Feature X",
        description="Implement feature X across Neo and Trinity floors",
        z_axis_floors=["Neo", "Trinity"],
        affected_files=["neo/feature.py", "trinity/ui.py"]
    )

    # Example: Cast vote
    claude.cast_vote(
        proposal_id=proposal_id,
        vote_type=VoteType.APPROVE,
        reasoning="Feature aligns with platform architecture"
    )

    # Check status
    claude.check_proposal_status(proposal_id)

    # Get session summary
    summary = claude.get_session_summary()
    print(json.dumps(summary, indent=2))

    # Cleanup
    claude.cleanup()
