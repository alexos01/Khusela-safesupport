#!/usr/bin/env python3
"""Khusela USSD service for feature phones (Africa's Talking format).
Run: pip install flask ; python ussd_server.py   (set callback URL in the AT dashboard)
Replies start with CON (menu continues) or END (session ends)."""
import json, time, hashlib, random, string

TXT = {
 "en": {"menu": "Khusela\n1 Emergency numbers\n2 I need help now\n3 Signs of abuse\n4 Safety tips",
        "emerg": "SA: Police 10111, GBV 0800 428 428\nEswatini: Police 999, SWAGAA 951",
        "ask": "Reply with a short message about what is happening (no names). 0 to cancel.",
        "signs": "Signs: injuries, fear, control of money or phone, isolation, threats, forced sex. It is never your fault.",
        "tips": "Plan a safe place and a person to call. Keep ID and a charged phone ready. Seek a clinic within 72h after rape.",
        "sent": "Received. An agent will contact you. Ref {ref}. In danger now? Call 10111 or 999."},
 "zu": {"menu": "Khusela\n1 Izinombolo eziphuthumayo\n2 Ngidinga usizo manje\n3 Izimpawu zodlame\n4 Amathiphu okuphepha",
        "emerg": "SA: Amaphoyisa 10111, GBV 0800 428 428\nEswatini: 999, SWAGAA 951",
        "ask": "Bhala umlayezo omufushane ngalokho okwenzekayo (ungabhali amagama). 0 ukukhansela.",
        "signs": "Izimpawu: ukulimala, ukwesaba, ukulawulwa kwemali noma ifoni, ukuzihlukanisa, izinsongo. Akulona iphutha lakho.",
        "tips": "Hlela indawo ephephile nomuntu ozomshayela. Gcina ID nefoni ishajiwe. Iya emtholampilo emahoreni angu-72.",
        "sent": "Samukelwe. Umsizi uzokufinyelela. Ref {ref}. Usengozini? Shayela 10111 noma 999."},
 "ss": {"menu": "Khusela\n1 Tinombolo tesiphutfumako\n2 Ngidzinga lusito nyalo\n3 Timphawu tebudlova\n4 Tincomo tekuphepha",
        "emerg": "SA: Emaphoyisa 10111, GBV 0800 428 428\nEswatini: 999, SWAGAA 951",
        "ask": "Bhala umlayeto lofishane ngalokwenteka (ungabhali emagama). 0 kukhansela.",
        "signs": "Timphawu: kulimala, kwesaba, kulawulwa kwemali nome luchuze, kuhlukaniswa, tintfokotelo. Akusilo licala lakho.",
        "tips": "Hlela indzawo lephephile nemuntfu lotamshayela. Gcina ID nelucingo lushajiwe. Iya emtfolamphilo emahoreni la-72.",
        "sent": "Samukelwe. Lusiti utakutsintsa. Ref {ref}. Usengotini? Shayela 999."},
 "st": {"menu": "Khusela\n1 Dinomoro tsa tshohanyetso\n2 Ke hloka thuso hona jwale\n3 Matshwao a pefo\n4 Malebela a polokeho",
        "emerg": "SA: Mapolesa 10111, GBV 0800 428 428\nEswatini: 999, SWAGAA 951",
        "ask": "Ngola molaetsa o motjhesa ka se etsahalang (ntle le mabitso). 0 ho hlakola.",
        "signs": "Matshwao: ho gobala, tshabo, taolo ya tjhelete kapa mohala, ho ikarola, ditshokolo. Ha se phoso ya hao.",
        "tips": "Rala sebaka se sireletsehileng le motho eo o ka mmitsang. Boloka ID le mohala o tjhajitsweng. Eya kliniking ka hare ho dihora tse 72.",
        "sent": "Re amohetse. Moemeli o tla ikutlwisa. Ref {ref}. O kotsing? Letsetsa 999."},
}
LANGS = {"1": "en", "2": "zu", "3": "ss", "4": "st"}
LANG_MENU = "CON Khusela\n1 English\n2 isiZulu\n3 siSwati\n4 Sesotho"
QUEUE = "ussd_cases.jsonl"  # replace with the secure case API

def ref():
    return "KH-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def save_case(phone, lang, message):
    r = ref()
    rec = {"ref": r, "channel": "ussd", "lang": lang, "summary": message, "urgency": "High",
           "status": "Received", "contact_hash": hashlib.sha256(phone.encode()).hexdigest()[:16],
           "contact": phone.lstrip("+"), "t": int(time.time() * 1000), "country": "Unknown", "log": []}
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return r

def handle(text, phone):
    """text is the full path typed so far, joined by '*', e.g. '2*2*my message'."""
    p = text.split("*") if text else []
    if not p:
        return LANG_MENU
    lang = LANGS.get(p[0])
    if not lang:
        return LANG_MENU
    t = TXT[lang]
    if len(p) == 1:
        return "CON " + t["menu"]
    c = p[1]
    if c == "1": return "END " + t["emerg"]
    if c == "3": return "END " + t["signs"]
    if c == "4": return "END " + t["tips"]
    if c == "2":
        if len(p) == 2: return "CON " + t["ask"]
        msg = p[2].strip()
        if msg == "0": return "END Cancelled"
        return "END " + t["sent"].format(ref=save_case(phone, lang, msg[:300]))
    return "CON " + t["menu"]

if __name__ == "__main__":
    from flask import Flask, request
    app = Flask(__name__)
    @app.post("/ussd")
    def ussd():
        return handle(request.form.get("text", ""), request.form.get("phoneNumber", "")), 200, {"Content-Type": "text/plain"}
    app.run(port=5000)
