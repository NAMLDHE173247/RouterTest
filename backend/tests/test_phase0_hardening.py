import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.routing import RouteResponse
from app.services.evaluation_service import EvaluationService
from app.services.routing.base import RouterVersionService
from app.services.routing.rule_based_router_service import RuleBasedRouterService
from app.services.routing.routing_service import routing_service
from app.settings_store import SettingsStore
from app.services.dataset_service import dataset_service
from app.adapters.base import load_isolated_router


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "Rule_based_Router" / "rule_based_router_v2" / "router_experiment" / "data" / "test_router.jsonl"
V2_CORE_PATH = REPO_ROOT / "Rule_based_Router" / "rule_based_router_v2" / "router_experiment" / "src"
PHASE0_PREDICTIONS_PATH = REPO_ROOT / "Rule_based_Router" / "rule_based_router_v3" / "router_experiment" / "outputs" / "phase_0" / "v3_phase_0_predictions.jsonl"


class DummyService(RouterVersionService):
    def __init__(self, router_id="dummy", family="rule_based"):
        self.router_id = router_id
        self.router_name = router_id
        self.family = family
        self.version = "test"

    def route(self, question: str, history=None) -> RouteResponse:
        raise NotImplementedError


def test_registry_contains_rule_versions_and_metadata():
    assert {"rule_v0", "rule_v1", "rule_v2", "rule_v3"}.issubset(
        routing_service.get_available_router_ids()
    )
    metadata = {
        item["id"]: item
        for item in routing_service.get_available_routers()
    }
    assert metadata["rule_v3"]["family"] == "rule_based"
    assert metadata["rule_v3"]["version"] == "v3"


def test_registry_rejects_duplicate_id_and_invalid_family():
    registry = RuleBasedRouterService(services=[])
    registry.register(DummyService())
    with pytest.raises(ValueError, match="Duplicate router ID"):
        registry.register(DummyService())
    with pytest.raises(ValueError, match="Invalid Rule-based service family"):
        registry.register(DummyService(router_id="slm", family="slm"))


def test_frozen_phase0_artifact_matches_v2_per_sample():
    v2_route = load_isolated_router(str(V2_CORE_PATH))
    fields = (
        "primary_subject",
        "secondary_subjects",
        "intent",
        "target_slm",
        "need_clarification",
    )

    with DATASET_PATH.open(encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if line.strip()]
    with PHASE0_PREDICTIONS_PATH.open(encoding="utf-8") as file:
        snapshot = {
            record["id"]: record
            for record in (json.loads(line) for line in file if line.strip())
        }

    assert len(rows) == 300
    assert len(snapshot) == 300
    for row in rows:
        v2 = v2_route(question=row["question"], history=row.get("history", []))
        frozen_v3 = snapshot[row["id"]]["prediction"]
        assert {field: frozen_v3.get(field) for field in fields} == {
            field: v2.get(field) for field in fields
        }, f"Frozen Phase 0 mismatch at sample {row.get('id')}"


def test_v3_evaluator_writes_phase_specific_outputs(tmp_path):
    experiment_dir = REPO_ROOT / "Rule_based_Router" / "rule_based_router_v3" / "router_experiment"
    script = experiment_dir / "src" / "evaluate_rule_router.py"
    output_dir = tmp_path / "phase_0"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--phase",
            "phase_1",
            "--dataset",
            str(DATASET_PATH),
            "--output-dir",
            str(output_dir),
        ],
        cwd=experiment_dir,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (output_dir / "v3_phase_1_predictions.jsonl").exists()
    assert (output_dir / "v3_phase_1_errors.json").exists()
    metrics = json.loads((output_dir / "v3_phase_1_metrics.json").read_text(encoding="utf-8"))
    assert metrics["metadata"]["dataset_sha256"]
    assert metrics["metadata"]["config_sha256"]
    assert metrics["metadata"]["generated_at_utc"]
    assert not list(output_dir.glob("v2_*.json*"))


def test_evaluation_separates_core_and_full_exact(tmp_path, monkeypatch):
    response = routing_service.get_service("rule_v3").route("Tính vận tốc vật rơi tự do", [])
    decision = response.decision.model_dump()
    gold_secondary = ["math"] if not decision["secondary_subjects"] else []
    row = {
        "id": "metric_contract_1",
        "question": "Tính vận tốc vật rơi tự do",
        "history": [],
        "primary_subject": decision["primary_subject"],
        "secondary_subjects": gold_secondary,
        "intent": decision["intent"],
        "target_slm": decision["target_slm"],
        "need_clarification": decision["need_clarification"],
        "case_type": "single_turn",
    }
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    monkeypatch.setattr(dataset_service, "get_dataset_path", lambda _dataset_id: str(dataset_path))
    service = EvaluationService()
    service.RUNS_DIR = str(tmp_path / "runs")
    result = service.run_evaluation(["rule_v3"])
    metrics = result.metrics["rule_v3"]

    assert metrics.exact_match_accuracy == 1.0
    assert metrics.full_exact_match_accuracy == 0.0
    assert metrics.secondary_subject_exact_set_accuracy == 0.0
    assert metrics.metrics_by_case_type["single_turn"]["exact_match_accuracy"] == 1.0
    assert metrics.metrics_by_case_type["single_turn"]["full_exact_match_accuracy"] == 0.0


def test_evaluation_rejects_unknown_router_before_run():
    with pytest.raises(ValueError, match="Unknown router IDs: rule_v33"):
        EvaluationService().run_evaluation(["rule_v33"])


def test_qwen_metadata_is_unavailable_without_cached_health(monkeypatch):
    monkeypatch.setattr(SettingsStore, "_qwen_url", None)
    monkeypatch.setattr(SettingsStore, "_qwen_health", None)
    metadata = {
        item["id"]: item
        for item in routing_service.get_available_routers()
    }
    assert metadata["qwen_v0"]["status"] == "unavailable"
    assert metadata["qwen_v0"]["capabilities"]["requires_external_service"] is True


def test_canonical_and_legacy_routes_are_available():
    client = TestClient(app)
    payload = {
        "router_id": "rule_v3",
        "question": "Tính vận tốc vật rơi tự do",
        "history": [],
    }
    canonical = client.post("/api/v1/router/route", json=payload)
    legacy = client.post("/api/v1/route", json=payload)
    routers = client.get("/api/v1/router/routers")
    invalid_evaluation = client.post(
        "/api/v1/evaluations",
        json={"router_ids": ["rule_v33"]},
    )

    assert canonical.status_code == 200
    assert legacy.status_code == 200
    assert routers.status_code == 200
    assert invalid_evaluation.status_code == 400
    assert "rule_v33" in invalid_evaluation.json()["detail"]
    assert "rule_v3" in {item["id"] for item in routers.json()}
