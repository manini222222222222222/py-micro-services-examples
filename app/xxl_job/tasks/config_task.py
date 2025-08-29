import json

from pyxxl.ctx import g

from app.common.logger import log
from app.config.nacos_config import get_nacos_client
from app.config.xxl_job_config import traced_executor as executor
# from app.common.utils.wechat_msg_util import send_markdown_template_exception_message
# from app.common.const import WechatRobotEnum

"""
    sync task demo
"""
@executor(name="refresh_nacos_config_task")
def refresh_nacos_config_task():
    try:
        start_msg = f"[XXL-JOB] process refresh nacos starts..."
        g.logger.info(start_msg)
        log.info(start_msg)

        nacos_client = get_nacos_client()

        nacos_client.refresh()

        log.info(f"[XXL-JOB] process refresh nacos result:{json.dumps(nacos_client.get_yaml_config())}")

        end_msg = "[XXL-JOB] process refresh nacos finish..."
        g.logger.info(end_msg)
        log.info(end_msg)
        return "success..."
    except Exception as e:
        g.logger.exception("[XXL-JOB] process refresh nacos error...")
        log.exception(f"[XXL-JOB] process refresh nacos error，error msg:{str(e)}")
        # send_markdown_template_exception_message(WechatRobotEnum.ALGORITHM_DEFAULT, ["[XXL-JOB] process refresh nacos error"], e)
        raise e