import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from parsers.ebay_parser import Ebay
from parsers.newegg_parser import Newegg


class TestEbay(unittest.IsolatedAsyncioTestCase):

    @patch('ebay_parser.httpx.AsyncClient')
    async def test_get_computers(self, MockAsyncClient):
        # Mocking the HTTP response
        mock_response = AsyncMock()
        mock_response.content = '<html><body>Mocked eBay page content</body></html>'
        mock_response.text = '<html><body>Mocked eBay page content</body></html>'
        MockAsyncClient.return_value.get.return_value = mock_response

        # Create an instance of the Ebay class
        ebay_store = Ebay(max_pages=1, items_per_page=10)
        
        # Call the get_computers method
        results = await ebay_store.get_computers()
        
        # Assert that the method returns a list of results
        self.assertIsInstance(results, list)


class TestNewegg(unittest.IsolatedAsyncioTestCase):

    @patch('newegg_parser.httpx.AsyncClient')
    async def test_get_computers(self, MockAsyncClient):
        # Mocking the HTTP response
        mock_response = AsyncMock()
        mock_response.content = '<html><body>Mocked Newegg page content</body></html>'
        mock_response.text = '<html><body>Mocked Newegg page content</body></html>'
        MockAsyncClient.return_value.get.return_value = mock_response

        # Create an instance of the Newegg class
        newegg_store = Newegg(max_pages=1, items_per_page=10)
        
        # Call the get_computers method
        results = await newegg_store.get_computers()
        
        # Assert that the method returns a list of results
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()
