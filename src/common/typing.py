from typing import Protocol, Dict, Any


class NamedTupleProtocol(Protocol):
    @staticmethod
    def _asdict() -> Dict[Any, Any]:
        ...
