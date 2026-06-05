from flask import Flask, render_template, request, jsonify, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
DATABASE = 'weather_dashboard.db'
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# Cache for API responses (in seconds)
CACHE_DURATION = 600  # 10 minutes

def get_db():
    """Get database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables."""
    with app.app_context():
        db = get_db()
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            temperature_unit TEXT DEFAULT 'C',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, city)
        );
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            city TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            threshold REAL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS weather_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT UNIQUE NOT NULL,
            latitude REAL,
            longitude REAL,
            weather_data TEXT NOT NULL,
            forecast_data TEXT NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
        ''')
        db.commit()

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_cached_weather(city):
    """Get cached weather data if available and not expired."""
    db = get_db()
    cache = db.execute(
        'SELECT * FROM weather_cache WHERE LOWER(city) = LOWER(?)',
        (city,)
    ).fetchone()
    
    if cache:
        cached_time = datetime.strptime(cache['cached_at'], '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - cached_time).seconds < CACHE_DURATION:
            return {
                'weather': json.loads(cache['weather_data']),
                'forecast': json.loads(cache['forecast_data']),
                'latitude': cache['latitude'],
                'longitude': cache['longitude']
            }
    return None

def cache_weather(city, weather, forecast, lat, lon):
    """Cache weather data in database."""
    db = get_db()
    db.execute(
        '''INSERT OR REPLACE INTO weather_cache 
           (city, latitude, longitude, weather_data, forecast_data, cached_at) 
           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
        (city, lat, lon, json.dumps(weather), json.dumps(forecast))
    )
    db.commit()

def get_weather_data(city):
    """Fetch weather data from OpenWeatherMap API."""
    try:
        # Check cache first
        cached = get_cached_weather(city)
        if cached:
            return cached
        
        # Current weather
        current_url = f"{OPENWEATHER_BASE_URL}/weather"
        current_params = {
            'q': city,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        current_response = requests.get(current_url, params=current_params, timeout=5)
        
        if current_response.status_code != 200:
            return {'error': 'City not found'}
        
        current_data = current_response.json()
        lat = current_data['coord']['lat']
        lon = current_data['coord']['lon']
        
        # Forecast
        forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
        forecast_params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        forecast_response = requests.get(forecast_url, params=forecast_params, timeout=5)
        forecast_data = forecast_response.json() if forecast_response.status_code == 200 else {}
        
        # One Call API (includes UV index, alerts, etc.)
        onecall_url = f"{OPENWEATHER_BASE_URL}/onecall"
        onecall_params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'exclude': 'minutely'
        }
        onecall_response = requests.get(onecall_url, params=onecall_params, timeout=5)
        onecall_data = onecall_response.json() if onecall_response.status_code == 200 else {}
        
        result = {
            'weather': {
                'current': current_data,
                'onecall': onecall_data
            },
            'forecast': forecast_data,
            'latitude': lat,
            'longitude': lon
        }
        
        # Cache the result
        cache_weather(city, result['weather'], result['forecast'], lat, lon)
        
        return result
    
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout. Please try again.'}
    except requests.exceptions.RequestException as e:
        return {'error': f'API Error: {str(e)}'}
    except Exception as e:
        return {'error': f'Error fetching weather: {str(e)}'}

def get_user_preferences(user_id):
    """Get user weather preferences."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return {
        'temperature_unit': user['temperature_unit'] if user else 'C'
    }

@app.route('/')
def home():
    """Home page."""
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('weather_home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect('/signup')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect('/signup')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect('/signup')
        
        db = get_db()
        try:
            pwd_hash = generate_password_hash(password)
            db.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, pwd_hash)
            )
            db.commit()
            flash('Account created! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
            return redirect('/signup')
    
    return render_template('weather_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password required.', 'danger')
            return redirect('/login')
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect('/dashboard')
        
        flash('Invalid username or password.', 'danger')
        return redirect('/login')
    
    return render_template('weather_login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Weather dashboard."""
    db = get_db()
    user_id = session['user_id']
    
    # Get favorites
    favorites = db.execute(
        'SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    
    # Get recent searches
    recent = db.execute(
        'SELECT DISTINCT city FROM search_history WHERE user_id = ? ORDER BY searched_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()
    
    # Get user preferences
    prefs = get_user_preferences(user_id)
    
    return render_template(
        'weather_dashboard.html',
        favorites=favorites,
        recent_searches=recent,
        temp_unit=prefs['temperature_unit']
    )

@app.route('/api/weather/<city>')
@login_required
def get_weather(city):
    """API endpoint to get weather for a city."""
    user_id = session['user_id']
    
    # Record search history
    db = get_db()
    weather_data = get_weather_data(city)
    
    if 'error' not in weather_data:
        db.execute(
            '''INSERT INTO search_history (user_id, city, latitude, longitude) 
               VALUES (?, ?, ?, ?)''',
            (user_id, city, weather_data['latitude'], weather_data['longitude'])
        )
        db.commit()
    
    return jsonify(weather_data)

@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_favorites():
    """Manage favorite cities."""
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'GET':
        favorites = db.execute(
            'SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        return jsonify([dict(fav) for fav in favorites])
    
    elif request.method == 'POST':
        data = request.get_json()
        city = data.get('city')
        
        if not city:
            return jsonify({'error': 'City name required'}), 400
        
        # Get coordinates from weather API
        weather_data = get_weather_data(city)
        if 'error' in weather_data:
            return jsonify(weather_data), 400
        
        try:
            db.execute(
                '''INSERT INTO favorites (user_id, city, latitude, longitude) 
                   VALUES (?, ?, ?, ?)''',
                (user_id, city, weather_data['latitude'], weather_data['longitude'])
            )
            db.commit()
            return jsonify({'success': True, 'message': f'{city} added to favorites'})
        except sqlite3.IntegrityError:
            return jsonify({'error': f'{city} is already in favorites'}), 400
    
    elif request.method == 'DELETE':
        city = request.args.get('city')
        if not city:
            return jsonify({'error': 'City name required'}), 400
        
        db.execute(
            'DELETE FROM favorites WHERE user_id = ? AND city = ?',
            (user_id, city)
        )
        db.commit()
        return jsonify({'success': True, 'message': f'{city} removed from favorites'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/api/alerts', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_alerts():
    """Manage weather alerts."""
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'GET':
        alerts = db.execute(
            'SELECT * FROM alerts WHERE user_id = ? AND is_active = 1',
            (user_id,)
        ).fetchall()
        return jsonify([dict(alert) for alert in alerts])
    
    elif request.method == 'POST':
        data = request.get_json()
        city = data.get('city')
        alert_type = data.get('alert_type')  # 'temperature', 'wind', 'rain'
        threshold = data.get('threshold')
        
        if not all([city, alert_type, threshold]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            db.execute(
                '''INSERT INTO alerts (user_id, city, alert_type, threshold) 
                   VALUES (?, ?, ?, ?)''',
                (user_id, city, alert_type, threshold)
            )
            db.commit()
            return jsonify({'success': True, 'message': 'Alert created'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        alert_id = request.args.get('id')
        if not alert_id:
            return jsonify({'error': 'Alert ID required'}), 400
        
        db.execute(
            'UPDATE alerts SET is_active = 0 WHERE id = ? AND user_id = ?',
            (alert_id, user_id)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Alert deleted'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/api/preferences', methods=['GET', 'POST'])
@login_required
def manage_preferences():
    """Manage user preferences."""
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'GET':
        prefs = get_user_preferences(user_id)
        return jsonify(prefs)
    
    elif request.method == 'POST':
        data = request.get_json()
        temp_unit = data.get('temperature_unit', 'C')
        
        if temp_unit not in ['C', 'F']:
            return jsonify({'error': 'Invalid temperature unit'}), 400
        
        db.execute(
            'UPDATE users SET temperature_unit = ? WHERE id = ?',
            (temp_unit, user_id)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Preferences updated'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=os.environ.get('FLASK_DEBUG', True))
