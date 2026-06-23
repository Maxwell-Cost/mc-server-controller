import sys
import requests
import time
import asyncio
 
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
    """Controls the Minecraft server by starting or stopping it via the AMP API. Initializes Instance within the API"""

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
        print(f"Error: Could not find an instance matching friendly name '{INSTANCE_NAME}'!")
        print("Discovered instances on this node:")
        for inst in controller.instances:
            print(f" - Friendly Name: {inst.friendly_name}")
        return

    print(f"{RED}Initialization complete.{RESET}")

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

        send_to_discord("⚠️ **The Server is shutting down now.** Saving world data...")
        
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


if __name__ == "__main__":
    # Check if the user provided an argument (start or stop)
    if len(sys.argv) < 2 or sys.argv[1] not in ["start", "stop", "backup"]:
        print("Usage: python3 server_controller.py [start|stop|backup]")
        sys.exit(1)
    else:
        asyncio.run(control_server(sys.argv[1]))

