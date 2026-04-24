import discord
from discord import ui, app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

SUGGESTION_CONFIG_FILE = "suggestion_config.json"

def load_config():
    if not os.path.exists(SUGGESTION_CONFIG_FILE): return {}
    with open(SUGGESTION_CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    with open(SUGGESTION_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_suggestion_config(key): return load_config().get(key)

class SuggestionModal(ui.Modal, title="💡 Enviar Sugestão"):
    sugestao = ui.TextInput(
        label="Sua sugestão",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva sua ideia em detalhes...",
        required=True,
        min_length=10,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        channel_id = config.get("suggestion_channel_id")
        if not channel_id:
            return await interaction.response.send_message("❌ O canal de sugestões não foi configurado!", ephemeral=True)

        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Canal de sugestões não encontrado!", ephemeral=True)

        embed = discord.Embed(
            title="💡 Nova Sugestão",
            description=self.sugestao.value,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Status", value="⌛ Aguardando avaliação", inline=False)
        embed.add_field(name="Votos", value="👍 0 | 👎 0", inline=True)
        embed.set_footer(text=f"ID do Usuário: {interaction.user.id}")

        view = SuggestionVoteView()
        msg = await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(f"✅ Sua sugestão foi enviada para {channel.mention}!", ephemeral=True)

# --- VIEW DE VOTAÇÃO E STAFF ---
class SuggestionVoteView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Concordo", style=discord.ButtonStyle.success, emoji="👍", custom_id="suggest_up")
    async def upvote(self, interaction: discord.Interaction, button: ui.Button):
        embed = interaction.message.embeds[0]
        votes_field = embed.fields[1].value
        up, down = [int(s.strip()) for s in votes_field.replace("👍", "").replace("👎", "").split("|")]
        
        embed.set_field_at(1, name="Votos", value=f"👍 {up + 1} | 👎 {down}", inline=True)
        await interaction.response.edit_message(embed=embed)

    @ui.button(label="Discordo", style=discord.ButtonStyle.danger, emoji="👎", custom_id="suggest_down")
    async def downvote(self, interaction: discord.Interaction, button: ui.Button):
        embed = interaction.message.embeds[0]
        votes_field = embed.fields[1].value
        up, down = [int(s.strip()) for s in votes_field.replace("👍", "").replace("👎", "").split("|")]
        
        embed.set_field_at(1, name="Votos", value=f"👍 {up} | 👎 {down + 1}", inline=True)
        await interaction.response.edit_message(embed=embed)

    @ui.button(label="Gerenciar", style=discord.ButtonStyle.secondary, emoji="🛠️", custom_id="suggest_manage")
    async def manage(self, interaction: discord.Interaction, button: ui.Button):
        staff_id = get_suggestion_config("staff_role_id")
        if not staff_id or interaction.guild.get_role(staff_id) not in interaction.user.roles:
            return await interaction.response.send_message("Apenas a Staff pode gerenciar sugestões!", ephemeral=True)
        
        view = SuggestionAdminActions(interaction.message)
        await interaction.response.send_message("Escolha uma ação para esta sugestão:", view=view, ephemeral=True)

class SuggestionAdminActions(ui.View):
    def __init__(self, original_msg):
        super().__init__(timeout=60)
        self.original_msg = original_msg

    @ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        embed = self.original_msg.embeds[0]
        embed.color = discord.Color.green()
        embed.set_field_at(0, name="Status", value="✅ **Aprovada pela Staff**", inline=False)
        
        await self.original_msg.edit(embed=embed, view=None)
        await interaction.response.edit_message(content="✅ Sugestão aprovada!", view=None)

    @ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        embed = self.original_msg.embeds[0]
        embed.color = discord.Color.red()
        embed.set_field_at(0, name="Status", value="❌ **Negada pela Staff**", inline=False)
        
        await self.original_msg.edit(embed=embed, view=None)
        await interaction.response.edit_message(content="❌ Sugestão negada!", view=None)

class SuggestConfigWizard(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.step = 1

    def get_embed(self):
        steps = {
            1: "## 💡 Setup de Sugestões (1/2)\nSelecione o **Canal** onde as sugestões serão postadas.",
            2: "## 🛡️ Setup de Sugestões (2/2)\nSelecione o **Cargo Staff** que poderá aprovar/negar."
        }
        return discord.Embed(description=steps[self.step], color=discord.Color.blue())

    def update_view(self):
        self.clear_items()
        if self.step == 1:
            s = ui.ChannelSelect(placeholder="Canal de Sugestões", channel_types=[discord.ChannelType.text])
            s.callback = self.save_channel
            self.add_item(s)
        elif self.step == 2:
            s = ui.RoleSelect(placeholder="Cargo para gerenciar", min_values=1, max_values=1)
            s.callback = self.save_role
            self.add_item(s)

    async def save_channel(self, interaction):
        config = load_config()
        config["suggestion_channel_id"] = int(interaction.data['values'][0])
        save_config(config)
        self.step = 2
        self.update_view()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def save_role(self, interaction):
        config = load_config()
        config["staff_role_id"] = int(interaction.data['values'][0])
        save_config(config)
        await interaction.response.edit_message(content="✅ Sistema de Sugestões configurado!", embed=None, view=None)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Envia uma sugestão para o servidor")
    async def suggest(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestionModal())

    @app_commands.command(name="suggestion_config", description="Configura o sistema de sugestões")
    @commands.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        view = SuggestConfigWizard()
        view.update_view()
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))