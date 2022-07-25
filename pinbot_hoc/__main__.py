from typing import Optional, Tuple
import discord
from discord import ForumChannel, TextChannel, CategoryChannel
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


async def get_channel_and_message_from_payload(payload: discord.RawReactionActionEvent) -> Optional[
        Tuple[ForumChannel | TextChannel | CategoryChannel, discord.Message]]:
    if payload.guild_id is None:
        logger.error('The guild was not found.')
        return None

    guild = client.get_guild(payload.guild_id)
    if guild is None:
        logger.error('The guild was not found.')
        return None

    channel = guild.get_channel(payload.channel_id)
    if channel is None:
        return None

    if not isinstance(channel, ForumChannel | TextChannel | CategoryChannel):
        logger.error('Invalid channel type.')
        return None

    message = channel.get_partial_message(payload.message_id)
    if message is None:
        logger.error('The expected message was not found.')
        channel.send(embed=discord.Embed(title='対象のメッセージが見つかりませんでした。'))
        return None

    target_message = await message.fetch()
    return channel, target_message


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    logger.info(
        f'A reaction was added to the message, added: {payload.emoji}')

    added_emoji = str(payload.emoji)

    if not(added_emoji == '📌' or added_emoji == '👎'):
        logger.info('The emoji is not pushpin.')
        return

    result = await get_channel_and_message_from_payload(payload)
    if result is None:
        logger.error('Channel or Message was not found.')
        return

    channel, message = result

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
        await channel.send(embed=discord.Embed(
            title='一定数の低評価が付いたため、ピン留めを解除しました',
            description=f'["ここをクリックすると対象のメッセージに移動できます"]({message.jump_url})'))
        await message.unpin()

    if added_emoji == '📌' and not message.pinned and not is_bad_message:
        logger.info('Pinned a message!')
        await message.pin()


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    logger.info(
        f'A reaction was removed from the message, removed: {payload.emoji}')

    if str(payload.emoji) != '📌':
        logger.info('The emoji is not pushpin.')
        return

    result = await get_channel_and_message_from_payload(payload)
    if result is None:
        return

    channel, message = result

    pin_reactions = [r for r in message.reactions if str(r) == '📌']

    logger.info(len(pin_reactions) > 0)

    if pin_reactions:
        logger.info(len(pin_reactions))
        return

    if message.pinned:
        await channel.send(embed=discord.Embed(
            title='ピン留めを解除しました',
            description=f'["ここをクリックすると対象のメッセージに移動できます"]({message.jump_url})'))
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
