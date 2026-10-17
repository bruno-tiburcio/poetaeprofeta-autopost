#!/usr/bin/env python3
"""Cliente mínimo da Instagram Content Publishing API (fluxo 'Instagram API with Instagram Login').

Base: graph.instagram.com. Publica foto, carrossel e reel na PRÓPRIA conta profissional.
Nada de login usuário/senha — é o canal oficial da Meta (sem risco de ban).
"""
import time
import requests

API = "https://graph.instagram.com"
VER = "v21.0"


def _url(path, versioned=True):
    return f"{API}/{VER}/{path}" if versioned else f"{API}/{path}"


def create_media(ig_id, token, **params):
    """Cria um 'media container'. Devolve o creation_id."""
    params["access_token"] = token
    r = requests.post(_url(f"{ig_id}/media"), data=params, timeout=120)
    _check(r)
    return r.json()["id"]


def container_status(cid, token):
    r = requests.get(_url(cid), params={"fields": "status_code", "access_token": token}, timeout=30)
    _check(r)
    return r.json().get("status_code")


def wait_finished(cid, token, timeout=420, every=6):
    """Reel/vídeo processam de forma assíncrona: espera o container ficar FINISHED."""
    start = time.time()
    last = None
    while time.time() - start < timeout:
        last = container_status(cid, token)
        if last == "FINISHED":
            return
        if last == "ERROR":
            raise RuntimeError(f"container {cid} voltou ERROR")
        time.sleep(every)
    raise TimeoutError(f"container {cid} não ficou FINISHED em {timeout}s (último status: {last})")


def publish(ig_id, token, creation_id):
    """Publica o container. Devolve o id da mídia publicada."""
    r = requests.post(_url(f"{ig_id}/media_publish"),
                      data={"creation_id": creation_id, "access_token": token}, timeout=120)
    _check(r)
    return r.json()["id"]


def comment(media_id, token, message):
    """Posta um comentário na mídia (usamos p/ o 1º comentário com as hashtags da casa)."""
    r = requests.post(_url(f"{media_id}/comments"),
                      data={"message": message, "access_token": token}, timeout=30)
    _check(r)
    return r.json().get("id")


def refresh_token(token):
    """Estende o long-lived token por +60 dias (precisa ter >=24h de vida)."""
    r = requests.get(_url("refresh_access_token", versioned=False),
                     params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30)
    _check(r)
    return r.json()  # {access_token, token_type, expires_in}


def _check(r):
    if not r.ok:
        try:
            err = r.json().get("error", {})
            raise RuntimeError(f"IG API {r.status_code}: {err.get('message')} "
                               f"(code={err.get('code')}, sub={err.get('error_subcode')})")
        except ValueError:
            r.raise_for_status()
