from src.worker.celery_app import celery_app


def test_celery_tasks_registered():
    """Verify that all expected tasks are explicitly registered in the Celery app registry."""
    registered_tasks = celery_app.tasks.keys()

    assert "sync_makerworld" in registered_tasks
    assert "sync_printables" in registered_tasks
    assert "sync_thingiverse" in registered_tasks
    assert "sync_cults3d" in registered_tasks
    assert "sync_minihoarder" in registered_tasks
    assert "sync_local" in registered_tasks
