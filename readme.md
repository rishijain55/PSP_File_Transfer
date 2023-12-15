# Computer Networks Project: Peer-to-Peer (PSP) File Distribution Simulation

## Overview

This project simulates a Peer-Server-Peer (PSP) network with a server and multiple clients, aiming to distribute a file among clients using both UDP and TCP communication. The file is divided into chunks, and each client must obtain all the chunks to reconstruct the complete file. The simulation is conducted in two parts, where Part 1 uses TCP for data transfer and UDP for control messages, while Part 2 employs TCP for control and UDP for data transfer.

## Part 1


### Simulation Steps
1. Simulate a server and n clients (n=5 initially).
2. Download the file and distribute it in n chunks among clients.
3. Clients operate independently, requesting missing chunks from the server using UDP and TCP.
4. Server implements LRU cache policy for chunk storage.
5. Simulation ends when each client has all required chunks.

### Execution
- Run `part1.sh` to execute Part 1 of the simulation.
- Adjust the file path in `server.py`.

### Configuration
- Clients have access to two multiple ports.
- Server can use n multiple ports to communicate with clients concurrently.

## Part 2

### Simulation Changes
- Control messages are carried out using TCP.
- UDP is used for all data transfers.

### Execution
- Run `part2.sh` to execute Part 2 of the simulation.
- Ensure the correct file path in `server.py`.
## Additional Details

### Port Usage
- Clients: Access to two multiple ports (justify the chosen number in the report).
- Server: Access to n multiple ports for concurrent communication with clients.

### Handling Packet Loss
- Account for packet loss in UDP communication.

## Report

Please refer to the accompanying report for justifications regarding the choice of ports, handling packet loss, and any other relevant details.

## Note
- Ensure Python is installed.
- The simulation progress can be observed in the terminal during execution.

Feel free to reach out for any clarifications or assistance!
