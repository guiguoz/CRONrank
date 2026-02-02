# 🏃 Challenge Raids Orientation

Application de gestion des classements pour les challenges de raids d'orientation (Trotteur, Orienteur, Raideur).

## ✨ Fonctionnalités

### Import des résultats
- Import de fichiers Excel (.xlsx) ou CSV
- Support jusqu'à 4 coéquipiers par équipe
- Détection automatique des doublons et conflits de noms
- Détection intelligente des catégories (Homme, Femme, Mixte) même dans des formats comme "TrotteurHomme"

### Gestion des données
- Création et gestion des saisons/challenges (ex: 2025-2026)
- Ajout, modification et suppression des participants
- Modification des points directement depuis le classement
- Gestion des raids (renommage, changement de date, suppression)

### Classement
- Classement dynamique par circuit et catégorie
- Calcul automatique des points selon le rang
- Export PDF par catégorie ou classement complet

### Maintenance & Qualité des données
- **Détection des coureurs invalides** : noms vides ou mal formatés avec possibilité de correction ou suppression
- **Détection des doublons** : participants inscrits plusieurs fois sur une même course
- **Détection des points aberrants** : résultats avec plus de 35 points
- Notifications automatiques quand des problèmes sont détectés

### Sauvegardes
- Sauvegarde automatique quotidienne
- Sauvegarde manuelle à la demande
- Nettoyage des sauvegardes de plus de 7 jours
- Conservation de 30 jours en automatique

### Historique
- Traçabilité complète des modifications (ajouts, modifications, suppressions)
- Détail des changements de points avec participant, course, circuit et catégorie

## 🚀 Installation

### Prérequis
- Python 3.10+

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## 💻 Utilisation

### Lancer l'application

```bash
streamlit run app.py
```

Ou double-cliquez sur `run.bat` (Windows). Le script détecte automatiquement Python et installe les dépendances si nécessaire.

L'application s'ouvre dans votre navigateur à l'adresse `http://localhost:8501`.

### Navigation

| Page | Description |
|------|-------------|
| **Import** | Importer des fichiers de résultats, créer/supprimer des challenges |
| **Édition** | Ajouter des participants, gérer les raids, maintenance des données, sauvegardes, historique |
| **Classement** | Consulter et modifier les classements, exporter en PDF, supprimer des participants |

## 📁 Structure du projet

```
├── app.py              # Application principale Streamlit
├── database.py         # Gestion de la base de données SQLite
├── utils.py            # Fonctions utilitaires (calcul points, PDF)
├── backup.py           # Système de sauvegarde automatique
├── audit.py            # Historique des modifications
├── dashboard.py        # Tableaux de bord et statistiques
├── challenge.db        # Base de données SQLite
├── requirements.txt    # Dépendances Python
├── run.bat             # Lanceur Windows
└── backups/            # Dossier des sauvegardes
```

## 🏆 Circuits

| Circuit | Description |
|---------|-------------|
| Trotteur | Niveau débutant |
| Orienteur | Niveau intermédiaire |
| Raideur | Niveau expert |

## 📊 Calcul des points

Les points sont attribués automatiquement selon le classement dans la catégorie :

| Rang | Points |
|------|--------|
| 1er | 35 pts |
| 2ème | 32 pts |
| 3ème | 30 pts |
| 4ème | 28 pts |
| 5ème | 27 pts |
| 6ème | 26 pts |
| 7ème-30ème | 31 - rang |
| 31ème+ | 1 pt |

## 🔧 Configuration

L'application utilise SQLite comme base de données locale (`challenge.db`). Aucune configuration supplémentaire n'est requise.

## 📝 Licence & Mentions Légales

### Propriété

© 2024-2026 Guillaume Lemiègre - Tous droits réservés.

### Développement

Cette application a été développée avec l'assistance d'une intelligence artificielle (Claude/Anthropic via Amp).

### Clause de non-responsabilité

CE LOGICIEL EST FOURNI "TEL QUEL", SANS GARANTIE D'AUCUNE SORTE, EXPRESSE OU IMPLICITE, Y COMPRIS, MAIS SANS S'Y LIMITER, LES GARANTIES DE QUALITÉ MARCHANDE, D'ADÉQUATION À UN USAGE PARTICULIER ET DE NON-VIOLATION.

EN AUCUN CAS L'AUTEUR OU LES CONTRIBUTEURS NE POURRONT ÊTRE TENUS RESPONSABLES DE TOUT DOMMAGE DIRECT, INDIRECT, ACCESSOIRE, SPÉCIAL, EXEMPLAIRE OU CONSÉCUTIF (Y COMPRIS, MAIS SANS S'Y LIMITER, L'ACQUISITION DE BIENS OU SERVICES DE SUBSTITUTION, LA PERTE D'UTILISATION, DE DONNÉES OU DE PROFITS, OU L'INTERRUPTION D'ACTIVITÉ) QUELLE QU'EN SOIT LA CAUSE ET SELON TOUTE THÉORIE DE RESPONSABILITÉ, QU'IL S'AGISSE D'UN CONTRAT, D'UNE RESPONSABILITÉ STRICTE OU D'UN DÉLIT (Y COMPRIS LA NÉGLIGENCE OU AUTRE) DÉCOULANT DE QUELQUE MANIÈRE QUE CE SOIT DE L'UTILISATION DE CE LOGICIEL, MÊME SI L'AUTEUR A ÉTÉ INFORMÉ DE LA POSSIBILITÉ DE TELS DOMMAGES.

### Données personnelles

Les données saisies dans cette application sont stockées localement sur votre machine. L'auteur ne collecte aucune donnée personnelle.

### Contact

Pour toute question : Guillaume Lemiègre

---

*Développé avec [Streamlit](https://streamlit.io) et l'assistance de l'IA*
