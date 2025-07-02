from sqlmodel import Session, select, and_, or_
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.friendship import (
    Friendship, FriendshipStatus, FriendRequestCreate,
    FriendRequestResponse, FriendshipRead, FriendRead, FriendsList
)
from app.models.user import User
from app.utils.exceptions import (
    UserValidationError, UserNotFoundError, PermissionError,
    FriendshipValidationError, FriendshipNotFoundError
)
from db.utils import DatabaseUtils


class FriendshipService:
    """Service class for managing user friendships."""
    
    @staticmethod
    def send_friend_request(requester_id: int, addressee_id: int, session: Session) -> FriendshipRead:
        """
        Send a friend request from requester to addressee.
        
        Args:
            requester_id: ID of user sending the request
            addressee_id: ID of user receiving the request
            session: Database session
            
        Returns:
            FriendshipRead: Created friendship object
            
        Raises:
            FriendshipValidationError: If request is invalid
            UserNotFoundError: If either user doesn't exist
        """
        # Validate users exist
        requester = DatabaseUtils.get_user_by_id_sync(requester_id)
        addressee = DatabaseUtils.get_user_by_id_sync(addressee_id)
        
        if not requester:
            raise UserNotFoundError("Requester user not found")
        if not addressee:
            raise UserNotFoundError("Addressee user not found")
        
        # Can't send friend request to yourself
        if requester_id == addressee_id:
            raise FriendshipValidationError("Cannot send friend request to yourself")
        
        # Check if friendship already exists
        existing_friendship = FriendshipService._get_existing_friendship(
            requester_id, addressee_id, session
        )
        
        if existing_friendship:
            if existing_friendship.status == FriendshipStatus.PENDING:
                raise FriendshipValidationError("Friend request already pending")
            elif existing_friendship.status == FriendshipStatus.ACCEPTED:
                raise FriendshipValidationError("Users are already friends")
            elif existing_friendship.status == FriendshipStatus.BLOCKED:
                raise FriendshipValidationError("Cannot send friend request to blocked user")
        
        # Create new friendship
        friendship = Friendship(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendshipStatus.PENDING
        )
        
        session.add(friendship)
        session.commit()
        session.refresh(friendship)
        
        return FriendshipRead.model_validate(friendship)
    
    @staticmethod
    def respond_to_friend_request(
        friendship_id: int, action: str, current_user_id: int, session: Session
    ) -> FriendshipRead:
        """
        Respond to a friend request (accept, reject, or block).
        
        Args:
            friendship_id: ID of the friendship to respond to
            action: 'accept', 'reject', or 'block'
            current_user_id: ID of user responding to request
            session: Database session
            
        Returns:
            FriendshipRead: Updated friendship object
            
        Raises:
            FriendshipNotFoundError: If friendship doesn't exist
            PermissionError: If user can't respond to this request
            FriendshipValidationError: If action is invalid
        """
        # Get friendship
        friendship = session.get(Friendship, friendship_id)
        if not friendship:
            raise FriendshipNotFoundError()
        
        # Only addressee can respond to friend request
        if friendship.addressee_id != current_user_id:
            raise PermissionError("You can only respond to friend requests sent to you")
        
        # Can only respond to pending requests
        if friendship.status != FriendshipStatus.PENDING:
            raise FriendshipValidationError("Can only respond to pending friend requests")
        
        # Update friendship status based on action
        if action == 'accept':
            friendship.status = FriendshipStatus.ACCEPTED
        elif action == 'reject':
            friendship.status = FriendshipStatus.REJECTED
        elif action == 'block':
            friendship.status = FriendshipStatus.BLOCKED
        else:
            raise FriendshipValidationError("Invalid action. Must be 'accept', 'reject', or 'block'")
        
        friendship.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(friendship)
        
        return FriendshipRead.model_validate(friendship)
    
    @staticmethod
    def remove_friend(user_id: int, friend_id: int, session: Session) -> bool:
        """
        Remove a friendship between two users.
        
        Args:
            user_id: ID of current user
            friend_id: ID of friend to remove
            session: Database session
            
        Returns:
            bool: True if friendship was removed
            
        Raises:
            FriendshipNotFoundError: If friendship doesn't exist
        """
        # Find the friendship (could be in either direction)
        friendship = FriendshipService._get_existing_friendship(user_id, friend_id, session)
        
        if not friendship:
            raise FriendshipNotFoundError("Friendship not found")
        
        # Only remove if they are actually friends
        if friendship.status != FriendshipStatus.ACCEPTED:
            raise FriendshipValidationError("Users are not friends")
        
        # Delete the friendship
        session.delete(friendship)
        session.commit()
        
        return True
    
    @staticmethod
    def get_friends_list(
        user_id: int, page: int = 1, per_page: int = 10, session: Session = None
    ) -> FriendsList:
        """
        Get a paginated list of user's friends.
        
        Args:
            user_id: ID of user whose friends to list
            page: Page number (1-based)
            per_page: Number of friends per page
            session: Database session
            
        Returns:
            FriendsList: Paginated list of friends
        """
        offset = (page - 1) * per_page
        
        # Query for accepted friendships where user is either requester or addressee
        statement = select(Friendship, User).join(
            User,
            or_(
                and_(Friendship.requester_id == user_id, User.id == Friendship.addressee_id),
                and_(Friendship.addressee_id == user_id, User.id == Friendship.requester_id)
            )
        ).where(
            Friendship.status == FriendshipStatus.ACCEPTED
        ).offset(offset).limit(per_page)
        
        results = session.exec(statement).all()
        
        # Count total friends
        count_statement = select(Friendship).where(
            and_(
                Friendship.status == FriendshipStatus.ACCEPTED,
                or_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == user_id
                )
            )
        )
        total = len(session.exec(count_statement).all())
        
        # Convert to FriendRead objects
        friends = []
        for friendship, user in results:
            friends.append(FriendRead(
                id=user.id,
                username=user.username,
                name=user.name,
                email=user.email,
                is_active=user.is_active,
                friendship_status=friendship.status,
                friendship_since=friendship.created_at
            ))
        
        return FriendsList(
            friends=friends,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
            has_prev=page > 1
        )
    
    @staticmethod
    def get_pending_requests(user_id: int, session: Session) -> List[FriendshipRead]:
        """
        Get pending friend requests for a user (requests sent TO the user).
        
        Args:
            user_id: ID of user to get pending requests for
            session: Database session
            
        Returns:
            List[FriendshipRead]: List of pending friend requests
        """
        statement = select(Friendship).where(
            and_(
                Friendship.addressee_id == user_id,
                Friendship.status == FriendshipStatus.PENDING
            )
        )
        
        friendships = session.exec(statement).all()
        return [FriendshipRead.model_validate(f) for f in friendships]
    
    @staticmethod
    def get_sent_requests(user_id: int, session: Session) -> List[FriendshipRead]:
        """
        Get friend requests sent by a user.
        
        Args:
            user_id: ID of user to get sent requests for
            session: Database session
            
        Returns:
            List[FriendshipRead]: List of sent friend requests
        """
        statement = select(Friendship).where(
            and_(
                Friendship.requester_id == user_id,
                Friendship.status == FriendshipStatus.PENDING
            )
        )
        
        friendships = session.exec(statement).all()
        return [FriendshipRead.model_validate(f) for f in friendships]
    
    @staticmethod
    def get_friendship_status(user1_id: int, user2_id: int, session: Session) -> Optional[FriendshipStatus]:
        """
        Get the friendship status between two users.
        
        Args:
            user1_id: ID of first user
            user2_id: ID of second user
            session: Database session
            
        Returns:
            Optional[FriendshipStatus]: Friendship status or None if no relationship
        """
        friendship = FriendshipService._get_existing_friendship(user1_id, user2_id, session)
        return friendship.status if friendship else None
    
    @staticmethod
    def _get_existing_friendship(user1_id: int, user2_id: int, session: Session) -> Optional[Friendship]:
        """
        Get existing friendship between two users (in either direction).
        
        Args:
            user1_id: ID of first user
            user2_id: ID of second user
            session: Database session
            
        Returns:
            Optional[Friendship]: Existing friendship or None
        """
        statement = select(Friendship).where(
            or_(
                and_(Friendship.requester_id == user1_id, Friendship.addressee_id == user2_id),
                and_(Friendship.requester_id == user2_id, Friendship.addressee_id == user1_id)
            )
        )
        
        return session.exec(statement).first()
    
    @staticmethod
    def cancel_friend_request(requester_id: int, addressee_id: int, session: Session) -> bool:
        """
        Cancel a pending friend request.
        
        Args:
            requester_id: ID of user who sent the request
            addressee_id: ID of user who received the request
            session: Database session
            
        Returns:
            bool: True if request was cancelled
            
        Raises:
            FriendshipNotFoundError: If no pending request exists
        """
        statement = select(Friendship).where(
            and_(
                Friendship.requester_id == requester_id,
                Friendship.addressee_id == addressee_id,
                Friendship.status == FriendshipStatus.PENDING
            )
        )
        
        friendship = session.exec(statement).first()
        if not friendship:
            raise FriendshipNotFoundError("No pending friend request found")
        
        session.delete(friendship)
        session.commit()
        
        return True 