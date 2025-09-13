from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("default_tz", sa.String(64)),
        sa.Column("work_hours_start", sa.String(5)),
        sa.Column("work_hours_end", sa.String(5)),
        sa.Column("tag_rules", sa.Text),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(255)),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_project_user_name"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(255)),
        sa.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("title", sa.String(500)),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("due", sa.DateTime, nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="3"),
        sa.Column("recurrence", sa.String(255), nullable=True),
        sa.Column("completed", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "task_tags",
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tags.id"), primary_key=True),
    )
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id")),
        sa.Column("remind_at", sa.DateTime),
        sa.Column("sent", sa.Boolean, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("token_hash", sa.String(255), unique=True),
        sa.Column("created_at", sa.DateTime),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(255)),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime),
    )

    # FTS5 virtual table for tasks
    op.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(title, notes, content='tasks', content_rowid='id')"
    )
    # triggers
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS tasks_ai AFTER INSERT ON tasks BEGIN
            INSERT INTO tasks_fts(rowid, title, notes) VALUES (new.id, new.title, new.notes);
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS tasks_ad AFTER DELETE ON tasks BEGIN
            INSERT INTO tasks_fts(tasks_fts, rowid, title, notes) VALUES('delete', old.id, old.title, old.notes);
        END;
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS tasks_au AFTER UPDATE ON tasks BEGIN
            INSERT INTO tasks_fts(tasks_fts, rowid, title, notes) VALUES('delete', old.id, old.title, old.notes);
            INSERT INTO tasks_fts(rowid, title, notes) VALUES (new.id, new.title, new.notes);
        END;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tasks_au")
    op.execute("DROP TRIGGER IF EXISTS tasks_ad")
    op.execute("DROP TRIGGER IF EXISTS tasks_ai")
    op.execute("DROP TABLE IF EXISTS tasks_fts")
    op.drop_table("audit_log")
    op.drop_table("api_tokens")
    op.drop_table("reminders")
    op.drop_table("task_tags")
    op.drop_table("tasks")
    op.drop_table("tags")
    op.drop_table("projects")
    op.drop_table("user_settings")
    op.drop_table("users")

