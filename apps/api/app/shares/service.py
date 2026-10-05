"""Service layer for Dashboard Sharing and Public Links."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.dashboards import Dashboard
from app.database.models.exports import DashboardShare
from app.shares.schemas import (
    ShareCreateRequest,
    SharedDashboardViewResponse,
    SharedFilterRefreshRequest,
    ShareResponse,
)


class ShareService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_share(
        self,
        dashboard_id: str,
        owner_id: str,
        request: ShareCreateRequest,
    ) -> ShareResponse:
        """Create a secure shareable link for a dashboard."""
        # 1. Verify dashboard ownership
        stmt = (
            select(Dashboard)
            .where(Dashboard.id == dashboard_id, Dashboard.user_id == owner_id)
            .options(
                selectinload(Dashboard.widgets),
                selectinload(Dashboard.filters),
            )
        )
        res = await self.db.execute(stmt)
        dashboard = res.scalar_one_or_none()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found or access denied.")

        # 2. Generate cryptographically secure token
        token = secrets.token_urlsafe(32)

        # 3. Calculate expiration
        expires_at: Optional[datetime] = None
        if request.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)

        # 4. If snapshot mode, freeze current spec and widget data
        snapshot_data: Optional[Dict[str, Any]] = None
        if request.is_snapshot:
            snapshot_data = {
                "title": dashboard.name,
                "description": dashboard.description,
                "dataset_id": dashboard.dataset_id,
                "dataset_version_id": dashboard.dataset_version_id,
                "theme": dashboard.theme,
                "layout_type": dashboard.layout_type,
                "layout_config": dashboard.layout_config,
                "widgets": [
                    {
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
                    }
                    for w in dashboard.widgets
                ],
                "filters": [
                    {
                        "id": f.id,
                        "column_name": f.column_name,
                        "display_name": f.display_name,
                        "filter_type": f.filter_type,
                        "operator": f.operator,
                        "current_value": f.current_value,
                        "allowed_values": f.allowed_values,
                        "scope": f.scope,
                    }
                    for f in dashboard.filters
                ],
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }

        # 5. Persist share record
        share = DashboardShare(
            dashboard_id=dashboard.id,
            owner_id=owner_id,
            share_token=token,
            access_type="read_only",
            is_active=True,
            is_snapshot=request.is_snapshot,
            snapshot_data=snapshot_data,
            allowed_filters=request.allowed_filters,
            expires_at=expires_at,
        )
        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)

        return ShareResponse(
            id=share.id,
            dashboard_id=share.dashboard_id,
            owner_id=share.owner_id,
            share_token=share.share_token,
            share_url=f"/shared/{share.share_token}",
            access_type=share.access_type,
            is_active=share.is_active,
            is_snapshot=share.is_snapshot,
            allowed_filters=share.allowed_filters,
            view_count=share.view_count,
            last_accessed_at=share.last_accessed_at,
            expires_at=share.expires_at,
            created_at=share.created_at,
            updated_at=share.updated_at,
        )

    async def list_shares(self, dashboard_id: str, owner_id: str) -> List[ShareResponse]:
        """List all shares for a dashboard (owner only)."""
        stmt = (
            select(DashboardShare)
            .where(DashboardShare.dashboard_id == dashboard_id, DashboardShare.owner_id == owner_id)
            .order_by(desc(DashboardShare.created_at))
        )
        res = await self.db.execute(stmt)
        shares = res.scalars().all()
        return [
            ShareResponse(
                id=s.id,
                dashboard_id=s.dashboard_id,
                owner_id=s.owner_id,
                share_token=s.share_token,
                share_url=f"/shared/{s.share_token}",
                access_type=s.access_type,
                is_active=s.is_active,
                is_snapshot=s.is_snapshot,
                allowed_filters=s.allowed_filters,
                view_count=s.view_count,
                last_accessed_at=s.last_accessed_at,
                expires_at=s.expires_at,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in shares
        ]

    async def revoke_share(self, share_id: str, owner_id: str) -> ShareResponse:
        """Revoke a share link immediately."""
        stmt = select(DashboardShare).where(DashboardShare.id == share_id, DashboardShare.owner_id == owner_id)
        res = await self.db.execute(stmt)
        share = res.scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=404, detail="Share link not found or access denied.")

        share.is_active = False
        await self.db.commit()
        await self.db.refresh(share)

        return ShareResponse(
            id=share.id,
            dashboard_id=share.dashboard_id,
            owner_id=share.owner_id,
            share_token=share.share_token,
            share_url=f"/shared/{share.share_token}",
            access_type=share.access_type,
            is_active=share.is_active,
            is_snapshot=share.is_snapshot,
            allowed_filters=share.allowed_filters,
            view_count=share.view_count,
            last_accessed_at=share.last_accessed_at,
            expires_at=share.expires_at,
            created_at=share.created_at,
            updated_at=share.updated_at,
        )

    async def get_shared_dashboard(self, share_token: str) -> SharedDashboardViewResponse:
        """Public / token-based read-only lookup of shared dashboard."""
        stmt = (
            select(DashboardShare)
            .where(DashboardShare.share_token == share_token)
            .options(
                selectinload(DashboardShare.dashboard).selectinload(Dashboard.widgets),
                selectinload(DashboardShare.dashboard).selectinload(Dashboard.filters),
            )
        )
        res = await self.db.execute(stmt)
        share = res.scalar_one_or_none()

        if not share or not share.is_active:
            raise HTTPException(status_code=404, detail="Shared dashboard link is invalid or has been revoked.")

        if share.expires_at:
            exp_time = share.expires_at
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            if exp_time < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="Shared dashboard link has expired.")

        # Update access metrics
        share.view_count += 1
        share.last_accessed_at = datetime.now(timezone.utc)
        await self.db.commit()

        # If snapshot mode, return frozen snapshot
        if share.is_snapshot and share.snapshot_data:
            snap = share.snapshot_data
            return SharedDashboardViewResponse(
                share_token=share.share_token,
                dashboard_id=share.dashboard_id,
                title=snap.get("title", "Shared Dashboard"),
                description=snap.get("description"),
                dataset_id=snap.get("dataset_id", ""),
                dataset_version_id=snap.get("dataset_version_id", ""),
                is_snapshot=True,
                status="READY",
                theme=snap.get("theme", "default"),
                layout_type=snap.get("layout_type", "grid_12"),
                layout_config=snap.get("layout_config", {}),
                widgets=snap.get("widgets", []),
                filters=snap.get("filters", []),
                allowed_filters=share.allowed_filters,
                created_at=share.created_at,
                updated_at=share.updated_at,
            )

        # Otherwise, return live dashboard data
        dashboard = share.dashboard
        if not dashboard:
            raise HTTPException(status_code=404, detail="Underlying dashboard no longer exists.")

        widgets_out = [
            {
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
            }
            for w in dashboard.widgets
        ]

        filters_out = [
            {
                "id": f.id,
                "column_name": f.column_name,
                "display_name": f.display_name,
                "filter_type": f.filter_type,
                "operator": f.operator,
                "current_value": f.current_value,
                "allowed_values": f.allowed_values,
                "scope": f.scope,
            }
            for f in dashboard.filters
        ]

        return SharedDashboardViewResponse(
            share_token=share.share_token,
            dashboard_id=dashboard.id,
            title=dashboard.name,
            description=dashboard.description,
            dataset_id=dashboard.dataset_id,
            dataset_version_id=dashboard.dataset_version_id,
            is_snapshot=False,
            status=dashboard.status,
            theme=dashboard.theme,
            layout_type=dashboard.layout_type,
            layout_config=dashboard.layout_config,
            widgets=widgets_out,
            filters=filters_out,
            allowed_filters=share.allowed_filters,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )

    async def refresh_shared_filters(
        self,
        share_token: str,
        request: SharedFilterRefreshRequest,
    ) -> SharedDashboardViewResponse:
        """Allow shared viewer to test temporary session filters without mutating owner dashboard."""
        base_view = await self.get_shared_dashboard(share_token)
        # Viewer filter execution can safely filter widget result_data in-memory or re-query DuckDB
        if not request.filter_values:
            return base_view

        filtered_widgets: List[Dict[str, Any]] = []
        for w in base_view.widgets:
            w_copy = dict(w)
            res_data = dict(w.get("result_data") or {})
            rows = res_data.get("rows") or []
            cols = res_data.get("columns") or []

            # In-memory row filtering for shared session
            if rows:
                matching_rows = []
                for r in rows:
                    match = True
                    for col_name, filter_val in request.filter_values.items():
                        if filter_val is not None and filter_val != "" and col_name in r:
                            if str(r[col_name]).lower() != str(filter_val).lower():
                                match = False
                                break
                    if match:
                        matching_rows.append(r)
                w_copy["result_data"] = {"columns": cols, "rows": matching_rows}
            filtered_widgets.append(w_copy)

        base_view.widgets = filtered_widgets
        return base_view
