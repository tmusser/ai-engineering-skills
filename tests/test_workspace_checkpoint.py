from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "workspace-checkpoint" / "SKILL.md"


def test_workspace_checkpoint_is_ephemeral_and_source_backed() -> None:
    text = SKILL.read_text(encoding="utf-8")

    for heading in (
        "## Purpose",
        "## When to use",
        "## Inputs",
        "## Workflow",
        "## Outputs",
        "## Stop conditions",
        "## Anti-patterns",
    ):
        assert heading in text

    assert "Reactivate, do not introspect." in text
    assert "Checkpoint, do not summarize." in text
    assert "Do not create `WORKSPACE.md`" in text
    assert "A checkpoint is a working projection of live sources, not a new source of truth." in text
    assert "Treat the checkpoint as expired" in text
    assert "Claiming this skill implements, observes, or proves a model's internal global workspace." in text


def test_workspace_checkpoint_has_a_small_fixed_output_shape() -> None:
    text = SKILL.read_text(encoding="utf-8")

    for field in (
        "WORKSPACE CHECKPOINT",
        "Action: ...",
        "Governing constraints: ...",
        "Current evidence: ...",
        "Open risk: ...",
        "Stop / escalate if: ...",
    ):
        assert field in text
