import os
import pathlib

from templafirm.core.provider import Provider
from templafirm.eai import templates


class EAIProvider(Provider):
    def __init__(self) -> None:
        self._localized_assets_pathway = self._get_localized_assets_path()
        super().__init__(self._localized_assets_pathway)

    def template_directory_path(self) -> str:
        template_module_file_path = pathlib.Path(os.path.abspath(templates.__file__))
        return str(template_module_file_path.parent)

    def _get_localized_assets_path(self) -> str:
        eai_provider_meta_path = os.path.join(self.template_directory_path(), "eai_provider_meta.yaml")
        return eai_provider_meta_path
