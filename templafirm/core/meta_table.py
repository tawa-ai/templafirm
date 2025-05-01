import dataclasses
from typing import Dict, Set


@dataclasses.dataclass
class ResourceTemplate:
    """DC for resource to be templated."""

    name: str
    version: str
    template_file_path: str
    description: str = ""
    file_extension: str = ".tf"
    template_inputs: Set[str] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class ProviderMetaTable:
    """DC for entire resource provider."""

    name: str
    version: str
    template_mapping: Dict[str, ResourceTemplate]
    description: str = ""

    def __contains__(self, resource_name: str) -> bool:
        return resource_name in self.template_mapping

    def __getitem__(self, resource_key: str) -> ResourceTemplate:
        if resource_key not in self.template_mapping:
            raise KeyError(f"{resource_key} not registered in provider.")

        return self.template_mapping[resource_key]
