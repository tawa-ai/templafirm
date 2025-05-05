import os
import pathlib

from templafirm.core.provider import Provider
from templafirm.gke import templates


class GKEProvider(Provider):
    """Template provider for GKE. Abstraction on top of file path provided in package.

    Attributes:
        _localized_assets_pathway (str): pathway in fs to the templates directory that is packaged
            with templafirm.
    """

    def __init__(self) -> None:
        self._localized_assets_pathway = self._get_localized_assets_path()
        super().__init__(self._localized_assets_pathway)

    def template_directory_path(self) -> str:
        """Return the template directory relative to python env.

        Returns:
            str: pathway to the template directory.
        """
        template_module_file_path = pathlib.Path(os.path.abspath(templates.__file__))
        return str(template_module_file_path.parent)

    def _get_localized_assets_path(self) -> str:
        """Get the localized assets path.

        Returns:
            str: pathway to local resource definitions.
        """
        gke_provider_meta_path = os.path.join(self.template_directory_path(), "gke_provider_meta.yaml")
        return gke_provider_meta_path
