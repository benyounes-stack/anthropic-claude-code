# Phasing de déploiement

Gabarit par défaut pour un lancement "normal" (quelques jours à deux semaines de marge). Adapte la durée des phases à l'urgence exprimée par le client, mais ne saute jamais la vérification du tracking en Phase 0 — c'est la seule étape où couper les coins ronds coûte plus cher que le temps gagné : des données de conversion cassées pendant 2 semaines de lancement ne se rattrapent pas rétroactivement.

## Phase 0 — Fondations (jours 0-2)

- Accès Business Manager / compte pub confirmés (rôles corrects, pas de blocage de paiement).
- Vérification de domaine effectuée.
- Pixel Meta installé et testé (Events Manager ou audit via le connecteur, voir `audit-facebook-mcp.md`) — vérifier que les événements clés se déclenchent réellement, pas seulement que le code est présent sur le site.
- Conversions API (CAPI) configurée en complément du Pixel, avec un taux de correspondance (match quality) correct — non négociable même pour un lancement urgent ; si le délai ne permet vraiment pas de l'installer avant le lancement, le dire explicitement au client comme un risque assumé, pas un détail.
- Priorisation des événements (Aggregated Event Measurement) configurée sur les 8 événements les plus importants si le domaine n'est pas déjà vérifié pour un volume illimité d'événements.
- Catalogue produit connecté et synchronisé (e-commerce) ou SDK de mesure d'app installé (app).
- Déclaration de catégorie spéciale si applicable (crédit/emploi/logement/enjeux sociaux).

## Semaine 1 — Lancement

- Structure minimale posée : 1-2 campagnes selon la verticale (voir la référence correspondante), Advantage+ audience, CBO.
- 3-6 créations au lancement, formats mixtes.
- Budget calibré pour viser ~50 conversions/semaine sur l'ad set principal (formule : `(coût cible × 50) / 7` par jour) — si le budget du client ne l'atteint pas sur l'événement final visé, documenter explicitement le compromis pris (événement d'optimisation intermédiaire, délai de bascule prévu).
- Pas de modification structurelle une fois la campagne lancée cette semaine-là, sauf erreur de configuration évidente (rejet publicitaire, tracking cassé détecté).

## Semaines 2-3 — Apprentissage & optimisation

- On laisse l'algorithme accumuler du signal — ne pas modifier budget/audience/créative sur un ad set qui n'a pas encore atteint le seuil des ~50 conversions, sauf signal de dysfonctionnement clair (pas juste "ça pourrait aller mieux").
- Surveillance : fréquence (alerte au-delà de 3-4), évolution du CPA/CPL/ROAS, volume de conversions réel vs. seuil visé.
- Dès qu'il y a assez de trafic à recibler (visiteurs, engageurs), lancement de la campagne de remarketing.
- Premiers ajustements créatifs mineurs si un signal de fatigue apparaît déjà (rare à ce stade sauf gros budget).

## Semaine 4 et suivantes — Scaling

- Coupe ce qui ne performe clairement pas (au-delà du seuil raisonnable de patience défini en Phase 1, pas au premier jour faible).
- Scale les ad sets/campagnes qui performent par paliers de 15-20 % tous les 2-3 jours plutôt que par sauts brutaux, pour ne pas relancer l'apprentissage.
- Renouvellement d'une partie des créations selon le rythme de fatigue observé (voir la référence de verticale pour le rythme indicatif).
- Affinage du ciblage/des exclusions si des enseignements clairs émergent (ex. exclusion des acheteurs récents en e-commerce, ajustement du rayon en local).
- Point de reporting régulier avec le client sur les KPIs de la verticale (voir la référence correspondante), en présentant les vrais chiffres — jamais un objectif présenté comme atteint s'il ne l'est pas réellement.

## Compression pour un lancement urgent

Si le client a besoin de lancer en 24-48h :
- Compresse la Phase 0 au strict minimum vital (Pixel + CAPI si techniquement possible dans le délai — sinon le signaler comme risque assumé), structure Semaine 1 lancée directement.
- Ne compresse jamais le principe de ne pas toucher un ad set en apprentissage — un lancement pressé qui panique et modifie tout au bout de 2 jours parce que "ça ne convertit pas encore" est le piège le plus fréquent d'un déploiement rapide mal maîtrisé.
- Sois transparent sur les compromis pris (tracking partiel, budget sous le seuil des 50 conversions/semaine, etc.) plutôt que de présenter un lancement compressé comme équivalent à un lancement dans les règles.
