"""Model Lineage and Prediction Provenance Graph Builder for Phase 16 MLOps."""

from typing import Any, Dict, List

from app.database.models.mlops import MLModelVersion


class ModelLineageEngine:
    """Constructs auditable DAG lineage graphs tracing dataset versions to deployments and predictions."""

    @staticmethod
    def build_lineage_graph(version: MLModelVersion) -> Dict[str, Any]:
        """Constructs nodes and directed edges illustrating the complete provenance of a model version."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # 1. Dataset Node
        ds_id = version.training_dataset_id or "dataset-unknown"
        ver_id = version.training_dataset_version_id or "v1"
        nodes.append(
            {
                "id": f"ds-{ds_id}",
                "node_type": "DATASET",
                "label": f"Dataset ({ds_id[:8]}...)",
                "details": {
                    "dataset_id": ds_id,
                    "version_id": ver_id,
                },
            }
        )

        # 2. Preprocessing & Feature Contract Node
        prep_id = f"prep-{version.id}"
        nodes.append(
            {
                "id": prep_id,
                "node_type": "PREPROCESSING",
                "label": f"Feature Pipeline ({version.preprocessing_version})",
                "details": {
                    "version": version.preprocessing_version,
                    "feature_count": len(version.feature_schema.get("features", {})),
                },
            }
        )
        edges.append(
            {
                "source": f"ds-{ds_id}",
                "target": prep_id,
                "relationship": "FEATURIZES",
            }
        )

        # 3. Model Version Node
        mv_id = f"model-{version.id}"
        model_name = version.model.name if version.model else "ML Model"
        nodes.append(
            {
                "id": mv_id,
                "node_type": "MODEL_VERSION",
                "label": f"{model_name} ({version.version})",
                "details": {
                    "version": version.version,
                    "checksum": version.checksum[:12] + "...",
                    "status": version.status.value if hasattr(version.status, "value") else str(version.status),
                    "metrics": version.metrics,
                },
            }
        )
        edges.append(
            {
                "source": prep_id,
                "target": mv_id,
                "relationship": "TRAINS_MODEL",
            }
        )

        # 4. Deployment Nodes
        for dep in getattr(version, "deployments", []):
            dep_id = f"dep-{dep.id}"
            nodes.append(
                {
                    "id": dep_id,
                    "node_type": "DEPLOYMENT",
                    "label": f"Deployment: {dep.environment.value if hasattr(dep.environment, 'value') else str(dep.environment)}",
                    "details": {
                        "environment": str(dep.environment),
                        "status": str(dep.status),
                        "deployed_at": str(dep.deployed_at),
                    },
                }
            )
            edges.append(
                {
                    "source": mv_id,
                    "target": dep_id,
                    "relationship": "DEPLOYS_TO",
                }
            )

        return {
            "model_version_id": version.id,
            "nodes": nodes,
            "edges": edges,
        }
