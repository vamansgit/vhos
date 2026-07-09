from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedSourcingRequest:
    category: str  # product | packaging | logistics | other
    quantity: int | None
    target_price: float | None
    destination: str | None
    deadline_days: int | None
    spec_attributes: dict = field(default_factory=dict)
    confirmation_line: str = ""  # one-line "here's what I understood" (PRD §5.2A)


class SourcingParser(ABC):
    """Turns free-text sourcing asks into a structured request (PRD §5.2A —
    parsed, then confirmed back to the user in one line before searching)."""

    name: str

    @abstractmethod
    def parse(self, raw_text: str) -> ParsedSourcingRequest:
        raise NotImplementedError
