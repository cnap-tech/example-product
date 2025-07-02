from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.models.user import User
from app.models.friendship import (
    FriendRequestCreate, FriendRequestResponse, FriendshipRead, 
    FriendRead, FriendsList, FriendshipStatus
)
from app.services.friendship_service import FriendshipService
from app.utils.exceptions import handle_service_exception
from app.dependencies.auth import require_auth
from app.dependencies.database import DBSession

router = APIRouter()

@router.post("/friend-requests", response_model=FriendshipRead)
async def send_friend_request(
    friend_request: FriendRequestCreate,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Send a friend request to another user.
    
    Args:
        friend_request: Friend request data containing addressee_id
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        FriendshipRead: Created friendship object
    """
    try:
        friendship = FriendshipService.send_friend_request(
            requester_id=current_user.id,
            addressee_id=friend_request.addressee_id,
            session=session
        )
        return friendship
    except Exception as e:
        handle_service_exception(e)

@router.post("/friend-requests/{friendship_id}/respond", response_model=FriendshipRead)
async def respond_to_friend_request(
    friendship_id: int,
    response: FriendRequestResponse,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Respond to a friend request (accept, reject, or block).
    
    Args:
        friendship_id: ID of the friendship to respond to
        response: Response data containing action ('accept', 'reject', 'block')
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        FriendshipRead: Updated friendship object
    """
    try:
        friendship = FriendshipService.respond_to_friend_request(
            friendship_id=friendship_id,
            action=response.action,
            current_user_id=current_user.id,
            session=session
        )
        return friendship
    except Exception as e:
        handle_service_exception(e)

@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Remove a friend from your friends list.
    
    Args:
        friend_id: ID of friend to remove
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Success message
    """
    try:
        FriendshipService.remove_friend(
            user_id=current_user.id,
            friend_id=friend_id,
            session=session
        )
        return {"detail": "Friend removed successfully"}
    except Exception as e:
        handle_service_exception(e)

@router.get("/friends", response_model=FriendsList)
async def get_friends_list(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Get a paginated list of current user's friends.
    
    Args:
        page: Page number (default: 1)
        per_page: Number of friends per page (default: 10, max: 100)
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        FriendsList: Paginated list of friends
    """
    friends_list = FriendshipService.get_friends_list(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        session=session
    )
    return friends_list

@router.get("/friend-requests/pending", response_model=List[FriendshipRead])
async def get_pending_friend_requests(
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Get pending friend requests received by the current user.
    
    Args:
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        List[FriendshipRead]: List of pending friend requests
    """
    pending_requests = FriendshipService.get_pending_requests(
        user_id=current_user.id,
        session=session
    )
    return pending_requests

@router.get("/friend-requests/sent", response_model=List[FriendshipRead])
async def get_sent_friend_requests(
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Get friend requests sent by the current user.
    
    Args:
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        List[FriendshipRead]: List of sent friend requests
    """
    sent_requests = FriendshipService.get_sent_requests(
        user_id=current_user.id,
        session=session
    )
    return sent_requests

@router.get("/friendship-status/{user_id}")
async def get_friendship_status(
    user_id: int,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Get the friendship status between current user and another user.
    
    Args:
        user_id: ID of the other user
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Friendship status information
    """
    status_result = FriendshipService.get_friendship_status(
        user1_id=current_user.id,
        user2_id=user_id,
        session=session
    )
    
    return {
        "user_id": user_id,
        "friendship_status": status_result,
        "are_friends": status_result == FriendshipStatus.ACCEPTED
    }

@router.delete("/friend-requests/cancel/{addressee_id}")
async def cancel_friend_request(
    addressee_id: int,
    current_user: User = Depends(require_auth),
    session = DBSession
):
    """
    Cancel a pending friend request sent to another user.
    
    Args:
        addressee_id: ID of user who received the friend request
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        dict: Success message
    """
    try:
        FriendshipService.cancel_friend_request(
            requester_id=current_user.id,
            addressee_id=addressee_id,
            session=session
        )
        return {"detail": "Friend request cancelled successfully"}
    except Exception as e:
        handle_service_exception(e) 