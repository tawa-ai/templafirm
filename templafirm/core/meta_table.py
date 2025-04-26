import dataclasses
from typing import Dict, List


@dataclasses.dataclass
class ResourceTemplate:
    """DC for resource to be templated."""

    name: str
    version: str
    template_file_path: str
    description: str = ""
    template_inputs: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ProviderMetaTable:
    """DC for entire resource provider."""

    name: str
    version: str
    template_mapping: Dict[str, ResourceTemplate]
    description: str = ""
