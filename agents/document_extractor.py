import asyncio
import structlog
from .base import BaseAgent

class DocumentExtractor(BaseAgent):
    async def run(self) -> None:
        log = structlog.get_logger().bind(agent="document-extractor",
                                          user=str(self.user_id))
        log.info("start", msg="Hello, I am a document-extractor agent")
        await asyncio.sleep(5)          
        log.info("complete")
        return None
