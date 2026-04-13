import os

# ╔══════════════════════════════════════════════════════════╗
# ║         🎫  TICKET BOT  —  CONFIG                       ║
# ╚══════════════════════════════════════════════════════════╝
# Στο Render βάλε τα παρακάτω ως Environment Variables
# Τοπικά μπορείς να τα βάλεις απευθείας εδώ

# ── Bot Token ──────────────────────────────────────────────
# Render: Environment Variable → TOKEN
TOKEN = os.environ.get('TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ── Channel IDs (αριθμοί, όχι string) ─────────────────────
# Render: Environment Variable → LOG_CHANNEL_ID
_log = os.environ.get('LOG_CHANNEL_ID', '')
LOG_CHANNEL_ID = int(_log) if _log.isdigit() else None  # π.χ. 1234567890

# Render: Environment Variable → TICKET_CATEGORY_ID
_cat = os.environ.get('TICKET_CATEGORY_ID', '')
TICKET_CATEGORY_ID = int(_cat) if _cat.isdigit() else None  # π.χ. 9876543210 (προαιρετικό)

# ── Server Images ──────────────────────────────────────────
# URL για thumbnail στο panel embed (null = αυτόματα server icon)
SERVER_ICON = os.environ.get('SERVER_ICON', None)  # π.χ. 'https://i.imgur.com/abc.png'

# URL για banner εικόνα στο panel embed (προαιρετικό)
BANNER_IMAGE = os.environ.get('BANNER_IMAGE', None)  # π.χ. 'https://i.imgur.com/banner.png'

# ── Role Names (ΑΚΡΙΒΩΣ όπως στον server) ─────────────────
ROLE_FOUNDER    = os.environ.get('ROLE_FOUNDER',    'Founder')
ROLE_CO_FOUNDER = os.environ.get('ROLE_CO_FOUNDER', 'Co-Founder')
ROLE_OWNER      = os.environ.get('ROLE_OWNER',      'Owner')
ROLE_CO_OWNER   = os.environ.get('ROLE_CO_OWNER',   'Co-Owner')
ROLE_STAFF      = os.environ.get('ROLE_STAFF',      'Staff')
