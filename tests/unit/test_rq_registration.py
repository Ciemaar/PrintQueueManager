from unittest.mock import MagicMock, patch

from src.worker.scheduler import setup_periodic_tasks


@patch("src.worker.scheduler.Scheduler")
@patch("src.worker.scheduler.get_redis_connection")
def test_rq_tasks_registered(mock_get_redis, mock_scheduler_cls):
    """Verify that all expected tasks are explicitly scheduled in the RQ scheduler."""
    mock_scheduler = MagicMock()
    mock_scheduler_cls.return_value = mock_scheduler
    # Make get_jobs return empty list to mock the cancellation loop
    mock_scheduler.get_jobs.return_value = []

    setup_periodic_tasks()

    assert mock_scheduler.schedule.call_count == 5

    # Check that each function is scheduled
    scheduled_funcs = [
        call.kwargs.get("func").__name__ for call in mock_scheduler.schedule.call_args_list
    ]

    assert "sync_makerworld" in scheduled_funcs
    assert "sync_printables" in scheduled_funcs
    assert "sync_thingiverse" in scheduled_funcs
    assert "sync_cults3d" in scheduled_funcs
    assert "sync_minihoarder" in scheduled_funcs
