"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_list_accounts(self):
        """It should List all Accounts"""
        # Create some accounts
        accounts = self._create_accounts(3)

        # Send GET request to list all accounts
        response = self.client.get(BASE_URL)

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the accounts returned by the API
        data = response.get_json()

        # Check that we received 3 accounts
        self.assertEqual(len(data), 3)

        # Check that the accounts returned are the ones we created
        self.assertEqual(data[0]["id"], accounts[0].id)
        self.assertEqual(data[1]["id"], accounts[1].id)
        self.assertEqual(data[2]["id"], accounts[2].id)

    def test_list_accounts_no_accounts(self):
        """It should return an empty list when there are no Accounts"""
        # The database is empty because setUp() clears it before each test

        # Send GET request
        response = self.client.get(BASE_URL)

        # It should still return 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The response should be an empty list
        data = response.get_json()
        self.assertEqual(data, [])

    def test_read_account(self):
        """It should Read an Account"""
        # Create an account
        accounts = self._create_accounts(1)
        account = accounts[0]

        # Send GET request for that account
        response = self.client.get(f"{BASE_URL}/{account.id}")

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the account returned by the API
        data = response.get_json()

        # Check that the correct account was returned
        self.assertEqual(data["id"], account.id)
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(data["phone_number"], account.phone_number)

    def test_read_account_not_found(self):
        """It should return 404 when an Account does not exist"""
        # Use an ID that does not exist
        account_id = 99999

        # Send GET request
        response = self.client.get(f"{BASE_URL}/{account_id}")

        # Account should not be found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account(self):
        """It should Update an Account"""
        # Create an account
        accounts = self._create_accounts(1)
        account = accounts[0]

        # Create updated account information
        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "address": "Updated Address",
            "phone_number": "0123456789"
        }

        # Send PUT request
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=updated_data
        )

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get the updated account returned by the API
        data = response.get_json()

        # Check that the account was updated
        self.assertEqual(data["id"], account.id)
        self.assertEqual(data["name"], updated_data["name"])
        self.assertEqual(data["email"], updated_data["email"])
        self.assertEqual(data["address"], updated_data["address"])
        self.assertEqual(data["phone_number"], updated_data["phone_number"])

    def test_update_account_not_found(self):
        """It should return 404 when updating an Account that does not exist"""
        # Use an ID that does not exist
        account_id = 99999

        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "address": "Updated Address",
            "phone_number": "0123456789"
        }

        # Send PUT request
        response = self.client.put(
            f"{BASE_URL}/{account_id}",
            json=updated_data
        )

        # Account should not be found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        # Create an account
        accounts = self._create_accounts(1)
        account = accounts[0]

        # Send DELETE request
        response = self.client.delete(f"{BASE_URL}/{account.id}")

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # The response should have an empty body
        self.assertEqual(response.data, b"")

        # Verify that the account was actually deleted
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should return 204 when deleting an Account that does not exist"""
        # Use an ID that does not exist
        account_id = 99999

        # Send DELETE request
        response = self.client.delete(f"{BASE_URL}/{account_id}")

        # Deleting a non-existent account should do nothing
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # The response should have an empty body
        self.assertEqual(response.data, b"")