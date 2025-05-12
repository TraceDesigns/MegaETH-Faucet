# HEXQUANT TOOLKIT - ETH Faucet Claimer & Balance Checker
#
# Developed by: HEXQUANT
#
# --- PREREQUISITES ---
# 1. Python 3.7+ installed.
# 2. Install required Python libraries by running:
#    pip install requests web3 twocaptcha-python colorama pytz tzlocal python-dotenv
#
# --- CONFIGURATION ---
# 1. Create a file named '.env' in the same directory as this script.
# 2. Inside the '.env' file, add your 2Captcha API key in the following format:
#    TWO_CAPTCHA_API_KEY="YOUR_ACTUAL_2CAPTCHA_API_KEY_HERE"
#    Replace "YOUR_ACTUAL_2CAPTCHA_API_KEY_HERE" with your real API key.
#
# 3. Create/Populate 'wallets.txt':
#    This file should contain your Ethereum wallet addresses, one address per line.
#    Example:
#    0x1234567890abcdef1234567890abcdef12345678
#    0xabcdef1234567890abcdef1234567890abcdef12
#
# 4. Create/Populate 'proxies.txt' (Optional but Recommended for Faucet):
#    This file should contain your proxies, one proxy per line.
#    Format: http://username:password@host:port  OR  http://host:port
#    Example:
#    http://user1:pass1@proxy.example.com:8080
#    http://192.168.1.100:3128
#    If this file is empty or not found, the script will attempt to run without proxies.
#
# --- HOW TO RUN ---
# 1. Ensure all prerequisites and configurations are met.
# 2. Open a terminal or command prompt.
# 3. Navigate to the directory where this script and the .env, wallets.txt, proxies.txt files are located.
# 4. Run the script using:
#    python your_script_name.py  (e.g., python main.py)
#
# --- SCRIPT OUTPUT ---
# - Faucet Success: Wallet addresses and transaction hashes will be saved to 'faucet_success.txt'.
# - Faucet Fail: Wallet addresses that failed to claim will be saved to 'faucet_fail.txt'.
# - Has Balance: Wallet addresses with a balance > 0 (and their balances) will be saved to 'has_balance.txt'.
# - No Balance: Wallet addresses with a balance of 0 or those that encountered errors during balance check
#               will be saved to 'no_balance.txt'.
#
# --- IMPORTANT NOTES ---
# - The script will create 'wallets.txt' and 'proxies.txt' with example comments if they don't exist on the first run.
#   You will need to populate them and restart the script.
# - Using a high number of threads with public RPCs or without good proxies might lead to rate limiting or IP bans.
# - The 2Captcha API key is crucial for the faucet functionality. Ensure it's correct and your 2Captcha account has balance.


import os
import sys
import threading
import time
import requests
from web3 import Web3, HTTPProvider
from twocaptcha import TwoCaptcha
from colorama import init as colorama_init, Fore, Style
from datetime import datetime
from tzlocal import get_localzone
import concurrent.futures
from dotenv import load_dotenv
load_dotenv()
colorama_init(autoreset=True)
DEFAULT_THREADS = 50
RPC_URL = "https://carrot.megaeth.com/rpc"
WALLET_FILE_NAME = "wallets.txt"
PROXY_FILE_NAME = "proxies.txt"
MAX_RETRIES_BALANCE = 5
MAX_RETRIES_FAUCET = 3
TWO_CAPTCHA_API_KEY = os.getenv("TWO_CAPTCHA_API_KEY")
if not TWO_CAPTCHA_API_KEY:
    print(Fore.RED + "Error: TWO_CAPTCHA_API_KEY not found in .env file or environment variables." + Style.RESET_ALL)
    print(Fore.YELLOW + "Please create a .env file with TWO_CAPTCHA_API_KEY='your_key' or set it as an environment variable." + Style.RESET_ALL)
    sys.exit(1)
TURNSTILE_SITEKEY = "0x4AAAAAABA4JXCaw9E2Py-9"
TURNSTILE_PAGE_URL = "https://testnet.megaeth.com/"
MEGAETH_API_URL = "https://carrot.megaeth.com/claim"
FAUCET_SUCCESS_FILE = "faucet_success.txt"
FAUCET_FAIL_FILE = "faucet_fail.txt"
BALANCE_HAS_FILE = "has_balance.txt"
BALANCE_NO_FILE = "no_balance.txt"
loaded_proxies = []
proxy_idx_faucet = 0
proxy_idx_balance = 0
proxy_lock_faucet = threading.Lock()
proxy_lock_balance = threading.Lock()
stop_event_faucet = threading.Event()
def print_header():
    print(Style.BRIGHT + Fore.MAGENTA + "=" * 60)
    print(Style.BRIGHT + Fore.CYAN + " " * 24 + "HEXQUANT" + " " * 28)
    print(Style.BRIGHT + Fore.MAGENTA + "=" * 60 + Style.RESET_ALL)
    print()
def get_local_time_str():
    local_tz = get_localzone()
    return datetime.now(local_tz).strftime("%H:%M:%S %d/%m/%Y")
def log_message(level, message, task_id=None):
    timestamp = get_local_time_str()
    prefix = f"[{timestamp}]"
    if task_id is not None:
        prefix += f" [Task {task_id}]"
    color = Fore.WHITE
    if level == "INFO":
        color = Fore.CYAN
    elif level == "SUCCESS":
        color = Fore.GREEN
    elif level == "WARNING":
        color = Fore.YELLOW
    elif level == "ERROR":
        color = Fore.RED
    print(f"{color}{prefix} {message}{Style.RESET_ALL}")
def initialize_required_files():
    files_to_check = [WALLET_FILE_NAME, PROXY_FILE_NAME]
    created_any = False
    for file_name in files_to_check:
        if not os.path.exists(file_name):
            try:
                with open(file_name, "w") as f:
                    if file_name == WALLET_FILE_NAME:
                        f.write("# Add wallet addresses here, one per line\n")
                    elif file_name == PROXY_FILE_NAME:
                        f.write("# Add proxies here (e.g., http://user:pass@host:port), one per line\n")
                log_message("INFO", f"Created missing file: {file_name}")
                created_any = True
            except IOError as e:
                log_message("ERROR", f"Could not create file {file_name}: {e}")
                sys.exit(1)
    if created_any:
        log_message("WARNING", "Necessary files were created. Please populate them and restart the script.")
        sys.exit(0)
def load_file_lines(file_path, file_description):
    try:
        with open(file_path, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        if not lines:
            log_message("ERROR", f"{file_description} file '{file_path}' is empty or contains no valid entries.")
            return None
        return lines
    except FileNotFoundError:
        log_message("ERROR", f"{file_description} file '{file_path}' not found.")
        return None
def get_next_proxy_for_faucet():
    global proxy_idx_faucet, loaded_proxies
    if not loaded_proxies:
        return None
    with proxy_lock_faucet:
        proxy = loaded_proxies[proxy_idx_faucet % len(loaded_proxies)]
        proxy_idx_faucet += 1
    return proxy
def get_next_proxy_for_balance():
    global proxy_idx_balance, loaded_proxies
    if not loaded_proxies:
        return None
    with proxy_lock_balance:
        proxy = loaded_proxies[proxy_idx_balance % len(loaded_proxies)]
        proxy_idx_balance += 1
    return proxy
def solve_captcha_via_2captcha(task_id=None):
    try:
        solver = TwoCaptcha(TWO_CAPTCHA_API_KEY)
        log_message("INFO", "Attempting to solve Turnstile CAPTCHA...", task_id)
        result = solver.turnstile(sitekey=TURNSTILE_SITEKEY, url=TURNSTILE_PAGE_URL)
        token = result.get("code")
        if token:
            log_message("SUCCESS", "Turnstile CAPTCHA solved successfully.", task_id)
            return token
        else:
            log_message("ERROR", f"Turnstile CAPTCHA solution invalid response: {result}", task_id)
            return None
    except Exception as e:
        log_message("ERROR", f"Error solving Turnstile CAPTCHA: {e}", task_id)
        return None
def claim_from_megaeth_faucet(wallet_address, captcha_token, proxy_url, task_id=None):
    headers = {
        "Accept": "*/*",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://testnet.megaeth.com",
        "Referer": "https://testnet.megaeth.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    payload = {"addr": wallet_address, "token": captcha_token}
    proxies_dict = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    try:
        log_message("INFO", f"Sending claim request for {wallet_address} via proxy {proxy_url if proxy_url else 'None'}", task_id)
        response = requests.post(MEGAETH_API_URL, json=payload, headers=headers, proxies=proxies_dict, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message("ERROR", f"Claim API request error for {wallet_address}: {e}", task_id)
        return None
    except ValueError:
        log_message("ERROR", f"Claim API returned non-JSON response for {wallet_address}: {response.text}", task_id)
        return None
def process_faucet_wallet(wallet_address, task_idx):
    log_message("INFO", f"Processing wallet: {wallet_address}", task_idx)
    for attempt in range(MAX_RETRIES_FAUCET):
        if stop_event_faucet.is_set():
            log_message("INFO", "Stop signal received, halting task.", task_idx)
            return False
        log_message("INFO", f"Attempt {attempt + 1}/{MAX_RETRIES_FAUCET} for {wallet_address}", task_idx)
        current_proxy = get_next_proxy_for_faucet()
        if not current_proxy and loaded_proxies:
             log_message("ERROR", "No proxy available, but proxies are loaded. This shouldn't happen.", task_idx)
             time.sleep(2)
             continue
        elif not loaded_proxies:
            log_message("INFO", "No proxies loaded, proceeding without proxy.", task_idx)
        captcha_token = solve_captcha_via_2captcha(task_idx)
        if not captcha_token:
            log_message("WARNING", f"Failed to solve CAPTCHA for {wallet_address}. Retrying if possible.", task_idx)
            time.sleep(5)
            continue
        claim_response = claim_from_megaeth_faucet(wallet_address, captcha_token, current_proxy, task_idx)
        if claim_response:
            log_message("INFO", f"Claim response for {wallet_address}: {claim_response}", task_idx)
            message = claim_response.get("message", "").lower()
            if "less than" in message and "hours have passed since the last claim" in message:
                log_message("WARNING", f"Wallet {wallet_address} already claimed recently. Skipping.", task_idx)
                return True
            success_status = claim_response.get("success", False)
            tx_hash = claim_response.get("txhash", "")
            if success_status and tx_hash:
                log_message("SUCCESS", f"Claim successful for {wallet_address}! TxHash: {tx_hash}", task_idx)
                with open(FAUCET_SUCCESS_FILE, "a") as f:
                    f.write(f"{wallet_address} - {tx_hash}\n")
                return True
            else:
                log_message("ERROR", f"Claim attempt failed for {wallet_address}. Response: {message}", task_idx)
        else:
            log_message("ERROR", f"No response or error from claim API for {wallet_address}.", task_idx)
        log_message("INFO", "Waiting before next retry...", task_idx)
        time.sleep(5)
    log_message("ERROR", f"All {MAX_RETRIES_FAUCET} claim attempts FAILED for {wallet_address}.", task_idx)
    with open(FAUCET_FAIL_FILE, "a") as f:
        f.write(wallet_address + "\n")
    return False
def run_faucet_claimer():
    global loaded_proxies, proxy_idx_faucet, stop_event_faucet
    stop_event_faucet.clear()
    proxy_idx_faucet = 0
    log_message("INFO", "Starting MegaETH Faucet Claimer...")
    wallets = load_file_lines(WALLET_FILE_NAME, "Wallets")
    if not wallets:
        return
    loaded_proxies = load_file_lines(PROXY_FILE_NAME, "Proxies")
    if not loaded_proxies:
        log_message("WARNING", f"No proxies loaded from {PROXY_FILE_NAME}. Will attempt without proxies.")
        loaded_proxies = []
    num_threads = DEFAULT_THREADS
    try:
        custom_threads = input(f"Enter number of threads for faucet (default {DEFAULT_THREADS}): ")
        if custom_threads.strip():
            num_threads = int(custom_threads)
            if num_threads <= 0:
                num_threads = DEFAULT_THREADS
                log_message("WARNING", "Invalid thread count, using default.")
    except ValueError:
        log_message("WARNING", "Invalid input for threads, using default.")
        num_threads = DEFAULT_THREADS
    log_message("INFO", f"Using {num_threads} threads for faucet operation.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_wallet = {
            executor.submit(process_faucet_wallet, wallet, idx + 1): wallet
            for idx, wallet in enumerate(wallets)
        }
        try:
            for future in concurrent.futures.as_completed(future_to_wallet):
                wallet_address = future_to_wallet[future]
                try:
                    future.result()
                except Exception as e:
                    log_message("ERROR", f"Unhandled exception for wallet {wallet_address} in faucet task: {e}", future_to_wallet[future])
        except KeyboardInterrupt:
            log_message("WARNING", "Keyboard interrupt detected! Attempting to stop faucet tasks gracefully...")
            stop_event_faucet.set()
            executor.shutdown(wait=False, cancel_futures=True)
            log_message("INFO", "Faucet tasks cancellation requested.")
    log_message("INFO", "Faucet claiming process finished.")
def fetch_wallet_balance_with_retry(wallet_address, task_id=None):
    last_exception = None
    for attempt in range(MAX_RETRIES_BALANCE):
        current_proxy = get_next_proxy_for_balance()
        proxy_config = {}
        if current_proxy:
            proxy_config = {"http": current_proxy, "https": current_proxy}
        provider = HTTPProvider(
            RPC_URL,
            request_kwargs={"timeout": 10, "proxies": proxy_config if proxy_config else None}
        )
        w3_instance = Web3(provider)
        try:
            log_message("INFO", f"Attempt {attempt+1} to get balance for {wallet_address} via proxy {current_proxy if current_proxy else 'None'}", task_id)
            checksum_address = w3_instance.to_checksum_address(wallet_address)
            balance_in_wei = w3_instance.eth.get_balance(checksum_address)
            balance_in_eth = float(w3_instance.from_wei(balance_in_wei, "ether"))
            return balance_in_eth
        except Exception as e:
            last_exception = e
            log_message("WARNING", f"Error fetching balance for {wallet_address} (attempt {attempt+1}): {e}", task_id)
            time.sleep(1)
    log_message("ERROR", f"Failed to fetch balance for {wallet_address} after {MAX_RETRIES_BALANCE} attempts. Last error: {last_exception}", task_id)
    raise last_exception if last_exception else Exception(f"Unknown error for {wallet_address}")
def check_single_wallet_balance(wallet_info):
    idx, wallet_address = wallet_info
    try:
        balance_eth = fetch_wallet_balance_with_retry(wallet_address, task_id=idx)
        return (idx, wallet_address, balance_eth, None)
    except Exception as e:
        return (idx, wallet_address, None, str(e))
def run_balance_checker():
    global loaded_proxies, proxy_idx_balance
    proxy_idx_balance = 0
    log_message("INFO", "Starting ETH Balance Checker...")
    wallets = load_file_lines(WALLET_FILE_NAME, "Wallets")
    if not wallets:
        return
    loaded_proxies = load_file_lines(PROXY_FILE_NAME, "Proxies")
    if not loaded_proxies:
        log_message("WARNING", f"No proxies loaded from {PROXY_FILE_NAME}. Will attempt without proxies.")
        loaded_proxies = []
    num_threads = DEFAULT_THREADS
    try:
        custom_threads = input(f"Enter number of threads for balance checker (default {DEFAULT_THREADS}): ")
        if custom_threads.strip():
            num_threads = int(custom_threads)
            if num_threads <= 0:
                num_threads = DEFAULT_THREADS
                log_message("WARNING", "Invalid thread count, using default.")
    except ValueError:
        log_message("WARNING", "Invalid input for threads, using default.")
        num_threads = DEFAULT_THREADS
    log_message("INFO", f"Using {num_threads} threads for balance checking.")
    total_eth_balance = 0.0
    wallets_with_balance = []
    wallets_with_no_balance = []
    wallet_tasks = [(idx + 1, wallet) for idx, wallet in enumerate(wallets)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_results = [executor.submit(check_single_wallet_balance, task) for task in wallet_tasks]
        for future in concurrent.futures.as_completed(future_results):
            idx, wallet, balance, error_msg = future.result()
            if error_msg:
                log_message("ERROR", f"Failed for {wallet}: {error_msg}", idx)
                wallets_with_no_balance.append(wallet)
            else:
                log_message("SUCCESS", f"Wallet: {wallet} | Balance: {balance:.8f} ETH", idx)
                total_eth_balance += balance
                if balance > 0:
                    wallets_with_balance.append(f"{wallet} | {balance:.8f} ETH")
                else:
                    wallets_with_no_balance.append(wallet)
    log_message("INFO", f"\n--- Balance Check Summary ---")
    log_message("INFO", f"Total ETH Balance Across Queried Wallets: {total_eth_balance:.8f} ETH")
    with open(BALANCE_HAS_FILE, "w") as f:
        for entry in wallets_with_balance:
            f.write(entry + "\n")
    log_message("INFO", f"Wallets with balance saved to: {BALANCE_HAS_FILE}")
    with open(BALANCE_NO_FILE, "w") as f:
        for wallet in wallets_with_no_balance:
            f.write(wallet + "\n")
    log_message("INFO", f"Wallets with no balance (or errors) saved to: {BALANCE_NO_FILE}")
    log_message("INFO", "Balance checking process finished.")
def display_main_menu():
    print_header()
    log_message("INFO", "Welcome to MegaETH Faucet Claimer & Balance Checker")
    print(Style.BRIGHT + Fore.YELLOW + "\nAvailable Operations:")
    print(Fore.GREEN + "  1. Claim from MegaETH Faucet")
    print(Fore.GREEN + "  2. Check ETH Balances")
    print(Fore.RED   + "  0. Exit")
    print(Style.RESET_ALL)
def main_application_loop():
    initialize_required_files()
    while True:
        display_main_menu()
        choice = input(Fore.WHITE + Style.BRIGHT + "Enter your choice (0-2): " + Style.RESET_ALL)
        if choice == '1':
            run_faucet_claimer()
        elif choice == '2':
            run_balance_checker()
        elif choice == '0':
            log_message("INFO", "Exiting HEXQUANT Toolkit. Goodbye!")
            break
        else:
            log_message("ERROR", "Invalid choice. Please try again.")
        input(Fore.CYAN + "\nPress Enter to return to the main menu..." + Style.RESET_ALL)
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
if __name__ == "__main__":
    try:
        main_application_loop()
    except KeyboardInterrupt:
        log_message("WARNING", "Application terminated by user (Ctrl+C).")
        stop_event_faucet.set()
    except Exception as e:
        log_message("CRITICAL", f"An unexpected critical error occurred: {e}")
    finally:
        log_message("INFO", "Shutting down.")
        sys.exit(0)
