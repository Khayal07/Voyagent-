"""Alembic konfiqurasiyasının bütövlüyü (DB-siz)."""

from alembic.script import ScriptDirectory

from app.db import _alembic_config


def test_migration_chain_resolves_to_head():
    script = ScriptDirectory.from_config(_alembic_config())
    head = script.get_current_head()
    assert head == "0003"
    # zəncir qırıq deyil — base-dən head-ə yol var
    revisions = list(script.walk_revisions())
    assert revisions[-1].down_revision is None
