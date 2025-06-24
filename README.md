Flask Dark Souls Shop

A simple e-commerce web application built with Flask, featuring user authentication, product categories, shopping cart, and Stripe payment integration. Inspired by Dark Souls aesthetics and designed as a practice project.
Features

    User registration and login with password hashing

    Product browsing by category and subcategory

    Shopping cart with add, remove, and quantity update functionality

    Checkout page with Stripe payment processing

    Order confirmation and saving orders to a JSON file

    Responsive design with Dark Souls-inspired fonts and styles

Technologies Used

    Python 3

    Flask

    Flask-Login

    Flask-SQLAlchemy

    Stripe API

    SQLite (for user data)

    HTML/CSS with Bootstrap

    dotenv for environment variable management

Getting Started
Prerequisites

    Python 3.7+ installed

    pip package manager

    Stripe account and API keys (Get API keys here: https://dashboard.stripe.com/apikeys)

Installation

1. Clone the repository:

git clone https://github.com/yourusername/flask-dark-souls-shop.git
cd flask-dark-souls-shop

2. Create and activate a virtual environment (optional but recommended):

On Linux/macOS: python -m venv venv then source venv/bin/activate
On Windows: python -m venv venv then venv\Scripts\activate

3. Install dependencies:

pip install -r requirements.txt

4. Create a .env file in the project root with your secrets:

FLASK_SECRET_KEY=your_flask_secret_key_here
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

5. Initialize the database:

Run flask shell then:

from app import db
db.create_all()
exit()

6. Run the application:

flask run

7. Open your browser and visit http://127.0.0.1:5000

Usage

    Register a new user or login

    Browse categories and subcategories of items

    Add items to your cart and adjust quantities

    Proceed to checkout and pay via Stripe

    After payment, your cart is cleared and order saved

Project Structure

flask-dark-souls-shop/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── data/
│   └── items.json          # Product data
└── orders.json             # Saved orders (appended on checkout)

Notes

    This project is for educational purposes and is not production-ready.

    Make sure to keep your .env file private and never commit secrets to public repos.

    Stripe keys used in .env should be your test keys during development.

    You can customize products by editing data/items.json.

    The checkout page includes a basic client-side validation; additional validation and security checks are recommended for production.

License

MIT License © Pitfall
Acknowledgements

    Inspired by the Dark Souls game aesthetics

    Uses Stripe API (https://stripe.com/docs/payments/checkout) for payments

    Built with Flask and Bootstrap

If you have questions or suggestions, feel free to open an issue or submit a pull request. Enjoy the journey through your own Dark Souls shop! 🗡️🔥



