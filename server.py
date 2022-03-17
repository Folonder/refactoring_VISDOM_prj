import asyncio
import os
import websockets
from json import dumps, loads
import logging
from shortcuts import *

logging.basicConfig(
    level=logging.DEBUG,
    filename="mylog.log",
    format="%(asctime)s - %(module)s - %(levelname)s"
           " - %(funcName)s: %(lineno)d - %(message)s",
    datefmt='%H:%M:%S',
)


class Webs:
    def __init__(self, websocket, data):
        self.websocket = websocket
        self.token = data[TOKEN]
        self.type = data[TYPE]


class Server:
    pairs = {}
    tokens = set()
    types = {GLASSES: 0, PI: 1}

    def __init__(self, port=1234):
        self.port = port

    def start(self):
        print(f'>>>> {SERV_ST_LISTEN}\n')
        logging.info(SERV_ST_LISTEN)
        return websockets.serve(self.server, '', self.port)

    async def server(self, websocket, path):
        message = loads(await websocket.recv())
        self.ws = Webs(websocket, message)
        status = await self.registration(message)
        if status == PAIR_ESTABLISHED:
            await self.ws.websocket.send(dumps(
                {ANSWER: SUCCESSFUL_REG}))
            await self.pairs[self.ws.token][0].websocket.send(
                dumps({ANSWER: status}))
            await self.pairs[self.ws.token][1].websocket.send(
                dumps({ANSWER: status}))
        else:
            await self.ws.websocket.send(dumps({ANSWER: status}))
        # await websocket.close(code=1000, reason='lol')
        try:
            async for message in self.ws.websocket:
                dict_message = loads(message)
                status = dict_message[STATUS]
                if status == READY_TO_GET:
                    await self.pairs[self.ws.token][1].websocket.send(dumps({
                        ANSWER: START_SHARING
                    }))
                elif status == SHARING:
                    await self.pairs[self.ws.token][0].websocket.send(dumps({
                        DATA: dict_message[DATA], ANSWER: SHARING
                    }))
                elif status == CLS_CONN:
                    await self.close_connection()

                await self.ws.websocket.pong()

        except websockets.exceptions.ConnectionClosedError as e:
            print(self.ws.token, self.ws.type, CLIENT_TERM_CONN)
            logging.info(
                f'{self.ws.token, self.ws.type} {CLIENT_TERM_CONN}')
            await self.close_connection()

    async def check_data(self, message):
        if not (message.get(STATUS) or message.get(TOKEN)
                or message.get(TYPE)):
            return UNSUPPORTED_CMD
        if message.get(STATUS) != REGISTRATION:
            return UNSUPPORTED_CMD
        if message.get(TOKEN):
            if not ((isinstance(message[TOKEN], int) and len(
                    str(message[TOKEN])) == 6)):
                return INCORRECT_TOKEN
        else:
            return NO_TOKEN
        if message[TOKEN] in self.tokens:
            return OCCUPIED_TOKEN
        if self.ws.token not in self.pairs:
            self.pairs[self.ws.token] = [None, None]
        if self.ws.type not in self.types:
            return INCORRECT_TYPE
        if self.pairs[self.ws.token][self.types[self.ws.type]]:
            return f'{self.ws.type.capitalize()} {OCCUPIED_TOKEN_CLIENT}'
        return CORRECT_DATA

    async def registration(self, message):
        response = await self.check_data(message)
        if response != CORRECT_DATA:
            return response
        self.pairs[self.ws.token][self.types[self.ws.type]] = self.ws
        if self.pairs[self.ws.token][0] and self.pairs[self.ws.token][1]:
            return ESTABLISHED_PAIR
        return SUCCESSFUL_REG

    async def close_connection(self):
        try:
            if self.pairs[self.ws.token][0]:
                await self.pairs[self.ws.token][0].websocket.send(
                    dumps({ANSWER: CLIENT_TERM_CONN}))
            if self.pairs[self.ws.token][1]:
                await self.pairs[self.ws.token][1].websocket.send(
                    dumps({ANSWER: CLIENT_TERM_CONN}))
        except (websockets.exceptions.ConnectionClosedError,) as e:
            pass
        del self.pairs[self.ws.token]
        if self.ws.token in self.tokens:
            self.tokens.remove(self.ws.token)


if __name__ == '__main__':
    # port = 1234
    port = int(os.environ['PORT'])
    server = Server(port=port)
    asyncio.get_event_loop().run_until_complete(server.start())
    asyncio.get_event_loop().run_forever()
