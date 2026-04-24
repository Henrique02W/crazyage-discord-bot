import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "autorole_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"role_id": None}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()

        if not config["role_id"]:
            return

        role = member.guild.get_role(config["role_id"])

        if role:
            try:
                await member.add_roles(role, reason="AutoRole")
            except Exception as e:
                print(f"Erro ao dar cargo: {e}")

    @app_commands.command(name="autorole_set", description="Define o cargo automático")
    async def autorole_set(self, interaction: discord.Interaction, role: discord.Role):

        config = load_config()
        config["role_id"] = role.id
        save_config(config)

        await interaction.response.send_message(
            f"✅ Cargo automático definido: {role.mention}"
        )

    @app_commands.command(name="autorole_remove", description="Remove o cargo automático")
    async def autorole_remove(self, interaction: discord.Interaction):

        config = load_config()
        config["role_id"] = None
        save_config(config)

        await interaction.response.send_message("🗑 AutoRole removido.")


async def setup(bot):
    await bot.add_cog(AutoRole(bot))