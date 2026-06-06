# Velvet Reaper

A reaper-themed leveling, economy, and light-moderation bot. `^` prefix, hybrid
(prefix **and** slash). Built for QueenVis; meant to live in `grxomen/velvetreaper`
so Forge posts its commits.

## Two meters
- **XP** drives your **rank** (the reaper ladder): Mortal → Wraith → Specter →
  Revenant → Reaper → Death's Hand → The Velvet Reaper. Earned from chatting and
  active voice time.
- **Souls 💀** is **currency** — earned on every level-up and from `^daily`, spent
  in the shop. Separate from XP.

## Commands

**Leveling** — `^rank [@user]` (Pillow rank card), `^top`

**Souls** — `^balance [@user]`, `^daily`, `^give @user <n>`, `^shop`, `^buy <boost|color|mark>`, `^setcolor #hex`

**Admin · leveling** — `^set <time> <n>` (e.g. `^set 30m 40`), `^setvcxp <n>`, `^levelchannel [#ch]`, `^leveltoggle <on/off>`

**Admin · rewards & mod** — `^levelrole <lvl> @role`, `^dellevelrole <lvl>`, `^levelroles`, `^purge <n>`, `^warn @user [reason]`

Shop perks are self-fulfilling (no role setup needed): **XP Boost** (2× for 1h),
**Custom Card Color** (then `^setcolor`), **Reaper's Mark** (cosmetic on the card).
Actual Discord roles are handed out via `^levelrole`.

## Install (QueenVis)

```bash
# unzip + SFTP to /mnt/verbatim_mnt/velvetreaper, then:
cd /mnt/verbatim_mnt/velvetreaper
python3.11 -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env          # DISCORD_TOKEN + OWNER_IDS
cp velvetreaper.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now velvetreaper
journalctl -u velvetreaper -f
```

Enable **Message Content**, **Server Members**, and **Voice State** intents in the
Discord Developer Portal — the bot needs all three (XP reads message content,
role rewards need members, voice XP needs voice states). The service file ships with
`User=root`; change it if you run a dedicated user.

Rank cards use DejaVu fonts (already on QueenVis from your PDF work). If a box
ever lacks them: `sudo apt install fonts-dejavu`.

## Notes
- The SQLite DB lives at `data/velvet.db` (auto-created, gitignored). Per-guild XP
  rates and level-up routing persist there.
- Voice sessions are tracked in memory, so a restart resets any open VC timer —
  deliberate, to avoid constant DB writes.
- Levels come from `level = floor(sqrt(xp / 100))`; level *L* needs `100·L²` total XP.
  Tune feel with `^set`.

