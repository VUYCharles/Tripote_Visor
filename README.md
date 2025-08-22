# Tripote Visor

Un projet parodique de **TripAdvisor en local**, pensé pour amuser vos invités.  
L’idée : transformer votre appartement en “hôtel” avec une page d’avis où vos amis peuvent poster leurs commentaires, photos et notes comme s’ils étaient sur un vrai site de voyage.

---

## Fonctionnalités

- Génération d’un **QR Code automatique** : vos invités scannent et accèdent directement à la page depuis leur smartphone.  
- Gestion d’**avis avec notes et titres automatiques** (par exemple : “Séjour exceptionnel” ou “Expérience décevante”).  
- **Upload de photos** avec stockage local.  
- **Statistiques sur les avis** : moyenne des notes, répartition par étoiles.  
- **Interface proche de TripAdvisor**, version maison : *Tripote Visor*.  

---

## Installation et lancement

### 1. Cloner le projet  
```bash
git clone https://github.com/votre-pseudo/tripote-visor.git
cd tripote-visor
```
### 2. Créer un environnement virtuel (optionnel mais recommandé)
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Linux / Mac
venv\Scripts\activate     # Sur Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Lancer le serveur
```bash
python tripote_visor_server.py
```

### 5. Scanner le qrcode
Une fois lancée, le script bug parce que tu connais mais le deuxième qrcode fonctionne, et affiche 
```bash
============================================================
Serveur Tripote Visor démarré!
URL du serveur: http://192.168.xx.xx:5000
============================================================
Scannez le QR Code ci-dessous avec votre smartphone:
```
Vos invités peuvent scanner le QR Code et accéder directement à votre faux TripAdvisor depuis leur téléphone.

---------------------------------------------------------------
### Structure du projet
```bash
tripote-visor/
│── tripote_visor_server.py   # Script principal Flask
│── reviews.json              # Avis sauvegardés (créé automatiquement)
│── static/uploads/           # Photos uploadées
│── requirements.txt          # Dépendances Python
│── README.md                 # Documentation
```
--------------------------------------------------------------
### Avertissements 
- Usage personnel uniquement
- pas affilié à TripAdvisor
- Les avis postés sont stockés en local dans reviews.json et dans static
