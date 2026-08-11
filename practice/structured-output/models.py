from enum import Enum
from typing import List
from pydantic import BaseModel, ConfigDict

class Category(str, Enum):
    urgent = "urgent"
    billing = "billing"
    technical = "technical"
    general = "general"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class EntityType(str, Enum):
    person = "person"
    product = "product"
    date = "date"
    organization = "organization"

class Entity(BaseModel):
    
    model_config = ConfigDict(extra="forbid")
    entity: str
    type: EntityType

class TicketTriage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    priority: Priority
    sentiment: Sentiment
    key_entities: List[Entity]
    requires_immediate_attention: bool




