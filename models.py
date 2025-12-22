from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey ,Table , Boolean


Base = declarative_base()

class User(Base):
    __tablename__ = "users"  e
    id = Column(Integer, primary_key=True)  
    name = Column(String, nullable=False)  
    email = Column(String, unique=True, nullable=False)  
    hashed_password = Column(String, nullable=False)  

    is_admin = Column(Boolean, default=False)  

    orders = relationship("Order", back_populates="user")  
    
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True)
)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True) 
    item = Column(String, nullable=False)  
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="orders")  
    products = relationship("Product", secondary=order_product, back_populates="orders")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    
    orders = relationship("Order", secondary=order_product, back_populates="products")
