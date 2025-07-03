#!/usr/bin/env python3
"""
Comprehensive API testing script for NotesNest
Tests all endpoints end-to-end to verify functionality
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import argparse


class NotesNestAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tokens = {}
        self.users = {}
        self.friendships = {}
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp and appropriate emoji"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "HEADER": "🚀"
        }
        symbol = symbols.get(level, "ℹ️")
        print(f"{symbol} [{timestamp}] {message}")
        
    def test_endpoint(self, test_name: str, method: str, endpoint: str,
                     data: Optional[Dict] = None, headers: Optional[Dict] = None,
                     expected_status: int = 200, should_fail: bool = False):
        """Test a single endpoint and track results"""
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
                
            # Check response
            if should_fail:
                if response.status_code == expected_status:
                    self.log(f"{test_name}: ✅ PASSED (Expected failure: {response.status_code})", "SUCCESS")
                    self.test_results["passed"] += 1
                    return response
                else:
                    self.log(f"{test_name}: ❌ FAILED (Should have failed but got {response.status_code})", "ERROR")
                    self.test_results["failed"] += 1
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
        self.log("🏥 Testing Server Health", "HEADER")
        
        # Test API docs accessibility
        response = self.test_endpoint("API Documentation", "GET", "/docs")
        if response:
            self.log("Server is accessible", "SUCCESS")
            
        # Test API documentation endpoints
        self.log("📚 Testing API Documentation", "HEADER")
        self.test_endpoint("OpenAPI JSON", "GET", "/openapi.json")
        self.test_endpoint("Swagger UI", "GET", "/docs")
        self.test_endpoint("ReDoc", "GET", "/redoc")
        
    def test_user_registration(self):
        """Test user registration functionality"""
        self.log("👤 Testing User Registration", "HEADER")
        
        # Test users with proper password requirements
        test_users = [
            {
                "username": "testuser1_new",
                "email": "testuser1_new@example.com",
                "name": "Test User 1 New",
                "password": "SecurePassword123!"
            },
            {
                "username": "testuser2_new",
                "email": "testuser2_new@example.com", 
                "name": "Test User 2 New",
                "password": "SecurePassword123!"
            },
            {
                "username": "admin_user_new",
                "email": "admin_new@example.com",
                "name": "Admin User New",
                "password": "AdminPassword123!"
            }
        ]
        
        for user_data in test_users:
            response = self.test_endpoint(
                f"User {user_data['username']} registered",
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
                    'password': user_data['password'],
                    'info': user_info
                }
                self.log(f"User {user_data['username']} registered (ID: {user_info['id']})", "SUCCESS")
                
    def test_authentication(self):
        """Test authentication functionality"""
        self.log("🔐 Testing Authentication", "HEADER")
        
        for username, user_info in self.users.items():
            # Test login with email and password
            login_data = {
                "username": user_info['email'],
                "password": user_info['password']
            }
            
            response = self.test_endpoint(
                f"Authentication successful for {username}",
                "POST",
                "/api/v1/token",
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
                
    def test_protected_routes(self):
        """Test routes that require authentication"""
        self.log("🔒 Testing Protected Routes", "HEADER")
        
        if not self.tokens:
            self.log("No valid tokens available for protected route testing", "ERROR")
            return
            
        # Use first user's token for testing
        username = list(self.tokens.keys())[0]
        token = self.tokens[username]['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test authenticated access to user list
        response = self.test_endpoint(
            "Authenticated access successful",
            "GET",
            "/api/v1/users",
            headers=headers
        )
        
        if response:
            users_data = response.json()
            self.log(f"Found {len(users_data)} users", "SUCCESS")
            
    def test_user_operations(self):
        """Test user CRUD operations"""
        self.log("👥 Testing User Operations", "HEADER")
        
        if not self.tokens:
            self.log("No valid tokens available for user operations testing", "ERROR")
            return
            
        username = list(self.tokens.keys())[0]
        token = self.tokens[username]['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        user_id = self.users[username]['id']
        
        # Test getting user profile
        self.test_endpoint(
            "User profile retrieval successful",
            "GET",
            f"/api/v1/users/{user_id}",
            headers=headers
        )
        
        # Test updating user profile
        update_data = {
            "name": "Updated Test Name",
            "bio": "Updated bio for testing"
        }
        
        self.test_endpoint(
            "User profile update successful",
            "PUT",
            f"/api/v1/users/{user_id}",
            data=update_data,
            headers=headers
        )
        
    def test_friendship_system(self):
        """Test friendship system functionality"""
        self.log("🤝 Testing Friendship System", "HEADER")
        
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
            "Friend request sent successfully",
            "POST",
            "/api/v1/friend-requests",
            data={"addressee_id": user2_id},
            headers=headers1
        )
        
        friendship_id = None
        if response:
            friendship_data = response.json()
            friendship_id = friendship_data.get('id')
            
        # Get pending friend requests
        self.test_endpoint(
            "Pending friend requests retrieved",
            "GET",
            "/api/v1/friend-requests/pending",
            headers=headers2
        )
        
        # Accept friend request
        if friendship_id:
            self.test_endpoint(
                "Friend request accepted successfully",
                "POST",
                f"/api/v1/friend-requests/{friendship_id}/respond",
                data={"friendship_id": friendship_id, "action": "accept"},
                headers=headers2
            )
            
        # Get friends list
        response = self.test_endpoint(
            "Friends list retrieved",
            "GET",
            "/api/v1/friends",
            headers=headers1
        )
        
        if response:
            friends_data = response.json()
            self.log(f"Friends list retrieved ({friends_data.get('total', 0)} friends)", "SUCCESS")
            
        # Check friendship status
        self.test_endpoint(
            "Friendship status check successful",
            "GET",
            f"/api/v1/friendship-status/{user2_id}",
            headers=headers1
        )
        
        # Remove friend
        self.test_endpoint(
            "Friend removal successful",
            "DELETE",
            f"/api/v1/friends/{user2_id}",
            headers=headers1
        )
        
    def test_admin_operations(self):
        """Test admin-specific operations"""
        self.log("👑 Testing Admin Operations", "HEADER")
        
        self.log("Admin operations require manual role assignment", "INFO")
        self.log("These endpoints exist but require database-level admin role setup", "INFO")
        
    def test_error_handling(self):
        """Test error handling"""
        self.log("⚠️ Testing Error Handling", "HEADER")
        
        # Test invalid JSON
        self.test_endpoint(
            "Invalid JSON properly rejected",
            "POST",
            "/api/v1/users",
            data="invalid json string",
            expected_status=422,
            should_fail=True
        )
        
    def run_all_tests(self):
        """Run the complete test suite"""
        self.log("🚀 Starting NotesNest API Tests", "HEADER")
        self.log(f"Base URL: {self.base_url}")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("-" * 60)
        
        # Execute test suites
        start_time = datetime.now()
        
        self.test_health_endpoints()
        self.test_user_registration()
        self.test_authentication()
        self.test_protected_routes()
        self.test_user_operations()
        self.test_friendship_system()
        self.test_admin_operations()
        self.test_error_handling()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Print summary
        self.log("-" * 60)
        self.log("📊 Test Summary", "HEADER")
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Execution Time: {execution_time:.2f}s")
        
        if self.test_results["errors"]:
            self.log("❌ Errors encountered:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        if self.test_results["failed"] == 0:
            self.log("🎉 All tests passed!", "SUCCESS")
        else:
            self.log(f"⚠️ {self.test_results['failed']} tests failed!", "WARNING")
            
        return self.test_results["failed"] == 0


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Test NotesNest API endpoints")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", default="8000", help="API port (default: 8000)")
    parser.add_argument("--ssl", action="store_true", help="Use HTTPS instead of HTTP")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Construct base URL
    protocol = "https" if args.ssl else "http"
    base_url = f"{protocol}://{args.host}:{args.port}"
    
    # Run tests
    tester = NotesNestAPITester(base_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 