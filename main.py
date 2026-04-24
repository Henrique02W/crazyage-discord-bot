import discord
import os
from discord.ext import commands

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        self.TEST_GUILD = discord.Object(id=1493616458373009549) 
        super().__init__(command_prefix='!', intents=intents, help_command=None)

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        self.tree.copy_global_to(guild=self.TEST_GUILD)
        await self.tree.sync(guild=self.TEST_GUILD)

    async def on_ready(self):
        print(f'🚀 Bot Online: {self.user}')

bot = MyBot()
if __name__ == "__main__":
    TOKEN = 'MTA0MDMyOTg0MzU2NjQ0ODc4Mg.GzW9Pc.AVSx786zjVo09E3NmijZA9Nf7qY7wUw--EjXSo'
    bot.run(TOKEN)