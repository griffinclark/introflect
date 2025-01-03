import pytest
from src.resources.firebase.firebase_init import firestore_client

# Constants for the test
TEST_COLLECTION = "test_collection"
TEST_DOCUMENT = "test_document"
TEST_DATA = {"field": "value"}


@pytest.fixture(scope="module")
def firestore_setup():
    """Fixture to set up and tear down Firestore test data."""
    # Set up: Create a test document
    firestore_client.collection(TEST_COLLECTION).document(TEST_DOCUMENT).set(TEST_DATA)
    yield
    # Tear down: Delete the test document
    firestore_client.collection(TEST_COLLECTION).document(TEST_DOCUMENT).delete()


def test_firestore_write(firestore_setup):
    """Test writing data to Firestore."""
    doc_ref = firestore_client.collection(TEST_COLLECTION).document(TEST_DOCUMENT)
    doc = doc_ref.get()
    assert doc.exists, "Test document should exist in Firestore."
    assert doc.to_dict() == TEST_DATA, "Test document data should match."


def test_firestore_read(firestore_setup):
    """Test reading data from Firestore."""
    doc_ref = firestore_client.collection(TEST_COLLECTION).document(TEST_DOCUMENT)
    doc = doc_ref.get()
    assert doc.exists, "Test document should exist in Firestore."
    assert doc.to_dict()["field"] == "value", "Field value should match the test data."


def test_firestore_delete():
    """Test deleting data from Firestore."""
    # Create a document to test deletion
    temp_doc_ref = firestore_client.collection(TEST_COLLECTION).document("temp_document")
    temp_doc_ref.set(TEST_DATA)
    temp_doc_ref.delete()

    # Check that the document no longer exists
    assert not temp_doc_ref.get().exists, "Temporary document should be deleted."
