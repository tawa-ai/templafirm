import asyncio
import logging
import os
from collections.abc import KeysView
from dataclasses import dataclass
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from templafirm.core.provider import Provider
from templafirm.gke.gke_provider import GKEProvider


@dataclass
class ProviderAndEnvironment:
    """Dataclass containing provider, associated jinja env, and lock for provider access.

    Args:
        environment (Environment): Jinja2 environment for template generation.
        provider (Provider): Provider object for defining templates.
        provider_lock (asyncio.Lock): Lock for provider access across threads.

    Attributes:
        environment (Environment): Jinja2 environment for template generation.
        provider (Provider): Provider object for defining templates.
        provider_lock (asyncio.Lock): Lock for provider access across threads.
    """

    environment: Environment
    provider: Provider
    provider_lock: asyncio.Lock


@dataclass
class ProviderRegistry:
    """Provider register dataclass.

    Holds the providers that are available as well as some easy access and setter methods.

    Attributes:
        providers (Dict[str, ProviderAndEnvironment]): Mapping from provider names to objects registered into registry.

    Raises:
        KeyError: Raises if provider key doesn't exist in registry.
    """

    providers: Dict[str, ProviderAndEnvironment]

    def keys(self) -> KeysView:
        """Get keys of providers available.

        Returns:
            KeysView[str]: Key view of available providers.
        """
        return self.providers.keys()

    def __getitem__(self, provider_key: str) -> ProviderAndEnvironment:
        """Get provider by key.

        Args:
            provider_key (str): Key of provider.

        Raises:
            KeyError: Raises if provider key is not registered.

        Returns:
            ProviderAndEnvironment: ProviderAndEnvironment obj corresponding to provider and associated jinja env.
        """
        if provider_key not in self.providers:
            raise KeyError(f"{provider_key} not a registered provider.")

        return self.providers[provider_key]

    def __setitem__(self, provider_key: str, provider_and_env: ProviderAndEnvironment) -> None:
        """Set provider in registry by key

        Args:
            provider_key (str): Key of provider.
            provider_and_env (ProviderAndEnvironment): ProviderAndEnvironment obj corresponding to provider and associated jinja env.
        """
        self.providers[provider_key] = provider_and_env

    def __contains__(self, provider_name: str) -> bool:
        """Determine if provider is registry.

        Args:
            provider_name (str): Key of provider in registry.

        Returns:
            bool: Whether provider exists in registry.
        """
        return provider_name in self.providers


class Templater:
    """Renders files from templates provider by registered providers.

    Supports adding new providers to the class level registry at runtime for custom
    provider support.

    Args:
        provider_lock_timeout (int, optional): Seconds to timeout on provider lock. Defaults to 5.

    Attributes:
        gke_provider (GKEProvider): Provider object for gke resources.
        _provider_lock_timeout (int): Time in seconds before provider lock timesout.
        _provider_registry (ProviderRegistry): Registry of providers available to all class instances.

    Raises:
        asyncio.TimeoutError: Raises if provider lock times out across instances. Done to ensure
            locking across all async Jinja envs.
        KeyError: Raises if user attempts access to un-registered provider or template.
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

    def __init__(self, provider_lock_timeout: int = 5):
        self._active_provider = self._provider_registry["gke"]
        self._provider_lock_timeout = provider_lock_timeout

    @classmethod
    def register_provider(cls, provider_key: str, provider_object: Provider) -> None:
        """Register provider to class registry.

        Args:
            provider_key (str): Key of provider to register.
            provider_object (Provider): Provider object to register.
        """
        if provider_key in cls._provider_registry:
            logging.warning(f"Overwriting previous registration of provider {provider_key}.")
        cls._provider_registry[provider_key] = ProviderAndEnvironment(
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
        return cls._provider_registry[provider_key]

    @classmethod
    def list_providers(cls) -> KeysView:
        """List registered providers

        Returns:
            KeysView[str]: dict keys of the registered providers.
        """
        return cls._provider_registry.keys()

    @classmethod
    def list_templates(cls, provider_name: str) -> KeysView:
        """List available templates for chosen provider.

        Args:
            provider_name (str): Name of provider to list templates.

        Returns:
            KeysView[str]: Key view of registered templates in chosen provider.
        """
        return cls._provider_registry[provider_name].provider._provider_meta_table.template_mapping.keys()

    def __verify_output_file_type(self, output_path: str, template_resource_name: str) -> bool:
        """Verify output path has expected file type.

        Args:
            output_path (str): desired output path for template resource.
            template_resource_name (str): name of the resource to template generate.

        Returns:
            bool: whether the file type is of the right type.
        """
        extension = os.path.splitext(output_path)[1]
        # don't need to lock as only doing look up and not using attached environment
        expected_extension = self._active_provider.provider[template_resource_name].file_extension
        if expected_extension != extension:
            logging.error(
                "Didn't generate template, provided path does not have expected file type.\nExpected {self._active_provider[template_resource_name].file_extension}."
            )
        return expected_extension == extension

    def activate_provider(self, provider_name: str) -> None:
        """Set the active provider.

        Args:
            provider_name str: Name of the provider to set to active state.
        """
        self._active_provider = self._provider_registry[provider_name]

    async def acquire_provider_lock(self) -> asyncio.Lock:
        """Acquire the provider lock.

        Raises:
            asyncio.TimeoutError: Raises if provider locking times out.

        Returns:
            asyncio.Lock: Async lock object to return.
        """
        provider_lock = self._active_provider.provider_lock
        try:
            await asyncio.wait_for(provider_lock.acquire(), self._provider_lock_timeout)
            logging.debug("Provider lock acquired, templating.")
            return provider_lock
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Timeout acquiring provider lock in {self._provider_lock_timeout} seconds.")

    async def render_template_resource(
        self, template_resource_inputs: Dict[str, Any], template_resource_name: str
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

    async def render_template_resource_to_file(
        self, output_path: str, template_resource_inputs: Dict[str, Any], template_resource_name: str
    ) -> None:
        """Render template and save it to a desired output file.

        Args:
            output_path (str): path to save templated resource.
            template_resource_inputs (Dict[str, Any]): inputs to render template file.
            template_resource_name (str): Name of the resource to template.
        """
        rendered_template_str = await self.render_template_resource(
            template_resource_inputs=template_resource_inputs, template_resource_name=template_resource_name
        )

        if rendered_template_str is not None:
            # verify output file type
            if self.__verify_output_file_type(output_path=output_path, template_resource_name=template_resource_name):
                if os.path.exists(output_path):
                    logging.warning(f"{output_path} exists, overwriting with new templated resource.")
                with open(output_path, "w+") as open_template_file:
                    open_template_file.writelines(rendered_template_str)
        else:
            logging.error("Template failed to render, check logs.")
