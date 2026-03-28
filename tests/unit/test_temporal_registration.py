"""Test module for the Temporal workflow and activity registration."""

from src.worker.temporal_workflows import (
    SyncMakerworldWorkflow,
    SyncPrintablesWorkflow,
    SyncThingiverseWorkflow,
    SyncCults3dWorkflow,
    SyncMinihoarderWorkflow,
    SyncLocalWorkflow,
    sync_makerworld,
    sync_printables,
    sync_thingiverse,
    sync_cults3d,
    sync_minihoarder,
    sync_local,
)

def test_workflows_exist():
    """Verify that all expected workflows exist."""
    assert SyncMakerworldWorkflow
    assert SyncPrintablesWorkflow
    assert SyncThingiverseWorkflow
    assert SyncCults3dWorkflow
    assert SyncMinihoarderWorkflow
    assert SyncLocalWorkflow

def test_activities_exist():
    """Verify that all expected activities exist."""
    assert sync_makerworld
    assert sync_printables
    assert sync_thingiverse
    assert sync_cults3d
    assert sync_minihoarder
    assert sync_local
