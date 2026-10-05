"""Root-Cause and Dimension Contribution Analysis for detected anomalies."""

from typing import List, Optional

import pandas as pd

from app.analytics.duckdb.manager import DuckDBManager
from app.anomalies.schemas import RootCauseContributor


class RootCauseAnalyzer:
    """Performs deterministic dimensional breakdown to identify subgroups accounting for an anomaly."""

    @classmethod
    def analyze_contribution(
        cls,
        duckdb_manager: DuckDBManager,
        table_name: str,
        metric_col: str,
        time_col: Optional[str],
        anomalous_period: str,
        dimension_col: str,
        overall_observed: float,
        overall_expected: float,
        max_contributors: int = 5,
    ) -> List[RootCauseContributor]:
        """Compute percentage contribution of each subgroup within dimension_col to the period's anomaly."""
        clean_metric = f'"{metric_col.replace('"', '""')}"'
        clean_dim = f'"{dimension_col.replace('"', '""')}"'

        # Query group breakdown in the anomalous period
        where_clause = ""
        if time_col:
            clean_time = f'"{time_col.replace('"', '""')}"'
            where_clause = f"WHERE TRY_CAST({clean_time} AS VARCHAR) LIKE '{anomalous_period}%' OR {clean_time} = '{anomalous_period}'"

        sql_current = f"""
        SELECT
            {clean_dim} AS grp,
            SUM(TRY_CAST({clean_metric} AS DOUBLE)) AS observed_sum
        FROM {table_name}
        {where_clause}
        GROUP BY {clean_dim}
        HAVING grp IS NOT NULL
        """

        # Query historical baseline for each group
        sql_baseline = f"""
        SELECT
            {clean_dim} AS grp,
            AVG(TRY_CAST({clean_metric} AS DOUBLE)) AS baseline_avg
        FROM {table_name}
        GROUP BY {clean_dim}
        HAVING grp IS NOT NULL
        """

        try:
            res_curr = duckdb_manager.execute_federated_query(sql_current, max_rows=100)
            res_base = duckdb_manager.execute_federated_query(sql_baseline, max_rows=100)

            rows_curr = res_curr.get("rows", [])
            rows_base = res_base.get("rows", [])

            if not rows_curr:
                return []

            df_curr = pd.DataFrame(rows_curr, columns=["grp", "observed"]).set_index("grp")
            df_base = pd.DataFrame(rows_base, columns=["grp", "baseline"]).set_index("grp")

            df_joined = df_curr.join(df_base, how="outer").fillna(0.0)
            df_joined["delta"] = df_joined["observed"] - df_joined["baseline"]
            df_joined["abs_delta"] = df_joined["delta"].abs()

            total_abs_delta = float(df_joined["abs_delta"].sum()) or 1.0

            df_joined["contribution_pct"] = (df_joined["abs_delta"] / total_abs_delta) * 100.0
            df_sorted = df_joined.sort_values(by="abs_delta", ascending=False).head(max_contributors)

            contributors: List[RootCauseContributor] = []
            for grp_val, row in df_sorted.iterrows():
                pct = round(float(row["contribution_pct"]), 1)
                delta_val = round(float(row["delta"]), 2)
                obs_val = round(float(row["observed"]), 2)
                base_val = round(float(row["baseline"]), 2)

                direction = "decline" if delta_val < 0 else "surge"
                narrative = (
                    f"{dimension_col.capitalize()} '{grp_val}' accounted for {pct}% of the variation "
                    f"({direction} of {abs(delta_val):.2f} relative to baseline {base_val:.2f})."
                )

                contributors.append(
                    RootCauseContributor(
                        dimension_field=dimension_col,
                        dimension_value=str(grp_val),
                        observed_value=obs_val,
                        baseline_value=base_val,
                        delta=delta_val,
                        contribution_pct=pct,
                        narrative=narrative,
                    )
                )

            return contributors
        except Exception:
            return []
