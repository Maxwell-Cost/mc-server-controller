# Configuration file for Minecraft server controller

# Paste this entire file into config.py and edit the values below to match your AMP instance and Discord webhook.

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/00000/abcde1234"
INSTANCE_NAME = "friendly_name_of_your_instance"
HIDDEN_INSTANCE_NAME = "friendly_name_of_your_instance01"

AMP_URL = "http://127.0.0.1:8080"
AMP_USER = "your_amp_username"
AMP_PASS = "your_amp_password"

AMP_BACKUP_DIR = f"/home/amp/.ampdata/instances/{HIDDEN_INSTANCE_NAME}/Backups"
BACKUP_DESTINATION_DIR = "/mnt/backups/minecraft_archives"

RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"