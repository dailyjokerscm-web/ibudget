# Weather Dashboard 🌤️

A modern, responsive Flask web application for real-time weather tracking using the OpenWeatherMap API.

## ✨ Features

### Current Weather
- Real-time temperature, humidity, wind speed
- Weather conditions and descriptions
- "Feels like" temperature
- UV index and visibility
- Pressure readings

### 5-Day Forecast
- Daily weather predictions
- Temperature trends
- Weather icons and descriptions
- Hourly breakdowns (if available)

### Favorites & Bookmarks
- Save favorite cities
- Quick access to frequently checked locations
- Search history tracking

### Weather Alerts
- Set custom temperature alerts
- Wind speed notifications
- Precipitation warnings
- Manage multiple alerts

### User Accounts
- Secure authentication
- Persistent favorites
- Custom preferences (Celsius/Fahrenheit)
- Search history

### Responsive Design
- Mobile-friendly interface
- Modern gradient UI
- Smooth animations
- Touch-optimized buttons

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **API**: OpenWeatherMap API (Free tier)
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Security**: Werkzeug password hashing, session management

## 📋 Prerequisites

- Python 3.7+
- OpenWeatherMap API key (free at https://openweathermap.org/api)
- pip (Python package manager)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/weather-dashboard.git
cd weather-dashboard
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create .env File
Create a `.env` file in the project root:
```
OPENWEATHER_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=True
```

### 5. Run the Application
```bash
python weather_app.py
```

Open your browser: `http://localhost:5000`

## 📱 Usage

### Sign Up
1. Click "Sign Up"
2. Enter username, email, and password
3. Click "Create Account"

### Login
1. Enter your credentials
2. Click "Login"

### Search Weather
1. Enter a city name in the search box
2. Press Enter or click the search button
3. View current conditions and 5-day forecast

### Add Favorites
1. Search for a city
2. Click "⭐ Add to Favorites"
3. Access from the Favorites tab anytime

### Create Alerts
1. Go to the Alerts tab
2. Enter city name
3. Select alert type (Temperature, Wind, Precipitation)
4. Set threshold value
5. Click "Create Alert"

### Change Temperature Unit
- Use the °C/°F toggle in the top right
- Automatically converts all temperatures

## 🗄️ Database Schema

### users
- id: Primary Key
- username: Unique username
- email: Unique email
- password_hash: Hashed password
- temperature_unit: User's preferred unit (C/F)
- created_at: Account creation timestamp

### favorites
- id: Primary Key
- user_id: Foreign Key (users)
- city: City name
- latitude/longitude: Geographic coordinates
- created_at: When added to favorites

### search_history
- id: Primary Key
- user_id: Foreign Key (users)
- city: Searched city
- latitude/longitude: Coordinates
- searched_at: Search timestamp

### alerts
- id: Primary Key
- user_id: Foreign Key (users)
- city: Alert location
- alert_type: Type (temperature, wind, rain)
- threshold: Alert value
- is_active: Alert status
- created_at: Creation timestamp

### weather_cache
- id: Primary Key
- city: City name (unique)
- weather_data: Current conditions JSON
- forecast_data: Forecast JSON
- cached_at: Cache timestamp

## 🔌 API Endpoints

### Weather
- `GET /api/weather/<city>` - Get weather for city

### Favorites
- `GET /api/favorites` - List favorites
- `POST /api/favorites` - Add favorite
- `DELETE /api/favorites?city=<name>` - Remove favorite

### Alerts
- `GET /api/alerts` - List active alerts
- `POST /api/alerts` - Create alert
- `DELETE /api/alerts?id=<id>` - Delete alert

### Preferences
- `GET /api/preferences` - Get user preferences
- `POST /api/preferences` - Update preferences

## 🎨 Customization

### Change Colors
Edit the gradient in `weather_base.html`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Add More Weather Data
Modify `displayCurrentWeather()` in `weather_dashboard.html` to show additional metrics.

### Adjust Cache Duration
In `weather_app.py`, change:
```python
CACHE_DURATION = 600  # 10 minutes
```

## 🚀 Deployment

### Heroku
1. Create `Procfile`:
```
web: gunicorn weather_app:app
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

3. Set environment variables:
```bash
heroku config:set OPENWEATHER_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret
```

### PythonAnywhere
1. Upload files
2. Create virtual environment
3. Install dependencies
4. Configure web app settings
5. Add environment variables

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- SQL injection prevention
- CSRF protection ready
- Input validation
- Rate limiting ready (easily addable)

## 🐛 Troubleshooting

### "City not found"
- Ensure city name is spelled correctly
- Try with country code (e.g., "London, UK")

### "API Key error"
- Verify API key in .env file
- Check OpenWeatherMap account status
- Ensure key has correct permissions

### "No forecast data"
- Free tier may have limitations
- Try with major cities first
- Check API quota usage

## 📚 Future Enhancements

- [ ] Map integration
- [ ] Weather notifications/push alerts
- [ ] Historical data tracking
- [ ] Weather comparison between cities
- [ ] Weather trends/analytics
- [ ] Mobile app version
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Air quality index
- [ ] Pollen count tracking

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📞 Support

For issues:
1. Check existing GitHub issues
2. Create detailed bug report
3. Include steps to reproduce
4. Attach screenshots if applicable

## 🙏 Credits

- OpenWeatherMap API
- Flask framework
- Weather icons from Emoji

---

**Built with ❤️ for weather enthusiasts**
