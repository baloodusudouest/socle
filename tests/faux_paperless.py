"""Faux Paperless pour les tests (socle 0.12.0), écrit d'après les FORMES relevées par la sonde du 21/11/2026
(Paperless-ngx 3.5.1, API 10). Données inventées. Copié tel quel dans les applis qui utilisent app/paperless.py.

Comportements reproduits :
  - un document envoyé par l'API appartient à son auteur ; un compte ne voit que ses documents et ceux qu'on lui ouvre ;
  - le document apparaît après un délai (« traitement ») : `delai_traitement` appels de liste ;
  - les doublons sont ACCEPTÉS (second document, relié par duplicate_documents) ;
  - filtres title__icontains, name__iexact, tags__id__all ; pagination (count/next/previous/results) ;
  - en-tête X-Version: 3.5.1 ; 401 si le jeton est inconnu ; aucune suppression permise.
Usage : faux = FauxPaperless(); faux.compte("jeton-gazette", 3); client = Paperless("http://paperless:8000",
"jeton-gazette", transport=faux.transport).
"""
from __future__ import annotations

import json
import re
import urllib.parse


class FauxPaperless:
    def __init__(self, delai_traitement: int = 1):
        self.comptes: dict[str, int] = {}
        self.documents: dict[int, dict] = {}
        self.tags: dict[int, dict] = {}
        self.types: dict[int, dict] = {}
        self.en_traitement: list[dict] = []
        self.delai_traitement = delai_traitement
        self.envois = 0
        self.panne = False                 # True : toute requête échoue (réseau)
        self._n = {"doc": 0, "tag": 0, "type": 0}

    # ---------------------------------------------------------------- préparation
    def compte(self, jeton: str, utilisateur: int) -> "FauxPaperless":
        self.comptes[jeton] = utilisateur
        return self

    def ajouter_tag(self, nom: str, proprietaire: int = 2, voir: tuple = ()) -> int:
        self._n["tag"] += 1
        self.tags[self._n["tag"]] = {"id": self._n["tag"], "name": nom, "matching_algorithm": 0,
                                     "owner": proprietaire, "voir": set(voir)}
        return self._n["tag"]

    def ajouter_document(self, titre: str, proprietaire: int = 2, voir: tuple = (), tags: tuple = (),
                         contenu: str = "texte inventé", octets: bytes = b"%PDF-1.4 faux") -> int:
        self._n["doc"] += 1
        i = self._n["doc"]
        self.documents[i] = {"id": i, "title": titre, "owner": proprietaire, "voir": set(voir), "tags": list(tags),
                             "content": contenu, "octets": octets, "created": "2026-01-01", "added": f"2026-11-21T{i:02d}",
                             "modified": f"2026-11-21T{i:02d}", "document_type": None, "duplicate_documents": []}
        return i

    def ouvrir(self, doc_id: int, utilisateur: int) -> None:
        self.documents[doc_id]["voir"].add(utilisateur)

    # ---------------------------------------------------------------- outils
    def _visible(self, doc: dict, u: int) -> bool:
        return u == 2 or doc["owner"] == u or u in doc["voir"] or doc["owner"] is None

    def _tag_visible(self, t: dict, u: int) -> bool:
        return u == 2 or t["owner"] == u or u in t["voir"] or t["owner"] is None

    def _traiter(self) -> None:
        reste = []
        for d in self.en_traitement:
            d["_attente"] -= 1
            if d["_attente"] <= 0:
                d.pop("_attente")
                memes = [o["id"] for o in self.documents.values() if o["octets"] == d["octets"]]
                self._n["doc"] += 1
                d["id"] = self._n["doc"]
                d["duplicate_documents"] = memes
                self.documents[d["id"]] = d
            else:
                reste.append(d)
        self.en_traitement = reste

    @staticmethod
    def _rep(code: int, corps=None):
        return code, {"X-Version": "3.5.1", "X-Api-Version": "10"}, (json.dumps(corps).encode() if corps is not None else b"")

    @staticmethod
    def _page(liste: list, q: dict, publics) -> dict:
        taille = int(q.get("page_size", ["25"])[0])
        page = int(q.get("page", ["1"])[0])
        morceau = liste[(page - 1) * taille: page * taille]
        return {"count": len(liste), "next": "suite" if page * taille < len(liste) else None, "previous": None,
                "results": [publics(o) for o in morceau]}

    @staticmethod
    def _doc_public(d: dict) -> dict:
        return {k: v for k, v in d.items() if k not in ("octets", "voir")}

    @staticmethod
    def _multipart(entetes: dict, donnees: bytes) -> dict:
        limite = re.search(r"boundary=(.+)", entetes["Content-Type"]).group(1).encode()
        champs: dict = {}
        for morceau in donnees.split(b"--" + limite):
            if b"Content-Disposition" not in morceau:
                continue
            tete, _, corps = morceau.partition(b"\r\n\r\n")
            nom = re.search(rb'name="([^"]+)"', tete).group(1).decode()
            corps = corps[:-2] if corps.endswith(b"\r\n") else corps
            champs.setdefault(nom, []).append(corps)
        return champs

    # ---------------------------------------------------------------- transport (même signature que transport_urllib)
    def transport(self, methode: str, url: str, entetes: dict, donnees, delai: float):
        if self.panne:
            raise OSError("faux réseau en panne")
        jeton = (entetes.get("Authorization") or "").removeprefix("Token ")
        if jeton not in self.comptes:
            return self._rep(401, {"detail": "Jeton non valide."})
        u = self.comptes[jeton]
        if "version=10" not in entetes.get("Accept", ""):
            return self._rep(406, {"detail": "version"})
        parts = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qs(parts.query)
        chemin = parts.path
        self._traiter()

        if chemin == "/api/documents/post_document/" and methode == "POST":
            c = self._multipart(entetes, donnees)
            self.envois += 1
            self.en_traitement.append({"title": c["title"][0].decode(), "owner": u, "voir": set(),
                                       "tags": [int(x) for x in c.get("tags", [])],
                                       "document_type": int(c["document_type"][0]) if "document_type" in c else None,
                                       "created": c["created"][0].decode() if "created" in c else "2026-01-01",
                                       "content": "texte lu par le faux Paperless", "octets": c["document"][0],
                                       "added": "2026-11-21T23", "modified": "2026-11-21T23",
                                       "_attente": self.delai_traitement})
            for t in [int(x) for x in c.get("tags", [])]:
                if self.tags[t]["name"] == "Impôts":                    # règle « Impôts → dime » (utilisateur 4)
                    self.en_traitement[-1]["voir"].add(4)
            return self._rep(200, "tache-" + str(self.envois))

        if chemin == "/api/documents/" and methode == "GET":
            liste = [d for d in self.documents.values() if self._visible(d, u)]
            if "title__icontains" in q:
                liste = [d for d in liste if q["title__icontains"][0].lower() in d["title"].lower()]
            if "tags__id__all" in q:
                t = int(q["tags__id__all"][0])
                liste = [d for d in liste if t in d["tags"]]
            return self._rep(200, self._page(liste, q, self._doc_public))

        m = re.fullmatch(r"/api/documents/(\d+)/(download/)?", chemin)
        if m:
            d = self.documents.get(int(m.group(1)))
            if not d or not self._visible(d, u):
                return self._rep(404, {"detail": "Pas trouvé."})
            if methode == "DELETE":
                return self._rep(403, {"detail": "Interdit."})
            if m.group(2):
                return 200, {"X-Version": "3.5.1"}, d["octets"]
            return self._rep(200, self._doc_public(d))

        for genre, table, cle in (("tags", self.tags, "tag"), ("document_types", self.types, "type")):
            if chemin == f"/api/{genre}/":
                if methode == "GET":
                    liste = [t for t in table.values() if genre == "document_types" or self._tag_visible(t, u)]
                    if "name__iexact" in q:
                        liste = [t for t in liste if t["name"].lower() == q["name__iexact"][0].lower()]
                    return self._rep(200, self._page(liste, q, lambda t: {k: v for k, v in t.items() if k != "voir"}))
                if methode == "POST":
                    corps = json.loads(donnees)
                    self._n[cle] += 1
                    table[self._n[cle]] = {"id": self._n[cle], "name": corps["name"],
                                           "matching_algorithm": corps.get("matching_algorithm", 6),
                                           "owner": u, "voir": set()}
                    return self._rep(201, {k: v for k, v in table[self._n[cle]].items() if k != "voir"})
        return self._rep(404, {"detail": "Pas trouvé."})
