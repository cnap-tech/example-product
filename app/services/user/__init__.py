"""User services package."""

from .crud import UserCRUDService
from .validation import UserValidationService  
from .management import UserManagementService
from .exceptions import UserValidationError, UserNotFoundError, PermissionError

# Maintain backward compatibility by creating a unified interface
class UserService:
    """Unified user service interface for backward compatibility."""
    
    # CRUD operations
    create_user = UserCRUDService.create_user
    create_user_async = UserCRUDService.create_user_async
    get_user_by_id = UserCRUDService.get_user_by_id
    get_user_by_id_async = UserCRUDService.get_user_by_id_async
    list_users = UserCRUDService.list_users
    list_users_async = UserCRUDService.list_users_async
    update_user = UserCRUDService.update_user
    update_user_async = UserCRUDService.update_user_async
    delete_user = UserCRUDService.delete_user
    delete_user_async = UserCRUDService.delete_user_async
    
    # Validation
    validate_unique_email = UserValidationService.validate_unique_email
    validate_unique_email_async = UserValidationService.validate_unique_email_async
    validate_unique_username = UserValidationService.validate_unique_username
    validate_unique_username_async = UserValidationService.validate_unique_username_async
    
    # Management
    check_user_access_permission = UserManagementService.check_user_access_permission
    update_user_role = UserManagementService.update_user_role
    update_user_role_async = UserManagementService.update_user_role_async
    verify_email = UserManagementService.verify_email
    verify_email_async = UserManagementService.verify_email_async


__all__ = [
    "UserService",
    "UserCRUDService", 
    "UserValidationService",
    "UserManagementService",
    "UserValidationError",
    "UserNotFoundError", 
    "PermissionError"
] 