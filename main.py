import asyncio
import aiohttp
import json
import random
import uuid
import pyfiglet
from colorama import init, Fore
import os
import itertools
import threading
import time

init()

async def join_group(session, group_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.yay.space/v1/groups/{group_id}/join"
    try:
        async with session.post(url, headers=headers) as response:
            response_text = await response.text()
            print(f"Join Status Code: {response.status}, Response: {response_text}")
            if response.status != 201:
                print(f"Failed Join Status Code: {response.status}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def fetch_group_members(session, group_id, token):
    url = f"https://api.yay.space/v2/groups/{group_id}/members?number=500"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                members = [{"id": member["user"]["id"], "nickname": member["user"]["nickname"]} for member in data["group_users"]]
                
                os.makedirs('scraped', exist_ok=True)
                file_path = os.path.join('scraped', f"{group_id}.txt")
                with open(file_path, 'w', encoding='utf-8') as f:
                    for member in members:
                        f.write(f"{member['id']}, {member['nickname']}\n")
                
                return members
            else:
                print(f"Failed to fetch group members. Status Code: {response.status}")
                return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

async def send_message(session, group_id, member, base_message, token):
    url = "https://yay.space/api/posts"
    headers = {"Authorization": f"Bearer {token}"}
    text = f"@{member['nickname']} {base_message}" if member else base_message
    message_tags = json.dumps([{"type": "user", "user_id": member['id'], "offset": 0, "length": len(member['nickname']) + 1}]) if member else "[]"
    
    post_data = {
        "post_type": "text",
        "text": text,
        "color": "0",
        "font_size": "0",
        "message_tags": message_tags,
        "group_id": group_id,
        "uuid": str(uuid.uuid4())
    }
    
    try:
        async with session.post(url, headers=headers, json=post_data) as response:
            response_text = await response.text()
            print(f"Message Status Code: {response.status}, Response: {response_text}")
            if response.status != 201:
                print(f"Failed to send message. Status Code: {response.status}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def tokenchecker(session, token):
    url = "https://api.yay.space/v1/payment_gateway/stripe/subscriptions/latest"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(url, headers=headers) as response:
            response_text = await response.text()
            if response.status == 200:
                print(f'Token Valid: {token}')
            else:
                print(f'Invalid Token: {token}, Status Code: {response.status}, Response: {response_text}')
    except Exception as e:
        print(f"An error occurred: {e}")

async def leave_group(session, group_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.yay.space/v1/groups/{group_id}/leave"
    try:
        async with session.post(url, headers=headers) as response:
            response_text = await response.text()
            print(f"Leave Status Code: {response.status}, Response: {response_text}")
            if response.status != 201:
                print(f"Failed Leave Status Code: {response.status}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def createthread(session, group_id, token, title):
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.yay.space/v1/threads"
    json_data = {
        "title": title,
        "group_id": group_id,
    }
    try:
        async with session.post(url, headers=headers, json=json_data) as response:
            response_text = await response.text()
            print(f"Thread Create Status Code: {response.status}, Response: {response_text}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def joiner(tokens, group_id):
    async with aiohttp.ClientSession() as session:
        for token in tokens:
            await join_group(session, group_id, token)
            await asyncio.sleep(1)

async def leaver(tokens, group_id):
    async with aiohttp.ClientSession() as session:
        for token in tokens:
            await leave_group(session, group_id, token)
            await asyncio.sleep(1)

async def spammer(tokens, group_id, base_message, num_messages, mention_random_member):
    async with aiohttp.ClientSession() as session:
        members = await fetch_group_members(session, group_id, random.choice(tokens))
        for _ in range(num_messages):
            token = random.choice(tokens)
            member = random.choice(members) if mention_random_member and members else None
            await send_message(session, group_id, member, base_message, token)
            await asyncio.sleep(0.3)

async def checker(tokens):
    async with aiohttp.ClientSession() as session:
        for token in tokens:
            await tokenchecker(session, token)
            await asyncio.sleep(0.2)

async def createThread(tokens, group_id, title, num):
    async with aiohttp.ClientSession() as session:
        for _ in range(num):
            token = random.choice(tokens)
            await createthread(session, group_id, token, title)
            await asyncio.sleep(0.3)

def display_menu():
    menu = [
        "╭────────────────────────────────────────────────────────────────────────────────────────────────╮",
        "│ «01» Joiner            «06» ???                «11» ???                 «16» ???               │",
        "│ «02» Leaver            «07» ???                «12» ???                 «17» ???               │",
        "│ «03» Spammer           «08» ???                «13» ???                 «18» ???               │",
        "│ «04» TokenChecker      «09» ???                «14» ???                 «19» ???               │",
        "│ «05» createThread      «10» ???                «15» ???                 «20» ???               │",
        "╰────────────────────────────────────────────────────────────────────────────────────────────────╯"
    ]
    for line in menu:
        print(Fore.MAGENTA + line.center(os.get_terminal_size().columns) + Fore.RESET)

def spinner():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if not spinner_active:
            break
        print(f'\rPress Enter to continue... {c}', end='', flush=True)
        time.sleep(0.2)
    print('\rPress Enter to continue... ', end='', flush=True)

async def main():
    while True:
        with open("token.txt", "r") as file:
            tokens = [line.strip() for line in file.readlines() if line.strip()]
        text1 = f"                                            Made By omonukko\n                                            Loaded <{len(tokens)}> tokens"

        text = "           Yay! Raider"
        font = "slant"
        ascii_art = pyfiglet.figlet_format(text, font=font)
        print(Fore.MAGENTA + ascii_art + Fore.RESET)
        print(Fore.MAGENTA + text1 + Fore.RESET) 
        display_menu()
        choice = input(f"{Fore.CYAN}Select Choice: {Fore.RESET}")
        
        if choice in ['1', '2', '3', '5']:
            group_id = input(f"{Fore.CYAN}Input Group ID: {Fore.RESET}")
        
        if choice == '1':
            os.system('cls' if os.name == 'nt' else 'clear')
            text = "Yay! Joiner"
            font = "slant"
            ascii_art = pyfiglet.figlet_format(text, font=font)
            print(Fore.MAGENTA + ascii_art + Fore.RESET)
            await joiner(tokens, group_id)
        elif choice == '2':
            os.system('cls' if os.name == 'nt' else 'clear')
            text = "Yay! Leaver"
            font = "slant"
            ascii_art = pyfiglet.figlet_format(text, font=font)
            print(Fore.MAGENTA + ascii_art + Fore.RESET)
            await leaver(tokens, group_id)
        elif choice == '3':
            os.system('cls' if os.name == 'nt' else 'clear')
            text = "Yay! Spammer"
            font = "slant"
            ascii_art = pyfiglet.figlet_format(text, font=font)
            print(Fore.MAGENTA + ascii_art + Fore.RESET)
            base_message = input(f"{Fore.CYAN}Message Input: {Fore.RESET}")
            num_messages = int(input(f"{Fore.CYAN}Num Messages: {Fore.RESET}"))
            mention_random_member = input(f"{Fore.CYAN}Random Mention? (y/n): {Fore.RESET}").lower() == 'y'
            await spammer(tokens, group_id, base_message, num_messages, mention_random_member)
        elif choice == '4':
            os.system('cls' if os.name == 'nt' else 'clear')
            text = "Yay! TokenChecker"
            font = "slant"
            ascii_art = pyfiglet.figlet_format(text, font=font)
            print(Fore.MAGENTA + ascii_art + Fore.RESET)
            await checker(tokens)
        elif choice == '5':
            os.system('cls' if os.name == 'nt' else 'clear')
            text = "Yay! CreateThreader"
            font = "slant"
            ascii_art = pyfiglet.figlet_format(text, font=font)
            print(Fore.MAGENTA + ascii_art + Fore.RESET)
            title = input(f"{Fore.CYAN}Title Input: {Fore.RESET}")
            num = int(input(f"{Fore.CYAN}Num Thread: {Fore.RESET}"))
            await createThread(tokens, group_id, title, num)
        else:
            print("Invalid Selection")

        global spinner_active
        spinner_active = True
        t = threading.Thread(target=spinner)
        t.start()
        input()
        spinner_active = False
        t.join()

        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    asyncio.run(main())
