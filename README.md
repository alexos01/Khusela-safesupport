# Khusela: Safe Support

**Khusela** (isiZulu/siSwati for "protect") is a privacy-first web app that helps people affected by gender-based violence (GBV) in Eswatini, South Africa and neighbouring countries find trusted help, document incidents safely, raise an alert, and reach volunteer agents. It was built for the FNB hackathon (challenge: *Safer communities and gender-based violence response*) and is designed to be embedded in a banking app.

> **Safety notice:** this is a prototype. Check every helpline number before real use, and do not present it as a finished emergency service.

---

## Features

| Area | What it does |
|---|---|
| Get help | One-tap emergency and helpline calling by country, plus a "what happens next" guide |
| Find services | Filterable list of helplines, police, medical, legal and shelters |
| Ask Khusela | AI guide (Google Gemini) that answers safely, in English, isiZulu, siSwati or Sesotho |
| Safe record | Notes encrypted on the user's own device (AES-GCM) with a passphrase |
| Quick exit / Discreet | One tap (or Esc twice) switches to a fake weather screen; Discreet mode renames the app |
| Wrong-password protection | A wrong passphrase instantly shows the weather screen. Data is kept, locked |
| Secret word | Typed into the fake weather search box or the Ask box, it prepares a danger alert |
| Panic triggers | Shake the phone 4 times, or tap the Khusela name 3 times |
| Alerts | Opens WhatsApp with a ready message and (only if the user agrees) exact location |
| Safe check-in | Timer that prepares an alert if the user does not confirm they are safe |
| Safety plan | Personal checklist saved on the device |
| In-app reports | Anonymous report with a reference number and urgency rating; status check by reference |
| Agent desk | Prioritised case queue, status changes, case log, referrals to police, clinic and shelter |
| Agent training and vetting | Quiz before desk access; coordinator vetting checklist before approval |
| Languages | English, isiZulu, siSwati, Sesotho (main screens) |
| Offline | Service worker lets the app open without data after the first visit |
| USSD | Feature-phone menu in four languages (needs a shortcode from a network) |
| Triage tool | Python script that builds a priority queue and anonymous prevention statistics |

---

## Project structure

```
khusela/
├── docs/                     Website (GitHub Pages)
│   ├── index.html            The whole app: HTML, CSS and JavaScript
│   ├── sw.js                 Offline support
│   └── manifest.webmanifest  Install-as-app settings
├── backend/                  Server (PythonAnywhere)
│   ├── khusela_server.py     Entry point: cases, status, applications, USSD, setup checker
│   ├── gemini_server.py      Gemini AI proxy, rate limiting, CORS
│   ├── ussd_server.py        USSD menu logic
│   ├── pythonanywhere_wsgi.py  WSGI template for PythonAnywhere
│   ├── requirements.txt
│   └── .env.example          Settings template (copy to .env)
├── tools/khusela_triage.py   Priority queue and anonymous statistics
└── README.md
```

## Technologies

- **Front end:** HTML5, CSS3, vanilla JavaScript, Web Crypto API, Geolocation API, Service Worker, DeviceMotion API
- **Back end:** Python 3, Flask, SQLite, python-dotenv
- **AI:** Google Gemini API (called from the server, never from the page)
- **Messaging:** WhatsApp click-to-chat links, `tel:` links, USSD (Africa's Talking format)
- **Hosting:** GitHub Pages (website), PythonAnywhere (server)

---

## Setup

### 1. Backend on PythonAnywhere

1. Upload the project and unzip it in a Bash console, so the files are in `/home/YOURUSERNAME/khusela/`.
2. Install packages (a virtualenv is recommended):
   ```
   mkvirtualenv khusela --python=python3.10
   pip install -r ~/khusela/backend/requirements.txt
   ```
3. Create your settings file:
   ```
   cd ~/khusela/backend
   cp .env.example .env
   ```
4. Edit `.env` (see the table below).
5. On the **Web** tab: add a web app with **Manual configuration**, set the **Virtualenv** path to `/home/YOURUSERNAME/.virtualenvs/khusela`, open the WSGI configuration file, delete its contents, and paste in `pythonanywhere_wsgi.py` (replace `YOURUSERNAME`).
6. Click **Reload**.
7. Open `https://YOURUSERNAME.pythonanywhere.com/health`. It should say `ok`.

### 2. Settings (`backend/.env`)

| Setting | Meaning |
|---|---|
| `GEMINI_API_KEY` | Key from Google AI Studio. No quotes, no spaces |
| `GEMINI_MODEL` | Model name, for example `gemini-3.6-flash` |
| `AGENT_TOKEN` | Secret agents type into the Agent desk. Generate one: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALLOWED_ORIGIN` | Your website's address only, for example `https://alexos01.github.io` (no repository name, no trailing slash) |
| `DB_PATH` | Database file, for example `/home/YOURUSERNAME/khusela.db` |

Never upload `.env` to GitHub. After any change, click **Reload** on the Web tab.

### 3. Check the backend

Open `https://YOURUSERNAME.pythonanywhere.com/api/check`. You want:

- `gemini_key_set`, `agent_token_set` and `db_ok` all true
- `gemini_test` showing `ok`
- `allowed_origin` showing your site's address

Remove the `/api/check` route from `khusela_server.py` before real use.

### 4. Website on GitHub Pages

1. In `docs/index.html`, find the `var CFG=` line (near the end) and replace both `YOURUSERNAME` with your PythonAnywhere username:
   ```
   askUrl:"https://YOURUSERNAME.pythonanywhere.com/api/ask",
   api:"https://YOURUSERNAME.pythonanywhere.com/api",
   ```
2. In the same line, check the WhatsApp numbers (agent desk, volunteers, police, clinic, shelter). Use digits with country code and no plus sign, for example `26879765069`.
3. Upload the project to a GitHub repository.
4. **Settings → Pages**: source **Deploy from a branch**, branch `main`, folder `/docs`.
5. Open the site and press Ctrl+Shift+R to clear any old copy.

### 5. Run it on your own computer (optional)

```
cd backend
pip install -r requirements.txt
cp .env.example .env            # fill it in, set ALLOWED_ORIGIN=*
flask --app khusela_server run --port 3000
```
In another terminal: `cd docs && python3 -m http.server 8000`, then open `http://localhost:8000`. Temporarily change the two addresses in the `CFG` line to `http://localhost:3000/api/ask` and `http://localhost:3000/api`.

### 6. USSD (when you have a shortcode)

Register a shortcode with Africa's Talking or a mobile network and set the callback to `https://YOURUSERNAME.pythonanywhere.com/ussd`.

### 7. Triage tool

Export cases from the Agent desk (**Export cases (JSON)**), then:
```
python3 tools/khusela_triage.py khusela-cases.json
```
This creates `priority_queue.csv` and `prevention_report.json` (anonymous counts only).

---

## Using the Agent desk

1. Open the **Agent desk** tab and pass the training quiz (4 of 5).
2. Enter the `AGENT_TOKEN` and click **Open desk**.
3. Cases appear most urgent first. Update status, add notes, open the survivor's location link, or refer to police, clinic or shelter (only with the survivor's consent).
4. Coordinators approve volunteer applications once ID, two references, police clearance and an interview are ticked.

## How alerts work

Alerts open WhatsApp with a ready message. The person still taps send. Location is only read when an alert is sent, and only if the user turned it on in **Safety setup**. Silent background alerts, SMS fallback and power-button triggers need the native FNB app.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: khusela_server` | Wrong `path` in the WSGI file, or the file is not in `backend/` |
| `ModuleNotFoundError: flask` | Set the **Virtualenv** path on the Web tab and reload |
| `gemini_test` shows `HTTP 401` | API key is invalid. Create a new one and update `.env` |
| `gemini_test` shows `HTTP 404` | Wrong model name in `GEMINI_MODEL` |
| AI or reports fail on the site | `ALLOWED_ORIGIN` is wrong, or `CFG` still says `YOURUSERNAME` |
| "Code not recognised" in the Agent desk | The old page is deployed. Use `docs/index.html` and clear the cache |
| "No desk access" | Token does not match `AGENT_TOKEN`. Retype it and reload the server |
| Browser shows 401 on `/api/col/cases` | Normal. The list is locked without the token |

---

## Security and privacy

- No accounts, names or tracking are required for survivors.
- Safe record text is encrypted in the browser and never sent anywhere.
- The Gemini key stays on the server. Questions are not logged.
- Survivors can only read a case's status, never its text. Agents need the token.

**Known limits (prototype):**
- One shared agent token, instead of individual agent accounts with two-factor login.
- Case text and contact numbers are stored unencrypted in SQLite.
- The training pass is remembered in the browser only.
- Helpline numbers must be confirmed by each organisation. Only South Africa and Eswatini are fully listed.
- Translations were not reviewed by native speakers.
- Police, clinic and shelter referrals open WhatsApp and are not linked to official systems.

## Roadmap

Individual agent accounts with two-factor login, encrypted storage for cases, verified services with last-checked dates, native FNB app features (silent alerts, SMS fallback, power-button trigger), native-speaker review of translations, links with police, health and shelter systems, and POPIA / local data-protection review.

## Emergency numbers (check before use)

- **South Africa:** Police 10111, GBV Command Centre 0800 428 428
- **Eswatini:** Police 999, SWAGAA 951

If you are in danger, call the emergency number for your country first.

here is the link for trying it out:

https://alexos01.github.io/Khusela-safesupport
