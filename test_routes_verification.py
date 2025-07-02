#!/usr/bin/env python3
"""
Comprehensive route verification script for NotesNest API
Tests all endpoints to ensure they're working correctly after database fixes
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class RoutesTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tokens = {}
        self.users = {}
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{symbols.get(level, 'ℹ️')} [{timestamp}] {message}")
        
    def test_endpoint(self, test_name: str, method: str, endpoint: str, 
                     data: Optional[Dict] = None, headers: Optional[Dict] = None,
                     expected_status: int = 200, should_fail: bool = False):
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                if headers and headers.get("Content-Type") == "application/x-www-form-urlencoded":
                    response = self.session.post(url, data=data, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            if should_fail:
                if response.status_code != expected_status:
                    self.log(f"{test_name}: ✅ PASSED (Expected failure: {response.status_code})", "SUCCESS")
                    self.test_results["passed"] += 1
                    return response
                else:
                    self.log(f"{test_name}: ❌ FAILED (Should have failed but got {response.status_code})", "ERROR")
                    self.test_results["failed"] += 1
                    self.test_results["errors"].append(f"{test_name}: Expected failure but succeeded")
                    return None
            else:
                if response.status_code == expected_status:
                    self.log(f"{test_name}: ✅ PASSED ({response.status_code})", "SUCCESS")
                    self.test_results["passed"] += 1
                    return response
                else:
                    self.log(f"{test_name}: ❌ FAILED (Expected {expected_status}, got {response.status_code})", "ERROR")
                    if response.text:
                        self.log(f"Response: {response.text[:200]}...", "ERROR")
                    self.test_results["failed"] += 1
                    self.test_results["errors"].append(f"{test_name}: Status {response.status_code}")
                    return None
                    
        except Exception as e:
            self.log(f"{test_name}: ❌ ERROR - {str(e)}", "ERROR")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            return None
    
    def test_health_endpoints(self):
        """Test basic health and documentation endpoints"""
        self.log("🏥 Testing Health & Documentation Endpoints")
        
        # Test API docs
        self.test_endpoint("API Documentation", "GET", "/docs")
        self.test_endpoint("OpenAPI JSON", "GET", "/openapi.json")
        self.test_endpoint("ReDoc", "GET", "/redoc")
        
    def test_user_registration(self):
        """Test user registration endpoints"""
        self.log("👤 Testing User Registration")
        
        # Create test users
        test_users = [
            {
                "username": "testuser1",
                "email": "testuser1@example.com",
                "name": "Test User 1",
                "password": "SecurePassword123!"
            },
            {
                "username": "testuser2", 
                "email": "testuser2@example.com",
                "name": "Test User 2",
                "password": "SecurePassword123!"
            },
            {
                "username": "adminuser",
                "email": "admin@example.com", 
                "name": "Admin User",
                "password": "AdminPassword123!"
            }
        ]
        
        for user_data in test_users:
            response = self.test_endpoint(
                f"Create User: {user_data['username']}", 
                "POST", 
                "/api/v1/users", 
                data=user_data,
                expected_status=200
            )
            if response:
                user_info = response.json()
                self.users[user_data['username']] = {
                    'id': user_info['id'],
                    'email': user_data['email'],
                    'password': user_data['password']
                }
                
        # Test duplicate email
        self.test_endpoint(
            "Duplicate Email Prevention",
            "POST",
            "/api/v1/users",
            data=test_users[0],  # Same user again
            expected_status=422,
            should_fail=True
        )
        
    def test_authentication(self):
        """Test authentication endpoints"""
        self.log("🔐 Testing Authentication")
        
        for username, user_info in self.users.items():
            # Test login
            login_data = {
                "username": user_info['email'],
                "password": user_info['password']
            }
            
            response = self.test_endpoint(
                f"Login: {username}",
                "POST", 
                "/api/v1/auth/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                expected_status=200
            )
            
            if response:
                token_data = response.json()
                self.tokens[username] = {
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token']
                }
                
        # Test invalid login
        self.test_endpoint(
            "Invalid Login",
            "POST",
            "/api/v1/auth/token", 
            data={"username": "invalid@example.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            expected_status=401,
            should_fail=True
        )
        
    def test_protected_routes(self):
        """Test routes that require authentication"""
        self.log("🔒 Testing Protected Routes")
        
        if not self.tokens:
            self.log("No valid tokens available for protected route testing", "ERROR")
            return
            
        # Get first user's token
        username = list(self.tokens.keys())[0]
        token = self.tokens[username]['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test protected endpoints
        self.test_endpoint("List Users (Authenticated)", "GET", "/api/v1/users", headers=headers)
        
        # Test user profile access
        user_id = self.users[username]['id']
        self.test_endpoint(f"Get User Profile", "GET", f"/api/v1/users/{user_id}", headers=headers)
        
        # Test unauthorized access
        self.test_endpoint(
            "Unauthorized Access",
            "GET", 
            "/api/v1/users",
            expected_status=401,
            should_fail=True
        )
        
        # Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        self.test_endpoint(
            "Invalid Token",
            "GET",
            "/api/v1/users", 
            headers=invalid_headers,
            expected_status=401,
            should_fail=True
        )
        
    def test_user_operations(self):
        """Test user CRUD operations"""
        self.log("👥 Testing User Operations")
        
        if not self.tokens:
            self.log("No valid tokens available for user operations testing", "ERROR")
            return
            
        username = list(self.tokens.keys())[0]
        token = self.tokens[username]['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        user_id = self.users[username]['id']
        
        # Test profile update
        update_data = {
            "name": "Updated Name",
            "bio": "Updated bio"
        }
        self.test_endpoint(
            "Update Profile",
            "PUT",
            f"/api/v1/users/{user_id}",
            data=update_data,
            headers=headers
        )
        
    def test_friendship_system(self):
        """Test friendship endpoints"""
        self.log("🤝 Testing Friendship System")
        
        if len(self.tokens) < 2:
            self.log("Need at least 2 users for friendship testing", "WARNING")
            return
            
        usernames = list(self.tokens.keys())[:2]
        user1_token = self.tokens[usernames[0]]['access_token']
        user2_token = self.tokens[usernames[1]]['access_token']
        user2_id = self.users[usernames[1]]['id']
        
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        # Send friend request
        response = self.test_endpoint(
            "Send Friend Request",
            "POST",
            "/api/v1/friend-requests",
            data={"addressee_id": user2_id},
            headers=headers1
        )
        
        friendship_id = None
        if response:
            friendship_data = response.json()
            friendship_id = friendship_data.get('id')
            
        # Check pending requests
        self.test_endpoint("Get Pending Requests", "GET", "/api/v1/friend-requests/pending", headers=headers2)
        
        # Accept friend request
        if friendship_id:
            self.test_endpoint(
                "Accept Friend Request",
                "POST",
                f"/api/v1/friend-requests/{friendship_id}/respond",
                data={"friendship_id": friendship_id, "action": "accept"},
                headers=headers2
            )
            
        # Get friends list
        self.test_endpoint("Get Friends List", "GET", "/api/v1/friends", headers=headers1)
        
        # Check friendship status
        self.test_endpoint(
            "Check Friendship Status",
            "GET",
            f"/api/v1/friendship-status/{user2_id}",
            headers=headers1
        )
        
    def test_error_handling(self):
        """Test error handling"""
        self.log("⚠️ Testing Error Handling")
        
        # Test invalid JSON
        self.test_endpoint(
            "Invalid JSON",
            "POST",
            "/api/v1/users",
            data="invalid json",
            expected_status=422,
            should_fail=True
        )
        
        # Test missing fields
        self.test_endpoint(
            "Missing Required Fields",
            "POST",
            "/api/v1/users",
            data={"username": "incomplete"},
            expected_status=422,
            should_fail=True
        )
        
    def run_all_tests(self):
        """Run all route tests"""
        self.log("🚀 Starting NotesNest Route Verification Tests")
        self.log(f"Base URL: {self.base_url}")
        self.log("-" * 60)
        
        # Run test suites
        self.test_health_endpoints()
        self.test_user_registration()
        self.test_authentication()
        self.test_protected_routes()
        self.test_user_operations()
        self.test_friendship_system()
        self.test_error_handling()
        
        # Print summary
        self.log("-" * 60)
        self.log("📊 Test Summary")
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            self.log("❌ Errors encountered:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        if self.test_results["failed"] == 0:
            self.log("🎉 All tests passed!")
        else:
            self.log(f"⚠️ {self.test_results['failed']} tests failed!")
            
        return self.test_results["failed"] == 0

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test NotesNest API routes")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", default="8000", help="API port") 
    parser.add_argument("--ssl", action="store_true", help="Use HTTPS")
    
    args = parser.parse_args()
    
    protocol = "https" if args.ssl else "http"
    base_url = f"{protocol}://{args.host}:{args.port}"
    
    tester = RoutesTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 