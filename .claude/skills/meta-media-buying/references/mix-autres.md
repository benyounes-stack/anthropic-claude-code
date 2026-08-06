# Framework — Mix / autres (SaaS, info-produit/formation, app)

Ces comptes ne rentrent pas nettement dans e-commerce ou lead-gen local — applique les principes de base de `SKILL.md` (consolidation, Advantage+, règle des ~50 conversions/semaine, CAPI) en les adaptant à l'événement de conversion réel, qui est souvent plus loin dans le funnel qu'un simple formulaire.

## SaaS

- **Structure** : une campagne prospection large (Advantage+ audience) optimisée sur l'inscription à l'essai gratuit ou la démo réservée, plus une campagne remarketing sur les visiteurs qui n'ont pas converti (souvent le segment le plus rentable en SaaS vu le cycle de décision plus long).
- **Événement d'optimisation** : si le volume d'essais payants/démos est trop faible pour sortir de l'apprentissage, optimiser temporairement sur un événement plus haut (visite de la page pricing, début du formulaire) le temps d'accumuler du volume, avec un plan de bascule explicite une fois le seuil atteignable.
- **KPIs** : coût par essai/démo, taux d'essai → client payant (à obtenir du client pour juger la vraie rentabilité, le CPA d'essai seul ne suffit pas), CAC à mettre en regard de la LTV si le client peut la fournir.

## Info-produit / formation

- **Structure** : le funnel est souvent piloté par un événement (webinaire, masterclass) plutôt qu'un achat direct au clic — structure autour de deux temps : (1) campagne d'inscription au webinaire/lead magnet, large et Advantage+, (2) campagne de conversion vers l'offre payante sur l'audience des inscrits/participants (remarketing serré, souvent le vrai moteur de rentabilité de ce type de compte).
- **Budget** : le volume de "vente finale" est souvent trop faible pour optimiser dessus directement au démarrage — optimiser sur l'inscription en amont, suivre la conversion finale en dehors de l'optimisation Meta (CRM/plateforme webinaire) tant que le volume ne permet pas d'optimiser directement sur la vente.
- **KPIs** : coût par inscription, taux de présence au webinaire, taux de conversion présents → clients, coût d'acquisition final rapporté au prix de l'offre.

## App (installs / engagement in-app)

- **Structure** : utiliser l'objectif **App campaigns** (souvent piloté par Advantage+ App Campaigns), optimisé directement sur un événement in-app pertinent (achat, inscription, action clé) plutôt que sur l'install seule dès que le SDK/SDK de mesure (Meta SDK ou MMP type AppsFlyer/Adjust) est en place et remonte cet événement.
- **Tracking** : la fiabilité du SDK de mesure d'app est l'équivalent du Pixel/CAPI pour le web — à vérifier en Phase 0 avant tout lancement (SDK installé, événements de valeur configurés, cohérence avec le MMP si utilisé).
- **KPIs** : coût par install, coût par événement in-app clé (inscription/achat), taux de rétention à J1/J7 si disponible — l'install seule est un indicateur de vanité si elle n'est pas mise en regard de la rétention/valeur derrière.

## Principe commun à toute cette catégorie

Plus l'événement de conversion final est loin dans le funnel (vente SaaS, achat après webinaire, achat in-app après install), plus il est tentant d'optimiser Meta sur un signal amont (visite, inscription, install) faute de volume suffisant sur l'événement final. C'est un compromis acceptable en phase de lancement, mais toujours à documenter explicitement dans la recommandation (quel événement, pourquoi, quand rebasculer) — ne le laisse jamais implicite, un client qui découvre après coup qu'on optimisait sur "visite page pricing" plutôt que "client payant" sans en avoir été informé perd confiance dans le service.
