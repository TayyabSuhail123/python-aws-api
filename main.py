from fastapi import FastAPI, HTTPException
from uuid import uuid4, UUID
import asyncio, structlog

from core.logger import configure_logging
from core.lock   import agent_lock
from core.models import AgentRunRequest, AgentStatusResponse, RunState, AgentType
from agents.document_extractor import DocumentExtractor
from agents.policy_checker    import PolicyChecker


configure_logging()
app = FastAPI(title="Agent Runner")
runs: dict[UUID, AgentStatusResponse] = {}

@app.post("/agents/run", status_code=202)
async def run_agent(request: AgentRunRequest):
    log = structlog.get_logger().bind(agent_type=request.agent_type,
                                      user=str(request.user_id))

    if agent_lock.locked():
        log.warning("rejected", reason="agent already running")
        raise HTTPException(status_code=409,
                            detail="Another agent is already running")

    run_id = uuid4()
    runs[run_id] = AgentStatusResponse(run_id=run_id,
                                       state=RunState.pending)

    asyncio.create_task(_execute_agent(run_id, request))

    return {"run_id": run_id}




async def _execute_agent(run_id: UUID, req: AgentRunRequest) -> None:
    log = structlog.get_logger().bind(run_id=str(run_id),
                                      agent_type=req.agent_type,
                                      user=str(req.user_id))

    async with agent_lock:  
        runs[run_id].state = RunState.running
        try:
            # Pick the right concrete agent
            if req.agent_type is AgentType.document_extractor:
                agent = DocumentExtractor(req.user_id)
            elif req.agent_type is AgentType.policy_checker:
                agent = PolicyChecker(req.user_id)
            else:  # should be impossible due to validation
                raise ValueError(f"Unknown agent_type {req.agent_type}")

            result = await agent.run()
            runs[run_id].state  = RunState.done
            runs[run_id].result = result

        except Exception as exc:
            # Catch any crash, log it, mark failed
            log.error("agent_failed", err=str(exc))
            runs[run_id].state = RunState.failed
            runs[run_id].error = str(exc)


@app.get("/agents/status/{run_id}", response_model=AgentStatusResponse)
async def get_status(run_id: UUID):
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return runs[run_id]
