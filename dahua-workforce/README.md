# Suivi d'occupation des postes — caméras Dahua → rapport WhatsApp

Mesure l'occupation des postes de travail d'une usine à partir des caméras Dahua
déjà installées, et livre un rapport de fin de quart en PDF sur WhatsApp.

```
Caméras Dahua ──snapshot──▶ Détection de présence ──▶ SQLite ──▶ PDF brandé ──▶ WhatsApp
   (CGI/HTTP)               (par zone, en mémoire)    (métadonnées)  (custom-reports)  (Cloud API)
```

## Ce que le système fait — et ne fait pas

| | |
|---|---|
| ✅ **Mesure** | Combien de personnes se trouvent dans chaque zone de travail, échantillonné toutes les 15 s |
| ✅ **Produit** | Taux d'occupation, inoccupation cumulée, plus longue absence, première et dernière présence, par poste |
| ✅ **Alerte** | Postes restés vides au-delà d'un seuil paramétrable, postes en sous-effectif |
| ❌ **N'identifie personne** | Le détecteur répond « combien », jamais « qui ». Aucune reconnaissance faciale, aucun gabarit biométrique |
| ❌ **Ne conserve aucune image** | Les JPEG sont analysés en mémoire puis détruits. La base ne contient que `(horodatage, site, zone, nombre)` |
| ❌ **N'est pas une pointeuse** | Il ne produit pas d'heures travaillées par personne et ne peut pas servir de base de calcul de la paie |

Ce dernier point est structurel, pas une limite temporaire. Une caméra atteste
qu'*un* humain occupait un poste, pas *lequel*, ni pendant combien de temps il a
été payé pour ça. Pour un pointage nominatif opposable à un employé, l'instrument
requis est un terminal de pointage par badge (Dahua `ASA1222E-S` par exemple) —
il produit des enregistrements horodatés par identifiant employé, exploitables en
paie. Les deux systèmes sont complémentaires : ce dépôt couvre le pilotage de
production, le terminal couvre la paie.

## Conformité — Algérie (loi 18-07 et loi 25-11)

À lire **avant** la mise en service. Les choix techniques ci-dessus découlent
directement de ce cadre.

### Ce que dit le cadre applicable

- **Loi 18-07** (10 juin 2018) fonde le régime et crée l'ANPDP.
- **Loi 25-11** (24 juillet 2025) la durcit : délégué à la protection des données
  obligatoire, analyse d'impact (DPIA) **avant** le projet, journalisation des
  accès, notification d'une violation à l'ANPDP **sous 5 jours**, encadrement
  strict des transferts hors d'Algérie. Sanctions : jusqu'à 500 000 DA d'amende,
  2 à 5 ans d'emprisonnement, avec **responsabilité personnelle des dirigeants**.
- **Règles ANPDP sur la vidéosurveillance au travail** (mars 2026) : les finalités
  reconnues sont la **protection des personnes et des biens** et un
  **environnement de travail sûr et organisé**. Conservation des enregistrements
  plafonnée à **un an**. Accès limité aux personnes désignées par le responsable
  du traitement. Installation soumise à **autorisation préalable du wali**.

### Les trois points de vigilance de ce projet

**1. La finalité doit rester le pilotage de l'organisation, pas la notation individuelle.**
Le contrôle du rendement individuel par caméra ne figure pas parmi les finalités
reconnues par l'ANPDP. C'est pourquoi ce système agrège par *poste* et non par
*personne* : « le poste 3 est resté vide 35 min » relève de l'organisation du
travail ; « Karim a travaillé 6 h 12 » relève de la surveillance individuelle.
Ne recréez pas la seconde lecture en collant une feuille d'affectation nominative
sur le rapport sans base légale et sans information des salariés.

**2. La reconnaissance faciale relève des données sensibles.**
Elle exige un consentement explicite ou une autorisation préalable de l'ANPDP.
Ce dépôt ne l'implémente pas, délibérément. Si l'identification devient
nécessaire, passez par un badge : même service rendu, régime juridique bien plus
léger.

**3. WhatsApp est un transfert de données hors d'Algérie.**
Les serveurs Meta sont à l'étranger : tout contenu envoyé quitte le territoire et
tombe sous le régime des transferts transfrontaliers de la loi 25-11. Le message
sortant produit par ce système est donc **agrégé et non nominatif** — des
libellés de postes et des pourcentages, aucun nom, aucun identifiant employé.
Le réglage `whatsapp.include_employee_names` est verrouillé à `false` ; ne le
changez qu'avec une base légale documentée pour le transfert.

### Checklist avant mise en service

- [ ] Autorisation préalable du wali pour l'installation des caméras
- [ ] Analyse d'impact (DPIA) réalisée **avant** le démarrage — exigence 25-11
- [ ] Délégué à la protection des données désigné
- [ ] Registre des traitements mis à jour (finalité, durée, destinataires)
- [ ] Information écrite des salariés : dispositif, finalité, données produites, droits
- [ ] Affichage sur site signalant la vidéosurveillance
- [ ] Durée de conservation fixée et alignée sur `retention_days`
- [ ] Liste nominative des personnes habilitées à consulter les rapports
- [ ] Procédure de notification d'incident sous 5 jours documentée
- [ ] Base légale du transfert WhatsApp documentée si des données personnelles y transitent

> Cette section est une synthèse technique destinée à cadrer l'implémentation, pas
> un avis juridique. Faites valider le dossier par un conseil local avant la mise
> en production.

## Installation

### 1. Prérequis

- Une machine **sur le même réseau que les caméras** (mini-PC, NUC, serveur local).
  Aucun GPU n'est nécessaire à la cadence d'échantillonnage retenue.
- Python 3.11+, Node.js 18+ (rendu PDF), ou Docker.
- Un compte caméra **dédié, en lecture seule** — pas le compte `admin`.

### 2. Dépendances

```bash
cd dahua-workforce
pip install -e ".[detect,dev]"
```

### 3. Modèle de détection

Non embarqué dans le dépôt (poids + licence). À exporter une fois :

```bash
pip install ultralytics
yolo export model=yolov8n.pt format=onnx imgsz=640
mkdir -p models && mv yolov8n.onnx models/
```

Laisser `detector.model_path` vide fait tourner le pipeline en `NullDetector`
(occupation nulle partout) : utile pour valider la chaîne avant d'installer le modèle.

### 4. Configuration

```bash
cp config/sites.example.yaml config/sites.yaml
```

Les mots de passe et le token Meta se référencent par `${VARIABLE}` et sont
résolus depuis l'environnement — ils ne doivent jamais figurer dans le YAML.

### 5. Vérifier la liaison caméras

```bash
export CAM_LIGNE_A_PASSWORD='...'
workforce --config config/sites.yaml probe
```

```
  ✓ cam-ligne-a          192.168.1.101    IPC-HDW1230 · firmware 2.820... · snapshot 184320 o · zones: poste-01, poste-02
  ✗ cam-ligne-b          192.168.1.102    192.168.1.102: identifiants refusés (401) sur /cgi-bin/magicBox.cgi?action=getSerialNo
```

À faire avant toute calibration : ça distingue un problème réseau ou
d'identifiants d'un problème de zones mal tracées.

### 6. Calibrer les zones

Chaque poste est un polygone en coordonnées **normalisées** (0.0–1.0), ce qui le
rend indépendant de la résolution du flux.

```bash
workforce --config config/sites.yaml calibrate --camera cam-ligne-a --output calib.jpg
```

Ouvrir l'image, relever les coins de chaque poste en pixels, puis diviser :
`x = pixel_x / largeur`, `y = pixel_y / hauteur`. Reporter dans `polygon:`.
**Supprimer l'image après calibration** — c'est la seule de tout le système, et
elle n'existe que sur demande explicite.

Trois conseils de terrain :

- **Tracer au sol, pas au torse.** Une personne est affectée à une zone par le
  milieu du bord inférieur de sa boîte de détection — ses pieds. Le polygone doit
  couvrir la surface où l'opérateur se tient, pas sa silhouette.
- **Ne pas coller les polygones.** Deux zones jointives font osciller un opérateur
  entre les deux. Laisser un couloir neutre de quelques pourcents.
- **Élargir `max_idle_minutes` pour les postes mobiles.** Un contrôleur qualité
  qui circule n'est pas un poste déserté.

### 7. Lancer la collecte

```bash
workforce --config config/sites.yaml collect
```

La collecte n'a lieu que pendant les quarts déclarés (± 15 min de marge). Hors
quart, aucune image n'est demandée aux caméras.

En Docker :

```bash
cp .env.example .env    # renseigner les secrets
docker compose up -d collector
```

### 8. Rapport de fin de quart

```bash
workforce --config config/sites.yaml report                  # PDF dans out/
workforce --config config/sites.yaml report --json           # + données brutes
workforce --config config/sites.yaml report --date 2026-08-12
workforce --config config/sites.yaml send                    # PDF + envoi WhatsApp
workforce --config config/sites.yaml send --yesterday        # quart de nuit terminé le matin
```

Automatisation, en fin de quart du matin (15 h, dimanche → jeudi) :

```cron
0 15 * * 0-4  cd /opt/dahua-workforce && docker compose run --rm reporter
```

Le PDF est généré par la skill `custom-reports` du dépôt : charte TPS Digital
Services (noir `#1A1A1A`, jaune `#FFBB10`, Space Grotesk), pagination et pied de
page « Document confidentiel ». Sa règle d'honnêteté des données s'applique
intégralement — un poste sous-mesuré apparaît en encadré `note gap`, jamais avec
un chiffre présenté comme un relevé complet.

## Configurer WhatsApp Cloud API

C'est l'étape la plus longue en délai administratif ; la lancer en premier.

### 1. Côté Meta

1. Compte **Meta Business** vérifié (documents d'entreprise à fournir).
2. Application de type *Business* avec le produit **WhatsApp** ajouté.
3. **Numéro de téléphone dédié.** ⚠️ Un numéro enregistré sur la Cloud API ne
   peut plus être utilisé dans l'application WhatsApp normale. Ne pas y mettre le
   numéro personnel du responsable de production.
4. Relever le `phone_number_id` et générer un **token permanent** via un
   utilisateur système (le token de test expire en 24 h).

### 2. Déclarer le gabarit de message

Un rapport quotidien est un message à l'initiative de l'entreprise, hors de la
fenêtre de service de 24 h : seul un **template approuvé** peut être envoyé. À
créer dans WhatsApp Manager, catégorie **Utility** (pas Marketing) :

- **Nom** : `rapport_fin_de_journee`
- **Langue** : français
- **En-tête** : type `Document` (Meta demande un PDF d'exemple à la création)
- **Corps** :

  ```
  Rapport de fin de journée — {{1}}
  Date : {{2}}

  {{3}}

  Détail par poste dans le PDF joint.
  ```

Les trois variables sont alimentées dans cet ordre par `site_label`, la date ISO,
et le résumé agrégé produit par `whatsapp_summary()`. Aucune ne contient de nom.

Compter quelques jours entre la vérification du numéro et l'approbation du
gabarit. Pendant ce délai, `workforce report` produit déjà le PDF : il peut être
diffusé par un autre canal.

### 3. Renseigner la configuration

```yaml
whatsapp:
  phone_number_id: ${WHATSAPP_PHONE_NUMBER_ID}
  access_token: ${WHATSAPP_ACCESS_TOKEN}
  recipients: ["213XXXXXXXXX"]     # format international, sans « + »
  template_name: rapport_fin_de_journee
  language_code: fr
```

Facturation : depuis juillet 2025, Meta facture **par message *utility* délivré**
(tarif indexé sur l'indicatif du destinataire), sans abonnement.

## Sécurité réseau

- **Ne jamais exposer les caméras sur Internet.** Les équipements Dahua sont
  massivement scannés. Accès distant : uniquement par VPN.
- Les règles ANPDP interdisent le raccordement à Internet des systèmes de
  vidéosurveillance des structures et entreprises **publiques**. Même en
  entreprise privée, garder les caméras sur un VLAN isolé, sans route sortante.
- Compte caméra dédié, en lecture seule, distinct de `admin`.
- La seule sortie Internet nécessaire est l'appel à `graph.facebook.com` depuis la
  machine du collecteur — pas depuis les caméras.
- Sauvegarder `data/workforce.db` : il ne contient aucune image, mais sa perte
  fait perdre l'historique d'occupation.

## Architecture du code

| Fichier | Rôle |
|---|---|
| `dahua.py` | Client CGI en authentification digest : identification, snapshot, config, flux d'événements |
| `detect.py` | Détection de personnes (YOLO ONNX) et affectation aux polygones de zones |
| `collect.py` | Boucle d'échantillonnage calée sur l'horloge, active pendant les quarts uniquement |
| `store.py` | SQLite. Le schéma n'a aucune colonne où une identité pourrait se glisser |
| `report.py` | Agrégation de fin de quart. Distingue « poste vide » de « pas de mesure » |
| `render.py` | Composition HTML via la skill `custom-reports`, rendu PDF Chromium |
| `whatsapp.py` | Cloud API : téléversement du PDF puis envoi du template, avec réessais |
| `cli.py` | `probe` · `calibrate` · `collect` · `report` · `send` |

### La règle qui gouverne l'agrégation

Un trou de collecte n'est **pas** une absence au poste. Si une caméra tombe, les
échantillons manquent : ils ne sont comptés ni comme occupés ni comme vides, la
série d'inoccupation est interrompue plutôt que prolongée, et le taux de
couverture chute — ce qui déclenche un encadré « mesure partielle » dans le
rapport. Sans cette règle, une panne réseau de 30 minutes se lirait comme un poste
déserté, et le rapport deviendrait un instrument d'accusation injustifiée.

C'est le comportement le plus testé du dépôt
(`tests/test_report.py::test_data_gap_does_not_extend_an_idle_run`).

## Tests

```bash
python -m pytest tests/ -q
```

Couvrent la géométrie d'affectation (polygones concaves, chevauchements, ancrage
aux pieds), l'agrégation (trous de données, quarts de nuit, sous-effectif,
bornes de fenêtre), la persistance et la validation de configuration. Ils ne
demandent ni caméra ni modèle.

## Limites connues

- **Occlusions.** Une machine haute, un chariot, un opérateur de dos derrière un
  autre : la détection sous-estime. Un taux d'occupation de 100 % est fiable, un
  taux de 85 % peut être un vrai 95 % mal vu. Corriger par l'angle de caméra
  avant de corriger par le seuil.
- **Éclairage.** Contre-jour d'une porte de quai, passage jour/nuit infrarouge :
  la détection se dégrade. Comparer les taux entre quarts avant de conclure à un
  problème d'organisation.
- **Postes mobiles.** Un opérateur polyvalent qui tourne sur trois machines
  produira trois taux d'occupation partiels, pas une absence.
- **Pas de comptage d'heures par personne.** Voir le premier tableau de ce README.
- **Testé contre l'API CGI documentée, pas contre votre parc.** Les réponses CGI
  varient selon les gammes et les firmwares. `workforce probe` est là pour lever
  ces écarts avant la mise en service.
