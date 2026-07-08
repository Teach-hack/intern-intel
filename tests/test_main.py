"""Unit tests for the main module entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


@patch("app.cli.main")
def test_main_delegates_to_cli_main(mock_cli_main: MagicMock) -> None:
    """Verify that execution of __main__ delegates directly to cli.main."""
    import runpy

    with patch("sys.argv", ["app", "run"]):
        runpy.run_module("app", run_name="__main__")
        mock_cli_main.assert_called_once()
