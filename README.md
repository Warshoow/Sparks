# Social Content Archiver

Une application intelligente pour archiver, analyser et synthétiser vos contenus sauvegardés depuis les réseaux sociaux, créant ainsi une base de connaissance structurée à partir de vos idées fragmentées.

## 🎯 Concept

Les réseaux sociaux comme Instagram, Facebook, LinkedIn et Beeper contiennent souvent des fragments d'idées, d'apprentissages et de valeur que nous sauvegardons mais n'exploitons jamais pleinement. Cette application :

1. **Collecte** vos posts/contenus sauvegardés depuis vos réseaux sociaux
2. **Traite** le contenu (transcription audio/vidéo, analyse visuelle, OCR)
3. **Analyse** et extrait les entités, sentiments et phrases-clés
4. **Tague** automatiquement les contenus par thème et sujet
5. **Agrège** les contenus liés par tags communs
6. **Synthétise** ces fragments en connaissances cohérentes
7. **Filtre** et vérifie la qualité des informations

## 🏗️ Architecture

```
social-content-archiver/
├── src/
│   ├── collectors/          # Collecteurs pour chaque plateforme
│   │   ├── instagram.py     # Instagram saved posts
│   │   ├── facebook.py      # Facebook saved items
│   │   ├── linkedin.py      # LinkedIn saved posts
│   │   └── beeper.py        # Beeper notes
│   │
│   ├── processors/          # Traitement du contenu
│   │   ├── transcription.py      # Whisper pour audio/vidéo
│   │   ├── visual_analysis.py    # GPT-4V + OCR
│   │   └── content_analyzer.py   # NLP, sentiment, entités
│   │
│   ├── tagging/            # Système de tagging
│   │   └── tagger.py       # Auto-tagging avec GPT
│   │
│   ├── knowledge_base/     # Base de connaissance
│   │   ├── aggregator.py   # Regroupe contenus similaires
│   │   └── synthesizer.py  # Synthétise en connaissances
│   │
│   ├── storage/            # Stockage
│   │   └── database.py     # SQLAlchemy + SQLite
│   │
│   ├── models.py           # Modèles de données
│   ├── config.py           # Configuration
│   └── main.py             # Point d'entrée principal
│
├── config/
│   └── config.yaml         # Configuration détaillée
│
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

## 🚀 Installation

### Prérequis

- Python 3.9+
- Clés API pour OpenAI (GPT-4, Whisper)
- Credentials pour les plateformes sociales

### Installation

```bash
# Cloner le repository
git clone <repo-url>
cd Sparks

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer spaCy model (pour NLP)
python -m spacy download en_core_web_sm

# Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API et credentials
```

### Configuration

Éditez `.env` avec vos informations :

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Instagram
INSTAGRAM_USERNAME=votre_username
INSTAGRAM_PASSWORD=votre_password

# Facebook
FACEBOOK_ACCESS_TOKEN=votre_token

# LinkedIn
LINKEDIN_EMAIL=votre_email
LINKEDIN_PASSWORD=votre_password

# Beeper
BEEPER_ACCESS_TOKEN=votre_token
```

Personnalisez `config/config.yaml` selon vos besoins.

## 💻 Utilisation

### Pipeline complet

Exécuter l'ensemble du processus :

```bash
python -m src.main run
```

Cela va :
1. Collecter les contenus sauvegardés
2. Les traiter (transcription, analyse)
3. Les taguer automatiquement
4. Construire la base de connaissance
5. Afficher un résumé

### Commandes individuelles

```bash
# Collecter uniquement
python -m src.main collect

# Traiter le contenu collecté
python -m src.main process

# Taguer le contenu
python -m src.main tag

# Construire la base de connaissance
python -m src.main build

# Afficher la base de connaissance actuelle
python -m src.main show
```

## 🔑 Fonctionnalités principales

### 1. Collecte multi-plateforme

- **Instagram**: Posts sauvegardés, stories, highlights
- **Facebook**: Posts sauvegardés, photos, vidéos
- **LinkedIn**: Posts et articles sauvegardés
- **Beeper**: Notes uniquement

### 2. Traitement avancé

- **Transcription**: OpenAI Whisper pour audio/vidéo
- **Analyse visuelle**: GPT-4 Vision pour comprendre les images
- **OCR**: Extraction de texte des images
- **NLP**: Entités, sentiment, phrases-clés

### 3. Tagging intelligent

- Auto-tagging avec GPT-4
- Score de confiance pour chaque tag
- Tags multisources (texte, transcription, visuel)
- Limite configurable de tags par contenu

### 4. Base de connaissance

- **Agrégation**: Regroupe contenus par tags communs
- **Clustering**: Fusion de clusters similaires
- **Synthèse**: Génère des résumés cohérents
- **Filtrage**: Vérification qualité et factualité

## 📊 Modèles de données

### Content
- ID, plateforme, type, URL
- Texte, médias, auteur
- Dates, métadonnées

### ProcessedContent
- Transcription
- Description visuelle
- Texte extrait (OCR)
- Objets détectés
- Entités, sentiment, phrases-clés

### TaggedContent
- Tags avec score de confiance
- Topic principal
- Date de tagging

### KnowledgeCluster
- Topic, tags
- IDs des contenus liés
- Résumé et synthèse
- Score de qualité

## 🛠️ Technologies utilisées

- **Python 3.9+**
- **OpenAI GPT-4** (analyse, tagging, synthèse)
- **OpenAI Whisper** (transcription)
- **spaCy** (NLP)
- **Sentence Transformers** (similarité sémantique)
- **SQLAlchemy** (ORM)
- **Instaloader** (Instagram)
- **Click** (CLI)
- **Rich** (interface terminal)

## 🎯 Cas d'usage

1. **Apprentissage personnel**: Construire une base de connaissance de vos apprentissages
2. **Veille**: Organiser et synthétiser votre veille thématique
3. **Recherche**: Retrouver et regrouper des idées similaires
4. **Content curation**: Identifier les vrais contenus de valeur
5. **Knowledge management**: Transformer des fragments en savoirs structurés

## 🔮 Roadmap

### Version actuelle (v0.1.0)
- ✅ Collecteurs de base pour 4 plateformes
- ✅ Pipeline de traitement complet
- ✅ Système de tagging automatique
- ✅ Agrégation et synthèse

### Futures améliorations
- [ ] Interface web (dashboard)
- [ ] Recherche sémantique dans la base
- [ ] Export (Notion, Obsidian, Markdown)
- [ ] Graphe de connaissances
- [ ] Notifications pour nouveaux clusters
- [ ] Support YouTube (séparé)
- [ ] API REST

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📝 Notes

### Limitations actuelles

- **LinkedIn & Beeper**: APIs non officielles, implémentation partielle
- **Rate limiting**: Respecter les limites des APIs
- **Coûts**: OpenAI GPT-4 et Whisper sont payants
- **Qualité**: Dépend de la qualité des contenus sources

### Sécurité

- Ne commitez JAMAIS vos credentials (`.env` est dans `.gitignore`)
- Utilisez des tokens avec permissions minimales
- Stockez les données sensibles de manière sécurisée

## 📄 License

MIT License - voir LICENSE file

## 🙏 Remerciements

Projet créé pour transformer les fragments d'idées éparpillés sur les réseaux sociaux en véritable base de connaissance exploitable.

---

**Note**: Cette application est destinée à un usage personnel. Respectez les conditions d'utilisation des plateformes et les lois sur la protection des données.
