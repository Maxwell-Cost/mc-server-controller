# Configuration file for Minecraft server controller

# Paste this entire file into config.py and edit the values below to match your AMP instance and Discord webhook.

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/00000/abcde1234"

# AMP instance URL and credentials
INSTANCE_NAME = "friendly_name_of_your_instance"
HIDDEN_INSTANCE_NAME = "friendly_name_of_your_instance01"

AMP_URL = "http://127.0.0.1:8080"
AMP_USER = "your_amp_username"
AMP_PASS = "your_amp_password"

# Backup configuration
AMP_BACKUP_DIR = f"/home/amp/.ampdata/instances/{HIDDEN_INSTANCE_NAME}/Backups"
BACKUP_DESTINATION_DIR = "/mnt/backups/minecraft_archives"

# Polling configuration
# Lower
ATTEMPTS = 60  # Default: 60 attempts (5 minutes)
SECONDS_BETWEEN_ATTEMPTS = 5  # Default: 5 seconds between attempts

# Color codes for terminal output

STATUS = "\033[91m"
ERROR = "\033[93m"
RESET = "\033[0m"