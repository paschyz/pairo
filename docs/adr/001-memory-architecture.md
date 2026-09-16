# ADR 001 — Architecture de la mémoire Pairo

**Statut :** Accepté
**Date :** 2026-09-16

## Contexte

Les utilisateurs de reviewers IA se plaignent de trois problèmes :
- Le bot re-suggère ce qui a été explicitement rejeté
- Chaque push génère des commentaires sur du code inchangé
- Relancer sans changement donne des résultats différents

## Décisions

### 1. Empreinte basée sur le contenu, pas sur les numéros de ligne

Les numéros de ligne changent à chaque push. L'empreinte utilise le code normalisé (whitespace-insensitive, blank-line-tolerant) + axe + catégorie + chemin. Un déplacement de code sans modification garde la même empreinte.

**Alternative rejetée :** empreinte par numéro de ligne — trop fragile, invalide à chaque rebase.

### 2. Signaux déterministes prioritaires sur l'interprétation LLM

Ordre de priorité :
1. Commandes explicites (`@pairo ignore/valid`)
2. Réactions (thumbs-down)
3. Fil résolu sans changement de code
4. Classification LLM des réponses libres (optionnel, désactivé par défaut)

Les trois premiers signaux sont gratuits, déterministes, et ne consomment pas de quota. Le LLM n'intervient que pour les cas ambigus, et uniquement si activé.

**Alternative rejetée :** tout classifier par LLM — coûteux, non déterministe, résultats imprévisibles.

### 3. Mémoire visible : marqueurs + config versionnée

Chaque commentaire contient un marqueur HTML invisible avec l'empreinte. Si la base est perdue, les décisions se reconstruisent depuis GitHub. Les règles persistantes passent par `.pairo.yml` (versionné, visible, humain décide).

**Alternative rejetée :** apprentissage automatique de règles repo-wide — opaque, non réversible, pas de contrôle humain.

### 4. Cache déterministe par versionnement des prompts

La clé de cache inclut `PROMPT_VERSION`, le nom du modèle, et la config. Tout changement invalide naturellement le cache. TTL configurable en sécurité supplémentaire.

**Alternative rejetée :** cache par hash du prompt complet — fragile aux reformulations mineures qui ne changent pas la sémantique.

## Conséquences

- Les rejets sont immédiats et gratuits (pas d'appel LLM)
- Le cache réduit les appels LLM sur les re-reviews
- La mémoire est transparente et contrôlable
- Pas de magie : l'humain garde le contrôle via commandes et `.pairo.yml`
