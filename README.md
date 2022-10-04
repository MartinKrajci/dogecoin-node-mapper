# Blockchain and Decentralised Applicatons
## Platform for monitoring nodes in the dogecoin p2p network

## Description

This application was made for mapping and monitoring nodes in dogecoin network, without need of running dogecoin client, because P2P communication was used. At the start of application, IP addresses from first_node.txt file are used to estabilsh first connection. This node is then asked for other known IP addresses, and every node from that list is asked cyclically. When all available nodes were found, application then ping them and updates time when they were last seen.

## Run
Application run in two containers, whereas PostgreSQL database is running in first and monitor in second.
Containers can be started with:
```bash
$ sudo bash start_docker.sh
```
After that you will be prompted to type your password.

## Output
When new node is found, its IP and port is written to standard output with time when it was found. All details about that node, like IP, port, user agent, version or service number are saved into database. 

Example output of mapper can look like this:
```
23:34:26.487429  || Adding IP:  35.82.32.180  Port:  8333
23:34:26.992332  || Adding IP:  89.149.218.113  Port:  22556
23:34:27.478289  || Adding IP:  67.220.3.113  Port:  22556
```
After all aviable dogecoin nodes are found and saved into database, application is sending ping message to nodes every 15 minutes. If node responds with pong message, time in the database is actualised with time when message was recieved. Node's IP is written to standard output with message "<IP> is alive.".

Example output of ping tool can look like this:
```
35.238.164.153  is alive.
23.251.156.33  is alive.
165.22.228.211  is alive.
```