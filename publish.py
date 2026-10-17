#!/usr/bin/env python3
"""Publica UM post da fila no Instagram, via API oficial.

Lê  agendados/<data>/post.json  (data = hoje em BRT por padrão, ou POST_DATE / argv[1]).
Monta os URLs públicos (raw.githubusercontent) dos arquivos, cria o container,
publica, e posta as hashtags no 1º comentário. Depois move a pasta p/ publicados/.

Env esperados (vêm dos GitHub Secrets no Actions):
  IG_USER_ID  = id numérico da sua conta IG
  IG_TOKEN    = long-lived access token
  REPO_RAW    = https://raw.githubusercontent.com/<user>/<repo>/<branch>
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import ig_api

ROOT = os.path.dirname(os.path.abspath(__file__))
BRT = timezone(timedelta(hours=-3))


def hoje_brt():
    return datetime.now(BRT).strftime("%Y-%m-%d")


def raw_url(data, fname):
    base = os.environ["REPO_RAW"].rstrip("/")
    return f"{base}/agendados/{data}/{fname}"


def publicar(data):
    ig_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_TOKEN"]
    pasta = os.path.join(ROOT, "agendados", data)
    meta_path = os.path.join(pasta, "post.json")
    if not os.path.exists(meta_path):
        print(f"[skip] sem post agendado p/ {data} ({meta_path} não existe)")
        return False

    post = json.load(open(meta_path, encoding="utf-8"))
    tipo = post["tipo"]
    arqs = post["arquivos"]
    legenda = post.get("legenda", "")
    coment = post.get("comentario", "")
    print(f"[{data}] publicando tipo={tipo} arquivos={arqs}")

    if tipo == "foto":
        cid = ig_api.create_media(ig_id, token, image_url=raw_url(data, arqs[0]), caption=legenda)
        media_id = ig_api.publish(ig_id, token, cid)

    elif tipo == "reel":
        params = dict(media_type="REELS", video_url=raw_url(data, arqs[0]), caption=legenda)
        if post.get("cover"):
            params["cover_url"] = raw_url(data, post["cover"])
        cid = ig_api.create_media(ig_id, token, **params)
        ig_api.wait_finished(cid, token)
        media_id = ig_api.publish(ig_id, token, cid)

    elif tipo == "carrossel":
        if len(arqs) > 10:
            raise ValueError("carrossel aceita no máximo 10 itens")
        filhos = []
        for f in arqs:
            is_video = f.lower().endswith((".mp4", ".mov"))
            kw = {"video_url" if is_video else "image_url": raw_url(data, f), "is_carousel_item": "true"}
            fcid = ig_api.create_media(ig_id, token, **kw)
            if is_video:
                ig_api.wait_finished(fcid, token)
            filhos.append(fcid)
        cid = ig_api.create_media(ig_id, token, media_type="CAROUSEL",
                                  children=",".join(filhos), caption=legenda)
        media_id = ig_api.publish(ig_id, token, cid)

    else:
        raise ValueError(f"tipo desconhecido: {tipo}")

    print(f"[ok] publicado media_id={media_id}")
    if coment:
        try:
            ig_api.comment(media_id, token, coment)
            print("[ok] 1º comentário (hashtags) postado")
        except Exception as e:  # noqa: BLE001 — comentário é secundário, não derruba o post
            print(f"[aviso] falhou o 1º comentário: {e}")

    # arquiva: move a pasta p/ publicados/ (o workflow commita a mudança)
    destino = os.path.join(ROOT, "publicados", data)
    os.replace(pasta, destino)
    print(f"[ok] movido p/ publicados/{data}")
    return True


if __name__ == "__main__":
    data = (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("POST_DATE", "") or hoje_brt()
    ok = publicar(data)
    sys.exit(0 if ok else 0)  # sem post do dia != erro
