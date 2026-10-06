"""Safe Federated Query Planner & Execution Engine with Duplication Protection."""

import re
import time
import uuid
from typing import Any, Dict, List, Tuple

from app.analytics.duckdb.manager import DuckDBManager
from app.database.models.dataset import DatasetVersion
from app.database.models.federation import DatasetRelationship
from app.datasets.storage import get_storage_provider
from app.federation.graph import FederationGraph
from app.federation.schemas import (
    FederatedAnalysisRequest,
    FederatedAnalysisResponse,
)


class FederatedPlannerError(Exception):
    """Raised when a federated query cannot be safely planned or violates boundaries."""

    pass


class FederatedQueryPlanner:
    """Plans and executes deterministic, multi-dataset analytical queries in DuckDB."""

    MAX_DATASETS_PER_ANALYSIS = 5
    MAX_RESULT_ROWS = 10000
    DEFAULT_TIMEOUT_SECONDS = 30.0

    @staticmethod
    def _sanitize_ident(ident: str) -> str:
        """Sanitize SQL identifiers to prevent injection."""
        clean = re.sub(r'[^a-zA-Z0-9_"]', "", ident)
        if clean.startswith('"') and clean.endswith('"'):
            return clean
        return f'"{clean}"'

    @classmethod
    def plan_and_execute(
        cls,
        duckdb_manager: DuckDBManager,
        request: FederatedAnalysisRequest,
        dataset_versions: List[DatasetVersion],
        validated_relationships: List[DatasetRelationship],
    ) -> FederatedAnalysisResponse:
        """Construct safe federated SQL, execute in DuckDB, and return validated results with full provenance."""
        start_time = time.perf_counter()
        analysis_id = str(uuid.uuid4())

        if len(request.dataset_version_ids) > cls.MAX_DATASETS_PER_ANALYSIS:
            raise FederatedPlannerError(
                f"Federated analysis exceeds max allowed datasets limit ({cls.MAX_DATASETS_PER_ANALYSIS})."
            )

        # 1. Map dataset version IDs to DatasetVersion models
        version_map = {dv.id: dv for dv in dataset_versions}
        dataset_to_version = {dv.dataset_id: dv for dv in dataset_versions}
        dataset_ids = list(dataset_to_version.keys())

        for v_id in request.dataset_version_ids:
            if v_id not in version_map:
                raise FederatedPlannerError(f"Dataset version {v_id} not found or unauthorized.")

        # 2. Register all participating datasets into DuckDB
        storage = get_storage_provider()
        table_aliases: Dict[str, str] = {}  # dataset_id -> alias ("t0", "t1")
        tbl_names: Dict[str, str] = {}  # dataset_id -> duckdb table name

        for idx, dv in enumerate(dataset_versions):
            f_path = str(getattr(dv, "file_path", None) or storage.get_file_path(dv.storage_reference))
            t_name = duckdb_manager.register_dataset(
                dataset_version_id=dv.id,
                file_path=f_path,
                file_format=dv.file_format.value if hasattr(dv.file_format, "value") else str(dv.file_format),
            )
            table_aliases[dv.dataset_id] = f"t{idx}"
            tbl_names[dv.dataset_id] = t_name

        # 3. Pathfinding across relationship graph
        graph = FederationGraph(validated_relationships)
        root_dataset_id, join_hops, graph_warnings = graph.resolve_join_tree(dataset_ids)

        # 4. Parse Dimensions & Measures with column resolution
        select_clauses: List[str] = []
        group_by_clauses: List[str] = []
        column_names: List[str] = []

        def resolve_column_ref(field_spec: str) -> Tuple[str, str, str]:
            """Resolves 'Customers.segment' or 'segment' to (table_alias, clean_column_name, display_alias)."""
            parts = field_spec.split(".", 1)
            if len(parts) == 2:
                prefix, col = parts
                # Find matching dataset by dataset_id or dataset name
                matching_id = None
                for d_id, dv in dataset_to_version.items():
                    if prefix.lower() in [d_id.lower(), getattr(dv.dataset, "name", "").lower(), dv.id.lower()]:
                        matching_id = d_id
                        break
                if not matching_id:
                    # Default to first dataset matching prefix if prefix is valid
                    matching_id = dataset_ids[0]
                alias = table_aliases[matching_id]
                clean_col = cls._sanitize_ident(col)
                display_name = f"{prefix}_{col}".replace(".", "_").replace(" ", "_")
                return alias, clean_col, display_name
            else:
                col = parts[0]
                alias = table_aliases[root_dataset_id]
                clean_col = cls._sanitize_ident(col)
                return alias, clean_col, col

        # Add dimensions
        for dim in request.dimensions:
            alias, clean_col, display_name = resolve_column_ref(dim)
            expr = f"{alias}.{clean_col}"
            select_clauses.append(f"{expr} AS {cls._sanitize_ident(display_name)}")
            group_by_clauses.append(expr)
            column_names.append(display_name)

        # Add measures
        for idx, meas in enumerate(request.measures):
            alias, clean_col, default_name = resolve_column_ref(meas.field)
            display_name = meas.alias or f"{meas.agg.lower()}_{default_name}"
            agg_func = meas.agg.upper()
            if agg_func == "COUNT_DISTINCT":
                expr = f"COUNT(DISTINCT {alias}.{clean_col})"
            else:
                expr = f"{agg_func}({alias}.{clean_col})"
            select_clauses.append(f"{expr} AS {cls._sanitize_ident(display_name)}")
            column_names.append(display_name)

        # 5. Build FROM and JOIN clauses
        root_tbl = tbl_names[root_dataset_id]
        root_alias = table_aliases[root_dataset_id]
        from_clause = f"FROM {root_tbl} {root_alias}"

        join_clauses: List[str] = []
        relationships_used_info: List[Dict[str, Any]] = []

        for hop in join_hops:
            target_alias = table_aliases[hop.to_dataset_id]
            source_alias = table_aliases[hop.from_dataset_id]
            target_tbl = tbl_names[hop.to_dataset_id]

            s_col = cls._sanitize_ident(hop.from_field)
            t_col = cls._sanitize_ident(hop.to_field)

            # Cast to VARCHAR for safe mixed-type join without error
            join_cond = f"CAST({source_alias}.{s_col} AS VARCHAR) = CAST({target_alias}.{t_col} AS VARCHAR)"
            join_clauses.append(f"LEFT JOIN {target_tbl} {target_alias} ON {join_cond}")

            relationships_used_info.append(
                {
                    "relationship_id": hop.relationship.id,
                    "from_dataset": hop.from_dataset_id,
                    "to_dataset": hop.to_dataset_id,
                    "from_field": hop.from_field,
                    "to_field": hop.to_field,
                    "type": hop.relationship.relationship_type.value
                    if hasattr(hop.relationship.relationship_type, "value")
                    else str(hop.relationship.relationship_type),
                }
            )

        # 6. Build WHERE clause for filters
        where_clauses: List[str] = []
        if request.filters:
            for f in request.filters:
                f_alias, f_col, _ = resolve_column_ref(f.field)
                op = f.operator.upper()
                val = f.value

                if op == "IS_NULL":
                    where_clauses.append(f"{f_alias}.{f_col} IS NULL")
                elif op == "IS_NOT_NULL":
                    where_clauses.append(f"{f_alias}.{f_col} IS NOT NULL")
                elif op == "IN" and isinstance(val, (list, tuple)):
                    formatted_vals = ", ".join(f"'{str(v).replace("'", "''")}'" for v in val)
                    where_clauses.append(f"{f_alias}.{f_col} IN ({formatted_vals})")
                elif op == "LIKE":
                    where_clauses.append(f"CAST({f_alias}.{f_col} AS VARCHAR) ILIKE '%{str(val).replace("'", "''")}%'")
                else:
                    if isinstance(val, (int, float)):
                        where_clauses.append(f"{f_alias}.{f_col} {op} {val}")
                    else:
                        where_clauses.append(f"{f_alias}.{f_col} {op} '{str(val).replace("'", "''")}'")

        # 7. Assemble SQL query
        sql_parts = [
            f"SELECT {', '.join(select_clauses)}",
            from_clause,
        ]
        if join_clauses:
            sql_parts.extend(join_clauses)
        if where_clauses:
            sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        if group_by_clauses:
            sql_parts.append(f"GROUP BY {', '.join(group_by_clauses)}")

        # Order By
        if request.sort_by:
            sort_dir = "DESC" if (request.sort_order or "").upper() == "DESC" else "ASC"
            sql_parts.append(f"ORDER BY {cls._sanitize_ident(request.sort_by)} {sort_dir}")
        elif len(column_names) > 0:
            # Default order by first measure if available
            default_sort = column_names[-1]
            sql_parts.append(f"ORDER BY {cls._sanitize_ident(default_sort)} DESC")

        # Limit
        limit = min(request.limit or 100, cls.MAX_RESULT_ROWS)
        sql_parts.append(f"LIMIT {limit}")

        final_sql = "\n".join(sql_parts)

        # 8. Execute in DuckDB
        exec_res = duckdb_manager.execute_federated_query(final_sql, timeout_seconds=cls.DEFAULT_TIMEOUT_SECONDS)
        exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Build join path description
        hops_desc = " -> ".join(
            [f"{h.from_dataset_id}.{h.from_field}={h.to_dataset_id}.{h.to_field}" for h in join_hops]
        )
        join_path_desc = f"Root: {root_dataset_id} | Hops: {hops_desc or 'Single dataset'}"

        cols = exec_res.get("columns", column_names)
        raw_rows = exec_res.get("rows", [])
        dict_rows = [dict(zip(cols, row)) if isinstance(row, (tuple, list)) else row for row in raw_rows]

        return FederatedAnalysisResponse(
            analysis_id=analysis_id,
            columns=cols,
            rows=dict_rows,
            row_count=len(dict_rows),
            execution_time_ms=exec_time_ms,
            datasets_involved=[
                {"dataset_id": dv.dataset_id, "dataset_version_id": dv.id, "version_num": dv.version_number}
                for dv in dataset_versions
            ],
            relationships_used=relationships_used_info,
            join_path_description=join_path_desc,
            provenance={
                "analysis_id": analysis_id,
                "root_dataset_id": root_dataset_id,
                "dataset_versions": [dv.id for dv in dataset_versions],
                "sql_query": final_sql,
                "execution_time_ms": exec_time_ms,
                "relationships_count": len(join_hops),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            warnings=graph_warnings,
        )
