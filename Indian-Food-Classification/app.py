import os
import sqlite3
import uuid
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template, jsonify, g, url_for
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Enhanced Configuration
app.config.update({
    'UPLOAD_FOLDER': 'static/uploads',
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'webp'},
    'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,  # 5MB
    'DATABASE': 'nutrition.db',
    'DAILY_LIMITS': {
        'calories': 2000,
        'sodium': 2300,      # mg
        'protein': 50,       # g
        'carbs': 300,        # g
        'fat': 70,           # g
        'fiber': 25          # g
    },
    'NUTRIENT_UNITS': {
        'calories': 'kcal',
        'sodium': 'mg',
        'protein': 'g',
        'carbs': 'g',
        'fat': 'g',
        'fiber': 'g'
    }
})

# Database Setup
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with app.app_context():
        db = get_db()
        try:
            # Enhanced user profile table
            db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT DEFAULT '',
                    age INTEGER DEFAULT 25,
                    gender TEXT DEFAULT 'other',
                    weight REAL DEFAULT 70.0,       -- kg
                    height REAL DEFAULT 170.0,      -- cm
                    goal TEXT NOT NULL DEFAULT 'maintain',
                    activity_level TEXT DEFAULT 'moderate',
                    allergies TEXT DEFAULT '',
                    conditions TEXT DEFAULT '',
                    dietary_preferences TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enhanced meals table with more nutritional data
            db.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_name TEXT NOT NULL,
                    calories REAL NOT NULL,
                    sodium REAL NOT NULL,
                    protein REAL NOT NULL,
                    carbs REAL NOT NULL,
                    fat REAL NOT NULL,
                    fiber REAL NOT NULL,
                    sugar REAL DEFAULT 0,
                    cholesterol REAL DEFAULT 0,
                    potassium REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    image_url TEXT DEFAULT ''
                )
            ''')
            
            # Create default user if not exists
            db.execute('''
                INSERT OR IGNORE INTO users 
                (id, name, goal) 
                VALUES (1, 'User', 'maintain')
            ''')
            
            db.commit()
        except Exception as e:
            app.logger.error(f"Database initialization failed: {str(e)}")
            db.rollback()
            raise e  # Re-raise the exception to see it in the console

init_db()

# Load ML model
try:
    model = load_model("model_inceptionV3.h5")
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Model loading failed: {str(e)}")
    model = None

# Enhanced Food Database with complete nutritional profiles
# ... (previous imports and configuration remain the same until FOOD_CLASSES)

# Complete Food Database with Full Nutritional Profiles
FOOD_CLASSES = {
    0: {
        "name": "Burger",
        "emoji": "🍔",
        "calories": 354,
        "protein": 16,
        "carbs": 29,
        "fat": 19,
        "fiber": 2,
        "sodium": 500,
        "sugar": 5,
        "cholesterol": 45,
        "potassium": 250,
        "rating": 2,
        "health_tips": [
            "High in saturated fats - consider leaner protein options",
            "Opt for whole grain buns to increase fiber content",
            "Add veggies like lettuce and tomato for micronutrients"
        ],
        "tags": ["fast-food", "high-fat", "high-sodium", "meat"]
    },
    1: {
        "name": "Butter Naan",
        "emoji": "🫓",
        "calories": 320,
        "protein": 9,
        "carbs": 46,
        "fat": 12,
        "fiber": 2,
        "sodium": 380,
        "sugar": 3,
        "cholesterol": 30,
        "potassium": 120,
        "rating": 3,
        "health_tips": [
            "High in refined carbs - pair with protein-rich dishes",
            "Contains butter - consider lighter versions",
            "Portion control recommended"
        ],
        "tags": ["bread", "high-carb", "vegetarian"]
    },
    2: {
        "name": "Chai",
        "emoji": "☕",
        "calories": 120,
        "protein": 4,
        "carbs": 18,
        "fat": 4,
        "fiber": 0,
        "sodium": 50,
        "sugar": 15,
        "cholesterol": 10,
        "potassium": 180,
        "rating": 4,
        "health_tips": [
            "Contains antioxidants - benefits heart health",
            "High sugar content - reduce sugar amount",
            "Use low-fat milk for healthier version"
        ],
        "tags": ["beverage", "dairy", "vegetarian"]
    },
    3: {
        "name": "Chapati",
        "emoji": "🥖",
        "calories": 104,
        "protein": 3,
        "carbs": 20,
        "fat": 2,
        "fiber": 3,
        "sodium": 190,
        "sugar": 1,
        "cholesterol": 0,
        "potassium": 140,
        "rating": 4,
        "health_tips": [
            "Good source of fiber - aids digestion",
            "Made from whole wheat - complex carbs",
            "Low fat content - healthy choice"
        ],
        "tags": ["bread", "whole-grain", "vegetarian", "vegan"]
    },
    4: {
        "name": "Chole Bhature",
        "emoji": "🥘",
        "calories": 430,
        "protein": 15,
        "carbs": 60,
        "fat": 16,
        "fiber": 8,
        "sodium": 620,
        "sugar": 5,
        "cholesterol": 0,
        "potassium": 480,
        "rating": 3,
        "health_tips": [
            "Chickpeas provide plant-based protein",
            "Fried bhature increases fat content",
            "High fiber content aids digestion"
        ],
        "tags": ["fried", "vegetarian", "high-protein"]
    },
    5: {
        "name": "Dal Makhani",
        "emoji": "🍛",
        "calories": 350,
        "protein": 18,
        "carbs": 40,
        "fat": 14,
        "fiber": 12,
        "sodium": 480,
        "sugar": 4,
        "cholesterol": 35,
        "potassium": 600,
        "rating": 4,
        "health_tips": [
            "Excellent source of plant protein",
            "High in fiber - promotes gut health",
            "Reduce cream for lighter version"
        ],
        "tags": ["vegetarian", "high-protein", "legumes"]
    },
    6: {
        "name": "Dhokla",
        "emoji": "🍲",
        "calories": 160,
        "protein": 8,
        "carbs": 26,
        "fat": 3,
        "fiber": 3,
        "sodium": 420,
        "sugar": 2,
        "cholesterol": 0,
        "potassium": 280,
        "rating": 4,
        "health_tips": [
            "Steamed preparation - low fat content",
            "Fermented food - good for gut health",
            "Watch portion size due to sodium content"
        ],
        "tags": ["steamed", "vegetarian", "vegan", "fermented"]
    },
    7: {
        "name": "Fried Rice",
        "emoji": "🍚",
        "calories": 380,
        "protein": 12,
        "carbs": 58,
        "fat": 12,
        "fiber": 3,
        "sodium": 540,
        "sugar": 3,
        "cholesterol": 85,
        "potassium": 220,
        "rating": 3,
        "health_tips": [
            "Add more vegetables for nutrients",
            "Use brown rice for better nutrition",
            "Control oil quantity when cooking"
        ],
        "tags": ["rice", "high-carb", "vegetable"]
    },
    8: {
        "name": "Idli",
        "emoji": "🍥",
        "calories": 110,
        "protein": 4,
        "carbs": 22,
        "fat": 1,
        "fiber": 2,
        "sodium": 290,
        "sugar": 1,
        "cholesterol": 0,
        "potassium": 150,
        "rating": 5,
        "health_tips": [
            "Low calorie - good for weight management",
            "Fermented - easier to digest",
            "Pair with sambar for complete protein"
        ],
        "tags": ["steamed", "vegetarian", "vegan", "fermented"]
    },
    9: {
        "name": "Jalebi",
        "emoji": "🥨",
        "calories": 320,
        "protein": 2,
        "carbs": 75,
        "fat": 5,
        "fiber": 1,
        "sodium": 30,
        "sugar": 65,
        "cholesterol": 0,
        "potassium": 50,
        "rating": 1,
        "health_tips": [
            "Very high in sugar - consume occasionally",
            "Deep fried - high calorie density",
            "Avoid on empty stomach"
        ],
        "tags": ["sweet", "fried", "vegetarian", "high-sugar"]
    },
    10: {
        "name": "Kaathi Rolls",
        "emoji": "🌯",
        "calories": 340,
        "protein": 18,
        "carbs": 32,
        "fat": 15,
        "fiber": 3,
        "sodium": 680,
        "sugar": 4,
        "cholesterol": 95,
        "potassium": 380,
        "rating": 3,
        "health_tips": [
            "Choose grilled over fried fillings",
            "Load up on vegetable fillings",
            "Watch portion size of wraps"
        ],
        "tags": ["street-food", "high-protein", "meat"]
    },
    11: {
        "name": "Kadai Paneer",
        "emoji": "🧆",
        "calories": 380,
        "protein": 22,
        "carbs": 18,
        "fat": 26,
        "fiber": 4,
        "sodium": 520,
        "sugar": 6,
        "cholesterol": 75,
        "potassium": 420,
        "rating": 3,
        "health_tips": [
            "Good source of vegetarian protein",
            "High in saturated fat - control portions",
            "Pair with whole grain roti for balance"
        ],
        "tags": ["vegetarian", "paneer", "high-fat"]
    },
    12: {
        "name": "Kulfi",
        "emoji": "🍦",
        "calories": 280,
        "protein": 6,
        "carbs": 32,
        "fat": 15,
        "fiber": 0,
        "sodium": 80,
        "sugar": 28,
        "cholesterol": 55,
        "potassium": 220,
        "rating": 2,
        "health_tips": [
            "High sugar content - occasional treat",
            "Contains calcium - benefits bones",
            "Try fruit-based versions for healthier option"
        ],
        "tags": ["dessert", "dairy", "high-sugar"]
    },
    13: {
        "name": "Masala Dosa",
        "emoji": "🥘",
        "calories": 320,
        "protein": 8,
        "carbs": 48,
        "fat": 10,
        "fiber": 5,
        "sodium": 580,
        "sugar": 3,
        "cholesterol": 0,
        "potassium": 320,
        "rating": 4,
        "health_tips": [
            "Fermented batter aids digestion",
            "Potato filling is carb-heavy",
            "Opt for less oil in preparation"
        ],
        "tags": ["fermented", "vegetarian", "vegan"]
    },
    14: {
        "name": "Momos",
        "emoji": "🥟",
        "calories": 180,
        "protein": 9,
        "carbs": 24,
        "fat": 5,
        "fiber": 2,
        "sodium": 420,
        "sugar": 2,
        "cholesterol": 35,
        "potassium": 180,
        "rating": 4,
        "health_tips": [
            "Steamed version is healthier than fried",
            "Good protein option for snacks",
            "Watch the sodium in dipping sauces"
        ],
        "tags": ["steamed", "dumplings", "high-protein"]
    },
    15: {
        "name": "Paani Puri",
        "emoji": "🧆",
        "calories": 120,
        "protein": 2,
        "carbs": 22,
        "fat": 3,
        "fiber": 2,
        "sodium": 380,
        "sugar": 4,
        "cholesterol": 0,
        "potassium": 120,
        "rating": 3,
        "health_tips": [
            "Small portions help control calories",
            "Water quality matters for food safety",
            "High in refined carbs - enjoy in moderation"
        ],
        "tags": ["street-food", "vegetarian", "snack"]
    },
    16: {
        "name": "Pakode",
        "emoji": "🍤",
        "calories": 280,
        "protein": 6,
        "carbs": 26,
        "fat": 16,
        "fiber": 3,
        "sodium": 450,
        "sugar": 2,
        "cholesterol": 0,
        "potassium": 220,
        "rating": 2,
        "health_tips": [
            "Deep-fried - high fat content",
            "Try air-fried version for healthier option",
            "Chickpea flour provides some protein"
        ],
        "tags": ["fried", "vegetarian", "snack"]
    },
    17: {
        "name": "Pav Bhaji",
        "emoji": "🥘",
        "calories": 350,
        "protein": 10,
        "carbs": 52,
        "fat": 12,
        "fiber": 8,
        "sodium": 840,
        "sugar": 6,
        "cholesterol": 25,
        "potassium": 680,
        "rating": 3,
        "health_tips": [
            "Vegetable-rich - good micronutrient source",
            "Very high in sodium - limit intake",
            "Use whole wheat pav for better nutrition"
        ],
        "tags": ["vegetarian", "vegetables", "high-sodium"]
    },
    18: {
        "name": "Pizza",
        "emoji": "🍕",
        "calories": 285,
        "protein": 12,
        "carbs": 36,
        "fat": 10,
        "fiber": 2,
        "sodium": 640,
        "sugar": 3,
        "cholesterol": 20,
        "potassium": 180,
        "rating": 3,
        "health_tips": [
            "Choose thin crust to reduce carbs",
            "Load up on vegetable toppings",
            "Control cheese quantity for lower fat"
        ],
        "tags": ["fast-food", "high-carb", "dairy"]
    },
    19: {
        "name": "Samosa",
        "emoji": "🥟",
        "calories": 310,
        "protein": 6,
        "carbs": 32,
        "fat": 18,
        "fiber": 3,
        "sodium": 480,
        "sugar": 1,
        "cholesterol": 0,
        "potassium": 240,
        "rating": 2,
        "health_tips": [
            "Deep-fried - high calorie density",
            "Try baked version for healthier alternative",
            "Potato filling is mostly carbs"
        ],
        "tags": ["fried", "vegetarian", "snack"]
    }
}

# ... (rest of the file remains exactly the same)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# In app.py - Update model_predict() with debug prints
def model_predict(img_path):
    img = image.load_img(img_path, target_size=(299, 299))
    print(f"Image loaded successfully: {img.size}")  # Debug
    x = image.img_to_array(img) / 255.0
    print(f"Array range: {x.min()} - {x.max()}")  # Should be 0-1
    x = np.expand_dims(x, axis=0)
    
    preds = model.predict(x)
    print(f"Raw predictions: {preds}")  # Debug output
    confidence = float(np.max(preds))
    print(f"Calculated confidence: {confidence}")  # Debug
    
    return np.argmax(preds), confidence * 100

class NutritionAnalyzer:
    @staticmethod
    def calculate_bmr(weight, height, age, gender):
        """Calculate Basal Metabolic Rate"""
        if gender.lower() == 'male':
            return 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            return 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    @staticmethod
    def get_daily_intake(user_id=1):
        db = get_db()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get complete nutritional sums for today
        result = db.execute('''
            SELECT 
                SUM(calories) AS calories,
                SUM(sodium) AS sodium,
                SUM(protein) AS protein,
                SUM(carbs) AS carbs,
                SUM(fat) AS fat,
                SUM(fiber) AS fiber,
                SUM(sugar) AS sugar,
                SUM(cholesterol) AS cholesterol,
                SUM(potassium) AS potassium
            FROM meals 
            WHERE DATE(timestamp) = ?
        ''', (today,)).fetchone()
        
        # Get user profile for personalized limits
        profile = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        # Calculate personalized limits based on profile
        if profile:
            bmr = NutritionAnalyzer.calculate_bmr(
                profile['weight'],
                profile['height'],
                profile['age'],
                profile['gender']
            )
            
            activity_factor = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9
            }.get(profile['activity_level'], 1.55)
            
            tdee = bmr * activity_factor
            
            if profile['goal'] == 'lose_weight':
                tdee -= 500  # 500 calorie deficit
            elif profile['goal'] == 'gain_muscle':
                tdee += 500  # 500 calorie surplus
            
            personalized_limits = {
                'calories': tdee,
                'protein': profile['weight'] * 1.6,  # g per kg body weight
                'carbs': (tdee * 0.5) / 4,          # 50% of calories from carbs
                'fat': (tdee * 0.3) / 9,            # 30% of calories from fat
                'fiber': 25,                         # g
                'sodium': 2300,                      # mg
                'sugar': (tdee * 0.1) / 4,           # max 10% from sugar
                'cholesterol': 300,                  # mg
                'potassium': 3500                    # mg
            }
        else:
            personalized_limits = app.config['DAILY_LIMITS']
        
        # Convert result to dict with default 0 values
        intake = {k: (result[k] or 0) for k in result.keys()}
        
        # Calculate percentages
        percentages = {
            k: round((intake[k] / personalized_limits[k]) * 100, 1)
            if personalized_limits[k] > 0 else 0
            for k in intake.keys()
        }
        
        return {
            'intake': intake,
            'limits': personalized_limits,
            'percentages': percentages,
            'units': app.config['NUTRIENT_UNITS']
        }

    @staticmethod
    def get_user_profile(user_id=1):
        db = get_db()
        try:
            profile = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if profile:
                return dict(profile)
            return {
                'goal': 'maintain',
                'allergies': '',
                'conditions': ''
            }
        except Exception as e:
            app.logger.error(f"Profile fetch error: {str(e)}")
            return None

    @staticmethod
    def generate_personalized_tips(food_data, user_profile=None):
        if not user_profile:
            user_profile = NutritionAnalyzer.get_user_profile()
        
        tips = food_data.get('health_tips', [])
        
        # Hypertension warnings
        if 'hypertension' in user_profile.get('conditions', '').lower():
            if food_data['sodium'] > 300:
                tips.append(f"⚠️ High sodium ({food_data['sodium']}mg) - may elevate blood pressure")
            if food_data['cholesterol'] > 100:
                tips.append(f"⚠️ Contains {food_data['cholesterol']}mg cholesterol - monitor intake")
        
        # Diabetes warnings
        if 'diabetes' in user_profile.get('conditions', '').lower():
            if food_data['carbs'] > 30:
                tips.append(f"⚠️ High carbs ({food_data['carbs']}g) - monitor blood sugar")
            if food_data.get('sugar', 0) > 10:
                tips.append(f"⚠️ Contains {food_data['sugar']}g sugar - consider alternatives")
        
        # Weight management tips
        if user_profile.get('goal') == 'lose_weight':
            if food_data['calories'] > 300:
                tips.append(f"🔹 High calorie ({food_data['calories']}kcal) - watch portion size")
            if food_data['fat'] > 15:
                tips.append(f"🔹 High fat ({food_data['fat']}g) - consider leaner options")
        
        # Allergy warnings
        allergies = [a.strip().lower() for a in user_profile.get('allergies', '').split(',') if a.strip()]
        food_name = food_data['name'].lower()
        food_tags = [t.lower() for t in food_data.get('tags', [])]
        
        for allergy in allergies:
            if allergy in food_name or allergy in food_tags:
                tips.append(f"❌ Contains {allergy} - not safe for your allergy")
        
        # Dietary preferences
        preferences = [p.strip().lower() for p in user_profile.get('dietary_preferences', '').split(',') if p.strip()]
        if 'vegetarian' in preferences and 'meat' in food_tags:
            tips.append("⚠️ Contains meat - not vegetarian")
        if 'vegan' in preferences and ('dairy' in food_tags or 'eggs' in food_tags):
            tips.append("⚠️ Contains animal products - not vegan")
        
        return tips

# API Endpoints
@app.route('/')
def index():
    return render_template('index.html', FOOD_CLASSES=FOOD_CLASSES)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'error': 'Invalid file type'}), 400

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if model is None:
            raise Exception("Food recognition model not available")

        pred_class, confidence = model_predict(filepath)
        print(f"Final confidence being sent: {confidence}%")  # Debug
        
        # Get food data BEFORE returning response
        food_data = FOOD_CLASSES.get(pred_class)
        if not food_data:
            raise Exception("Food class not recognized")

        # Get user profile for personalized tips
        user_profile = NutritionAnalyzer.get_user_profile()
        food_data['health_tips'] = NutritionAnalyzer.generate_personalized_tips(food_data, user_profile)

        # Save meal to database
        db = get_db()
        db.execute('''
            INSERT INTO meals (
                food_name, calories, sodium, protein, carbs, fat, fiber, 
                sugar, cholesterol, potassium, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            food_data['name'],
            food_data['calories'],
            food_data['sodium'],
            food_data['protein'],
            food_data['carbs'],
            food_data['fat'],
            food_data['fiber'],
            food_data.get('sugar', 0),
            food_data.get('cholesterol', 0),
            food_data.get('potassium', 0),
            url_for('static', filename=f'uploads/{filename}')
        ))
        db.commit()

        return jsonify({
            'status': 'success',
            'prediction': food_data,
            'confidence': confidence,  # Send as raw number
            'confidence_percent': f"{confidence:.1f}%",  # Formatted version
            'image_url': url_for('static', filename=f'uploads/{filename}'),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        app.logger.error(f"Prediction error: {str(e)}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if 'filepath' in locals() and os.path.exists(filepath) and os.path.getsize(filepath) == 0:
            os.remove(filepath)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    db = get_db()
    user_id = 1  # Default user ID
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            # Validate and update profile
            db.execute('''
                UPDATE users SET
                    name = ?,
                    age = ?,
                    gender = ?,
                    weight = ?,
                    height = ?,
                    goal = ?,
                    activity_level = ?,
                    allergies = ?,
                    conditions = ?,
                    dietary_preferences = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                data.get('name'),
                int(data.get('age', 25)),
                data.get('gender', 'other'),
                float(data.get('weight', 70.0)),
                float(data.get('height', 170.0)),
                data.get('goal', 'maintain'),
                data.get('activity_level', 'moderate'),
                data.get('allergies', ''),
                data.get('conditions', ''),
                data.get('dietary_preferences', ''),
                user_id
            ))
            db.commit()
            
            # Return updated profile
            profile = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            return jsonify({
                'status': 'success',
                'profile': dict(profile),
                'daily_needs': NutritionAnalyzer.get_daily_intake(user_id)['limits']
            })
            
        except Exception as e:
            db.rollback()
            app.logger.error(f"Profile update failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to update profile',
                'error': str(e)
            }), 500

    # GET request
    try:
        profile = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if profile:
            return jsonify({
                'status': 'success',
                'profile': dict(profile),
                'daily_needs': NutritionAnalyzer.get_daily_intake(user_id)['limits']
            })
        return jsonify({
            'status': 'error',
            'message': 'User profile not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch profile',
            'error': str(e)
        }), 500

@app.route('/daily_intake', methods=['GET'])
def daily_intake():
    try:
        user_id = 1  # Default user ID
        data = NutritionAnalyzer.get_daily_intake(user_id)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/meal_history', methods=['GET'])
def meal_history():
    try:
        db = get_db()
        limit = request.args.get('limit', default=7, type=int)
        meals = db.execute('''
            SELECT * FROM meals 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
        
        return jsonify({
            'status': 'success',
            'meals': [dict(meal) for meal in meals]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# # import os
# # import sqlite3
# # import numpy as np
# # from datetime import datetime
# # from flask import Flask, request, render_template, jsonify, g
# # from werkzeug.utils import secure_filename
# # from tensorflow.keras.models import load_model
# # from tensorflow.keras.preprocessing import image

# # app = Flask(__name__)
# # app.secret_key = 'your_secret_key_here'

# # # Configuration
# # app.config.update({
# #     'UPLOAD_FOLDER': 'static/uploads',
# #     'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'webp'},
# #     'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
# #     'DATABASE': 'nutrition.db',
# #     'DAILY_LIMITS': {
# #         'calories': 2000,
# #         'sodium': 2300,
# #         'protein': 50,
# #         'carbs': 300,
# #         'fat': 70
# #     }
# # })

# # # Database setup
# # def get_db():
# #     if 'db' not in g:
# #         g.db = sqlite3.connect(app.config['DATABASE'])
# #         g.db.row_factory = sqlite3.Row
# #     return g.db

# # def init_db():
# #     with app.app_context():
# #         db = get_db()
# #         try:
# #             # Create tables if they don't exist
# #             db.execute('''
# #                 CREATE TABLE IF NOT EXISTS users (
# #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                     goal TEXT NOT NULL DEFAULT 'maintain',
# #                     allergies TEXT DEFAULT '',
# #                     conditions TEXT DEFAULT '',
# #                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #                 )
# #             ''')
            
# #             db.execute('''
# #                 CREATE TABLE IF NOT EXISTS meals (
# #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                     food_name TEXT NOT NULL,
# #                     calories REAL NOT NULL,
# #                     sodium REAL NOT NULL,
# #                     carbs REAL NOT NULL,
# #                     protein REAL NOT NULL,
# #                     fat REAL NOT NULL,
# #                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #                 )
# #             ''')
            
# #             # Ensure default user exists
# #             db.execute('''
# #                 INSERT OR IGNORE INTO users (id, goal) 
# #                 VALUES (1, 'maintain')
# #             ''')
            
# #             db.commit()
# #         except Exception as e:
# #             app.logger.error(f"Database initialization failed: {str(e)}")
# #             db.rollback()

# # # Call this at startup
# # init_db()

# # if not os.path.exists(app.config['DATABASE']):
# #     init_db()

# # # Load model
# # try:
# #     model = load_model("model_inceptionV3.h5")
# #     print("Model loaded successfully")
# # except Exception as e:
# #     print(f"Model loading failed: {str(e)}")
# #     model = None
# # # Food classes with emojis and nutritional information
# # FOOD_CLASSES = {
# #     0: {
# #         "name": "🍔 Burger",
# #         "calories": 354,
# #         "protein": 16,
# #         "carbs": 29,
# #         "fat": 19,
# #         "fiber": 2,
# #         "sodium": 500,
# #         "health_tips": ["High in saturated fats", "Opt for whole grain buns", "Add veggies for fiber"],
# #         "rating": 2  # 1-5 scale (1=least healthy, 5=most healthy)
# #     },
# #     1: {
# #         "name": "🫓 Butter Naan",
# #         "calories": 320,
# #         "protein": 9,
# #         "carbs": 46,
# #         "fat": 12,
# #         "fiber": 2,
# #         "sodium": 380,
# #         "health_tips": ["High in refined carbs", "Pair with protein-rich curries", "Limit portion size"],
# #         "rating": 3
# #     },
# #     # Add all other food items with similar nutritional info
# #     2: {
# #         "name": "☕ Chai",
# #         "calories": 120,
# #         "protein": 4,
# #         "carbs": 18,
# #         "fat": 4,
# #         "fiber": 0,
# #         "sodium": 50,
# #         "health_tips": ["Contains antioxidants", "Reduce sugar content", "Use low-fat milk"],
# #         "rating": 4
# #     },
# #     3: {
# #         "name": "🥖 Chapati",
# #         "calories": 104,
# #         "protein": 3,
# #         "carbs": 20,
# #         "fat": 2,
# #         "fiber": 3,
# #         "sodium": 190,
# #         "health_tips": ["Good source of fiber", "Made from whole wheat", "Low fat content"],
# #         "rating": 4
# #     },
# #     4: {
# #         "name": "🥘 Chole Bhature",
# #         "calories": 430,
# #         "protein": 15,
# #         "carbs": 60,
# #         "fat": 16,
# #         "fiber": 8,
# #         "sodium": 620,
# #         "health_tips": ["High in complex carbs", "Chickpeas are protein-rich", "Fried component increases fat"],
# #         "rating": 3
# #     },
# #     5: {
# #         "name": "🍛 Dal Makhani",
# #         "calories": 350,
# #         "protein": 18,
# #         "carbs": 40,
# #         "fat": 14,
# #         "fiber": 12,
# #         "sodium": 480,
# #         "health_tips": ["Excellent plant protein", "High in fiber", "Reduce cream for healthier version"],
# #         "rating": 4
# #     },
# #     6: {
# #         "name": "🍲 Dhokla",
# #         "calories": 160,
# #         "protein": 8,
# #         "carbs": 26,
# #         "fat": 3,
# #         "fiber": 3,
# #         "sodium": 420,
# #         "health_tips": ["Steamed - low fat", "Fermented - good for gut", "High in sodium"],
# #         "rating": 4
# #     },
# #     7: {
# #         "name": "🍚 Fried Rice",
# #         "calories": 380,
# #         "protein": 12,
# #         "carbs": 58,
# #         "fat": 12,
# #         "fiber": 3,
# #         "sodium": 540,
# #         "health_tips": ["Add more vegetables", "Use brown rice for better nutrition", "Control oil quantity"],
# #         "rating": 3
# #     },
# #     8: {
# #         "name": "🍥 Idli",
# #         "calories": 110,
# #         "protein": 4,
# #         "carbs": 22,
# #         "fat": 1,
# #         "fiber": 2,
# #         "sodium": 290,
# #         "health_tips": ["Low calorie option", "Fermented - easy to digest", "Pair with sambar for protein"],
# #         "rating": 5
# #     },
# #     9: {
# #         "name": "🥨 Jalebi",
# #         "calories": 320,
# #         "protein": 2,
# #         "carbs": 75,
# #         "fat": 5,
# #         "fiber": 1,
# #         "sodium": 30,
# #         "health_tips": ["High in simple sugars", "Occasional treat only", "Avoid on empty stomach"],
# #         "rating": 1
# #     },
# #     10: {
# #         "name": "🌯 Kaathi Rolls",
# #         "calories": 340,
# #         "protein": 18,
# #         "carbs": 32,
# #         "fat": 15,
# #         "fiber": 3,
# #         "sodium": 680,
# #         "health_tips": ["Choose grilled over fried", "Load up on veggies", "Watch portion size"],
# #         "rating": 3
# #     },
# #     11: {
# #         "name": "🧆 Kadai Paneer",
# #         "calories": 380,
# #         "protein": 22,
# #         "carbs": 18,
# #         "fat": 26,
# #         "fiber": 4,
# #         "sodium": 520,
# #         "health_tips": ["Good protein source", "High in saturated fat", "Control portion size"],
# #         "rating": 3
# #     },
# #     12: {
# #         "name": "🍦 Kulfi",
# #         "calories": 280,
# #         "protein": 6,
# #         "carbs": 32,
# #         "fat": 15,
# #         "fiber": 0,
# #         "sodium": 80,
# #         "health_tips": ["High in sugar", "Contains calcium", "Occasional treat"],
# #         "rating": 2
# #     },
# #     13: {
# #         "name": "🥘 Masala Dosa",
# #         "calories": 320,
# #         "protein": 8,
# #         "carbs": 48,
# #         "fat": 10,
# #         "fiber": 5,
# #         "sodium": 580,
# #         "health_tips": ["Fermented - good for digestion", "Opt for less oil", "Potato filling is carb-heavy"],
# #         "rating": 4
# #     },
# #     14: {
# #         "name": "🥟 Momos",
# #         "calories": 180,
# #         "protein": 9,
# #         "carbs": 24,
# #         "fat": 5,
# #         "fiber": 2,
# #         "sodium": 420,
# #         "health_tips": ["Steamed version is healthier", "Good protein option", "Watch the dipping sauce"],
# #         "rating": 4
# #     },
# #     15: {
# #         "name": "🧆 Paani Puri",
# #         "calories": 120,
# #         "protein": 2,
# #         "carbs": 22,
# #         "fat": 3,
# #         "fiber": 2,
# #         "sodium": 380,
# #         "health_tips": ["Small portion size", "Water quality matters", "High in refined carbs"],
# #         "rating": 3
# #     },
# #     16: {
# #         "name": "🍤 Pakode",
# #         "calories": 280,
# #         "protein": 6,
# #         "carbs": 26,
# #         "fat": 16,
# #         "fiber": 3,
# #         "sodium": 450,
# #         "health_tips": ["Deep-fried - high fat", "Try air-fried version", "Use chickpea flour for protein"],
# #         "rating": 2
# #     },
# #     17: {
# #         "name": "🥘 Pav Bhaji",
# #         "calories": 350,
# #         "protein": 10,
# #         "carbs": 52,
# #         "fat": 12,
# #         "fiber": 8,
# #         "sodium": 840,
# #         "health_tips": ["Vegetable-rich", "High in sodium", "Use whole wheat pav"],
# #         "rating": 3
# #     },
# #     18: {
# #         "name": "🍕 Pizza",
# #         "calories": 285,
# #         "protein": 12,
# #         "carbs": 36,
# #         "fat": 10,
# #         "fiber": 2,
# #         "sodium": 640,
# #         "health_tips": ["Choose thin crust", "Load up on veggies", "Control cheese quantity"],
# #         "rating": 3
# #     },
# #     19: {
# #         "name": "🥟 Samosa",
# #         "calories": 310,
# #         "protein": 6,
# #         "carbs": 32,
# #         "fat": 18,
# #         "fiber": 3,
# #         "sodium": 480,
# #         "health_tips": ["Deep-fried - high calorie", "Try baked version", "Potato filling is carb-heavy"],
# #         "rating": 2
# #     }
# # }

# # # --- Helper Functions ---
# # def allowed_file(filename):
# #     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# # def model_predict(img_path):
# #     img = image.load_img(img_path, target_size=(299, 299))
# #     x = image.img_to_array(img) / 255
# #     x = np.expand_dims(x, axis=0)
# #     preds = model.predict(x)
# #     return np.argmax(preds), float(np.max(preds))

# # # --- Nutrition Logic ---
# # class NutritionAnalyzer:
# #     @staticmethod
# #     def get_daily_intake():
# #         db = get_db()
# #         today = datetime.now().strftime('%Y-%m-%d')
# #         result = db.execute('''
# #             SELECT SUM(calories) AS calories, SUM(sodium) AS sodium, 
# #                    SUM(protein) AS protein, SUM(carbs) AS carbs, SUM(fat) AS fat
# #             FROM meals 
# #             WHERE DATE(timestamp) = ?
# #         ''', (today,)).fetchone()
        
# #         # Convert None to 0 for each value
# #         intake = dict(result) if result else {}
# #         for nutrient in ['calories', 'sodium', 'protein', 'carbs', 'fat']:
# #             intake[nutrient] = intake.get(nutrient, 0) or 0
            
# #         return intake

# #     @staticmethod
# #     def get_user_profile():
# #         db = get_db()
# #         try:
# #             profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
# #             return {
# #                 'goal': profile['goal'] if profile and 'goal' in profile else 'maintain',
# #                 'allergies': profile['allergies'] if profile and 'allergies' in profile else '',
# #                 'conditions': profile['conditions'] if profile and 'conditions' in profile else ''
# #             }
# #         except Exception:
# #             return {
# #                 'goal': 'maintain',
# #                 'allergies': '',
# #                 'conditions': ''
# #             }


# #     @staticmethod
# #     def generate_personalized_tips(food_data):
# #         profile = NutritionAnalyzer.get_user_profile()
# #         tips = food_data.get('health_tips', [])
        
# #         # Add tips based on user profile
# #         if 'hypertension' in profile['conditions'].lower() and food_data['sodium'] > 300:
# #             tips.append(f"⚠️ High sodium ({food_data['sodium']}mg) - may elevate blood pressure")
        
# #         if 'diabetes' in profile['conditions'].lower() and food_data['carbs'] > 30:
# #             tips.append(f"⚠️ High carbs ({food_data['carbs']}g) - monitor blood sugar")
        
# #         if profile['goal'] == 'lose_weight' and food_data['calories'] > 300:
# #             tips.append(f"🔹 High calorie ({food_data['calories']}kcal) - watch portion size")
        
# #         # Check for allergies
# #         allergies = [a.strip().lower() for a in profile['allergies'].split(',') if a.strip()]
# #         food_name = food_data['name'].lower()
        
# #         for allergy in allergies:
# #             if allergy in food_name:
# #                 tips.append(f"❌ May contain {allergy} - not safe for your allergy")
        
# #         return tips

# # # --- Routes ---
# # @app.route('/')
# # def index():
# #     return render_template('index.html', FOOD_CLASSES=FOOD_CLASSES)

# # @app.route('/predict', methods=['POST'])
# # def predict():
# #     try:
# #         # Validate request
# #         if 'file' not in request.files:
# #             return jsonify({'status': 'error', 'error': 'No file provided'}), 400
            
# #         file = request.files['file']
# #         if file.filename == '':
# #             return jsonify({'status': 'error', 'error': 'No selected file'}), 400
            
# #         # Validate file type
# #         if not allowed_file(file.filename):
# #             return jsonify({
# #                 'status': 'error',
# #                 'error': 'Invalid file type. Only JPG, JPEG, PNG or WEBP allowed'
# #             }), 400

# #         # Create upload directory if needed
# #         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
# #         # Generate unique filename
# #         ext = file.filename.rsplit('.', 1)[1].lower()
# #         filename = f"{uuid.uuid4().hex}.{ext}"
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
# #         try:
# #             # Save file
# #             file.save(filepath)
            
# #             # Verify file was saved
# #             if not os.path.exists(filepath):
# #                 raise Exception("Failed to save uploaded file")
                
# #             # Verify model is loaded
# #             if model is None:
# #                 raise Exception("Food recognition model not loaded")

# #             # Process image
# #             img = image.load_img(filepath, target_size=(299, 299))
# #             x = image.img_to_array(img) / 255.0
# #             x = np.expand_dims(x, axis=0)
            
# #             # Make prediction
# #             preds = model.predict(x)
# #             pred_class = np.argmax(preds, axis=1)[0]
# #             confidence = float(np.max(preds))
            
# #             # Get food data
# #             food_data = FOOD_CLASSES.get(pred_class)
# #             if not food_data:
# #                 raise Exception("Food not recognized")
                
# #             # Generate safe image URL
# #             image_url = url_for('static', filename=f'uploads/{filename}', _external=False)
            
# #             # Log to database
# #             try:
# #                 db = get_db()
# #                 db.execute('''
# #                     INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
# #                     VALUES (?, ?, ?, ?, ?, ?)
# #                 ''', (
# #                     food_data['name'],
# #                     food_data['calories'],
# #                     food_data['sodium'],
# #                     food_data['carbs'],
# #                     food_data['protein'],
# #                     food_data['fat']
# #                 ))
# #                 db.commit()
# #             except Exception as db_error:
# #                 app.logger.error(f"Database error: {str(db_error)}")
# #                 db.rollback()

# #             return jsonify({
# #                 'status': 'success',
# #                 'prediction': food_data,
# #                 'confidence': f"{confidence * 100:.2f}%",
# #                 'image_url': image_url
# #             })
            
# #         except Exception as processing_error:
# #             # Clean up file if processing failed
# #             if os.path.exists(filepath):
# #                 os.remove(filepath)
# #             raise processing_error

# #     except Exception as e:
# #         app.logger.error(f"Prediction error: {str(e)}")
# #         return jsonify({
# #             'status': 'error',
# #             'error': str(e)
# #         }), 500
# #     try:
# #         # Validate request
# #         if 'file' not in request.files:
# #             return jsonify({'error': 'No file provided'}), 400
            
# #         file = request.files['file']
# #         if file.filename == '':
# #             return jsonify({'error': 'No selected file'}), 400
            
# #         # Validate file type
# #         if not allowed_file(file.filename):
# #             return jsonify({
# #                 'error': 'Invalid file type. Please upload JPG, JPEG, PNG or WEBP'
# #             }), 400

# #         # Create upload directory if needed
# #         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
# #         # Generate secure filename
# #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# #         filename = f"{timestamp}_{secure_filename(file.filename)}"
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
# #         # Save file
# #         file.save(filepath)
        
# #         # Verify model is loaded
# #         if not model:
# #             raise Exception("Food recognition model not initialized")

# #         # Process image
# #         try:
# #             img = image.load_img(filepath, target_size=(299, 299))
# #             x = image.img_to_array(img) / 255.0
# #             x = np.expand_dims(x, axis=0)
            
# #             # Make prediction
# #             preds = model.predict(x)
# #             pred_class = np.argmax(preds, axis=1)[0]
# #             confidence = float(np.max(preds))
# #         except Exception as e:
# #             raise Exception(f"Image processing failed: {str(e)}")

# #         # Get food data
# #         food_data = FOOD_CLASSES.get(pred_class)
# #         if not food_data:
# #             return jsonify({'error': 'Food not recognized'}), 400

# #         # Generate safe image URL
# #         image_url = url_for('static', filename=f'uploads/{filename}', _external=True)

# #         # Log to database
# #         try:
# #             db = get_db()
# #             db.execute('''
# #                 INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
# #                 VALUES (?, ?, ?, ?, ?, ?)
# #             ''', (
# #                 food_data['name'],
# #                 food_data['calories'],
# #                 food_data['sodium'],
# #                 food_data['carbs'],
# #                 food_data['protein'],
# #                 food_data['fat']
# #             ))
# #             db.commit()
# #         except Exception as e:
# #             app.logger.error(f"Database error: {str(e)}")
# #             db.rollback()

# #         return jsonify({
# #             'status': 'success',
# #             'prediction': food_data,
# #             'confidence': f"{confidence * 100:.2f}%",
# #             'image_url': image_url
# #         })

# #     except Exception as e:
# #         app.logger.error(f"Prediction error: {str(e)}")
# #         return jsonify({
# #             'status': 'error',
# #             'error': str(e)
# #         }), 500
        
# #     finally:
# #         # Clean up if needed
# #         pass
# #     try:
# #         if 'file' not in request.files:
# #             return jsonify({'error': 'No file part'}), 400
            
# #         file = request.files['file']
        
# #         if file.filename == '':
# #             return jsonify({'error': 'No selected file'}), 400
            
# #         if not allowed_file(file.filename):
# #             return jsonify({'error': 'Only JPG, JPEG, PNG & WEBP files allowed'}), 400

# #         # Create upload directory if not exists
# #         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
# #         # Generate unique filename
# #         filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# #         file.save(filepath)

# #         # Verify model is loaded
# #         if model is None:
# #             raise Exception("Food recognition model not loaded")

# #         # Make prediction
# #         pred_class, confidence = model_predict(filepath)
        
# #         # Get food data
# #         food_data = FOOD_CLASSES.get(pred_class, {})
# #         if not food_data:
# #             return jsonify({'error': 'Food not recognized'}), 400

# #         # Generate safe URL for the image
# #         image_url = url_for('static', filename=f'uploads/{filename}')

# #         # Log to database
# #         db = get_db()
# #         db.execute('''
# #             INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
# #             VALUES (?, ?, ?, ?, ?, ?)
# #         ''', (
# #             food_data['name'],
# #             food_data['calories'],
# #             food_data['sodium'],
# #             food_data['carbs'],
# #             food_data['protein'],
# #             food_data['fat']
# #         ))
# #         db.commit()

# #         return jsonify({
# #             'prediction': food_data,
# #             'confidence': f"{confidence * 100:.2f}%",
# #             'image_url': image_url
# #         })

# #     except Exception as e:
# #         app.logger.error(f"Prediction failed: {str(e)}")
# #         return jsonify({'error': str(e)}), 500
        
# #     finally:
# #         # No need to delete file as we're keeping it for display
# #         pass
# #     try:
# #         if 'file' not in request.files:
# #             return jsonify({'error': 'No file part'}), 400
            
# #         file = request.files['file']
        
# #         if file.filename == '':
# #             return jsonify({'error': 'No selected file'}), 400
            
# #         if not allowed_file(file.filename):
# #             return jsonify({'error': 'Invalid file type'}), 400

# #         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
# #         filename = secure_filename(file.filename)
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# #         file.save(filepath)

# #         if model is None:
# #             raise Exception("Model not loaded")

# #         if not os.path.exists(filepath):
# #             raise Exception("File failed to save")

# #         # Make prediction
# #         pred_class, confidence = model_predict(filepath)
        
# #         # Get food data
# #         food_data = FOOD_CLASSES.get(pred_class, {})
# #         if not food_data:
# #             return jsonify({'error': 'Food class not recognized'}), 400

# #         # Ensure health_tips exists and is a list
# #         if 'health_tips' not in food_data:
# #             food_data['health_tips'] = []
# #         elif not isinstance(food_data['health_tips'], list):
# #             food_data['health_tips'] = [food_data['health_tips']]

# #         # Generate personalized tips safely
# #         profile = NutritionAnalyzer.get_user_profile()
# #         if profile:
# #             if 'hypertension' in (profile.get('conditions') or '').lower() and food_data.get('sodium', 0) > 300:
# #                 food_data['health_tips'].append(f"⚠️ High sodium ({food_data['sodium']}mg) - may elevate blood pressure")
            
# #             if 'diabetes' in (profile.get('conditions') or '').lower() and food_data.get('carbs', 0) > 30:
# #                 food_data['health_tips'].append(f"⚠️ High carbs ({food_data['carbs']}g) - monitor blood sugar")
            
# #             if (profile.get('goal') or '') == 'lose_weight' and food_data.get('calories', 0) > 300:
# #                 food_data['health_tips'].append(f"🔹 High calorie ({food_data['calories']}kcal) - watch portion size")

# #         # Log to database
# #         db = get_db()
# #         db.execute('''
# #             INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
# #             VALUES (?, ?, ?, ?, ?, ?)
# #         ''', (
# #             food_data.get('name', 'Unknown'),
# #             food_data.get('calories', 0),
# #             food_data.get('sodium', 0),
# #             food_data.get('carbs', 0),
# #             food_data.get('protein', 0),
# #             food_data.get('fat', 0)
# #         ))
# #         db.commit()

# #         return jsonify({
# #             'prediction': food_data,
# #             'confidence': f"{confidence * 100:.2f}%",
# #             'image_url': filepath
# #         })

# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500
        
# #     finally:
# #         if 'filepath' in locals() and os.path.exists(filepath):
# #             os.remove(filepath)
# #     try:
# #         if 'file' not in request.files:
# #             return jsonify({'error': 'No file part'}), 400
            
# #         file = request.files['file']
        
# #         if file.filename == '':
# #             return jsonify({'error': 'No selected file'}), 400
            
# #         if not allowed_file(file.filename):
# #             return jsonify({'error': 'Invalid file type'}), 400

# #         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
# #         filename = secure_filename(file.filename)
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# #         file.save(filepath)

# #         if model is None:
# #             raise Exception("Model not loaded")

# #         if not os.path.exists(filepath):
# #             raise Exception("File failed to save")

# #         # Make prediction
# #         pred_class, confidence = model_predict(filepath)
        
# #         # Get food data
# #         food_data = FOOD_CLASSES.get(pred_class, {})
# #         if not food_data:
# #             return jsonify({'error': 'Food class not recognized'}), 400

# #         # Generate personalized tips
# #         personalized_tips = NutritionAnalyzer.generate_personalized_tips(food_data)
# #         food_data['health_tips'] = personalized_tips

# #         # Log to database
# #         db = get_db()
# #         db.execute('''
# #             INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
# #             VALUES (?, ?, ?, ?, ?, ?)
# #         ''', (
# #             food_data['name'],
# #             food_data['calories'],
# #             food_data['sodium'],
# #             food_data['carbs'],
# #             food_data['protein'],
# #             food_data['fat']
# #         ))
# #         db.commit()

# #         return jsonify({
# #             'prediction': food_data,
# #             'confidence': f"{confidence * 100:.2f}%",
# #             'image_url': filepath
# #         })

# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500
        
# #     finally:
# #         if 'filepath' in locals() and os.path.exists(filepath):
# #             os.remove(filepath)

# # @app.route('/profile', methods=['GET', 'POST'])
# # def profile():
# #     db = get_db()
    
# #     if request.method == 'POST':
# #         try:
# #             # Ensure database connection is open
# #             if db is None:
# #                 raise Exception("Database connection failed")
                
# #             # Get form data safely
# #             data = request.form
# #             goal = data.get('goal', 'maintain')
# #             allergies = data.get('allergies', '')
# #             conditions = data.get('conditions', '')
            
# #             # Update or insert profile
# #             db.execute('''
# #                 INSERT OR REPLACE INTO users (id, goal, allergies, conditions)
# #                 VALUES (1, ?, ?, ?)
# #             ''', (goal, allergies, conditions))
# #             db.commit()
            
# #             return jsonify({
# #                 'status': 'success',
# #                 'message': 'Profile updated successfully',
# #                 'profile': {
# #                     'goal': goal,
# #                     'allergies': allergies,
# #                     'conditions': conditions
# #                 }
# #             })
            
# #         except Exception as e:
# #             db.rollback()
# #             app.logger.error(f"Profile update failed: {str(e)}")
# #             return jsonify({
# #                 'status': 'error',
# #                 'message': 'Failed to update profile'
# #             }), 500

# #     # GET request
# #     try:
# #         profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
# #         if profile:
# #             return jsonify(dict(profile))
# #         else:
# #             # Return default profile if none exists
# #             return jsonify({
# #                 'goal': 'maintain',
# #                 'allergies': '',
# #                 'conditions': ''
# #             })
# #     except Exception as e:
# #         app.logger.error(f"Profile fetch failed: {str(e)}")
# #         return jsonify({
# #             'status': 'error',
# #             'message': 'Failed to fetch profile'
# #         }), 500
# #     db = get_db()
    
# #     if request.method == 'POST':
# #         try:
# #             # Get form data
# #             goal = request.form.get('goal', 'maintain')
# #             allergies = request.form.get('allergies', '')
# #             conditions = request.form.get('conditions', '')
            
# #             # Update profile in database
# #             db.execute('''
# #                 UPDATE users 
# #                 SET goal = ?, allergies = ?, conditions = ?
# #                 WHERE id = 1
# #             ''', (goal, allergies, conditions))
# #             db.commit()
            
# #             return jsonify({
# #                 'status': 'success',
# #                 'message': 'Profile updated successfully'
# #             })
# #         except Exception as e:
# #             return jsonify({
# #                 'status': 'error',
# #                 'message': str(e)
# #             }), 500

# #     # GET request
# #     try:
# #         profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
# #         return jsonify(dict(profile)) if profile else jsonify({
# #             'goal': 'maintain',
# #             'allergies': '',
# #             'conditions': ''
# #         })
# #     except Exception as e:
# #         return jsonify({
# #             'status': 'error',
# #             'message': str(e)
# #         }), 500
# #     db = get_db()
    
# #     if request.method == 'POST':
# #         try:
# #             data = request.get_json() or request.form.to_dict()
# #             db.execute('''
# #                 UPDATE users 
# #                 SET goal = ?, allergies = ?, conditions = ?
# #                 WHERE id = 1
# #             ''', (
# #                 data.get('goal', 'maintain'),
# #                 data.get('allergies', ''),
# #                 data.get('conditions', '')
# #             ))
# #             db.commit()
# #             return jsonify({'status': 'success'})
# #         except Exception as e:
# #             return jsonify({'error': str(e)}), 500

# #     # GET request
# #     try:
# #         profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
# #         return jsonify(dict(profile)) if profile else jsonify({
# #             'goal': 'maintain',
# #             'allergies': '',
# #             'conditions': ''
# #         })
# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500

# # @app.route('/daily_intake', methods=['GET'])
# # def daily_intake():
# #     try:
# #         intake = NutritionAnalyzer.get_daily_intake()
# #         limits = app.config['DAILY_LIMITS']
        
# #         # Calculate percentages
# #         percentages = {
# #             'calories': (intake['calories'] / limits['calories']) * 100,
# #             'sodium': (intake['sodium'] / limits['sodium']) * 100,
# #             'protein': (intake['protein'] / limits['protein']) * 100,
# #             'carbs': (intake['carbs'] / limits['carbs']) * 100,
# #             'fat': (intake['fat'] / limits['fat']) * 100
# #         }
        
# #         return jsonify({
# #             'consumed': intake,
# #             'limits': limits,
# #             'percentages': percentages
# #         })
# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500

# # @app.teardown_appcontext
# # def close_db(error):
# #     if hasattr(g, 'db'):
# #         g.db.close()

# # if __name__ == '__main__':
# #     init_db()  # Ensure database is initialized
# #     app.run(debug=True)

# import os
# import sqlite3
# import uuid
# import numpy as np
# from datetime import datetime
# from flask import Flask, request, render_template, jsonify, g, url_for
# from werkzeug.utils import secure_filename
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing import image

# app = Flask(__name__)
# app.secret_key = 'your_secret_key_here'

# # Configuration
# app.config.update({
#     'UPLOAD_FOLDER': 'static/uploads',
#     'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'webp'},
#     'MAX_CONTENT_LENGTH': 5 * 1024 * 1024,
#     'DATABASE': 'nutrition.db',
#     'DAILY_LIMITS': {
#         'calories': 2000,
#         'sodium': 2300,
#         'protein': 50,
#         'carbs': 300,
#         'fat': 70
#     }
# })

# # Database setup
# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(app.config['DATABASE'])
#         g.db.row_factory = sqlite3.Row
#     return g.db

# def init_db():
#     with app.app_context():
#         db = get_db()
#         try:
#             db.execute('''
#                 CREATE TABLE IF NOT EXISTS users (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     goal TEXT NOT NULL DEFAULT 'maintain',
#                     allergies TEXT DEFAULT '',
#                     conditions TEXT DEFAULT '',
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
            
#             db.execute('''
#                 CREATE TABLE IF NOT EXISTS meals (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     food_name TEXT NOT NULL,
#                     calories REAL NOT NULL,
#                     sodium REAL NOT NULL,
#                     carbs REAL NOT NULL,
#                     protein REAL NOT NULL,
#                     fat REAL NOT NULL,
#                     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             ''')
            
#             db.execute('INSERT OR IGNORE INTO users (id, goal) VALUES (1, "maintain")')
#             db.commit()
#         except Exception as e:
#             app.logger.error(f"Database initialization failed: {str(e)}")
#             db.rollback()

# init_db()

# # Load model
# try:
#     model = load_model("model_inceptionV3.h5")
#     print("Model loaded successfully")
# except Exception as e:
#     print(f"Model loading failed: {str(e)}")
#     model = None

# # Food classes with nutritional information
# FOOD_CLASSES = {
#     0: {"name": "Burger", "calories": 354, "protein": 16, "carbs": 29, "fat": 19, "fiber": 2, "sodium": 500, "rating": 2,
#         "health_tips": ["High in saturated fats", "Opt for whole grain buns", "Add veggies for fiber"]},
#     1: {"name": "Butter Naan", "calories": 320, "protein": 9, "carbs": 46, "fat": 12, "fiber": 2, "sodium": 380, "rating": 3,
#         "health_tips": ["High in refined carbs", "Pair with protein-rich curries", "Limit portion size"]},
#     2: {"name": "Chai", "calories": 120, "protein": 4, "carbs": 18, "fat": 4, "fiber": 0, "sodium": 50, "rating": 4,
#         "health_tips": ["Contains antioxidants", "Reduce sugar content", "Use low-fat milk"]},
#     3: {"name": "Chapati", "calories": 104, "protein": 3, "carbs": 20, "fat": 2, "fiber": 3, "sodium": 190, "rating": 4,
#         "health_tips": ["Good source of fiber", "Made from whole wheat", "Low fat content"]},
#     4: {"name": "Chole Bhature", "calories": 430, "protein": 15, "carbs": 60, "fat": 16, "fiber": 8, "sodium": 620, "rating": 3,
#         "health_tips": ["High in complex carbs", "Chickpeas are protein-rich", "Fried component increases fat"]},
#     5: {"name": "Dal Makhani", "calories": 350, "protein": 18, "carbs": 40, "fat": 14, "fiber": 12, "sodium": 480, "rating": 4,
#         "health_tips": ["Excellent plant protein", "High in fiber", "Reduce cream for healthier version"]},
#     6: {"name": "Dhokla", "calories": 160, "protein": 8, "carbs": 26, "fat": 3, "fiber": 3, "sodium": 420, "rating": 4,
#         "health_tips": ["Steamed - low fat", "Fermented - good for gut", "High in sodium"]},
#     7: {"name": "Fried Rice", "calories": 380, "protein": 12, "carbs": 58, "fat": 12, "fiber": 3, "sodium": 540, "rating": 3,
#         "health_tips": ["Add more vegetables", "Use brown rice for better nutrition", "Control oil quantity"]},
#     8: {"name": "Idli", "calories": 110, "protein": 4, "carbs": 22, "fat": 1, "fiber": 2, "sodium": 290, "rating": 5,
#         "health_tips": ["Low calorie option", "Fermented - easy to digest", "Pair with sambar for protein"]},
#     9: {"name": "Jalebi", "calories": 320, "protein": 2, "carbs": 75, "fat": 5, "fiber": 1, "sodium": 30, "rating": 1,
#         "health_tips": ["High in simple sugars", "Occasional treat only", "Avoid on empty stomach"]},
#     10: {"name": "Kaathi Rolls", "calories": 340, "protein": 18, "carbs": 32, "fat": 15, "fiber": 3, "sodium": 680, "rating": 3,
#          "health_tips": ["Choose grilled over fried", "Load up on veggies", "Watch portion size"]},
#     11: {"name": "Kadai Paneer", "calories": 380, "protein": 22, "carbs": 18, "fat": 26, "fiber": 4, "sodium": 520, "rating": 3,
#          "health_tips": ["Good protein source", "High in saturated fat", "Control portion size"]},
#     12: {"name": "Kulfi", "calories": 280, "protein": 6, "carbs": 32, "fat": 15, "fiber": 0, "sodium": 80, "rating": 2,
#          "health_tips": ["High in sugar", "Contains calcium", "Occasional treat"]},
#     13: {"name": "Masala Dosa", "calories": 320, "protein": 8, "carbs": 48, "fat": 10, "fiber": 5, "sodium": 580, "rating": 4,
#          "health_tips": ["Fermented - good for digestion", "Opt for less oil", "Potato filling is carb-heavy"]},
#     14: {"name": "Momos", "calories": 180, "protein": 9, "carbs": 24, "fat": 5, "fiber": 2, "sodium": 420, "rating": 4,
#          "health_tips": ["Steamed version is healthier", "Good protein option", "Watch the dipping sauce"]},
#     15: {"name": "Paani Puri", "calories": 120, "protein": 2, "carbs": 22, "fat": 3, "fiber": 2, "sodium": 380, "rating": 3,
#          "health_tips": ["Small portion size", "Water quality matters", "High in refined carbs"]},
#     16: {"name": "Pakode", "calories": 280, "protein": 6, "carbs": 26, "fat": 16, "fiber": 3, "sodium": 450, "rating": 2,
#          "health_tips": ["Deep-fried - high fat", "Try air-fried version", "Use chickpea flour for protein"]},
#     17: {"name": "Pav Bhaji", "calories": 350, "protein": 10, "carbs": 52, "fat": 12, "fiber": 8, "sodium": 840, "rating": 3,
#          "health_tips": ["Vegetable-rich", "High in sodium", "Use whole wheat pav"]},
#     18: {"name": "Pizza", "calories": 285, "protein": 12, "carbs": 36, "fat": 10, "fiber": 2, "sodium": 640, "rating": 3,
#          "health_tips": ["Choose thin crust", "Load up on veggies", "Control cheese quantity"]},
#     19: {"name": "Samosa", "calories": 310, "protein": 6, "carbs": 32, "fat": 18, "fiber": 3, "sodium": 480, "rating": 2,
#          "health_tips": ["Deep-fried - high calorie", "Try baked version", "Potato filling is carb-heavy"]}
# }

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# def model_predict(img_path):
#     img = image.load_img(img_path, target_size=(299, 299))
#     x = image.img_to_array(img) / 255.0
#     x = np.expand_dims(x, axis=0)
#     preds = model.predict(x)
#     return np.argmax(preds), float(np.max(preds))

# class NutritionAnalyzer:
#     @staticmethod
#     def get_daily_intake():
#         db = get_db()
#         today = datetime.now().strftime('%Y-%m-%d')
#         result = db.execute('''
#             SELECT SUM(calories) AS calories, SUM(sodium) AS sodium, 
#                    SUM(protein) AS protein, SUM(carbs) AS carbs, SUM(fat) AS fat
#             FROM meals 
#             WHERE DATE(timestamp) = ?
#         ''', (today,)).fetchone()
        
#         intake = dict(result) if result else {}
#         for nutrient in ['calories', 'sodium', 'protein', 'carbs', 'fat']:
#             intake[nutrient] = intake.get(nutrient, 0) or 0
            
#         return intake

#     @staticmethod
#     def get_user_profile():
#         db = get_db()
#         try:
#             profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
#             return {
#                 'goal': profile['goal'] if profile else 'maintain',
#                 'allergies': profile['allergies'] if profile else '',
#                 'conditions': profile['conditions'] if profile else ''
#             }
#         except Exception:
#             return {'goal': 'maintain', 'allergies': '', 'conditions': ''}

#     @staticmethod
#     def generate_personalized_tips(food_data):
#         profile = NutritionAnalyzer.get_user_profile()
#         tips = food_data.get('health_tips', [])
        
#         if 'hypertension' in profile['conditions'].lower() and food_data['sodium'] > 300:
#             tips.append(f"⚠️ High sodium ({food_data['sodium']}mg) - may elevate blood pressure")
        
#         if 'diabetes' in profile['conditions'].lower() and food_data['carbs'] > 30:
#             tips.append(f"⚠️ High carbs ({food_data['carbs']}g) - monitor blood sugar")
        
#         if profile['goal'] == 'lose_weight' and food_data['calories'] > 300:
#             tips.append(f"🔹 High calorie ({food_data['calories']}kcal) - watch portion size")
        
#         allergies = [a.strip().lower() for a in profile['allergies'].split(',') if a.strip()]
#         food_name = food_data['name'].lower()
        
#         for allergy in allergies:
#             if allergy in food_name:
#                 tips.append(f"❌ May contain {allergy} - not safe for your allergy")
        
#         return tips

# @app.route('/')
# def index():
#     return render_template('index.html', FOOD_CLASSES=FOOD_CLASSES)

# @app.route('/predict', methods=['POST'])
# def predict():
#     try:
#         if 'file' not in request.files:
#             return jsonify({'status': 'error', 'error': 'No file provided'}), 400
            
#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'status': 'error', 'error': 'No selected file'}), 400
            
#         if not allowed_file(file.filename):
#             return jsonify({'status': 'error', 'error': 'Invalid file type'}), 400

#         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
#         filename = secure_filename(f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}")
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         if model is None:
#             raise Exception("Model not loaded")

#         pred_class, confidence = model_predict(filepath)
        
#         food_data = FOOD_CLASSES.get(pred_class)
#         if not food_data:
#             raise Exception("Food class not recognized")

#         food_data['health_tips'] = NutritionAnalyzer.generate_personalized_tips(food_data)

#         db = get_db()
#         db.execute('''
#             INSERT INTO meals (food_name, calories, sodium, carbs, protein, fat)
#             VALUES (?, ?, ?, ?, ?, ?)
#         ''', (
#             food_data['name'],
#             food_data['calories'],
#             food_data['sodium'],
#             food_data['carbs'],
#             food_data['protein'],
#             food_data['fat']
#         ))
#         db.commit()

#         return jsonify({
#             'status': 'success',
#             'prediction': food_data,
#             'confidence': f"{confidence * 100:.2f}%",
#             'image_url': url_for('static', filename=f'uploads/{filename}')
#         })

#     except Exception as e:
#         app.logger.error(f"Prediction error: {str(e)}")
#         if 'filepath' in locals() and os.path.exists(filepath):
#             os.remove(filepath)
#         return jsonify({'status': 'error', 'error': str(e)}), 500

# @app.route('/profile', methods=['GET', 'POST'])
# def profile():
#     db = get_db()
    
#     if request.method == 'POST':
#         try:
#             # Get data from form or JSON
#             data = request.get_json() if request.is_json else request.form
            
#             goal = data.get('goal', 'maintain')
#             allergies = data.get('allergies', '')
#             conditions = data.get('conditions', '')
            
#             # Validate data
#             if not goal or goal not in ['maintain', 'lose_weight', 'gain_muscle']:
#                 return jsonify({'status': 'error', 'message': 'Invalid goal'}), 400
                
#             # Update profile
#             db.execute('''
#                 INSERT OR REPLACE INTO users (id, goal, allergies, conditions)
#                 VALUES (1, ?, ?, ?)
#             ''', (goal, allergies, conditions))
#             db.commit()
            
#             return jsonify({
#                 'status': 'success',
#                 'message': 'Profile updated successfully',
#                 'profile': {
#                     'goal': goal,
#                     'allergies': allergies,
#                     'conditions': conditions
#                 }
#             })
            
#         except Exception as e:
#             db.rollback()
#             app.logger.error(f"Profile update failed: {str(e)}")
#             return jsonify({
#                 'status': 'error',
#                 'message': 'Failed to update profile',
#                 'error': str(e)
#             }), 500

#     # GET request
#     try:
#         profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
#         if profile:
#             return jsonify(dict(profile))
#         return jsonify({
#             'goal': 'maintain',
#             'allergies': '',
#             'conditions': ''
#         })
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': 'Failed to fetch profile',
#             'error': str(e)
#         }), 500
#     db = get_db()
    
#     if request.method == 'POST':
#         try:
#             data = request.get_json() or request.form.to_dict()
#             db.execute('''
#                 INSERT OR REPLACE INTO users (id, goal, allergies, conditions)
#                 VALUES (1, ?, ?, ?)
#             ''', (
#                 data.get('goal', 'maintain'),
#                 data.get('allergies', ''),
#                 data.get('conditions', '')
#             ))
#             db.commit()
#             return jsonify({'status': 'success', 'message': 'Profile updated'})
#         except Exception as e:
#             db.rollback()
#             return jsonify({'status': 'error', 'message': str(e)}), 500

#     # GET request
#     try:
#         profile = db.execute('SELECT * FROM users WHERE id = 1').fetchone()
#         return jsonify(dict(profile)) if profile else jsonify({
#             'goal': 'maintain',
#             'allergies': '',
#             'conditions': ''
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500
# # Add this temporary route to check meals
# @app.route('/debug/meals')
# def debug_meals():
#     db = get_db()
#     meals = db.execute('SELECT * FROM meals WHERE DATE(timestamp) = DATE("now")').fetchall()
#     return jsonify([dict(meal) for meal in meals])
# @app.route('/daily_intake', methods=['GET'])
# def daily_intake():
#     try:
#         db = get_db()
#         today = datetime.now().strftime('%Y-%m-%d')
        
#         # Get sums with proper default values
#         result = db.execute('''
#             SELECT 
#                 COALESCE(SUM(calories), 0) AS calories,
#                 COALESCE(SUM(sodium), 0) AS sodium,
#                 COALESCE(SUM(protein), 0) AS protein,
#                 COALESCE(SUM(carbs), 0) AS carbs,
#                 COALESCE(SUM(fat), 0) AS fat
#             FROM meals 
#             WHERE DATE(timestamp) = ?
#         ''', (today,)).fetchone()

#         limits = app.config['DAILY_LIMITS']
        
#         return jsonify({
#             'status': 'success',
#             'consumed': dict(result),
#             'limits': limits,
#             'percentages': {
#                 'calories': round((result['calories'] / limits['calories']) * 100, 1),
#                 'sodium': round((result['sodium'] / limits['sodium']) * 100, 1),
#                 'protein': round((result['protein'] / limits['protein']) * 100, 1),
#                 'carbs': round((result['carbs'] / limits['carbs']) * 100, 1),
#                 'fat': round((result['fat'] / limits['fat']) * 100, 1)
#             }
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500
#     try:
#         db = get_db()
#         today = datetime.now().strftime('%Y-%m-%d')
        
#         # Get sums with proper default values
#         result = db.execute('''
#             SELECT 
#                 COALESCE(SUM(calories), 0) AS calories,
#                 COALESCE(SUM(sodium), 0) AS sodium,
#                 COALESCE(SUM(protein), 0) AS protein,
#                 COALESCE(SUM(carbs), 0) AS carbs,
#                 COALESCE(SUM(fat), 0) AS fat
#             FROM meals 
#             WHERE DATE(timestamp) = ?
#         ''', (today,)).fetchone()

#         limits = app.config['DAILY_LIMITS']
        
#         return jsonify({
#             'status': 'success',
#             'consumed': dict(result),
#             'limits': limits,
#             'percentages': {
#                 'calories': round((result['calories'] / limits['calories']) * 100, 1),
#                 'sodium': round((result['sodium'] / limits['sodium']) * 100, 1),
#                 'protein': round((result['protein'] / limits['protein']) * 100, 1),
#                 'carbs': round((result['carbs'] / limits['carbs']) * 100, 1),
#                 'fat': round((result['fat'] / limits['fat']) * 100, 1)
#             }
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500
#     try:
#         intake = NutritionAnalyzer.get_daily_intake()
#         limits = app.config['DAILY_LIMITS']
        
#         percentages = {
#             'calories': (intake['calories'] / limits['calories']) * 100,
#             'sodium': (intake['sodium'] / limits['sodium']) * 100,
#             'protein': (intake['protein'] / limits['protein']) * 100,
#             'carbs': (intake['carbs'] / limits['carbs']) * 100,
#             'fat': (intake['fat'] / limits['fat']) * 100
#         }
        
#         return jsonify({
#             'status': 'success',
#             'consumed': intake,
#             'limits': limits,
#             'percentages': percentages
#         })
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# @app.teardown_appcontext
# def close_db(error):
#     if hasattr(g, 'db'):
#         g.db.close()

# if __name__ == '__main__':
#     app.run(debug=True)