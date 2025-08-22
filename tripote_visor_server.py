# tripote_visor_server.py
import json
import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
import socket
import qrcode
from io import BytesIO
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'  # Nécessaire pour flash messages

# Configuration pour le téléchargement d'images
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Créer le dossier de téléchargement s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fichier pour stocker les avis
REVIEWS_FILE = 'reviews.json'

# Vérifier si le fichier est une image autorisée
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Charger les avis existants
def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r') as f:
            return json.load(f)
    return []

# Sauvegarder les avis
def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w') as f:
        json.dump(reviews, f, indent=4)

# Calculer les statistiques des avis
def calculate_stats(reviews):
    if not reviews:
        return {
            'average': 0,
            'count': 0,
            'distribution': {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }

    total = sum(review['rating'] for review in reviews)
    average = total / len(reviews)

    distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        distribution[review['rating']] += 1

    # Convertir en pourcentages
    for key in distribution:
        distribution[key] = (distribution[key] / len(reviews)) * 100

    return {
        'average': round(average, 1),
        'count': len(reviews),
        'distribution': distribution
    }

# Générer un titre en fonction de la note
def generate_review_title(rating):
    titles = {
        1: "Expérience décevante",
        2: "Séjour médiocre",
        3: "Séjour acceptable",
        4: "Bon séjour",
        5: "Séjour exceptionnel"
    }
    return titles.get(rating, "Avis sur le séjour")

# Générer le QR Code
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Obtenir l'adresse IP locale correcte
def get_local_ip():
    try:
        # Créer une socket pour se connecter à un serveur externe
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        # Fallback à l'ancienne méthode
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

# Template HTML (inchangé, sauf les parties modifiées ci-dessous)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mon Appartement Parisien - Tripote Visor</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --main-color: #34E0A1;
            --secondary-color: #FFB800;
            --dark-text: #2d2d2d;
            --light-text: #6b6b6b;
            --border-color: #e0e0e0;
            --background-light: #f8f9fa;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', BlinkMacSystemFont, -apple-system, Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }

        body {
            background-color: white;
            color: var(--dark-text);
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 15px;
        }

        /* Header */
        header {
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
        }

        .logo {
            display: flex;
            align-items: center;
            color: var(--main-color);
            font-size: 24px;
            font-weight: bold;
        }

        .logo i {
            margin-right: 10px;
            font-size: 28px;
        }

        nav ul {
            display: flex;
            list-style: none;
        }

        nav ul li {
            margin-left: 25px;
        }

        nav ul li a {
            color: var(--dark-text);
            text-decoration: none;
            font-weight: 500;
            font-size: 16px;
            transition: color 0.2s;
        }

        nav ul li a:hover {
            color: var(--main-color);
        }

        /* Hero Section */
        .hero {
            padding: 40px 0 20px;
        }

        .breadcrumb {
            font-size: 14px;
            color: var(--light-text);
            margin-bottom: 15px;
        }

        .breadcrumb a {
            color: var(--main-color);
            text-decoration: none;
        }

        .breadcrumb span {
            margin: 0 8px;
        }

        .hotel-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            color: var(--dark-text);
        }

        .hotel-info {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }

        .rating-badge {
            background-color: var(--secondary-color);
            color: white;
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 4px;
            margin-right: 15px;
            font-size: 16px;
        }

        .review-count {
            color: var(--light-text);
            font-size: 16px;
        }

        /* Photo Gallery */
        .photo-gallery {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            grid-template-rows: 200px 200px;
            gap: 8px;
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
        }

        .main-photo {
            grid-row: span 2;
            background-image: url('https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1200&q=80');
            background-size: cover;
            background-position: center;
        }

        .photo-2 {
            background-image: url('https://images.unsplash.com/photo-1584622650111-993a426fbf0a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80');
            background-size: cover;
            background-position: center;
        }

        .photo-3 {
            background-image: url('https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80');
            background-size: cover;
            background-position: center;
        }

        .photo-4 {
            background-image: url('https://images.unsplash.com/photo-1567767292278-a4f21aa2d36e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80');
            background-size: cover;
            background-position: center;
        }

        .photo-5 {
            background-image: url('https://images.unsplash.com/photo-1616594039964-ae902f0c1497?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80');
            background-size: cover;
            background-position: center;
            position: relative;
        }

        .view-all-photos {
            position: absolute;
            bottom: 15px;
            right: 15px;
            background-color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 14px;
            color: var(--dark-text);
            text-decoration: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        /* Main Content */
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }

        /* Details Section */
        .details-section {
            margin-bottom: 40px;
        }

        .section-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }

        .about-place {
            margin-bottom: 25px;
        }

        .about-place p {
            margin-bottom: 15px;
            line-height: 1.8;
        }

        .amenities {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }

        .amenity {
            display: flex;
            align-items: center;
        }

        .amenity i {
            margin-right: 10px;
            color: var(--main-color);
            width: 20px;
        }

        /* Reviews Section */
        .reviews-section {
            margin-bottom: 40px;
        }

        .review-summary {
            display: flex;
            align-items: center;
            margin-bottom: 25px;
        }

        .overall-rating {
            text-align: center;
            margin-right: 30px;
        }

        .rating-score {
            font-size: 48px;
            font-weight: 700;
            color: var(--secondary-color);
            line-height: 1;
        }

        .rating-stars {
            color: var(--secondary-color);
            margin: 5px 0;
        }

        .rating-count {
            color: var(--light-text);
            font-size: 14px;
        }

        .rating-bars {
            flex-grow: 1;
        }

        .rating-bar {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }

        .rating-bar-label {
            width: 80px;
            font-size: 14px;
            color: var(--light-text);
        }

        .rating-bar-progress {
            flex-grow: 1;
            height: 8px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin: 0 10px;
        }

        .rating-bar-fill {
            height: 100%;
            background-color: var(--secondary-color);
        }

        .rating-bar-value {
            width: 30px;
            font-size: 14px;
            color: var(--light-text);
            text-align: right;
        }

        .review {
            border-bottom: 1px solid var(--border-color);
            padding: 25px 0;
        }

        .review:last-child {
            border-bottom: none;
        }

        .review-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }

        .reviewer-info {
            display: flex;
            align-items: center;
        }

        .avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            margin-right: 15px;
            background-color: var(--main-color);
        }

        .reviewer-name {
            font-weight: 600;
            margin-bottom: 5px;
        }

        .review-location {
            font-size: 14px;
            color: var(--light-text);
        }

        .review-rating {
            color: var(--secondary-color);
            margin-bottom: 10px;
        }

        .review-title {
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 18px;
        }

        .review-content {
            margin-bottom: 15px;
            line-height: 1.6;
        }

        .review-date {
            font-size: 14px;
            color: var(--light-text);
        }

        .review-image img {
            max-width: 300px;
            margin-top: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* Review Form */
        .review-form-container {
            background-color: var(--background-light);
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 40px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px 15px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 16px;
        }

        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }

        .star-rating {
            display: flex;
            flex-direction: row-reverse;
            justify-content: flex-end;
            font-size: 28px;
        }

        .star-rating input {
            display: none;
        }

        .star-rating label {
            color: #ddd;
            cursor: pointer;
            padding: 0 2px;
        }

        .star-rating input:checked ~ label {
            color: var(--secondary-color);
        }

        .star-rating label:hover,
        .star-rating label:hover ~ label {
            color: var(--secondary-color);
        }

        button {
            background-color: var(--main-color);
            color: white;
            border: none;
            padding: 12px 25px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #2BC58F;
        }

        /* Sidebar */
        .sidebar {
            position: sticky;
            top: 90px;
        }

        .booking-card {
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .price {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .price-period {
            font-size: 16px;
            color: var(--light-text);
            font-weight: normal;
        }

        .booking-info {
            margin: 20px 0;
            padding: 15px;
            background-color: var(--background-light);
            border-radius: 4px;
        }

        .info-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .info-item:last-child {
            margin-bottom: 0;
        }

        .info-label {
            color: var(--light-text);
        }

        .info-value {
            font-weight: 500;
        }

        .booking-button {
            display: block;
            width: 100%;
            text-align: center;
            padding: 15px;
            background-color: var(--secondary-color);
            color: white;
            font-weight: 600;
            font-size: 18px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 15px;
        }

        .contact-host {
            margin-top: 20px;
            text-align: center;
        }

        .contact-host a {
            color: var(--main-color);
            text-decoration: none;
            font-weight: 500;
        }

        /* QR Code Banner */
        .qr-banner {
            background-color: var(--main-color);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-top: 30px;
        }

        .qr-banner h3 {
            margin-bottom: 15px;
        }

        .qr-code {
            display: inline-block;
            background: white;
            padding: 10px;
            border-radius: 8px;
            margin: 15px 0;
        }

        .qr-banner p {
            margin-bottom: 10px;
        }

        /* Flash Messages */
        .flash-messages {
            margin: 20px 0;
        }

        .flash-message {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-weight: 500;
        }

        .flash-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .flash-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        /* Responsive */
        @media (max-width: 992px) {
            .main-content {
                grid-template-columns: 1fr;
            }

            .photo-gallery {
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 200px 200px 200px;
            }

            .main-photo {
                grid-column: span 2;
            }

            .amenities {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                text-align: center;
            }

            nav ul {
                margin-top: 15px;
                justify-content: center;
            }

            .review-summary {
                flex-direction: column;
                align-items: flex-start;
            }

            .overall-rating {
                margin-right: 0;
                margin-bottom: 20px;
            }

            .rating-bars {
                width: 100%;
            }

            .footer-content {
                flex-direction: column;
            }

            .footer-section {
                margin-bottom: 30px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-umbrella-beach"></i>
                    <span>Tripote Visor</span>
                </div>
                <nav>
                    <ul>
                        <li><a href="#">Hôtels</a></li>
                        <li><a href="#">Vacances</a></li>
                        <li><a href="#">Restaurants</a></li>
                        <li><a href="#">Activités</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Flash Messages -->
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>

        <div class="hero">
            <div class="breadcrumb">
                <a href="#">Europe</a> <span>&gt;</span>
                <a href="#">France</a> <span>&gt;</span>
                <a href="#">Île-de-France</a> <span>&gt;</span>
                <a href="#">Paris</a> <span>&gt;</span>
                <a href="#">Hébergements Paris</a>
            </div>

            <h1 class="hotel-title">Appartement Parisien Charmant - Le Marais</h1>

            <div class="hotel-info">
                <div class="rating-badge">{{ stats.average }}</div>
                <div class="review-count">{{ stats.count }} avis</div>
            </div>

            <div class="photo-gallery">
                <div class="main-photo"></div>
                <div class="photo-2"></div>
                <div class="photo-3"></div>
                <div class="photo-4"></div>
                <div class="photo-5">
                    <a href="#" class="view-all-photos">Voir toutes les photos</a>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="left-column">
                <div class="details-section">
                    <h2 class="section-title">À propos de ce lieu</h2>
                    <div class="about-place">
                        <p>Bienvenue dans cet appartement parisien spacieux et lumineux situé en plein cœur du Marais, l'un des quartiers les plus animés et historiques de Paris. À proximité de la Place des Vosges, du Centre Pompidou et de nombreux sites emblématiques, c'est l'endroit idéal pour découvrir la ville.</p>
                        <p>Cet appartement de 75m² dispose de deux chambres, une cuisine entièrement équipée, un salon confortable avec canapé-lit et une salle de bain moderne. La connexion Wi-Fi haut débit est incluse.</p>
                        <p>Idéalement situé à moins de 5 minutes à pied de la station de métro, vous serez à 10 minutes de Notre-Dame et à 15 minutes du Louvre. De nombreux restaurants, cafés et boutiques se trouvent à proximité immédiate.</p>
                    </div>

                    <h3 class="section-title">Équipements</h3>
                    <div class="amenities">
                        <div class="amenity"><i class="fas fa-wifi"></i> Wi-Fi haute vitesse</div>
                        <div class="amenity"><i class="fas fa-tv"></i> Télévision intelligente</div>
                        <div class="amenity"><i class="fas fa-utensils"></i> Cuisine équipée</div>
                        <div class="amenity"><i class="fas fa-snowflake"></i> Climatisation</div>
                        <div class="amenity"><i class="fas fa-parking"></i> Parking à proximité</div>
                        <div class="amenity"><i class="fas fa-tshirt"></i> Lave-linge</div>
                        <div class="amenity"><i class="fas fa-soap"></i> Produits de toilette</div>
                        <div class="amenity"><i class="fas fa-concierge-bell"></i> Service de ménage</div>
                    </div>
                </div>

                <div class="reviews-section">
                    <h2 class="section-title">Avis des voyageurs</h2>

                    <div class="review-summary">
                        <div class="overall-rating">
                            <div class="rating-score">{{ stats.average }}</div>
                            <div class="rating-stars">
                                {% for i in range(5) %}
                                    {% if i < stats.average|round(0, 'floor')|int %}
                                        <i class="fas fa-star"></i>
                                    {% elif i < stats.average %}
                                        <i class="fas fa-star-half-alt"></i>
                                    {% else %}
                                        <i class="far fa-star"></i>
                                    {% endif %}
                                {% endfor %}
                            </div>
                            <div class="rating-count">{{ stats.count }} avis</div>
                        </div>

                        <div class="rating-bars">
                            <div class="rating-bar">
                                <div class="rating-bar-label">Excellent</div>
                                <div class="rating-bar-progress">
                                    <div class="rating-bar-fill" style="width: {{ stats.distribution[5] }}%;"></div>
                                </div>
                                <div class="rating-bar-value">{{ stats.distribution[5]|round(1) }}%</div>
                            </div>
                            <div class="rating-bar">
                                <div class="rating-bar-label">Très bien</div>
                                <div class="rating-bar-progress">
                                    <div class="rating-bar-fill" style="width: {{ stats.distribution[4] }}%;"></div>
                                </div>
                                <div class="rating-bar-value">{{ stats.distribution[4]|round(1) }}%</div>
                            </div>
                            <div class="rating-bar">
                                <div class="rating-bar-label">Moyen</div>
                                <div class="rating-bar-progress">
                                    <div class="rating-bar-fill" style="width: {{ stats.distribution[3] }}%;"></div>
                                </div>
                                <div class="rating-bar-value">{{ stats.distribution[3]|round(1) }}%</div>
                            </div>
                            <div class="rating-bar">
                                <div class="rating-bar-label">Médiocre</div>
                                <div class="rating-bar-progress">
                                    <div class="rating-bar-fill" style="width: {{ stats.distribution[2] }}%;"></div>
                                </div>
                                <div class="rating-bar-value">{{ stats.distribution[2]|round(1) }}%</div>
                            </div>
                            <div class="rating-bar">
                                <div class="rating-bar-label">Horrible</div>
                                <div class="rating-bar-progress">
                                    <div class="rating-bar-fill" style="width: {{ stats.distribution[1] }}%;"></div>
                                </div>
                                <div class="rating-bar-value">{{ stats.distribution[1]|round(1) }}%</div>
                            </div>
                        </div>
                    </div>

                    {% if reviews %}
                        {% for review in reviews %}
                        <div class="review">
                            <div class="review-header">
                                <div class="reviewer-info">
                                    <div class="avatar">{{ review.name[0] }}</div>
                                    <div>
                                        <div class="reviewer-name">{{ review.name }}</div>
                                        <div class="review-location">Paris, France</div>
                                    </div>
                                </div>
                                <div class="review-date">{{ review.date }}</div>
                            </div>
                            <div class="review-rating">
                                {% for i in range(5) %}
                                    {% if i < review.rating %}
                                        <i class="fas fa-star"></i>
                                    {% else %}
                                        <i class="far fa-star"></i>
                                    {% endif %}
                                {% endfor %}
                            </div>
                            <div class="review-title">{{ review.title }}</div>
                            <div class="review-content">
                                {{ review.comment }}
                            </div>
                            {% if review.image %}
                            <div class="review-image">
                                <img src="{{ review.image }}" alt="Photo du séjour">
                            </div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    {% else %}
                        <p>Soyez le premier à laisser un commentaire !</p>
                    {% endif %}
                </div>

                <div class="review-form-container">
                    <h2 class="section-title">Écrire un avis</h2>
                    <form action="/add_review" method="POST" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="name">Votre nom</label>
                            <input type="text" id="name" name="name" required>
                        </div>

                        <div class="form-group">
                            <label>Votre note</label>
                            <div class="star-rating">
                                <input type="radio" id="star5" name="rating" value="5" required>
                                <label for="star5"><i class="fas fa-star"></i></label>
                                <input type="radio" id="star4" name="rating" value="4">
                                <label for="star4"><i class="fas fa-star"></i></label>
                                <input type="radio" id="star3" name="rating" value="3">
                                <label for="star3"><i class="fas fa-star"></i></label>
                                <input type="radio" id="star2" name="rating" value="2">
                                <label for="star2"><i class="fas fa-star"></i></label>
                                <input type="radio" id="star1" name="rating" value="1">
                                <label for="star1"><i class="fas fa-star"></i></label>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="comment">Votre commentaire</label>
                            <textarea id="comment" name="comment" required></textarea>
                        </div>

                        <div class="form-group">
                            <label for="image">Ajouter une photo (optionnel)</label>
                            <input type="file" id="image" name="image" accept="image/*">
                        </div>

                        <button type="submit"><i class="fas fa-paper-plane"></i> Publier votre avis</button>
                    </form>
                </div>
            </div>

            <div class="sidebar">
                <div class="booking-card">
                    <div class="price">120€ <span class="price-period">/ nuit</span></div>

                    <div class="booking-info">
                        <div class="info-item">
                            <span class="info-label">Dates</span>
                            <span class="info-value">15 août - 20 août</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Voyageurs</span>
                            <span class="info-value">2 adultes</span>
                        </div>
                    </div>

                    <a href="#" class="booking-button">Vérifier la disponibilité</a>

                    <div class="contact-host">
                        <a href="#"><i class="fas fa-envelope"></i> Contacter le propriétaire</a>
                    </div>
                </div>

                <div class="qr-banner">
                    <h3>Scannez pour visiter</h3>
                    <div class="qr-code">
                        <img src="data:image/png;base64,{{ qr_code }}" alt="QR Code" width="150">
                    </div>
                    <p>Scannez ce code QR pour accéder à cette page</p>
                    <p><strong>{{ server_url }}</strong></p>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>À propos de Tripote Visor</h3>
                    <ul>
                        <li><a href="#">À propos de nous</a></li>
                        <li><a href="#">Press</a></li>
                        <li><a href="#">Recrutement</a></li>
                        <li><a href="#">Investisseurs</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h3>Assistance</h3>
                    <ul>
                        <li><a href="#">Centre d'aide</a></li>
                        <li><a href="#">Contact</a></li>
                        <li><a href="#">Politique de remboursement</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h3>Lieux populaires</h3>
                    <ul>
                        <li><a href="#">Hôtels Paris</a></li>
                        <li><a href="#">Hôtels Londres</a></li>
                        <li><a href="#">Hôtels New York</a></li>
                        <li><a href="#">Hôtels Rome</a></li>
                    </ul>
                </div>
            </div>

            <div class="copyright">
                <p>&copy; 2023 Tripote Visor - Tous droits réservés</p>
                <p>Ceci est une démonstration, créée pour un usage personnel</p>
            </div>
        </div>
    </footer>
</body>
</html>
"""

# Page d'accueil avec les avis
@app.route('/')
def index():
    reviews = load_reviews()
    stats = calculate_stats(reviews)

    # Obtenir l'adresse IP locale correcte
    ip_address = get_local_ip()
    port = 5000

    server_url = f"http://{ip_address}:{port}"
    qr_code_data = generate_qr_code(server_url)

    return render_template_string(HTML_TEMPLATE, reviews=reviews, stats=stats, qr_code=qr_code_data, server_url=server_url)

# Soumission d'un nouvel avis
@app.route('/add_review', methods=['POST'])
def add_review():
    name = request.form.get('name')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    image_file = request.files.get('image')

    if name and rating and comment:
        reviews = load_reviews()

        # Gérer l'image téléchargée
        image_path = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            # Ajouter un timestamp pour éviter les conflits de noms
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_path = f"/{filepath}"

        # Ajouter l'avis
        reviews.append({
            'name': name,
            'rating': int(rating),
            'comment': comment,
            'title': generate_review_title(int(rating)),
            'date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'image': image_path
        })
        save_reviews(reviews)

        flash('Votre avis a été publié avec succès!', 'success')
    else:
        flash('Veuillez remplir tous les champs obligatoires.', 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Obtenir l'adresse IP locale correcte
    ip_address = get_local_ip()
    port = 5000

    server_url = f"http://{ip_address}:{port}"

    print("=" * 60)
    print("Serveur Tripote Visor démarré!")
    print(f"URL du serveur: {server_url}")
    print("=" * 60)
    print("Scannez le QR Code ci-dessous avec votre smartphone:")

    # Afficher le QR Code dans la console
    qr = qrcode.QRCode()
    qr.add_data(server_url)
    qr.print_ascii(invert=True)

    # Démarrer le serveur
    app.run(host='0.0.0.0', port=port, debug=True)
