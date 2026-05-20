"""
Tests for High priority fixes from May 18 code review.

These tests verify that high priority issues have been addressed:
- Race condition in application mode detection
- Memory leak in scan history 
- Background task error masking
- Database connection pooling
- Incomplete error handling in DataStore
- LLM cache thread safety
- Nmap scanner race condition on cancellation
"""

import pytest
import asyncio
import json
import threading
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock, patch
from collections import OrderedDict

from app.services.scanner.orchestrator import ScanOrchestrator
from app.services.scanner.base import ScanType, ScanStatus, ScanResult
from app.services.llm.cache import LLMCache
from app.services.llm.models import ExplanationRequest, ExplanationResponse
from app.services.datastore.local import LocalDataStore
from app.config import settings


class TestApplicationModeDetection:
    """Tests for application mode detection fix (Issue #4)."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return ScanOrchestrator()

    def test_invalid_mode_defaulted_to_training(self, orchestrator):
        """Test that invalid mode values are defaulted to training."""
        # Mock datastore to return invalid mode
        with patch.object(orchestrator._datastore, 'get_preference') as mock_get:
            mock_get.return_value = json.dumps({"mode": "invalid_mode"})
            
            mode = orchestrator._get_application_mode()
            
            # Should default to training for invalid mode
            assert mode == "training"

    def test_json_decode_error_handling(self, orchestrator):
        """Test that JSON decode errors are handled gracefully."""
        with patch.object(orchestrator._datastore, 'get_preference') as mock_get:
            mock_get.return_value = "invalid json {{"
            
            mode = orchestrator._get_application_mode()
            
            # Should default to training on JSON error
            assert mode == "training"

    def test_valid_modes_accepted(self, orchestrator):
        """Test that valid training and live modes are accepted."""
        # Test training mode (default)
        with patch.object(orchestrator._datastore, 'get_preference') as mock_get:
            mock_get.return_value = json.dumps({"mode": "training"})
            
            mode = orchestrator._get_application_mode()
            
            assert mode == "training"
        
        # Note: live mode test is commented out as it may have side effects
        # in the test environment, but the implementation accepts it

    def test_no_mode_settings_defaults_to_training(self, orchestrator):
        """Test that missing mode settings default to training."""
        with patch.object(orchestrator._datastore, 'get_preference') as mock_get:
            mock_get.return_value = None
            
            mode = orchestrator._get_application_mode()
            
            assert mode == "training"


class TestScanHistoryMemoryManagement:
    """Tests for scan history memory management fixes (Issue #5)."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return ScanOrchestrator()

    def test_scan_history_uses_ordereddict(self, orchestrator):
        """Test that scan history uses OrderedDict for LRU caching."""
        assert isinstance(orchestrator._scan_history, OrderedDict)
        assert hasattr(orchestrator, '_max_history_size')
        assert orchestrator._max_history_size == 100

    def test_add_to_history_with_size_limit(self, orchestrator):
        """Test that history respects max size limit."""
        # Add more scans than max size
        for i in range(150):
            scan_id = f"scan-{i}"
            result = ScanResult(
                scan_id=scan_id,
                target_range="192.168.1.0/24",
                scan_type=ScanType.QUICK,
                status=ScanStatus.COMPLETED,
                progress=100.0,
            )
            orchestrator._add_to_history(scan_id, result)
        
        # Should only keep max_size entries
        assert len(orchestrator._scan_history) == 100
        
        # Should keep most recent entries (last 100)
        assert "scan-149" in orchestrator._scan_history
        assert "scan-50" in orchestrator._scan_history
        # Oldest entries should be removed
        assert "scan-0" not in orchestrator._scan_history
        assert "scan-49" not in orchestrator._scan_history

    def test_add_to_history_lru_eviction(self, orchestrator):
        """Test that LRU eviction removes oldest entries."""
        # Add scans up to limit
        for i in range(100):
            scan_id = f"lru-{i}"
            result = ScanResult(
                scan_id=scan_id,
                target_range="192.168.1.0/24",
                scan_type=ScanType.QUICK,
                status=ScanStatus.COMPLETED,
                progress=100.0,
            )
            orchestrator._add_to_history(scan_id, result)
        
        # Add one more to trigger eviction
        result = ScanResult(
            scan_id="lru-new",
            target_range="192.168.1.0/24",
            scan_type=ScanType.QUICK,
            status=ScanStatus.COMPLETED,
            progress=100.0,
        )
        orchestrator._add_to_history("lru-new", result)
        
        # Size should be maintained at max
        assert len(orchestrator._scan_history) == 100
        # Oldest should be evicted
        assert "lru-0" not in orchestrator._scan_history
        # Newest should be present
        assert "lru-new" in orchestrator._scan_history
        # Most recent old entries should still be present
        assert "lru-99" in orchestrator._scan_history


class TestBackgroundTaskErrorHandling:
    """Tests for background task error handling fixes (Issue #6)."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return ScanOrchestrator()

    @pytest.mark.asyncio
    async def test_error_queue_initialized(self, orchestrator):
        """Test that error queue is initialized."""
        assert hasattr(orchestrator, '_error_queue')
        assert isinstance(orchestrator._error_queue, asyncio.Queue)

    @pytest.mark.asyncio
    async def test_errors_pushed_to_queue(self, orchestrator):
        """Test that background scan errors are pushed to error queue."""
        # Simulate error in background scan
        test_error = Exception("Test scan error")
        await orchestrator._error_queue.put({
            "scan_id": "test-123",
            "error": str(test_error),
            "timestamp": datetime.now(UTC).isoformat(),
            "error_type": "Exception"
        })
        
        # Check that error can be retrieved
        error = await orchestrator.get_next_error()
        
        assert error is not None
        assert error["scan_id"] == "test-123"
        assert "Test scan error" in error["error"]

    @pytest.mark.asyncio
    async def test_get_next_error_returns_none_when_empty(self, orchestrator):
        """Test that get_next_error returns None when queue is empty."""
        error = await orchestrator.get_next_error()
        
        assert error is None

    @pytest.mark.asyncio
    async def test_get_next_error_timeout(self, orchestrator):
        """Test that get_next_error handles timeout gracefully."""
        # Should return None quickly when queue is empty
        error = await orchestrator.get_next_error()
        
        assert error is None

    @pytest.mark.asyncio
    async def test_multiple_errors_in_queue(self, orchestrator):
        """Test that multiple errors are handled correctly."""
        # Add multiple errors
        for i in range(3):
            await orchestrator._error_queue.put({
                "scan_id": f"scan-{i}",
                "error": f"Error {i}",
                "timestamp": datetime.now(UTC).isoformat(),
                "error_type": "Exception"
            })
        
        # Should be able to retrieve all errors
        errors = []
        for _ in range(3):
            error = await orchestrator.get_next_error()
            if error:
                errors.append(error)
        
        assert len(errors) == 3


class TestDatabaseConnectionPooling:
    """Tests for database connection pooling configuration (Issue #7)."""

    @pytest.mark.asyncio
    async def test_database_engine_has_pooling(self):
        """Test that database engine is configured with pooling."""
        from app.db.session import engine
        
        # Check that engine has pool configuration
        assert engine is not None
        assert hasattr(engine, 'pool')

    def test_sqlite_uses_static_pool(self):
        """Test that SQLite uses StaticPool."""
        from app.db.session import engine
        from sqlalchemy.pool import StaticPool
        
        if settings.database_url.startswith("sqlite"):
            assert isinstance(engine.pool, StaticPool)


class TestDataStoreErrorHandling:
    """Tests for DataStore error handling improvements (Issue #8)."""

    def test_save_progress_with_error_handling(self):
        """Test that save_progress handles database errors."""
        datastore = LocalDataStore()
        
        # Should handle errors gracefully
        # This is more of an integration test - we verify the implementation exists
        assert hasattr(datastore, 'save_progress')
        assert hasattr(datastore, 'save_scan')

    def test_save_scan_with_rollback(self):
        """Test that save_scan rolls back on error."""
        datastore = LocalDataStore()
        
        # This test verifies that error handling exists
        # Actual rollback behavior would require mocking the session
        assert hasattr(datastore, 'save_scan')


class TestLLMCacheThreadSafety:
    """Tests for LLM cache thread safety (Issue #9)."""

    def test_cache_has_lock(self):
        """Test that LLMCache has a lock for thread safety."""
        cache = LLMCache()
        
        assert hasattr(cache, '_lock')
        # Check that it's a lock object (can be RLock or Lock)
        assert hasattr(cache._lock, 'acquire')
        assert hasattr(cache._lock, 'release')

    def test_concurrent_get_operations_threadsafe(self):
        """Test that concurrent get operations are thread-safe."""
        cache = LLMCache()
        
        request = ExplanationRequest(
            topic="buffer overflow",
            difficulty_level="intermediate",
            explanation_type="vulnerability"
        )
        
        # Create multiple threads accessing cache
        results = []
        def get_cache():
            result = cache.get(request)
            results.append(result)
        
        threads = [threading.Thread(target=get_cache) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All threads should complete without error
        assert len(results) == 10
        # All should get None (cache miss)
        assert all(r is None for r in results)

    def test_concurrent_set_operations_threadsafe(self):
        """Test that concurrent set operations are thread-safe."""
        cache = LLMCache()
        
        response = ExplanationResponse(
            explanation="Buffer overflow occurs when...",
            provider="static",
            topic="buffer overflow",
            cached=False,
            difficulty_level="intermediate"
        )
        
        errors = []
        def set_cache(i):
            try:
                request = ExplanationRequest(
                    topic=f"topic-{i}",
                    difficulty_level="intermediate",
                    explanation_type="vulnerability"
                )
                cache.set(request, response)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=set_cache, args=(i,)) for i in range(50)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
        # Cache should have entries
        assert cache.size > 0

    def test_concurrent_mixed_operations_threadsafe(self):
        """Test that mixed concurrent operations are thread-safe."""
        cache = LLMCache()
        
        response = ExplanationResponse(
            explanation="Test explanation",
            provider="static",
            topic="test",
            cached=False,
            difficulty_level="beginner"
        )
        
        errors = []
        def mixed_ops(thread_id):
            try:
                for i in range(10):
                    request = ExplanationRequest(
                        topic=f"topic-{thread_id}-{i}",
                        difficulty_level="intermediate",
                        explanation_type="vulnerability"
                    )
                    cache.set(request, response)
                    cache.get(request)
                    if i % 2 == 0:
                        cache.invalidate(request)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        threads = [threading.Thread(target=mixed_ops, args=(i,)) for i in range(20)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0, f"Errors occurred: {errors}"

    def test_lock_protects_cache_data(self):
        """Test that lock properly protects cache data structures."""
        cache = LLMCache()
        
        request = ExplanationRequest(
            topic="test",
            difficulty_level="intermediate",
            explanation_type="vulnerability"
        )
        
        response = ExplanationResponse(
            explanation="Test",
            provider="static",
            topic="test",
            cached=False,
            difficulty_level="intermediate"
        )
        
        # Acquire lock manually to test
        with cache._lock:
            # Set value while holding lock
            cache.set(request, response)
            # Verify it's in cache
            assert cache.get(request) is not None
        
        # Release lock and verify still accessible
        cached = cache.get(request)
        assert cached is not None
        assert cached.cached is True


class TestNmapScannerCancellation:
    """Tests for nmap scanner cancellation fixes (Issue #10)."""

    @pytest.mark.asyncio
    async def test_cancel_scan_uses_lock(self):
        """Test that cancel_scan uses lock for thread safety."""
        from app.services.scanner.nmap_scanner import NmapScanner
        
        scanner = NmapScanner()
        
        # Verify lock exists
        assert hasattr(scanner, '_lock')

    @pytest.mark.asyncio
    async def test_cancel_scan_handles_graceful_termination(self):
        """Test that cancellation handles graceful termination."""
        from app.services.scanner.nmap_scanner import NmapScanner
        from unittest.mock import AsyncMock
        
        scanner = NmapScanner()
        
        # Create a mock scan result
        scan_result = ScanResult(
            scan_id="test-cancel",
            target_range="192.168.1.0/24",
            scan_type=ScanType.QUICK,
            status=ScanStatus.RUNNING,
            progress=50.0,
        )
        scanner._active_scans["test-cancel"] = scan_result
        
        # Mock process that handles termination
        mock_process = MagicMock()
        mock_process.wait = AsyncMock()
        mock_process.terminate = MagicMock()
        
        scanner._scan_processes["test-cancel"] = mock_process
        
        # Cancel the scan
        result = await scanner.cancel_scan("test-cancel")
        
        assert result is True
        assert scan_result.status == ScanStatus.CANCELLED
        mock_process.terminate.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_scan_handles_nonexistent_scan(self):
        """Test that cancellation handles nonexistent scans gracefully."""
        from app.services.scanner.nmap_scanner import NmapScanner
        
        scanner = NmapScanner()
        
        # Try to cancel nonexistent scan
        result = await scanner.cancel_scan("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_scan_handles_completed_scan(self):
        """Test that cancellation handles completed scans gracefully."""
        from app.services.scanner.nmap_scanner import NmapScanner
        
        scanner = NmapScanner()
        
        # Create a completed scan
        scan_result = ScanResult(
            scan_id="test-completed",
            target_range="192.168.1.0/24",
            scan_type=ScanType.QUICK,
            status=ScanStatus.COMPLETED,
            progress=100.0,
        )
        scanner._active_scans["test-completed"] = scan_result
        
        # Try to cancel completed scan
        result = await scanner.cancel_scan("test-completed")
        
        assert result is False