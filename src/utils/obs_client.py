from datetime import datetime

from fastapi import UploadFile
from obs import ObsClient
from pathlib import Path

from starlette.concurrency import run_in_threadpool

from src.config import settings


class OBSUtils:
    def __init__(self):
        self.client = ObsClient(
            access_key_id=settings.keiyue_ak,
            secret_access_key=settings.keiyue_sk,
            server=settings.obs_endpoint
        )


myObs = OBSUtils()
myBucket = "projeck"


# 时间戳应保持一致
async def pre_link(rid: int, img: UploadFile, timestamp) -> str:
    img_key = f"RImg/{rid}/{timestamp}_img{Path(img.filename).suffix}"
    iurl = f"https://{myBucket}.obs.cn-south-1.myhuaweicloud.com/{img_key}"
    print(iurl)
    return iurl


async def img_upload(rid: int, img: UploadFile, timestamp) -> str | None:
    img_key = f"RImg/{rid}/{timestamp}_img{Path(img.filename).suffix}"
    # print('endpoint:', repr(settings.obs_endpoint), type(settings.obs_endpoint))
    print("---------")
    print(img_key)

    try:
        iurl = f"https://{myBucket}.obs.cn-south-1.myhuaweicloud.com/{img_key}"
        print("---------1")
        myObs.client.putContent(bucketName=myBucket, objectKey=img_key, content=await img.read())
        print("---------2")
        return iurl

    except Exception as e:
        print(e)
        try:
            myObs.client.deleteObject(bucketName=myBucket, objectKey=img_key)
        except Exception as e:
            print(e)
            return None
        return None
