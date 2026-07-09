from app.config import get_settings
from app.services.nlp.base import ParsedSourcingRequest, SourcingParser
from app.services.nlp.heuristic_parser import HeuristicSourcingParser

_parser: SourcingParser | None = None


def get_sourcing_parser() -> SourcingParser:
    global _parser
    if _parser is not None:
        return _parser

    settings = get_settings()
    if settings.anthropic_api_key:
        from app.services.nlp.llm_parser import LLMSourcingParser

        try:
            _parser = LLMSourcingParser()
            return _parser
        except Exception:
            pass

    _parser = HeuristicSourcingParser()
    return _parser


__all__ = ["get_sourcing_parser", "SourcingParser", "ParsedSourcingRequest"]
