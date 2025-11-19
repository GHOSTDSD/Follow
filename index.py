import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from curl_cffi import requests

app = FastAPI()

# ======= MODELO DA REQUEST =======
class FollowRequest(BaseModel):
    user_id: int
    cookie: str

# ======= FUNÇÃO PARA PEGAR CSRF =======
def get_csrf(cookie):
    try:
        session = requests.Session()

        r = session.post(
            "https://auth.roblox.com/v2/logout",
            headers={"Cookie": f".ROBLOSECURITY={cookie}"},
            impersonate="chrome110"
        )
        token = r.headers.get("x-csrf-token")
        return token
    except:
        return None

# ======= EXECUTAR O FOLLOW =========
def follow_user(user_id, cookie):
    session = requests.Session()

    csrf = get_csrf(cookie)
    if not csrf:
        return False, "Não foi possível obter o token CSRF."

    headers = {
        "Content-Type": "application/json",
        "Cookie": f".ROBLOSECURITY={cookie}",
        "X-CSRF-TOKEN": csrf,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Origin": "https://www.roblox.com",
        "Referer": f"https://www.roblox.com/users/{user_id}/profile"
    }

    response = session.post(
        f"https://friends.roblox.com/v1/users/{user_id}/follow",
        headers=headers,
        data=json.dumps({}),
        impersonate="chrome110"
    )

    if response.status_code == 200:
        return True, "Follow realizado com sucesso!"
    else:
        return False, f"Erro {response.status_code}: {response.text}"

# ======= ENDPOINT DA API ==========
@app.post("/follow")
def api_follow(data: FollowRequest):
    ok, msg = follow_user(data.user_id, data.cookie)
    return {
        "success": ok,
        "message": msg
    }
