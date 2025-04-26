from abc import ABC, abstractmethod
from collections.abc import KeysView

import yaml

from templafirm.core.meta_table import ProviderMetaTable, ResourceTemplate


class Provider(ABC):
    """Base class struct for providing template structs to Jinja engine."""

    def __init__(self, provider_meta_path: str):
        self._provider_meta_path = provider_meta_path
        self._provider_meta_table = self._load_meta_table()

    @abstractmethod
    def template_directory_path(self) -> str:
        raise NotImplementedError(
            "Need to implement method to locate your template directory on fs. Done for Jinja2 FileSystemLoader."
        )

    def _load_meta_table(self) -> ProviderMetaTable:
        """Load meta provider definition table to memory."""
        with open(self._provider_meta_path, "r") as open_provider_meta_buffer:
            provider_yaml_obj = yaml.safe_load(open_provider_meta_buffer)
            provider_meta_table = ProviderMetaTable(**provider_yaml_obj)
            # need to parse the resources individually as dataclass constructor doesn't form in sub class objects
            # these are silently type failed as they come across as dicts.
            resource_yaml_defs = provider_meta_table.template_mapping
            resource_obj_defs = {}
            for resource_name, resource_yaml_def in resource_yaml_defs.items():
                # type ignore on this because mypy thinks the type is ResourceTemplate but it gets loaded as dict
                resource_obj_defs[resource_name] = ResourceTemplate(**resource_yaml_def)  # type: ignore

            provider_meta_table.template_mapping = resource_obj_defs
        return provider_meta_table

    @property
    def name(self) -> str:
        return self._provider_meta_table.name

    @property
    def version(self) -> str:
        return self._provider_meta_table.version

    @property
    def resources(self) -> KeysView[str]:
        return self._provider_meta_table.template_mapping.keys()

    def __getitem__(self, resource_name: str) -> ResourceTemplate:
        if resource_name not in self._provider_meta_table.template_mapping:
            raise KeyError(f"{resource_name} does not exist in {self.__class__.__name__}.")

        return self._provider_meta_table.template_mapping[resource_name]
