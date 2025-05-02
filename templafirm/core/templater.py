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
    environment: Environment
    provider: Provider
    provider_lock: asyncio.Lock


@dataclass
class ProviderRegistry:
    providers: Dict[str, ProviderAndEnvironment]

    def keys(self) -> KeysView[str]:
        return self.providers.keys()

    def __getitem__(self, provider_key: str) -> ProviderAndEnvironment:
        if provider_key not in self.providers:
            raise KeyError(f"{provider_key} not a registered provider.")

        return self.providers[provider_key]

    def __setitem__(self, provider_key: str, provider_and_env: ProviderAndEnvironment) -> None:
        self.providers[provider_key] = provider_and_env

    def __contains__(self, provider_name: str) -> bool:
        return provider_name in self.providers


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

    def __init__(self, provider_lock_timeout: int = 5):
        """Init Templater class instance.

        Args:
        """
        self._active_provider = self._provider_registry["gke"]
        self._provider_lock_timeout = provider_lock_timeout

    @classmethod
    def register_provider(cls, provider_key: str, provider_object: Provider) -> None:
        """Register provider into templater class attr.

        Args:
            provider_key (str): Lookup key for provider.
            provider_object (Any): Abstracted provider object with common interface.
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
    def list_providers(cls) -> KeysView[str]:
        """List registered providers

        Returns:
            KeysView[str]: dict keys of the registered providers.
        """
        return cls._provider_registry.keys()

    @classmethod
    def list_templates(cls, provider_name: str) -> KeysView[str]:
        """List templates for particular provider

        Returns:
            KeysView[str]: dict keys of registered templates.
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
