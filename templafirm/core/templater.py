import logging
from collections.abc import KeysView
from dataclasses import dataclass
from typing import Dict

from jinja2 import Environment, FileSystemLoader

from templafirm.core.provider import Provider
from templafirm.eai.eai_provider import EAIProvider


@dataclass
class ProviderAndEnvironment:
    provider: Provider
    environment: Environment


@dataclass
class ProviderRegistry:
    providers: Dict[str, ProviderAndEnvironment]


class Templater:
    """
    Head class holding the regsitered providers and operating the template engine
    based off the provided template and args given by provider.
    """

    eai_provider = EAIProvider()
    _provider_registry: ProviderRegistry = ProviderRegistry(
        providers={
            "eai": ProviderAndEnvironment(
                provider=eai_provider,
                environment=Environment(loader=FileSystemLoader(searchpath=eai_provider.template_directory_path())),
            )
        }
    )

    def __init__(self, template_directory: str = "."):
        """Init Templater class instance.

        Args:
            template_directory (str, default = '.'). Directory to drop completed
                templates, defaults to current working directory.
        """
        self._template_directory = template_directory

    @classmethod
    def register_provider(cls, provider_key: str, provider_object: Provider) -> None:
        """Register provider into templater class attr.

        Args:
            provider_key (str): Lookup key for provider.
            provider_object (Any): Abstracted provider object with common interface.
        """
        if provider_key in cls._provider_registry.providers:
            logging.warning(f"Overwriting previous registration of provider {provider_key}.")
        cls._provider_registry.providers[provider_key] = ProviderAndEnvironment(
            provider=provider_object,
            environment=Environment(loader=FileSystemLoader(searchpath=provider_object.template_directory_path())),
        )

    @classmethod
    def list_providers(cls) -> KeysView[str]:
        """List registered providers

        Returns:
            KeysView[str]: dict keys of the registered providers.
        """
        return cls._provider_registry.providers.keys()
