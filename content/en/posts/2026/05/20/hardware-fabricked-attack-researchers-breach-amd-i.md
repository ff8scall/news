---
title: "Fabricked Attack: Researchers Breach AMD Infinity Fabric to Bypass SEV-SNP Cloud Security"
date: "2026-05-20T01:53:50Z"
description: "Researchers at ETH Zurich have disclosed a critical software-only vulnerability dubbed 'Fabricked,' which targets the routing mechanisms within AMD's Infinity Fabric—the high-speed interconnect responsible for data movement between chiplets and memory controllers. This sophisticated attack vector allows a malicious cloud host to manipulate internal data paths of AMD EPYC systems during the critical boot process, effectively undermining the Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) protections. SEV-SNP is designed to create a cryptographic isolation boundary between a Virtu..."
image: "/images/posts/2026/05/20/hardware-fabricked-attack-researchers-breach-amd-i.jpg"
alt_text: "Fabricked Attack: Researchers Breach AMD Infinity Fabric to Bypass SEV-SNP Cloud Security - AI 테크 인텔리전스 리포트 시각 자료"
eng_summary: ["Researchers at ETH Zurich have disclosed a critical software-only vulnerability dubbed 'Fabricked,' which targets the routing mechanisms within AMD's Infinity Fabric—the high-speed interconnect responsible for data movement between chiplets and memory controllers. This sophisticated attack vector allows a malicious cloud host to manipulate internal data paths of AMD EPYC systems during the critical boot process, effectively undermining the Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) protections. SEV-SNP is designed to create a cryptographic isolation boundary between a Virtu..."]
clusters: ["hardware"]
tags: []
featured: false
---
## Strategic Deep-Dive

Researchers at ETH Zurich have disclosed a critical software-only vulnerability dubbed 'Fabricked,' which targets the routing mechanisms within AMD's Infinity Fabric—the high-speed interconnect responsible for data movement between chiplets and memory controllers. This sophisticated attack vector allows a malicious cloud host to manipulate internal data paths of AMD EPYC systems during the critical boot process, effectively undermining the Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) protections. SEV-SNP is designed to create a cryptographic isolation boundary between a Virtual Machine (VM) and the host hypervisor, ensuring that even if the host is compromised, the tenant's data remains encrypted and inaccessible.

The Fabricked exploit functions by intercepting the configuration phase of the Infinity Fabric. By redirecting information flow at the hardware interconnect level, the attack enables the silent reading of confidential VM memory. The technical core of the vulnerability lies in the way the AMD Secure Processor (ASP) validates the hardware environment during the attestation process.

The researchers discovered that by inducing specific routing misconfigurations, they could trick the system into mapping unauthorized memory regions to trusted Source IDs. Consequently, the memory encryption keys and the Reverse Map Table (RMP), which SEV-SNP relies on to track memory ownership, can be bypassed or misled.

Furthermore, the vulnerability permits the forgery of attestation reports. In a standard confidential computing workflow, a tenant requests an attestation report to verify that their VM is running on a genuine, secure AMD processor with specific security features enabled. Fabricked allows a compromised host to generate a valid-looking signature for an insecure environment, providing a false sense of security while actively exfiltrating sensitive data.

The discovery of Fabricked represents a significant setback for the confidential computing movement, as it targets the very communication fabric that binds processing cores and memory together. Unlike traditional software exploits that target application logic, this bypass leverages the fundamental architectural design of the hardware interconnect.

For cloud service providers (CSPs) like AWS, Azure, and Google Cloud, who rely on SEV-SNP to offer 'Confidential VM' instances, this research necessitates an immediate re-evaluation of boot-time security protocols. AMD has been alerted to the findings and is expected to release firmware-level mitigations. However, because the flaw is rooted in the logic of the interconnect routing, implementing a fix without incurring a performance penalty on multi-die EPYC systems will be a significant engineering challenge.

This research underscores the ongoing arms race in semiconductor security, proving that even robust hardware-level attestation mechanisms can be subverted by innovative attack methodologies focusing on interconnect logic and boot-sequence vulnerabilities. As data centers move toward increasingly disaggregated architectures, the security of the fabric becomes just as critical as the security of the CPU core itself.


