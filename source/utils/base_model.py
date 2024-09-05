from typing import Optional
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from enum import Enum
from source.utils.prompt import PROMPT_ELS_OR_TEXT

class GradeID(BaseModel):
    """The product ID is in the user's question."""
    ID: list[int] = Field(default = [0], description="ID of the product, just give the number")


class GradeReWrite(BaseModel):
    """Viết lại câu hỏi của người dùng dựa trên câu hỏi và lịch sử."""
    rewrite: str = Field(description="Viết lại câu hỏi của người dùng dựa vào câu hỏi và lịch sử")
    
class Seaching(BaseModel):
    """Lựa chọn giữa truy xuất bằng ELS và truy xuất bằng docs(text)"""
    type: str = Field(description="Giá trị là TEXT hoặc ELS hoặc NONE")
    
class Stage(BaseModel):
    """Lựa chọn giữa các stage của quá trình tư vấn bán hàng"""
    type: str = Field(description="Giá trị S1 (Tư vấn bán hàng), S2 (Chốt đơn), S3 (Xem thông tin đơn hàng)")

class Product(BaseModel):
    """Class representing a product."""
    ProductName: str = Field(description="Name of the product")
    Price: float = Field(description="Price of the product")
    Quantity: str = Field(description="Quantity of the product")
    
class ProductList(BaseModel):
    """List of products."""
    Name: str = Field(description="Name of the customer")   
    Address: str = Field(description="Address of the customer")
    PhoneNumber: str = Field(description="Phone number of the customer")
    ProductList: list[Product] = Field(description="List of products")    
    Note: Optional[str] = Field(description="Note of the customer")
    
class Products(BaseModel):
    """Class representing a product that the user buy."""
    ProductName: str = Field(description="Full name of the product")
    # ProductCode: str = Field(description=" The code of the product") 
    Buy: bool = Field(description="User's decision to buy the product. Default is False. Read history conversation carefully to get the correct value")
    # Specification: str = Field(description="Specifications of the product")
    Price: float = Field(description="Price of the product")
    Quantity: int = Field(description="Quantity of the product. Ask customer before decide how many products to buy")
    

class OrderDetails(BaseModel):
    """Class representing the order details."""
    FullName: str = Field(description="The full Name of the customer. Ask customer before fill this field. Avoid misunderstanding the customer's name")    
    Address: str = Field(description="Address of the customer")
    PhoneNumber: str = Field(description="Phone number of the customer")
    Intent: Stage  = Field(description="Lựa chọn giữa các stage của quá trình tư vấn bán hàng")
    RetrieveDecision: Seaching = Field(description="Decision on how to retrieve information: TEXT, ELS, NONE")
    ProductList: list[Products] = Field(description="List of products the user has bought")
    Note: Optional[str] = Field(description="Additional notes from the customer")