from dataclasses import dataclass
from typing import List, Dict


@dataclass
class InventoryItem:
    barcode: str
    stock: int
    title: str = ""


class BaseConnector:
    provider = ""

    def __init__(self, integration):
        self.integration = integration

    def fetch_inventory(self) -> List[InventoryItem]:
        """Fetch inventory from the provider. Override in provider connector."""
        return []


class ShopifyConnector(BaseConnector):
    provider = "shopify"


class SquareConnector(BaseConnector):
    provider = "square"


class QuickBooksConnector(BaseConnector):
    provider = "quickbooks"


CONNECTORS = {
    "shopify": ShopifyConnector,
    "square": SquareConnector,
    "quickbooks": QuickBooksConnector,
}


def build_connector(integration):
    connector_cls = CONNECTORS.get(integration.provider)
    if not connector_cls:
        return None
    return connector_cls(integration)
