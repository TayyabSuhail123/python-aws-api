import asyncio, random
import structlog
from .base import BaseAgent

class PolicyChecker(BaseAgent):
    async def run(self) -> str:
        log = structlog.get_logger().bind(agent="policy-checker",
                                          user=str(self.user_id))
        log.info("start", msg="Hello, I am a policy-checker agent")
        await asyncio.sleep(5)
        decision = random.choice(["approved", "rejected"])
        log.info("complete", decision=decision)
        return decision
