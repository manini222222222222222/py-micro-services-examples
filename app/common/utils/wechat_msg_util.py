import asyncio
import json
import ssl
import traceback

import aiohttp
import certifi

from app.common.const import AlarmLevel, WechatRobotEnum
from app.common.logger import log
from app.config.nacos_config import get_config

"""
Core methods for sending enterprise WeChat messages
"""
async def _send_wechat_message_core(
        robot_key: str,
        msgtype: str,
        content: str,
        mentioned_list: list[str] = None,
        mentioned_mobile_list: list[str] = None
) -> bool:
    """
    Send group chat Markdown messages through enterprise WeChat bots

    :param robot_key: 企业微信机器人Webhook的key
    :param msgtype: 消息类型 text=纯文本内容 markdown=markdown消息体
    :param content: markdown格式消息内容 或纯文本text
    :param mentioned_list: @成员微信号列表，支持["@all"]全体成员
    :param mentioned_mobile_list: @手机号列表，支持["@all"]
    :return: 发送成功返回True，否则返回False
    """
    mentioned_list = mentioned_list or []
    mentioned_mobile_list = mentioned_mobile_list or []

    if msgtype == "text":
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list,
                "mentioned_mobile_list": mentioned_mobile_list,
            }
        }
    elif msgtype == "markdown":
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    else:
        raise ValueError("Currently only supports' text 'and' markdown 'type")

    headers = {
        "Content-Type": "application/json"
    }

    try:
        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=sslcontext)) as session:
            async with session.post(f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={robot_key}", headers=headers, data=json.dumps(payload)) as resp:
                if resp.status != 200:
                    log.error(f"发送企微消息失败，状态码: {resp.status}")
                    return False
                resp_json = await resp.json()
                if resp_json.get("errcode") == 0:
                    # 发送成功
                    return True
                else:
                    log.error(f"发送企微消息失败，错误信息: {resp_json}")
                    return False
    except Exception as ex:
        log.exception(f"发送企微消息失败，错误信息: {ex}")
        return False


"""
send a specified msgtoype message
"""
def _send_wechat_message_by_type(
        robot_enum: WechatRobotEnum,
        msgtype: str,
        content: str,
        mentioned_list: list[str] = None,
        mentioned_mobile_list: list[str] = None
) -> bool:
    """
   Synchronous interface, calling asynchronous sending functions for easy use in synchronous environments

    :return: 发送是否成功
    """
    robot_key = get_config()["wechat"]["robot_templates"][robot_enum.robot_name]["key"]
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(_send_wechat_message_core(robot_key, msgtype, content, mentioned_list, mentioned_mobile_list))
            return True
        else:
            return asyncio.run(_send_wechat_message_core(robot_key, msgtype, content, mentioned_list, mentioned_mobile_list))
    except RuntimeError:
        return asyncio.run(_send_wechat_message_core(robot_key, msgtype, content, mentioned_list, mentioned_mobile_list))

"""
Send a simple plain text message to a designated group of robots
"""
def send_simple_text_message(
        robot_enum: WechatRobotEnum,
        content: str,
        mentioned_list: list[str] = None,
        mentioned_mobile_list: list[str] = None
) -> bool:
    return _send_wechat_message_by_type(robot_enum, "text", content, mentioned_list, mentioned_mobile_list)

"""
Send a simple plain text message to the default alarm group robot
"""
def send_simple_text_message_to_default(
        content: str,
        mentioned_list: list[str] = None,
        mentioned_mobile_list: list[str] = None
) -> bool:
    return send_simple_text_message(WechatRobotEnum.DEFAULT, content, mentioned_list, mentioned_mobile_list)


"""
Send a markdown message to the designated group of robots
"""
def send_markdown_message(
        robot_enum: WechatRobotEnum,
        content: str
) -> bool:
    return _send_wechat_message_by_type(robot_enum, "markdown", content)


"""
Send a markdown template message to the designated group chat robot
"""
def send_markdown_template_message(
        robot_enum: WechatRobotEnum,
        params: list[str],
        alarm_level_enum: AlarmLevel = None,
) -> bool:
    """
    Send a markdown template message to the designated group chat robot

    :param robot_enum: 群机器人枚举
    :param params: 模版参数列表
    :param alarm_level_enum: 告警等级枚举
    :return: 发送是否成功
    """
    # 获取消息模版配置
    template_config = get_config()["wechat"]["robot_templates"][robot_enum.robot_name]
    # 消息模版
    template_context = template_config["template"]

    # 告警等级
    if alarm_level_enum is None:
        alarm_level_enum = AlarmLevel.get_by_key(template_config["alarm_level"])

    # 拼接样式
    params = tuple(f"{alarm_level_enum.tag_start}{param}{alarm_level_enum.tag_end}" for param in params)

    # 替换模版参数
    content = template_context.format(*params)
    return send_markdown_message(robot_enum, content)

"""
Send a markdown exception stack template message to the specified group chat robot
"""
def send_markdown_template_exception_message(
        robot_enum: WechatRobotEnum,
        params: list[str],
        err: Exception,
        alarm_level_enum: AlarmLevel = None
) -> bool:
    """
    Send an exception template message to the designated group chat robot

    :param robot_enum: 群机器人枚举
    :param err: 异常对象
    :param params: 参数集合
    :param alarm_level_enum: 告警等级枚举
    :return: 发送是否成功
    """
    if params is None:
        params = []

    params.append(_format_exception_markdown(err))
    return send_markdown_template_message(robot_enum, params, alarm_level_enum)


"""
Format the exception stack information as Markdown and truncate the excessively long stack.
"""
def _format_exception_markdown(err: Exception, max_lines=15) -> str:

    # get a complete list of stack strings
    tb_lines = traceback.format_exception(type(err), err, err.__traceback__)

    # Splicing into a string and limiting the number of lines to prevent messages from being too long
    tb_text = "".join(tb_lines)
    tb_summary = "\n".join(tb_text.splitlines()[-max_lines:])

    return tb_summary


if __name__ == "__main__":
    try:
        1 / 0
    except Exception as e:
        success = send_markdown_template_exception_message(WechatRobotEnum.DEFAULT, ["测试示例计算失败"], e)
        if success:
            log.info("消息发送成功")
        else:
            log.info("消息发送失败")
