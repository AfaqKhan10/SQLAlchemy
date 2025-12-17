from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Order, Product
from exceptions import *
from fastapi.security import OAuth2PasswordRequestForm
from auth import hash_password, verify_password, create_access_token, get_current_user
# Rate Limiting ke liye imports
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request



app = FastAPI()


# Rate Limiting setup – spam rokne ke liye
limiter = Limiter(key_func=get_remote_address)  # IP address se track karega
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: ({"detail": "Bhai thoda wait kar lo – bohot tezi se requests bhej rahe ho!"}, 429))

# -------------------------
#   CREATE ENDPOINTS
# -------------------------


# ➤ Create order
@app.post("/orders")
def create_order(item: str, user_id: int, db: Session = Depends(get_db)):
    order = Order(item=item, user_id=user_id)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# ➤ Get user + orders (relationship example)
@app.get("/users/{user_id}/details")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound()                    # ← ab custom exception chalega
    return {
        "id": user.id,
        "name": user.name,
        "orders": [o.item for o in user.orders]
    }

# -------------------------
#       QUERIES SECTION
# -------------------------

# ➤ Fetch all users
@app.get("/users")
def fetch_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]

# ➤ Fetch single user by id
@app.get("/users/{user_id}")
def fetch_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound()                    # ← custom exception
    return {"id": user.id, "name": user.name, "email": user.email}

# ➤ Fetch orders of a user (relationship)
@app.get("/users/{user_id}/orders")
def fetch_user_orders(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound()                    # ← custom exception
    return {
        "user": user.name,
        "orders": [o.item for o in user.orders]
    }

# ➤ Fetch all orders sorted
@app.get("/orders")
def fetch_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.item).all()
    return [{"id": o.id, "item": o.item, "user_id": o.user_id} for o in orders]


# ➤ Fetch orders by order id
@app.get("/orders/{order_id}")
def get_single_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise OrderNotFound()          # ← Ye chalega
    return {"order_id": order.id, "item": order.item}



# -------------------------
#   TRANSACTION PRACTICE
# -------------------------

# ➤ Example: Create user + multiple orders in a transaction
@app.post("/users/transaction")
def create_user_with_orders(name: str, email: str, items: list[str], db: Session = Depends(get_db)):
    try:
        # Start transaction
        user = User(name=name, email=email)
        db.add(user)
        db.flush()  # flush → assign ID before committing

        for item_name in items:
            order = Order(item=item_name, user_id=user.id)
            db.add(order)
        
        db.commit()  # Commit everything together
        db.refresh(user)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "orders": items
        }

    except Exception as e:
        db.rollback()  # rollback in case of error
        raise ValidationException("Transaction failed")   # ← custom exception

# -------------------------
#   MANY-TO-MANY (Order + Products)
# -------------------------

# ← YE LINE ADD KARNA MAT BHULNA
@app.post("/users/{user_id}/orders")
def create_order_with_products(
    user_id: int,
    products: list[str],
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)
    if not user:
        raise UserNotFound()                    # ← custom exception

    new_order = Order(item="Cloths Order", user_id=user_id)
    db.add(new_order)
    db.flush()

    for name in products:
        product = db.query(Product).filter(Product.name == name).first()
        if not product:
            product = Product(name=name)
            db.add(product)
            db.flush()
        new_order.products.append(product)

    db.commit()
    return {"message": "Order Done", "products": products}

@app.get("/users/{user_id}/orders-with-products")
def get_user_orders_with_products(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound()                    # ← custom exception
    
    orders_list = []
    for order in user.orders:
        orders_list.append({
            "order_id": order.id,
            "created_for": order.item,           # ye ab "Food Order" dikhega
            "products": [p.name for p in order.products]   # ← YAHAN ASLI PRODUCTS DIKHENGE
        })
    
    return {
        "user": user.name,
        "total_orders": len(orders_list),
        "orders": orders_list
    }


# Test endpoint – ProductNotFound exception check karne ke liye
@app.get("/products/{product_name}")
def get_product_by_name(product_name: str, db: Session = Depends(get_db)):
    """
    Test endpoint to verify ProductNotFound custom exception
    Returns product if exists, otherwise raises ProductNotFound
    """
    product = db.query(Product).filter(Product.name == product_name).first()
    
    if not product:
        raise ProductNotFound()        # Triggers → {"error": true, "message": "Product not found"}
    
    return {
        "id": product.id,
        "name": product.name,
        "message": "Product Founded Successfully"
    }




# ➤ Register – naya user banaye with password hashing
@app.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):
    # Email already hai ya nahi check karo
    if db.query(User).filter(User.email == email).first():
        raise ValidationException("Email already registered")
    
    # Password ko hash karo
    hashed = hash_password(password)
    
    new_user = User(name=name, email=email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}




# ➤ Login – JWT token dega (rate limited – 1 minute mein sirf 5 try)
@app.post("/login")
@limiter.limit("3/minute")   # ← ye decorator rakh
def login(
    request: Request,   # ← YE LINE ADD KAR DE (ye slowapi ke liye zaroori hai)
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AuthException()
    
    token = create_access_token(user=user)
    
    return {"access_token": token, "token_type": "bearer"}



# ➤ Protected route – sirf logged-in user dekh sakega
@app.get("/me")
def my_profile(current_user: User = Depends(get_current_user)):
    return {
        "message": "Login successful",
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }


# ➤ Admin only route – sirf admin dekh sakega
@app.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)   # ← YE LINE ADD KAR DE
):
    if "admin" not in current_user.scopes:
        raise PermissionException()   # 403 error
    
    # Roman Urdu comment: admin ke liye total users aur orders count dikhao
    return {
        "message": "Welcome to Admin Dashboard!",
        "admin_user": current_user.name,
        "total_users": db.query(User).count(),          # ← db use kar rahe hain
        "total_orders": db.query(Order).count(),       # ← db use kar rahe hain
        "your_scopes": current_user.scopes
    }


