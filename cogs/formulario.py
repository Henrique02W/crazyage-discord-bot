import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "form_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"panel_channel": None, "result_channel": None, "questions": []}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


class DynamicForm(discord.ui.Modal):
    def __init__(self, questions):
        super().__init__(title="Formulário")

        self.questions = questions
        self.inputs = []

        for q in questions[:5]:
            field = discord.ui.TextInput(label=q, required=True)
            self.add_item(field)
            self.inputs.append(field)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        channel = interaction.client.get_channel(config["result_channel"])

        embed = discord.Embed(title="📨 Nova resposta", color=discord.Color.blue())
        embed.add_field(name="Usuário", value=interaction.user.mention, inline=False)

        for i, field in enumerate(self.inputs):
            embed.add_field(name=self.questions[i], value=field.value, inline=False)

        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Formulário enviado!", ephemeral=True)


class FormView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir formulário",
        style=discord.ButtonStyle.green,
        custom_id="form_open"
    )
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()

        if not config["questions"]:
            return await interaction.response.send_message("❌ Nenhuma pergunta.", ephemeral=True)

        await interaction.response.send_modal(DynamicForm(config["questions"]))


async def question_autocomplete(interaction: discord.Interaction, current: str):
    config = load_config()
    return [
        app_commands.Choice(name=q, value=q)
        for q in config["questions"]
        if current.lower() in q.lower()
    ][:25]


class Formulario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(FormView())

    form = app_commands.Group(name="form", description="Sistema de formulário")

    @form.command(name="setpanel")
    async def setpanel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        config["panel_channel"] = channel.id
        save_config(config)

        await interaction.response.send_message(f"✅ Canal do painel: {channel.mention}")

    @form.command(name="setresult")
    async def setresult(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        config["result_channel"] = channel.id
        save_config(config)

        await interaction.response.send_message(f"✅ Canal de respostas: {channel.mention}")

    @form.command(name="addquestion")
    async def addquestion(self, interaction: discord.Interaction, pergunta: str):
        config = load_config()
        config["questions"].append(pergunta)
        save_config(config)

        await interaction.response.send_message(f"✅ Pergunta adicionada:\n{pergunta}")

    @form.command(name="removequestion")
    @app_commands.autocomplete(pergunta=question_autocomplete)
    async def removequestion(self, interaction: discord.Interaction, pergunta: str):
        config = load_config()

        if pergunta not in config["questions"]:
            return await interaction.response.send_message("❌ Pergunta não encontrada.", ephemeral=True)

        config["questions"].remove(pergunta)
        save_config(config)

        await interaction.response.send_message(f"🗑 Pergunta removida:\n{pergunta}")

    @form.command(name="painel")
    async def painel(self, interaction: discord.Interaction):
        config = load_config()

        if not config["panel_channel"]:
            return await interaction.response.send_message("❌ Defina o canal primeiro.", ephemeral=True)

        channel = self.bot.get_channel(config["panel_channel"])

        embed = discord.Embed(
            title="📋 Formulário",
            description="Clique no botão para responder.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=FormView())

        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Formulario(bot))