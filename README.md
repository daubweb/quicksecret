# quicksecret

A minimal, platform-independent tool to fetch secrets from [Infisical](https://infisical.com/) using Machine Identity authentication.

## Features

- **Machine Identity Auth**: Uses `INFISICAL_MACHINE_ID` and `INFISICAL_MACHINE_SECRET` for authentication.
- **Caching**: Optional internal caching of secrets to reduce API calls.
- **Logging**: Integrated logging for better observability.
- **Environment Injection**: Easily fetch secrets and inject them directly into your application's environment variables.
- **Minimalistic**: Low overhead and easy to integrate.
- **Git Installation**: Easily installable via `uv` directly from GitHub.

## Installation

```bash
uv add git+https://github.com/daubweb/quicksecret.git
```

## Setup

Before using `quicksecret`, ensure you have an Infisical Machine Identity and the following environment variables set:

- `INFISICAL_MACHINE_ID`: Your Infisical Machine Identity Client ID.
- `INFISICAL_MACHINE_SECRET`: Your Infisical Machine Identity Client Secret.

Optional environment variables:

- `INFISICAL_PROJECT_ID`: Default Infisical project ID (can be the project slug).
- `INFISICAL_ENVIRONMENT`: Default environment (e.g., "dev", "prod"). Defaults to "dev".
- `INFISICAL_SITE_URL`: Infisical site URL. Defaults to "https://app.infisical.com".

## Usage

### Basic Usage

```python
from quicksecret import QuickSecret

# Initialize with project ID and environment
qs = QuickSecret(project_id="your-project-id", environment="dev")

# Fetch a single secret
db_url = qs.get_secret("DATABASE_URL")
print(f"Database URL: {db_url}")

# Inject a secret into environment variables
qs.inject_to_env("API_KEY")
import os
print(f"API Key from env: {os.getenv('API_KEY')}")
```

### Inject All Secrets

```python
from quicksecret import QuickSecret

qs = QuickSecret(project_id="your-project-id")

# Inject all secrets from the root path of the 'dev' environment
qs.inject_all_to_env()
```

## Development

### Prerequisites

- [uv](https://github.com/astral-sh/uv)

### Running Tests

```bash
uv run pytest
```

### Building Documentation

```bash
cd docs
uv run .\make.bat html  # On Windows
uv run make html        # On Linux/macOS
```

## License

MIT
