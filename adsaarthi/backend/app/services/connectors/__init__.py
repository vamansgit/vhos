from app.models.enums import AdPlatform
from app.services.connectors.base import AdConnector, ConnectorNotConfiguredError, RawDailyMetric
from app.services.connectors.meta_connector import MetaConnector
from app.services.connectors.mock_connector import MockConnector
from app.services.connectors.youtube_connector import YouTubeConnector

_LIVE_CONNECTORS: dict[AdPlatform, type[AdConnector]] = {
    AdPlatform.META: MetaConnector,
    AdPlatform.YOUTUBE: YouTubeConnector,
}


def get_connector(platform: AdPlatform) -> AdConnector:
    """Returns the live platform connector if credentials are configured,
    otherwise falls back to the deterministic mock connector so the product
    is fully usable and demoable without production API access.
    """
    live_cls = _LIVE_CONNECTORS.get(platform)
    if live_cls is not None:
        try:
            return live_cls()
        except ConnectorNotConfiguredError:
            pass
    return MockConnector(platform=platform.value)


__all__ = ["get_connector", "AdConnector", "RawDailyMetric", "ConnectorNotConfiguredError"]
