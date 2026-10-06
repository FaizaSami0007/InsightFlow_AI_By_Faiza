"""Abstract Base Connector Interface for Phase 17 Enterprise Data Connectors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.connectors.schemas import (
    ConnectionTestResult,
    ResourcePreviewResponse,
    ResourceSpec,
)
from app.database.models.connectors import ConnectorType, SyncType


class ConnectorError(Exception):
    """Base exception for all connector operation failures."""

    pass


class ConnectorAuthenticationError(ConnectorError):
    """Raised when authentication with the external data source fails."""

    pass


class ConnectorNetworkError(ConnectorError):
    """Raised on connection timeout or network unreachability."""

    pass


class ConnectorResourceNotFoundError(ConnectorError):
    """Raised when the specified table/endpoint/file is not found on the remote source."""

    pass


class DataConnector(ABC):
    """Provider-independent interface for external enterprise data sources."""

    def __init__(self, configuration: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        self.config = configuration or {}
        self.credentials = credentials or {}
        self._is_connected = False

    @property
    @abstractmethod
    def connector_type(self) -> ConnectorType:
        """Returns the specific connector family type."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establishes authenticated connection or client session with external source."""
        pass

    @abstractmethod
    async def validate_connection(self) -> ConnectionTestResult:
        """Tests connectivity, credentials, and basic read permissions."""
        pass

    @abstractmethod
    async def discover_schema(self) -> List[ResourceSpec]:
        """Discovers tables, views, endpoints, columns, and data types without downloading full data."""
        pass

    @abstractmethod
    async def list_resources(self) -> List[str]:
        """Lists available resources (e.g. table names, file keys, endpoints)."""
        pass

    @abstractmethod
    async def preview(
        self,
        resource_id: str,
        limit: int = 50,
        query_filter: Optional[str] = None,
    ) -> ResourcePreviewResponse:
        """Fetches a lightweight sample preview bounded by row limits."""
        pass

    @abstractmethod
    async def ingest(
        self,
        resource_id: str,
        sync_type: SyncType = SyncType.FULL_SYNC,
        cursor_value: Optional[Any] = None,
        column_selection: Optional[List[str]] = None,
        row_limit: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extracts records from the source with optional incremental cursor filtering.

        Returns:
            Tuple of (records_list, sync_metadata)
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Safely closes connections, pools, or client handles."""
        pass

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
