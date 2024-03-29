import imp
from nonebot.adapters.onebot.v11 import Bot
from nonebot.permission import SUPERUSER
from nonebot import on_command
from .data_source import check_update, get_latest_version_data
from src.utils.log import logger
from src.utils.function import get_bot
from pathlib import Path
from src.utils.config import config
from configs.config import Config
from nonebot.rule import to_me
from nonebot.params import ArgStr
import platform
from nonebot import require
import os

scheduler = require("nonebot_plugin_apscheduler").scheduler

__zx_plugin_name__ = "自动更新 [Superuser]"
__plugin_usage__ = """
usage：
    检查更新钟离最新版本，包括了自动更新
    指令：
        检查更新钟离
        重启
""".strip()
__plugin_des__ = "就算是钟离也会成长的"
__plugin_cmd__ = ["检查更新钟离", "重启"]
__plugin_version__ = 0.1
__plugin_author__ = "HibiKier"
__plugin_configs__ = {
    "UPDATE_REMIND": {
        "value": True,
        "help": "钟离是否检测版本状态",
        "default": True,
    },
    "AUTO_UPDATE_ZHENXUN": {
        "value": False,
        "help": "钟离是否自动检查更新",
        "default": False,
    }
}

NICKNAME = config.nickname[0]

update_zhenxun = on_command(
    "检查更新钟离", permission=SUPERUSER, priority=1, block=True)

restart = on_command(
    "重启",
    aliases={"restart"},
    permission=SUPERUSER,
    rule=to_me(),
    priority=1,
    block=True,
)


@update_zhenxun.handle()
async def _(bot: Bot):
    try:
        code, error = await check_update(bot)
        if error:
            logger.error(f"更新钟离未知错误 {error}")
            await bot.send_private_msg(
                user_id=int(list(bot.config.superusers)[0]), message=f"更新钟离未知错误 {error}"
            )
    except Exception as e:
        logger.error(f"更新钟离未知错误 {type(e)}：{e}")
        await bot.send_private_msg(
            user_id=int(list(bot.config.superusers)[0]),
            message=f"更新钟离未知错误 {type(e)}：{e}",
        )
    else:
        if code == 200:
            await bot.send_private_msg(
                user_id=int(list(bot.config.superusers)[0]), message=f"更新完毕，请重启钟离...."
            )


@restart.got("flag", prompt=f"确定是否重启{NICKNAME}？确定请回复[是|好|确定]（重启失败咱们将失去联系，请谨慎！）")
async def _(flag: str = ArgStr("flag")):
    if flag.lower() in ["true", "是", "好", "确定", "确定是"]:
        await restart.send(f"开始重启{NICKNAME}..请稍等...")
        open("is_restart", "w")
        if str(platform.system()).lower() == "windows":
            import sys
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            os.system("./restart.sh")
    else:
        await restart.send("已取消操作...")


@scheduler.scheduled_job(
    "cron",
    hour=12,
    minute=0,
)
async def _():
    if Config.get_config("check_zhenxun_update", "UPDATE_REMIND"):
        _version = "v0.0.0"
        _version_file = Path() / "__version__"
        if _version_file.exists():
            _version = (
                open(_version_file, "r", encoding="utf8")
                .readline()
                .split(":")[-1]
                .strip()
            )
        data = await get_latest_version_data()
        if data:
            latest_version = data["name"]
            if _version != latest_version:
                bot = get_bot()
                await bot.send_private_msg(
                    user_id=int(list(bot.config.superusers)[0]),
                    message=f"检测到钟离版本更新\n"
                    f"当前版本：{_version}，最新版本：{latest_version}",
                )
                if Config.get_config("check_zhenxun_update", "AUTO_UPDATE_ZHENXUN"):
                    try:
                        code = await check_update(bot)
                    except Exception as e:
                        logger.error(f"更新钟离未知错误 {type(e)}：{e}")
                        await bot.send_private_msg(
                            user_id=int(list(bot.config.superusers)[0]),
                            message=f"更新钟离未知错误 {type(e)}：{e}\n",
                        )
                    else:
                        if code == 200:
                            await bot.send_private_msg(
                                user_id=int(list(bot.config.superusers)[0]),
                                message=f"更新完毕，请重启{NICKNAME}....",
                            )
