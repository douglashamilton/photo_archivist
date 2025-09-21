"""Test fixtures and utilities for Photo Archivist tests."""

import os
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Generator, Optional, Any
from uuid import UUID, uuid4

import httpx
import pytest
from app.sync.graph_client import GraphClient
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, HTTPStatusError
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.config import Settings
from app.main import create_app
from app.models.domain import (
    User, AuthToken, SyncState, Asset, Score,
    Shortlist, ShortlistItem, PrintOrder, ShortlistStatus,
    PrintOrderStatus
)

@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment."""
    os.environ["ENV_FILE"] = ".env.test"
    yield
    os.environ.pop("ENV_FILE", None)

# Test data paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PHOTO = FIXTURES_DIR / "sample.jpg"
BURST_PHOTOS = [FIXTURES_DIR / f"burst_{i}.jpg" for i in range(1, 4)]

# Test constants
TEST_USER_ID = str(uuid4())
TEST_TENANT_ID = "test-tenant"
TEST_DELTA_LINK = "https://graph.microsoft.com/v1.0/drive/root/delta?token=123"

@pytest.fixture
def test_settings() -> Settings:
    """Test settings with stubbed credentials."""
    return Settings(
        msal_tenant_id="test-tenant",
        msal_client_id="test-client",
        msal_client_secret="test-secret",
        database_url="sqlite:///:memory:",
        secret_key="test-key",
        kite_api_key="test-key",
        kite_test_mode=True
    )

@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest_asyncio.fixture
async def test_db(test_db_engine):
    """Create test database session."""
    with Session(test_db_engine) as session:
        yield session

@pytest_asyncio.fixture
async def app(test_settings, test_db_engine) -> FastAPI:
    """Create test FastAPI application."""
    app = create_app()
    app.state.settings = test_settings
    app.state.engine = test_db_engine
    return app

@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_graph_client(mocker):
    """Mock Microsoft Graph client responses."""
    # Mock successful response data
    response_data = {
        "@odata.deltaLink": TEST_DELTA_LINK,
        "value": [
            {
                "id": f"item_{i}",
                "name": f"photo_{i}.jpg",
                "file": {"mimeType": "image/jpeg"},
                "parentReference": {"path": "/drive/root:/Photos"},
                "photo": {"takenDateTime": "2025-01-01T00:00:00Z"}
            }
            for i in range(3)
        ]
    }
    
    # Create minimally valid test JWT
    test_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0ZXN0IjoidHJ1ZSJ9.test"  # Header + payload + signature

    # Create mock GraphClient instance
    mock_client = mocker.MagicMock(spec=GraphClient)
    mock_client.access_token = test_jwt
    mock_client.base_url = "https://graph.microsoft.com/v1.0"
    mock_client.headers = {
        "Authorization": f"Bearer {test_jwt}",
        "Accept": "application/json"
    }

    # Create mock HTTP client
    mock_http_client = mocker.MagicMock(spec=httpx.AsyncClient)

    # Configure HTTP client context manager
    mock_http_client.__aenter__.return_value = mock_http_client
    mock_http_client.__aexit__.return_value = None

    # Add HTTP client to GraphClient
    mock_client.client = mock_http_client

    # Set up initial get method behavior with request/response validation
    attempts = {}  # Track retry attempts per URL
    
    async def mock_get(url, **kwargs):
        # Track the request
        get_mock.call_args_list.append(mocker.call(url, **kwargs))

        # For initial sync without token - return deltaLink with correct URL structure
        if url == f"{mock_client.base_url}/me/drive/root/delta":
            attempts[url] = attempts.get(url, 0) + 1
            
            # First attempt returns 429 with Retry-After
            if attempts[url] == 1:
                response = mocker.Mock(spec=httpx.Response)
                response.status_code = 429
                response.request = httpx.Request("GET", url)
                response.is_error = True
                response.headers = {"Retry-After": "1"}
                response.json.return_value = {"error": {"message": "Too Many Requests"}}
                return response
            
            # Subsequent attempts succeed
            response = mocker.Mock(spec=httpx.Response)
            response.status_code = 200
            response.request = httpx.Request("GET", url)
            response.is_error = False
            response.json.return_value = {
                "@odata.deltaLink": f"{mock_client.base_url}/drive/root/delta?token=123",
                "value": response_data["value"]
            }
            return response

        # For subsequent sync with token=123 - handle similarly
        if "token=123" in url:
            attempts[url] = attempts.get(url, 0) + 1
            
            # First attempt returns 429
            if attempts[url] == 1:
                response = mocker.Mock(spec=httpx.Response)
                response.status_code = 429
                response.request = httpx.Request("GET", url)
                response.is_error = True
                response.headers = {"Retry-After": "1"}
                response.json.return_value = {"error": {"message": "Too Many Requests"}}
                return response

            # Subsequent attempts succeed
            response = mocker.Mock(spec=httpx.Response)
            response.status_code = 200
            response.request = httpx.Request("GET", url)
            response.is_error = False
            response.json.return_value = {
                "@odata.deltaLink": f"{mock_client.base_url}/drive/root/delta?token=456",
                "value": [
                    {
                        "id": "new_item",
                        "name": "new_photo.jpg",
                        "file": {"mimeType": "image/jpeg"},
                        "parentReference": {"path": "/drive/root:/Photos"},
                        "photo": {"takenDateTime": "2025-01-01T00:00:00Z"}
                    }
                ]
            }
            return response

        # Default unauthorized response
        response = mocker.Mock(spec=httpx.Response)
        response.status_code = 401
        response.request = httpx.Request("GET", url)
        response.is_error = True
        response.json.return_value = {"error": {"message": "Unauthorized"}}
        return response

    # Create and store the get mock so tests can access it
    get_mock = mocker.MagicMock(side_effect=mock_get)
    mock_http_client.get = get_mock

    # Make list_delta use the real implementation with retries
    async def real_list_delta(delta_token=None, page_size=200):
        url = f"{mock_client.base_url}/me/drive/root/delta"
        if delta_token:
            if delta_token.startswith("http"):
                url = delta_token
            else:
                url = f"{url}?token={delta_token}"

        async with mock_http_client as client:
            while True:
                response = await client.get(
                    url,
                    headers=mock_client.headers,
                    params=None if delta_token else {
                        "$select": "id,name,file,photo,size,parentReference",
                        "$top": page_size
                    }
                )
                
                if response.is_error:
                    # Handle 429 with retry
                    if response.status_code == 429 and "Retry-After" in response.headers:
                        retry_after = int(response.headers["Retry-After"])
                        from asyncio import sleep
                        await sleep(retry_after)  # Honor throttling delay
                        continue
                        
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown Graph API error")
                    raise HTTPStatusError(
                        message=error_msg,
                        request=response.request,
                        response=response
                    )
                    
                # Success - break out of retry loop
                break
                
            return response.json()

    mock_client.list_delta = real_list_delta

    # Create factory to return our mock instance
    mock_factory = mocker.Mock(spec=GraphClient)
    mock_factory.return_value = mock_client

    # Patch GraphClient class in delta_scanner module
    mocker.patch('app.sync.delta_scanner.GraphClient', mock_factory)
    return mock_factory

@pytest.fixture
def test_user(test_db, test_settings) -> User:
    """Create test user."""
    user = User(
        id=UUID('14a968b4-35af-4c5b-a34d-780e7da43fa3'),
        tenant_id=test_settings.msal_tenant_id,
        display_name="Test User",
        scopes=["Files.Read", "offline_access"]
    )
    
    token = AuthToken(
        user_id=user.id,
        access_token=f"Bearer {uuid4()}",
        refresh_token=str(uuid4()),
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None)  # Make naive for comparison
    )
    
    test_db.add(user)
    test_db.add(token)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def mock_kite_client(mocker):
    """Mock Kite client."""
    return mocker.patch('app.print.routes.KiteClient')