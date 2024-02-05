#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

logger = logging.getLogger(__name__)


class MlopsLibsCharm(ops.CharmBase):
    """Tester charm for MLOps libs."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on["some_container"].pebble_ready, self._on_pebble_ready)

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(MlopsLibsCharm)  # type: ignore
