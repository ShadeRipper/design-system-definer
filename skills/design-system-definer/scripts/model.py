"""Token model shared by the generators and exporters."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Alias:
    target: str  # variable path, e.g. color/neutral-cool/900
    collection: str  # collection that owns the target


@dataclass
class Variable:
    path: str  # lowercase slash path
    type: str  # color | number | string | boolean | easing
    values: dict  # mode name -> literal or Alias
    scopes: list = field(default_factory=list)
    description: str = ""


@dataclass
class Collection:
    name: str
    modes: list
    variables: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def get(self, path):
        for v in self.variables:
            if v.path == path:
                return v
        raise KeyError(f"{path} not in collection {self.name}")

    def paths(self):
        return [v.path for v in self.variables]


FIGMA_TYPES = {"color": "COLOR", "number": "FLOAT", "string": "STRING",
               "boolean": "BOOLEAN", "easing": "EASING"}
