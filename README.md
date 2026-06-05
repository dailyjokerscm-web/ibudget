# iBudget - Your Money Coach 💰

A modern, secure Flask web application to help you plan your finances, track expenses, and achieve your financial goals.

## ✨ Features

- **User Authentication**: Secure signup and login with password hashing
- **Budget Planning**: Create monthly budgets and track income vs expenses
- **Goal Setting**: Set financial goals with deadlines and track progress
- **Expense Tracking**: Categorize and monitor all your spending
- **Smart Recommendations**: Get personalized advice on cutting expenses
- **Dashboard**: View statistics, goals, and expense history
- **Responsive Design**: Beautiful UI that works on all devices

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Security**: Werkzeug password hashing
- **Frontend**: HTML5 with modern CSS3

## 📋 Prerequisites

- Python 3.7+
- pip (Python package manager)

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone https://github.com/dailyjokerscm-web/ibudget.git
cd ibudget
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 📱 Running the Application

1. **Start the Flask server**:
```bash
python ibudget.py
```

2. **Open your browser**:
```
http://localhost:5000
```

## 💡 Usage Guide

### Create Account
1. Click "Sign Up"
2. Enter username (3-20 chars, alphanumeric)
3. Enter email address
4. Create a password (min 6 chars)
5. Confirm password

### Login
1. Enter your username
2. Enter your password
3. Click "Login"

### Create Budget Plan
1. Go to Dashboard
2. Enter your monthly income
3. Enter expenses by category:
   - Rent
   - Food
   - Transport
   - Entertainment
   - Utilities
   - Other
4. Set your savings goal and deadline
5. Click "Calculate Plan"
6. Get personalized recommendations!

### View History
- Click "View History" to see all past expenses
- All expenses are categorized and timestamped

### Track Goals
- Click "All Goals" to see your financial targets
- View progress bars for each goal
- See deadline information

## 📊 Database Schema

### users
- id: Integer (Primary Key)
- username: Text (Unique)
- email: Text (Unique)
- password_hash: Text
- created_at: Timestamp

### expenses
- id: Integer (Primary Key)
- user_id: Integer (Foreign Key)
- category: Text
- amount: Real
- description: Text
- date: Timestamp

### goals
- id: Integer (Primary Key)
- user_id: Integer (Foreign Key)
- goal_name: Text
- target_amount: Real
- current_amount: Real
- deadline: Text
- created_at: Timestamp

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Input validation
- SQL injection prevention with parameterized queries
- Email validation
- Username format validation

## 🎨 UI/UX Improvements

- Modern gradient design
- Responsive grid layout
- Interactive forms with validation
- Flash messages for user feedback
- Progress bars for goal tracking
- Intuitive navigation
- Mobile-friendly interface

## 📝 Project Structure

```
ibudget/
├── ibudget.py              # Main Flask application
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── home.html          # Home page
│   ├── signup.html        # Registration page
│   ├── login.html         # Login page
│   ├── dashboard.html     # Main dashboard
│   ├── history.html       # Expense history
│   └── goals.html         # Goals page
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore file
└── README.md              # This file
```

## 🚀 Deployment

### Using Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 ibudget:app
```

### Using Heroku
1. Create `Procfile`:
```
web: gunicorn ibudget:app
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

## 📈 Future Enhancements

- [ ] Charts and visualizations
- [ ] Budget alerts and notifications
- [ ] Income tracking
- [ ] Recurring expenses
- [ ] Export to PDF/CSV
- [ ] Mobile app
- [ ] Multi-currency support
- [ ] Advanced analytics

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

Developed with ❤️ for better financial management

## 📞 Support

For issues or questions, please open a GitHub issue.
