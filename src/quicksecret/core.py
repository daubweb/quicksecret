import os
from typing import Dict, List, Optional
from infisical_client import InfisicalClient, ClientSettings, GetSecretOptions, ListSecretsOptions

class QuickSecret:
    """
    A minimal tool to fetch secrets from Infisical using machine identity.
    
    Attributes:
        client (InfisicalClient): The Infisical client instance.
        project_id (str, optional): The default Infisical project ID.
        environment (str): The default environment to fetch secrets from.
    """
    
    def __init__(
        self, 
        project_id: Optional[str] = None, 
        environment: str = "dev", 
        site_url: str = "https://app.infisical.com"
    ):
        """
        Initialize the QuickSecret client.
        
        Args:
            project_id: The Infisical project ID (found in Infisical project settings).
            environment: The environment to fetch secrets from (e.g., "dev", "prod").
            site_url: The Infisical site URL. Defaults to the public Infisical cloud.
            
        Raises:
            ValueError: If INFISICAL_MACHINE_ID or INFISICAL_MACHINE_SECRET is not set.
        """
        client_id = os.getenv("INFISICAL_MACHINE_ID")
        client_secret = os.getenv("INFISICAL_MACHINE_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Environment variables INFISICAL_MACHINE_ID and INFISICAL_MACHINE_SECRET must be set for authentication."
            )
            
        self.project_id = project_id
        self.environment = environment
        
        settings = ClientSettings(
            client_id=client_id,
            client_secret=client_secret,
            site_url=site_url
        )
        self.client = InfisicalClient(settings)

    def get_secret(
        self, 
        secret_name: str, 
        environment: Optional[str] = None, 
        path: str = "/", 
        project_id: Optional[str] = None
    ) -> str:
        """
        Fetch a single secret value from Infisical.
        
        Args:
            secret_name: The name of the secret to fetch.
            environment: Optional override for the environment.
            path: The path of the secret (defaults to "/").
            project_id: Optional override for the project ID.
            
        Returns:
            The secret value as a string.
            
        Raises:
            ValueError: If no project_id is available.
        """
        env = environment or self.environment
        pid = project_id or self.project_id
        
        if not pid:
            raise ValueError("Project ID must be provided during initialization or as a method argument.")
            
        secret = self.client.getSecret(options=GetSecretOptions(
            secret_name=secret_name,
            project_id=pid,
            environment=env,
            path=path
        ))
        return secret.secret_value

    def list_secrets(
        self, 
        environment: Optional[str] = None, 
        path: str = "/", 
        project_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        List all secrets in a given path and environment.
        
        Args:
            environment: Optional override for the environment.
            path: The path of the secrets (defaults to "/").
            project_id: Optional override for the project ID.
            
        Returns:
            A dictionary mapping secret names to their values.
            
        Raises:
            ValueError: If no project_id is available.
        """
        env = environment or self.environment
        pid = project_id or self.project_id
        
        if not pid:
            raise ValueError("Project ID must be provided during initialization or as a method argument.")
            
        secrets = self.client.listSecrets(options=ListSecretsOptions(
            project_id=pid,
            environment=env,
            path=path
        ))
        
        return {s.secret_name: s.secret_value for s in secrets}

    def inject_to_env(
        self, 
        secret_name: str, 
        environment: Optional[str] = None, 
        path: str = "/", 
        project_id: Optional[str] = None
    ) -> str:
        """
        Fetch a secret and inject it into the current process's environment variables.
        
        Args:
            secret_name: The name of the secret to fetch and inject.
            environment: Optional override for the environment.
            path: The path of the secret.
            project_id: Optional override for the project ID.
            
        Returns:
            The secret value.
        """
        value = self.get_secret(secret_name, environment, path, project_id)
        os.environ[secret_name] = value
        return value

    def inject_all_to_env(
        self, 
        environment: Optional[str] = None, 
        path: str = "/", 
        project_id: Optional[str] = None
    ) -> None:
        """
        Fetch all secrets in a path and inject them into the current process's environment variables.
        
        Args:
            environment: Optional override for the environment.
            path: The path of the secrets.
            project_id: Optional override for the project ID.
        """
        secrets = self.list_secrets(environment, path, project_id)
        for name, value in secrets.items():
            os.environ[name] = value
