# Auditer un compte existant via le connecteur Meta Ads (Facebook)

Quand un compte publicitaire existant est mentionné, préfère toujours tirer les données réelles plutôt que de redemander au client des chiffres qu'il connaît mal ou approximativement. Le connecteur Facebook (nommé `Facebook` dans la liste des serveurs MCP) expose des dizaines de tools sous le préfixe `mcp__Facebook__ads_*`, chargés à la demande via `ToolSearch` — ne devine jamais leur schéma, charge-les d'abord.

## Étape 0 — Vérifier la disponibilité

Le connecteur peut être encore en cours de connexion en début de session. Avant de dire à l'utilisateur qu'un audit n'est pas possible, appelle `ToolSearch` (ex. `"select:mcp__Facebook__ads_get_ad_accounts"` ou une recherche par mot-clé `"facebook ads account"`) — s'il n'apparaît toujours pas après une recherche, bascule proprement sur le questionnaire déclaratif (`questionnaire.md`) sans faire perdre de temps au client.

## Étape 1 — Identifier le compte

- `ads_get_ad_accounts` — liste les comptes accessibles ; confirme avec l'utilisateur lequel auditer si plusieurs sont disponibles.
- `ads_get_ad_account_pages` / `ads_get_ig_accounts` — pages Facebook et comptes Instagram liés, utile pour vérifier que les bons actifs sont bien rattachés au compte pub.

## Étape 2 — Structure actuelle

- `ads_get_ad_entities` — récupère la structure existante (campagnes, ad sets, ads) : nombre de campagnes actives, CBO vs ABO déjà en place, niveau de fragmentation des audiences. C'est la base pour juger si le compte est sur-segmenté (trop d'ad sets pour le volume de données disponible) ou au contraire trop consolidé pour son volume.
- `ads_get_creatives` / `ads_get_creative_ads` / `ads_get_ad_images` / `ads_get_ad_videos` — inventaire créatif existant : combien de variantes actives, formats utilisés (image/vidéo/carrousel), ancienneté — sert à juger si une fatigue créative est probable avant même de regarder les métriques.

## Étape 3 — Performance & benchmarks

- `ads_insights_performance_trend` — évolution de la performance dans le temps (CPA/ROAS/CTR selon l'objectif) ; utile pour dater le début d'une éventuelle fatigue créative ou d'un problème de tracking.
- `ads_insights_industry_benchmark` / `ads_insights_auction_ranking_benchmarks` — benchmarks sectoriels pour situer le compte par rapport à sa verticale plutôt que de comparer à des chiffres génériques.
- `ads_insights_anomaly_signal` — signaux d'anomalie déjà détectés par Meta (chute soudaine, hausse de CPA) à croiser avec le phasing recommandé.
- `ads_insights_advertiser_context` / `ads_get_opportunity_score` — contexte et score d'opportunité globaux du compte, bon point de départ pour prioriser les recommandations.

## Étape 4 — Maturité du tracking

- `ads_pixel_event_read` / `ads_pixel_parameter_read` — vérifie que le Pixel est bien configuré, quels événements remontent, et si les paramètres attendus (valeur, devise, contenu) sont présents. C'est la vérification concrète à faire avant d'affirmer que le tracking est prêt.
- `ads_get_datasets` / `ads_get_dataset_details` / `ads_get_dataset_quality` / `ads_get_dataset_stats` — présence et qualité d'un dataset serveur (Conversions API). Une mauvaise qualité de dataset (faible taux de correspondance, événements manquants) doit remonter en Phase 0 du phasing, pas être découverte après le lancement.
- `ads_catalog_get_catalogs` / `ads_catalog_get_diagnostics` / `ads_catalog_get_dynamic_ads_health` — pour un compte e-commerce, vérifie que le catalogue existe, est synchronisé, et que la santé des publicités dynamiques est correcte avant de recommander des Advantage+ Shopping Campaigns.

## Étape 5 — Audiences existantes

- `ads_get_ad_account_custom_audiences` / `ads_get_custom_audience` / `ads_get_custom_audience_adsets` — audiences personnalisées déjà créées (visiteurs site, liste client, engageurs) ; sert à juger si une campagne de remarketing peut être lancée immédiatement (le pool existe déjà) ou doit attendre l'accumulation de trafic.

## Cas fréquent — client en panique ("on brûle du budget, il faut tout changer")

Quand un client arrive avec ce message, ne pars jamais du principe que la stratégie entière est à refaire — dans l'immense majorité des cas, le problème est localisé et structurel, pas un signe que le produit, l'offre ou le marché ne fonctionnent pas. Avant de proposer quoi que ce soit de nouveau, cherche spécifiquement ces quatre schémas, qui expliquent à eux seuls la plupart des "on dépense sans résultat" :

1. **Fragmentation** — plusieurs ad sets quasi identiques (même audience, créations différentes) qui se cannibalisent sur le même budget/même auction. Symptôme typique : une campagne consolidée qui performe bien à côté d'une autre coupée en 2-3 clones qui saignent chacun un peu de budget sans jamais sortir de l'apprentissage. `ads_get_opportunity_score` détecte ça directement (type `fragmentation`, avec les IDs des ad sets concernés) — ne le découvre pas à la main si l'outil peut te le dire.
2. **Ciblage mal configuré derrière un nom trompeur** — un ad set nommé "Broad"/"Large" mais dont l'audience réelle est minuscule (erreur de configuration, audience personnalisée ou lookalike oubliée). `ads_insights_anomaly_signal` remonte ça explicitement (`active_delivery_narrow_audience`) avec la taille d'audience réelle — un nom rassurant ne veut rien dire, vérifie toujours le reach réel.
3. **Budget dispersé sur trop d'ad sets en parallèle** — chacun reçoit trop peu pour atteindre le seuil de sortie d'apprentissage (~50 conversions/semaine), donc aucun ne performe jamais correctement même si le total dépensé semble suffisant. `ads_get_opportunity_score` (type `budget_limited`) le signale aussi, souvent avec le plus gros gain de score potentiel de toute la liste.
4. **Fatigue créative partielle, pas globale** — certaines publicités du pool voient leur CTR chuter fortement (`ads_insights_performance_trend`, tendance "BAD") pendant que d'autres progressent encore. Le réflexe de tout renouveler d'un coup gaspille les créations qui marchent encore ; ne coupe que celles dont la tendance est mauvaise.

Dans tous les cas, cherche activement une preuve que les fondamentaux marchent déjà ailleurs dans le même compte (une campagne ou un ad set rentable, un CTR correct, un tracking qui compte bien les ventes) avant de dire au client que "ça ne marche pas" — c'est plus honnête (on ne casse pas ce qui fonctionne) et ça change la conversation : le sujet n'est plus "faut-il une nouvelle stratégie" mais "quelle correction structurelle ciblée". Le correctif est presque toujours de la **consolidation** (fusionner les doublons, corriger le ciblage, concentrer le budget sur ce qui prouve déjà que ça marche) plutôt qu'un changement de stratégie complet — cohérent avec le principe de consolidation de `SKILL.md`.

## Ce que l'audit ne remplace pas

L'audit donne des faits sur le compte, pas le contexte business du client : budget réellement disponible (vs. dépense passée, qui peut avoir été sous-optimale), contraintes de stock/saisonnalité, capacité de production créative future, urgence du déploiement, catégorie spéciale. Ces éléments restent à demander via `questionnaire.md` même quand l'audit technique est complet.

Ne fais jamais d'action d'écriture (créer/modifier une campagne, un ad set, une audience, un événement pixel) sans confirmation explicite du client — ce skill sert à *recommander* une stratégie, pas à la déployer automatiquement dans le compte. Si le client demande explicitement d'implémenter la recommandation, traite ça comme une action à fort impact (modification d'un compte pub actif) : confirme le détail de ce qui va être créé/modifié avant d'exécuter les tools de création (`ads_create_campaign`, `ads_create_ad_set`, etc.).
