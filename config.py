"""Velvet Reaper — shared constants. Every cog reads ranks/level math/shop here
so the leveling, rewards, economy, and card code never drift apart.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.environ.get("DISCORD_TOKEN", "")
PREFIX = os.environ.get("PREFIX", ".")
OWNER_IDS = {int(x) for x in os.environ.get("OWNER_IDS", "").replace(" ", "").split(",") if x}

# ---- identity / palette ---------------------------------------------------
BLOOD = 0x8B0000        # primary accent (blood red)
VELVET = 0x4A0E2E       # deep velvet
BONE = 0xE8E0D5         # off-white text
ASH = 0x6E6A66          # muted
GREEN = 0x2EA043
RED = 0xCF222E
SOUL = "💀"             # currency glyph

# ---- economy defaults -----------------------------------------------------
DAILY_MIN, DAILY_MAX = 60, 160          # souls from ^daily
LEVELUP_SOULS = lambda lvl: 25 + lvl * 5  # souls granted each level-up
DAILY_COOLDOWN = 22 * 3600              # seconds (slightly under a day)

# ---- xp / leveling defaults (per-guild overridable via ^set) --------------
DEFAULT_XP_AMOUNT = 20                  # xp per eligible message
DEFAULT_XP_COOLDOWN = 60               # seconds between xp-earning messages
DEFAULT_VC_XP_PER_MIN = 5             # xp per active voice minute
MIN_MESSAGE_LEN = 4


def xp_for_level(level: int) -> int:
    """Total xp needed to *reach* a level. Inverse of level_from_xp."""
    return 100 * level * level


def level_from_xp(xp: int) -> int:
    return int((max(xp, 0) / 100) ** 0.5)


def progress(xp: int):
    """Return (level, xp_into_level, xp_needed_for_next)."""
    lvl = level_from_xp(xp)
    base = xp_for_level(lvl)
    nxt = xp_for_level(lvl + 1)
    return lvl, xp - base, nxt - base


# ---- reaper rank ladder (level band -> title) -----------------------------
RANKS = [
    (0,   "Mortal"),
    (5,   "Wraith"),
    (10,  "Specter"),
    (20,  "Revenant"),
    (35,  "Reaper"),
    (50,  "Death's Hand"),
    (75,  "The Velvet Reaper"),
]


def rank_title(level: int) -> str:
    title = RANKS[0][1]
    for need, name in RANKS:
        if level >= need:
            title = name
        else:
            break
    return title


# ---- shop catalog ---------------------------------------------------------
# All items are self-fulfilling (no per-guild role setup needed). Level-based
# Discord role rewards are configured separately via the rewards cog.
SHOP = {
    "boost": {
        "name": "XP Boost",
        "price": 250,
        "desc": "2× XP for 1 hour.",
        "emoji": "⚡",
    },
    "color": {
        "name": "Custom Card Color",
        "price": 500,
        "desc": "Unlock a custom rank-card accent. Set it with `^setcolor #hex`.",
        "emoji": "🎨",
    },
    "mark": {
        "name": "Reaper's Mark",
        "price": 750,
        "desc": "A cosmetic mark shown on your rank card.",
        "emoji": "🩸",
    },
}

BOOST_MULTIPLIER = 2
BOOST_DURATION = 3600  # seconds
