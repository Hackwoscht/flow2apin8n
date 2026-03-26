# Flow2API

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.119.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

**Ein vollständiger OpenAI-kompatibler API-Dienst für Google Flow (Gemini / Imagen / Veo)**

</div>

## ✨ Kernfunktionen

- 🎨 Text-zu-Bild / Bild-zu-Bild
- 🎬 Text-zu-Video / Bild-zu-Video
- 🎞️ Anfangs-/Endframe-Video
- 🔄 AT/ST automatische Erneuerung — AT wird bei Ablauf automatisch erneuert, ST wird bei Ablauf automatisch über den Browser aktualisiert (Personal-Modus)
- 📊 Guthaben-Anzeige — Echtzeit-Abfrage und Anzeige der VideoFX Credits
- 🚀 Lastverteilung — Multi-Token-Rotation und Parallelitätssteuerung
- 🌐 Proxy-Unterstützung — HTTP/SOCKS5 Proxy
- 📱 Web-Verwaltungsoberfläche — intuitive Token- und Konfigurationsverwaltung
- 🎨 Bildgenerierung mit fortlaufendem Dialog
- 🧩 Gemini offizielles Request-Format kompatibel
- ✅ Gemini offizielles Format getestet und funktioniert

---

## 🚀 Schnellstart

### Voraussetzungen

- Docker und Docker Compose (empfohlen)
- Oder Python 3.8+
- Captcha-Lösung: Drittanbieter (CapSolver/YesCaptcha) oder Browser-Captcha (headed)
- Automatische ST-Aktualisierung per Browser-Erweiterung: [Flow2API-Token-Updater](https://github.com/TheSmallHanCat/Flow2API-Token-Updater)

---

### Methode 1: Docker-Deployment (empfohlen)

#### Standardmodus (ohne Proxy)

```bash
git clone https://github.com/Hackwoscht/flow2apin8n.git
cd flow2apin8n
docker-compose up -d
docker-compose logs -f
```

#### Docker Headed-Captcha-Modus (browser / personal)

```bash
docker compose -f docker-compose.headed.yml up -d --build
docker compose -f docker-compose.headed.yml logs -f
```

- API-Port: `8000`
- Nach dem Start im Admin-Panel die Captcha-Methode auf `browser` oder `personal` setzen

### Methode 2: Lokales Deployment

```bash
git clone https://github.com/Hackwoscht/flow2apin8n.git
cd flow2apin8n
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

### Erster Zugriff

Nach dem Start: **http://localhost:8000** — beim ersten Login sofort das Passwort ändern!

- Benutzername: `admin`
- Passwort: `admin`

---

## 📡 API-Nutzung (Streaming erforderlich)

```bash
# Text-zu-Bild
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer DEIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-3.1-flash-image-landscape","messages":[{"role":"user","content":"Eine Katze im Garten"}],"stream":true}'

# Text-zu-Video
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer DEIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"veo_3_1_t2v_fast_landscape","messages":[{"role":"user","content":"Ein Kätzchen jagt Schmetterlinge"}],"stream":true}'
```

Auch Gemini-Format unterstützt: `POST /models/{model}:generateContent`

---

## 📄 Lizenz

MIT-Lizenz. Siehe [LICENSE](LICENSE).

## 🙏 Danksagung

- [PearNoDec](https://github.com/PearNoDec) — YesCaptcha-Lösung
- [raomaiping](https://github.com/raomaiping) — Headless-Captcha-Lösung
- [TheSmallHanCat](https://github.com/TheSmallHanCat/flow2api) — Original-Projekt

⭐ Wenn dir dieses Projekt hilft, gib ihm einen Star!
