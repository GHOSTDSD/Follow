# api/index.py
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from curl_cffi import requests

app = FastAPI(title="Roblox Follow API - Vercel")

# ======== MODELO DO BODY ============
class FollowRequest(BaseModel):
    user_id: int
    cookie: str

# ======== PEGAR X-CSRF-TOKEN ============
def get_csrf(cookie: str):
    try:
        session = requests.Session()
        r = session.post(
            "https://auth.roblox.com/v2/logout",
            headers={"Cookie": f".ROBLOSECURITY={cookie}"},
            impersonate="chrome110",
            timeout=10
        )
        return r.headers.get("x-csrf-token")
    except:
        return None

# ======== TENTAR FOLLOW ============
def follow_user(user_id: int, cookie: str, csrf: str):
    session = requests.Session()

    headers = {
        "Content-Type": "application/json",
        "Cookie": f".ROBLOSECURITY={cookie}",
        "X-CSRF-TOKEN": csrf,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://www.roblox.com",
        "Referer": f"https://www.roblox.com/users/{user_id}/profile"
    }

    response = session.post(
        f"https://friends.roblox.com/v1/users/{user_id}/follow",
        headers=headers,
        data=json.dumps({}),
        impersonate="chrome110",
        timeout=10
    )

    return response


# ======== ENDPOINT PRINCIPAL ===============
@app.post("/follow")
def follow(req: FollowRequest):

    # Obter token CSRF
    csrf = get_csrf(req.cookie)
    if not csrf:
        raise HTTPException(status_code=500, detail="Não foi possível obter X-CSRF-TOKEN")

    # Tentar follow
    r = follow_user(req.user_id, req.cookie, csrf)

    if r.status_code == 200:
        return {"success": True, "message": f"Follow realizado com sucesso em {req.user_id}"}

    # 403 → tentar renovar token e tentar de novo
    if r.status_code == 403:
        new_csrf = get_csrf(req.cookie)
        if new_csrf and new_csrf != csrf:
            r2 = follow_user(req.user_id, req.cookie, new_csrf)
            if r2.status_code == 200:
                return {"success": True, "message": f"Follow OK (token renovado) em {req.user_id}"}

        raise HTTPException(status_code=403, detail="403 Forbidden — Cookie inválido ou sem permissão")

    # Outros erros
    raise HTTPException(status_code=r.status_code, detail=r.text)
