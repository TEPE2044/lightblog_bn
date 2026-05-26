# 全局配置
from pathlib import Path
from pydantic.v1 import BaseSettings

# 定位到项目根目录（.env 所在）
ROOT_DIR = Path(__file__).resolve().parent.parent
env_file = ROOT_DIR / ".env.dev"


class Settings(BaseSettings):
    pgdb_url: str
    pgdb_ab_url: str
    pgdb_password: str
    rd_url: str
    rd_local_url: str
    rd_train_url: str
    outdated_session: int
    aliyun_key: str
    aliyun_secret: str
    jwt_secret: str
    aes_secret: str
    em_sender: str
    em_password: str
    keiyue_ak: str
    keiyue_sk: str
    obs_endpoint: str
    obs_bucket: str
    obs_region: str
    obs_endpoint: str
    obs_bucket: str
    obs_region: str

    # 傻逼勾勾页，这都能写错？？？
    # WARNING:TODO:这条TODO将一直留在这里，警醒自己，有问题的时候，不要想得太复杂
    # obs_endpoint = str
    # obs_bucket = str
    # obs_region = str
    # obs_endpoint = str
    # obs_bucket = str
    # obs_region = str

    class Config:
        env_file = env_file  # 告诉 pydantic 去加载 .env
        case_sensitive = False  # 不区分大小写


# 单例，随处导入
settings = Settings()
