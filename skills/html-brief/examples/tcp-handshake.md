---
title: TCP three-way handshake
subtitle: Why the third packet cannot be removed
theme: blueprint
mode: auto
---

## The exchange {span=2}

A connection starts with three packets. The client asks, the server answers and
names its own starting sequence number, then the client confirms. After the
third packet, both ends hold a number the other has acknowledged. Each side can
then drop a duplicated segment from an earlier session (RFC 793, section 3.4).

```sequence num
Client -> Server: SYN, seq=x
Server -.-> Client: SYN+ACK, seq=y, ack=x+1
Client -> Server: ACK, ack=y+1
note Client, Server: ESTABLISHED on both sides
```

## State changes {span=2}

A passive open moves the server to LISTEN. A duplicate SYN restarts the
timer, which is why a second client cannot silently take over a half-open
connection.

```flow TB
(CLOSED) -> LISTEN: passive open
LISTEN -> SYN-RECEIVED: get SYN, send SYN+ACK
SYN-RECEIVED -> *ESTABLISHED*: get ACK
ESTABLISHED -> CLOSE-WAIT: get FIN
CLOSE-WAIT -> LAST-ACK: send FIN
LAST-ACK -> CLOSED: get ACK
```

## Why three, not two {span=2}

> key: Two packets leave one side's belief about the other unconfirmed.
> Three packets make each side's claim visible to the other.

| Two packets | Three packets |
| --- | --- |
| Client cannot tell a live server from a lost reply | Both ends hold acknowledged numbers |
| A stale segment can enter the connection | A stale segment fails the sequence check |
| Half-open connections stay in the table | The server releases state after the ACK |

## Where the third packet goes {span=2}

TCP Fast Open (RFC 7413) removes the handshake round trip for returning
clients by carrying data in the SYN. It needs a cookie issued earlier, so the
first connection still pays for all three packets.

```flow LR
{Cookie present} -> SYN+data: fast path
{No cookie} -> SYN: three packets
SYN+data -> *1-RTT data*
SYN -> Server: wait for the ACK
```

## Limits to remember {span=2}

```limits
Delayed ACK window | 40-200ms | 60% | Linux default linger
Retransmit timeout | 1s initial | 25% | RTO doubles per round trip
Handshake cost | 1 RTT | 100% | Drops to 0.5 RTT with TFO and a cookie
```

> warn: A lossy mobile link often loses the third packet first.
> Budget for one extra handshake, not one extra packet.

## Numbers

```stat
Packets to establish | 3 | 1 RTT | ok
Packets with TFO and a cookie | 2 | 0.5 RTT | good
Protocol lines in RFC 793 | 3.4 | 30 pages | warn
```