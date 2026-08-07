# Framework — Génération de leads (local & services)

Couvre les commerces/services locaux (artisans, cliniques, agences immobilières, avocats, restaurants) et les services à vente plus longue (B2B services, consulting) vendus via un formulaire ou un appel plutôt qu'un panier e-commerce.

## Structure de compte

- **Démarrage** : une seule campagne de génération de leads, ciblage large (Advantage+ audience) sur la zone de chalandise pertinente, CBO, un seul ad set tant que le volume de leads/semaine est faible. Ne segmente pas par quartier/rayon ou par service dès le départ — ça fragmente un volume déjà limité.
- **Volume établi** : on peut séparer par service/offre si chacun a assez de volume propre pour sortir de l'apprentissage indépendamment (règle des ~50 conversions/semaine), sinon garder une seule campagne consolidée et laisser le reporting distinguer les performances par créative/annonce plutôt que par structure de campagne.
- Une campagne de remarketing (visiteurs page de destination sans soumission, engageurs) devient pertinente dès qu'il y a un trafic suffisant à recibler — souvent plus tôt en local que sur un funnel e-commerce, car le volume de trafic nécessaire est plus faible.

## Type de campagne

- **Lead Ads (formulaire natif Meta)** vs **campagne de conversion vers une landing page** : le formulaire natif réduit la friction (pas de chargement de page, pré-rempli) et convient bien à un besoin de volume/vitesse, mais donne des leads en moyenne moins qualifiés qu'un formulaire sur site avec plus de friction et de contexte. Pose la question au client : priorité au volume ou à la qualité/pré-qualification ? Recommande le Lead Ads en phase de lancement rapide (moins de friction technique, pas de dépendance à une landing page performante), avec bascule vers un formulaire site dès que le pipeline de qualification est en place.
- Pour un besoin d'appel plutôt que de formulaire (ex. plombier, restaurant), envisage l'extension d'appel ou l'objectif orienté "appels" si le volume le justifie.
- **Ciblage géographique** : rayon autour du point de vente ou de la zone d'intervention — vérifier la zone de chalandise réelle donnée par le client (Bloc 4 du questionnaire) plutôt que de deviner un rayon par défaut.

## Budget & enchères

- Événement d'optimisation par défaut : **Lead** (soumission de formulaire). Si le volume de leads est trop faible pour atteindre ~50/semaine avec le budget disponible, il vaut souvent mieux élargir la zone géographique ou l'audience que de changer d'événement d'optimisation (contrairement à l'e-commerce, il n'y a généralement pas d'événement intermédiaire aussi pertinent qu'"ajouter au panier").
- Calcul du budget quotidien minimum : `(coût par lead cible × 50) / 7`. Exemple : CPL cible de 15€ → budget quotidien minimum recommandé ≈ 107€.
- Attention à la **qualité des leads**, pas seulement au volume : si le client dispose d'un CRM ou remonte les leads qualifiés/RDV pris via Conversions API ou Conversions personnalisées (`ads_get_customconversions`), optimiser sur cet événement en aval (lead qualifié plutôt que simple soumission) donne de meilleurs résultats business dès que le volume le permet — à activer en Phase 3 (scaling) plutôt qu'au lancement si le volume ne le supporte pas encore.

## Plan de test créatif

- Formats prioritaires : témoignage/UGC, avant-après (si visuel, ex. artisan/beauté), offre claire avec accroche locale ("proche de chez vous"), vidéo courte présentant le service ou l'équipe (la confiance compte plus qu'en e-commerce pur).
- 3-5 variantes suffisent souvent en local vu les volumes plus faibles ; le renouvellement peut être plus lent (4-6 semaines) car la fréquence monte moins vite avec un budget local modeste — mais reste à surveiller pareil.

## Contraintes fréquentes en local — catégories spéciales

Beaucoup de comptes de génération de leads locaux touchent aux **catégories spéciales Meta** (crédit, emploi, logement) — ex. agence immobilière, recrutement, courtage. Si c'est le cas :
- Le ciblage détaillé par centres d'intérêt, âge précis, genre et rayon fin est restreint ou interdit selon la catégorie — vérifie ce point en Bloc 4 du questionnaire avant de construire l'audience, pas après un rejet publicitaire.
- Prévoir ce point dans le phasing (Phase 0) : la déclaration de catégorie spéciale se fait au niveau de la campagne et conditionne les options disponibles ensuite.

## KPIs & benchmarks indicatifs

- **Coût par lead (CPL)**, **taux de complétion du formulaire**, **coût par lead qualifié / RDV pris** (si remonté), **taux de leads qualifiés / total leads**, **CTR**.
- Le coût par lead brut seul est un indicateur incomplet — pousse toujours le client à remonter au moins la qualification (qualifié/non qualifié, ou converti en client) pour juger la vraie rentabilité, sans quoi la campagne "la moins chère au lead" peut être la moins rentable en réalité.
