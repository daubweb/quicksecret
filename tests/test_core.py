import pytest
import os
from unittest.mock import MagicMock, patch
from quicksecret import QuickSecret

@pytest.fixture
def env_vars():
    """Fixture to set up necessary environment variables."""
    with patch.dict(os.environ, {
        "INFISICAL_MACHINE_ID": "test-id",
        "INFISICAL_MACHINE_SECRET": "test-secret"
    }):
        yield

@pytest.fixture
def mock_client(mocker):
    """Fixture to mock the InfisicalClient."""
    return mocker.patch("quicksecret.core.InfisicalClient")

def test_init_missing_env_vars():
    """Test that ValueError is raised when environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="INFISICAL_MACHINE_ID and INFISICAL_MACHINE_SECRET must be set"):
            QuickSecret()

def test_init_success(mock_client, env_vars):
    """Test successful initialization."""
    qs = QuickSecret(project_id="test-project")
    assert qs.project_id == "test-project"
    assert qs.environment == "dev"
    mock_client.assert_called_once()

def test_get_secret_success(mock_client, env_vars):
    """Test fetching a secret successfully."""
    mock_instance = mock_client.return_value
    mock_secret = MagicMock()
    mock_secret.secret_value = "secret-value"
    mock_instance.getSecret.return_value = mock_secret
    
    qs = QuickSecret(project_id="test-project")
    value = qs.get_secret("MY_SECRET")
    
    assert value == "secret-value"
    mock_instance.getSecret.assert_called_once()

def test_get_secret_no_project_id(mock_client, env_vars):
    """Test that ValueError is raised when project_id is missing during get_secret."""
    qs = QuickSecret()
    with pytest.raises(ValueError, match="Project ID must be provided"):
        qs.get_secret("MY_SECRET")

def test_list_secrets_success(mock_client, env_vars):
    """Test listing secrets successfully."""
    mock_instance = mock_client.return_value
    
    s1 = MagicMock()
    s1.secret_name = "K1"
    s1.secret_value = "V1"
    
    s2 = MagicMock()
    s2.secret_name = "K2"
    s2.secret_value = "V2"
    
    mock_instance.listSecrets.return_value = [s1, s2]
    
    qs = QuickSecret(project_id="test-project")
    secrets = qs.list_secrets()
    
    assert secrets == {"K1": "V1", "K2": "V2"}
    mock_instance.listSecrets.assert_called_once()

def test_inject_to_env(mock_client, env_vars):
    """Test injecting a secret into environment variables."""
    mock_instance = mock_client.return_value
    mock_secret = MagicMock()
    mock_secret.secret_value = "secret-value"
    mock_instance.getSecret.return_value = mock_secret
    
    qs = QuickSecret(project_id="test-project")
    
    # Ensure it's not there before
    if "MY_SECRET" in os.environ:
        del os.environ["MY_SECRET"]
        
    qs.inject_to_env("MY_SECRET")
    
    assert os.environ["MY_SECRET"] == "secret-value"
    del os.environ["MY_SECRET"]

def test_inject_all_to_env(mock_client, env_vars):
    """Test injecting all secrets into environment variables."""
    mock_instance = mock_client.return_value
    
    s1 = MagicMock()
    s1.secret_name = "K1"
    s1.secret_value = "V1"
    
    mock_instance.listSecrets.return_value = [s1]
    
    qs = QuickSecret(project_id="test-project")
    
    if "K1" in os.environ:
        del os.environ["K1"]
        
    qs.inject_all_to_env()
    
    assert os.environ["K1"] == "V1"
    del os.environ["K1"]
