import socket
import time
import random
import struct
import hashlib
import asyncio
from datetime import datetime

from node import Node

magic_value = 0xc0c0c0c0
header_size = 24
default_doge_port = 22556

# Create binary data which describe given node
# Used in version message
def describe_node(addr, port, service):
    if len(addr) == 4:
        network_address = struct.pack('>Q16sH', service, bytearray.fromhex('00000000000000000000ffff') + addr, port)
    elif len(addr) == 16:
        network_address = struct.pack('>Q16sH', service, addr, port)
    return(network_address)

# Create message with given command
def create_message(magic, command, payload=b''):
    if not payload:
        checksum = b'\x5d\xf6\xe0\xe2'
    else:
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[0:4]
    header = struct.pack('<L12sL4s', magic, command.encode() + ((12 - len(command)) * chr(0)).encode(), len(payload), checksum)
    return(header + payload)

# Create payload for message
def create_payload_version(peer_ip_address, port=22556):
    version = 70015
    services = 0
    timestamp = int(time.time())
    addr_local = describe_node(bytearray.fromhex('7f000001'), 22556, 0)
    addr_peer = describe_node(peer_ip_address, port, 1)
    nonce = random.getrandbits(64)
    sub_version = '/Shibetoshi:1.14.5/'
    start_height = 0
    relay = 0
    payload = struct.pack('<LQQ26s26sQB' + str(len(sub_version)) + 'sLB', version, services, timestamp, addr_peer,
                          addr_local, nonce, len(sub_version), sub_version.encode(), start_height, relay)
    return(payload)

# Helper function. Helps unpack variable lenght string
def unpack_compact_size(buffer):
    num = struct.unpack("<B", buffer[:1])[0]
    offset = 1
    if num == 0xfd:
        num = struct.unpack("<H", buffer[1:3])[0]
        offset = 3
    elif num == 0xfe:
        num = struct.unpack("<I", buffer[1:5])[0]
        offset = 5
    elif num == 0xff:
        num = struct.unpack("<Q", buffer[1:9])[0]
        offset = 9
    return num, offset

# Unpack recieved version message
async def get_version(buffer_size, reader):
    command = ''
    while 'version' not in command:
        response_data = await asyncio.wait_for(reader.read(buffer_size), timeout=4)
        if not response_data:
            raise Exception("Connection lost")
        while len(response_data) < header_size:
            response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=4)
            if not response_data_temp:
                raise Exception("Connection lost")
            response_data += response_data_temp
        _, command, size, _ = struct.unpack('<4s12sI4s',response_data[:24])
        try:
            command = command.decode()
        except:
            command = ''

    size += header_size

    while len(response_data) < size:
        response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=4)
        if not response_data_temp:
            raise Exception("Connection lost")
        response_data += response_data_temp

    version, services, timestamp, _, _, _, services_trans, _, _, _ = struct.unpack(
        '<IQQQ16sHQ16sHQ', response_data[header_size:header_size + 80])
    num, offset = unpack_compact_size(response_data[header_size + 80:])
    user_agent = response_data[header_size + 80 + offset: header_size + 80 + offset + num]
    start_heigh = struct.unpack('I', response_data[header_size + 80 + offset + num:header_size + 80 + offset + num + 4])
    if len(response_data[header_size + 80 + offset + num + 4:]) == 1:
        relay = response_data[header_size + 80 + offset + num + 4:]

    return user_agent, version, services, timestamp

async def get_addresses(buffer_size, reader):
    command = ''
    while 'addr' not in command:
        response_data = await asyncio.wait_for(reader.read(buffer_size), timeout=300)
        if not response_data:
            raise Exception("Connection lost")
        while len(response_data) < header_size:
            response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=300)
            if not response_data_temp:
                raise Exception("Connection lost")
            response_data += response_data_temp
        _, command, size, _ = struct.unpack('<4s12sI4s',response_data[:header_size])
        try:
            command = command.decode()
        except:
            command = ''
    
    # header size
    size += header_size
    # while not whole message
    while len(response_data) < size:
        response_data_temp = await asyncio.wait_for(reader.read(buffer_size), timeout=300)
        if not response_data_temp:
            raise Exception("Connection lost")
        response_data += response_data_temp

    # cut possible other commands at the end of message
    response_data = response_data[header_size:size]
    num, offset = unpack_compact_size(response_data)
    response_data = response_data[offset:]

    nodes = []
    for _, _, addr, port in struct.iter_unpack('<IQ16sH', response_data):
        if addr[:12] != bytes.fromhex('00000000000000000000ffff'):
            nodes.append((socket.inet_ntop(socket.AF_INET6,addr), socket.ntohs(port)))
        else:
            nodes.append((socket.inet_ntop(socket.AF_INET, addr[12:]), socket.ntohs(port)))
    return nodes

# Connect to node with given address and port
async def create_connection(addr, port=22556):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(
            addr, port), timeout=2)

    except asyncio.TimeoutError:
        return None, None
    except ConnectionRefusedError:
        return None, None
    except:
        return None, None

    return (reader, writer)


# Get address from file if first connection.
# Connect to given node and try to get another addresses.
async def get_node(addr=None, port=22556):
    buffer_size = 10000

    verack_message = create_message(magic_value, 'verack')
    getdata_message = create_message(magic_value, 'getaddr')

    #If first connection, get IP address from file
    if not addr:
        file = open('first_node.txt', 'r')

        reader, writer = None, None
        while not reader or not writer:
            addr = file.readline()[:-1]
            reader, writer = await asyncio.wait_for(create_connection(addr), timeout=2)
    else:
        reader, writer = await create_connection(addr, port)
        if not reader or not writer:
            return

    if ':' in addr:
        ip_version = 6
        addr_bin = socket.inet_pton(socket.AF_INET6, addr)
    elif '.' in addr:
        ip_version = 4
        addr_bin = socket.inet_pton(socket.AF_INET, addr)
    else:
        #print("Adress with wrong format: ", addr)
        return

    version_payload = create_payload_version(addr_bin)
    version_message = create_message(magic_value, 'version', version_payload)
    writer.write(version_message)
    try:
        user_agent, version, services, timestamp = await get_version(buffer_size, reader)
    except asyncio.TimeoutError:
        writer.close()
        return
    except Exception as e:
        #print(e)
        writer.close()
        return

    writer.write(verack_message)

    writer.write(getdata_message)
    try:
        nodes = await get_addresses(buffer_size, reader)
    except asyncio.TimeoutError:
        writer.close()
        return
    except Exception as e:
        #print(e)
        writer.close()
        return

    writer.close()

    print(datetime.now().time(), ' || Adding IP: ', addr, ' Port: ', port)
    Node.upsert_node(addr, port, ip_version, user_agent.decode(), version, services, timestamp)
    tasks = []
    for next_addr, next_port in nodes:
        if Node.node_exists(next_addr, next_port):
            continue
        tasks.append(asyncio.create_task(get_node(next_addr, int(next_port))))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    #loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    # Get first node
    try:
        loop.run_until_complete(get_node())
    except Exception as e:
        print('Uknown error occurred\n', e, '\n')