import dramatiq

# We must import the module so the actors are registered with the broker
import src.worker.dramatiq_app  # noqa: F401


def test_dramatiq_actors_registered():
    """Verify that all expected actors are explicitly registered in the Dramatiq broker registry."""
    broker = dramatiq.get_broker()
    registered_actors = broker.get_declared_actors()

    assert "sync_makerworld" in registered_actors
    assert "sync_printables" in registered_actors
    assert "sync_thingiverse" in registered_actors
    assert "sync_cults3d" in registered_actors
    assert "sync_minihoarder" in registered_actors
    assert "sync_local" in registered_actors
