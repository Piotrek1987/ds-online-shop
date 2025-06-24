from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json
from datetime import datetime
import os
from collections import defaultdict
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_fallback_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy in-memory user store
users = {}

# Load item data from JSON
with open('data/items.json') as f:
    all_items = json.load(f)

# Helper: get item by ID
def get_item_by_id(item_id):
    return next((item for item in all_items if item['id'] == item_id), None)

def add_item_to_cart(item_id):
    cart = session.get('cart', {})
    cart[str(item_id)] = cart.get(str(item_id), 0) + 1
    session['cart'] = cart

def remove_item_from_cart(item_id):
    cart = session.get('cart', {})
    if str(item_id) in cart:
        del cart[str(item_id)]
        session['cart'] = cart


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Load items from file
def load_items():
    with open('data/items.json') as f:
        return json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/category/<category>')
def category_view(category):
    all_items = load_items()
    subcategories = defaultdict(list)
    uncategorized_items = []

    for item in all_items:
        if item['category'].lower() == category.lower():
            if item['subcategory'] and item['subcategory'] != '.':
                subcategories[item['subcategory']].append(item)
            else:
                uncategorized_items.append(item)

    # 🟡 If there are no subcategories, redirect directly to 'category_all_items'
    if not subcategories:
        return redirect(url_for('category_all_items', category=category.lower()))

    return render_template('category.html',
                           category=category.title(),
                           subcategories=subcategories,
                           uncategorized_items=uncategorized_items)



@app.route('/category/<category_name>/<subcategory_name>')
def subcategory_view(category_name, subcategory_name):
    all_items = load_items()
    filtered_items = [
        item for item in all_items
        if item['category'].lower() == category_name.lower()
        and item['subcategory'].lower() == subcategory_name.lower()
    ]

    if not filtered_items:
        return "Subcategory not found", 404

    return render_template('subcategory.html',
                           category_name=category_name,  # raw for URL building
                           subcategory_name=subcategory_name,  # raw for URL building
                           category=category_name.title(),  # for display
                           subcategory=subcategory_name.title(),  # for display
                           items=filtered_items)

@app.route('/category/<category>/all')
def category_all_items(category):
    all_items = load_items()
    items = [item for item in all_items if item['category'].lower() == category.lower()]

    if not items:
        return "No items found in this category", 404

    return render_template('category_all_items.html',
                           category=category.title(),
                           items=items)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    items = load_items()
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return "Item not found", 404
    return render_template('item_detail.html', item=item)

# Auth
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        user = User(email=email, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('index'))
        flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

# Cart
@app.route('/add_to_cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item = get_item_by_id(item_id)
    if not item:
        flash("Item not found.")
        return redirect(url_for('index'))

    cart = session.get('cart', {})
    item_id_str = str(item_id)
    cart[item_id_str] = cart.get(item_id_str, 0) + 1
    session['cart'] = cart

    flash(f"{item['name']} added to cart!")
    return redirect(request.referrer or url_for('index'))



@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0

    for item_id, quantity in cart.items():
        item = get_item_by_id(int(item_id))
        if item:
            item_copy = item.copy()
            item_copy['quantity'] = quantity
            item_copy['subtotal'] = quantity * item['price']
            items.append(item_copy)
            total += item_copy['subtotal']

    return render_template('cart.html', items=items, total=total)


@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        cart[item_id_str] -= 1
        if cart[item_id_str] <= 0:
            del cart[item_id_str]
        session['cart'] = cart
        flash("Item updated in cart.")
    else:
        flash("Item not in cart.")
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('cart'))

    items = []
    total = 0
    for item_id, quantity in cart.items():
        item = get_item_by_id(int(item_id))
        if item:
            item_copy = item.copy()
            item_copy['quantity'] = quantity
            item_copy['subtotal'] = quantity * item['price']
            items.append(item_copy)
            total += item_copy['subtotal']

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        card = request.form['card']

        if len(card) != 16 or not card.isdigit():
            flash("Invalid card number.")
            return render_template('checkout.html', items=items, total=total)

        # 🔽 INSERT THIS BLOCK RIGHT HERE:
        import random
        success = random.random() < 0.85
        if not success:
            flash("Payment was declined! Please try again.")
            return render_template('checkout.html', items=items, total=total)

        # ✅ Then continue with saving the order
        order = {
            "order_id": str(uuid.uuid4())[:8],
            "user": current_user.username,
            "email": email,
            "address": address,
            "datetime": datetime.now().isoformat(),
            "items": items,
            "total": total
        }

        with open("orders.json", "a") as f:
            f.write(json.dumps(order) + "\n")

        session['cart'] = {}
        flash("Payment successful! Order confirmed.")
        return redirect(url_for('index'))

    return render_template('checkout.html', items=items, total=total)


@app.route('/update_cart/<int:item_id>/<action>')
@login_required
def update_cart(item_id, action):
    cart = session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        if action == 'increase':
            cart[item_id_str] += 1
        elif action == 'decrease':
            cart[item_id_str] -= 1
            if cart[item_id_str] <= 0:
                del cart[item_id_str]
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('cart'))

    line_items = []
    for item_id, quantity in cart.items():
        item = get_item_by_id(int(item_id))
        if item:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': item['price'],  # price in cents
                    'product_data': {
                        'name': item['name'],
                        'description': item['description'],
                    },
                },
                'quantity': quantity,
            })

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('checkout_success', _external=True),
            cancel_url=url_for('cart', _external=True),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Payment error: {str(e)}")
        return redirect(url_for('cart'))

@app.route('/checkout/success')
@login_required
def checkout_success():
    session['cart'] = {}  # Clear the cart
    flash("Payment successful! Thank you for your order.")
    return render_template('checkout_success.html')



with app.app_context():
    db.create_all()

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
