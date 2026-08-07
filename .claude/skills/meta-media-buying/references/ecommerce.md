# Framework — E-commerce (DTC, Shopify, catalogue produits)

## Structure de compte

- **Compte neuf ou petit volume (< ~50 achats/semaine visés)** : une seule campagne **Advantage+ Shopping Campaign (ASC)**, ciblage automatique large, CBO, catalogue produit connecté. Ne crée pas plusieurs ad sets par catégorie de produit ou par audience tant que le volume ne le justifie pas — l'ASC est justement conçue pour gérer cette segmentation automatiquement une fois le catalogue bien structuré (product sets par catégorie si pertinent, mais dans une seule campagne).
- **Compte avec volume établi (> ~50 achats/semaine, historique de plusieurs mois)** : peut supporter une structure à deux étages :
  1. **Prospection** — Advantage+ Shopping large + éventuellement une deuxième campagne prospection classique pour tester des audiences ou créatifs spécifiques hors ASC.
  2. **Remarketing** — campagne dédiée sur audiences personnalisées (visiteurs 7/14/30j, ajouts panier, checkout initié sans achat, engageurs IG/FB), souvent avec des créations dynamiques catalogue (DPA) montrant les produits vus/abandonnés.
- Exclusion des acheteurs récents de la campagne de prospection pour ne pas payer deux fois pour un client déjà acquis, sauf stratégie de rachat/réachat volontaire (produits consommables, cross-sell).

## Type de campagne

- **Objectif "Ventes" avec Advantage+ Shopping Campaigns** par défaut pour les comptes avec catalogue — Meta optimise automatiquement placements, audience et budget entre les produits.
- Catalogue produit obligatoire et à jour (flux synchronisé, pas d'upload manuel ponctuel) — un catalogue mal synchronisé (prix/stock obsolètes) dégrade la confiance de l'algorithme et l'expérience utilisateur (produit indisponible affiché).
- Domain verification à faire en Phase 0 si ce n'est pas déjà fait — nécessaire pour la fiabilité du tracking post-iOS14 et pour certaines fonctionnalités catalogue.

## Budget & enchères

- Événement d'optimisation par défaut : **Achat**. Si le budget ne permet pas d'atteindre ~50 achats/semaine sur l'ad set principal, ne force pas cet événement — propose temporairement d'optimiser sur "Ajouter au panier" ou "Initier le paiement" pour accumuler du signal, avec un plan explicite de bascule vers "Achat" dès que le budget ou la marge le permettent. Sois transparent : optimiser sur un événement plus haut dans le funnel génère plus de volume mais un CPA d'achat réel potentiellement moins bon à court terme.
- Calcul du budget quotidien minimum : `(CPA cible × 50) / 7`. Exemple : CPA cible de 30€ → budget quotidien minimum recommandé ≈ 214€ pour espérer sortir de l'apprentissage en une semaine sur cet ad set.
- Lowest cost sans plafond en phase de lancement ; envisage un cost cap une fois 2-4 semaines de données stables disponibles, pour verrouiller la rentabilité en scaling.

## Plan de test créatif

- Formats prioritaires : vidéo courte produit en situation (UGC ou pro), image produit sur fond travaillé, carrousel multi-produits, et créations dynamiques catalogue pour le remarketing.
- 4-6 variantes minimum au lancement pour l'ASC (l'algorithme a besoin de choix à arbitrer) ; renouvellement conseillé toutes les 2-3 semaines pour un budget quotidien élevé (fatigue plus rapide), 4-6 semaines pour un budget plus modeste.
- Signal de fatigue typique en e-commerce : hausse du CPM et de la fréquence combinée à une baisse du taux de clic sur les mêmes créations depuis 10+ jours.

## KPIs & benchmarks indicatifs

- **ROAS** (attention à distinguer le ROAS rapporté par Meta et celui d'un outil tiers type Triple Whale — les fenêtres d'attribution diffèrent structurellement, ne jamais les présenter comme le même chiffre).
- **CPA / coût par achat**, **AOV** (panier moyen), **taux d'ajout au panier**, **taux de conversion checkout**, **CTR**, **CPM**.
- Ces métriques n'ont de sens qu'en comparaison avec la marge réelle du client (donnée qu'il faut lui demander, jamais supposée) — un ROAS de 3 peut être excellent ou insuffisant selon la marge produit.
