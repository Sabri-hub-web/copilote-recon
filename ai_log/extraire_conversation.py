"""Extrait UNE conversation de l'export officiel de Claude (conversations.json) vers ai_log/.

L'export de claude.ai (Paramètres > Confidentialité > Exporter les données) contient
TOUTES mes conversations. Ce script ne garde que celle du projet et produit :
  - ai_log/conversations/conversation_claude.json : l'export brut de cette conversation
  - ai_log/conversations/conversation_claude.md   : la même, lisible (messages + outils utilisés)
Les adresses email sont masquées, et on retire les lectures de la mémoire personnelle de
Claude ainsi que son raisonnement interne : ils parlent de ma vie hors projet (pas de données
personnelles dans le dépôt, exigence R1).

    python ai_log/extraire_conversation.py chemin/vers/conversations.json
"""
import json
import re
import sys
from pathlib import Path

TITRE = "Projet final Coding for AI"
SORTIE = Path(__file__).resolve().parent / "conversations"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def masquer(objet):
    """Remplace toutes les adresses email, partout dans l'objet (texte, listes, dicts)."""
    if isinstance(objet, str):
        return EMAIL.sub("[email masqué]", objet)
    if isinstance(objet, list):
        return [masquer(x) for x in objet]
    if isinstance(objet, dict):
        return {k: masquer(v) for k, v in objet.items()}
    return objet


def nettoyer(conv):
    """Retire les blocs 'thinking' et les appels à la mémoire personnelle (et leurs résultats)."""
    ids_memoire = {b.get("id") for m in conv["chat_messages"] for b in m.get("content") or []
                   if b.get("type") == "tool_use" and str(b.get("name", "")).startswith("mcp__memory")}
    for m in conv["chat_messages"]:
        m["content"] = [b for b in m.get("content") or []
                        if b.get("type") != "thinking"
                        and b.get("id") not in ids_memoire
                        and b.get("tool_use_id") not in ids_memoire]
    conv.pop("summary", None)
    return conv


def message_en_markdown(m):
    qui = "🧑 Moi" if m["sender"] == "human" else "🤖 Claude"
    morceaux = []
    for bloc in m.get("content") or []:
        if bloc.get("type") == "text" and bloc.get("text", "").strip():
            morceaux.append(bloc["text"].strip())
        elif bloc.get("type") == "tool_use":
            entree = bloc.get("input") or {}
            detail = entree.get("description") or entree.get("file_path") or ""
            morceaux.append(f"*[outil utilisé par Claude : {bloc.get('name')} — {detail}]*")
    for f in (m.get("files") or []) + (m.get("attachments") or []):
        nom = f.get("file_name") or f.get("name") or "fichier"
        morceaux.append(f"*[pièce jointe : {nom}]*")
    return f"### {qui} — {m.get('created_at', '')[:16].replace('T', ' ')} (UTC)\n\n" + "\n\n".join(morceaux)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    toutes = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    choisies = [c for c in toutes if c.get("name") == TITRE]
    if not choisies:
        print("Conversation introuvable. Titres présents :", [c.get("name") for c in toutes])
        sys.exit(1)
    conv = masquer(nettoyer(choisies[0]))

    SORTIE.mkdir(exist_ok=True)
    (SORTIE / "conversation_claude.json").write_text(
        json.dumps(conv, indent=1, ensure_ascii=False), encoding="utf-8")

    messages = conv["chat_messages"]
    entete = (f"# {TITRE} : export de la conversation avec Claude\n\n"
              f"Export officiel de claude.ai, {len(messages)} messages, du "
              f"{messages[0]['created_at'][:10]} au {messages[-1]['created_at'][:10]}. "
              "Emails masqués ; raisonnement interne de Claude et lectures de sa mémoire "
              "personnelle retirés. Les sorties détaillées des outils (commandes, résultats) "
              "sont dans `conversation_claude.json`.\n\n---\n\n")
    corps = "\n\n---\n\n".join(message_en_markdown(m) for m in messages)
    (SORTIE / "conversation_claude.md").write_text(entete + corps + "\n", encoding="utf-8")
    print(f"OK : {len(messages)} messages -> {SORTIE / 'conversation_claude.md'}")


if __name__ == "__main__":
    main()
