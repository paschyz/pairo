# `.pairo.md` — Pairo propose une règle par PR (lot 1 : écriture)

## Objectif

Quand un utilisateur de confiance répond `@pairo ignore <raison>` à un commentaire
de Pairo, le LLM décide si la raison est une **règle durable du projet** (ex. « on
n'utilise pas cette stack »). Si oui et que la confiance dépasse le seuil, Pairo
ouvre (ou complète) une PR qui ajoute la règle à `.pairo.md` à la racine du repo.

**Hors périmètre (lot 2) :** lecture de `.pairo.md` et injection dans le prompt de
review. Ce lot ne change pas le comportement des reviews.

## Déclencheur

Le flux existant `@pairo ignore` (`api/webhook.py::_handle_comment`) enregistre déjà
le rejet et répond dans le fil. On lui ajoute, **après** ce traitement, la
proposition de règle. Aucun nouvel événement GitHub n'est nécessaire.

Conditions (toutes requises) :

1. `cmd.action == "ignore"` et `cmd.reason` non vide.
2. `comment.author_association` ∈ `OWNER`, `MEMBER`, `COLLABORATOR`.
3. `.pairo.yml` n'a pas `context.propose_rules: false` (défaut : `true`).

## Composants (hexagonal)

| Couche | Élément | Rôle |
|---|---|---|
| domain | `context_rule.py` | `RuleProposal(persist, confidence, rule)`, `is_trusted(assoc)`, `accept(proposal, threshold)`, `merge_rule(existing_md, rule)` |
| domain | `ports.py` | `RuleClassifier.classify(reason, finding_text, file) -> RuleProposal` ; `CodeHost.propose_file_change(...) -> str` (URL de la PR) |
| domain | `repo_config.py` | champ `context_propose_rules: bool = True` |
| application | `propose_context_rule.py` | orchestre : classify → accept → lire `.pairo.md` → merge → propose_file_change → répondre dans le fil |
| infrastructure | `llm/litellm_reviewer.py` (ou module voisin) + `llm/fake.py` | implémentations de `RuleClassifier` |
| infrastructure | `github/client.py` | `propose_file_change` : branche `pairo/context` (créée depuis la branche par défaut si absente), commit de `.pairo.md`, PR ouverte si aucune PR ouverte sur cette branche |
| config | `settings.context_rule_threshold: float = 0.7` | seuil de confiance |

### Règles du domaine

- `merge_rule` ajoute `- <rule>` sous un en-tête `# Pairo context` (créé si le fichier
  n'existe pas). Retourne `None` si la règle est déjà présente (comparaison
  normalisée : casse et espaces) ou si le fichier dépasserait `MAX_FILE_CHARS = 8000`.
- `rule` est plafonnée à `MAX_RULE_CHARS = 280`, une seule ligne (retours à la ligne
  remplacés par des espaces).
- `accept` = `persist and confidence >= threshold and rule non vide`.

### Sécurité

- Le commentaire et le texte du finding sont des **données non fiables** dans le
  prompt du classifieur. La sortie est strictement structurée et validée (Pydantic).
  Toute sortie invalide = `persist=False`.
- Lecture de `.pairo.md` depuis `pairo/context` si la branche existe (pour ne pas écraser
  une règle déjà proposée dans une PR ouverte), sinon depuis la **branche par défaut**.
  Jamais depuis la branche d'une PR utilisateur.
- Jamais de push sur la branche par défaut. L'humain relit et merge.
- Permissions GitHub App à ajouter : `contents:write`, `pull_requests:write`.
  Les installations existantes devront les réaccepter. Sans ces permissions,
  `propose_file_change` échoue (403) : erreur loguée, le rejet du finding reste acquis.

### Réponse dans le fil

- PR créée ou mise à jour : « Règle proposée dans `.pairo.md` : <url> ».
- Règle non retenue (confiance trop basse ou `persist=False`) : aucune réponse
  supplémentaire, pour ne pas bruiter. Le rejet est déjà confirmé par le message existant.
- Doublon ou fichier plein : « Not added to `.pairo.md`: the rule is already there or the file is full. »

## Flux d'erreur

Toute exception dans la proposition est loguée (`logger.exception`) et n'affecte pas
le rejet déjà enregistré. Même schéma que `_handle_comment`.

## Tests (TDD, à écrire avant l'implémentation)

**`tests/domain/test_context_rule.py`**
- `is_trusted` : OWNER/MEMBER/COLLABORATOR vrai ; CONTRIBUTOR, NONE, FIRST_TIMER faux.
- `accept` : refuse `persist=False`, refuse sous le seuil, accepte au seuil exact, refuse règle vide.
- `merge_rule` : crée le fichier avec en-tête si `None` ; ajoute en fin de liste ;
  `None` sur doublon (casse/espaces ignorés) ; `None` si dépassement de `MAX_FILE_CHARS` ;
  règle multi-lignes aplatie ; règle tronquée à `MAX_RULE_CHARS`.

**`tests/domain/test_repo_config.py`** (ajout)
- `context.propose_rules` absent → `True` ; `false` → `False`.

**`tests/test_propose_context_rule.py`** (fakes en mémoire, même convention que `test_review_use_case.py`)
- règle durable au-dessus du seuil → `propose_file_change` appelé avec le contenu fusionné, réponse avec l'URL.
- sous le seuil → aucun appel à `propose_file_change`, aucune réponse.
- `.pairo.md` existant → la règle est ajoutée au contenu existant.
- `pairo/context` existe déjà avec une règle → la nouvelle règle s'ajoute à ce contenu (la 1re n'est pas écrasée).
- `.pairo.yml` avec `context.propose_rules: false` → classifieur non appelé, aucune réponse (la config est lue par le use case).
- doublon → aucun appel, réponse « déjà dans `.pairo.md` ».
- `propose_file_change` lève → le use case laisse l'exception remonter (c'est le webhook qui la logue).
- le classifieur reçoit raison, texte du finding et fichier.

**`tests/infrastructure/test_github_propose_file_change.py`** (respx)
- branche absente : lecture de la branche par défaut, création de `refs/heads/pairo/context`, PUT du contenu, POST de la PR, retourne l'URL.
- branche existante + PR ouverte : PUT du contenu sur la branche, aucun POST de PR, retourne l'URL de la PR existante.
- fichier déjà présent sur la branche : le PUT inclut le `sha` courant.
- 403 → exception.

**`tests/infrastructure/test_rule_classifier.py`**
- sortie JSON valide → `RuleProposal` correct.
- sortie invalide / hors schéma → `persist=False`.
- le commentaire n'est pas interprété comme instruction (le prompt l'encadre comme donnée).
- fake : règle déterministe selon un mot-clé, pour les tests e2e.

**`tests/test_comment_webhook.py`** (ajouts)
- `@pairo ignore <raison>` par un `COLLABORATOR` → le use case est appelé (mock) après l'enregistrement du rejet.
- même commentaire par `NONE`/`CONTRIBUTOR` → rejet enregistré, use case non appelé.
- `@pairo ignore` sans raison → use case non appelé.
- échec du use case → le rejet reste enregistré et la réponse « Noted » est envoyée.

## Décisions ouvertes

Aucune. Hypothèses actées : seuil 0.7 configurable par env, branche fixe
`pairo/context`, interrupteur par repo via `.pairo.yml`.
