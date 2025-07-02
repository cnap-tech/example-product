#!/usr/bin/env python3
"""
Comprehensive test script for the Friends API endpoints including edge cases
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login_user(email, password):
    """Login user and return token"""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def create_user(username, email, password, name):
    """Create a new user"""
    response = requests.post(
        f"{BASE_URL}/users",
        json={
            "username": username,
            "email": email,
            "password": password,
            "name": name
        }
    )
    if response.status_code == 200:
        return response.json()["id"]
    else:
        print(f"User creation failed: {response.text}")
        return None

def test_comprehensive_friends_system():
    """Test comprehensive friends system functionality"""
    print("🧪 Comprehensive Friends System Testing")
    print("=" * 60)
    
    # Create a third user for more complex scenarios
    print("1. Creating Charlie...")
    charlie_id = create_user("charlie", "charlie@example.com", "Password123!", "Charlie Brown")
    if not charlie_id:
        print("❌ Charlie creation failed")
        return
    print(f"✅ Charlie created with ID: {charlie_id}")
    
    # Login all users
    print("2. Logging in all users...")
    alice_token = login_user("alice@example.com", "Password123!")
    bob_token = login_user("bob@example.com", "Password123!")
    charlie_token = login_user("charlie@example.com", "Password123!")
    
    if not all([alice_token, bob_token, charlie_token]):
        print("❌ Failed to login all users")
        return
    print("✅ All users logged in successfully")
    
    # Test sending friend request to self (should fail)
    print("3. Testing friend request to self...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": 1},  # Alice trying to friend herself
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test sending friend request to non-existent user
    print("4. Testing friend request to non-existent user...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": 999},
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test duplicate friend request (Alice already friends with Bob)
    print("5. Testing duplicate friend request...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": 2},  # Alice trying to friend Bob again
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Alice sends friend request to Charlie
    print("6. Alice sending friend request to Charlie...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": charlie_id},
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    if response.status_code == 200:
        alice_charlie_friendship_id = response.json()["id"]
        print("✅ Friend request sent successfully")
    
    # Charlie sends friend request to Bob
    print("7. Charlie sending friend request to Bob...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": 2},
        headers={"Authorization": f"Bearer {charlie_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    if response.status_code == 200:
        charlie_bob_friendship_id = response.json()["id"]
        print("✅ Friend request sent successfully")
    
    # Test getting sent requests (Alice's perspective)
    print("8. Getting Alice's sent requests...")
    response = requests.get(
        f"{BASE_URL}/friend-requests/sent",
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test friendship status check (Alice-Charlie)
    print("9. Checking Alice-Charlie friendship status...")
    response = requests.get(
        f"{BASE_URL}/friendship-status/{charlie_id}",
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Charlie rejects Alice's friend request
    print("10. Charlie rejecting Alice's friend request...")
    response = requests.post(
        f"{BASE_URL}/friend-requests/{alice_charlie_friendship_id}/respond",
        json={"friendship_id": alice_charlie_friendship_id, "action": "reject"},
        headers={"Authorization": f"Bearer {charlie_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Bob blocks Charlie's friend request
    print("11. Bob blocking Charlie's friend request...")
    response = requests.post(
        f"{BASE_URL}/friend-requests/{charlie_bob_friendship_id}/respond",
        json={"friendship_id": charlie_bob_friendship_id, "action": "block"},
        headers={"Authorization": f"Bearer {bob_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test removing friend (Alice removes Bob)
    print("12. Alice removing Bob as friend...")
    response = requests.delete(
        f"{BASE_URL}/friends/2",  # Bob's ID
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Check friends list after removal
    print("13. Getting Alice's friends list after removal...")
    response = requests.get(
        f"{BASE_URL}/friends",
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test canceling friend request
    print("14. Alice sending new friend request to Charlie...")
    response = requests.post(
        f"{BASE_URL}/friend-requests",
        json={"addressee_id": charlie_id},
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    print("15. Alice canceling friend request to Charlie...")
    response = requests.delete(
        f"{BASE_URL}/friend-requests/cancel/{charlie_id}",
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    print(f"Status: {response.status_code}, Response: {response.text}")
    
    print("=" * 60)
    print("🎉 Comprehensive testing completed!")

if __name__ == "__main__":
    test_comprehensive_friends_system()