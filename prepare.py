#!/usr/bin/env python3
"""Monta um post na fila: converte PNG->JPEG (a API só aceita JPEG p/ imagem) e
escreve agendados/<data>/post.json pronto pra publicar.

Uso:
  python prepare.py <data> <tipo> <arquivo...> [--legenda-arquivo cap.txt] [--comentario-arquivo tags.txt] [--cover capa.png]

Exemplos:
  # reel (o MP4 já tem áudio embutido; nada a converter)
  python prepare.py 2026-10-20 reel ../build/reels/l2-06-o-mesmo-lodo.mp4 --legenda-arquivo cap.txt --comentario-arquivo tags.txt

  # carrossel de poema (PNGs viram JPEG automaticamente)
  python prepare.py 2026-10-21 carrossel ../build/cards/l2-01-a-duvida-e-a-fe/*.png --legenda-arquivo cap.txt

  # foto única (versículo)
  python prepare.py 2026-10-22 foto ../build/versiculos/lote/01-e4-josue-1-9.png --legenda-arquivo cap.txt
"""
import argparse
import glob
import json
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))


def to_jpeg(src, dst):
    """PNG/qualquer imagem -> JPEG sRGB sem alpha, qualidade 92."""
    im = Image.open(src)
    if im.mode in ("RGBA", "P", "LA"):
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        fundo.paste(im, mask=im.split()[-1])
        im = fundo
    else:
        im = im.convert("RGB")
    im.save(dst, "JPEG", quality=92, optimize=True)


def copiar(src, pasta):
    """Copia pra pasta da fila, convertendo imagem p/ JPEG. Devolve o nome final."""
    base = os.path.basename(src)
    ext = os.path.splitext(base)[1].lower()
    if ext in (".mp4", ".mov"):
        shutil.copy2(src, os.path.join(pasta, base))
        return base
    nome = os.path.splitext(base)[0] + ".jpg"
    to_jpeg(src, os.path.join(pasta, nome))
    return nome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("tipo", choices=["foto", "reel", "carrossel"])
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--legenda-arquivo")
    ap.add_argument("--comentario-arquivo")
    ap.add_argument("--cover")
    a = ap.parse_args()

    # expande globs (o shell às vezes não expande dentro de aspas)
    arquivos = []
    for pat in a.arquivos:
        arquivos += sorted(glob.glob(pat)) or [pat]

    pasta = os.path.join(ROOT, "agendados", a.data)
    os.makedirs(pasta, exist_ok=True)

    finais = [copiar(f, pasta) for f in arquivos]
    post = {"tipo": a.tipo, "arquivos": finais}
    if a.cover:
        post["cover"] = copiar(a.cover, pasta)
    post["legenda"] = open(a.legenda_arquivo, encoding="utf-8").read().strip() if a.legenda_arquivo else ""
    post["comentario"] = open(a.comentario_arquivo, encoding="utf-8").read().strip() if a.comentario_arquivo else ""

    json.dump(post, open(os.path.join(pasta, "post.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[ok] fila montada: agendados/{a.data}/  ({a.tipo}, {len(finais)} arquivo(s))")
    print("      revise o post.json, faça git add/commit/push — o Actions publica no dia.")


if __name__ == "__main__":
    main()
