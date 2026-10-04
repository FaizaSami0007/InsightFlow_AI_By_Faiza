"""Core Dashboard orchestration service (AsyncSession native).

Coordinates AI planning, plan validation, deterministic analytical execution,
visualization recommendation, grid layout calculation, filter propagation, and persistence.
"""

import copy
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.duckdb.manager import duckdb_manager
from app.analytics.engine.registry import analysis_registry
from app.dashboards.engine.layout import DashboardLayoutEngine
from app.dashboards.planner.planner import DashboardPlanner
from app.dashboards.planner.validator import DashboardPatchValidator
from app.dashboards.schemas import (
    DashboardCreateRequest,
    DashboardFilterResponse,
    DashboardGenerateRequest,
    DashboardPatch,
    DashboardPlan,
    DashboardQualityReport,
    DashboardResponse,
    DashboardUpdateRequest,
    DashboardWidgetResponse,
    PatchOp,
)
from app.database.models.analytics import AnalysisJob, AnalysisJobStatus
from app.database.models.dashboards import (
    Dashboard,
    DashboardFilter,
    DashboardStatus,
    DashboardWidget,
)
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.profiling import DatasetProfile, SemanticColumn, SemanticRole
from app.datasets.storage import get_storage_provider
from app.visualization.engine.rules import recommendation_engine
from app.visualization.schemas import ChartType, VisualizationSpec

logger = logging.getLogger("insightflow.dashboards.service")


class DashboardService:
    @classmethod
    def _get_visualization_for_job(
        cls,
        job: AnalysisJob,
        preferred_chart_type: Optional[ChartType] = None,
        intent: Optional[str] = None,
    ) -> VisualizationSpec:
        result_payload = job.result_json or {}
        columns = result_payload.get("columns", [])
        rows = result_payload.get("rows", [])
        summary = job.summary_json or {}
        parameters = job.parameters_json or {}
        filters = job.filters_json or {}

        return recommendation_engine.recommend(
            operation=job.operation,
            columns=columns,
            rows=rows,
            summary=summary,
            parameters=parameters,
            filters=filters,
            dataset_id=job.dataset_id,
            dataset_version_id=job.dataset_version_id,
            analysis_id=job.id,
            preferred_chart_type=preferred_chart_type,
        )

    @classmethod
    async def _execute_analytical_job(
        cls,
        db: AsyncSession,
        user_id: str,
        dataset_id: str,
        dataset_version_id: str,
        operation: str,
        params: Dict[str, Any],
        filters: Optional[Any] = None,
    ) -> AnalysisJob:
        res = await db.execute(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
        version = res.scalars().first()
        if not version:
            raise ValueError(f"DatasetVersion '{dataset_version_id}' not found")

        storage_backend = get_storage_provider()
        physical_path = str(storage_backend.get_file_path(version.storage_reference))

        view_name = duckdb_manager.register_dataset(
            dataset_version_id=version.id,
            file_path=physical_path,
            file_format=version.file_format.value if hasattr(version.file_format, "value") else str(version.file_format),
        )
        schema_dict = duckdb_manager.get_schema(version.id)
        dataset_columns = list(schema_dict.keys())

        analytical_dataset = AnalyticalDataset(
            dataset_id=dataset_id,
            version_id=version.id,
            view_name=view_name,
            file_path=physical_path,
            file_format=version.file_format.value if hasattr(version.file_format, "value") else str(version.file_format),
            schema=schema_dict,
            columns=dataset_columns,
        )

        job = AnalysisJob(
            user_id=user_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            operation=operation,
            parameters_json=params,
            filters_json=filters,
            status=AnalysisJobStatus.RUNNING,
        )
        db.add(job)
        await db.flush()

        start_time = time.perf_counter()
        cols, rows, summary = analysis_registry.execute(
            tool_name=operation,
            dataset=analytical_dataset,
            parameters=params,
            filters=filters,
        )
        exec_time = round((time.perf_counter() - start_time) * 1000, 2)
        job.status = AnalysisJobStatus.COMPLETED
        job.execution_time_ms = exec_time
        job.row_count = len(rows)
        job.summary_json = summary
        job.result_json = {"columns": cols, "rows": rows}
        job.completed_at = datetime.utcnow()
        await db.flush()
        return job

    @classmethod
    async def get_dashboard_entity(cls, db: AsyncSession, user_id: str, dashboard_id: str) -> Dashboard:
        """Fetch dashboard with eager loading and strict user authorization check."""
        stmt = (
            select(Dashboard)
            .where(Dashboard.id == dashboard_id)
            .options(
                selectinload(Dashboard.widgets).selectinload(DashboardWidget.analysis),
                selectinload(Dashboard.filters),
                selectinload(Dashboard.dataset),
                selectinload(Dashboard.dataset_version),
            )
        )
        res = await db.execute(stmt)
        dashboard = res.scalars().first()
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dashboard '{dashboard_id}' not found.",
            )
        if dashboard.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this dashboard.",
            )
        return dashboard

    @classmethod
    async def generate_dashboard(
        cls,
        db: AsyncSession,
        user_id: str,
        request: DashboardGenerateRequest,
    ) -> DashboardResponse:
        """
        Executes end-to-end automated dashboard generation:
        1. Context discovery (profile + semantic layer)
        2. AI Dashboard Planner -> Structured Plan
        3. Deterministic plan validation
        4. Analytical execution graph
        5. Visualization recommendation & validation
        6. Grid layout calculation
        7. Persistence & provenance tracking
        """
        # 1. Authorization & dataset version verification
        dataset_res = await db.execute(
            select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == user_id)
        )
        dataset = dataset_res.scalars().first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{request.dataset_id}' not found or access denied.",
            )

        version_res = await db.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == request.dataset_version_id,
                DatasetVersion.dataset_id == request.dataset_id,
            )
        )
        version = version_res.scalars().first()
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset version '{request.dataset_version_id}' not found.",
            )

        profile_res = await db.execute(
            select(DatasetProfile)
            .where(DatasetProfile.dataset_version_id == version.id)
            .options(selectinload(DatasetProfile.column_profiles), selectinload(DatasetProfile.semantic_columns))
        )
        profile = profile_res.scalars().first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset version has not been profiled yet. Please run profiling first.",
            )

        sem_res = await db.execute(
            select(SemanticColumn).where(SemanticColumn.profile_id == profile.id)
        )
        semantic_cols = {sc.column_name: sc for sc in sem_res.scalars().all()}

        # 2. Plan generation
        plan: DashboardPlan = DashboardPlanner.generate_plan(
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            profile=profile,
            semantic_columns=semantic_cols,
            intent=request.intent,
            purpose=request.purpose,
            min_widgets=request.min_widgets,
            max_widgets=request.max_widgets,
        )

        # 3. Create Dashboard entity
        dashboard = Dashboard(
            name=plan.title,
            description=f"Automated dashboard for purpose: {plan.purpose}",
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            user_id=user_id,
            status=DashboardStatus.GENERATING.value,
            theme="default",
            layout_type="grid_12",
            layout_config={"columns": 12},
            metadata_json={
                "purpose": plan.purpose,
                "reasoning_summary": plan.reasoning_summary,
                "ai_generated": True,
            },
        )
        db.add(dashboard)
        await db.flush()

        # 4. Compute layout for planned widgets
        widget_dicts = [
            {
                "widget_type": w.widget_type.value,
                "title": w.title,
                "description": w.description,
                "operation": w.operation,
                "params": w.params,
                "preferred_chart_type": w.preferred_chart_type.value if w.preferred_chart_type else None,
                "grid_w": w.grid_w,
                "grid_h": w.grid_h,
            }
            for w in plan.widgets
        ]
        layout_widgets = DashboardLayoutEngine.compute_auto_layout(widget_dicts)

        # 5. Execute analytical jobs & visualization for each widget
        success_count = 0
        failed_count = 0

        for w_data in layout_widgets:
            op_name = w_data["operation"]
            params = w_data["params"]
            pref_chart = None
            if w_data.get("preferred_chart_type"):
                try:
                    pref_chart = ChartType(w_data["preferred_chart_type"])
                except ValueError:
                    pref_chart = None

            try:
                # Execute deterministic analytics tool
                job = await cls._execute_analytical_job(
                    db=db,
                    user_id=user_id,
                    dataset_id=dataset.id,
                    dataset_version_id=version.id,
                    operation=op_name,
                    params=params,
                )

                # Recommend and validate visualization
                rec_spec = cls._get_visualization_for_job(
                    job=job,
                    preferred_chart_type=pref_chart,
                    intent=w_data.get("title"),
                )

                widget = DashboardWidget(
                    dashboard_id=dashboard.id,
                    analysis_id=job.id,
                    widget_type=w_data["widget_type"],
                    title=w_data["title"],
                    description=w_data.get("description"),
                    chart_spec_json=rec_spec.model_dump(mode="json"),
                    grid_x=w_data["grid_x"],
                    grid_y=w_data["grid_y"],
                    grid_w=w_data["grid_w"],
                    grid_h=w_data["grid_h"],
                    metadata_json={"status": "READY"},
                )
                db.add(widget)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to generate widget '{w_data['title']}': {e}")
                failed_count += 1
                widget = DashboardWidget(
                    dashboard_id=dashboard.id,
                    analysis_id=None,
                    widget_type=w_data["widget_type"],
                    title=w_data["title"],
                    description=w_data.get("description"),
                    chart_spec_json={},
                    grid_x=w_data["grid_x"],
                    grid_y=w_data["grid_y"],
                    grid_w=w_data["grid_w"],
                    grid_h=w_data["grid_h"],
                    metadata_json={"status": "FAILED", "error": str(e)},
                )
                db.add(widget)

        # 6. Add default filters from plan
        for filter_col in plan.suggested_filters:
            sem_col = semantic_cols.get(filter_col)
            f_type = "categorical"
            if sem_col and (sem_col.is_temporal or sem_col.inferred_role in [SemanticRole.DATE, SemanticRole.DATETIME]):
                f_type = "temporal"
            elif sem_col and (sem_col.is_measure or sem_col.inferred_role == SemanticRole.MEASURE):
                f_type = "numeric"

            db_filter = DashboardFilter(
                dashboard_id=dashboard.id,
                column_name=filter_col,
                display_name=filter_col.replace("_", " ").title(),
                filter_type=f_type,
                operator="eq" if f_type == "categorical" else "between",
                current_value=None,
                allowed_values=None,
                scope="global",
                target_widget_ids=[],
            )
            db.add(db_filter)

        # 7. Update dashboard final status
        if failed_count == 0:
            dashboard.status = DashboardStatus.READY.value
        elif success_count > 0:
            dashboard.status = DashboardStatus.PARTIAL.value
        else:
            dashboard.status = DashboardStatus.FAILED.value

        await db.commit()
        return await cls.get_dashboard(db, user_id, dashboard.id)

    @classmethod
    async def list_dashboards(
        cls,
        db: AsyncSession,
        user_id: str,
        dataset_id: Optional[str] = None,
    ) -> List[DashboardResponse]:
        """Lists all dashboards owned by user."""
        stmt = (
            select(Dashboard)
            .where(Dashboard.user_id == user_id)
            .options(
                selectinload(Dashboard.widgets).selectinload(DashboardWidget.analysis),
                selectinload(Dashboard.filters),
                selectinload(Dashboard.dataset),
                selectinload(Dashboard.dataset_version),
            )
        )
        if dataset_id:
            stmt = stmt.where(Dashboard.dataset_id == dataset_id)
        stmt = stmt.order_by(Dashboard.updated_at.desc())
        res = await db.execute(stmt)
        dashboards = res.scalars().all()
        return [cls._format_dashboard_response(d) for d in dashboards]

    @classmethod
    async def get_dashboard(cls, db: AsyncSession, user_id: str, dashboard_id: str) -> DashboardResponse:
        """Retrieves single dashboard with enriched widget data."""
        dashboard = await cls.get_dashboard_entity(db, user_id, dashboard_id)
        return cls._format_dashboard_response(dashboard)

    @classmethod
    async def create_dashboard(
        cls,
        db: AsyncSession,
        user_id: str,
        request: DashboardCreateRequest,
    ) -> DashboardResponse:
        """Creates an empty dashboard container."""
        ds_res = await db.execute(
            select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == user_id)
        )
        dataset = ds_res.scalars().first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found.",
            )

        dashboard = Dashboard(
            name=request.name,
            description=request.description,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            user_id=user_id,
            status=DashboardStatus.READY.value,
            theme=request.theme,
            layout_type="grid_12",
            layout_config={"columns": 12},
            metadata_json={},
        )
        db.add(dashboard)
        await db.commit()
        return await cls.get_dashboard(db, user_id, dashboard.id)

    @classmethod
    async def update_dashboard(
        cls,
        db: AsyncSession,
        user_id: str,
        dashboard_id: str,
        request: DashboardUpdateRequest,
    ) -> DashboardResponse:
        """Updates dashboard metadata."""
        dashboard = await cls.get_dashboard_entity(db, user_id, dashboard_id)
        if request.name is not None:
            dashboard.name = request.name
        if request.description is not None:
            dashboard.description = request.description
        if request.theme is not None:
            dashboard.theme = request.theme

        await db.commit()
        return await cls.get_dashboard(db, user_id, dashboard.id)

    @classmethod
    async def delete_dashboard(cls, db: AsyncSession, user_id: str, dashboard_id: str) -> bool:
        """Deletes dashboard and associated widgets."""
        dashboard = await cls.get_dashboard_entity(db, user_id, dashboard_id)
        await db.delete(dashboard)
        await db.commit()
        return True

    @classmethod
    async def duplicate_dashboard(
        cls,
        db: AsyncSession,
        user_id: str,
        dashboard_id: str,
    ) -> DashboardResponse:
        """Creates an exact clone of an existing dashboard."""
        orig = await cls.get_dashboard_entity(db, user_id, dashboard_id)
        cloned = Dashboard(
            name=f"{orig.name} (Copy)",
            description=orig.description,
            dataset_id=orig.dataset_id,
            dataset_version_id=orig.dataset_version_id,
            user_id=user_id,
            status=orig.status,
            theme=orig.theme,
            layout_type=orig.layout_type,
            layout_config=copy.deepcopy(orig.layout_config),
            metadata_json=copy.deepcopy(orig.metadata_json),
        )
        db.add(cloned)
        await db.flush()

        for w in orig.widgets:
            cloned_w = DashboardWidget(
                dashboard_id=cloned.id,
                analysis_id=w.analysis_id,
                widget_type=w.widget_type,
                title=w.title,
                description=w.description,
                chart_spec_json=copy.deepcopy(w.chart_spec_json),
                grid_x=w.grid_x,
                grid_y=w.grid_y,
                grid_w=w.grid_w,
                grid_h=w.grid_h,
                metadata_json=copy.deepcopy(w.metadata_json),
            )
            db.add(cloned_w)

        for f in orig.filters:
            cloned_f = DashboardFilter(
                dashboard_id=cloned.id,
                column_name=f.column_name,
                display_name=f.display_name,
                filter_type=f.filter_type,
                operator=f.operator,
                current_value=copy.deepcopy(f.current_value),
                allowed_values=copy.deepcopy(f.allowed_values),
                scope=f.scope,
                target_widget_ids=copy.deepcopy(f.target_widget_ids),
            )
            db.add(cloned_f)

        await db.commit()
        return await cls.get_dashboard(db, user_id, cloned.id)

    @classmethod
    async def apply_patches(
        cls,
        db: AsyncSession,
        user_id: str,
        dashboard_id: str,
        patches: List[DashboardPatch],
    ) -> DashboardResponse:
        """
        Applies structured atomic modifications to a dashboard.
        """
        dashboard = await cls.get_dashboard_entity(db, user_id, dashboard_id)

        prof_res = await db.execute(
            select(DatasetProfile)
            .where(DatasetProfile.dataset_version_id == dashboard.dataset_version_id)
            .options(selectinload(DatasetProfile.column_profiles))
        )
        profile = prof_res.scalars().first()
        semantic_cols: Dict[str, SemanticColumn] = {}
        if profile:
            sem_res = await db.execute(
                select(SemanticColumn).where(SemanticColumn.profile_id == profile.id)
            )
            semantic_cols = {sc.column_name: sc for sc in sem_res.scalars().all()}

        for patch in patches:
            is_valid, errors = DashboardPatchValidator.validate_patch(
                patch, dashboard, profile, semantic_cols
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Patch error: {'; '.join(errors)}",
                )

            if patch.op == PatchOp.RENAME_DASHBOARD:
                dashboard.name = patch.params["name"]

            elif patch.op == PatchOp.REMOVE_WIDGET:
                w_to_remove = next((w for w in dashboard.widgets if w.id == patch.widget_id), None)
                if w_to_remove:
                    dashboard.widgets.remove(w_to_remove)
                    await db.delete(w_to_remove)
                    await db.flush()
                    remaining = [
                        {
                            "id": w.id,
                            "grid_x": w.grid_x,
                            "grid_y": w.grid_y,
                            "grid_w": w.grid_w,
                            "grid_h": w.grid_h,
                        }
                        for w in dashboard.widgets
                    ]
                    compacted = DashboardLayoutEngine.reflow_compact(remaining)
                    compact_map = {c["id"]: c for c in compacted}
                    for w in dashboard.widgets:
                        if w.id in compact_map:
                            w.grid_x = compact_map[w.id]["grid_x"]
                            w.grid_y = compact_map[w.id]["grid_y"]
                            w.grid_w = compact_map[w.id]["grid_w"]
                            w.grid_h = compact_map[w.id]["grid_h"]

            elif patch.op in [PatchOp.MOVE_WIDGET, PatchOp.RESIZE_WIDGET]:
                target_w = next((w for w in dashboard.widgets if w.id == patch.widget_id), None)
                if target_w:
                    if "grid_x" in patch.params:
                        target_w.grid_x = int(patch.params["grid_x"])
                    if "grid_y" in patch.params:
                        target_w.grid_y = int(patch.params["grid_y"])
                    if "grid_w" in patch.params:
                        target_w.grid_w = int(patch.params["grid_w"])
                    if "grid_h" in patch.params:
                        target_w.grid_h = int(patch.params["grid_h"])

            elif patch.op == PatchOp.CHANGE_CHART:
                target_w = next((w for w in dashboard.widgets if w.id == patch.widget_id), None)
                if target_w and target_w.analysis_id:
                    new_type = ChartType(patch.params["chart_type"])
                    job_res = await db.execute(
                        select(AnalysisJob).where(AnalysisJob.id == target_w.analysis_id)
                    )
                    job = job_res.scalars().first()
                    if job:
                        new_spec = cls._get_visualization_for_job(
                            job=job,
                            preferred_chart_type=new_type,
                            intent=target_w.title,
                        )
                        target_w.chart_spec_json = new_spec.model_dump(mode="json")

            elif patch.op == PatchOp.ADD_WIDGET:
                w_dict = patch.params.get("widget", {})
                op_name = w_dict.get("operation", "describe_dataset")
                params = w_dict.get("params", {})
                title = w_dict.get("title", "New Analysis")
                pref_chart = None
                if w_dict.get("preferred_chart_type"):
                    try:
                        pref_chart = ChartType(w_dict["preferred_chart_type"])
                    except ValueError:
                        pref_chart = None

                job = await cls._execute_analytical_job(
                    db=db,
                    user_id=user_id,
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                    operation=op_name,
                    params=params,
                )
                rec_spec = cls._get_visualization_for_job(
                    job=job,
                    preferred_chart_type=pref_chart,
                    intent=title,
                )

                current_widgets = [
                    {
                        "widget_type": w.widget_type,
                        "grid_w": w.grid_w,
                        "grid_h": w.grid_h,
                        "grid_x": w.grid_x,
                        "grid_y": w.grid_y,
                    }
                    for w in dashboard.widgets
                ]
                new_w_dict = {
                    "widget_type": w_dict.get("widget_type", "chart"),
                    "grid_w": w_dict.get("grid_w", 6),
                    "grid_h": w_dict.get("grid_h", 4),
                }
                placed = DashboardLayoutEngine.compute_auto_layout(current_widgets + [new_w_dict])
                last_placed = placed[-1]

                new_widget = DashboardWidget(
                    dashboard_id=dashboard.id,
                    analysis_id=job.id,
                    widget_type=w_dict.get("widget_type", "chart"),
                    title=title,
                    description=w_dict.get("description"),
                    chart_spec_json=rec_spec.model_dump(mode="json"),
                    grid_x=last_placed["grid_x"],
                    grid_y=last_placed["grid_y"],
                    grid_w=last_placed["grid_w"],
                    grid_h=last_placed["grid_h"],
                    metadata_json={"status": "READY"},
                )
                dashboard.widgets.append(new_widget)
                await db.flush()

            elif patch.op == PatchOp.CHANGE_FILTER:
                f_col = patch.params.get("column_name")
                val = patch.params.get("value")
                existing_f = next((f for f in dashboard.filters if f.column_name == f_col), None)
                if existing_f:
                    existing_f.current_value = val
                else:
                    new_f = DashboardFilter(
                        dashboard_id=dashboard.id,
                        column_name=f_col,
                        display_name=f_col.replace("_", " ").title(),
                        filter_type=patch.params.get("filter_type", "categorical"),
                        operator=patch.params.get("operator", "eq"),
                        current_value=val,
                        scope="global",
                    )
                    dashboard.filters.append(new_f)
                    await db.flush()

        await db.commit()
        return await cls.get_dashboard(db, user_id, dashboard.id)

    @classmethod
    async def refresh_dashboard(
        cls,
        db: AsyncSession,
        user_id: str,
        dashboard_id: str,
        filter_overrides: Optional[Dict[str, Any]] = None,
    ) -> DashboardResponse:
        """
        Re-executes all analytical jobs with applied filters.
        """
        dashboard = await cls.get_dashboard_entity(db, user_id, dashboard_id)

        active_filters: Dict[str, Any] = {}
        for f in dashboard.filters:
            if f.current_value is not None:
                active_filters[f.column_name] = f.current_value
        if filter_overrides:
            active_filters.update(filter_overrides)

        for widget in dashboard.widgets:
            if not widget.analysis_id:
                continue

            orig_res = await db.execute(
                select(AnalysisJob).where(AnalysisJob.id == widget.analysis_id)
            )
            orig_job = orig_res.scalars().first()

            if not orig_job:
                continue

            job_params = copy.deepcopy(orig_job.parameters_json or {})
            filter_conds = None
            if active_filters:
                filter_conds = []
                for col_name, val in active_filters.items():
                    filter_conds.append({
                        "column": col_name,
                        "operator": "eq" if not isinstance(val, list) else "in",
                        "value": val,
                    })

            try:
                new_job = await cls._execute_analytical_job(
                    db=db,
                    user_id=user_id,
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                    operation=orig_job.operation,
                    params=job_params,
                    filters=filter_conds,
                )
                widget.analysis_id = new_job.id

                curr_spec = widget.chart_spec_json
                if curr_spec and "provenance" in curr_spec:
                    curr_spec["provenance"]["analysis_id"] = new_job.id
                    widget.chart_spec_json = curr_spec
            except Exception as e:
                logger.error(f"Failed to refresh widget {widget.id}: {e}")

        await db.commit()
        return await cls.get_dashboard(db, user_id, dashboard.id)

    @classmethod
    def calculate_quality_score(cls, dashboard: Dashboard) -> DashboardQualityReport:
        """
        Calculates an explainable quality score (0-100).
        """
        total_widgets = len(dashboard.widgets)
        if total_widgets == 0:
            return DashboardQualityReport(
                overall_score=0.0,
                valid_widget_ratio=0.0,
                visual_diversity_score=0.0,
                redundancy_penalty=0.0,
                data_coverage_score=0.0,
                breakdown={"message": "Empty dashboard"},
            )

        valid_widgets = sum(1 for w in dashboard.widgets if w.analysis_id is not None)
        valid_ratio = valid_widgets / total_widgets

        chart_types = set()
        operations = set()
        signatures = set()
        duplicates = 0

        for w in dashboard.widgets:
            spec = w.chart_spec_json or {}
            ctype = spec.get("chart_type")
            if ctype:
                chart_types.add(ctype)
            if w.analysis and w.analysis.operation:
                operations.add(w.analysis.operation)
                sig = f"{w.analysis.operation}:{w.analysis.parameters_json}"
                if sig in signatures:
                    duplicates += 1
                signatures.add(sig)

        diversity_score = min(1.0, len(chart_types) / 3.0)
        redundancy_pen = min(1.0, duplicates / max(1, total_widgets))
        coverage_score = min(1.0, len(operations) / 2.0)

        raw_score = (
            (valid_ratio * 40.0)
            + (diversity_score * 25.0)
            + (coverage_score * 35.0)
            - (redundancy_pen * 20.0)
        )
        final_score = max(0.0, min(100.0, raw_score))

        return DashboardQualityReport(
            overall_score=round(final_score, 1),
            valid_widget_ratio=round(valid_ratio, 2),
            visual_diversity_score=round(diversity_score, 2),
            redundancy_penalty=round(redundancy_pen, 2),
            data_coverage_score=round(coverage_score, 2),
            breakdown={
                "total_widgets": total_widgets,
                "valid_widgets": valid_widgets,
                "chart_types": list(chart_types),
                "distinct_operations": list(operations),
                "duplicate_count": duplicates,
            },
        )

    @classmethod
    def _format_dashboard_response(cls, dashboard: Dashboard) -> DashboardResponse:
        """Formats Dashboard DB entity into full DashboardResponse with widget data."""
        widget_responses: List[DashboardWidgetResponse] = []
        for w in dashboard.widgets:
            chart_spec = None
            if w.chart_spec_json:
                try:
                    chart_spec = VisualizationSpec(**w.chart_spec_json)
                except Exception:
                    chart_spec = None

            analysis_status = None
            result_data = None
            if w.analysis:
                analysis_status = w.analysis.status.value if hasattr(w.analysis.status, "value") else str(w.analysis.status)
                result_data = w.analysis.result_json

            widget_responses.append(
                DashboardWidgetResponse(
                    id=w.id,
                    dashboard_id=w.dashboard_id,
                    analysis_id=w.analysis_id,
                    widget_type=w.widget_type,
                    title=w.title,
                    description=w.description,
                    chart_spec=chart_spec,
                    grid_x=w.grid_x,
                    grid_y=w.grid_y,
                    grid_w=w.grid_w,
                    grid_h=w.grid_h,
                    metadata=w.metadata_json or {},
                    analysis_status=analysis_status,
                    result_data=result_data,
                    created_at=w.created_at,
                    updated_at=w.updated_at,
                )
            )

        filter_responses = [
            DashboardFilterResponse(
                id=f.id,
                dashboard_id=f.dashboard_id,
                column_name=f.column_name,
                display_name=f.display_name,
                filter_type=f.filter_type,
                operator=f.operator,
                current_value=f.current_value,
                allowed_values=f.allowed_values,
                scope=f.scope,
                target_widget_ids=f.target_widget_ids or [],
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in dashboard.filters
        ]

        dataset_name = dashboard.dataset.name if dashboard.dataset else None
        version_num = dashboard.dataset_version.version_number if dashboard.dataset_version else None

        return DashboardResponse(
            id=dashboard.id,
            name=dashboard.name,
            description=dashboard.description,
            dataset_id=dashboard.dataset_id,
            dataset_name=dataset_name,
            dataset_version_id=dashboard.dataset_version_id,
            dataset_version_num=version_num,
            user_id=dashboard.user_id,
            status=dashboard.status,
            theme=dashboard.theme,
            layout_type=dashboard.layout_type,
            layout_config=dashboard.layout_config or {},
            metadata=dashboard.metadata_json or {},
            widgets=widget_responses,
            filters=filter_responses,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )
