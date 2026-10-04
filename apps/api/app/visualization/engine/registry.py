"""Chart Registry defining supported chart types, data type constraints, and cardinality rules."""

from typing import Dict, List, Optional, Set

from app.visualization.schemas import AxisDataType, ChartType, ChartTypeMetadata


class ChartDefinition:
    """Descriptor defining semantic rules and capabilities for a specific chart type."""

    def __init__(
        self,
        chart_type: ChartType,
        label: str,
        description: str,
        allowed_x_types: Set[AxisDataType],
        allowed_y_types: Set[AxisDataType],
        required_axes: List[str],
        max_cardinality: Optional[int] = None,
        min_values: Optional[int] = None,
        supports_series: bool = False,
        disallow_negative: bool = False,
    ) -> None:
        self.chart_type = chart_type
        self.label = label
        self.description = description
        self.allowed_x_types = allowed_x_types
        self.allowed_y_types = allowed_y_types
        self.required_axes = required_axes
        self.max_cardinality = max_cardinality
        self.min_values = min_values
        self.supports_series = supports_series
        self.disallow_negative = disallow_negative

    def to_metadata(self) -> ChartTypeMetadata:
        return ChartTypeMetadata(
            chart_type=self.chart_type,
            label=self.label,
            description=self.description,
            required_axes=self.required_axes,
            max_cardinality=self.max_cardinality,
            min_values=self.min_values,
            supports_series=self.supports_series,
        )


class ChartRegistry:
    """Registry maintaining definitions and constraints for all supported chart types."""

    # Configurable Cardinality & Suitability Thresholds
    MAX_PIE_CATEGORIES = 6
    MAX_BAR_CATEGORIES = 20
    MIN_HISTOGRAM_VALUES = 10
    MAX_SCATTER_POINTS = 500

    def __init__(self) -> None:
        self._charts: Dict[ChartType, ChartDefinition] = {}
        self._register_default_charts()

    def register(self, definition: ChartDefinition) -> None:
        self._charts[definition.chart_type] = definition

    def get(self, chart_type: ChartType) -> Optional[ChartDefinition]:
        return self._charts.get(chart_type)

    def list_all(self) -> List[ChartTypeMetadata]:
        return [defn.to_metadata() for defn in self._charts.values()]

    def is_supported(self, chart_type: str) -> bool:
        try:
            ct = ChartType(chart_type)
            return ct in self._charts
        except ValueError:
            return False

    def _register_default_charts(self) -> None:
        # 1. Bar Chart (Vertical)
        self.register(
            ChartDefinition(
                chart_type=ChartType.BAR,
                label="Bar Chart",
                description="Categorical comparison with vertical bars",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.TEMPORAL, AxisDataType.BOOLEAN},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                max_cardinality=self.MAX_BAR_CATEGORIES,
                supports_series=True,
            )
        )

        # 2. Horizontal Bar Chart
        self.register(
            ChartDefinition(
                chart_type=ChartType.HORIZONTAL_BAR,
                label="Horizontal Bar Chart",
                description="Categorical comparison with horizontal bars for long labels or many categories",
                allowed_x_types={AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.CATEGORICAL, AxisDataType.TEMPORAL, AxisDataType.BOOLEAN},
                required_axes=["x_axis", "y_axis"],
                max_cardinality=self.MAX_BAR_CATEGORIES,
                supports_series=True,
            )
        )

        # 3. Line Chart
        self.register(
            ChartDefinition(
                chart_type=ChartType.LINE,
                label="Line Chart",
                description="Temporal trends and ordered continuous series",
                allowed_x_types={AxisDataType.TEMPORAL, AxisDataType.CATEGORICAL, AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                supports_series=True,
            )
        )

        # 4. Area Chart
        self.register(
            ChartDefinition(
                chart_type=ChartType.AREA,
                label="Area Chart",
                description="Volume and cumulative trends over time",
                allowed_x_types={AxisDataType.TEMPORAL, AxisDataType.CATEGORICAL},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                supports_series=True,
            )
        )

        # 5. Pie Chart
        self.register(
            ChartDefinition(
                chart_type=ChartType.PIE,
                label="Pie Chart",
                description="Part-to-whole composition with few categories (3 to 6)",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.BOOLEAN},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                max_cardinality=self.MAX_PIE_CATEGORIES,
                disallow_negative=True,
            )
        )

        # 6. Donut Chart
        self.register(
            ChartDefinition(
                chart_type=ChartType.DONUT,
                label="Donut Chart",
                description="Part-to-whole composition with center space for KPI",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.BOOLEAN},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                max_cardinality=self.MAX_PIE_CATEGORIES,
                disallow_negative=True,
            )
        )

        # 7. Scatter Plot
        self.register(
            ChartDefinition(
                chart_type=ChartType.SCATTER,
                label="Scatter Plot",
                description="Relationship and correlation between two numerical variables",
                allowed_x_types={AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                max_cardinality=self.MAX_SCATTER_POINTS,
                supports_series=True,
            )
        )

        # 8. Histogram
        self.register(
            ChartDefinition(
                chart_type=ChartType.HISTOGRAM,
                label="Histogram",
                description="Frequency distribution of a continuous numeric variable",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["x_axis", "y_axis"],
                min_values=self.MIN_HISTOGRAM_VALUES,
            )
        )

        # 9. Box Plot
        self.register(
            ChartDefinition(
                chart_type=ChartType.BOXPLOT,
                label="Box Plot",
                description="Five-number summary distribution, quartiles, and outliers",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=["y_axis"],
            )
        )

        # 10. KPI Metric Card
        self.register(
            ChartDefinition(
                chart_type=ChartType.KPI,
                label="KPI Metric Card",
                description="Single high-impact scalar metric",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.NUMERIC},
                allowed_y_types={AxisDataType.NUMERIC},
                required_axes=[],
                max_cardinality=1,
            )
        )

        # 11. Data Table Fallback
        self.register(
            ChartDefinition(
                chart_type=ChartType.TABLE,
                label="Data Table",
                description="Tabular presentation fallback for high-cardinality or multidimensional data",
                allowed_x_types={AxisDataType.CATEGORICAL, AxisDataType.TEMPORAL, AxisDataType.NUMERIC, AxisDataType.BOOLEAN},
                allowed_y_types={AxisDataType.CATEGORICAL, AxisDataType.TEMPORAL, AxisDataType.NUMERIC, AxisDataType.BOOLEAN},
                required_axes=[],
            )
        )


chart_registry = ChartRegistry()
