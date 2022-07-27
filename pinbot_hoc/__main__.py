from typing import Optional
import discord
from discord import Guild, Message, RawReactionActionEvent, TextChannel, Thread
from utils import setup_logger
from configs import Environments

envs = Environments()

logger = setup_logger(__name__)


class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        await self.wait_until_ready()
        logger.info(f'Logged in as {self.user.name}')


client = Client()


def get_guild_from_payload(payload: RawReactionActionEvent) -> Optional[Guild]:
    """ リアクションイベントからギルド(サーバ)を取得する

    Args:
        payload (RawReactionActionEvent): イベント発火時の情報

    Returns:
        Optional[Guild]: ギルド
    """
    if payload.guild_id is None:
        logger.error('The guild was not found.')
        return None

    guild = client.get_guild(payload.guild_id)
    if guild is None:
        logger.error('The guild was not found.')
        return None

    return guild


def get_text_channel_from_payload(payload: RawReactionActionEvent) -> Optional[TextChannel]:
    """ リアクションイベントからテキストチャンネルを取得する

    Args:
        payload (RawReactionActionEvent): イベント発火時の情報

    Returns:
        Optional[TextChannel]: チャンネル
    """
    guild = get_guild_from_payload(payload)
    if guild is None:
        return None

    channel = guild.get_channel(payload.channel_id)
    if channel is None:
        logger.info('The channel was not found. It may be thread_id')
        return None

    if not isinstance(channel, TextChannel):
        logger.error('The channel is not TextChannel.')
        return None

    return channel


async def get_message_from_payload(payload: RawReactionActionEvent) -> Optional[Message]:
    """ リアクションイベントからメッセージを取得する

    Args:
        payload (RawReactionActionEvent): イベント発火時の情報

    Returns:
        Optional[Message]: メッセージ
    """
    channel = get_text_channel_from_payload(payload)
    thread = get_thread_from_payload(payload)
    if not (channel or thread):
        return None

    if channel:
        partial_message = channel.get_partial_message(payload.message_id)
    elif thread:
        partial_message = thread.get_partial_message(payload.message_id)
    else:
        logger.error('Channel or thread was not found.')

    message = await partial_message.fetch()

    return message


def get_thread_from_payload(payload: RawReactionActionEvent) -> Optional[Thread]:
    """ リアクションイベントからスレッドを取得する

    Args:
        payload (RawReactionActionEvent): イベント発火時の情報

    Returns:
        Optional[Thread]: スレッド
    """
    guild = get_guild_from_payload(payload)
    if guild is None:
        return None

    thread = guild.get_thread(payload.channel_id)
    if thread is None:
        logger.info('The thread was not found. It may be channel_id')
        return None

    return thread


@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    logger.info(
        f'A reaction was added to the message, added: {payload.emoji}')

    added_emoji = str(payload.emoji)

    if not(added_emoji == '📌' or added_emoji == '👎'):
        logger.info('The emoji is not pushpin or thumbsdown.')
        return

    channel = get_text_channel_from_payload(payload)
    thread = get_thread_from_payload(payload)
    message = await get_message_from_payload(payload)

    if not (message and (channel or thread)):
        logger.error('No message, channel, or thread.')
        return

    guild = get_guild_from_payload(payload)
    if not guild:
        return

    # :thumbsdown: が3つ以上付けられたメッセージはピン留めしない
    thumbsdown_reaction = [r for r in message.reactions if str(r) == '👎']
    is_bad_message = len(
        thumbsdown_reaction) > 0 and thumbsdown_reaction[0].count >= 3

    logger.info(thumbsdown_reaction)

    if thumbsdown_reaction:
        logger.info(thumbsdown_reaction[0].count)

    logger.info(is_bad_message)

    # 3つ目の :thumbsdown: が付いたタイミングでピン留めを解除する
    if added_emoji == '👎' and is_bad_message and message.pinned:
        embed = discord.Embed(
            title='一定数の低評価が付いたため、ピン留めを解除しました',
            description=f'[ここをクリックすると対象のメッセージに移動できます]({message.jump_url})')

        if thread:
            await thread.send(embed=embed)
        elif channel:
            await channel.send(embed=embed)
        else:
            logger.error('Something went wrong!!')
            return

        await message.unpin()

    if added_emoji == '📌' and not message.pinned and not is_bad_message:
        logger.info('Pinned a message!')
        await message.pin()


@client.event
async def on_raw_reaction_remove(payload: RawReactionActionEvent):
    logger.info(
        f'A reaction was removed from the message, removed: {payload.emoji}')

    if str(payload.emoji) != '📌':
        logger.info('The emoji is not pushpin.')
        return

    channel = get_text_channel_from_payload(payload)
    thread = get_thread_from_payload(payload)
    message = await get_message_from_payload(payload)

    if not (message and (channel or message)):
        return

    pin_reactions = [r for r in message.reactions if str(r) == '📌']

    logger.info(len(pin_reactions) > 0)

    if pin_reactions:
        logger.info(len(pin_reactions))
        return

    if message.pinned:
        embed = discord.Embed(
            title='ピン留めを解除しました',
            description=f'[ここをクリックすると対象のメッセージに移動できます]({message.jump_url})')

        if thread:
            await thread.send(embed=embed)
        elif channel:
            await channel.send(embed=embed)
        else:
            logger.error('Something went wrong!!')

        await message.unpin()

"""
TODO: スラッシュコマンドによるbotの説明を追加する。
      おそらく、botの権限設定でスラッシュコマンドを有効にしたうえで
      以下のコードのコメントアウトを外せば使えるようになる。
"""

# tree = app_commands.CommandTree(client)


# @tree.command(name='pinbot-help', description='pinbot-hokamonの使い方を表示します。')
# async def vox_test(interaction: discord.Interaction) -> None:
#     """ /pinbot-help """
#     await interaction.response.send_message(embed=discord.Embed(title="使用方法",
#                                                                 description="""
#     - ピン留めしたいメッセージに 📌 のリアクションをつけてください。
#     - ピン留めを解除するには、以下のうちどちらかの操作を行なってください:
#       A. すべての 📌 を外す
#       B. 👎 を3つ付ける
#     """))

client.run(token=envs.discord_token)
