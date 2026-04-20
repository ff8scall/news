---
title: "Investigating Split Locks on x86-64 Architecture"
date: "2026-04-20T10:19:14Z"
description: "This investigation explores the performance penalties associated with split locks in the x86-64 instruction set and evaluates the effectiveness of current mitigation strategies. Split locks occur when an atomic operation spans across two cache lines, forcing the processor to use expensive bus locking mechanisms. Understanding the trade-offs between performance degradation and the 'medicine' provided by hardware and software fixes is crucial for optimizing modern multi-core systems."
image: "/images/defaults/market/split_lock.jpg"
clusters: ["insights"]
categories: ["analysis"]
tags: ["Split Lock", "x86-64", "Cache Line", "Atomic Operations", "Bus Lock", "EFLAGS AC Bit", "Latency"]
featured: false
---
## Executive Summary
- This investigation explores the performance penalties associated with split locks in the x86-64 instruction set and evaluates the effectiveness of current mitigation strategies. Split locks occur when an atomic operation spans across two cache lines, forcing the processor to use expensive bus locking mechanisms. Understanding the trade-offs between performance degradation and the "medicine" provided by hardware and software fixes is crucial for optimizing modern multi-core systems.

## Strategic Deep-Dive

Split locks have long been a thorn in the side of x86-64 performance optimization. A split lock occurs when a processor executes an atomic instruction that accesses memory spanning across a 64-byte cache line boundary. Because the operation cannot be handled within a single cache hit, the processor must ensure atomicity by locking the entire memory bus or using complex cache coherency protocols that stall other cores.

In 2026, as core counts continue to rise and memory bandwidth becomes a bottleneck, the impact of split locks is more pronounced than ever. The "medicine"—features like Intel's Split Lock Detection or specialized kernel handlers—attempts to mitigate this by either throttling the offending process or forcing an alignment check exception. While these mitigations prevent a single malicious or poorly written application from bringing down system-wide performance, they introduce their own overhead.

Specifically, in the x86-64 context, the assertion of the LOCK# signal on the bus freezes all other memory traffic. When the AC (Alignment Check) bit in the EFLAGS register is set, modern kernels attempt to trap these events to prevent intentional "bus-locking" attacks. Our investigation shows that the performance penalty of a split lock can be orders of magnitude higher than a standard aligned atomic operation.


