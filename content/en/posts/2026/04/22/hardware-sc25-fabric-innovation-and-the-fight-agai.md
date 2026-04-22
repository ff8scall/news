---
title: "SC25: Fabric Innovation and the Fight Against Tail Latency with Cornelis Networks CEO Lisa Spelman"
date: "2026-04-22T12:02:44Z"
description: "At the Supercomputing 25 (SC25) conference, the spotlight has shifted from raw FLOPS to the 'fabric'—the interconnect technology that determines whether a cluster of 50,000 GPUs acts as a unified supercomputer or a fragmented collection of nodes. Lisa Spelman, CEO of Cornelis Networks and a veteran of the data center industry, provided a compelling roadmap for the future of HPC networking. Her insights centered on a critical, often overlooked metric in the AI era: tail latency."
image: "/images/posts/2026/04/22/hardware-sc25-fabric-innovation-and-the-fight-agai_gen.jpg"
clusters: ["hardware"]
categories: ["chips"]
tags: []
featured: false
---
## Executive Summary
- At the Supercomputing 25 (SC25) conference, the spotlight has shifted from raw FLOPS to the "fabric"—the interconnect technology that determines whether a cluster of 50,000 GPUs acts as a unified supercomputer or a fragmented collection of nodes. Lisa Spelman, CEO of Cornelis Networks and a veteran of the data center industry, provided a compelling roadmap for the future of HPC networking. Her insights centered on a critical, often overlooked metric in the AI era: tail latency.

## Strategic Deep-Dive

At the Supercomputing 25 (SC25) conference, the spotlight has shifted from raw FLOPS to the "fabric"—the interconnect technology that determines whether a cluster of 50,000 GPUs acts as a unified supercomputer or a fragmented collection of nodes. Lisa Spelman, CEO of Cornelis Networks and a veteran of the data center industry, provided a compelling roadmap for the future of HPC networking. Her insights centered on a critical, often overlooked metric in the AI era: tail latency.

As AI training scales to the exascale level, the network is increasingly the primary bottleneck. Spelman pointed out that in massive AI training runs, the entire system must wait for the slowest packet of data to arrive before moving to the next compute step. This "tail latency" can render even the fastest MI400 or Blackwell chips idle for significant percentages of their duty cycle.

Cornelis Networks is addressing this through its next-generation Omni-Path evolution, which prioritizes deterministic performance over raw, unmanaged bandwidth. Unlike standard Ethernet, which is built for general-purpose traffic, the Cornelis fabric is being tuned specifically for the collective communication patterns—like All-Reduce and All-to-All—that define modern deep learning.

A major strategic theme at SC25 is the tension between proprietary ecosystems and open standards. While Nvidia’s InfiniBand offers a high-performance, tightly integrated solution, the industry is pushing back against vendor lock-in. Spelman’s leadership has positioned Cornelis Networks as a key proponent of the Ultra Ethernet Consortium (UEC).

By contributing intellectual property to open standards, Cornelis aims to provide a high-performance alternative that maintains interoperability across different vendors' CPUs and accelerators. This is crucial for national laboratories and massive enterprise data centers that cannot afford to be tethered to a single hardware provider for their multi-billion dollar AI investments.

Technically, Cornelis is moving toward "in-network collective operations." This involves offloading synchronization tasks from the CPU/GPU directly into the network switches. By performing data reduction and synchronization within the fabric itself, the system reduces the number of "hops" a packet must take, further slashing latency. Spelman emphasized that the future of HPC networking is not just about moving bits faster; it’s about making the network "disappear" by removing the overhead associated with data movement.

As we look toward SC26 and beyond, the evolution of these fabrics will be the deciding factor in which AI clouds can truly scale to the next order of magnitude in model complexity.


