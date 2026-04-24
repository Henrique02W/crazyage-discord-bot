import discord
from discord import ui, app_commands
from discord.ext import commands
import asyncio
import io
import os
import logging
import random
import string
import json
from datetime import datetime
import chat_exporter

THUMBNAIL_ICON_URL = "https://media.discordapp.net/attachments/1431271313481404557/1455378630460047450/unnamed__26_-removebg-preview_1.png"

CONFIG_FILE = "config.json"
EMOJIS_FILE = "emojis.json"
EMOJIS_DIR = "./emojis" 
BANNER_FILENAME = "banner-ticket.png" 
TICKET_COUNT_FILE = "ticket_count.txt"
REVIEWS_FILE = "reviews.json"

# --- MAPA DE TRADUÇÃO ---
EMOJI_FILENAME_MAP = {
    "confirm": "certo",
    "cancel": "errado",
    "star": "estrela",
    "notes": "notas",
    "photo": "camera",
    "others": "livro",
    "trash": "sirene",
    "discord": "discord",
    "minecraft": "minecraft",
    "sites": "sites",
    "loading": "loading",
    "info": "info"
}

def load_emojis():
    if not os.path.exists(EMOJIS_FILE): return {}
    with open(EMOJIS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_emojis_to_file(data):
    with open(EMOJIS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

EMOJIS = load_emojis()

def get_emoji(logic_key):
    file_name = EMOJI_FILENAME_MAP.get(logic_key, logic_key)
    emoji_str = EMOJIS.get(file_name)
    defaults = {
        "confirm": "✅", "cancel": "❌", "star": "⭐", "notes": "📝", 
        "photo": "📷", "discord": "🤖", "minecraft": "🧱", "sites": "🌐", 
        "others": "📚", "loading": "⌛", "trash": "🗑️", "info": "ℹ️"
    }
    if not emoji_str: return defaults.get(logic_key, "❓")
    if emoji_str.startswith("<"):
        try: return discord.PartialEmoji.from_str(emoji_str)
        except: return defaults.get(logic_key, "❓")
    return emoji_str

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(data):
    current_config = load_config()
    current_config.update(data)
    with open(CONFIG_FILE, "w") as f: json.dump(current_config, f, indent=4)

def get_config(key): return load_config().get(key)

def get_next_ticket_number():
    if not os.path.exists(TICKET_COUNT_FILE):
        with open(TICKET_COUNT_FILE, "w") as f: f.write("0"); return 1
    with open(TICKET_COUNT_FILE, "r") as f:
        try: return int(f.read()) + 1
        except: return 1

def save_next_ticket_number(number):
    with open(TICKET_COUNT_FILE, "w") as f: f.write(str(number))

def generate_review_id():
    return f"#{''.join(random.choices(string.ascii_letters + string.digits, k=7))}"

def save_review(review_id, data):
    reviews = {}
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            try: reviews = json.load(f)
            except: pass
    reviews[review_id] = data
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f: json.dump(reviews, f, indent=4)

class ConfigWizardView(ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.step = 1
        self.setup_step()

    def setup_step(self):
        self.clear_items()
        
        if self.step == 1:
            btn = ui.Button(label="Continuar Instalação", style=discord.ButtonStyle.primary, emoji="🚀")
            btn.callback = self.callback_step_1_continue
            self.add_item(btn)

        elif self.step == 2:
            select = ui.RoleSelect(placeholder="Selecione o cargo...", min_values=1, max_values=1)
            select.callback = self.callback_step_2
            self.add_item(select)
        
        elif self.step == 3:
            select = ui.ChannelSelect(placeholder="Selecione a categoria...", channel_types=[discord.ChannelType.category], min_values=1, max_values=1)
            select.callback = self.callback_step_3
            self.add_item(select)

        elif self.step == 4:
            select = ui.ChannelSelect(placeholder="Selecione a categoria...", channel_types=[discord.ChannelType.category], min_values=1, max_values=1)
            select.callback = self.callback_step_4
            self.add_item(select)

        elif self.step == 5:
            select = ui.ChannelSelect(placeholder="Selecione o canal...", channel_types=[discord.ChannelType.text], min_values=1, max_values=1)
            select.callback = self.callback_step_5
            self.add_item(select)

        elif self.step == 6:
            select = ui.ChannelSelect(placeholder="Selecione o canal...", channel_types=[discord.ChannelType.text], min_values=1, max_values=1)
            select.callback = self.callback_step_6
            self.add_item(select)

    def get_embed(self):
        embed = discord.Embed(color=discord.Color.blue())
        
        if self.step == 1:
            embed.description = (
                "## `👋` `Bem-vindo à Instalação`\n\n"
                "> Clique em **Continuar** para configurar os canais e cargos do bot."
            )
        elif self.step == 2:
            embed.description = (
                "## `🛠️` `Configuração (2/6)`\n\n"
                "Por favor, selecione abaixo o **Cargo da Staff**.\n\n"
                "> Esse cargo será usado para conceder permissões às pessoas correspondentes, permitindo que visualizem e enviem mensagens nos tickets."
            )
        elif self.step == 3:
            embed.description = (
                "## `📂` `Configuração (3/6)`\n\n"
                "Agora, selecione a **Categoria** onde os novos tickets serão criados.\n\n"
                "> Sempre que um membro abrir um novo chamado pelo painel, o canal de texto correspondente será criado dentro desta categoria."
            )
        elif self.step == 4:
            embed.description = (
                "## `🗂️` `Configuração (4/6)`\n\n"
                "Selecione a **Categoria** para onde os tickets devem ser movidos após serem assumidos.\n\n"
                "> Quando um staff clicar no botão 'Assumir', o ticket sairá da categoria de abertos e irá para esta."
            )
        elif self.step == 5:
            embed.description = (
                "## `📜` `Configuração (5/6)`\n\n"
                "Selecione o **Canal de Texto** onde os registros (logs) serão enviados.\n\n"
                "> Ao finalizar um atendimento, o bot gera um arquivo HTML contendo todo o histórico da conversa."
            )
        elif self.step == 6:
            embed.description = (
                "## `⭐` `Configuração (6/6)`\n\n"
                "Por fim, selecione o **Canal de Texto** onde as avaliações serão publicadas.\n\n"
                "> Após o fechamento do ticket, o cliente recebe um formulário na DM. As estrelas e comentários aparecerão aqui."
            )
        return embed

    async def advance_step(self, interaction: discord.Interaction):
        self.step += 1
        if self.step > 6:
            final_embed = discord.Embed(
                description="## `✅` `Configuração Concluída!`\n\nO sistema foi configurado com sucesso.\n\n> Agora você pode usar `/ticket_panel` para enviar o painel.",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=final_embed, view=None)
        else:
            self.setup_step()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def callback_step_1_continue(self, interaction: discord.Interaction):
        await self.advance_step(interaction)

    async def callback_step_2(self, interaction: discord.Interaction):
        save_config({"staff_role_id": int(interaction.data['values'][0])})
        await self.advance_step(interaction)
    async def callback_step_3(self, interaction: discord.Interaction):
        save_config({"category_open_id": int(interaction.data['values'][0])})
        await self.advance_step(interaction)
    async def callback_step_4(self, interaction: discord.Interaction):
        save_config({"category_claimed_id": int(interaction.data['values'][0])})
        await self.advance_step(interaction)
    async def callback_step_5(self, interaction: discord.Interaction):
        save_config({"transcript_channel_id": int(interaction.data['values'][0])})
        await self.advance_step(interaction)
    async def callback_step_6(self, interaction: discord.Interaction):
        save_config({"feedback_channel_id": int(interaction.data['values'][0])})
        await self.advance_step(interaction)

class CommentModal(ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Deixe seu comentário")
        self.parent_view = parent_view
        self.comment = ui.TextInput(label="Comentário", style=discord.TextStyle.paragraph, required=False, max_length=500, default=parent_view.comment_text)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.comment_text = self.comment.value
        await interaction.response.defer(ephemeral=True)
        self.parent_view.update_buttons()
        await interaction.edit_original_response(view=self.parent_view)
        await interaction.followup.send(f"{get_emoji('notes')} Comentário salvo!", ephemeral=True)

class FeedbackView(ui.View):
    def __init__(self, ticket_id, handled_by):
        super().__init__(timeout=None)
        self.ticket_id, self.handled_by = ticket_id, handled_by
        self.step = 1
        self.service_stars = 0
        self.image_urls = []
        self.comment_text = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.step == 1:
            for i in range(1, 6):
                btn = ui.Button(label=str(i), emoji=get_emoji('star'), style=discord.ButtonStyle.secondary, custom_id=f"star_{i}")
                btn.callback = self.star_callback
                self.add_item(btn)
        elif self.step == 2:
            style_comm = discord.ButtonStyle.success if self.comment_text else discord.ButtonStyle.secondary
            btn_comm = ui.Button(label="Comentário", emoji=get_emoji('notes'), style=style_comm)
            btn_comm.callback = self.comment_callback
            self.add_item(btn_comm)
            
            style_img = discord.ButtonStyle.success if len(self.image_urls) > 0 else discord.ButtonStyle.secondary
            label_img = f"{len(self.image_urls)} Imagens" if len(self.image_urls) > 0 else "Anexar Imagens"
            btn_img = ui.Button(label=label_img, emoji=get_emoji('photo'), style=style_img)
            btn_img.callback = self.image_callback
            self.add_item(btn_img)
            
            btn_fin = ui.Button(label="Finalizar", emoji=get_emoji('confirm'), style=discord.ButtonStyle.success)
            btn_fin.callback = self.finish_callback
            self.add_item(btn_fin)

    async def star_callback(self, interaction: discord.Interaction):
        self.service_stars = int(interaction.data['custom_id'].split('_')[1])
        self.step = 2 
        embed = interaction.message.embeds[0]
        embed.clear_fields()
        embed.add_field(name="(2/2) Detalhes Finais", value="Se desejar, deixe um comentário ou foto abaixo e clique em **Finalizar**.", inline=False)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def image_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{get_emoji('photo')} **Envie as imagens no chat agora (60s).**", ephemeral=True)
        try:
            msg = await interaction.client.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel and m.attachments, timeout=60)
            self.image_urls.extend([a.url for a in msg.attachments])
            self.update_buttons()
            try: await interaction.message.edit(view=self)
            except: pass
            await interaction.followup.send(f"{get_emoji('confirm')} Salvo!", ephemeral=True)
        except: await interaction.followup.send(f"{get_emoji('cancel')} Tempo esgotado.", ephemeral=True)

    async def comment_callback(self, interaction: discord.Interaction): await interaction.response.send_modal(CommentModal(self))

    async def finish_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rid = generate_review_id()
        rdata = {"user": interaction.user.name, "stars": self.service_stars, "comment": self.comment_text or "Sem comentário", "imgs": self.image_urls, "staff": self.handled_by, "tid": self.ticket_id, "date": str(datetime.now())}
        save_review(rid, rdata)
        
        fid = get_config("feedback_channel_id")
        if fid and (chan := interaction.client.get_channel(int(fid))):
            color = discord.Color.green() if self.service_stars == 5 else (discord.Color.orange() if self.service_stars >= 3 else discord.Color.red())
            embed = discord.Embed(title="Nova Avaliação", color=color)
            embed.set_author(name=f"{interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="Nota", value=f"{str(get_emoji('star')) * self.service_stars}")
            embed.add_field(name="Staff", value=self.handled_by)
            embed.add_field(name="Ticket", value=self.ticket_id)
            embed.description = f"**Comentário:**\n```{rdata['comment']}```"
            
            guild = chan.guild
            icon_url = guild.icon.url if guild.icon else None
            embed.set_footer(text=f"© {guild.name}. All rights reserved.", icon_url=icon_url)

            if self.image_urls: embed.set_image(url=self.image_urls[0])
            msg = await chan.send(embed=embed)
            try: await msg.create_thread(name=f"Avaliação {rid}", auto_archive_duration=1440)
            except: pass
        
        await interaction.edit_original_response(embed=discord.Embed(title="Obrigado!", description=f"{get_emoji('confirm')} Avaliação enviada.", color=discord.Color.green()), view=None)


class TicketActionsView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        try:
            self.children[0].emoji = get_emoji('cancel')
            self.children[1].emoji = get_emoji('confirm')
            self.children[2].emoji = get_emoji('info')
        except: pass
    
    async def check_staff(self, interaction):
        sid = get_config("staff_role_id")
        return False if not sid else interaction.guild.get_role(int(sid)) in interaction.user.roles

    @ui.button(label="Fechar", style=discord.ButtonStyle.danger, custom_id="close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction): return await interaction.response.send_message("❌ Apenas Staff.", ephemeral=True)
        await interaction.response.defer()
        
        tid = get_config("transcript_channel_id")
        tchan = interaction.guild.get_channel(int(tid)) if tid else None
        
        try:
            topic_data = interaction.channel.topic.split(" | ")
            uid = int(topic_data[1].replace("Aberto por: ", ""))
            ticket_owner = await interaction.guild.fetch_member(uid)
        except: ticket_owner = None

        handler = "Staff"
        async for m in interaction.channel.history(limit=50):
            if m.embeds and "Ticket Assumido Por" in str(m.embeds[0].to_dict()):
                for f in m.embeds[0].fields:
                    if f.name == "Ticket Assumido Por": handler = f.value
        
        try:
            transcript = await chat_exporter.export(interaction.channel, limit=None, bot=interaction.client)
            tfile = discord.File(io.BytesIO(transcript.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.html")
            
            if tchan: 
                log = discord.Embed(title=f"Ticket Fechado: {interaction.channel.name}", color=discord.Color.red())
                log.add_field(name="Fechado por", value=interaction.user.mention)
                log.add_field(name="Dono", value=ticket_owner.mention if ticket_owner else "N/A")
                await tchan.send(embed=log, file=tfile)

            if ticket_owner:
                dm_file = discord.File(io.BytesIO(transcript.encode("utf-8")), filename=f"transcript-{interaction.channel.name}.html")
                embed = discord.Embed(title="Atendimento Finalizado", description="Avalie nosso atendimento abaixo.", color=discord.Color.blue())
                embed.add_field(name="Atendido por", value=handler)
                
                icon_url = interaction.guild.icon.url if interaction.guild.icon else None
                embed.set_footer(text=f"© {interaction.guild.name}. All rights reserved.", icon_url=icon_url)
                
                await ticket_owner.send(embed=embed, file=dm_file, view=FeedbackView(interaction.channel.name, handler))
        except Exception as e: print(f"Erro transcript/DM: {e}")

        await interaction.followup.send(f"## {get_emoji('cancel')} `Fechando Ticket...`\n\n> O canal será deletado em 5 segundos.")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @ui.button(label="Assumir", style=discord.ButtonStyle.success, custom_id="claim_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction): return await interaction.response.send_message("❌ Apenas Staff.", ephemeral=True)
        
        async for m in interaction.channel.history(limit=5, oldest_first=True):
            if m.author == interaction.client.user and m.embeds:
                embed = m.embeds[0]
                if any(f.name == "Ticket Assumido Por" for f in embed.fields):
                    return await interaction.response.send_message("Já assumido!", ephemeral=True)
                embed.add_field(name="Ticket Assumido Por", value=interaction.user.mention, inline=False)
                button.disabled = True
                await m.edit(embed=embed, view=self)
                break
        
        cat_id = get_config("category_claimed_id")
        if cat_id: 
            try: await interaction.channel.edit(category=interaction.guild.get_channel(int(cat_id)))
            except: pass
        
        await interaction.response.send_message(f"## {get_emoji('confirm')} `Ticket Assumido!`\n\n> O staff {interaction.user.mention} assumiu a responsabilidade por este chamado.")

    @ui.button(label="Informações", style=discord.ButtonStyle.secondary, custom_id="info_btn")
    async def info_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(f"## {get_emoji('info')} `Informações do Ticket`\n\n> **Canal:** {interaction.channel.mention}\n> **ID:** `{interaction.channel.id}`", ephemeral=True)

class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        emoji = get_emoji('others')
        btn = ui.Button(label="Abrir Ticket", style=discord.ButtonStyle.secondary, custom_id="ticket_open_btn", emoji=emoji)
        btn.callback = self.open_ticket_callback
        self.add_item(btn)

    async def open_ticket_callback(self, interaction: discord.Interaction):
        # 1. Carrega Configs
        sid = get_config("staff_role_id")
        cid = get_config("category_open_id")

        if not sid or not cid: 
            return await interaction.response.send_message("❌ O sistema não foi configurado corretamente. Use `/config_ticket`.", ephemeral=True)

        open_category = interaction.guild.get_channel(int(cid))
        if not open_category:
            return await interaction.response.send_message("❌ A categoria de tickets configurada não existe mais.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        if any(c.topic and str(interaction.user.id) in c.topic for c in open_category.text_channels):
            return await interaction.followup.send(f"{get_emoji('cancel')} Você já possui um ticket aberto!", ephemeral=True)

        tnum = get_next_ticket_number()
        save_next_ticket_number(tnum)
        
        staff = interaction.guild.get_role(int(sid))
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            staff: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True) if staff else discord.PermissionOverwrite(read_messages=True)
        }
        
        chan = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}", category=open_category, overwrites=overwrites,
            topic=f"Ticket ID: #{tnum} | Aberto por: {interaction.user.id}"
        )

        embed = discord.Embed(title="Obrigado por contatar o suporte!", color=discord.Color.dark_green())
        embed.description = (
            f"Obrigado pela colaboração e paciência, {interaction.user.mention}!\n\n"
            "**No ticket, inclua:**\n"
            "- Descrição clara do problema.\n"
            "- Prints, logs ou provas relevantes.\n"
            "- Nomes dos envolvidos (se houver).\n"
            "- O que já tentou para resolver.\n\n"
            "**Processo:**\n"
            "- Um atendente analisará e responderá o mais rápido possível.\n"
            "- Podemos pedir mais informações.\n"
            "- Após solução, o ticket será fechado. Para mais ajuda, abra outro ticket."
        )
        
        icon_url = interaction.guild.icon.url if interaction.guild.icon else None
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text=f"© {interaction.guild.name}. All rights reserved.", icon_url=icon_url)

        banner_path = os.path.join(EMOJIS_DIR, BANNER_FILENAME)
        file_to_send = None
        if os.path.exists(banner_path):
            file_to_send = discord.File(banner_path, filename=BANNER_FILENAME)
            embed.set_image(url=f"attachment://{BANNER_FILENAME}")

        view = TicketActionsView()
        
        if file_to_send:
            await chan.send(content=interaction.user.mention, embed=embed, view=view, file=file_to_send)
        else:
            await chan.send(content=interaction.user.mention, embed=embed, view=view)
        
        await interaction.followup.send(f"## {get_emoji('confirm')} `Ticket criado com sucesso!`\n\n> O seu canal foi criado com sucesso: {chan.mention}", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketPanelView())
        view = TicketActionsView()
        try:
            view.children[0].emoji = get_emoji('cancel')
            view.children[1].emoji = get_emoji('confirm')
            view.children[2].emoji = get_emoji('info')
        except: pass
        self.bot.add_view(view)

    @app_commands.command(name="setup_emojis", description="Instala os recursos visuais (emojis e banner) no servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_emojis(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not os.path.exists(EMOJIS_DIR): return await interaction.followup.send(f"❌ Pasta `{EMOJIS_DIR}` não encontrada.")

        guild = interaction.guild
        uploaded_count = 0
        current_emojis = load_emojis()
        files = os.listdir(EMOJIS_DIR)
        
        if not files: return await interaction.followup.send("❌ Pasta vazia.")
        msg = await interaction.followup.send(f"⏳ Instalando emojis...")
        
        for filename in files:
            if "banner" in filename.lower(): continue

            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                emoji_name = os.path.splitext(filename)[0]
                file_path = os.path.join(EMOJIS_DIR, filename)
                existing_str = current_emojis.get(emoji_name)
                exists_in_guild = False
                if existing_str and existing_str.startswith("<"):
                    try:
                        if guild.get_emoji(int(existing_str.split(":")[-1].replace(">", ""))): exists_in_guild = True
                    except: pass
                
                if not exists_in_guild:
                    try:
                        with open(file_path, "rb") as image_file: image_data = image_file.read()
                        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=image_data)
                        current_emojis[emoji_name] = str(new_emoji)
                        uploaded_count += 1
                        print(f"Instalado: {emoji_name}")
                        await asyncio.sleep(1.0)
                    except Exception as e: print(f"Erro ao instalar {emoji_name}: {e}")
        
        save_emojis_to_file(current_emojis)
        global EMOJIS; EMOJIS = current_emojis
        await interaction.followup.send(f"✅ **{uploaded_count}** emojis instalados/atualizados!")

    @app_commands.command(name="config_ticket", description="Inicia o assistente de configuração do sistema de atendimento.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_ticket(self, interaction: discord.Interaction):
        view = ConfigWizardView()
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    @app_commands.command(name="ticket_panel", description="Envia o painel de atendimento para o canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="Central de Atendimento", color=discord.Color.from_rgb(47, 49, 54))
        embed.description = """
        Seja bem-vindo(a) à nossa Central de Atendimento!
        
        Para iniciar seu **atendimento**, clique no botão abaixo.
        Um novo canal será criado para que você possa falar diretamente com nossa equipe.
        """
        embed.add_field(name="**Instruções**", value="> - Descreva seu pedido de forma clara.\n> - Aguarde pacientemente.", inline=False)
        embed.add_field(name="**Horário de atendimento**", value="> `08:00 – 21:00`", inline=False)
        
        icon_url = interaction.guild.icon.url if interaction.guild.icon else None
        embed.set_thumbnail(url=icon_url)
        embed.set_footer(text=f"© {interaction.guild.name}. All rights reserved.", icon_url=icon_url)

        banner_path = os.path.join(EMOJIS_DIR, BANNER_FILENAME)
        file_to_send = None
        
        if os.path.exists(banner_path):
            file_to_send = discord.File(banner_path, filename=BANNER_FILENAME)
            embed.set_image(url=f"attachment://{BANNER_FILENAME}")
        
        if file_to_send:
            await interaction.channel.send(embed=embed, view=TicketPanelView(), file=file_to_send)
        else:
            await interaction.channel.send(embed=embed, view=TicketPanelView())

        await interaction.followup.send("Painel enviado!", ephemeral=True)

async def setup(bot): await bot.add_cog(TicketSystem(bot))
