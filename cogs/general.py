import discord
from discord.ext import commands
from discord import app_commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='say', description="Envia uma mensagem em Embed para um canal específico")
    @app_commands.describe(
        channel="O canal de destino", 
        message="O texto da Embed (use \\n para pular linha)",
        mostrar_autor="Se deve mostrar quem enviou a mensagem (Padrão: Sim)"
    )
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, channel: discord.TextChannel, mostrar_autor: bool = True, *, message: str):
        try:
            processed_message = message.replace('\\n', '\n')

            embed = discord.Embed(
                description=processed_message,
                color=discord.Color.blue(),
                timestamp=ctx.message.created_at if ctx.message else discord.utils.utcnow()
            )
            
            if mostrar_autor:
                embed.set_author(
                    name=ctx.author.display_name, 
                    icon_url=ctx.author.display_avatar.url
                )
            
            embed.set_footer(text=f"Enviado via {self.bot.user.name}")

            await channel.send(embed=embed)
            
            if ctx.interaction:
                await ctx.send(f"✅ Embed enviada para {channel.mention}!", ephemeral=True)
            else:
                await ctx.message.delete()
                
        except discord.Forbidden:
            await ctx.send("❌ Sem permissão para enviar Embeds ou falar nesse canal.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Erro ao enviar: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))