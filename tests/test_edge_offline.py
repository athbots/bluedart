"""
Tests for Edge Offline SQLite Buffering and Reconnection Sync.
Verifies queue insertion, backoff retry, and acknowledgement removal.
"""

import os
import pytest
from edge.edge_agent.offline_buffer import OfflineEdgeBuffer


def test_offline_buffer_enqueue_and_ack(tmp_path):
    db_file = str(tmp_path / "test_edge_buffer.db")
    buffer = OfflineEdgeBuffer(db_path=db_file)

    payload1 = {
        "vehicle_id": "BUS_101",
        "occupancy_score": 0.65,
        "crowd_level": "HIGH",
        "confidence": 0.92,
    }
    payload2 = {
        "vehicle_id": "BUS_101",
        "occupancy_score": 0.70,
        "crowd_level": "HIGH",
        "confidence": 0.92,
    }

    # Enqueue 2 events
    event_id1 = buffer.enqueue("BUS_101", "crowd", payload1)
    event_id2 = buffer.enqueue("BUS_101", "crowd", payload2)

    assert buffer.get_queue_size() == 2

    # Pending fetch
    pending = buffer.get_pending()
    assert len(pending) == 2
    assert pending[0]["id"] == event_id1

    # Simulate successful transmission of first item
    buffer.acknowledge_success(event_id1)
    assert buffer.get_queue_size() == 1

    # Simulate transmission failure on second item with backoff
    buffer.record_failure(event_id2, current_retries=0)
    assert buffer.get_queue_size() == 1
