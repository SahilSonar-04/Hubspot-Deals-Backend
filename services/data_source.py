"""
Root services alias module pointing to api.services.data_source
"""
from api.services.data_source import transform_deal_record, DealsDataSource

__all__ = ["transform_deal_record", "DealsDataSource"]
