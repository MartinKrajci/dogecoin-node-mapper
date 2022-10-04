import socket
import time
import random
import struct
import asyncio

from node import Node
from crawl import create_message, create_payload_version, create_connection, get_version

magic_value = 0xc0c0c0c0
header_size = 24
buffer_size = 5000
nonce_size = 8

# Create payload for pong message
def create_payload_pong(nonce):
    payload = struct.pack('<Q', nonce)
    return payload

# Send pong message
def send_pong(message, writer):
    nonce = message[header_size:header_size + nonce_size]
    pong_message = create_message(magic_value, 'pong', nonce)

    writer.write(pong_message)

# Check command of recieved message and call adequate function
async def process_response(reader, writer, response_data):
    command = ''
    while True:
        while len(response_data) < header_size:
            response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=30)
            if not response_data_temp:
                raise Exception('Connection lost')
            response_data += response_data_temp
        _, command, size, _ = struct.unpack('<4s12sI4s',response_data[:header_size])

        while len(response_data) < header_size + size:
            response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=30)
            if not response_data_temp:
                raise Exception('Connection lost')
            response_data += response_data_temp

        command = command.decode()
        message = response_data[:header_size + size]
        response_data = response_data[header_size + size:]

        if 'pong' in command:
            return response_data
        elif 'ping' in command:
            send_pong(message, writer)

# Create payload for ping message
def create_payload_ping():
    payload = struct.pack('<Q', random.getrandbits(64))
    return payload

# Send ping message
def send_ping(writer):
    ping_payload = create_payload_ping()
    ping_message = create_message(magic_value, 'ping', ping_payload)
    writer.write(ping_message)

# Check if node is online
async def check_status(addr, port):
    if ':' in addr:
        addr_bin = socket.inet_pton(socket.AF_INET6, addr)
    elif '.' in addr:
        addr_bin = socket.inet_pton(socket.AF_INET, addr)
    else:
        print("Adress with wrong format: ", addr)
        return

    version_payload = create_payload_version(addr_bin, port)
    version_message = create_message(magic_value, 'version', version_payload)
    verack_message = create_message(magic_value, 'verack')
    response_data = b''

    reader, writer = await create_connection(addr, port)
    if not reader or not writer:
        return
    writer.write(version_message)
    try:
        user_agent, version, services, timestamp = await get_version(buffer_size, reader)
    except asyncio.TimeoutError:
        print('Did not recieve version message in time.')
        writer.close()
        return
    except Exception as e:
        print('Did not recieve version message.')
        print(e)
        writer.close()
        return

    writer.write(verack_message)

    while True:
        send_ping(writer)
        try:
            response_data = await process_response(reader, writer, response_data)
        except asyncio.TimeoutError:
            print('Did not recieve pong message in time.')
            writer.close()
            return
        except Exception as e:
            print('Did not recieve pong message.')
            print(e)
            writer.close()
            return
        print(addr, ' is alive.')
        Node.update_time(addr, port, int(time.time()))
        await asyncio.sleep(900)
        
async def ping_all():
    nodes = Node.get_all_nodes()
    tasks = []
    for node in nodes:
        tasks.append(asyncio.create_task(check_status(node.ip, node.port)))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ping_all())