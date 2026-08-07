# Questionnaire de découverte de compte

Objectif : recueillir en un minimum d'échanges tout ce qui change réellement la recommandation. Ne transforme pas ça en interrogatoire — groupe les questions par thème, saute ce que l'utilisateur a déjà donné, et utilise `AskUserQuestion` pour les champs à choix fermés (ça va plus vite pour l'utilisateur qu'une réponse libre).

Propose ces 4 blocs dans l'ordre — chaque bloc peut être une seule question groupée ou un appel `AskUserQuestion` à plusieurs questions :

## Bloc 1 — Business & objectif

- **Verticale / type de business** : e-commerce (catalogue produits) / génération de leads local ou services (ex. artisan, clinique, agence immo, avocat) / SaaS ou app / info-produit ou formation / autre.
- **Objectif principal de la pub Meta** : ventes en ligne, leads/RDV, notoriété, trafic magasin, installs d'app, inscriptions webinaire/essai. C'est ce qui détermine l'objectif de campagne Meta à choisir (voir la référence de verticale).
- **Marché(s) ciblé(s) et langue(s)** : pays/région, et si c'est un marché local (rayon autour d'un point de vente) ou national/international.

Pourquoi c'est critique : ça détermine quelle référence de verticale utiliser et le type de campagne — se tromper ici invalide toute la recommandation qui suit.

## Bloc 2 — Budget & historique

- **Budget publicitaire disponible** (mensuel ou quotidien — précise l'unité). Sert à calculer si le compte peut atteindre le seuil des ~50 conversions/semaine par ad set sur l'événement d'optimisation visé (voir `phasing-deploiement.md` et le calcul dans `SKILL.md`).
- **Compte neuf ou existant** :
  - Si neuf → pas d'historique à auditer, on part sur une structure d'amorçage large.
  - Si existant → demande (ou récupère via l'audit Meta Ads si le connecteur est disponible, voir `audit-facebook-mcp.md`) : dépense totale récente, CPA ou ROAS actuel, nombre de conversions/mois sur les 30-90 derniers jours. Un compte qui a déjà du volume peut supporter une structure plus segmentée (retargeting séparé, plusieurs audiences) sans repartir de zéro en apprentissage.
- **Délai de lancement souhaité** : "il faut lancer cette semaine" change le phasing (on compresse mais on ne saute jamais la vérification du tracking) vs "on a un mois pour bien poser les bases" (on peut faire un vrai audit créatif/catalogue avant de lancer).

## Bloc 3 — Tracking & créatif

- **Maturité du tracking** :
  - Pixel Meta installé et qui déclenche correctement ? (à vérifier via Events Manager si accès, ou via l'audit Meta Ads)
  - Conversions API (CAPI) configurée en plus du Pixel ? C'est important à souligner même si le client ne sait pas ce que c'est : depuis iOS14/ATT, le tracking navigateur seul sous-compte une partie réelle des conversions, et Meta priorise dans l'enchère les comptes avec un tracking serveur fiable. Si CAPI n'est pas en place, c'est une action Phase 0 non négociable, pas une option.
  - Catalogue produits connecté (pour e-commerce, condition pour les Advantage+ Shopping Campaigns et les publicités dynamiques) ?
- **Assets créatifs disponibles** : vidéos, photos, UGC existant, et surtout — capacité à en produire régulièrement (agence en interne, créateur externe, ou rien de prévu). Ça détermine si on peut soutenir un plan de renouvellement créatif toutes les 2-4 semaines ou s'il faut prévoir cette production comme un chantier séparé avant de scaler.

## Bloc 4 — Contraintes particulières

- **Catégorie spéciale Meta** : le compte touche-t-il au crédit, à l'emploi, au logement, ou à des enjeux sociaux/électoraux/politiques ? Ces catégories ont des restrictions de ciblage obligatoires chez Meta (pas de ciblage par âge/genre/code postal précis ni par centres d'intérêt détaillés dans certains cas) — à identifier avant de construire l'audience, pas après un rejet de publicité.
- **Saisonnalité / promotions / contraintes de stock** : y a-t-il des pics prévisibles (soldes, saison) ou des ruptures de stock à anticiper dans le phasing budgétaire ?
- **Zone de chalandise** (pour le local) : rayon pertinent autour du point de vente, plusieurs points de vente à gérer séparément ou en une seule structure ?

## Comment adapter selon les réponses

- Si le client ne connaît pas ses propres chiffres de tracking/historique et qu'un compte existant est mentionné, propose l'audit via le connecteur Meta Ads (`audit-facebook-mcp.md`) plutôt que de bloquer sur la question.
- Si l'urgence est maximale ("il faut lancer demain"), réduis le questionnaire aux champs vraiment critiques listés dans `SKILL.md` Étape 1, et signale clairement au client les hypothèses prises par défaut (ex. "je pars sur du Lowest cost sans tracking CAPI en attendant sa mise en place, à corriger dès que possible") plutôt que de retarder le lancement.
- Si plusieurs verticales se chevauchent (ex. e-commerce avec un volet B2B lead-gen), pose les questions des deux blocs verticaux concernés.
