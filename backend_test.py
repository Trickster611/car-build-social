import requests
import sys
import json
from datetime import datetime

class AutoSocialAPITester:
    def __init__(self, base_url="https://autosocial-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.username = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_project_id = None
        self.second_user_token = None
        self.second_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 200:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_register_user(self, username, email, bio="Car enthusiast"):
        """Test user registration"""
        success, response = self.run_test(
            f"Register User ({username})",
            "POST",
            "auth/register",
            200,
            data={
                "username": username,
                "email": email,
                "bio": bio
            }
        )
        if success and 'token' in response:
            if not self.token:  # First user
                self.token = response['token']
                self.user_id = response['user']['id']
                self.username = response['user']['username']
            else:  # Second user
                self.second_user_token = response['token']
                self.second_user_id = response['user']['id']
            return True, response
        return False, {}

    def test_login_user(self, username):
        """Test user login"""
        success, response = self.run_test(
            f"Login User ({username})",
            "POST",
            "auth/login",
            200,
            data={"username": username}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.username = response['user']['username']
            return True, response
        return False, {}

    def test_get_current_user(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_create_project(self, title, make, model, year, description, modifications=None, images=None, build_cost=0):
        """Test creating a project"""
        project_data = {
            "title": title,
            "car_make": make,
            "car_model": model,
            "car_year": year,
            "description": description,
            "modifications": modifications or [],
            "images": images or [],
            "build_cost": build_cost
        }
        
        success, response = self.run_test(
            f"Create Project ({title})",
            "POST",
            "projects",
            200,
            data=project_data
        )
        
        if success and 'id' in response:
            if not self.created_project_id:
                self.created_project_id = response['id']
            return True, response
        return False, {}

    def test_get_projects(self):
        """Test getting all projects"""
        return self.run_test("Get All Projects", "GET", "projects", 200)

    def test_get_project_by_id(self, project_id):
        """Test getting a specific project"""
        return self.run_test(
            f"Get Project by ID",
            "GET",
            f"projects/{project_id}",
            200
        )

    def test_update_project(self, project_id, updates):
        """Test updating a project"""
        return self.run_test(
            "Update Project",
            "PUT",
            f"projects/{project_id}",
            200,
            data=updates
        )

    def test_get_user_projects(self, user_id):
        """Test getting user's projects"""
        return self.run_test(
            "Get User Projects",
            "GET",
            f"users/{user_id}/projects",
            200
        )

    def test_like_project(self, project_id):
        """Test liking a project"""
        return self.run_test(
            "Like Project",
            "POST",
            "likes",
            200,
            data={"project_id": project_id}
        )

    def test_add_comment(self, project_id, content):
        """Test adding a comment"""
        return self.run_test(
            "Add Comment",
            "POST",
            "comments",
            200,
            data={
                "project_id": project_id,
                "content": content
            }
        )

    def test_get_comments(self, project_id):
        """Test getting project comments"""
        return self.run_test(
            "Get Project Comments",
            "GET",
            f"projects/{project_id}/comments",
            200
        )

    def test_follow_user(self, user_id):
        """Test following a user"""
        return self.run_test(
            "Follow User",
            "POST",
            f"users/{user_id}/follow",
            200
        )

    def test_unfollow_user(self, user_id):
        """Test unfollowing a user"""
        return self.run_test(
            "Unfollow User",
            "DELETE",
            f"users/{user_id}/follow",
            200
        )

    def test_get_user_profile(self, user_id):
        """Test getting user profile"""
        return self.run_test(
            "Get User Profile",
            "GET",
            f"users/{user_id}",
            200
        )

    def switch_to_second_user(self):
        """Switch authentication to second user"""
        if self.second_user_token:
            self.token = self.second_user_token
            print(f"\n🔄 Switched to second user authentication")
            return True
        return False

def main():
    print("🚗 AutoSocial Hub API Testing Suite")
    print("=" * 50)
    
    tester = AutoSocialAPITester()
    timestamp = datetime.now().strftime('%H%M%S')
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: User Registration
    user1_email = f"testuser1_{timestamp}@example.com"
    user1_username = f"testuser1_{timestamp}"
    success, _ = tester.test_register_user(user1_username, user1_email, "Love building drift cars!")
    
    if not success:
        print("❌ User registration failed, stopping tests")
        return 1
    
    # Test 3: Get current user
    tester.test_get_current_user()
    
    # Test 4: Create a project
    success, _ = tester.test_create_project(
        "My Drift Build",
        "Toyota",
        "AE86",
        1986,
        "Building the ultimate drift machine with custom suspension and turbo setup",
        ["Coilovers", "Turbo kit", "Roll cage", "Bucket seats"],
        ["https://example.com/ae86_1.jpg", "https://example.com/ae86_2.jpg"],
        15000
    )
    
    if not success or not tester.created_project_id:
        print("❌ Project creation failed, stopping tests")
        return 1
    
    # Test 5: Get all projects
    tester.test_get_projects()
    
    # Test 6: Get specific project
    tester.test_get_project_by_id(tester.created_project_id)
    
    # Test 7: Update project
    tester.test_update_project(tester.created_project_id, {
        "description": "Updated: Building the ultimate drift machine with even more mods!",
        "build_cost": 18000
    })
    
    # Test 8: Get user projects
    tester.test_get_user_projects(tester.user_id)
    
    # Test 9: Register second user for social features
    user2_email = f"testuser2_{timestamp}@example.com"
    user2_username = f"testuser2_{timestamp}"
    success, _ = tester.test_register_user(user2_username, user2_email, "JDM enthusiast")
    
    if not success:
        print("❌ Second user registration failed, continuing with limited tests")
    else:
        # Test 10: Switch to second user and test social features
        tester.switch_to_second_user()
        
        # Test 11: Like the first user's project
        tester.test_like_project(tester.created_project_id)
        
        # Test 12: Add comment to project
        tester.test_add_comment(tester.created_project_id, "Amazing build! Love the AE86!")
        
        # Test 13: Get comments
        tester.test_get_comments(tester.created_project_id)
        
        # Test 14: Follow first user
        tester.test_follow_user(tester.user_id)
        
        # Test 15: Get user profile
        tester.test_get_user_profile(tester.user_id)
        
        # Test 16: Unfollow user
        tester.test_unfollow_user(tester.user_id)
        
        # Test 17: Like project again (should unlike)
        tester.test_like_project(tester.created_project_id)
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())