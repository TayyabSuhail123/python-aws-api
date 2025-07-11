from enum import Enum
from uuid import UUID
from pydantic import BaseModel

class AgentType(str, Enum):
    document_extractor = "document-extractor"
    policy_checker     = "policy-checker"


class RunState(str, Enum):
    pending = "PENDING"
    running = "RUNNING"
    done    = "DONE"
    failed  = "FAILED"


class AgentRunRequest(BaseModel):
    agent_type: AgentType
    user_id:    UUID


class AgentStatusResponse(BaseModel):
    run_id: UUID
    state:  RunState
    result: str | None = None   # "approved"/"rejected" or None
    error:  str | None = None   # populated only on failures

