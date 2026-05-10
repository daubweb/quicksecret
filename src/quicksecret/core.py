import logging
import os
from typing import Dict, Optional, Any

from infisical_client import (
    ClientSettings,
    GetSecretOptions,
    InfisicalClient,
    ListSecretsOptions,
)

logger = logging.getLogger(__name__)


class QuickSecret:
    """
    A minimal tool to fetch secrets from Infisical using machine identity.

    Attributes:
        client (InfisicalClient): The Infisical client instance.
        project_id (str, optional): The default Infisical project ID.
        environment (str): The default environment to fetch secrets from.
        cache (Dict[str, Any]): A simple internal cache for secrets.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        environment: Optional[str] = None,
        site_url: Optional[str] = None,
        use_cache: bool = False,
    ):
        """
        Initialize the QuickSecret client.

        Args:
            project_id: The Infisical project ID. Defaults to INFISICAL_PROJECT_ID env var.
            environment: The environment to fetch secrets from. Defaults to INFISICAL_ENVIRONMENT or "dev".
            site_url: The Infisical site URL. Defaults to INFISICAL_SITE_URL or "https://app.infisical.com".
            use_cache: Whether to use an internal cache for secrets. Defaults to False.

        Raises:
            ValueError: If INFISICAL_MACHINE_ID or INFISICAL_MACHINE_SECRET is not set.
        """
        client_id = os.getenv("INFISICAL_MACHINE_ID")
        client_secret = os.getenv("INFISICAL_MACHINE_SECRET")

        if not client_id or not client_secret:
            logger.error("Authentication environment variables are missing.")
            raise ValueError(
                "Environment variables INFISICAL_MACHINE_ID and INFISICAL_MACHINE_SECRET must be set for authentication."
            )

        self.project_id = project_id or os.getenv("INFISICAL_PROJECT_ID")
        self.environment = environment or os.getenv("INFISICAL_ENVIRONMENT") or "dev"
        actual_site_url = (
            site_url or os.getenv("INFISICAL_SITE_URL") or "https://app.infisical.com"
        )
        self.use_cache = use_cache
        self._cache: Dict[str, Any] = {}

        logger.debug(f"Initializing QuickSecret with site_url: {actual_site_url}")

        settings = ClientSettings(
            client_id=client_id, client_secret=client_secret, site_url=actual_site_url
        )
        self.client = InfisicalClient(settings)

        # Security: Clean up sensitive local variables
        del client_id
        del client_secret

    def get_secret(
        self,
        secret_key: str,
        environment: Optional[str] = None,
        path: str = "/",
        project_id: Optional[str] = None,
        use_cache: Optional[bool] = None,
    ) -> str:
        """
        Fetch a single secret value from Infisical.

        Args:
            secret_key: The key of the secret to fetch.
            environment: Optional override for the environment.
            path: The path of the secret (defaults to "/").
            project_id: Optional override for the project ID.
            use_cache: Optional override for cache usage.

        Returns:
            The secret value as a string.

        Raises:
            ValueError: If no project_id is available or if secret_key is empty.
            Exception: If fetching the secret fails.
        """
        if not secret_key:
            raise ValueError("Secret key cannot be empty.")

        env = environment or self.environment
        pid = project_id or self.project_id
        should_cache = use_cache if use_cache is not None else self.use_cache

        if not pid:
            logger.error("Project ID is missing.")
            raise ValueError(
                "Project ID must be provided during initialization or as a method argument."
            )

        cache_key = f"{pid}:{env}:{path}:{secret_key}"
        if should_cache and cache_key in self._cache:
            logger.debug(f"Cache hit for secret: {secret_key}")
            return self._cache[cache_key]

        logger.info(f"Fetching secret: {secret_key} from {env}:{path}")
        try:
            secret = self.client.getSecret(
                options=GetSecretOptions(
                    secret_name=secret_key, project_id=pid, environment=env, path=path
                )
            )
            if secret is None:
                raise ValueError(f"Secret '{secret_key}' not found in {env}:{path}")
            value = secret.secret_value
            if should_cache:
                self._cache[cache_key] = value
            return value
        except Exception as e:
            logger.error(f"Failed to fetch secret '{secret_key}': {e}")
            raise

    def list_secrets(
        self,
        environment: Optional[str] = None,
        path: str = "/",
        project_id: Optional[str] = None,
        use_cache: Optional[bool] = None,
    ) -> Dict[str, str]:
        """
        List all secrets in a given path and environment.

        Args:
            environment: Optional override for the environment.
            path: The path of the secrets (defaults to "/").
            project_id: Optional override for the project ID.
            use_cache: Optional override for cache usage.

        Returns:
            A dictionary mapping secret keys to their values.

        Raises:
            ValueError: If no project_id is available.
            Exception: If listing secrets fails.
        """
        env = environment or self.environment
        pid = project_id or self.project_id
        should_cache = use_cache if use_cache is not None else self.use_cache

        if not pid:
            logger.error("Project ID is missing.")
            raise ValueError(
                "Project ID must be provided during initialization or as a method argument."
            )

        cache_key = f"{pid}:{env}:{path}:__all__"
        if should_cache and cache_key in self._cache:
            logger.debug(f"Cache hit for list_secrets in {path}")
            return self._cache[cache_key]

        logger.info(f"Listing secrets from {env}:{path}")
        try:
            secrets = self.client.listSecrets(
                options=ListSecretsOptions(project_id=pid, environment=env, path=path)
            )

            if secrets is None:
                secrets = []

            result = {s.secret_name: s.secret_value for s in secrets}
            if should_cache:
                self._cache[cache_key] = result
                # Also cache individual secrets
                for key, value in result.items():
                    self._cache[f"{pid}:{env}:{path}:{key}"] = value
            return result
        except Exception as e:
            logger.error(f"Failed to list secrets in '{path}': {e}")
            raise

    def clear_cache(self) -> None:
        """Clear the internal secret cache."""
        self._cache.clear()
        logger.debug("Cache cleared.")

    def inject_to_env(
        self,
        secret_key: str,
        environment: Optional[str] = None,
        path: str = "/",
        project_id: Optional[str] = None,
    ) -> str:
        """
        Fetch a secret and inject it into the current process's environment variables.

        Args:
            secret_key: The key of the secret to fetch and inject.
            environment: Optional override for the environment.
            path: The path of the secret.
            project_id: Optional override for the project ID.

        Returns:
            The secret value.
        """
        value = self.get_secret(secret_key, environment, path, project_id)
        os.environ[secret_key] = value
        return value

    def inject_all_to_env(
        self,
        environment: Optional[str] = None,
        path: str = "/",
        project_id: Optional[str] = None,
    ) -> None:
        """
        Fetch all secrets in a path and inject them into the current process's environment variables.

        Args:
            environment: Optional override for the environment.
            path: The path of the secrets.
            project_id: Optional override for the project ID.
        """
        secrets = self.list_secrets(environment, path, project_id)
        for key, value in secrets.items():
            os.environ[key] = value
