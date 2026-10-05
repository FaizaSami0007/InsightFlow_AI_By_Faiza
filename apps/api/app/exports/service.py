"""Service layer for Dashboard Exports."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.dashboards import Dashboard
from app.database.models.exports import DashboardExport, ExportStatus
from app.exports.engine import (
    MAX_EXPORT_FILE_SIZE,
    MAX_EXPORT_WIDGETS,
    ExportEngine,
    sanitize_filename,
)
from app.exports.schemas import ExportRequest, ExportResponse

EXPORTS_STORAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "exports")
)


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_export(
        self,
        dashboard_id: str,
        user_id: str,
        request: ExportRequest,
    ) -> ExportResponse:
        """Create a deterministic export file and record for the dashboard."""
        # 1. Fetch dashboard with ownership check
        stmt = (
            select(Dashboard)
            .where(Dashboard.id == dashboard_id, Dashboard.user_id == user_id)
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.filters),
            )
        )
        res = await self.db.execute(stmt)
        dashboard = res.scalar_one_or_none()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found or access denied.")

        # 2. Prepare metadata and widget data snapshot
        active_filters = request.filter_values or {}
        if not active_filters:
            for f in dashboard.filters:
                if f.current_value is not None:
                    active_filters[f.column_name] = f.current_value

        dashboard_spec = {
            "id": dashboard.id,
            "name": dashboard.name,
            "title": dashboard.name,
            "description": dashboard.description,
            "dataset_id": dashboard.dataset_id,
            "dataset_version_id": dashboard.dataset_version_id,
            "theme": dashboard.theme,
            "layout_type": dashboard.layout_type,
        }

        # Format widgets
        widgets_data: List[Dict[str, Any]] = []
        for w in dashboard.widgets[:MAX_EXPORT_WIDGETS]:
            widgets_data.append({
                "id": w.id,
                "title": w.title,
                "description": w.description,
                "widget_type": w.widget_type,
                "analysis_id": w.analysis_id,
                "chart_spec": w.chart_spec_json,
                "grid_x": w.grid_x,
                "grid_y": w.grid_y,
                "grid_w": w.grid_w,
                "grid_h": w.grid_h,
                "metadata": w.metadata_json,
                "result_data": (w.metadata_json or {}).get("result_data", {}),
            })

        # 3. Create DB Export entry
        import uuid
        export_id = str(uuid.uuid4())
        clean_title = request.title_override or dashboard.name
        safe_base = sanitize_filename(clean_title)
        ext = request.format.value.lower()
        rel_path = f"{user_id}/{safe_base}-{export_id[:8]}.{ext}"
        full_output_path = os.path.join(EXPORTS_STORAGE_DIR, user_id, f"{safe_base}-{export_id[:8]}.{ext}")

        content_types = {
            "pdf": "application/pdf",
            "png": "image/png",
            "csv": "text/csv",
            "json": "application/json",
        }
        content_type = content_types.get(ext, "application/octet-stream")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # 4. Generate file deterministically
        file_size = 0
        status = ExportStatus.COMPLETED.value
        err_msg = None

        try:
            if ext == "pdf":
                file_size = ExportEngine.generate_pdf(
                    dashboard_spec=dashboard_spec,
                    widgets_data=widgets_data,
                    filter_snapshot=active_filters,
                    output_path=full_output_path,
                    page_size=request.page_size,
                    orientation=request.orientation,
                    include_provenance=request.include_provenance,
                    include_filters=request.include_filters,
                    title_override=request.title_override,
                )
            elif ext == "png":
                file_size = ExportEngine.generate_png(
                    dashboard_spec=dashboard_spec,
                    widgets_data=widgets_data,
                    filter_snapshot=active_filters,
                    output_path=full_output_path,
                    title_override=request.title_override,
                )
            elif ext == "csv":
                file_size = ExportEngine.generate_csv(
                    dashboard_spec=dashboard_spec,
                    widgets_data=widgets_data,
                    filter_snapshot=active_filters,
                    output_path=full_output_path,
                    target_widget_id=request.widget_id,
                )
            elif ext == "json":
                import json
                os.makedirs(os.path.dirname(os.path.abspath(full_output_path)), exist_ok=True)
                json_payload = {
                    "dashboard": dashboard_spec,
                    "widgets": widgets_data,
                    "filters": active_filters,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                }
                with open(full_output_path, "w", encoding="utf-8") as jf:
                    json.dump(json_payload, jf, indent=2)
                file_size = os.path.getsize(full_output_path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported export format: {ext}")

            if file_size > MAX_EXPORT_FILE_SIZE:
                os.remove(full_output_path)
                raise HTTPException(status_code=413, detail="Generated export exceeded maximum allowed file size.")

        except HTTPException:
            raise
        except Exception as ex:
            status = ExportStatus.FAILED.value
            err_msg = str(ex)

        # 5. Persist export record
        db_export = DashboardExport(
            id=export_id,
            dashboard_id=dashboard.id,
            user_id=user_id,
            format=ext,
            status=status,
            title=clean_title,
            file_path=rel_path if status == ExportStatus.COMPLETED.value else None,
            file_size_bytes=file_size if status == ExportStatus.COMPLETED.value else 0,
            content_type=content_type,
            filter_snapshot=active_filters,
            metadata_snapshot={
                "dataset_id": dashboard.dataset_id,
                "dataset_version_id": dashboard.dataset_version_id,
                "widgets_count": len(widgets_data),
            },
            error_message=err_msg,
            expires_at=expires_at,
        )
        self.db.add(db_export)
        await self.db.commit()
        await self.db.refresh(db_export)

        return ExportResponse(
            id=db_export.id,
            dashboard_id=db_export.dashboard_id,
            user_id=db_export.user_id,
            format=db_export.format,
            status=db_export.status,
            title=db_export.title,
            file_size_bytes=db_export.file_size_bytes,
            content_type=db_export.content_type,
            filter_snapshot=db_export.filter_snapshot,
            metadata_snapshot=db_export.metadata_snapshot,
            error_message=db_export.error_message,
            download_url=f"/api/v1/exports/{db_export.id}/download",
            expires_at=db_export.expires_at,
            created_at=db_export.created_at,
            updated_at=db_export.updated_at,
        )

    async def get_export(self, export_id: str, user_id: str) -> ExportResponse:
        """Get export details with ownership check."""
        stmt = select(DashboardExport).where(DashboardExport.id == export_id, DashboardExport.user_id == user_id)
        res = await self.db.execute(stmt)
        exp = res.scalar_one_or_none()
        if not exp:
            raise HTTPException(status_code=404, detail="Export not found or access denied.")

        return ExportResponse(
            id=exp.id,
            dashboard_id=exp.dashboard_id,
            user_id=exp.user_id,
            format=exp.format,
            status=exp.status,
            title=exp.title,
            file_size_bytes=exp.file_size_bytes,
            content_type=exp.content_type,
            filter_snapshot=exp.filter_snapshot,
            metadata_snapshot=exp.metadata_snapshot,
            error_message=exp.error_message,
            download_url=f"/api/v1/exports/{exp.id}/download",
            expires_at=exp.expires_at,
            created_at=exp.created_at,
            updated_at=exp.updated_at,
        )

    async def list_exports(self, dashboard_id: str, user_id: str) -> List[ExportResponse]:
        """List exports created for a dashboard."""
        stmt = (
            select(DashboardExport)
            .where(DashboardExport.dashboard_id == dashboard_id, DashboardExport.user_id == user_id)
            .order_by(desc(DashboardExport.created_at))
        )
        res = await self.db.execute(stmt)
        items = res.scalars().all()
        return [
            ExportResponse(
                id=e.id,
                dashboard_id=e.dashboard_id,
                user_id=e.user_id,
                format=e.format,
                status=e.status,
                title=e.title,
                file_size_bytes=e.file_size_bytes,
                content_type=e.content_type,
                filter_snapshot=e.filter_snapshot,
                metadata_snapshot=e.metadata_snapshot,
                error_message=e.error_message,
                download_url=f"/api/v1/exports/{e.id}/download",
                expires_at=e.expires_at,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in items
        ]

    async def get_export_file_for_download(self, export_id: str, user_id: str) -> Tuple[str, str, str]:
        """Return (full_file_path, filename, content_type) after checking ownership & expiration."""
        stmt = select(DashboardExport).where(DashboardExport.id == export_id, DashboardExport.user_id == user_id)
        res = await self.db.execute(stmt)
        exp = res.scalar_one_or_none()
        if not exp:
            raise HTTPException(status_code=404, detail="Export not found or access denied.")

        if exp.status != ExportStatus.COMPLETED.value or not exp.file_path:
            raise HTTPException(status_code=400, detail="Export file is not ready or has failed.")

        if exp.expires_at:
            exp_time = exp.expires_at
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            if exp_time < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="Export has expired.")

        full_path = os.path.abspath(os.path.join(EXPORTS_STORAGE_DIR, exp.file_path))
        # Directory traversal prevention
        if not full_path.startswith(EXPORTS_STORAGE_DIR):
            raise HTTPException(status_code=403, detail="Invalid export storage path.")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Export file missing from storage.")

        filename = os.path.basename(full_path)
        return full_path, filename, exp.content_type
