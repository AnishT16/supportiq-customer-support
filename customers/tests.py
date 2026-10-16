from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Customer

User = get_user_model()


class CustomerAPITests(APITestCase):
    def setUp(self):
        # Create users for all 4 roles
        self.customer_user_1 = User.objects.create_user(
            username='cust1',
            email='cust1@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.customer_user_2 = User.objects.create_user(
            username='cust2',
            email='cust2@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.customer_user_without_profile = User.objects.create_user(
            username='cust_new',
            email='cust_new@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.agent_user = User.objects.create_user(
            username='agent1',
            email='agent1@supportiq.com',
            password='Password123!',
            role=User.Role.AGENT
        )
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@supportiq.com',
            password='Password123!',
            role=User.Role.MANAGER
        )
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@supportiq.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # Baseline customer profiles
        self.customer_1 = Customer.objects.create(
            user=self.customer_user_1,
            name='Alice Customer',
            email='alice@supportiq.com',
            phone='+1234567890',
            address='123 Main Street'
        )
        self.customer_2 = Customer.objects.create(
            user=self.customer_user_2,
            name='Bob Customer',
            email='bob@supportiq.com',
            phone='+1987654321',
            address='456 Elm Street'
        )

        self.list_create_url = reverse('customers:customer-list')
        self.detail_url_1 = reverse('customers:customer-detail', kwargs={'pk': self.customer_1.pk})
        self.detail_url_2 = reverse('customers:customer-detail', kwargs={'pk': self.customer_2.pk})

    # 1. Successful customer creation
    def test_customer_can_create_own_profile(self):
        self.client.force_authenticate(user=self.customer_user_without_profile)
        payload = {
            'name': 'Charlie New',
            'email': 'charlie@supportiq.com',
            'phone': '+1122334455',
            'address': '789 Oak Avenue'
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Charlie New')
        self.assertEqual(response.data['email'], 'charlie@supportiq.com')
        self.assertEqual(response.data['username'], 'cust_new')

        # Verify DB association
        profile = Customer.objects.get(user=self.customer_user_without_profile)
        self.assertEqual(profile.name, 'Charlie New')

    def test_customer_cannot_create_duplicate_profile(self):
        # Customer 1 already has a profile
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {
            'name': 'Duplicate Alice',
            'email': 'alice_dup@supportiq.com',
            'phone': '+1234567890'
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 2. Listing and retrieving permitted customer records
    def test_customer_only_sees_own_profile_in_list(self):
        self.client.force_authenticate(user=self.customer_user_1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return Alice's profile
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.customer_1.id)

    def test_agent_and_manager_see_all_customers_in_list(self):
        for staff_user in [self.agent_user, self.manager_user, self.admin_user]:
            with self.subTest(role=staff_user.role):
                self.client.force_authenticate(user=staff_user)
                response = self.client.get(self.list_create_url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertGreaterEqual(len(response.data), 2)

    def test_customer_can_retrieve_own_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        response = self.client.get(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'alice@supportiq.com')

    def test_customer_cannot_retrieve_other_customer_profile(self):
        # Alice tries to retrieve Bob's profile
        self.client.force_authenticate(user=self.customer_user_1)
        response = self.client.get(self.detail_url_2)
        # Returns 404 because customer's queryset excludes other users
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 3. Updating and partially updating customer data
    def test_customer_can_update_own_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {
            'name': 'Alice Updated',
            'email': 'alice.updated@supportiq.com',
            'phone': '+1999888777',
            'address': 'New Address 456'
        }
        response = self.client.put(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Alice Updated')
        self.assertEqual(response.data['email'], 'alice.updated@supportiq.com')

        self.customer_1.refresh_from_db()
        self.assertEqual(self.customer_1.name, 'Alice Updated')

    def test_customer_can_partially_update_own_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {'phone': '+1444333222'}
        response = self.client.patch(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], '+1444333222')

    def test_customer_cannot_update_other_customer_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {'name': 'Hacked Name'}
        response = self.client.patch(self.detail_url_2, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 4. Deleting a customer when permitted
    def test_customer_cannot_delete_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Customer.objects.filter(pk=self.customer_1.pk).exists())

    def test_agent_cannot_delete_customer_profile(self):
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Customer.objects.filter(pk=self.customer_1.pk).exists())

    def test_manager_can_delete_customer_profile(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.delete(self.detail_url_2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=self.customer_2.pk).exists())

    def test_admin_can_delete_customer_profile(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=self.customer_1.pk).exists())

    # 5. Unauthenticated requests are rejected
    def test_unauthenticated_requests_rejected(self):
        self.assertEqual(self.client.get(self.list_create_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.list_create_url, {}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.patch(self.detail_url_1, {}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)

    # 6. Invalid data and duplicate email handling
    def test_duplicate_customer_email_rejected(self):
        self.client.force_authenticate(user=self.customer_user_without_profile)
        payload = {
            'name': 'Duplicate Email Customer',
            'email': 'ALICE@SUPPORTIQ.COM',  # Existing Alice's email
            'phone': '+1999999999'
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_invalid_phone_number_rejected(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {'phone': 'invalid_phone_number_letters'}
        response = self.client.patch(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response.data)

    # 7. Protected ownership fields and escalation attempts
    def test_cannot_reassign_customer_ownership(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {'user_id': self.customer_user_2.id}
        response = self.client.patch(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.customer_1.refresh_from_db()
        self.assertEqual(self.customer_1.user, self.customer_user_1)

    # 8. Staff / Admin creating a customer for a user
    def test_admin_can_create_customer_for_user(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'user_id': self.customer_user_without_profile.id,
            'name': 'Admin Created Customer',
            'email': 'admin_created@supportiq.com',
            'phone': '+1555666777',
            'address': 'Admin Street 1'
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'cust_new')
