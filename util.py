import time
from discord_webhook import DiscordWebhook, DiscordEmbed


def safeCast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


def safeCastBool(val, default=False):
    try:
        return str(val).lower() in ['true', '1', 'y', 'yes']
    except Exception as e:
        return default


def isTimeFormat(inputTime):
    try:
        time.strptime(inputTime, '%H:%M')
        return True
    except Exception as e:
        return False


def notifyUser(color, config, notifyDiscord, titleMsg=None, descMsg=None):
    emoji = [":checkered_flag:", ":books:", ":wink:", "*"]
    titleMsgCmd = titleMsg
    descMsgCmd = descMsg

    if titleMsg is not None and descMsg is None:
        for e in emoji:
            titleMsgCmd = titleMsgCmd.replace(e, "").strip()
        print(titleMsgCmd)
    elif titleMsg is None and descMsg is not None:
        for e in emoji:
            descMsgCmd = descMsgCmd.replace(e, "").strip()
        print(descMsgCmd)
    elif titleMsg is not None and descMsg is not None:
        for e in emoji:
            titleMsgCmd = titleMsgCmd.replace(e, "").strip()
            descMsgCmd = descMsgCmd.replace(e, "").strip()
        print(f"{titleMsgCmd}. {descMsgCmd}")

    if notifyDiscord:
        webhook = DiscordWebhook(url=config.maintainerUrl)

        embedColor = color
        if titleMsg is not None and descMsg is None:
            embed = DiscordEmbed(title=titleMsg, color=embedColor)
        elif titleMsg is None and descMsg is not None:
            embed = DiscordEmbed(description=descMsg, color=embedColor)
        elif titleMsg is not None and descMsg is not None:
            embed = DiscordEmbed(title=titleMsg, description=descMsg, color=embedColor)

        webhook.add_embed(embed)

        try:
            webhook.execute()
        except Exception as e:
            print("ERROR: discord Url is not valid - you will still be getting info in the container logs!")
