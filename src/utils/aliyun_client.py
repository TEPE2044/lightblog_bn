from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525.client import Client as Keiyue
# DypnsClient = Dy(Aliyun Product) + Phone + Number + Service
from src.config import settings


def create_client() -> Keiyue:
    config = open_api_models.Config(
        access_key_id=settings.aliyun_key,
        access_key_secret=settings.aliyun_secret
    )
    config.endpoint = "dypnsapi.aliyuncs.com"
    return Keiyue(config)
