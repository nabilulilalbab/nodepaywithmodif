import os
import time
import requests
from termcolor import colored
import pyfiglet
import inquirer
from threading import Thread
from datetime import datetime
import itertools
from loguru import logger
import httpx






BOT_TOKEN = "7761568719:AAHZceTGz-Y8Fskdg5ZZpBeYNN-SYgySZ14"  # Ganti dengan token bot Anda
CHAT_ID = "7053916798"      # Ganti dengan chat ID Anda
NOTIFICATION_INTERVAL = 1800   # Interval notifikasi (30 menit)


async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID, 
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            logger.info("Pesan berhasil dikirim ke Telegram.")
    except Exception as e:
        logger.error(f"Gagal mengirim pesan ke Telegram: {e}")





def read_lines(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

class Config:
    def __init__(self):
        self.base_url = 'https://nodepay.org'
        self.ping_url = 'http://nw.nodepay.ai/api/network/ping'
        self.retry_interval = 30
        self.session_url = 'http://api.nodepay.ai/api/auth/session'

class Logger:
    @staticmethod
    def info(message, data=None):
        print(colored(f"[INFO] {message}: {data}", 'green'))

    @staticmethod
    def error(message, data=None):
        print(colored(f"[ERROR] {message}: {data}", 'red'))

class Bot:
    def __init__(self, config, logger, proxies=None):
        self.config = config
        self.logger = logger
        self.proxies = proxies or []
        self.proxy_cycle = itertools.cycle(self.proxies)

    def connect(self, token):
        try:
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.37'
            account_info = self.get_session(token, user_agent)
            print(colored(f"Connected to session successfully for token {token[:10]}...", 'cyan'))
            self.logger.info('Session info', {'status': 'success', 'token': token[:10] + '...'})

            while True:
                try:
                    proxy = next(self.proxy_cycle)
                    self.send_ping(account_info, token, user_agent, proxy)
                except Exception as error:
                    print(colored(f"Ping error for token {token[:10]}...: {error}", 'yellow'))
                    self.logger.error('Ping error', {'error': str(error), 'token': token[:10] + '...'})

                time.sleep(self.config.retry_interval)
        except Exception as error:
            print(colored(f"Connection error for token {token[:10]}...: {error}", 'red'))
            self.logger.error('Connection error', {'error': str(error), 'token': token[:10] + '...'})



    async def send_telegram_notification(self, account_info, ping_result):
        try:
            uuid = account_info.get('uid', 'Tidak diketahui')
            balance = account_info.get('balance', {})
            current_amount = balance.get('current_amount', 'Tidak diketahui')
            total = balance.get('total_collected', 'Tidak diketahui')
            
            message = (
                f"📊 <b>NodePay Bot Status</b>\n\n"
                f"🪪 <b>Akun ID:</b> {uuid}\n"
                f"💵 <b>Penghasilan Saat Ini:</b> {current_amount}\n"
                f"💰 <b>Total Saldo:</b> {total}\n"
                f"⏱️ <b>Ping Terakhir:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await send_telegram_message(message)
        except Exception as e:
            logger.error(f"Gagal mengirim notifikasi: {e}")


    def get_session(self, token, user_agent):
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }

        if self.proxies:
            response = requests.post(self.config.session_url, headers=headers, proxies=self.proxies[0])
        else:
            response = requests.post(self.config.session_url, headers=headers)

        return response.json()['data']

    def send_ping(self, account_info, token, user_agent, proxy):
        ping_data = {
            'id': account_info.get('uid', 'Unknown'),
            'browser_id': account_info.get('browser_id', 'random_browser_id'),
            'timestamp': int(time.time()),
            'version': '2.2.7'
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }

        try:
            start_time = time.time()

            response = requests.post(self.config.ping_url, json=ping_data, headers=headers, proxies=proxy)

            end_time = time.time()

            ping_duration = end_time - start_time

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(colored(f"[{timestamp}] Ping sent successfully for token {token[:10]}... using proxy {proxy['http'][:30]}... | Duration: {ping_duration:.2f} seconds", 'magenta'))
            self.logger.info('Ping sent', {'status': 'success', 'token': token[:10] + '...', 'proxy': proxy['http'][:30], 'duration': f'{ping_duration:.2f} seconds'})

            # global last_notification_time
            # current_time = time.time()
            # if current_time - last_notification_time >= NOTIFICATION_INTERVAL:
            #     uuid = account_info.get('uid', 'Tidak diketahui')
            #     balance = account_info.get('balance', {})
            #     current_amount = balance.get('current_amount', 'Tidak diketahui')
            #     total = balance.get('total_collected', 'Tidak diketahui')
            #     message = (
            #         f"📊Status koneksi: {status_connect}\n"
            #         f"🪪Akun: {uuid}\n\n"
            #         f"💵Penghasilan: {current_amount}\n"
            #         f"💰Total Saldo: {total}"
            #     )
            #     await send_telegram_message(message)
            #     last_notification_time = current_time
            #

        except Exception as error:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(colored(f"[{timestamp}] Ping error for token {token[:10]}... using proxy {proxy['http'][:30]}: {error}", 'yellow'))
            self.logger.error('Ping error', {'error': str(error), 'token': token[:10] + '...', 'proxy': proxy['http'][:30]})

def display_welcome():
    ascii_art = pyfiglet.figlet_format("Nodepay Bot")
    print(colored(ascii_art, 'yellow'))
    print(colored("========================================", 'cyan'))
    print(colored("=        Welcome to MiweAirdrop        =", 'cyan'))
    print(colored("=       Automated & Powerful Bot       =", 'cyan'))
    print(colored("========================================", 'cyan'))

def ask_proxy_mode():
    questions = [
        inquirer.List('proxy_mode',
                      message="Do you want to use a proxy?",
                      choices=['No Proxy', 'Use Proxy'],
                      default='No Proxy',
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['proxy_mode']

def configure_proxy():
    proxies = read_lines('proxy.txt')
    if not proxies:
        print(colored("No proxies found in proxy.txt", 'red'))
        return None

    proxies = proxies[:100]

    proxy_list = []
    for proxy in proxies:
        proxy_parts = proxy.split(':')
        if len(proxy_parts) == 4:
            host, port, username, password = proxy_parts
            proxy_dict = {
                'http': f'http://{username}:{password}@{host}:{port}',
                'https': f'http://{username}:{password}@{host}:{port}'
            }
            proxy_list.append(proxy_dict)
    
    return proxy_list

def main():
    display_welcome()

    tokens = read_lines('token.txt')
    config = Config()
    logger = Logger()

    proxy_mode = ask_proxy_mode()

    proxies = None
    if proxy_mode == 'Use Proxy':
        proxies = configure_proxy()
        if proxies:
            print(colored(f"Using {len(proxies)} proxies", 'green'))
        else:
            print(colored("No valid proxy configured, using direct connection.", 'yellow'))

    bot = Bot(config, logger, proxies)

    threads = []
    for token in tokens:
        thread = Thread(target=bot.connect, args=(token,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
