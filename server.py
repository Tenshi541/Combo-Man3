"""Local controller collector and OBS Browser Source server."""
import os
os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import argparse
import asyncio
import json
from pathlib import Path
import time
import pygame
from aiohttp import web
from core import Timeline

ROOT = Path(__file__).parent / 'web'

class Collector:
    def __init__(self, demo=False):
        self.demo = demo
        self.timeline = Timeline()
        self.devices = {}
        self.metadata = []
        self.started = time.perf_counter()
        self.latest = {}
        self.task = None

    def add(self, index):
        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        self.devices[joystick.get_instance_id()] = joystick

    async def run(self):
        if not self.demo:
            pygame.display.init()
            pygame.display.set_mode((1, 1))
            pygame.joystick.init()
            for index in range(pygame.joystick.get_count()):
                self.add(index)
        try:
            while True:
                elapsed = time.perf_counter() - self.started
                if self.demo:
                    phase = int(elapsed * 4) % 12
                    controls = {'B0'} if phase in (2, 3, 7) else set()
                    if phase in (5, 6, 7):
                        controls.add('H0 Right')
                    self.timeline.update(0, controls, elapsed)
                    self.metadata = [dict(id=0, name='DEMO · synthetic inputs', guid='demo', axes=[0, 0], buttons=4, hats=1)]
                else:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYDEVICEADDED:
                            self.add(event.device_index)
                        elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                            # Preserve queued taps even if their final polled state is up.
                            controls = set(self.timeline.active.get(event.instance_id, set()))
                            control = f'B{event.button}'
                            if event.type == pygame.JOYBUTTONDOWN: controls.add(control)
                            else: controls.discard(control)
                            self.timeline.update(event.instance_id, controls, elapsed)
                        elif event.type == pygame.JOYDEVICEREMOVED:
                            joystick = self.devices.pop(event.instance_id, None)
                            if joystick:
                                joystick.quit()
                            self.timeline.remove(event.instance_id, elapsed)
                    self.metadata = []
                    for instance, joystick in list(self.devices.items()):
                        try:
                            controls = {f'B{i}' for i in range(joystick.get_numbuttons()) if joystick.get_button(i)}
                            axes = [round(joystick.get_axis(i), 3) for i in range(joystick.get_numaxes())]
                            for i, value in enumerate(axes):
                                if abs(value) >= .5:
                                    controls.add(f'A{i}{"+" if value > 0 else "-"}')
                            for i in range(joystick.get_numhats()):
                                x, y = joystick.get_hat(i)
                                if x: controls.add(f'H{i} {"Right" if x > 0 else "Left"}')
                                if y: controls.add(f'H{i} {"Up" if y > 0 else "Down"}')
                            self.timeline.update(instance, controls, elapsed)
                            self.metadata.append(dict(id=instance, name=joystick.get_name(), guid=joystick.get_guid(), axes=axes,
                                                      buttons=joystick.get_numbuttons(), hats=joystick.get_numhats()))
                        except pygame.error:
                            self.devices.pop(instance, None)
                            self.timeline.remove(instance, elapsed)
                # Capture is independent of rendering and stream delivery. OS scheduling
                # and device polling can make the actual interval longer than requested.
                await asyncio.sleep(.001)
        finally:
            if not self.demo:
                pygame.quit()

    def packet(self, since):
        result = self.timeline.snapshot(time.perf_counter() - self.started, self.metadata)
        result['events'] = [event for event in result['events'] if event['seq'] > since]
        return result


def make_app(demo=False):
    collector = Collector(demo)
    app = web.Application()

    async def page(request):
        return web.FileResponse(ROOT / 'index.html')

    async def asset(request):
        return web.FileResponse(ROOT / request.match_info['name'])

    async def stream(request):
        response = web.StreamResponse(headers={'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache'})
        await response.prepare(request)
        since = 0
        try:
            while True:
                packet = collector.packet(since)
                await asyncio.wait_for(response.write(('data: ' + json.dumps(packet) + '\n\n').encode()), 5)
                since = packet['sequence']
                await asyncio.sleep(1 / 60)
        except (ConnectionError, asyncio.TimeoutError):
            pass
        return response

    async def lifecycle(app):
        collector.task = asyncio.create_task(collector.run())
        # Surface startup failures before accepting connections.
        await asyncio.sleep(.02)
        if collector.task.done():
            collector.task.result()
        yield
        collector.task.cancel()
        try: await collector.task
        except asyncio.CancelledError: pass

    app.cleanup_ctx.append(lifecycle)
    app.router.add_get('/', page)
    app.router.add_get('/overlay', page)
    app.router.add_get('/events', stream)
    app.router.add_get('/{name:app.js|style.css}', asset)
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    print(f'Combo-Man3: http://127.0.0.1:{args.port} | OBS: http://127.0.0.1:{args.port}/overlay')
    web.run_app(make_app(args.demo), host='127.0.0.1', port=args.port)
