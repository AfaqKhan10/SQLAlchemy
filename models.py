from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey ,Table , Boolean


Base = declarative_base()

#  User table model
class User(Base):
    __tablename__ = "users"  e
    id = Column(Integer, primary_key=True)  
    name = Column(String, nullable=False)  
    email = Column(String, unique=True, nullable=False)  
    hashed_password = Column(String, nullable=False)  

    is_admin = Column(Boolean, default=False)  

    orders = relationship("Order", back_populates="user")  
    


# Bich ka table — ye batata hai kis order mein kon sa product hai
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True)
)

# Order table model
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)  # Order ka unique ID
    item = Column(String, nullable=False)  # Item name
    user_id = Column(Integer, ForeignKey("users.id"))  # Foreign key to link User
    user = relationship("User", back_populates="orders")  # Link back to User
    products = relationship("Product", secondary=order_product, back_populates="orders")



# Product table (jaise "Biryani", "Coke", "Pizza")
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    # Is product kitne orders mein hai
    orders = relationship("Order", secondary=order_product, back_populates="products")




