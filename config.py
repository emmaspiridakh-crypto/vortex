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
_log = os.environ.get('LOG_CHANNEL_ID', '1492438845352841226')
LOG_CHANNEL_ID = int(_log) if _log.isdigit() else None  # π.χ. 1234567890

_cat = os.environ.get('TICKET_CATEGORY_ID', '1492438858250322001')  # ← ID category (προαιρετικό)
TICKET_CATEGORY_ID = int(_cat) if _cat.isdigit() else None

SERVER_ICON = os.environ.get('SERVER_ICON', 'https://i.imgur.com/M2FCuDq.png')  # ← URL εικόνας
BANNER_IMAGE = os.environ.get('BANNER_IMAGE', 'https://i.imgur.com/ujVGie1.jpeg')  # ← URL banner

ROLE_FOUNDER    = 1492438843385843895  # ← ID του Founder
ROLE_CO_FOUNDER = 1492438843385843892  # ← ID του Co-Founder
ROLE_OWNER      = 1492438843385843894  # ← ID του Owner
ROLE_CO_OWNER   = 1492438843385843893  # ← ID του Co-Owner
ROLE_STAFF      = 1492438843352154165  # ← ID του Staff
