"""Connector Registry & Factory for Phase 17 Enterprise Data Connectors."""

from typing import Any, Dict, List, Optional, Type

from app.connectors.api import RESTApiConnector
from app.connectors.base import DataConnector
from app.connectors.database import MySQLConnector, PostgresConnector, SQLiteConnector
from app.connectors.schemas import ConnectorCatalogItem, ConnectorCatalogResponse
from app.connectors.sheets import GoogleSheetsConnector
from app.connectors.storage import ObjectStorageConnector
from app.database.models.connectors import ConnectorType


class ConnectorRegistry:
    """Central registry and factory managing enterprise connector classes and catalog metadata."""

    _REGISTRY: Dict[ConnectorType, Type[DataConnector]] = {
        ConnectorType.SQLITE: SQLiteConnector,
        ConnectorType.POSTGRESQL: PostgresConnector,
        ConnectorType.MYSQL: MySQLConnector,
        ConnectorType.REST_API: RESTApiConnector,
        ConnectorType.OBJECT_STORAGE: ObjectStorageConnector,
        ConnectorType.GOOGLE_SHEETS: GoogleSheetsConnector,
    }

    _CATALOG_METADATA: List[ConnectorCatalogItem] = [
        ConnectorCatalogItem(
            connector_type=ConnectorType.POSTGRESQL,
            name="PostgreSQL",
            category="Database",
            description="Enterprise relational database with read-only query safety and schema discovery.",
            supported_auth=["PASSWORD", "SSL_CERT", "IAM"],
            capabilities=["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["host", "port", "database", "username"],
            is_available=True,
        ),
        ConnectorCatalogItem(
            connector_type=ConnectorType.MYSQL,
            name="MySQL",
            category="Database",
            description="High-performance relational storage with binary-safe streaming synchronization.",
            supported_auth=["PASSWORD", "SSL_CERT"],
            capabilities=["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["host", "port", "database", "username"],
            is_available=True,
        ),
        ConnectorCatalogItem(
            connector_type=ConnectorType.SQLITE,
            name="SQLite",
            category="Database",
            description="File-backed or embedded SQLite databases with immutable table introspection.",
            supported_auth=["NONE", "FILE_PERMISSIONS"],
            capabilities=["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["database_path"],
            is_available=True,
        ),
        ConnectorCatalogItem(
            connector_type=ConnectorType.REST_API,
            name="REST API / Webhook",
            category="API",
            description="Generic HTTP/REST endpoints with SSRF protection, pagination, and JSON normalization.",
            supported_auth=["API_KEY", "BEARER_TOKEN", "BASIC_AUTH", "OAUTH2"],
            capabilities=["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["base_url"],
            is_available=True,
        ),
        ConnectorCatalogItem(
            connector_type=ConnectorType.OBJECT_STORAGE,
            name="Cloud Object Storage (S3/GCS/Azure)",
            category="Storage",
            description="Parquet, CSV, and JSON datasets in AWS S3, Google Cloud Storage, or Azure Blob.",
            supported_auth=["ACCESS_KEY", "IAM_ROLE", "SAS_TOKEN"],
            capabilities=["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["bucket_name"],
            is_available=True,
        ),
        ConnectorCatalogItem(
            connector_type=ConnectorType.GOOGLE_SHEETS,
            name="Google Sheets",
            category="Spreadsheet",
            description="Cloud spreadsheets with named worksheet range synchronization and live drift tracking.",
            supported_auth=["OAUTH2", "SERVICE_ACCOUNT"],
            capabilities=["FULL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
            required_config=["spreadsheet_id"],
            is_available=True,
        ),
    ]

    @classmethod
    def get_connector(
        cls,
        connector_type: ConnectorType,
        configuration: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None,
    ) -> DataConnector:
        """Instantiates a connector instance from registered classes."""
        connector_cls = cls._REGISTRY.get(connector_type)
        if not connector_cls:
            raise ValueError(f"Unsupported connector type '{connector_type}'.")
        return connector_cls(configuration, credentials)

    @classmethod
    def create_connector(
        cls,
        connector_type: ConnectorType,
        configuration: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None,
    ) -> DataConnector:
        """Alias for get_connector."""
        return cls.get_connector(connector_type, configuration, credentials)

    @classmethod
    def get_catalog(cls) -> ConnectorCatalogResponse:
        """Returns metadata for all available production connectors."""
        return ConnectorCatalogResponse(
            items=cls._CATALOG_METADATA,
            total=len(cls._CATALOG_METADATA),
        )
