---
name: meta-media-buying
description: Définit la stratégie de media buying et la structure de compte Meta Ads (Facebook/Instagram) à recommander pour un client — campagnes, CBO vs ABO, Advantage+, budgets, plan de test créatif, phasing de déploiement et KPIs — en fonction du contexte réel de chaque compte (verticale, budget, tracking, historique). Utilise ce skill dès que l'utilisateur parle de lancer, auditer, restructurer, ou optimiser un compte pub Meta/Facebook/Instagram, de structure de campagne, de CBO/ABO, d'Advantage+, de phase d'apprentissage, de fatigue créative, ou veut une proposition/stratégie media buying pour un client — même si la demande est formulée de façon vague ("comment on structure ce compte", "quelle stratégie pour ce client", "on lance quoi comme campagnes"). Pose TOUJOURS un questionnaire de contexte (ou audite le compte via le connecteur Meta Ads si disponible) avant de proposer une structure, afin de maximiser la rapidité et la pertinence du déploiement.
---

# Stratégie Media Buying & Structure de Compte Meta

Ce skill sert à recommander, pour un compte publicitaire Meta (Facebook/Instagram) donné, la structure de campagne, la stratégie de budget/enchères, le plan de test créatif, le phasing de déploiement et les KPIs les plus adaptés — en partant toujours du contexte réel du compte plutôt que d'un template générique. L'objectif business est double : **la qualité du service** (structure vraiment adaptée au client) et **la vitesse de déploiement** (un compte doit pouvoir être lancé ou restructuré en quelques jours, pas en plusieurs semaines d'allers-retours).

Ne saute jamais l'étape de contexte pour aller plus vite — une structure mal calibrée (trop fragmentée, mauvais objectif, tracking manquant) coûte beaucoup plus de temps à corriger après coup que les quelques minutes nécessaires pour poser les bonnes questions ou auditer le compte en amont.

## Étape 1 — Construire le contexte du compte

Deux sources possibles, à combiner plutôt qu'à opposer :

**A. Si un compte pub existant est mentionné et que le connecteur Meta Ads (Facebook) est disponible dans la session** : commence par l'auditer avant de questionner le client sur des informations que la donnée peut fournir directement (structure actuelle, dépense, statut du tracking, catalogue). Suis `references/audit-facebook-mcp.md` pour savoir quels tools chercher via ToolSearch et quoi en extraire. Utilise ensuite le questionnaire uniquement pour ce que la donnée ne peut pas révéler (budget disponible réel, contraintes business, capacité créative, urgence).

**B. Si le compte est neuf, ou si le connecteur n'est pas disponible/pas encore prêt** : repose-toi entièrement sur le questionnaire déclaratif dans `references/questionnaire.md`. Ne pose pas les 10 questions d'un bloc façon interrogatoire — groupe-les logiquement (business & objectif, puis budget & historique, puis tracking & créatif, puis contraintes & délai), et utilise l'outil `AskUserQuestion` pour les champs à choix fermés (verticale, objectif, urgence). Si l'utilisateur a déjà donné une partie du contexte dans sa demande initiale, ne redemande pas ce qu'il a déjà dit — comble seulement les trous.

Les champs vraiment critiques (ceux qui changent la recommandation, à ne jamais sauter) : **verticale/objectif**, **budget**, **compte neuf ou historique**, **maturité du tracking (Pixel/CAPI)**, **catégorie spéciale éventuelle** (crédit, emploi, logement, enjeux sociaux/politiques — ces catégories ont des restrictions de ciblage Meta obligatoires), et **délai de lancement souhaité**. Le reste peut s'affiner en cours de route.

## Étape 2 — Choisir le cadre adapté à la verticale

Les principes de base (Advantage+, consolidation, sortie de la phase d'apprentissage, CAPI) sont communs à tous les comptes — voir Étape 3. Mais chaque famille de compte a des arbitrages spécifiques : lis le fichier de référence correspondant à la verticale identifiée à l'étape 1 avant d'écrire la recommandation.

| Verticale | Référence | Spécificités clés |
|---|---|---|
| E-commerce (DTC, Shopify, catalogue produits) | `references/ecommerce.md` | Advantage+ Shopping Campaigns, catalogue/DPA, ROAS comme KPI pivot |
| Génération de leads (local/services) | `references/generation-leads.md` | Lead Ads vs formulaire site, ciblage géo/rayon, catégories spéciales fréquentes |
| Mix / autres (SaaS, info-produit, app) | `references/mix-autres.md` | Adaptation des principes de base : App campaigns, funnel d'essai/webinaire |

Un compte peut chevaucher deux familles (ex. e-commerce avec un volet lead-gen B2B) — dans ce cas, combine les deux références plutôt que d'en forcer une seule.

## Étape 3 — Construire la recommandation (gabarit commun)

Toute recommandation, quelle que soit la verticale, couvre ces 6 blocs. Les fichiers de référence par verticale détaillent les variantes ; voici la logique de décision commune.

### 1. Structure de compte
- **Par défaut, consolide plutôt que fragmente.** L'algorithme de Meta a besoin de volume de signal par ad set ; multiplier les ad sets par intérêt/audience dilue ce signal et allonge la phase d'apprentissage de chacun. La structure par défaut recommandée depuis 2024 est simple : **une campagne prospection large avec Advantage+ audience (ciblage automatique)**, éventuellement complétée d'**une campagne remarketing** (visiteurs site, ajouts panier, engageurs, liste clients) une fois qu'il y a du trafic à recibler.
- Ne construis une structure TOF/MOF/BOF plus détaillée (plusieurs campagnes par étape de funnel) que si le compte a déjà un volume de conversions suffisant pour alimenter plusieurs ad sets sans les priver de signal (voir règle des ~50 conversions/semaine ci-dessous), ou si le client a un besoin business explicite de séparer les budgets par segment (ex. reporting par marché).
- **CBO (budget au niveau de la campagne) est le réglage par défaut** — Meta répartit lui-même le budget entre ad sets selon la performance. Ne passe en ABO (budget par ad set) que si le client a un besoin de contrôle explicite (ex. garantir un minimum de budget sur un marché ou une audience spécifique indépendamment de sa performance relative), ce qui reste l'exception, pas la règle.

### 2. Type de campagne
Choisis l'objectif de campagne Meta qui correspond à l'objectif réel du client (ventes catalogue → Advantage+ Shopping ; leads → Leads Ads ou conversions site selon où vit le formulaire ; notoriété → awareness/reach ; app → App campaigns). Voir la référence de verticale pour le détail.

### 3. Budget & enchères
- Stratégie d'enchère par défaut : **coût le plus bas (lowest cost / highest volume)** sans plafond, le temps de sortir de l'apprentissage. Un plafond de coût (cost cap) ou d'enchère ne devient pertinent qu'une fois qu'on connaît le CPA/coût par résultat réel du compte, pour verrouiller la rentabilité en phase de scaling.
- **Budget minimum par ad set : vise à générer au moins ~50 conversions (de l'événement d'optimisation choisi) par semaine.** C'est le seuil informel de Meta pour qu'un ad set sorte de la phase d'apprentissage de façon fiable. Calcule le budget minimum recommandé ainsi : `budget quotidien minimum ≈ (CPA cible × 50 conversions) / 7`. Si le budget du client ne permet pas d'atteindre ce seuil sur l'événement choisi, recommande un événement d'optimisation plus haut dans le funnel (ex. "Ajouter au panier" plutôt que "Achat" pour un compte e-commerce à petit budget, ou "Lead" plutôt que "Lead qualifié" pour un compte à faible volume) le temps de monter en volume — sois transparent avec le client sur ce compromis.
- Ne touche pas à un ad set qui est encore en apprentissage (moins de 50 conversions atteintes) sauf urgence — chaque modification significative (budget, audience, créative) relance l'apprentissage. Pour scaler un ad set qui performe, augmente le budget par paliers de 15-20 % tous les 2-3 jours plutôt que par sauts brutaux qui réinitialisent l'apprentissage.

### 4. Plan de test créatif
- Démarre avec **3 à 6 variantes créatives minimum** par ad set (formats mixtes : vidéo courte, image statique, carrousel/UGC selon la verticale) — Advantage+ et l'algorithme en général performent mieux avec plusieurs variantes à arbitrer entre elles qu'avec une seule création figée.
- Utilise la création dynamique (dynamic creative) quand le volume de test le justifie, sinon un test A/B manuel simple sur 2-3 axes (accroche, format, preuve sociale) suffit pour un compte qui démarre.
- Surveille la fatigue créative via la fréquence (au-delà de 3-4 sur la fenêtre de la campagne, c'est un signal d'alerte) et l'évolution du CTR/CPA — planifie un renouvellement d'au moins une partie des créations toutes les 2 à 4 semaines selon le budget quotidien (plus le budget est élevé, plus vite les créations s'épuisent).

### 5. Phasing de déploiement
C'est le levier principal de la **rapidité de déploiement** demandée par le client — structure toujours la recommandation dans le temps, pas seulement en "quoi mettre en place". Gabarit par défaut (à adapter à l'urgence et à la maturité du compte) — détail complet dans `references/phasing-deploiement.md` :
- **Jours 0-2 — Fondations** : accès Business Manager, vérification du domaine, installation/vérification Pixel + Conversions API (CAPI), catalogue produits si e-commerce, configuration des événements prioritaires (Aggregated Event Measurement).
- **Semaine 1 — Lancement** : structure minimale (1-2 campagnes), Advantage+ large, 3-6 créations, budget calibré pour sortir de l'apprentissage en une semaine.
- **Semaines 2-3 — Apprentissage & optimisation** : on ne touche pas la structure sauf signal fort ; on surveille fréquence/CPA/volume ; on lance la campagne de remarketing dès qu'il y a assez de trafic à recibler.
- **Semaine 4+ — Scaling** : on coupe ce qui ne performe pas, on scale par paliers ce qui marche, on renouvelle les créations fatiguées, on affine le ciblage/les exclusions si pertinent.

Si le client demande un lancement plus rapide encore, compresse les phases mais ne saute jamais la vérification du tracking (Pixel/CAPI) — un lancement rapide sur un tracking cassé coûte plus cher en données perdues qu'un délai de lancement de 24-48h.

### 6. KPIs & benchmarks
Indique les KPIs pertinents pour la verticale (voir les références) avec, si possible, des ordres de grandeur indicatifs — jamais des chiffres inventés présentés comme une garantie : ce sont des repères de lecture, pas des engagements de performance.

## Étape 4 — Livrable

**Par défaut**, réponds directement dans la conversation avec la recommandation structurée en markdown, en suivant les 6 blocs ci-dessus (structure de compte → type de campagne → budget/enchères → plan créatif → phasing → KPIs). C'est le format le plus rapide pour itérer avec l'utilisateur.

**Si l'utilisateur demande explicitement un document présentable au client** (proposition, deck de lancement, document à envoyer) : génère un document formaté professionnel plutôt qu'un simple export du markdown.
- Pour un **artifact web** (proposition à partager ou consulter en ligne) : charge d'abord le skill `artifact-design`, puis construis la page en reprenant l'identité visuelle réelle de l'agence — voir `.claude/skills/custom-reports/references/brand.json` (Noir `#1A1A1A` / Jaune `#FFBB10`, police Space Grotesk) pour rester cohérent avec les autres livrables de l'agence.
- Pour un **document Word ou PDF classique**, utilise respectivement le skill `docx` ou `pdf`, avec la même charte.
- Dans les deux cas, structure le document autour des mêmes 6 blocs, mais written pour un lecteur client (moins de jargon média, plus d'explication du "pourquoi" de chaque choix) plutôt que pour un media buyer interne.

## Fichiers de référence

- `references/questionnaire.md` — le questionnaire de découverte complet, avec la justification de chaque question et comment l'adapter selon les réponses.
- `references/audit-facebook-mcp.md` — comment utiliser le connecteur Meta Ads (Facebook) via ToolSearch pour auditer un compte existant avant/au lieu de reposer certaines questions.
- `references/ecommerce.md` — framework détaillé pour les comptes e-commerce.
- `references/generation-leads.md` — framework détaillé pour la génération de leads locale/services.
- `references/mix-autres.md` — adaptation des principes de base pour SaaS, info-produit, app.
- `references/phasing-deploiement.md` — le gabarit de phasing semaine par semaine, avec variantes selon l'urgence et la maturité du compte.
