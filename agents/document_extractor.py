import asyncio
import structlog
from .base import BaseAgent
from config import settings

class DocumentExtractor(BaseAgent):
    async def run(self) -> None:
        log = structlog.get_logger().bind(agent="document-extractor",
                                          user=str(self.user_id))
        log.info("start", msg="Hello, I am a document-extractor agent")
        log.debug("System", msg="Test of Debug logs")
        await asyncio.sleep(settings.agent_timeout)     
        log.info("complete")
        return None
