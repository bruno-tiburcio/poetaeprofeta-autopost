# autopost — publicação automática e GRÁTIS do @poetaeprofeta

Publica pela **API oficial da Meta** (Content Publishing). Sem bot, sem senha, sem risco de ban.
O Mac só **gera** a arte (pipeline atual) e dá `git push` da fila; o **GitHub Actions publica** no
horário, na nuvem — o Mac pode estar desligado.

```
Mac (gera arte) → prepare.py (PNG→JPEG + fila) → git push → GitHub Actions (cron diário) → API → Instagram
```

Tudo roda no **free tier**: API da Meta é grátis; repo público do GitHub = minutos de Actions
ilimitados + a própria `raw.githubusercontent.com` serve a mídia (a API exige URL público).

---

## 1. Setup da Meta (só você faz, ~20-30 min, uma vez)

> É a parte chata (os menus da Meta mudam de nome). Faça logado na conta do @poetaeprofeta.

1. **Conta profissional**: o @poetaeprofeta já é Creator → ok. (Se virar conta pessoal, a API para.)
2. Entre em **developers.facebook.com** → *Meus Apps* → **Criar app** → tipo **"Business"**.
3. No app, **Adicionar produto → Instagram** → escolha **"API setup with Instagram login"**
   (o fluxo NOVO — **não precisa de Página do Facebook**; ignore tutoriais do "Facebook Login").
4. Em *Instagram → API setup with Instagram login*: **adicione/conecte a conta @poetaeprofeta**
   e adicione você como **tester** (aceite o convite nas configs do Instagram, se pedir).
5. Permissões (scopes): **`instagram_business_basic`** + **`instagram_business_content_publish`**.
   Publicar na SUA própria conta usa **Standard Access** → **sem App Review**.
6. Gere o **token** (Business Login / gerador do painel). Ele vem curto (1h).
7. **Troque pelo long-lived (60 dias)** e anote:
   - **IG_TOKEN** = o token longo
   - **IG_USER_ID** = seu id (`GET https://graph.instagram.com/v21.0/me?fields=user_id&access_token=SEU_TOKEN`)

> Me manda `IG_USER_ID` e eu te ajudo a validar com um post de teste. **Nunca** me mande o token em texto aberto — ele vai só nos Secrets do GitHub.

## 2. Setup do GitHub (uma vez)

1. Crie um repo **PÚBLICO** (ex.: `poetaeprofeta-autopost`) e suba esta pasta `autopost/` como raiz dele.
2. Em *Settings → Secrets and variables → Actions → New repository secret*, crie:
   - `IG_USER_ID` — seu id numérico
   - `IG_TOKEN` — o long-lived token
   - `GH_PAT` — um token fine-grained DESTE repo com permissão **Secrets: write**
     (serve só pro workflow renovar o `IG_TOKEN` sozinho a cada 60 dias)
3. Pronto. O `refresh-token.yml` mantém o token vivo pra sempre; o `post.yml` publica todo dia.

## 3. Uso no dia a dia

```bash
# 1) gere a arte no pipeline de sempre (build/)
# 2) monte a fila (converte PNG→JPEG e escreve agendados/<data>/post.json):

python prepare.py 2026-10-20 reel      ../build/reels/l2-06-o-mesmo-lodo.mp4      --legenda-arquivo cap.txt --comentario-arquivo tags.txt
python prepare.py 2026-10-21 carrossel "../build/cards/l2-01-a-duvida-e-a-fe/*.png" --legenda-arquivo cap.txt --comentario-arquivo tags.txt
python prepare.py 2026-10-22 foto      ../build/versiculos/lote/01-e4-josue-1-9.png --legenda-arquivo cap.txt --comentario-arquivo tags.txt

# 3) revise, e empurre pro GitHub:
git add agendados && git commit -m "fila: posts da semana" && git push
```

No dia certo (06h BRT), o Actions publica e move a pasta p/ `publicados/`. Pra postar na hora:
*Actions → publicar-ig → Run workflow* (dá pra forçar uma data).

### Formato do `post.json` (o prepare.py gera, você só revisa)
```json
{
  "tipo": "reel",                 // reel | foto | carrossel
  "arquivos": ["l2-06-o-mesmo-lodo.mp4"],
  "cover": "capa.jpg",            // opcional (reel)
  "legenda": "poema completo...\n\nBruno Tiburcio",
  "comentario": "#poetaeprofeta #textosautorais #poesiasautorais ..."  // 1º comentário
}
```

## 4. Ponte no-code pra postar JÁ esta semana (Meta Business Suite)

Enquanto a API não está no ar, use o **Planner do Meta Business Suite** (grátis, oficial, risco zero):
1. **business.facebook.com** (ou app Meta Business Suite) → logar na conta.
2. **Planejar → Criar publicação** / **Criar reel** → selecione o Instagram.
3. Suba o arquivo (de `build/reels/` ou `build/cards/`), cole a legenda, **Agendar** no dia/hora.
4. Repita pra semana toda de uma vez (janela de ~75 dias à frente). Ele publica sozinho.

Contra: upload manual arquivo-a-arquivo (uns 10 min/semana). Migra pra API quando o setup estiver pronto.

## Gotchas (confirmados na pesquisa, out/2026)
- **Imagem só JPEG** — o `prepare.py` converte os PNG automaticamente. 1080×1350 (4:5) já é a proporção certa.
- **Carrossel** corta tudo pela proporção do 1º slide; mantenha os slides do mesmo tamanho. Máx **10**.
- **Reel** processa assíncrono — o `publish.py` faz polling até `FINISHED` antes de publicar.
- **Áudio do reel** tem que estar no MP4 (a API não deixa pôr música da biblioteca do IG). Use só **áudio livre** (mixkit) — copyright gera mute/strike.
- **URL público**: repo precisa ser **público** (a mídia é pública mesmo, vira post). O token fica só nos Secrets.
- **Token**: 60 dias, renovado sozinho pelo `refresh-token.yml`. Se parar de postar por 60 dias, o Actions agendado é desativado (basta reativar).
- **NUNCA** usar instagrapi/Selenium/painéis com senha nesta conta real — é o que a Meta bane.
