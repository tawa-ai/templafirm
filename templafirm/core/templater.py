import asyncio
import logging
from collections.abc import KeysView
from dataclasses import dataclass
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from templafirm.core.provider import Provider
from templafirm.gke.gke_provider import GKEProvider


@dataclass
class ProviderAndEnvironment:
    environment: Environment
    provider: Provider
    provider_lock: asyncio.Lock


@dataclass
class ProviderRegistry:
    providers: Dict[str, ProviderAndEnvironment]


class Templater:
    """
    Head class holding the regsitered providers and operating the template engine
    based off the provided template and args given by provider.
    """

    gke_provider = GKEProvider()
    _provider_registry: ProviderRegistry = ProviderRegistry(
        providers={
            "gke": ProviderAndEnvironment(
                provider=gke_provider,
                provider_lock=asyncio.Lock(),
                environment=Environment(
                    loader=FileSystemLoader(searchpath=gke_provider.template_directory_path()), enable_async=True
                ),
            )
        }
    )

    def __init__(self, template_directory: str = ".", provider_lock_timeout: int = 5):
        """Init Templater class instance.

        Args:
            template_directory (str, default = '.'). Directory to drop completed
                templates, defaults to current working directory.
        """
        self._template_directory = template_directory
        self._active_provider = self._provider_registry.providers["gke"]
        self._provider_lock_timeout = provider_lock_timeout

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
            provider_lock=asyncio.Lock(),
            environment=Environment(
                loader=FileSystemLoader(searchpath=provider_object.template_directory_path()), enable_async=True
            ),
        )

    @classmethod
    def return_provider(cls, provider_key: str) -> ProviderAndEnvironment:
        """Return the ProviderAndEnvironment dc if available.

        Args:
            provider_key (str): The key of the provider to return.

        Returns:
            ProviderAndEnvironment: Provider and environment dataclass.
        """
        if provider_key in cls._provider_registry.providers:
            return cls._provider_registry.providers[provider_key]
        else:
            raise KeyError(f"{provider_key} not registered as a provider.")

    @classmethod
    def list_providers(cls) -> KeysView[str]:
        """List registered providers

        Returns:
            KeysView[str]: dict keys of the registered providers.
        """
        return cls._provider_registry.providers.keys()

    @classmethod
    def list_templates(cls, provider_name: str) -> KeysView[str]:
        """List templates for particular provider

        Returns:
            KeysView[str]: dict keys of registered templates.
        """
        return cls._provider_registry.providers[provider_name].provider._provider_meta_table.template_mapping.keys()

    def activate_provider(self, provider_name: str) -> None:
        """Set the active provider.

        Args:
            provider_name str: Name of the provider to set to active state.
        """
        if provider_name in self.list_providers():
            self._active_provider = self._provider_registry.providers[provider_name]
        else:
            raise KeyError(f"{provider_name} not a registered provider.")

    async def acquire_provider_lock(self) -> asyncio.Lock:
        """Acquire the provider lock.

        Raises:
            asyncio.TimeoutError: Timeout error when the provider lock can't be
                acquired.
        """
        provider_lock = self._active_provider.provider_lock
        try:
            await asyncio.wait_for(provider_lock.acquire(), self._provider_lock_timeout)
            logging.debug("Provider lock acquired, templating.")
            return provider_lock
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Timeout acquiring provider lock in {self._provider_lock_timeout} seconds.")

    async def render_template_resource(
        self, template_resource_name: str, template_resource_inputs: Dict[str, Any]
    ) -> Optional[str]:
        """Render template resource async.

        Args:
            template_resource_name (str): Name of the resource to render, must be registered with active provider.
            template_resource_inputs (Dict[str, Any]): Inputs to template.

        Returns:
            str: templated resource in the form of a string
        """
        active_provider_obj = self._active_provider.provider
        if template_resource_name not in active_provider_obj:
            raise KeyError(f"{template_resource_name} not registered in {active_provider_obj.name} provider.")

        provider_lock = await self.acquire_provider_lock()
        template_render = None
        try:
            resource_obj = active_provider_obj[template_resource_name]
            template = self._active_provider.environment.get_template(resource_obj.template_file_path)
            template_render = await template.render_async(**template_resource_inputs)
        except Exception as e:
            logging.error(f"Error generating template: {e}")
        finally:
            if provider_lock.locked():
                provider_lock.release()
                logging.debug(f"Released {self._active_provider.provider.name} provider lock.")
        return template_render
