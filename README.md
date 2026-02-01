# 🏃 Challenge Raids Orientation

Application de gestion des classements pour les challenges de raids d'orientation (Trotteur, Orienteur, Raideur).

## ✨ Fonctionnalités

- **Import des résultats** : Import de fichiers Excel (.xlsx) ou CSV avec détection automatique des doublons
- **Gestion des challenges** : Création et suivi des saisons (ex: 2025-2026)
- **Classement dynamique** : Calcul automatique des points et classements par circuit et catégorie
- **Édition des données** : Modification/suppression des participants et des raids
- **Export PDF** : Génération de classements au format PDF
- **Sauvegardes automatiques** : Backup quotidien de la base de données
- **Historique des modifications** : Audit trail des changements

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

Ou double-cliquez sur `run.bat` (Windows).

L'application s'ouvre dans votre navigateur à l'adresse `http://localhost:8501`.

### Navigation

| Page | Description |
|------|-------------|
| **Import** | Importer des fichiers de résultats, créer des challenges |
| **Édition** | Ajouter/modifier des participants, gérer les raids |
| **Classement** | Consulter les classements, exporter en PDF |

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
- 1er : 35 pts
- 2ème : 32 pts
- 3ème : 30 pts
- 4ème+ : décroissant

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
