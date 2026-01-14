"""Global test configuration and fixtures for Turbo."""

import asyncio
from collections.abc import AsyncGenerator, Generator
import os
from pathlib import Path
import tempfile

from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from turbo.core.database import Base, get_db_session
from turbo.core.models import Document, Issue, Project

# from turbo.main import app  # Commented out for now since we need to fix circular imports


# Test Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_session):
    """Override database dependency for testing."""
    from turbo.main import app

    async def _override_get_db():
        yield test_session

    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def test_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    from httpx import ASGITransport

    from turbo.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def turbo_workspace(temp_dir) -> Path:
    """Create a temporary Turbo workspace."""
    workspace = temp_dir / "turbo_workspace"
    workspace.mkdir()

    # Create .turbo directory structure
    turbo_dir = workspace / ".turbo"
    turbo_dir.mkdir()
    (turbo_dir / "context").mkdir()
    (turbo_dir / "templates").mkdir()
    (turbo_dir / "responses").mkdir()
    (turbo_dir / "exports").mkdir()
    (turbo_dir / "backups").mkdir()

    return workspace


# Sample Data Fixtures
@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "priority": "medium",
        "status": "active",
    }


@pytest.fixture
async def sample_project(test_session, sample_project_data):
    """Create a sample project in the database."""
    project = Project(**sample_project_data)
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)
    return project


@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "title": "Test Issue",
        "description": "A test issue for unit testing",
        "type": "feature",
        "status": "open",
        "priority": "medium",
    }


@pytest.fixture
async def sample_issue(test_session, sample_project, sample_issue_data):
    """Create a sample issue in the database."""
    issue_data = {**sample_issue_data, "project_id": sample_project.id}
    issue = Issue(**issue_data)
    test_session.add(issue)
    await test_session.commit()
    await test_session.refresh(issue)
    return issue


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "content": "# Test Document\n\nThis is a test document.",
        "type": "specification",
        "format": "markdown",
    }


@pytest.fixture
async def sample_document(test_session, sample_project, sample_document_data):
    """Create a sample document in the database."""
    document_data = {**sample_document_data, "project_id": sample_project.id}
    document = Document(**document_data)
    test_session.add(document)
    await test_session.commit()
    await test_session.refresh(document)
    return document


# Mock Fixtures
@pytest.fixture
def mock_claude_service():
    """Mock Claude integration service."""
    from unittest.mock import AsyncMock, Mock

    mock_service = Mock()
    mock_service.generate_spec = AsyncMock(
        return_value={
            "title": "Generated Specification",
            "content": "# Generated Content\n\nThis is AI-generated content.",
            "metadata": {
                "model": "claude-3.5-sonnet",
                "timestamp": "2025-09-28T10:00:00Z",
            },
        }
    )
    mock_service.analyze_project = AsyncMock(
        return_value={
            "health_score": 85,
            "recommendations": ["Add more tests", "Update documentation"],
            "risks": ["Technical debt in module X"],
        }
    )
    return mock_service


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations."""
    from unittest.mock import Mock, patch

    mock_fs = Mock()
    mock_fs.root_path = temp_dir
    mock_fs.write_file = Mock()
    mock_fs.read_file = Mock()
    mock_fs.delete_file = Mock()

    with patch("turbo.utils.file_system.FileSystem", return_value=mock_fs):
        yield mock_fs


# Test Data Generators
def generate_projects(count: int = 5):
    """Generate multiple test projects."""
    projects = []
    for i in range(count):
        projects.append(
            {
                "name": f"Test Project {i + 1}",
                "description": f"Description for test project {i + 1}",
                "priority": ["low", "medium", "high"][i % 3],
                "status": ["active", "on_hold", "completed"][i % 3],
            }
        )
    return projects


def generate_issues(project_id, count: int = 3):
    """Generate multiple test issues for a project."""
    issues = []
    for i in range(count):
        issues.append(
            {
                "title": f"Test Issue {i + 1}",
                "description": f"Description for test issue {i + 1}",
                "type": ["feature", "bug", "task"][i % 3],
                "status": ["open", "in_progress", "closed"][i % 3],
                "priority": ["low", "medium", "high"][i % 3],
                "project_id": project_id,
            }
        )
    return issues


# Performance Testing Fixtures
@pytest.fixture
def performance_data():
    """Generate data for performance testing."""
    return {
        "projects": generate_projects(100),
        "issues_per_project": 20,
        "documents_per_project": 5,
    }


# Integration Test Fixtures
@pytest.fixture
async def populated_database(test_session):
    """Create a database populated with test data."""
    # Create multiple projects
    projects = []
    for project_data in generate_projects(10):
        project = Project(**project_data)
        test_session.add(project)
        projects.append(project)

    await test_session.commit()

    # Create issues for each project
    for project in projects:
        for issue_data in generate_issues(project.id, 5):
            issue = Issue(**issue_data)
            test_session.add(issue)

    await test_session.commit()
    return projects


# Environment Configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "TURBO_ENV": "testing",
        "TURBO_DEBUG": "true",
        "TURBO_LOG_LEVEL": "DEBUG",
        "DATABASE_URL": TEST_DATABASE_URL,
        "CLAUDE_INTEGRATION_ENABLED": "false",
    }

    # Set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Pytest Markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line(
        "markers", "claude: marks tests that require Claude integration"
    )


# Test Utilities
class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def assert_dict_contains(actual: dict, expected: dict):
        """Assert that actual dict contains all key-value pairs from expected."""
        for key, value in expected.items():
            assert key in actual, f"Key '{key}' not found in actual dict"
            assert actual[key] == value, f"Value mismatch for key '{key}'"

    @staticmethod
    def assert_model_fields(model, expected_fields: dict):
        """Assert that model has expected field values."""
        for field, expected_value in expected_fields.items():
            actual_value = getattr(model, field)
            assert actual_value == expected_value, (
                f"Field '{field}' mismatch: expected {expected_value}, "
                f"got {actual_value}"
            )


@pytest.fixture
def test_utils():
    """Provide test utility functions."""
    return TestUtils
