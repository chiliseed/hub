import json
from dataclasses import dataclass, asdict


@dataclass
class BaseConf:
    def to_dict(self):
        return asdict(self)

    def to_str(self):
        return json.dumps(asdict(self))
