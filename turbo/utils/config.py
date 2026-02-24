"""Configuration management for Turbo application."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = "sqlite+aiosqlite:///./turbo.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    @field_validator("url", mode="before")
    @classmethod
    def convert_postgres_url(cls, v):
        """Convert postgres:// to postgresql+asyncpg:// for async SQLAlchemy."""
        if isinstance(v, str):
            # Fly.io provides postgres:// but SQLAlchemy async needs postgresql+asyncpg://
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            # Also handle postgresql:// without asyncpg driver
            elif v.startswith("postgresql://") and "+asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Strip sslmode parameter - asyncpg handles SSL differently
            if "?sslmode=" in v:
                v = v.split("?sslmode=")[0]
            elif "&sslmode=" in v:
                # Handle case where sslmode is not first param
                import re
                v = re.sub(r"[&?]sslmode=[^&]*", "", v)
        return v

    model_config = {"env_prefix": "DATABASE_", "env_file": ".env", "extra": "ignore"}


class APISettings(BaseSettings):
    """API server configuration settings."""

    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = False

    model_config = {"env_prefix": "API_", "env_file": ".env", "extra": "ignore"}


class WebSettings(BaseSettings):
    """Web UI configuration settings."""

    host: str = "127.0.0.1"
    port: int = 8501
    enable_ui: bool = True

    model_config = {"env_prefix": "WEB_", "env_file": ".env", "extra": "ignore"}


class ClaudeSettings(BaseSettings):
    """Claude integration configuration settings."""

    integration_enabled: bool = True
    context_directory: str = ".turbo/context"
    templates_directory: str = ".turbo/templates"
    responses_directory: str = ".turbo/responses"

    model_config = {"env_prefix": "CLAUDE_", "env_file": ".env", "extra": "ignore"}


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    secret_key: str = ""  # Set via SECURITY_SECRET_KEY env var
    cors_origins: list[str] = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {"env_prefix": "SECURITY_", "env_file": ".env", "extra": "ignore"}


class FeatureSettings(BaseSettings):
    """Feature flags and configuration."""

    ai_generation: bool = True
    export_formats: list[str] = ["pdf", "docx", "html", "markdown"]
    git_integration: bool = True

    @field_validator("export_formats", mode="before")
    @classmethod
    def parse_export_formats(cls, v):
        """Parse export formats from comma-separated string or list."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v

    model_config = {"env_prefix": "FEATURE_", "env_file": ".env", "extra": "ignore"}


class GraphSettings(BaseSettings):
    """Knowledge Graph (Neo4j + Local Embeddings) configuration settings."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""  # Set via NEO4J_PASSWORD env var
    database: str = "neo4j"
    embedding_model: str = "all-MiniLM-L6-v2"  # Fast, high-quality embeddings
    enabled: bool = True

    model_config = {"env_prefix": "NEO4J_", "env_file": ".env", "extra": "ignore"}


class LLMSettings(BaseSettings):
    """LLM (Ollama) configuration settings."""

    base_url: str = "http://ollama:11434"
    default_model: str = "qwen2.5:7b"
    enabled: bool = True

    model_config = {"env_prefix": "OLLAMA_", "env_file": ".env", "extra": "ignore"}


class AnthropicSettings(BaseSettings):
    """Anthropic Claude API configuration settings."""

    api_key: str = ""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.0
    enabled: bool = True

    model_config = {"env_prefix": "ANTHROPIC_", "env_file": ".env", "extra": "ignore"}


class Settings(BaseSettings):
    """Main application settings."""

    # Application settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    web: WebSettings = WebSettings()
    claude: ClaudeSettings = ClaudeSettings()
    security: SecuritySettings = SecuritySettings()
    features: FeatureSettings = FeatureSettings()
    graph: GraphSettings = GraphSettings()
    llm: LLMSettings = LLMSettings()
    anthropic: AnthropicSettings = AnthropicSettings()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        valid_environments = ["development", "testing", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(
                f"Invalid environment: {v}. Must be one of {valid_environments}"
            )
        return v.lower()

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "case_sensitive": False,
        "extra": "ignore",
    }

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
