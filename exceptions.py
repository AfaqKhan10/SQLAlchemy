from fastapi import HTTPException
from typing import Any


class AppException(HTTPException):
    def __init__(self, status_code: int, message: str, extra: Any = None):
        detail = {"error": True, "message": message}
        if extra:
            detail.update(extra)
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    def __init__(self, item: str = "Resource"):
        super().__init__(404, f"{item} not found")


class UserNotFound(NotFoundException):
    def __init__(self):
        super().__init__("User")          

class OrderNotFound(NotFoundException):
    def __init__(self):
        super().__init__("Order")        

class ProductNotFound(NotFoundException):
    def __init__(self):
        super().__init__("Product")      


class AuthException(AppException):
    def __init__(self):
        super().__init__(401, "Invalid or expired token")



class PermissionException(AppException):
    def __init__(self):
        super().__init__(403, "You do not have permission to perform this action")


class ValidationException(AppException):
    def __init__(self, message: str = "Invalid data provided"):

        super().__init__(400, message)
