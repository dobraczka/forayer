from typing import Any, Dict


class KG:
    def __init__(self, entities: Dict[Any, Dict[Any, Any]], rel: Dict[Any, Any]):
        self.entities = entities
        self.rel = rel
