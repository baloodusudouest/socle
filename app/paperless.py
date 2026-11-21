"""Client Paperless-ngx commun des applis maison (socle 0.12.0) — copié tel quel dans chaque appli qui range ou lit des
papiers dans Paperless (Gazette, Dîme ; carnet plus tard). Bibliothèque standard seulement, comme maison.py.

Ce que la sonde du 21/11/2026 a établi sur la vraie installation (Paperless-ngx 3.5.1, API 10) et que ce module suit :
  - un compte par appli (jeton dans la stack, vide = service coupé) ; l'appli est propriétaire de ce qu'elle envoie par
    l'API et le retrouve PAR SON TITRE (les tâches de Paperless 3 sont introuvables par leur task_id) ;
  - Paperless 3 ACCEPTE les doublons (second document relié au premier) : avant tout envoi on cherche le titre ; un envoi
    parti n'est JAMAIS renvoyé tant que la recherche n'a pas conclu ; un renvoi voulu porte un autre titre ;
  - une étiquette ou un type créé par l'appli l'est avec l'appariement désactivé (matching_algorithm = 0) ;
  - en-tête « Accept: application/json; version=10 ».

Usage (dans une appli) :
    from app import paperless
    client = paperless.Paperless(url=..., jeton=..., lecture_seule=lambda: maison.lecture_seule("GAZETTE_LECTURE_SEULE"))
    file = paperless.FileEnvois(client, chemin=data / "paperless-envois.json", lire_source=lambda ref: ...)
    file.ajouter(cle="gazette-12", source="livret/12", titre="Gazette — Prénom NOM — 12/12/2026", date="2026-12-12",
                 type_nom="Journal maison", etiquettes=["Prénom NOM"], nom_fichier="gazette-12.pdf")
    file.tour()                     # dans une tâche de fond, un envoi à la fois
    paperless.declarer_service(services, client, file, lit="…", ecrit="…", reglage="GAZETTE_PAPERLESS_JETON")
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

VERSION = "0.12.0"            # version du socle d'où vient ce fichier
VERSION_API = 10              # relevée par la sonde du 21/11/2026 (Paperless-ngx 3.5.1)
DELAI_S = 10.0                # délai d'une requête
ATTENTE_RETROUVER_S = 120     # après un envoi : recherche du titre toutes les 10 s, 2 min au plus dans le même tour
INTERVALLE_RETROUVER_S = 10
REESSAI_S = 600               # un échec réseau : nouvel essai au plus tôt 10 min après
INTROUVABLE_APRES_S = 1800    # envoi parti mais titre toujours introuvable après 30 min : « à vérifier », jamais renvoyé
SIGNALER_APRES_S = 86400      # en attente depuis plus de 24 h : signalé dans la fiche « Connexion »
ETATS = ("attente", "parti", "range", "a_verifier", "abandon")


class ErreurPaperless(Exception):
    """Réponse inattendue de Paperless (code HTTP et court message, jamais de jeton)."""

    def __init__(self, code: int, message: str = ""):
        super().__init__(f"Paperless a répondu {code}" + (f" : {message}" if message else ""))
        self.code = code


def maintenant() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _vrai(v) -> bool:
    try:
        return bool(v() if callable(v) else v)
    except Exception:                                    # noqa: BLE001 — un réglage illisible = faux
        return False


def transport_urllib(methode: str, url: str, entetes: dict, donnees: bytes | None, delai: float):
    """Transport réel (urllib). Rend (code, en-têtes, octets) ; une erreur réseau lève OSError."""
    req = urllib.request.Request(url, data=donnees, headers=entetes, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:    # noqa: S310 — adresse de la stack
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


class Paperless:
    """Accès à l'API de Paperless avec le jeton d'un compte d'appli. Aucune suppression n'est jamais demandée."""

    def __init__(self, url: str | None, jeton: str | None, lecture_seule=False, delai: float = DELAI_S,
                 transport=None):
        self.url = (url or "").strip().rstrip("/")
        self.jeton = (jeton or "").strip()
        self._lecture_seule = lecture_seule
        self.delai = delai
        self.transport = transport or transport_urllib
        self._cache: dict[str, tuple[float, dict]] = {}
        self.version_vue: str | None = None

    # ---------------------------------------------------------------- état
    @property
    def regle(self) -> bool:
        """Relié dans la stack : adresse et jeton présents."""
        return bool(self.url and self.jeton)

    @property
    def lecture_seule(self) -> bool:
        return _vrai(self._lecture_seule)

    # ---------------------------------------------------------------- requêtes
    def _appel(self, methode: str, chemin: str, *, corps=None, multipart=None, brut: bool = False):
        if not self.regle:
            raise ErreurPaperless(0, "pas relié (adresse ou jeton absent)")
        entetes = {"Authorization": f"Token {self.jeton}", "Accept": f"application/json; version={VERSION_API}",
                   "User-Agent": "maison"}
        donnees = None
        if multipart is not None:
            limite = "----maison" + uuid.uuid4().hex
            morceaux = []
            for nom, valeur in multipart:
                if isinstance(valeur, tuple):            # (nom_fichier, octets)
                    morceaux.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nom}"; '
                                    f'filename="{valeur[0]}"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
                                    + valeur[1] + b"\r\n")
                else:
                    morceaux.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nom}"\r\n\r\n'
                                    f"{valeur}\r\n".encode())
            morceaux.append(f"--{limite}--\r\n".encode())
            donnees = b"".join(morceaux)
            entetes["Content-Type"] = f"multipart/form-data; boundary={limite}"
        elif corps is not None:
            donnees = json.dumps(corps).encode()
            entetes["Content-Type"] = "application/json"
        code, tetes, contenu = self.transport(methode, self.url + chemin, entetes, donnees, self.delai)
        version = {k.lower(): v for k, v in (tetes or {}).items()}.get("x-version")
        if version:
            self.version_vue = version
        if not 200 <= code < 300:
            message = ""
            try:
                d = json.loads(contenu or b"null")
                message = d.get("detail", "") if isinstance(d, dict) else ""
            except ValueError:
                pass
            raise ErreurPaperless(code, str(message)[:120])
        if brut:
            return contenu
        return json.loads(contenu) if contenu else None

    @staticmethod
    def _q(v: str) -> str:
        return urllib.parse.quote(v, safe="")

    # ---------------------------------------------------------------- essai léger (fiche « Connexion »)
    def essai(self) -> tuple[bool, str]:
        """Lit une page d'un document (rien d'écrit). Rend (True, « Paperless 3.5.1, API 10. »)."""
        self._appel("GET", "/api/documents/?page_size=1&fields=id")
        return True, (f"Paperless {self.version_vue}, API {VERSION_API}." if self.version_vue else None)

    # ---------------------------------------------------------------- étiquettes et types
    def _objet(self, genre: str, nom: str, creer: bool) -> int | None:
        """genre : « tags » ou « document_types ». Retrouve par le nom exact ; crée sans appariement si demandé."""
        nom = (nom or "").strip()
        if not nom:
            return None
        cle = f"{genre}:{nom.lower()}"
        en_cache = self._cache.get(cle)
        if en_cache and time.monotonic() - en_cache[0] < 600:
            return en_cache[1]["id"]
        d = self._appel("GET", f"/api/{genre}/?name__iexact={self._q(nom)}&page_size=10")
        for o in (d or {}).get("results", []):
            if (o.get("name") or "").strip().lower() == nom.lower():
                self._cache[cle] = (time.monotonic(), o)
                return o["id"]
        if not creer or self.lecture_seule:
            return None
        o = self._appel("POST", f"/api/{genre}/", corps={"name": nom, "matching_algorithm": 0})
        self._cache[cle] = (time.monotonic(), o)
        return o["id"]

    def etiquette(self, nom: str, creer: bool = True) -> int | None:
        return self._objet("tags", nom, creer)

    def type_document(self, nom: str, creer: bool = True) -> int | None:
        return self._objet("document_types", nom, creer)

    # ---------------------------------------------------------------- documents
    def chercher_titre(self, titre: str) -> int | None:
        """Numéro du document (visible par ce compte) dont le titre est exactement celui-ci, sinon None."""
        d = self._appel("GET", f"/api/documents/?title__icontains={self._q(titre)}&page_size=25"
                               "&fields=id,title&ordering=-added")
        exacts = [o["id"] for o in (d or {}).get("results", []) if (o.get("title") or "") == titre]
        return exacts[0] if exacts else None

    def envoyer_brut(self, pdf: bytes, nom_fichier: str, titre: str, date: str | None = None,
                     type_id: int | None = None, etiquettes: list[int] | None = None) -> None:
        """POST /api/documents/post_document/. Ne dit pas le numéro : le chercher ensuite par le titre."""
        if self.lecture_seule:
            raise ErreurPaperless(0, "lecture seule")
        champs: list = [("title", titre)]
        if date:
            champs.append(("created", date[:10]))
        if type_id:
            champs.append(("document_type", str(type_id)))
        for e in etiquettes or []:
            champs.append(("tags", str(e)))
        champs.append(("document", (nom_fichier or "document.pdf", pdf)))
        self._appel("POST", "/api/documents/post_document/", multipart=champs)

    def documents(self, etiquette_id: int, champs: str = "id,title,owner,created,added,modified,tags") -> list[dict]:
        """Tous les documents visibles portant cette étiquette (toutes les pages)."""
        res, page = [], 1
        while True:
            d = self._appel("GET", f"/api/documents/?tags__id__all={etiquette_id}&page_size=100&page={page}"
                                   f"&fields={champs}&ordering=added")
            res.extend((d or {}).get("results", []))
            if not (d or {}).get("next") or page >= 50:
                return res
            page += 1

    def document(self, doc_id: int) -> dict:
        return self._appel("GET", f"/api/documents/{int(doc_id)}/")

    def texte(self, doc_id: int) -> str:
        """Texte déjà extrait par Paperless (champ content) : jamais de nouvel OCR côté appli."""
        return (self.document(doc_id) or {}).get("content") or ""

    def telecharger(self, doc_id: int) -> bytes:
        return self._appel("GET", f"/api/documents/{int(doc_id)}/download/?original=true", brut=True)


class FileEnvois:
    """File d'envoi locale : un envoi à la fois, retrouvé par son titre, jamais renvoyé à l'aveugle.

    Chaque élément : cle (unique, choisie par l'appli), source (référence que l'appli sait relire : JAMAIS de copie du
    PDF dans la file), titre (unique dans Paperless), date, type_nom, etiquettes (noms), nom_fichier, etat, document_id,
    essais, erreur, cree_le, parti_le, range_le, prochain_essai.
    Stockage : fichier JSON (chemin=) ou fonctions charger()/sauver(liste) fournies par l'appli (Dîme : son coffre).
    """

    def __init__(self, client: Paperless, *, chemin: str | Path | None = None, charger=None, sauver=None,
                 lire_source=None, apres_range=None, horloge=time.time, dormir=time.sleep):
        if chemin is None and (charger is None or sauver is None):
            raise ValueError("chemin, ou charger et sauver, sont nécessaires")
        self.client = client
        self.chemin = Path(chemin) if chemin else None
        self._charger = charger
        self._sauver = sauver
        self.lire_source = lire_source
        self.apres_range = apres_range               # rappel(element) quand un document est rangé (numéro connu)
        self.horloge = horloge
        self.dormir = dormir
        self._verrou = threading.RLock()
        self.dernier_tour: str | None = None
        self.dernier_range: str | None = None

    # ---------------------------------------------------------------- stockage
    def _lire(self) -> list[dict]:
        if self._charger is not None:
            return list(self._charger() or [])
        try:
            return json.loads(self.chemin.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def _ecrire(self, liste: list[dict]) -> None:
        if self._sauver is not None:
            self._sauver(liste)
            return
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.chemin.with_suffix(".tmp")
        tmp.write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.chemin)

    # ---------------------------------------------------------------- lecture
    def elements(self) -> list[dict]:
        with self._verrou:
            return [dict(e) for e in self._lire()]

    def element(self, cle: str) -> dict | None:
        return next((e for e in self.elements() if e["cle"] == cle), None)

    def resume(self) -> dict:
        liste = self.elements()
        compte = {k: 0 for k in ETATS}
        for e in liste:
            compte[e.get("etat", "attente")] = compte.get(e.get("etat", "attente"), 0) + 1
        en_attente = [e for e in liste if e.get("etat") in ("attente", "parti")]
        vieux = min((e["cree_le"] for e in en_attente), default=None)
        signaler = False
        if vieux:
            try:
                signaler = (datetime.now().astimezone() - datetime.fromisoformat(vieux)).total_seconds() > SIGNALER_APRES_S
            except ValueError:
                signaler = False
        return {"compte": compte, "en_attente": len(en_attente), "plus_ancien": vieux, "a_signaler": signaler,
                "dernier_range": self.dernier_range or max((e.get("range_le") or "" for e in liste), default="") or None,
                "dernier_tour": self.dernier_tour}

    # ---------------------------------------------------------------- écriture
    def ajouter(self, *, cle: str, source: str, titre: str, type_nom: str | None = None, etiquettes=None,
                date: str | None = None, nom_fichier: str | None = None) -> dict:
        """Met un envoi en file. Une clé déjà connue n'est jamais remise (même rangée) : rend l'élément existant."""
        with self._verrou:
            liste = self._lire()
            for e in liste:
                if e["cle"] == cle:
                    return dict(e)
            if any(e["titre"] == titre for e in liste):
                raise ValueError("titre déjà utilisé par un autre envoi : chaque titre doit être unique")
            e = {"cle": cle, "source": source, "titre": titre, "type_nom": type_nom, "etiquettes": list(etiquettes or []),
                 "date": date, "nom_fichier": nom_fichier or f"{cle}.pdf", "etat": "attente", "document_id": None,
                 "essais": 0, "erreur": None, "cree_le": maintenant(), "parti_le": None, "parti_t": None,
                 "range_le": None, "prochain_essai": 0}
            liste.append(e)
            self._ecrire(liste)
            return dict(e)

    def abandonner(self, cle: str) -> None:
        self._modifier(cle, etat="abandon")

    def reprendre(self, cle: str) -> None:
        """Après « à vérifier » : relance la RECHERCHE du titre (jamais un renvoi)."""
        self._modifier(cle, etat="parti", parti_t=self.horloge(), prochain_essai=0, erreur=None)

    def _modifier(self, cle: str, **champs) -> dict | None:
        with self._verrou:
            liste = self._lire()
            for e in liste:
                if e["cle"] == cle:
                    e.update(champs)
                    self._ecrire(liste)
                    return dict(e)
        return None

    # ---------------------------------------------------------------- le tour
    def tour(self) -> dict:
        """Traite la file, un envoi à la fois. Rend {"ranges": n, "erreurs": n}. Ne lève jamais pour un envoi."""
        bilan = {"ranges": 0, "erreurs": 0}
        self.dernier_tour = maintenant()
        if not self.client.regle or self.client.lecture_seule:
            return bilan
        for e in self.elements():
            if e.get("etat") not in ("attente", "parti") or self.horloge() < (e.get("prochain_essai") or 0):
                continue
            try:
                if self._traiter(e):
                    bilan["ranges"] += 1
            except Exception as exc:                     # noqa: BLE001 — noté sur l'élément, réessayé plus tard
                bilan["erreurs"] += 1
                self._modifier(e["cle"], essais=(e.get("essais") or 0) + 1, erreur=str(exc)[:200],
                               prochain_essai=self.horloge() + REESSAI_S)
        return bilan

    def _ranger(self, e: dict, doc_id: int) -> bool:
        el = self._modifier(e["cle"], etat="range", document_id=int(doc_id), range_le=maintenant(), erreur=None)
        self.dernier_range = maintenant()
        if self.apres_range and el:
            try:
                self.apres_range(el)
            except Exception:                            # noqa: BLE001 — le rappel de l'appli ne bloque pas la file
                pass
        return True

    def _retrouver(self, e: dict) -> bool:
        debut = self.horloge()
        while True:
            doc = self.client.chercher_titre(e["titre"])
            if doc:
                return self._ranger(e, doc)
            if self.horloge() - debut >= ATTENTE_RETROUVER_S:
                return False
            self.dormir(INTERVALLE_RETROUVER_S)

    def _traiter(self, e: dict) -> bool:
        if e.get("etat") == "parti":
            # déjà parti : on cherche seulement ; jamais de renvoi
            doc = self.client.chercher_titre(e["titre"])
            if doc:
                return self._ranger(e, doc)
            if self.horloge() - (e.get("parti_t") or 0) > INTROUVABLE_APRES_S:
                self._modifier(e["cle"], etat="a_verifier",
                               erreur="Envoyé, mais introuvable dans Paperless : à vérifier (rien n'est renvoyé).")
            else:
                self._modifier(e["cle"], prochain_essai=self.horloge() + 60)
            return False
        # pas encore parti : le titre est-il déjà là (envoi d'une version précédente, ou posé à la main) ?
        doc = self.client.chercher_titre(e["titre"])
        if doc:
            return self._ranger(e, doc)
        if self.lire_source is None:
            raise RuntimeError("aucune source lisible")
        pdf = self.lire_source(e["source"])
        if not pdf:
            raise RuntimeError("source introuvable")
        type_id = self.client.type_document(e["type_nom"]) if e.get("type_nom") else None
        etiquettes = [i for i in (self.client.etiquette(n) for n in e.get("etiquettes") or []) if i]
        self.client.envoyer_brut(pdf, e["nom_fichier"], e["titre"], e.get("date"), type_id, etiquettes)
        self._modifier(e["cle"], etat="parti", parti_le=maintenant(), parti_t=self.horloge(),
                       essais=(e.get("essais") or 0) + 1, erreur=None)
        e = dict(e, etat="parti")
        return self._retrouver(e)


def declarer_service(services, client: Paperless, file: FileEnvois | None, *, lit: str, ecrit: str, reglage: str):
    """Fiche « Connexion » Paperless (contrat 3 de maison.py). L'essai lit une page ; le détail dit la file d'envoi."""

    def essai():
        ok, detail = client.essai()
        if file is not None:
            r = file.resume()
            morceaux = [detail] if detail else []
            if r["en_attente"]:
                morceaux.append(f"{r['en_attente']} envoi(s) en attente" + (" depuis plus de 24 h." if r["a_signaler"] else "."))
            if r["compte"].get("a_verifier"):
                morceaux.append(f"{r['compte']['a_verifier']} à vérifier.")
            detail = " ".join(morceaux) or None
        return ok, detail

    services.ajouter("paperless", "Paperless", lit=lit, ecrit=ecrit, regle=lambda: client.regle, essai=essai,
                     reglage=reglage,
                     derniere_ecriture=(lambda: file.resume()["dernier_range"]) if file is not None else None)
    return services
# empreinte: cfb35b8e5b20c10b
