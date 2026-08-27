"""
Root services alias module pointing to api.services.data_source
"""
from api.services.data_source import (
    transform_deal_record,
    DealsDataSource,
    hubspot_deals_resource,
    hubspot_deals_source,
)

__all__ = [
    "transform_deal_record",
    "DealsDataSource",
    "hubspot_deals_resource",
    "hubspot_deals_source",
]
