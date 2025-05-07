import os
from abc import ABC, abstractmethod
from collections.abc import KeysView

import yaml

from templafirm.core.meta_table import ProviderMetaTable, ResourceTemplate


class Provider(ABC):
    """Base class struct for providing template structs to Jinja engine.


    Args:
        provider_meta_path (str): Path to the meta data table.

    Attributes:
        _provider_meta_path (str): Path to the meta data table.
        _provider_meta_table (ProviderMetaTable): Meta table object storing provider meta and resources.
    """

    def __init__(self, provider_meta_path: str):
        self._provider_meta_path = provider_meta_path
        self._provider_meta_table = self._load_meta_table()

    @abstractmethod
    def template_directory_path(self) -> str:
        """Get the defined path to the templates.

        Raises:
            NotImplementedError: When not implemented in subclass.

        Returns:
            str: The path on the system to the template directory.
        """
        raise NotImplementedError(
            "Need to implement method to locate your template directory on fs. Done for Jinja2 FileSystemLoader."
        )

    def __verify_meta_table(self, provider_meta_table: ProviderMetaTable) -> None:
        """Verify the template files that are present in the meta table."""
        for _, resource_template in provider_meta_table.template_mapping.items():
            resource_template_path = os.path.join(
                os.path.dirname(self._provider_meta_path), resource_template.template_file_path
            )
            assert os.path.exists(resource_template_path)

    def _load_meta_table(self) -> ProviderMetaTable:
        """Load the meta table.

        Returns:
            ProviderMetaTable: Meta table for the provider containing the provider data and template data.
        """
        with open(self._provider_meta_path, "r") as open_provider_meta_buffer:
            provider_yaml_obj = yaml.safe_load(open_provider_meta_buffer)
            provider_meta_table = ProviderMetaTable(**provider_yaml_obj)
            # need to parse the resources individually as dataclass constructor doesn't form in sub class objects
            # these are silently type failed as they come across as dicts.
            resource_yaml_defs = provider_meta_table.template_mapping
            resource_obj_defs = {}
            for resource_name, resource_yaml_def in resource_yaml_defs.items():
                # type ignore on this because mypy thinks the type is ResourceTemplate but it gets loaded as dict
                resource_template_obj = ResourceTemplate(**resource_yaml_def)  # type: ignore
                # have to do the same thing to the set of inputs
                resource_template_obj.template_inputs = (
                    set(resource_yaml_def["template_inputs"]) if "template_inputs" in resource_yaml_def else set()  # type: ignore
                )
                resource_obj_defs[resource_name] = resource_template_obj
            provider_meta_table.template_mapping = resource_obj_defs
        # verify all files in the table exist in the described directory
        self.__verify_meta_table(provider_meta_table)
        return provider_meta_table

    @property
    def name(self) -> str:
        """Get name of provider.

        Returns:
            str: Provider name.
        """
        return self._provider_meta_table.name

    @property
    def version(self) -> str:
        """Get version of provider.

        Returns:
            str: Provider version.
        """
        return self._provider_meta_table.version

    @property
    def resources(self) -> KeysView:
        """Get resource names as KeysView.

        Returns:
            KeysView[str]: Keys for provider defined resources.
        """
        return self._provider_meta_table.template_mapping.keys()

    def __contains__(self, resource_name: str) -> bool:
        return resource_name in self._provider_meta_table

    def __getitem__(self, resource_name: str) -> ResourceTemplate:
        if resource_name not in self._provider_meta_table.template_mapping:
            raise KeyError(f"{resource_name} does not exist in {self.__class__.__name__}.")

        return self._provider_meta_table[resource_name]
