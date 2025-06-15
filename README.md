# ALX Travel App 

A comprehensive Django REST API for travel booking and accommodation management, similar to Airbnb. This application provides a complete backend solution for managing property listings, bookings, reviews, and user interactions.

## Features

- **Property Listings Management**: Create, update, and manage accommodation listings
- **Booking System**: Handle reservations with date validation and pricing
- **Review & Rating System**: User reviews and ratings for properties
- **User Management**: Authentication and user profiles
- **RESTful API**: Comprehensive API endpoints for all operations
- **Database Seeding**: Automated sample data generation
- **PostgreSQL Integration**: Production-ready database configuration

## Tech Stack

- **Backend**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Django's built-in authentication + Token Authentication
- **Environment Management**: python-dotenv
- **API Documentation**: Django REST Framework Browsable API

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alx_travel_app_0x00
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install django djangorestframework psycopg2-binary python-dotenv django-cors-headers
```

### 4. Database Setup

#### Create PostgreSQL Database

```bash

sudo -u postgres psql

CREATE DATABASE alx_travel_app_db;
CREATE USER travel_app_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE alx_travel_app_db TO travel_app_user;
ALTER USER travel_app_user CREATEDB;
\q
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=alx_travel_app_db
DB_USER=travel_app_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Database Migration

```bash

python manage.py makemigrations

python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```


```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/admin/` for admin interface

## Database Models

### Listing Model
- Property details (title, description, location)
- Pricing and capacity information
- Property type and amenities
- Host relationship
- Availability status

### Booking Model
- Reservation details (dates, guests)
- Pricing calculations
- Status tracking (pending, confirmed, cancelled, completed)
- Guest and listing relationships

### Review Model
- Rating system (1-5 stars)
- User comments and feedback
- Relationship to bookings and listings

## API Endpoints

The application provides RESTful API endpoints for:

- **Listings**: CRUD operations for property listings
- **Bookings**: Reservation management
- **Reviews**: Rating and review system
- **Users**: User management and authentication

### Example API Usage

```python
NB: JWT required in Authorization header: Bearer <token> 

GET /api/v1/listings/
{
    'title': 'New Test Listing',
    'description': 'A new test listing description',
    'location': 'New Test City',
    'property_type': 'house',
    'price_per_night': '150.00',
    'max_guests': 6,
    'number_of_bedrooms': 3,
    'number_of_bathrooms': 2,
    'amenities': 'WiFi, Kitchen, TV, Pool',
    'house_rules': 'No smoking, No pets',
    'latitude': 41.8781,
    'longitude': -87.6298,
    'availability': True,
    'instant_book': True
}

POST /api/bookings/
{
    "listing_id": 1,
    "check_in_date": "2024-07-01",
    "check_out_date": "2024-07-05",
    "number_of_guests": 2
}

POST /api/reviews/
{
    "listing": 1,
    "rating": 5,
    "comment": "Amazing place!"
}
```

## Management Commands

### Seed Command Options

```bash

python manage.py seed
python manage.py seed --listings 10 --bookings 25 --reviews 15
python manage.py seed --clear
python manage.py seed --help
```

## Project Structure

```
alx_travel_app_0x01/
├── alx_travel_app/          # Main project directory
│   ├── settings.py          # Django settings
│   ├── urls.py             # URL configuration
│   └── wsgi.py             # WSGI configuration
├── listings/               # Main app directory
│   ├── models.py           # Database models
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views
│   ├── management/
│   │   └── commands/
│   │       └── seed.py     # Database seeding command
│   └── migrations/         # Database migrations
├── static/                 # Static files
├── media/                  # Media files
├── logs/                   # Log files
├── .env                    # Environment variables
├── manage.py              # Django management script
└── README.md              # This file
```

## Testing

### Test Database Connection

```python
python manage.py shell

from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

### Verify Seeded Data

```python
python manage.py shell

from listings.models import Listing, Booking, Review
from django.contrib.auth.models import User

print(f"Users: {User.objects.count()}")
print(f"Listings: {Listing.objects.count()}")
print(f"Bookings: {Booking.objects.count()}")
print(f"Reviews: {Review.objects.count()}")
```

## Security Features

- Environment variable configuration
- Database connection security
- CORS handling
- Authentication required for API endpoints
- Input validation and sanitization
- SQL injection protection through Django ORM

## Deployment

### Environment Variables for Production

```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Static Files

```bash
python manage.py collectstatic
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database exists

2. **Migration Issues**
   ```bash
   # Reset migrations if needed
   python manage.py migrate --fake-initial
   ```

3. **Permission Errors**
   ```sql
   # Grant additional PostgreSQL permissions
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO travel_app_user;
   ```

4. **Import Errors**
   - Ensure all dependencies are installed
   - Check virtual environment is activated


---

**ALX Travel App** - Making travel booking simple and efficient!