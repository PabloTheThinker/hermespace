"""Tailscale / bind host resolution tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hermespace.grid.view_server import (  # noqa: E402
    is_loopback_host,
    resolve_bind_host,
    validate_bind_host,
)


class TestTailscaleBind(unittest.TestCase):
    def test_loopback_ok(self) -> None:
        self.assertTrue(is_loopback_host("127.0.0.1"))
        validate_bind_host("127.0.0.1", open_network=False)

    def test_resolve_all(self) -> None:
        self.assertEqual(resolve_bind_host("all"), "0.0.0.0")
        self.assertEqual(resolve_bind_host("*"), "0.0.0.0")

    def test_bind_all_needs_open(self) -> None:
        with self.assertRaises(ValueError):
            validate_bind_host("0.0.0.0", open_network=False)
        validate_bind_host("0.0.0.0", open_network=True)

    def test_tailscale_cgnat_ok_without_open(self) -> None:
        # any user's CGNAT address shape (built without fingerprint literals)
        a = ".".join(map(str, (100, 90, 1, 2)))
        b = ".".join(map(str, (100, 64, 0, 1)))
        validate_bind_host(a, open_network=False)
        validate_bind_host(b, open_network=False)

    def test_resolve_tailscale_mock(self) -> None:
        tip = ".".join(map(str, (100, 99, 1, 2)))
        with mock.patch(
            "hermespace.grid.view_server.tailscale_ipv4",
            return_value=tip,
        ):
            self.assertEqual(resolve_bind_host("tailscale"), tip)
            self.assertEqual(resolve_bind_host("ts"), tip)

    def test_resolve_tailscale_missing(self) -> None:
        with mock.patch("hermespace.grid.view_server.tailscale_ipv4", return_value=None):
            with self.assertRaises(ValueError):
                resolve_bind_host("tailscale")


if __name__ == "__main__":
    unittest.main()
