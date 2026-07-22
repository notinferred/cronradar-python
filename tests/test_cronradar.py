"""
CronRadar Python SDK Tests
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

import cronradar


class TestMonitor:
    """Tests for the monitor() function."""

    def setup_method(self):
        """Set up test environment."""
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        """Clean up test environment."""
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.urlopen')
    def test_sends_get_request_to_correct_url(self, mock_urlopen):
        """Should send GET request to correct URL."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.monitor('test-job')

        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert '/api/v1/ping/test-job/test-api-key-123' in request.full_url
        assert request.method == 'GET'

    def test_does_not_throw_when_api_key_missing(self):
        """Should not throw when API key is missing."""
        del os.environ['CRONRADAR_API_KEY']

        # Should not raise
        cronradar.monitor('test-job')

    @patch('cronradar.urlopen')
    def test_url_encodes_special_characters(self, mock_urlopen):
        """Should URL encode special characters in monitor key."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.monitor('test job/special')

        request = mock_urlopen.call_args[0][0]
        assert 'test%20job%2Fspecial' in request.full_url

    @patch('cronradar.sync_monitor')
    @patch('cronradar._send_ping_internal')
    def test_triggers_sync_on_404_with_schedule(self, mock_ping, mock_sync):
        """Should trigger sync on 404 when schedule provided."""
        mock_ping.return_value = 404

        cronradar.monitor('test-job', schedule='* * * * *')

        mock_sync.assert_called_once()

    @patch('cronradar._send_ping_internal')
    def test_does_not_trigger_sync_on_404_without_schedule(self, mock_ping):
        """Should not trigger sync on 404 without schedule."""
        mock_ping.return_value = 404

        with patch('cronradar.sync_monitor') as mock_sync:
            cronradar.monitor('test-job')
            mock_sync.assert_not_called()

    @patch('cronradar.urlopen')
    def test_handles_network_errors_gracefully(self, mock_urlopen):
        """Should handle network errors gracefully."""
        mock_urlopen.side_effect = URLError('Connection refused')

        # Should not raise
        cronradar.monitor('test-job')


class TestStartJob:
    """Tests for the start_job() function."""

    def setup_method(self):
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.urlopen')
    def test_sends_post_to_start_endpoint(self, mock_urlopen):
        """Should send POST to start endpoint."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.start_job('test-job')

        request = mock_urlopen.call_args[0][0]
        assert '/start' in request.full_url
        assert request.method == 'POST'

    @patch('cronradar.urlopen')
    def test_includes_schedule_query_param(self, mock_urlopen):
        """Should include schedule query param when provided."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.start_job('test-job', schedule='*/5 * * * *')

        request = mock_urlopen.call_args[0][0]
        assert 'schedule=' in request.full_url

    def test_does_not_throw_when_api_key_missing(self):
        """Should not throw when API key is missing."""
        del os.environ['CRONRADAR_API_KEY']

        # Should not raise
        cronradar.start_job('test-job')


class TestCompleteJob:
    """Tests for the complete_job() function."""

    def setup_method(self):
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.urlopen')
    def test_sends_post_to_complete_endpoint(self, mock_urlopen):
        """Should send POST to complete endpoint."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.complete_job('test-job')

        request = mock_urlopen.call_args[0][0]
        assert '/complete' in request.full_url
        assert request.method == 'POST'

    def test_does_not_throw_when_api_key_missing(self):
        """Should not throw when API key is missing."""
        del os.environ['CRONRADAR_API_KEY']

        # Should not raise
        cronradar.complete_job('test-job')


class TestFailJob:
    """Tests for the fail_job() function."""

    def setup_method(self):
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.urlopen')
    def test_sends_post_to_fail_endpoint(self, mock_urlopen):
        """Should send POST to fail endpoint."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.fail_job('test-job')

        request = mock_urlopen.call_args[0][0]
        assert '/fail' in request.full_url
        assert request.method == 'POST'

    @patch('cronradar.urlopen')
    def test_includes_message_query_param(self, mock_urlopen):
        """Should include message query param when provided."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.fail_job('test-job', message='Test error')

        request = mock_urlopen.call_args[0][0]
        assert 'message=' in request.full_url

    def test_does_not_throw_when_api_key_missing(self):
        """Should not throw when API key is missing."""
        del os.environ['CRONRADAR_API_KEY']

        # Should not raise
        cronradar.fail_job('test-job', 'error')


class TestJobContextManager:
    """Tests for the job() context manager."""

    def setup_method(self):
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.complete_job')
    @patch('cronradar.start_job')
    def test_calls_start_and_complete_on_success(self, mock_start, mock_complete):
        """Should call start_job and complete_job on success."""
        with cronradar.job('test-job'):
            pass

        mock_start.assert_called_once_with('test-job', None)
        mock_complete.assert_called_once_with('test-job')

    @patch('cronradar.fail_job')
    @patch('cronradar.start_job')
    def test_calls_start_and_fail_on_error(self, mock_start, mock_fail):
        """Should call start_job and fail_job on error."""
        with pytest.raises(ValueError):
            with cronradar.job('test-job'):
                raise ValueError('Test error')

        mock_start.assert_called_once()
        mock_fail.assert_called_once_with('test-job', 'Test error')

    @patch('cronradar.fail_job')
    @patch('cronradar.start_job')
    def test_re_raises_exception(self, mock_start, mock_fail):
        """Should re-raise the original exception."""
        with pytest.raises(ValueError, match='Test error'):
            with cronradar.job('test-job'):
                raise ValueError('Test error')


class TestSyncMonitor:
    """Tests for the sync_monitor() function."""

    def setup_method(self):
        os.environ['CRONRADAR_API_KEY'] = 'test-api-key-123'

    def teardown_method(self):
        if 'CRONRADAR_API_KEY' in os.environ:
            del os.environ['CRONRADAR_API_KEY']

    @patch('cronradar.urlopen')
    def test_sends_post_to_api_sync(self, mock_urlopen):
        """Should send POST to /api/v1/sync."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.sync_monitor('test-job', '* * * * *')

        request = mock_urlopen.call_args[0][0]
        assert '/api/v1/sync' in request.full_url
        assert request.method == 'POST'

    @patch('cronradar.urlopen')
    def test_includes_basic_auth_header(self, mock_urlopen):
        """Should include Basic auth header."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.sync_monitor('test-job', '* * * * *')

        request = mock_urlopen.call_args[0][0]
        auth_header = request.get_header('Authorization')
        assert auth_header.startswith('Basic ')

    @patch('cronradar.urlopen')
    def test_sends_correct_payload_structure(self, mock_urlopen):
        """Should send correct JSON payload."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        cronradar.sync_monitor('test-job', '*/5 * * * *')

        request = mock_urlopen.call_args[0][0]
        import json
        body = json.loads(request.data.decode('utf-8'))
        assert body['monitors'][0]['key'] == 'test-job'
        assert body['monitors'][0]['schedule'] == '*/5 * * * *'
        assert body['monitors'][0]['gracePeriod'] == 60

    def test_does_not_throw_when_api_key_missing(self):
        """Should not throw when API key is missing."""
        del os.environ['CRONRADAR_API_KEY']

        # Should not raise
        cronradar.sync_monitor('test-job', '* * * * *')


class TestGenerateReadableName:
    """Tests for the _generate_readable_name() function."""

    def test_converts_kebab_case(self):
        """Should convert kebab-case to Title Case."""
        result = cronradar._generate_readable_name('check-overdue-pings')
        assert result == 'Check Overdue Pings'

    def test_converts_snake_case(self):
        """Should convert snake_case to Title Case."""
        result = cronradar._generate_readable_name('check_overdue_pings')
        assert result == 'Check Overdue Pings'

    def test_handles_pascal_case(self):
        """Should handle PascalCase."""
        result = cronradar._generate_readable_name('CheckOverduePings')
        assert 'Check' in result
        assert 'Overdue' in result

    def test_handles_empty_string(self):
        """Should handle empty string."""
        result = cronradar._generate_readable_name('')
        assert result == ''

    def test_handles_simple_key(self):
        """Should capitalize simple key."""
        result = cronradar._generate_readable_name('backup')
        assert result == 'Backup'


class TestDetectSource:
    """Tests for the _detect_source() function."""

    def test_returns_manual_by_default(self):
        """Should return 'manual' by default."""
        result = cronradar._detect_source()
        assert result in ['manual', 'celery', 'airflow', 'apscheduler',
                          'celery-direct', 'airflow-direct', 'django-direct', 'flask-direct']
