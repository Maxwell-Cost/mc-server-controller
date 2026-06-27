from datetime import datetime
import os
import sys
import requests
import time
import asyncio
import shutil
 
from ampapi import (
    APIParams,
    Bridge,
    Core,
    AMPMinecraftInstance,
    AMPInstance,
    AMPControllerInstance
)

from config import *

def send_to_discord(message):
    """Sends a simple text notification to your Discord channel."""
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        print(f"Discord error: {e}")

async def control_server(action):
    """Controls the Minecraft server by starting, stopping, or backing up the instance. Initializes Instance within the API"""

    print(f"Logging into AMP API and initalizing instance...")

    # Initialize the authenticated connection layer
    _params = APIParams(url=AMP_URL, user=AMP_USER, password=AMP_PASS)
    _bridge = Bridge(api_params=_params)
    del _params

    # Initialize master object and get instances for loop
    controller = AMPControllerInstance()

    await controller.get_instances(format_data=True)

    # Loop through instances to find ours
    server_instance = None
    for inst in controller.instances:
        if inst.friendly_name == INSTANCE_NAME:
            server_instance = inst
            break

    # If the instance name wasn't found, raise an error to prevent a crash later
    if not server_instance:
        print(f"     [{YELLOW}Warning{RESET}] Could not find an instance matching friendly name '{INSTANCE_NAME}'!")
        print("Discovered instances on this node:")
        for inst in controller.instances:
            print(f" - Friendly Name: {inst.friendly_name}")
        return

    print(f"{RED}Initialization complete.{RESET}")

    # =========================================================================
    # START ACTION (Boot Sequence)
    # =========================================================================

    if action == "start":
        print(f"Waking up {INSTANCE_NAME} instance...")

        try:
            await server_instance.start_instance()
        except TypeError:
            server_instance.start_instance()

        
        print("Waiting 10 seconds for the application environment to initialize...")
        time.sleep(10)


        print(f"Launching Minecraft Java Application...")
        try:
            await server_instance.start_application()
        except TypeError:
            server_instance.start_application()
        
        send_to_discord("⚔️ **The Server is now ONLINE!**")

        print(f"{RED}Server Launch Sequence Complete.{RESET}")

    # =========================================================================
    # STOP ACTION (Graceful Shutdown Sequence with Player Warnings)
    # =========================================================================        

    elif action == "stop":
        print(f"{RED}Starting Graceful Shutdown Sequence...{RESET}")
        
        # Discord warning for players
        send_to_discord("⏳ **Sending a 15-minute warning to players on The Server...**")
        
        # 15 min Warning
        await server_instance.send_console_message('say WARNING: The Server will shut down in 15 minutes! Please prepare to log out safely.')
        print("15 Minute shutdown warning sent to console")
        time.sleep(300)

        # 10 min Warning
        await server_instance.send_console_message('say WARNING: The Server will shut down in 10 minutes! Please prepare to log out safely.')
        print("10 Minute shutdown warning sent to console")
        time.sleep(300)

        # 5 min Warning
        await server_instance.send_console_message('say WARNING: The Server will shut down in 5 minutes! Please prepare to log out safely.')
        print("5 Minute shutdown warning sent to console")
        time.sleep(240)

        # 1 min Warning
        await server_instance.send_console_message('say WARNING: The Server will shut down in 1 minute! Please prepare to log out safely.')
        print("1 Minute shutdown warning sent to console")
        time.sleep(60)
        
        # Stop the server
        print(f"Shutting Down Minecraft Java Application...")

        send_to_discord("⚠️ **The Server is shutting down now.**")
        
        try:
            await server_instance.stop_application()
        except TypeError:
            server_instance.stop_application()

        print("Waiting 20 seconds for the Minecraft Java application environment to shut down...")
        time.sleep(20)
        print(f"Shutting Down Application Enviroment...")
        
        try:
            await server_instance.stop_instance()
        except TypeError:
            server_instance.stop_instance()
        
        
        send_to_discord("😴 **The server is now OFFLINE.**")
        print(f"{RED}Server Shut Down Sequence Complete.{RESET}")

    # =========================================================================
    # BACKUP ACTION (Trigger AMP Backup + Ship Result to External Hard Drive)
    # =========================================================================

    elif action == "backup":
        print("Starting Backup Sequence...")

        # Generate a timestamped backup name and description
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        backup_name = f"AutoBackup_{datetime.now().strftime('%Y%m%d_%H%M')}"
        backup_desc = f"Automated cron backup generated on {current_time}"
        
        script_start_time = time.time()

        send_to_discord("💾 **The Server is starting a backup.**")
        
        # Take a backup using the AMP API
        try:
            await server_instance.take_backup(backup_name, backup_desc)
            print(f"{backup_name} initiated with description: {backup_desc}")
            print(f"{RED}AMP backup command successfully dispatched to the server panel.{RESET}")
        except Exception as e:
            print(f"{YELLOW}AMP native backup failed: {e}{RESET}")
            send_to_discord(f"❌ **AMP Native Backup failed!** Error log: {e}")


        # File monitoring loop
        print(f"Waiting for AMP background thread to compile the backup...")
        time.sleep(5)

        target_filename = None

        for attempt in range(60):  # Wait up to 5 minutes (60 attempts * 5 seconds)
            try:
                backups_list = await server_instance.get_backups(format_data=False)

                # Look through the API list for our backup by name and get the filename
                matched_backup = None
                for backup in backups_list:
                    if backup.get('Name') == backup_name:
                        matched_backup = backup
                        break

                if matched_backup:
                    target_filename = matched_backup.get('FileName')
                    print(f"{RED}API confirmed backup is ready with filesignature: {target_filename}{RESET}")
                    break
                print(f"    [{YELLOW}API Check {attempt + 1}/60{RESET}] Backup still processing... retrying in 5 seconds.")
                time.sleep(5)  # Wait before checking again
            
            except Exception as poll_error:
                    print(f"     [{YELLOW}Poll Warning{RESET}] Failed to reach API on this attempt: {poll_error}")

        # Handle case where the backup was not found after polling
        if not target_filename:
            print(f"{YELLOW}Warning: Backup tracking timed out via the API.{RESET}")
            send_to_discord("❌ **Backup Sync Failed:** Python timed out waiting for the AMP API state change.")
            return
        
        # Move the backup to the external hard drive
        source_file_path = os.path.join(AMP_BACKUP_DIR, target_filename)
        destination_path = os.path.join(BACKUP_DESTINATION_DIR, target_filename)

        print(f"Moving backup from {source_file_path} to {destination_path}...")
        os.makedirs(BACKUP_DESTINATION_DIR, exist_ok=True)

        try:
            shutil.move(source_file_path, destination_path)
            print(f"{RED}Backup successfully moved to external storage.{RESET}")
            send_to_discord(f"💾 **Backup Complete:** {backup_name} has been moved to external storage.")
        except Exception as move_error:
            print(f"     [{YELLOW}Warning{RESET}] Could not move backup to external storage: {move_error}")
            send_to_discord(f"❌ **Backup Move Failed:** Could not move {backup_name} to external storage.")


        
if __name__ == "__main__":
    # Check if the user provided an argument (start or stop)
    if len(sys.argv) < 2 or sys.argv[1] not in ["start", "stop", "backup"]:
        print("Usage: python3 server_controller.py [start|stop|backup]")
        sys.exit(1)
    else:
        asyncio.run(control_server(sys.argv[1]))

