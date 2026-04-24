import discord
from discord.ext import commands
from discord import app_commands
import json
import os

REACTION_DATA_FILE = "reaction_roles.json"

def load_reaction_data():
    if not os.path.exists(REACTION_DATA_FILE): return {}
    with open(REACTION_DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_reaction_data(data):
    with open(REACTION_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot: return
        
        data = load_reaction_data()
        msg_id = str(payload.message_id)
        emoji_str = str(payload.emoji)

        if msg_id in data and emoji_str in data[msg_id]:
            role_id = data[msg_id][emoji_str]
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id)
            
            if role:
                try:
                    await payload.member.add_roles(role)
                    try: await payload.member.send(f"✅ Você recebeu o cargo **{role.name}** em **{guild.name}**!")
                    except: pass
                except discord.Forbidden:
                    print(f"❌ Sem permissão para dar o cargo {role.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        data = load_reaction_data()
        msg_id = str(payload.message_id)
        emoji_str = str(payload.emoji)

        if msg_id in data and emoji_str in data[msg_id]:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if not member: return
            
            role_id = data[msg_id][emoji_str]
            role = guild.get_role(role_id)
            
            if role:
                try:
                    await member.remove_roles(role)
                    try: await member.send(f"⚠️ O cargo **{role.name}** foi removido de você em **{guild.name}**.")
                    except: pass
                except discord.Forbidden:
                    pass

    @app_commands.command(name="reaction_setup", description="Cria um novo menu de cargos por reação")
    @app_commands.describe(titulo="Título do Menu", descricao="Descrição inicial do menu")
    @commands.has_permissions(administrator=True)
    async def setup_menu(self, interaction: discord.Interaction, titulo: str, descricao: str):
        embed = discord.Embed(
            title=titulo,
            description=f"{descricao}\n\n**Cargos disponíveis:**\n(Aguardando adição de cargos...)",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Reaja abaixo para obter seus cargos")
        
        await interaction.response.send_message("✅ Criando menu...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        
        await interaction.followup.send(f"Menu criado! Use `/reaction_add` com o ID `{msg.id}` para adicionar cargos.", ephemeral=True)

    @app_commands.command(name="reaction_add", description="Vincula um emoji a um cargo e atualiza a mensagem")
    @app_commands.describe(
        message_id="O ID da mensagem do menu",
        emoji="O emoji que será usado",
        role="O cargo que o usuário receberá"
    )
    @commands.has_permissions(administrator=True)
    async def add_logic(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Mensagem não encontrada neste canal.", ephemeral=True)

        if not msg.embeds:
            return await interaction.response.send_message("❌ Essa mensagem não possui uma Embed para ser editada.", ephemeral=True)

        data = load_reaction_data()
        if message_id not in data: data[message_id] = {}
        data[message_id][emoji] = role.id
        save_reaction_data(data)

        embed = msg.embeds[0]
        
        new_description = ""
        if "**Cargos disponíveis:**" in embed.description:
            base_text = embed.description.split("**Cargos disponíveis:**")[0]
            new_description = base_text + "**Cargos disponíveis:**\n"
        else:
            new_description = embed.description + "\n\n**Cargos disponíveis:**\n"

        for e, r_id in data[message_id].items():
            new_description += f"{e} - <@&{r_id}>\n"

        embed.description = new_description

        try:
            await msg.add_reaction(emoji)
            await msg.edit(embed=embed)
            await interaction.response.send_message(f"✅ Sucesso! O cargo {role.mention} foi adicionado ao menu com o emoji {emoji}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao atualizar: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reactions(bot))