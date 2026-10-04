---
title: TCP congestion control, 1988 to today
subtitle: Four algorithms that changed what the sender is allowed to do
theme: blueprint
mode: auto
---

## Milestones {span=2}

```timeline
1988-09 | Reno | Loss-based slow start with fast recovery
1998-06 | SACK | RFC 2018 lets the receiver report which segments arrived
2007-10 | CUBIC | RFC 8312 replaces time-based growth with a cubic window
2011-06 | PRR | RFC 6937 caps recovery volume after a drop
2016-09 | BBR | Models bandwidth and round-trip time instead of loss
```

## What each one optimises {span=2}

```kv
Reno | react to loss | simple, punishes deep buffers
SACK | react to loss | knows what survived a drop
CUBIC | react to loss | scales on long links with a fixed target
PRR | react to loss | recovery no longer overshoots
BBR | react to delay | keeps the pipe full on links with random loss
```

## Choosing an algorithm {span=2}

| Algorithm | Deep buffer link | Random loss | Long fat link | Complexity |
| --- | --- | --- | --- | --- |
| Reno | no | ok | no | low |
| CUBIC | ok | warn | ok | medium |
| BBR | ok | ok | ok | high |

> tip: Pick by link behaviour, not by benchmark headline. BBR wins where loss
> is random; CUBIC wins where loss marks a full queue.

## Recovery loop {span=2}

```sequence num
Sender -> Network: send cwnd of data
Network -.-> Sender: SACK blocks received
Sender -> Sender: cwnd = Wmax - (bytes delivered / bytes acked)
Sender -> Network: resume at a reduced window
```

## Notes

- RFC 2018 and RFC 6937 are dated by their publication month.
- BBR started as a Google draft; treat its version number as moving.
- Linux exposes per-algorithm sockets, so a test can compare them on one host.