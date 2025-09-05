import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from bot import Bot 
from database import init_database

# This is a special instance of the bot for the lifespan manager
# We create it here to control its startup sequence precisely.
bot_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This new lifespan function has extremely verbose logging to find the point of failure.
    """
    global bot_instance
    
    print("\n--- STARTING DIAGNOSTIC SEQUENCE ---\n", flush=True)

    try:
        # STEP 1: Initialize the database. This also tests the DATABASE_URI.
        print("[DIAGNOSTIC STEP 1/4] Initializing database connection...", flush=True)
        await init_database()
        print("[DIAGNOSTIC STEP 1/4] SUCCESS: Database connection appears stable.\n", flush=True)

        # STEP 2: Initialize the main Bot class.
        print("[DIAGNOSTIC STEP 2/4] Initializing Pyrogram Bot class...", flush=True)
        bot_instance = Bot()
        if bot_instance:
             print("[DIAGNOSTIC STEP 2/4] SUCCESS: Bot class initialized.\n", flush=True)
        else:
             print("[DIAGNOSTIC STEP 2/4] FAILURE: Bot class initialization failed.", flush=True)
             sys.exit(1)

        # STEP 3: Start the Pyrogram client connection.
        print("[DIAGNOSTIC STEP 3/4] Starting Pyrogram client (bot_instance.start())...", flush=True)
        await bot_instance.start()
        print("[DIAGNOSTIC STEP 3/4] SUCCESS: Pyrogram client started. Bot should be online.\n", flush=True)

        # STEP 4: Yield to the web server. If it gets here, the bot is running.
        print("[DIAGNOSTIC STEP 4/4] Handing over to Uvicorn web server...", flush=True)
        print("\n--- DIAGNOSTIC SEQUENCE COMPLETE: BOT IS RUNNING ---\n", flush=True)
        
        yield # The web server runs here
    
    except Exception as e:
        print("\n!!!!!!!!!!!!!!! A FATAL ERROR OCCURRED DURING STARTUP !!!!!!!!!!!!!!!\n", flush=True)
        print(f"The failure occurred at one of the steps above.", flush=True)
        print(f"Error Type: {type(e).__name__}", flush=True)
        print(f"Error Details: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", flush=True)
        # We exit forcefully to make sure Render logs the failure.
        sys.exit(1)
    finally:
        # On Shutdown
        if bot_instance and bot_instance.is_connected:
            print("Shutting down Pyrogram client...", flush=True)
            await bot_instance.stop()
            print("Pyrogram client stopped.", flush=True)

# Initialize the FastAPI web app with our new diagnostic lifespan manager
web_app = FastAPI(lifespan=lifespan)

@web_app.get("/")
def read_root():
    return {"status": "Bot is running"}
