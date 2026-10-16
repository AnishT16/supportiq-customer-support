from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from customers.models import Customer
from .models import Ticket

UserModel = get_user_model()


class TicketAPITests(APITestCase):
    def setUp(self):
        # 1. Users for all roles
        self.customer_user_1 = UserModel.objects.create_user(
            username='cust1',
            email='cust1@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.customer_user_2 = UserModel.objects.create_user(
            username='cust2',
            email='cust2@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.customer_user_no_profile = UserModel.objects.create_user(
            username='cust_noprofile',
            email='cust_noprofile@supportiq.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.agent_user_1 = UserModel.objects.create_user(
            username='agent1',
            email='agent1@supportiq.com',
            password='Password123!',
            role=User.Role.AGENT
        )
        self.agent_user_2 = UserModel.objects.create_user(
            username='agent2',
            email='agent2@supportiq.com',
            password='Password123!',
            role=User.Role.AGENT
        )
        self.manager_user = UserModel.objects.create_user(
            username='manager1',
            email='manager1@supportiq.com',
            password='Password123!',
            role=User.Role.MANAGER
        )
        self.admin_user = UserModel.objects.create_user(
            username='admin1',
            email='admin1@supportiq.com',
            password='Password123!',
            role=User.Role.ADMIN
        )

        # 2. Customer Profiles
        self.customer_profile_1 = Customer.objects.create(
            user=self.customer_user_1,
            name='Alice Customer',
            email='alice@supportiq.com',
            phone='+1112223334'
        )
        self.customer_profile_2 = Customer.objects.create(
            user=self.customer_user_2,
            name='Bob Customer',
            email='bob@supportiq.com',
            phone='+1444555666'
        )

        # 3. Base Tickets
        self.ticket_1 = Ticket.objects.create(
            customer=self.customer_profile_1,
            subject='Delivery Delay on Order #1001',
            description='Package has not arrived for 3 days past ETA.',
            category=Ticket.Category.DELIVERY,
            priority=Ticket.Priority.HIGH,
            status=Ticket.Status.OPEN,
            assigned_to=self.agent_user_1
        )
        self.ticket_2 = Ticket.objects.create(
            customer=self.customer_profile_2,
            subject='Payment Failed during Checkout',
            description='Card was charged but order status says unpaid.',
            category=Ticket.Category.PAYMENT,
            priority=Ticket.Priority.CRITICAL,
            status=Ticket.Status.OPEN,
            assigned_to=None  # Unassigned
        )

        self.list_url = reverse('tickets:ticket-list')
        self.detail_url_1 = reverse('tickets:ticket-detail', kwargs={'pk': self.ticket_1.pk})
        self.detail_url_2 = reverse('tickets:ticket-detail', kwargs={'pk': self.ticket_2.pk})

    # 1. Ticket creation with valid data
    def test_customer_can_create_ticket_for_own_profile(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {
            'subject': 'Damaged item received',
            'description': 'The outer box was smashed and the screen cracked.',
            'category': 'PRODUCT',
            'priority': 'HIGH',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subject'], 'Damaged item received')
        self.assertEqual(response.data['category'], 'PRODUCT')
        self.assertEqual(response.data['priority'], 'HIGH')
        self.assertEqual(response.data['status'], 'OPEN')
        self.assertEqual(response.data['customer_name'], 'Alice Customer')
        self.assertTrue(response.data['ticket_number'].startswith('TIK-'))

    def test_customer_without_profile_cannot_create_ticket(self):
        self.client.force_authenticate(user=self.customer_user_no_profile)
        payload = {
            'subject': 'Help inquiry',
            'description': 'I have a question.',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_staff_can_create_ticket_for_customer(self):
        self.client.force_authenticate(user=self.manager_user)
        payload = {
            'customer_id': self.customer_profile_2.id,
            'subject': 'Staff initiated ticket',
            'description': 'Proactive ticket generated by support.',
            'category': 'DELIVERY',
            'priority': 'MEDIUM',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_name'], 'Bob Customer')

    # 2. Required fields and invalid choice validation
    def test_invalid_category_and_priority_rejected(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {
            'subject': 'Invalid choices test',
            'description': 'Testing validation.',
            'category': 'NON_EXISTENT_CATEGORY',
            'priority': 'SUPER_URGENT',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)
        self.assertIn('priority', response.data)

    # 3. Unique ticket number generation
    def test_ticket_number_is_unique_and_formatted(self):
        t1 = Ticket.objects.create(
            customer=self.customer_profile_1,
            subject='Test 1',
            description='Desc 1'
        )
        t2 = Ticket.objects.create(
            customer=self.customer_profile_1,
            subject='Test 2',
            description='Desc 2'
        )
        self.assertTrue(t1.ticket_number.startswith('TIK-'))
        self.assertTrue(t2.ticket_number.startswith('TIK-'))
        self.assertNotEqual(t1.ticket_number, t2.ticket_number)

    # 4. Customer isolation between different accounts
    def test_customer_isolation_list_and_detail(self):
        # Alice lists tickets: only sees ticket 1
        self.client.force_authenticate(user=self.customer_user_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.ticket_1.id, ticket_ids)
        self.assertNotIn(self.ticket_2.id, ticket_ids)

        # Alice attempts to retrieve Bob's ticket: 404
        response_detail = self.client.get(self.detail_url_2)
        self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)

        # Alice attempts to update Bob's ticket: 404
        response_update = self.client.patch(self.detail_url_2, {'subject': 'Hacked Subject'}, format='json')
        self.assertEqual(response_update.status_code, status.HTTP_404_NOT_FOUND)

    # 5. Agent access to assigned and unassigned tickets
    def test_agent_can_see_assigned_and_unassigned_tickets(self):
        # Agent 1 has ticket 1 assigned, and ticket 2 is unassigned
        self.client.force_authenticate(user=self.agent_user_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.ticket_1.id, ticket_ids)
        self.assertIn(self.ticket_2.id, ticket_ids)

        # Agent 2 has no tickets assigned, but can see unassigned ticket 2
        self.client.force_authenticate(user=self.agent_user_2)
        response_agent_2 = self.client.get(self.list_url)
        agent_2_ids = [item['id'] for item in response_agent_2.data['results']]
        self.assertNotIn(self.ticket_1.id, agent_2_ids)  # Assigned to agent 1
        self.assertIn(self.ticket_2.id, agent_2_ids)      # Unassigned

    def test_agent_cannot_reassign_tickets(self):
        self.client.force_authenticate(user=self.agent_user_1)
        payload = {'assigned_to_id': self.agent_user_2.id}
        response = self.client.patch(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assigned_to_id', response.data)

    def test_agent_cannot_delete_tickets(self):
        self.client.force_authenticate(user=self.agent_user_1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Ticket.objects.filter(pk=self.ticket_1.pk).exists())

    # 6. Manager assignment permissions
    def test_manager_can_assign_ticket_to_eligible_agent(self):
        self.client.force_authenticate(user=self.manager_user)
        assign_url = reverse('tickets:ticket-assign', kwargs={'pk': self.ticket_2.pk})
        payload = {'assigned_to_id': self.agent_user_2.id}
        response = self.client.post(assign_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_to_username'], 'agent2')

        self.ticket_2.refresh_from_db()
        self.assertEqual(self.ticket_2.assigned_to, self.agent_user_2)

    def test_cannot_assign_ticket_to_customer_user(self):
        self.client.force_authenticate(user=self.manager_user)
        assign_url = reverse('tickets:ticket-assign', kwargs={'pk': self.ticket_2.pk})
        payload = {'assigned_to_id': self.customer_user_1.id}
        response = self.client.post(assign_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 7. Admin access and deletion
    def test_admin_can_manage_and_delete_ticket(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url_2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ticket.objects.filter(pk=self.ticket_2.pk).exists())

    # 8. Unauthorized & unauthenticated requests
    def test_unauthenticated_requests_rejected(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.list_url, {}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)

    # 9. Protected field and role escalation attempts
    def test_customer_cannot_change_status_or_assignment_directly(self):
        self.client.force_authenticate(user=self.customer_user_1)
        payload = {
            'status': 'RESOLVED',
            'assigned_to_id': self.agent_user_1.id,
            'priority': 'CRITICAL'
        }
        response = self.client.patch(self.detail_url_1, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, Ticket.Status.OPEN)
        self.assertEqual(self.ticket_1.priority, Ticket.Priority.HIGH)

    # 10. Status transitions, resolution timestamps, and reopening behavior
    def test_resolution_and_reopening_workflow(self):
        self.client.force_authenticate(user=self.agent_user_1)
        resolve_url = reverse('tickets:ticket-resolve', kwargs={'pk': self.ticket_1.pk})
        reopen_url = reverse('tickets:ticket-reopen', kwargs={'pk': self.ticket_1.pk})

        # 1. Resolve ticket
        res_response = self.client.post(resolve_url)
        self.assertEqual(res_response.status_code, status.HTTP_200_OK)
        self.assertEqual(res_response.data['status'], 'RESOLVED')
        self.assertIsNotNone(res_response.data['resolved_at'])

        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, Ticket.Status.RESOLVED)
        self.assertIsNotNone(self.ticket_1.resolved_at)

        # 2. Reopen ticket
        reopen_response = self.client.post(reopen_url)
        self.assertEqual(reopen_response.status_code, status.HTTP_200_OK)
        self.assertEqual(reopen_response.data['status'], 'OPEN')
        self.assertIsNone(reopen_response.data['resolved_at'])

        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, Ticket.Status.OPEN)
        self.assertIsNone(self.ticket_1.resolved_at)

    def test_customer_can_close_own_ticket(self):
        self.client.force_authenticate(user=self.customer_user_1)
        close_url = reverse('tickets:ticket-close', kwargs={'pk': self.ticket_1.pk})
        response = self.client.post(close_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'CLOSED')

        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, Ticket.Status.CLOSED)

    # 11. Filtering, search, and pagination
    def test_query_parameter_filtering_and_search(self):
        self.client.force_authenticate(user=self.manager_user)

        # Filter by status
        res_status = self.client.get(f"{self.list_url}?status=OPEN")
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res_status.data['count'], 2)

        # Filter by category
        res_cat = self.client.get(f"{self.list_url}?category=DELIVERY")
        self.assertEqual(res_cat.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cat.data['count'], 1)
        self.assertEqual(res_cat.data['results'][0]['id'], self.ticket_1.id)

        # Search by subject text
        res_search = self.client.get(f"{self.list_url}?search=Checkout")
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(res_search.data['count'], 1)
        self.assertEqual(res_search.data['results'][0]['id'], self.ticket_2.id)

    def test_customer_query_params_cannot_leak_other_tickets(self):
        # Alice passes ?customer=<Bob's customer ID>
        self.client.force_authenticate(user=self.customer_user_1)
        res = self.client.get(f"{self.list_url}?customer={self.customer_profile_2.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should return 0 items because base queryset only contains Alice's tickets
        self.assertEqual(res.data['count'], 0)
