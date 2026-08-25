"""Tests for the Module 7 Amazon S3 download helper."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import s3_fetch


def test_get_s3_client():
    """The helper should request an Amazon S3 client."""
    with patch("s3_fetch.boto3.client") as mock_client:
        expected = MagicMock()
        mock_client.return_value = expected

        result = s3_fetch.get_s3_client()

        mock_client.assert_called_once_with("s3")
        assert result is expected


def test_download_from_s3(tmp_path):
    """The helper should download the requested object."""
    client = MagicMock()
    destination = tmp_path / "data" / "applicant_data.json"

    result = s3_fetch.download_from_s3(
        "grad-cafe-bucket",
        "applicant_data.json",
        destination,
        client=client,
    )

    client.download_file.assert_called_once_with(
        "grad-cafe-bucket",
        "applicant_data.json",
        str(destination),
    )

    assert result == destination
    assert destination.parent.exists()


def test_download_uses_default_client(tmp_path):
    """A client should be created when one is not supplied."""
    destination = tmp_path / "applicant_data.json"
    client = MagicMock()

    with patch(
        "s3_fetch.get_s3_client",
        return_value=client,
    ):
        s3_fetch.download_from_s3(
            "test-bucket",
            "data.json",
            destination,
        )

    client.download_file.assert_called_once_with(
        "test-bucket",
        "data.json",
        str(destination),
    )


def test_main_requires_bucket(monkeypatch):
    """The command should reject execution without an S3 bucket."""
    monkeypatch.delenv("S3_BUCKET", raising=False)
    monkeypatch.setattr(sys, "argv", ["s3_fetch.py"])

    with pytest.raises(SystemExit) as exc_info:
        s3_fetch.main()

    assert exc_info.value.code == 2


def test_main_downloads_configured_object(
    monkeypatch,
    tmp_path,
    capsys,
):
    """CLI arguments should be forwarded to the downloader."""
    destination = tmp_path / "applicant_data.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "s3_fetch.py",
            "--bucket",
            "grad-cafe-bucket",
            "--key",
            "applicant_data.json",
            "--destination",
            str(destination),
        ],
    )

    with patch(
        "s3_fetch.download_from_s3",
        return_value=destination,
    ) as mock_download:
        s3_fetch.main()

    mock_download.assert_called_once_with(
        "grad-cafe-bucket",
        "applicant_data.json",
        str(destination),
    )

    output = capsys.readouterr().out
    assert "grad-cafe-bucket" in output
    assert "applicant_data.json" in output