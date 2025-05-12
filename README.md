# MegaETH-Faucet 🛠️✨

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue.svg" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  <a href="https://github.com/HexQuant-Hub/MegaETH-Faucet/issues"><img src="https://img.shields.io/github/issues/HexQuant-Hub/MegaETH-Faucet.svg" alt="GitHub issues"></a>
  <a href="https://github.com/HexQuant-Hub/MegaETH-Faucet/stargazers"><img src="https://img.shields.io/github/stars/HexQuant-Hub/MegaETH-Faucet.svg" alt="GitHub stars"></a>
</p>

Welcome to the **MegaETH-Faucet**! This powerful Python script allows you to:
1. Claim ETH from the [MegaETH Testnet Faucet](https://testnet.megaeth.com/) 💧
2. Check ETH balances for a list of wallet addresses 💰

Developed by **[HexQuant-Hub](https://github.com/HexQuant-Hub)**.

---

## 🌟 Features

* **Automated Faucet Claiming**: Automatically solve CAPTCHAs (via 2Captcha) and claim testnet ETH.
* **Batch Balance Checking**: Efficiently check the ETH balance of multiple wallets.
* **Proxy Support**: Use proxies for faucet claiming and balance checking to avoid rate limits.
* **Multi-threading**: Perform operations concurrently for faster processing.
* **User-Friendly Menu**: Easy-to-navigate command-line interface.
* **Detailed Logging**: Keep track of successful claims, failures, and balances.
* **`.env` Configuration**: Securely manage your API keys.

---

## 🚀 Getting Started

Follow these steps to get the toolkit up and running on your system.

### 1. Prerequisites

* Python 3.7 or higher installed.
* Git (for cloning the repository).

### 2. Clone the Repository

Open your terminal or command prompt and clone the repository:
```bash
git clone https://github.com/HexQuant-Hub/MegaETH-Faucet.git
cd MegaETH-Faucet
```

### 3. Set Up a Python Virtual Environment (Recommended)

It's best practice to use a virtual environment to manage project dependencies.

Create a virtual environment:

```bash
python -m venv venv
```

(On some systems, you might need to use python3 instead of python)

Activate the virtual environment:

On Windows:
```bash
.\venv\Scripts\activate
```

On macOS and Linux:
```bash
source venv/bin/activate
```

You should see (venv) at the beginning of your terminal prompt.

### 4. Install Dependencies

With the virtual environment activated, install the required Python libraries. First, ensure you have a requirements.txt file in the MegaETH-Faucet directory with the following content:

```txt
requests
web3
twocaptcha-python
colorama
pytz
tzlocal
python-dotenv
```

Then, run:
```bash
pip install -r requirements.txt
```

### 5. Configuration ⚙️

You'll need to configure a few things before running the script:

**2Captcha API Key**:

Create a file named `.env` in the MegaETH-Faucet directory.

Open the `.env` file and add your 2Captcha API key:
```
TWO_CAPTCHA_API_KEY="YOUR_ACTUAL_2CAPTCHA_API_KEY_HERE"
```

Replace "YOUR_ACTUAL_2CAPTCHA_API_KEY_HERE" with your real key.

If you don't have a 2Captcha account, you can sign up and purchase credits here: 👉 [2Captcha Sign Up](https://2captcha.com/)

**Wallet Addresses (wallets.txt)**:

The script will create `wallets.txt` if it doesn't exist.

Open `wallets.txt` and add your Ethereum wallet addresses, one address per line.
Example:
```
0x1234567890abcdef1234567890abcdef12345678
0xabcdef1234567890abcdef1234567890abcdef12
```

**Proxies (proxies.txt)** (Optional but Highly Recommended for Faucet):

The script will create `proxies.txt` if it doesn't exist.

Open `proxies.txt` and add your proxies, one proxy per line.
Format: `http://username:password@host:port` or `http://host:port`
Example:
```
http://user1:pass1@proxy.example.com:8080
http://192.168.1.100:3128
```

If you need reliable proxies, consider checking out: 👉 [NSTProxy](https://nstproxy.com/)

If this file is empty or not found, the script will attempt operations without proxies (not recommended for faucet).

### 6. Run the Toolkit 🏃‍♂️

Once everything is set up, run the script from your terminal (ensure your virtual environment is still active):

```bash
python main.py
```

(Assuming your main script file is named main.py. If it's different, adjust the command accordingly.)

You'll be greeted with the MegaETH-Faucet menu. Choose an option to begin!

## 📊 Script Output

The script generates the following files to log results:

* **faucet_success.txt**: Lists wallet addresses and transaction hashes for successful faucet claims.
* **faucet_fail.txt**: Lists wallet addresses that failed to claim from the faucet.
* **has_balance.txt**: Lists wallet addresses with a balance > 0, along with their respective balances.
* **no_balance.txt**: Lists wallet addresses with a balance of 0 or those that encountered errors during the balance check.

## 📝 Important Notes

* The script will automatically create `wallets.txt` and `proxies.txt` with example comments if they don't exist on the first run. You'll need to populate them with your actual data and then restart the script.
* Using a high number of threads, especially with public RPCs or without good quality proxies, might lead to rate limiting or temporary IP bans from the services.
* Ensure your 2Captcha API key is correct and your 2Captcha account has sufficient balance for CAPTCHA solving, as this is crucial for the faucet claiming functionality.

To deactivate the virtual environment when you're done:
```bash
deactivate
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page for this repository.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details (you might need to create this file if it doesn't exist).

Happy Claiming and Checking with MegaETH-Faucet! 🎉
