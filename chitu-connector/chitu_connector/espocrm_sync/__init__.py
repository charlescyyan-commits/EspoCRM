"""Offline-only Prospecting Engine to EspoCRM sync adapter."""

from chitu_connector.espocrm_sync.audit import SyncAuditLog
from chitu_connector.espocrm_sync.client import EspoCRMSyncAdapter, MockEspoCRMClient
from chitu_connector.espocrm_sync.contract import SyncContractPayload, validate_sync_contract
from chitu_connector.espocrm_sync.gate import evaluate_sync_gate
from chitu_connector.espocrm_sync.mapper import EspoCRMSyncMapper
from chitu_connector.espocrm_sync.lifecycle import LifecycleAction, LifecycleConflictError, LifecycleSyncResult, LifecycleSyncService
from chitu_connector.espocrm_sync.models import AdapterResult, AuditStatus, GateDecision, MockSyncStatus, SyncSource
from chitu_connector.espocrm_sync.real_client import LocalEspoCRMClient, RealSyncStatus
from chitu_connector.espocrm_sync.lifecycle_sync import LifecycleRuntimeResult, run_local_synthetic_lifecycle_sync
from chitu_connector.espocrm_sync.email_lifecycle import EmailLifecycleStatus, EmailLifecycleSyncResult, EmailLifecycleSyncService, EmailLifecycleUpdate
from chitu_connector.espocrm_sync.email_lifecycle_sync import EmailLifecycleRuntimeResult, run_local_synthetic_email_lifecycle_sync
from chitu_connector.espocrm_sync.connector_api import ConnectorApiError, ConnectorSyncResponse, ProspectingConnectorClient
from chitu_connector.espocrm_sync.feedback_api import FeedbackApiError, FeedbackConnectorClient, FeedbackSyncPayload, FeedbackSyncResponse
from chitu_connector.espocrm_sync.brevo_api import BrevoApiError, BrevoConnectorClient, BrevoEmailEventPayload, BrevoEmailEventResponse
from chitu_connector.espocrm_sync.feedback_signal_export import FeedbackSignalExportClient, FeedbackSignalExportError, FeedbackSignalPayload
from chitu_connector.espocrm_sync.research_evidence_persistence import (
    EvidencePersistenceResult,
    EvidencePersistenceStatus,
    ResearchEvidencePersistenceAdapter,
    ResearchEvidencePersistenceClient,
)
from chitu_connector.espocrm_sync.enrichment_gate import (
    DeterministicEnrichmentGate,
    EnrichmentGate,
    QualificationDecision,
    QualificationStatus,
)
from chitu_connector.espocrm_sync.score_input_adapter import (
    DeterministicScoreInputAdapter,
    ScoreInput,
    ScoreInputAdapter,
)
from chitu_connector.espocrm_sync.canonical_score_integration import (
    CanonicalScoreDecision,
    CanonicalScoreExecutor,
    CanonicalScoreIntegration,
    CanonicalScoreTrace,
)
from chitu_connector.espocrm_sync.crm_score_projection import (
    CRMScoreProjectionAdapter,
    LeadScoreProjectionClient,
    ScoreProjectionResult,
    ScoreProjectionStatus,
)
from chitu_connector.espocrm_sync.outreach_input_adapter import (
    CompanyContext,
    DeterministicOutreachInputAdapter,
    EvidenceBackedTalkingPoint,
    OutreachInput,
    OutreachInputAdapter,
)
from chitu_connector.espocrm_sync.email_draft_generation import (
    DeterministicEmailDraftGenerator,
    DraftEvidenceReference,
    EmailDraft,
    EmailDraftGenerator,
    PersonalizationReference,
)
from chitu_connector.espocrm_sync.campaign_projection import (
    CampaignProjectionAdapter,
    CampaignProjectionResult,
    CampaignProjectionStatus,
    LeadCampaignProjectionClient,
)
from chitu_connector.espocrm_sync.send_idempotency import (
    InMemorySendIdempotencyRegistry,
    SendAttempt,
    SendAttemptState,
    SendIdempotencyRegistry,
    SendRequest,
    SendReservation,
    SendReservationStatus,
    generate_send_idempotency_key,
    validate_send_request,
)
from chitu_connector.espocrm_sync.human_approval import (
    APPROVAL_VERSION,
    ApprovalAuditTrace,
    ApprovalStatus,
    DraftApproval,
    HumanApprovalRegistry,
    InMemoryHumanApprovalRegistry,
)
from chitu_connector.espocrm_sync.send_provider import (
    ProviderResultStatus,
    SendProvider,
    SendProviderAdapter,
    SendProviderAttemptResult,
    SendProviderResult,
    SendProviderUnavailableError,
    validate_provider_result,
)
from chitu_connector.espocrm_sync.send_execution import (
    ControlledSendExecutionService,
    InMemorySendExecutionRegistry,
    SendExecution,
    SendExecutionAuditTrace,
    SendExecutionOutcome,
    SendExecutionRegistry,
    SendExecutionState,
)
from chitu_connector.espocrm_sync.reply_tracking import (
    REPLY_EVENT_VERSION,
    InMemoryReplyEventRegistry,
    ReplyEvent,
    ReplyEventRegistry,
    ReplyEventReservation,
    ReplyEventReservationStatus,
    ReplyStatus,
    ReplyTrackingService,
    generate_reply_event_id,
    validate_reply_event,
)

__all__ = [
    "AdapterResult", "AuditStatus", "EspoCRMSyncAdapter", "EspoCRMSyncMapper", "GateDecision",
    "MockEspoCRMClient", "MockSyncStatus", "SyncAuditLog", "SyncContractPayload", "SyncSource",
    "LocalEspoCRMClient", "RealSyncStatus", "evaluate_sync_gate", "validate_sync_contract",
    "LifecycleAction", "LifecycleConflictError", "LifecycleSyncResult", "LifecycleSyncService",
    "LifecycleRuntimeResult", "run_local_synthetic_lifecycle_sync",
    "EmailLifecycleStatus", "EmailLifecycleSyncResult", "EmailLifecycleSyncService", "EmailLifecycleUpdate",
    "EmailLifecycleRuntimeResult", "run_local_synthetic_email_lifecycle_sync",
    "ConnectorApiError", "ConnectorSyncResponse", "ProspectingConnectorClient",
    "FeedbackApiError", "FeedbackConnectorClient", "FeedbackSyncPayload", "FeedbackSyncResponse",
    "BrevoApiError", "BrevoConnectorClient", "BrevoEmailEventPayload", "BrevoEmailEventResponse",
    "FeedbackSignalExportClient", "FeedbackSignalExportError", "FeedbackSignalPayload",
    "EvidencePersistenceResult", "EvidencePersistenceStatus", "ResearchEvidencePersistenceAdapter",
    "ResearchEvidencePersistenceClient",
    "DeterministicEnrichmentGate", "EnrichmentGate", "QualificationDecision", "QualificationStatus",
    "DeterministicScoreInputAdapter", "ScoreInput", "ScoreInputAdapter",
    "CanonicalScoreDecision", "CanonicalScoreExecutor", "CanonicalScoreIntegration", "CanonicalScoreTrace",
    "CRMScoreProjectionAdapter", "LeadScoreProjectionClient", "ScoreProjectionResult", "ScoreProjectionStatus",
    "CompanyContext", "DeterministicOutreachInputAdapter", "EvidenceBackedTalkingPoint", "OutreachInput",
    "OutreachInputAdapter",
    "DeterministicEmailDraftGenerator", "DraftEvidenceReference", "EmailDraft", "EmailDraftGenerator",
    "PersonalizationReference",
    "CampaignProjectionAdapter", "CampaignProjectionResult", "CampaignProjectionStatus",
    "LeadCampaignProjectionClient",
    "InMemorySendIdempotencyRegistry", "SendAttempt", "SendAttemptState", "SendIdempotencyRegistry",
    "SendRequest", "SendReservation", "SendReservationStatus", "generate_send_idempotency_key",
    "validate_send_request",
    "APPROVAL_VERSION", "ApprovalAuditTrace", "ApprovalStatus", "DraftApproval", "HumanApprovalRegistry",
    "InMemoryHumanApprovalRegistry",
    "ProviderResultStatus", "SendProvider", "SendProviderAdapter", "SendProviderAttemptResult",
    "SendProviderResult", "SendProviderUnavailableError", "validate_provider_result",
    "ControlledSendExecutionService", "InMemorySendExecutionRegistry", "SendExecution",
    "SendExecutionAuditTrace", "SendExecutionOutcome", "SendExecutionRegistry", "SendExecutionState",
    "REPLY_EVENT_VERSION", "InMemoryReplyEventRegistry", "ReplyEvent", "ReplyEventRegistry",
    "ReplyEventReservation", "ReplyEventReservationStatus", "ReplyStatus", "ReplyTrackingService",
    "generate_reply_event_id", "validate_reply_event",
]
