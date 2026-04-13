import discord
from discord.ext import commands
import json
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import config

# ─── Fake HTTP server για Render ──────────────────────────────────────────────
# Το Render χρειάζεται έναν HTTP server αλλιώς κλείνει το service

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Bot is alive!')

    def log_message(self, format, *args):
        pass  # Απόκρυψη HTTP logs

def run_http_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f'🌐 HTTP server listening on port {port}')
    server.serve_forever()

# Ξεκίνα τον fake HTTP server σε background thread
threading.Thread(target=run_http_server, daemon=True).start()

# ─── Bot Setup ────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ─── Categories ───────────────────────────────────────────────────────────────

CATEGORIES = {
    'talk_owner':   {'label': '💬 Talk to Owner',  'emoji': '💬', 'color': discord.Color.from_rgb(88, 101, 242),  'description': 'Speak directly with the server owner.'},
    'ban_appeal':   {'label': '⚖️ Ban Appeal',      'emoji': '⚖️', 'color': discord.Color.from_rgb(237, 66, 69),   'description': 'Appeal your ban from the server.'},
    'donate':       {'label': '💎 Donate',          'emoji': '💎', 'color': discord.Color.from_rgb(255, 215, 0),   'description': 'Support the server with a donation.'},
    'bug':          {'label': '🐛 Bug Report',      'emoji': '🐛', 'color': discord.Color.from_rgb(87, 242, 135),  'description': 'Report a bug or technical issue.'},
    'support':      {'label': '🎫 Support',         'emoji': '🎫', 'color': discord.Color.from_rgb(0, 176, 244),   'description': 'Get general support from our staff.'},
    'staff_report': {'label': '🚨 Staff Report',    'emoji': '🚨', 'color': discord.Color.from_rgb(254, 231, 92),  'description': "Report a staff member's behaviour."},
}

HIGH_RANK_ONLY = {'talk_owner', 'ban_appeal', 'donate'}

# ─── JSON helpers ─────────────────────────────────────────────────────────────

def load_json(path, default):
    if not os.path.exists(path):
        save_json(path, default)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_log(action: str, details: str):
    logs = load_json('logs.json', [])
    logs.append({'action': action, 'details': details, 'timestamp': datetime.utcnow().isoformat()})
    save_json('logs.json', logs)

def next_ticket_number() -> str:
    logs = load_json('logs.json', [])
    count = len([l for l in logs if l['action'] == 'OPEN']) + 1
    return str(count).zfill(4)

# ─── Role helpers ─────────────────────────────────────────────────────────────

def has_high_rank(member: discord.Member) -> bool:
    names = {config.ROLE_FOUNDER, config.ROLE_CO_FOUNDER, config.ROLE_OWNER, config.ROLE_CO_OWNER}
    return any(r.name in names for r in member.roles) or member.guild_permissions.administrator

def is_staff(member: discord.Member) -> bool:
    return any(r.name == config.ROLE_STAFF for r in member.roles) or has_high_rank(member)

def build_overwrites(guild: discord.Guild, category: str, ticket_owner: discord.Member) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ticket_owner: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    for rname in [config.ROLE_FOUNDER, config.ROLE_CO_FOUNDER, config.ROLE_OWNER, config.ROLE_CO_OWNER]:
        role = discord.utils.get(guild.roles, name=rname)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, manage_messages=True
            )
    if category not in HIGH_RANK_ONLY:
        staff_role = discord.utils.get(guild.roles, name=config.ROLE_STAFF)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
    return overwrites

# ─── Close helper ─────────────────────────────────────────────────────────────

async def do_close(channel: discord.TextChannel, closed_by: discord.Member, guild: discord.Guild):
    tickets = load_json('tickets.json', {})
    ticket = tickets.get(str(channel.id))
    if not ticket:
        return False

    add_log('CLOSE', f"Ticket #{ticket['number']} ({ticket['category']}) closed by {closed_by}")

    if config.LOG_CHANNEL_ID:
        log_ch = guild.get_channel(config.LOG_CHANNEL_ID)
        if log_ch:
            cat = CATEGORIES.get(ticket['category'], {})
            log_embed = discord.Embed(title='🔒 Ticket Closed', color=discord.Color.red(), timestamp=datetime.utcnow())
            log_embed.add_field(name='Ticket #', value=f"`{ticket['number']}`", inline=True)
            log_embed.add_field(name='Category', value=cat.get('label', ticket['category']), inline=True)
            log_embed.add_field(name='Closed by', value=closed_by.mention, inline=True)
            await log_ch.send(embed=log_embed)

    del tickets[str(channel.id)]
    save_json('tickets.json', tickets)
    return True

# ─── Dropdown ─────────────────────────────────────────────────────────────────

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=v['label'], value=k, emoji=v['emoji'], description=v['description'])
            for k, v in CATEGORIES.items()
        ]
        super().__init__(
            custom_id='ticket_category',
            placeholder='📂  Επίλεξε κατηγορία...',
            min_values=1, max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        cat = CATEGORIES[category]
        member = interaction.user
        guild = interaction.guild

        await interaction.response.defer(ephemeral=True)

        tickets = load_json('tickets.json', {})
        existing = next((t for t in tickets.values() if t['owner_id'] == member.id and t['category'] == category), None)
        if existing:
            return await interaction.followup.send(
                f"❌ Έχεις ήδη ανοιχτό **{cat['label']}** ticket! <#{existing['channel_id']}>", ephemeral=True
            )

        ticket_number = next_ticket_number()
        safe_name = ''.join(c for c in member.name.lower() if c.isalnum())[:20] or 'user'
        cat_slug = category.replace('_', '-')
        channel_name = f"{cat['emoji']}・{safe_name}-{cat_slug}-{ticket_number}"

        cat_channel = guild.get_channel(config.TICKET_CATEGORY_ID) if config.TICKET_CATEGORY_ID else None

        channel = await guild.create_text_channel(
            name=channel_name,
            category=cat_channel,
            overwrites=build_overwrites(guild, category, member),
        )

        tickets[str(channel.id)] = {
            'channel_id': channel.id,
            'owner_id': member.id,
            'category': category,
            'number': ticket_number,
            'opened_at': datetime.utcnow().isoformat(),
        }
        save_json('tickets.json', tickets)
        add_log('OPEN', f"Ticket #{ticket_number} ({category}) opened by {member}")

        # Server icon ως thumbnail
        server_icon = config.SERVER_ICON or (str(guild.icon.url) if guild.icon else None)

        embed = discord.Embed(
            title=f"{cat['emoji']}  {cat['label']}",
            description=(
                f"> Καλώς ήρθες {member.mention}! Ένα μέλος του staff θα σε εξυπηρετήσει σύντομα.\n\n"
                f"**👤 Χρήστης:** {member.mention} (`{member}`)\n"
                f"**📂 Κατηγορία:** {cat['label']}\n"
                f"**🎫 Ticket #:** `{ticket_number}`\n"
                f"**📅 Ανοίχτηκε:** <t:{int(datetime.utcnow().timestamp())}:F>\n\n"
                f"📌 Περίγραψε το πρόβλημά σου παρακάτω.\n"
                f"🔒 Πάτα το κουμπί **Close Ticket** για να κλείσεις."
            ),
            color=cat['color'],
            timestamp=datetime.utcnow(),
        )
        if server_icon:
            embed.set_thumbnail(url=server_icon)
        embed.set_footer(text=f"{guild.name} • Ticket System", icon_url=member.display_avatar.url)

        # Ping roles
        pings = []
        for rname in [config.ROLE_FOUNDER, config.ROLE_CO_FOUNDER, config.ROLE_OWNER, config.ROLE_CO_OWNER]:
            r = discord.utils.get(guild.roles, name=rname)
            if r:
                pings.append(r.mention)
        if category not in HIGH_RANK_ONLY:
            sr = discord.utils.get(guild.roles, name=config.ROLE_STAFF)
            if sr:
                pings.append(sr.mention)

        view = TicketControlView()
        await channel.send(content=' '.join(pings) if pings else None, embed=embed, view=view)

        # Log
        if config.LOG_CHANNEL_ID:
            log_ch = guild.get_channel(config.LOG_CHANNEL_ID)
            if log_ch:
                log_embed = discord.Embed(title='📂 New Ticket Opened', color=cat['color'], timestamp=datetime.utcnow())
                log_embed.add_field(name='User', value=f"{member.mention} (`{member}`)", inline=True)
                log_embed.add_field(name='Category', value=cat['label'], inline=True)
                log_embed.add_field(name='Channel', value=channel.mention, inline=True)
                log_embed.add_field(name='Ticket #', value=f'`{ticket_number}`', inline=True)
                log_embed.set_thumbnail(url=member.display_avatar.url)
                await log_ch.send(embed=log_embed)

        await interaction.followup.send(f"✅ Το ticket σου δημιουργήθηκε! {channel.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ─── Ticket Control Buttons ───────────────────────────────────────────────────

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.danger, custom_id='close_ticket')
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        closed = await do_close(interaction.channel, interaction.user, interaction.guild)
        if not closed:
            return await interaction.response.send_message('❌ Ticket not found.', ephemeral=True)

        embed = discord.Embed(
            title='🔒 Ticket Closing...',
            description=f"Closed by {interaction.user.mention}. Διαγράφεται σε **5 δευτερόλεπτα**...",
            color=discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label='✋ Claim', style=discord.ButtonStyle.success, custom_id='claim_ticket')
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            return await interaction.response.send_message('❌ Μόνο staff μπορεί να κάνει claim.', ephemeral=True)

        add_log('CLAIM', f"Ticket #{interaction.channel.name} claimed by {interaction.user}")
        embed = discord.Embed(
            description=f"✋ Το ticket ανελήφθη από {interaction.user.mention}!",
            color=discord.Color.green(), timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

        if config.LOG_CHANNEL_ID:
            log_ch = interaction.guild.get_channel(config.LOG_CHANNEL_ID)
            if log_ch:
                log_embed = discord.Embed(title='✋ Ticket Claimed', color=discord.Color.green(), timestamp=datetime.utcnow())
                log_embed.add_field(name='Channel', value=interaction.channel.mention, inline=True)
                log_embed.add_field(name='Claimed by', value=interaction.user.mention, inline=True)
                await log_ch.send(embed=log_embed)


# ─── Commands ─────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControlView())
    print(f'✅ Logged in as {bot.user} ({bot.user.id})')
    print('─' * 40)


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    icon_url = config.SERVER_ICON or (str(ctx.guild.icon.url) if ctx.guild.icon else None)
    embed = discord.Embed(
        title='🎫  Support Tickets',
        description=(
            '> Χρειάζεσαι βοήθεια; Επίλεξε κατηγορία παρακάτω για να ανοίξεις ticket.\n\n'
            '💬 **Talk to Owner** — Άμεση επικοινωνία με τον owner\n'
            '⚖️ **Ban Appeal** — Έκκληση για το ban σου\n'
            '💎 **Donate** — Υποστήριξε τον server\n'
            '🐛 **Bug Report** — Αναφορά bug\n'
            '🎫 **Support** — Γενική υποστήριξη\n'
            '🚨 **Staff Report** — Αναφορά μέλους staff'
        ),
        color=discord.Color.from_rgb(88, 101, 242),
        timestamp=datetime.utcnow(),
    )
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    if config.BANNER_IMAGE:
        embed.set_image(url=config.BANNER_IMAGE)
    embed.set_footer(text=f"{ctx.guild.name} • Ticket System", icon_url=icon_url)

    await ctx.send(embed=embed, view=TicketPanelView())
    await ctx.message.delete()


@bot.command()
async def close(ctx):
    closed = await do_close(ctx.channel, ctx.author, ctx.guild)
    if not closed:
        return
    embed = discord.Embed(
        title='🔒 Ticket Closing...',
        description=f"Closed by {ctx.author.mention}. Διαγράφεται σε **5 δευτερόλεπτα**...",
        color=discord.Color.red(), timestamp=datetime.utcnow()
    )
    await ctx.send(embed=embed)
    await asyncio.sleep(5)
    await ctx.channel.delete()


@bot.command()
async def adduser(ctx, member: discord.Member = None):
    if str(ctx.channel.id) not in load_json('tickets.json', {}):
        return
    if not is_staff(ctx.author):
        return await ctx.reply('❌ Μόνο staff μπορεί να προσθέσει χρήστη.')
    if not member:
        return await ctx.reply('❌ Κάνε mention έναν χρήστη.')
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
    await ctx.reply(f'✅ Ο χρήστης {member.mention} προστέθηκε στο ticket.')


@bot.command(name='logs')
async def logs_cmd(ctx):
    if not is_staff(ctx.author):
        return await ctx.reply('❌ No permission.')
    logs = load_json('logs.json', [])[-20:][::-1]
    if not logs:
        return await ctx.reply('📭 Δεν υπάρχουν logs ακόμα.')
    lines = [f"`{l['timestamp'][:19]}` **{l['action']}** — {l['details']}" for l in logs]
    embed = discord.Embed(
        title='📋 Ticket Logs (τελευταία 20)',
        description='\n'.join(lines),
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    await ctx.reply(embed=embed)


# ─── Run ──────────────────────────────────────────────────────────────────────

bot.run(config.TOKEN)
