# Hardware Requirements: Biblical Language Translation Engine

## 1. NLP Model Training & Fine-Tuning (Phase 4)
- **Training Cluster**:
  - **Minimum**: 8x NVIDIA A100 (80GB) nodes for distributed training.
  - **Recommended**: 8x NVIDIA H100 (80GB) instances for accelerated fine-tuning of large context-window models.
  - **Council OS constraint**: GPU is granted only to the `linguistic_nlp` domain for `translation_model_training`. The other seven kernel domains remain CPU service boundaries.
  - **Dell OptiPlex 5040 MT housing**: this Skylake/Q170 mini-tower skeleton has no discrete GPU. Seat Council OS as an original custom-built virtualized profile on that chassis; do not clone OEM Windows, flash BIOS/UEFI, wipe the host, or expect A100-class training on the 5040 itself. An OEM Windows 10 BIOS-setup trap is observed, not repaired by firmware writes.
  - **Galaxy S26 absorbable handset**: Council OS seats as a portable virtual profile (`galaxy_s26`). Compatibility is full-virtual. Do not flash the handset, unlock the bootloader, root the device, replace One UI, or install the kernel onto the phone. Transcendent completeness means charter fidelity. Complete authority remains biblical; the kernel does not claim it.
- **Interconnect**: NVIDIA NVLink for high-speed node communication.
- **Framework**: PyTorch/DeepSpeed optimized for multi-GPU scaling.
