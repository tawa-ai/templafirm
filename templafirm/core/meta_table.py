import dataclasses
from typing import Dict, Set


@dataclasses.dataclass
class ResourceTemplate:
    """DC for resource to be templated.

    Args:
        description (str, optional): Description of the resource, defaults to ''.
        file_extension (str, optional): Type of file, defaults to '.tf'.
        name (str): Name of the resource.
        version (str): Version of the resource.
        template_file_path (str): Path in the template directory to template file.
        template_inputs (Set[str]): Inputs into the templated resource, defaults to empty set.

    Attributes:
        description (str): Description of the resource, defaults to ''.
        file_extension (str): Type of file, defaults to '.tf'.
        name (str): Name of the resource.
        version (str): Version of the resource.
        template_file_path (str): Path in the template directory to template file.
        template_inputs (Set[str]): Inputs into the templated resource, defaults to empty set.

    """

    name: str
    version: str
    template_file_path: str
    description: str = ""
    file_extension: str = ".tf"
    template_inputs: Set[str] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class ProviderMetaTable:
    """DC for entire resource provider.

    Args:
        description (str, optional): Description of the provider, defaults to ''.
        name (str): Name of the provider.
        version (str): Version of the provider.
        template_mapping (Dict[str, ResourceTemplate]): Mapping of template name to definition.

    Attributes:
        description (str, optional): Description of the provider, defaults to ''.
        name (str): Name of the provider.
        version (str): Version of the provider.
        template_mapping (Dict[str, ResourceTemplate]): Mapping of template name to definition.
    """

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
