from flask import Flask, render_template, request, redirect, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
DATABASE = 'ibudget.db'

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
        CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
        ''')
        db.commit()

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format."""
    if len(username) < 3 or len(username) > 20:
        return False
    return re.match(r'^[a-zA-Z0-9_-]+$', username) is not None

def calculate_plan(income, expenses, target, deadline_str):
    """Calculate savings plan and provide recommendations."""
    try:
        monthly_save = income - expenses
        if monthly_save <= 0:
            return {
                'status': 'warning',
                'message': '⚠️ You spend more than you earn. Cut expenses first.',
                'months_to_goal': None
            }
        
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        today = datetime.now()
        
        if deadline <= today:
            return {
                'status': 'error',
                'message': '❌ Deadline already passed. Pick a future date.',
                'months_to_goal': None
            }
        
        months_left = (deadline.year - today.year) * 12 + (deadline.month - today.month)
        needed_monthly = target / months_left
        shortfall = needed_monthly - monthly_save
        
        if shortfall <= 0:
            months_to_goal = int(target / monthly_save) if monthly_save > 0 else 0
            return {
                'status': 'success',
                'message': f'✅ On track! Save R{monthly_save:.2f}/month. Hit R{target:.2f} in {months_to_goal} months',
                'months_to_goal': months_to_goal,
                'monthly_save': monthly_save
            }
        else:
            extra_months = int(shortfall * months_left / monthly_save) if monthly_save > 0 else 0
            return {
                'status': 'shortfall',
                'message': f'⚡ Shortfall: R{shortfall:.2f}/month needed. Cut expenses or extend deadline by ~{extra_months} months',
                'shortfall': shortfall,
                'extra_months': extra_months,
                'months_to_goal': months_left
            }
    except ValueError:
        return {
            'status': 'error',
            'message': '❌ Invalid date format. Use YYYY-MM-DD.',
            'months_to_goal': None
        }

def get_cutting_advice(expenses_dict, shortfall):
    """Generate cutting advice based on expenses and shortfall."""
    advice = []
    sorted_exp = sorted(expenses_dict.items(), key=lambda x: x[1], reverse=True)
    remaining = shortfall
    
    for cat, amt in sorted_exp:
        if remaining <= 0:
            break
        if amt > 0:
            cut = min(amt * 0.15, remaining)
            if cut > 25:
                advice.append(f'💰 Cut R{cut:.0f} from {cat.title()} (currently R{amt:.2f})')
                remaining -= cut
    
    if not advice:
        advice.append('📊 All expenses look tight. Consider increasing income or extending deadline.')
    
    return advice

def get_user_stats(user_id):
    """Get user statistics."""
    db = get_db()
    
    total_expenses = db.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE user_id = ?',
        (user_id,)
    ).fetchone()['total'] or 0
    
    active_goals = db.execute(
        'SELECT COUNT(*) as count FROM goals WHERE user_id = ? AND deadline > ?',
        (user_id, datetime.now().strftime('%Y-%m-%d'))
    ).fetchone()['count']
    
    return {
        'total_expenses': total_expenses,
        'active_goals': active_goals
    }

@app.route('/')
def home():
    """Home page."""
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect('/signup')
        
        if not validate_username(username):
            flash('Username must be 3-20 characters, alphanumeric with hyphens/underscores.', 'danger')
            return redirect('/signup')
        
        if not validate_email(email):
            flash('Invalid email format.', 'danger')
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
            flash('Account created successfully! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                flash('Username already exists.', 'danger')
            elif 'email' in str(e):
                flash('Email already registered.', 'danger')
            else:
                flash('Registration failed. Try again.', 'danger')
            return redirect('/signup')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password required.', 'danger')
            return redirect('/login')
        
        db = get_db()
        user = db.execute(
            'SELECT id, password_hash FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect('/dashboard')
        
        flash('Invalid username or password.', 'danger')
        return redirect('/login')
    
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """User dashboard."""
    db = get_db()
    user_id = session['user_id']
    result = None
    advice_list = []
    
    if request.method == 'POST':
        try:
            income = float(request.form.get('income', 0))
            target = float(request.form.get('target', 0))
            deadline = request.form.get('deadline', '')
            
            if income <= 0 or target <= 0:
                flash('Income and target must be positive numbers.', 'danger')
                return redirect('/dashboard')
            
            categories = ['rent', 'food', 'transport', 'entertainment', 'utilities', 'other']
            total_expenses = 0
            expenses_dict = {}
            
            for cat in categories:
                amt = float(request.form.get(cat, 0))
                if amt < 0:
                    flash(f'{cat.title()} cannot be negative.', 'danger')
                    return redirect('/dashboard')
                expenses_dict[cat] = amt
                total_expenses += amt
                if amt > 0:
                    db.execute(
                        'INSERT INTO expenses (user_id, category, amount) VALUES (?, ?, ?)',
                        (user_id, cat, amt)
                    )
            
            db.execute(
                'INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)',
                (user_id, 'Monthly Goal', target, deadline)
            )
            db.commit()
            
            result = calculate_plan(income, total_expenses, target, deadline)
            
            if result['status'] in ['shortfall', 'warning']:
                monthly_save = income - total_expenses
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
                today = datetime.now()
                months_left = (deadline_dt.year - today.year) * 12 + (deadline_dt.month - today.month)
                if months_left > 0:
                    needed_monthly = target / months_left
                    shortfall = needed_monthly - monthly_save
                    if shortfall > 0:
                        advice_list = get_cutting_advice(expenses_dict, shortfall)
            
            if result['status'] == 'success':
                flash('Plan calculated successfully!', 'success')
            
        except ValueError:
            flash('Please enter valid numbers.', 'danger')
            return redirect('/dashboard')
    
    # Get user stats
    stats = get_user_stats(user_id)
    
    # Get recent goals
    recent_goals = db.execute(
        'SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()
    
    return render_template('dashboard.html', result=result, advice=advice_list, stats=stats, goals=recent_goals)

@app.route('/history')
@login_required
def history():
    """View expense history."""
    db = get_db()
    user_id = session['user_id']
    
    expenses = db.execute(
        'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC',
        (user_id,)
    ).fetchall()
    
    return render_template('history.html', expenses=expenses)

@app.route('/goals')
@login_required
def goals():
    """View all goals."""
    db = get_db()
    user_id = session['user_id']
    
    goals = db.execute(
        'SELECT * FROM goals WHERE user_id = ? ORDER BY deadline ASC',
        (user_id,)
    ).fetchall()
    
    return render_template('goals.html', goals=goals)

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=os.environ.get('FLASK_DEBUG', True))
