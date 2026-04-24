import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime

try:
    from mcstatus import JavaServer, BedrockServer
    HAS_MCSTATUS = True
except ImportError:
    HAS_MCSTATUS = False

MC_CONFIG_FILE = "minecraft_config.json"

def load_mc_config():
    if not os.path.exists(MC_CONFIG_FILE): 
        return {"ip": "jogar.seuservidor.com", "port": 25565, "type": "java", "live_channel": None, "live_msg": None}
    with open(MC_CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {"ip": "jogar.seuservidor.com", "port": 25565, "type": "java", "live_channel": None, "live_msg": None}

def save_mc_config(data):
    with open(MC_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_update_status.start()

    def cog_unload(self):
        self.auto_update_status.cancel()

    async def get_server_status(self, config):
        """Helper para consultar o servidor de forma assíncrona."""
        try:
            if config['type'] == "java":
                server = JavaServer.lookup(f"{config['ip']}:{config['port']}")
            else:
                server = BedrockServer.lookup(f"{config['ip']}:{config['port']}")
            
            status = await server.async_status()
            return status, True
        except:
            return None, False

    @tasks.loop(seconds=60)
    async def auto_update_status(self):
        """Tarefa que atualiza a mensagem de status e a presença do bot."""
        if not HAS_MCSTATUS: return
        
        config = load_mc_config()
        status, online = await self.get_server_status(config)
        
        if online:
            await self.bot.change_presence(activity=discord.Game(name=f"🎮 {status.players.online} Players Online"))
        else:
            await self.bot.change_presence(activity=discord.Game(name="🔴 Servidor Offline"))

        if config.get("live_channel") and config.get("live_msg"):
            try:
                channel = self.bot.get_channel(config["live_channel"])
                if not channel: return
                
                msg = await channel.fetch_message(config["live_msg"])
                embed = self.create_status_embed(status, online, config)
                await msg.edit(content=None, embed=embed)
            except Exception as e:
                print(f"Erro ao atualizar live status: {e}")

    def create_status_embed(self, status, online, config):
        """Cria uma embed padronizada de status."""
        if online:
            embed = discord.Embed(
                title="⛏️ Status do Servidor",
                description=f"### {status.motd.to_plain()}\n\n**IP:** `{config['ip']}`\n**Tipo:** `{config['type'].upper()}`",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="📌 Status", value="🟢 **Online**", inline=True)
            embed.add_field(name="👥 Jogadores", value=f"`{status.players.online}/{status.players.max}`", inline=True)
            embed.add_field(name="📶 Latência", value=f"`{round(status.latency)}ms`", inline=True)
            
            if hasattr(status.players, 'sample') and status.players.sample:
                player_list = ", ".join([p.name for p in status.players.sample])
                embed.add_field(name="👤 Jogando agora", value=f"```{player_list}```", inline=False)
            
            embed.set_footer(text="Última atualização")
            return embed
        else:
            embed = discord.Embed(
                title="⛏️ Status do Servidor",
                description=f"🔴 **O servidor está atualmente offline.**\n\n**IP:** `{config['ip']}`",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Tentando reconectar...")
            return embed

    @app_commands.command(name="mc_setup", description="Configura os dados básicos do servidor")
    @commands.has_permissions(administrator=True)
    async def mc_setup(self, interaction: discord.Interaction, ip: str, porta: int = 25565, tipo: str = "java"):
        config = load_mc_config()
        config.update({"ip": ip, "port": porta, "type": tipo.lower()})
        save_mc_config(config)
        await interaction.response.send_message(f"✅ Configurações salvas para `{ip}:{porta}`!", ephemeral=True)

    @app_commands.command(name="mc_live_setup", description="Cria um canal de status que se atualiza sozinho")
    @commands.has_permissions(administrator=True)
    async def mc_live(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        config = load_mc_config()
        status, online = await self.get_server_status(config)
        embed = self.create_status_embed(status, online, config)
        
        msg = await interaction.channel.send(embed=embed)
        
        config["live_channel"] = interaction.channel.id
        config["live_msg"] = msg.id
        save_mc_config(config)
        
        await interaction.followup.send("✅ Canal de status configurado! Esta mensagem será atualizada a cada minuto.", ephemeral=True)

    @app_commands.command(name="status", description="Veja o status atual do servidor")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        config = load_mc_config()
        status, online = await self.get_server_status(config)
        embed = self.create_status_embed(status, online, config)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Minecraft(bot))