import asyncio
import json
import unittest
from aiohttp.test_utils import TestServer, TestClient
from server import make_app

class ServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_stream_static_and_reconnect(self):
        async with TestClient(TestServer(make_app(demo=True))) as client:
            for path in ('/','/overlay','/app.js','/style.css'):
                response=await client.get(path)
                self.assertEqual(response.status,200)
                self.assertTrue(await response.read())
            response=await client.get('/events')
            line=await asyncio.wait_for(response.content.readline(),2)
            first=json.loads(line.decode().removeprefix('data: '))
            self.assertEqual(first['devices'][0]['guid'],'demo')
            for _ in range(90):
                line=await asyncio.wait_for(response.content.readline(),2)
                if line.startswith(b'data: '):
                    packet=json.loads(line[6:])
                    if packet['events']:break
            else:self.fail('No synthetic transitions delivered')
            self.assertGreater(packet['sequence'],0)
            response.close()
            reconnected=await client.get('/events')
            line=await asyncio.wait_for(reconnected.content.readline(),2)
            recovered=json.loads(line[6:])
            self.assertGreaterEqual(recovered['sequence'],packet['sequence'])
            self.assertTrue(recovered['events'])
            reconnected.close()
            self.assertEqual((await client.get('/../server.py')).status,404)
