from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import seedream_client
        self.client = seedream_client

    async def test_external_asset_download_omits_api_credential(self):
        headers = []
        def respond(request):
            headers.append(dict(request.headers))
            return httpx.Response(200, content=b"asset")
        async with httpx.AsyncClient(base_url="https://ark.example/v3", headers={"Authorization": "Bearer test-key"}, transport=httpx.MockTransport(respond)) as session:
            await self.client._download_image(session, "https://assets.example/image.png", 1)
        self.assertNotIn("authorization", headers[0])

    async def test_unknown_submission_is_not_repeated(self):
        calls = []
        def respond(request):
            calls.append(request)
            raise httpx.ReadTimeout("unknown", request=request)
        original = httpx.AsyncClient
        def session(**kwargs):
            return original(transport=httpx.MockTransport(respond), **kwargs)
        with patch.object(self.client.httpx, "AsyncClient", session):
            with self.assertRaises(self.client._APIError) as caught:
                await self.client._generate_with_retry("test-key", "https://ark.example/v3", {"prompt": "test"}, 1)
        self.assertEqual(caught.exception.code, "OutcomeUnknown")
        self.assertEqual(len(calls), 1)

    async def test_download_failure_never_repeats_generation(self):
        calls = []
        def respond(request):
            calls.append(request.method)
            if request.method == "POST":
                return httpx.Response(200, json={"data": [{"url": "https://assets.example/image.png"}]})
            return httpx.Response(503)
        original = httpx.AsyncClient
        def session(**kwargs):
            return original(transport=httpx.MockTransport(respond), **kwargs)
        with patch.object(self.client.httpx, "AsyncClient", session), patch.object(self.client, "MAX_RETRIES", 1), patch.object(self.client.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(self.client._APIError) as caught:
                await self.client._generate_with_retry("test-key", "https://ark.example/v3", {}, 1)
        self.assertEqual(caught.exception.code, "DownloadFailed")
        self.assertEqual(calls.count("POST"), 1)
        self.assertEqual(calls.count("GET"), 2)

    async def test_empty_success_is_a_failure(self):
        async with httpx.AsyncClient(base_url="https://ark.example/v3", transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": []}))) as session:
            with self.assertRaises(self.client._APIError) as caught:
                await self.client._generate_single(session, {}, 1)
        self.assertEqual(caught.exception.code, "EmptyImages")


if __name__ == "__main__":
    unittest.main()
