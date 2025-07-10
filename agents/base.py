from abc import ABC, abstractmethod
from uuid import UUID

class BaseAgent(ABC):
    
    def __init__(self, user_id: UUID):
        self.user_id = user_id   

    @abstractmethod
    async def run(self) -> str | None:
        ...
