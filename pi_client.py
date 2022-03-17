import websockets
import asyncio
import json
import time

pi_data = {
    'status': 'registration',
    'type': 'pi',
    'token': 123456
}


async def start_client():
    global pi_data
    url = 'wss://fathomless-plateau-34690.herokuapp.com/'
    # url = 'wss://visdom-ws-server.herokuapp.com/'
    # url = 'ws://127.0.0.1:1234'
    async with websockets.connect(url) as websocket:
        pi_data = json.dumps(pi_data)
        await websocket.send(pi_data)
        async for message in websocket:
            answer = json.loads(message)
            print(answer)
            if answer['answer'] == 'Start sharing':
                while True:
                    await websocket.send(json.dumps(
                        {'status': 'sharing', 'data': time.localtime()}))
                await websocket.send(
                    json.dumps({'status': 'Close connection'}))
            if answer['answer'] == 'Client forcibly terminated the connection':
                exit()


if __name__ == '__main__':
    print('>>> Pi start connection')
    asyncio.get_event_loop().run_until_complete(start_client())
    asyncio.get_event_loop().run_forever()
