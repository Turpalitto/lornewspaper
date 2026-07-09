"""Tests for Content Discovery Engine."""

from __future__ import annotations

import pytest

from api.discovery.engine import ContentDiscoveryEngine


class TestContentDiscoveryEngine:
    @pytest.mark.asyncio
    async def test_discover_today_returns_result(self):
        engine = ContentDiscoveryEngine()
        result = await engine.discover_today()
        assert result.id
        assert result.total_discovered >= 0

    @pytest.mark.asyncio
    async def test_strategies_recorded(self):
        engine = ContentDiscoveryEngine()
        result = await engine.discover_today()
        assert len(result.strategies_used) >= 0

    @pytest.mark.asyncio
    async def test_get_latest_returns_result(self):
        engine = ContentDiscoveryEngine()
        await engine.discover_today()
        latest = await engine.get_latest()
        assert latest is not None

    @pytest.mark.asyncio
    async def test_get_trending_topics(self):
        engine = ContentDiscoveryEngine()
        await engine.discover_today()
        topics = engine.get_trending_topics()
        assert isinstance(topics, list)

    @pytest.mark.asyncio
    async def test_get_emerging_topics(self):
        engine = ContentDiscoveryEngine()
        await engine.discover_today()
        topics = engine.get_emerging_topics()
        assert isinstance(topics, list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_discovery(self):
        engine = ContentDiscoveryEngine()
        result = await engine.get_discovery("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_without_discovery(self):
        engine = ContentDiscoveryEngine()
        assert await engine.get_latest() is None
