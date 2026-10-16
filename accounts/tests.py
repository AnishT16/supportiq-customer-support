from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        # Endpoints
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.refresh_url = reverse('accounts:refresh')
        self.me_url = reverse('accounts:me')

        # Baseline test user
        self.base_password = 'StrongTestPassword123!'
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@supportiq.com',
            password=self.base_password,
            first_name='Existing',
            last_name='User',
            role=User.Role.CUSTOMER,
        )

    # 1. Successful customer registration
    def test_successful_customer_registration(self):
        payload = {
            'username': 'newcustomer',
            'email': 'newcustomer@supportiq.com',
            'password': 'SecurePassword2026!#',
            'password_confirm': 'SecurePassword2026!#',
            'first_name': 'Jane',
            'last_name': 'Doe',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newcustomer')
        self.assertEqual(response.data['email'], 'newcustomer@supportiq.com')
        self.assertEqual(response.data['role'], 'CUSTOMER')
        self.assertNotIn('password', response.data)

        # Verify DB entry
        user = User.objects.get(username='newcustomer')
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    # 2. Duplicate username / email handling
    def test_duplicate_username_rejected(self):
        payload = {
            'username': 'existinguser',
            'email': 'different_email@supportiq.com',
            'password': 'SecurePassword2026!#',
            'password_confirm': 'SecurePassword2026!#',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_duplicate_email_rejected_case_insensitive(self):
        payload = {
            'username': 'uniqueuser',
            'email': 'EXISTING@SUPPORTIQ.COM',
            'password': 'SecurePassword2026!#',
            'password_confirm': 'SecurePassword2026!#',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # 3. Password hashing and password validation
    def test_password_is_properly_hashed(self):
        raw_password = 'ValidPassword9988!#'
        payload = {
            'username': 'hashcheckuser',
            'email': 'hashcheck@supportiq.com',
            'password': raw_password,
            'password_confirm': raw_password,
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username='hashcheckuser')
        self.assertNotEqual(created_user.password, raw_password)
        self.assertTrue(check_password(raw_password, created_user.password))

    def test_weak_password_rejected(self):
        payload = {
            'username': 'weakpassuser',
            'email': 'weak@supportiq.com',
            'password': '123',
            'password_confirm': '123',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_mismatched_password_confirmation_rejected(self):
        payload = {
            'username': 'mismatchuser',
            'email': 'mismatch@supportiq.com',
            'password': 'SecurePassword2026!#',
            'password_confirm': 'DifferentPassword2026!#',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    # 4. Attempts to register with a privileged role
    def test_privileged_role_registration_rejected(self):
        for prohibited_role in ['ADMIN', 'MANAGER', 'AGENT']:
            with self.subTest(role=prohibited_role):
                payload = {
                    'username': f'user_{prohibited_role.lower()}',
                    'email': f'{prohibited_role.lower()}@supportiq.com',
                    'password': 'SecurePassword2026!#',
                    'password_confirm': 'SecurePassword2026!#',
                    'role': prohibited_role,
                }
                response = self.client.post(self.register_url, payload, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('role', response.data)

    # 5. Successful login and JWT token response
    def test_successful_login_returns_jwt_and_user_profile(self):
        payload = {
            'username': 'existinguser',
            'password': self.base_password,
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'existinguser')
        self.assertEqual(response.data['user']['role'], 'CUSTOMER')

    # 6. Invalid credentials handling
    def test_invalid_login_credentials(self):
        payload = {
            'username': 'existinguser',
            'password': 'WrongPassword123!',
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user_login(self):
        payload = {
            'username': 'ghost_user',
            'password': 'AnyPassword123!',
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 7. Authenticated and unauthenticated access to /api/auth/me/
    def test_unauthenticated_access_to_me_endpoint_rejected(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_to_me_endpoint_succeeds(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')
        self.assertEqual(response.data['email'], 'existing@supportiq.com')
        self.assertEqual(response.data['role'], 'CUSTOMER')
        self.assertNotIn('password', response.data)

    # 8. Profile updates cannot change role or privilege fields
    def test_profile_update_permitted_fields(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
        }
        response = self.client.patch(self.me_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'UpdatedFirst')
        self.assertEqual(response.data['last_name'], 'UpdatedLast')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.last_name, 'UpdatedLast')

    def test_profile_update_cannot_escalate_role_or_privileges(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'role': 'ADMIN',
            'is_staff': True,
            'is_superuser': True,
        }
        response = self.client.patch(self.me_url, payload, format='json')
        # Either validation error 400 or role remains CUSTOMER
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertTrue(any(f in response.data for f in ['role', 'is_staff', 'is_superuser']))
        else:
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.CUSTOMER)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_profile_update_duplicate_email_rejected(self):
        User.objects.create_user(
            username='otheruser',
            email='other@supportiq.com',
            password='StrongPassword123!',
        )
        self.client.force_authenticate(user=self.user)
        payload = {'email': 'other@supportiq.com'}
        response = self.client.patch(self.me_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # 9. JWT refresh endpoint behavior
    def test_jwt_token_refresh_succeeds_with_valid_token(self):
        login_res = self.client.post(self.login_url, {
            'username': 'existinguser',
            'password': self.base_password,
        }, format='json')
        refresh_token = login_res.data['refresh']

        refresh_res = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_jwt_token_refresh_fails_with_invalid_token(self):
        response = self.client.post(self.refresh_url, {'refresh': 'invalid.token.here'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
