# Research Report: UPS Identification, Battery Replacement, and Remote Power-On Strategy for Athena

- **Author:** researcher gem (`research.2o.gem`)
- **Date:** 2026-09-26
- **Target Host:** `athena` (Debian GNU/Linux 6.12, ASUS PRIME TRX40-PRO, AMD Ryzen Threadripper 3970X, NVIDIA RTX 3080 Ti)
- **Repo Target:** `sase/repos/research/202609/ups_battery_replacement_and_remote_power_on__gem.md`

---

## 1. Executive Summary & Headline Findings

This investigation resolves three key operational questions regarding the unmonitored uninterruptible power supply (UPS) powering the workstation `athena`:
1. **UPS Model Identification:** Which UPS is powering `athena`?
2. **Battery Replacement:** What battery cartridge or cells are required, and how should they be replaced?
3. **Remote Power-On:** How can the machine be reliably and remotely powered on following power outages or remote shutdowns?

### Summary of Findings

| Category | Finding | Primary Evidence / Recommendation |
| :--- | :--- | :--- |
| **Identified UPS** | **CyberPower CP1500PFCLCD** (1500VA / 900W, Pure Sine Wave) | Direct hardware manifest in `~/Sync/var/notes/Journal/computer.txt`; residual Debian package `powerpanel 1.3.3`; shell alias `alias pwrstat='sudo pwrstat'`. |
| **Battery Needed** | **2x 12V 9Ah SLA AGM Batteries** with **F2 (0.250") Terminals** | OEM Cartridge: **CyberPower RB1290X2** (or **RB1290X2B**). Aftermarket alternative: Pair of standard 12V 9Ah F2 batteries (e.g., Mighty Max ML9-12 F2). |
| **Immediate Cost** | **~$35 – $85** depending on OEM vs. aftermarket route | OEM pack (~$75–$85) offers pre-wired drop-in simplicity; bare SLA pair (~$35–$45) requires reusing the original wiring harness and fuse. |
| **Remote Power-On** | **Hybrid: BIOS AC Restore + Smart Plug + Wake-on-LAN** | Set BIOS `Restore AC Power Loss = Power On` and configure Wake-on-LAN on Intel I211 NIC (`enp67s0`). Place a heavy-duty 15A smart plug (e.g. Kasa KP125M / Shelly Plus 1PM) on the UPS battery outlet for remote on-demand power cycling. |
| **Out-of-Band Option**| **PiKVM / NanoKVM (ATX Power Control)** | Dedicated remote hardware KVM for out-of-band power button control, hardware reset, BIOS access, and video capture. |

---

## 2. UPS Identification & System Clues

### 2.1 The Evidence Trail

A comprehensive search of system configurations, hardware registers, dotfile repositories, and note archives on `athena` revealed conclusive evidence identifying the exact UPS:

1. **Hardware Build Log (`~/Sync/var/notes/Journal/computer.txt`)**:
   Under the workstation build specification for `athena` (matching the current ASUS PRIME TRX40-PRO motherboard, Ryzen Threadripper 3970X CPU, and RTX 3080 Ti GPU), the UPS is explicitly recorded:
   ```text
   ##### ROUND 2 #####
   ===== UPS =====
   [X] CyberPower CP1500PFCLCD
       - https://www.amazon.com/gp/product/B00429N19W/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1
   ===== Motherboard =====
   [X] ASUS PRIME TRX40-PRO [$450]
   ===== CPU =====
   [X] AMD Ryzen Threadripper 3970X [$1900]
   ```

2. **Package Manager State (`dpkg -l`)**:
   Checking Debian package status revealed residual configuration files for CyberPower's proprietary Linux monitoring utility:
   ```text
   rc  powerpanel  1.3.3  amd64  PowerPanel for Linux is a software program that monitors the status of your CyberPower Systems UPS.
   ```
   The `rc` status confirms `powerpanel` was previously installed and its binary provided the `pwrstat` command before being uninstalled/partially removed.

3. **Shell Aliases (`~/.config/aliases.sh`)**:
   Line 461 of `~/.config/aliases.sh` (tracked in `chezmoi`) contains:
   ```bash
   alias pwrstat='sudo pwrstat'
   ```

4. **Shell History (`~/.zsh_history`)**:
   Repeated historical calls to `pwrstat` and `pwrstat -status` were logged:
   - July 2022: Initial monitoring queries.
   - July 29, 2023: Executed right after Ansible playbooks (`pwrstat -status` followed by `reboot` and another `pwrstat -status`).
   - August–September 2026: Repeated invocations as battery alert tasks emerged.

5. **Obsidian Vault Action Items (`~/bob/cash.md` & `~/bob/dev.md`)**:
   In `~/bob/cash.md`:
   - Line 73: `- [ ] #task Buy new battery for UPS! [created::2026-08-24] [priority::high]`
   - Line 76: `*2026-09-01 → 2026-09-06* — I need access to the UPS.`
   - Line 79: `- [ ] #task Buy a new battery for UPS! [created::2026-08-28] [priority::high]`
   In `~/bob/dev.md`:
   - Line 74: `- [-] #task Figure out why UPS doesn't protect athena! [created:: 2026-07-18] -> OBSOLETE: See [[cash#^buy-ups-battery]]!`

6. **USB Device Scan (`lsusb`)**:
   Currently, `lsusb` shows no USB HID Power Device or CyberPower vendor ID (`0764`), corroborating the prompt's recollection that the USB monitoring cable was physically detached.

### 2.2 Concluded Make & Model

- **Manufacturer:** CyberPower Systems
- **Model:** **CP1500PFCLCD** (PFC Sinewave Series)
- **Form Factor:** Mini-Tower
- **Capacity:** 1500 VA / 900 Watts
- **Topology:** Line-Interactive, Pure Sine Wave output (crucial for Active PFC power supplies like the one powering this Threadripper workstation).

---

## 3. Battery Replacement Guide

### 3.1 Failure Cause & Urgency

Sealed Lead Acid (SLA) Absorbent Glass Mat (AGM) batteries have a standard service life of **3 to 5 years**. With the unit purchased around 2020–2021, the internal cells are approximately 5 to 6 years old. 

At this stage, lead sulfation and electrolyte dry-out cause internal resistance to spike. The UPS detects that the battery cannot sustain nominal float voltage or pass its periodic internal self-test, triggering an audible alarm and a flashing battery indicator on the front LCD panel. In this condition, the UPS provides **zero runtime buffer** during a brownout or blackout; any power fluctuation will immediately drop power to `athena`.

### 3.2 Battery Specifications

The CP1500PFCLCD utilizes **two 12V 9Ah** (or 12V 8.5Ah) sealed lead-acid batteries wired in series to create a **24V DC** battery bank.

- **Cell Voltage / Capacity:** 12 Volts, 9 Amp-hours (each).
- **Quantity:** 2 internal cells.
- **Physical Dimensions (per cell):**
  - Length: 5.94 in (151 mm)
  - Width: 2.56 in (65 mm)
  - Height: 3.70 in (94 mm)
  - Total Height with Terminals: ~3.94 in (100 mm)
- **Terminal Size:** **F2** (0.250 in / 6.35 mm wide faston tabs).
  > [!WARNING]
  > Do not purchase F1 terminals (0.187 in / 4.75 mm). Standard UPS harnesses require F2 terminals for high-current discharge.

### 3.3 Replacement Options

#### Option A: Official CyberPower Replacement Cartridge (Recommended for Convenience)
- **Part Number:** **CyberPower RB1290X2** (or **RB1290X2B** for newer revision units).
- **Price:** ~$75 – $85.
- **Pros:**
  - 100% OEM guaranteed fit and pre-assembled with proper heavy-gauge interconnect wire, internal fuse, and protective tape.
  - Drop-in replacement: disconnect red/black main leads, slide old cartridge out, slide new cartridge in, reconnect.
  - Includes manufacturer warranty and certified recycling packaging.
- **Verification:** Check the serial number sticker on the back/bottom of the UPS at [CyberPower Battery Replacement Tool](https://www.cyberpowersystems.com/tools/battery-replacement/) to confirm whether `RB1290X2` or `RB1290X2B` is specified.

#### Option B: Third-Party Bare SLA Batteries (Recommended for Value)
- **Part Numbers / Brands:**
  - Mighty Max ML9-12 F2 (2-pack) (~$38 – $42)
  - ExpertPower EXP1290 F2 (2-pack) (~$40 – $45)
  - Power Sonic PS-1290 F2 (2-pack) (~$55 – $65)
- **Pros:** Half the price of the OEM cartridge for identical battery chemistry and capacity.
- **Cons / Requirements:**
  - You must carefully disassemble the dual-battery pack, retaining the short series bridge wire (with integrated inline fuse) and outer holding tape/bracket.
  - Requires manually attaching the bridge wire to the new terminals and taping the two cells together.

### 3.4 Step-by-Step Battery Replacement Procedure

1. **Graceful Shutdown:** Safely shut down `athena` and any other connected peripherals.
2. **Disconnect Power:** Turn off the UPS power switch and unplug the UPS main power cable from the wall outlet.
3. **Access Battery Compartment:**
   - Place the UPS on its side on a clean work surface.
   - On the CP1500PFCLCD, remove the retaining screw(s) on the bottom/front battery door and slide the front/bottom faceplate downward to release it.
4. **Extract Existing Pack:**
   - Gently slide the dual-battery assembly outward using the plastic pull tab.
   - Disconnect the main red cable (+) and black cable (-) connecting the battery assembly to the UPS chassis.
5. **Prepare New Pack:**
   - *If using OEM Cartridge:* Ready to install immediately.
   - *If using bare SLA batteries:* Lay the old and new packs side-by-side. Carefully disconnect the intermediate bridge wire/fuse linking the positive terminal of Battery 1 to the negative terminal of Battery 2 on the old pack. Connect this bridge wire between the new batteries in identical series orientation. Tape the two batteries together securely.
6. **Install & Reconnect:**
   - Connect the red lead to the positive (+) terminal of the pack.
   - Connect the black lead to the negative (-) terminal of the pack. (A brief, harmless small spark may occur due to capacitor inrush current).
   - Slide the battery assembly back into the chassis and reattach the faceplate.
7. **Recharge & Self-Test:**
   - Plug the UPS into the AC wall outlet.
   - Allow the new batteries to charge undisturbed for at least **8 to 12 hours** to reach 100% capacity before subjecting them to full load.
   - Power on the UPS and initiate an internal self-test (hold down the power button until the unit beeps twice, or run test via software) to clear the battery alert state.

---

## 4. Reconnecting the UPS & Software Monitoring

To restore automated load protection and safe unattended shutdown on `athena`, the USB connection between the UPS and the workstation must be restored.

### 4.1 Physical Connection
Connect a standard **USB 2.0 Type-A to Type-B cable** (standard printer-style USB cable) from the USB port on the back of the CyberPower CP1500PFCLCD to any available USB-A port on `athena`. Verify detection with `lsusb` (Vendor `0764` Cyber Power System).

### 4.2 Software Options: PowerPanel vs. Network UPS Tools (NUT)

#### Option 1: Reinstall CyberPower PowerPanel for Linux (`powerpanel` / `pwrstat`)
Since Bryan already has configuration familiarity and existing shell aliases for `pwrstat`:
1. Download the latest PowerPanel 64-bit `.deb` package from [CyberPower Systems](https://www.cyberpowersystems.com/products/software/power-panel-for-linux/).
2. Install via dpkg/apt:
   ```bash
   sudo apt install ./powerpanel_*.deb
   ```
3. Verify connection:
   ```bash
   sudo pwrstat -status
   ```
4. Configure shutdown parameters:
   ```bash
   sudo pwrstat -config
   ```
   Set low-battery threshold (e.g., remaining runtime <= 5 minutes or capacity <= 20%) to trigger a graceful Linux shutdown.

#### Option 2: Network UPS Tools (`NUT`) — The Modern Homelab Approach
If multiple machines on the network (e.g. `apollo`, Kelly's MacBook, NAS) or home automation (Home Assistant) need to know when power fails:
1. Install NUT:
   ```bash
   sudo apt update && sudo apt install nut
   ```
2. Configure `/etc/nut/ups.conf`:
   ```ini
   [cyberpower]
   driver = usbhid-ups
   port = auto
   desc = "CyberPower CP1500PFCLCD"
   ```
3. Set `MODE=standalone` or `MODE=netserver` in `/etc/nut/nut.conf`.
4. NUT provides native support for Prometheus metrics, Home Assistant discovery, and network-wide shutdown broadcasts via `upsmon`.

---

## 5. Remote Power-On Solutions After Outages

The workstation `athena` is an AMD Ryzen Threadripper 3970X system built on an **ASUS PRIME TRX40-PRO** motherboard. When power fails and battery depletes, or when the machine is shut down cleanly ahead of battery exhaustion, the system enters the ACPI **S5 (Soft Off)** state.

To remotely turn `athena` back on, several architectures are evaluated below.

### 5.1 Architecture & Constraint Analysis

1. **System Power Draw:** The Threadripper 3970X (280W TDP) combined with the RTX 3080 Ti (350W TDP) and high-end workstation components can draw 600W to 800W+ under full multi-core / GPU load. Any in-line relay or smart plug must be rated for at least **15A / 1800W**.
2. **Motherboard Hardware Capabilities:**
   - Motherboard: ASUS PRIME TRX40-PRO (AMD TRX40 chipset, Socket sTRX4).
   - Onboard NIC: **Intel I211-AT Gigabit Controller** (`enp67s0`, MAC: `a8:5e:45:d0:74:53`).
   - ACPI Wake Support: In Linux, `/sys/class/net/enp67s0/device/power/wakeup` is already `enabled`.
   - BIOS APM Features: Supports "Restore AC Power Loss" (`[Power On]`, `[Power Off]`, `[Last State]`) and "Power On By PCI-E" (Wake-on-LAN).
3. **The "Clean Shutdown" Dilemma:**
   If a UPS daemon (like `pwrstatd` or `nut`) cleanly halts Linux before the battery dies, the motherboard rests in S5 with AC standby power still present. If utility power returns:
   - If the UPS never dropped output power, the PSU never lost AC line voltage. Therefore, standard BIOS "Restore AC Power Loss" will **not** trigger an automatic boot.
   - For BIOS AC restore to work, the motherboard must undergo a true **G3 (mechanical power loss)** transition where 5VSB (standby voltage) drops to 0V.

---

### 5.2 Comparative Evaluation of Remote Turn-On Methods

```
+---------------------------------------------------------------------------------------------------+
| Method 1: BIOS Restore AC Power Loss                                                              |
|   Mains Restore -> UPS Output Restores -> PSU senses G3 transition -> Auto Boot                   |
+---------------------------------------------------------------------------------------------------+
| Method 2: Smart Plug Power-Cycle (Combined with BIOS AC Restore)                                  |
|   Phone App / Cloud -> Smart Plug OFF (15s) -> Smart Plug ON -> PSU senses G3 -> Auto Boot        |
+---------------------------------------------------------------------------------------------------+
| Method 3: Wake-on-LAN (WoL)                                                                       |
|   Router / LAN Device / Tailscale -> Magic Packet (MAC a8:5e:45:d0:74:53) -> Intel I211 -> Boot   |
+---------------------------------------------------------------------------------------------------+
| Method 4: Mechanical / Relay Switch (SwitchBot Bot or Motherboard PWR_SW Header)                  |
|   Cloud / BLE / Zigbee -> Momentary contact closure across Power Switch -> Motherboard Boots       |
+---------------------------------------------------------------------------------------------------+
| Method 5: Hardware KVM-over-IP (PiKVM / NanoKVM / Bipi)                                           |
|   Web UI / Tailscale -> ATX Power Relay -> Video/Keyboard/Mouse + Power/Reset Control            |
+---------------------------------------------------------------------------------------------------+
```

#### Detailed Comparison Matrix

| Feature / Metric | Method 1: BIOS AC Restore | Method 2: Smart Plug + BIOS | Method 3: Wake-on-LAN (WoL) | Method 4: SwitchBot / Relay | Method 5: PiKVM / NanoKVM |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Additional Hardware Cost** | $0 | $15 – $25 | $0 | $30 – $40 | $40 – $150 |
| **Setup Complexity** | Very Low (BIOS toggle) | Low (Plug in & pair) | Low (BIOS + OS setting) | Low (Mechanical / Header) | Medium (Hardware cabling) |
| **Requires Outage to Trigger?** | Yes (Needs full power cycle) | No (Can cycle on demand) | No (Wakes on demand) | No (Wakes on demand) | No (Full out-of-band) |
| **Works If Cleanly Shut Down?** | Only if UPS cuts outlets | **Yes** (Remote power toggle)| **Yes** (If standby power ok)| **Yes** (Direct power pulse) | **Yes** (Direct ATX header) |
| **WAN / Remote Access** | N/A (Autonomous) | Cloud App / HomeKit / HA | Requires Router / Subnet | Cloud App / BLE Hub | Web UI via Tailscale / VPN |
| **Handles OS Freeze / Crash?** | No | **Yes** (Hard AC power cycle)| No | **Yes** (Hold button for 5s)| **Yes** (Direct reset/power) |
| **Remote BIOS / Video View?** | No | No | No | No | **Yes** (Full HDMI capture) |

---

### 5.3 Method Deep-Dive & Configuration Details

#### Method 1 & 2: BIOS "Restore AC Power Loss" + Heavy-Duty Smart Plug (The Practical Champion)

This combination offers the highest reliability for remote recovery with minimal cost.

**A. BIOS Configuration on ASUS PRIME TRX40-PRO:**
1. Reboot `athena` and press `<Delete>` or `<F2>` to enter UEFI BIOS.
2. Press `<F7>` to enter **Advanced Mode**.
3. Navigate to **Advanced** > **APM Configuration**.
4. Set **Restore AC Power Loss** to **`[Power On]`**.
   *(Note: Avoid `[Last State]` because if the machine cleanly shut down into S5 before power was cut, `Last State` evaluates to "Off" and will keep the machine off).*
5. Press `<F10>` to save and exit.

**B. Smart Plug Integration:**
- Plug a 15A/1800W smart plug (e.g., **Kasa KP125M**, **TP-Link Tapo P125M**, or **Shelly Plus 1PM Gen3**) into one of the **Battery + Surge** protected outlets on the CyberPower CP1500PFCLCD.
- Plug `athena`'s main power supply cable into the smart plug.
- **How to Turn On Remotely:**
  1. If `athena` is off or unresponsive, open the smart plug app (Kasa/Tapo/Shelly) on your phone from anywhere.
  2. Turn the smart plug **OFF**.
  3. Wait **15 to 30 seconds** (allowing the PSU capacitors to discharge and drop 5VSB to zero).
  4. Turn the smart plug **ON**.
  5. The ASUS motherboard detects AC mains restoration from G3 and immediately powers up the system!

> [!IMPORTANT]
> **Power Rating Warning:** Ensure the smart plug is rated for **15A / 1800W**. The AMD Threadripper 3970X and RTX 3080 Ti can draw over 600W under heavy computational load; do not use cheap 10A-rated smart plugs.

---

#### Method 3: Wake-on-LAN (WoL) via Intel I211 Controller

Wake-on-LAN sends an Ethernet magic packet containing `athena`'s MAC address (`a8:5e:45:d0:74:53`) to wake the system from S5.

**A. BIOS Configuration:**
1. In ASUS UEFI BIOS > **Advanced** > **APM Configuration**:
   - Set **Power On By PCI-E** to **`[Enabled]`** (On ASUS TRX40 motherboards, the onboard Intel I211 NIC is on the PCIe bus; this setting enables onboard LAN wake).
   - Set **ErP Ready** to **`[Disabled]`** (ErP shuts off PCIe standby power, which prevents the NIC from listening for magic packets in S5).
2. Save and exit (`<F10>`).

**B. Linux NetworkManager Configuration:**
`athena` uses NetworkManager for `enp67s0` ("Wired connection 1"). To persist WoL across reboots:
```bash
sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.wake-on-lan magic
sudo nmcli connection up "Wired connection 1"
```
Verify wakeup flag:
```bash
cat /sys/class/net/enp67s0/device/power/wakeup
# Output must be: enabled
```

**C. Triggering WoL Remotely:**
Because magic packets are Layer-2 broadcast packets (UDP port 7 or 9), they cannot be routed directly across the public Internet from an external network. You have three easy ways to trigger it:
1. **Via Home Router (TP-Link AX11000 / FIOS Router):**
   Bryan's build notes show a `TP-Link AX11000` router. The TP-Link Tether smartphone app or web management interface includes a built-in **Wake-on-LAN** button that broadcasts directly into the local subnet.
2. **Via Tailscale Peer on the Local Network:**
   If a lightweight always-on device (Raspberry Pi, Apple TV / HomePod, or an old laptop) is on the local network running Tailscale, SSH into it and send the packet:
   ```bash
   wakeonlan a8:5e:45:d0:74:53
   ```
3. **Tailscale Subnet Router:**
   A local Tailscale node configured with `--advertise-routes=192.168.1.0/24` allows sending directed UDP broadcast packets (`192.168.1.255:9`) directly from a remote machine (like Kelly's MacBook Pro).

---

#### Method 4: SwitchBot Bot or Smart Relay (Non-Invasive Physical Trigger)

If you prefer not to cycle AC mains power or rely on broadcast packets:
- **SwitchBot Bot:**
  - A small, battery-operated robotic device positioned over `athena`'s chassis power button.
  - Paired with a SwitchBot Hub (connected to home Wi-Fi).
  - From the SwitchBot mobile app anywhere in the world, tap "Press" -> the physical mechanical arm presses the power button for 1 second.
  - **Advantage:** Completely independent of motherboard state, OS state, or network drivers. Can also perform a 5-second long press to force a hard shutdown if the machine freezes.
- **Shelly Plus 1 Dry Contact Relay:**
  - A tiny Wi-Fi relay installed inside the PC case.
  - Wired in parallel with the chassis `POWER SW` pins on the motherboard front-panel header.
  - Configured with an auto-off timer of 0.5s ("inching"). When activated via web app or Home Assistant, it momentarily shorts the power switch pins, simulating an exact physical button press.

---

#### Method 5: PiKVM or NanoKVM (The Ultimate Homelab / Out-of-Band Management)

For a workstation of this caliber, a hardware KVM-over-IP provides enterprise-grade IPMI/BMC functionality:
- **Devices:**
  - **NanoKVM (RISC-V based):** ~$40 – $50. Inexpensive, compact, includes ATX power control board.
  - **PiKVM v3 / v4 (Raspberry Pi based):** ~$150 – $220. Feature-rich, highly active open-source community.
- **Capabilities:**
  - Directly attaches to the motherboard's front-panel headers (`PWR_SW`, `RESET_SW`, `PWR_LED`).
  - Captures HDMI video output and provides virtual USB keyboard and mouse over HTML5.
  - Accessible securely over Tailscale.
  - **Key Benefit:** If `athena` fails to boot after an outage due to an fsck error, kernel panic, or stuck BIOS prompt, you can see the screen and interact with the keyboard remotely, rather than being locked out until returning home.

---

## 6. Recommended Action Plan & Phased Roadmap

### Phase 1: Restore Battery & Power Protection (Immediate / Day 1)
1. **Verify Serial Number:** Inspect the label on the bottom/rear of the CyberPower CP1500PFCLCD. Check serial prefix against CyberPower's battery tool to confirm whether `RB1290X2` or `RB1290X2B` is required.
2. **Order Replacement Batteries:**
   - *Budget option:* Pair of 12V 9Ah F2 SLA batteries (e.g. Mighty Max ML9-12 F2) for ~$40.
   - *Convenience option:* CyberPower OEM RB1290X2 cartridge for ~$80.
3. **Install Batteries:** Follow the step-by-step procedure in Section 3.4.
4. **Initial Charge:** Allow 8–12 hours of charging on AC wall power before connecting critical workstation loads.

### Phase 2: Re-establish USB Telemetry (Day 2)
1. **Cable:** Connect a USB Type-A to Type-B cable from the UPS to `athena`.
2. **Software:** Reinstall CyberPower `powerpanel` (`sudo apt install ./powerpanel_*.deb`) or set up `nut`.
3. **Verify:** Confirm with `sudo pwrstat -status` that line status, battery capacity (100%), load wattage, and runtime are actively reporting.

### Phase 3: Implement Remote Power-On (Day 2)
1. **Enable BIOS AC Recovery:**
   - Enter UEFI BIOS (`<Del>` on boot) > **Advanced** > **APM Configuration** > Set **Restore AC Power Loss = `[Power On]`**.
   - Set **Power On By PCI-E = `[Enabled]`** and **ErP Ready = `[Disabled]`**.
2. **Enable WoL in Linux:**
   - Run: `sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.wake-on-lan magic`
3. **Install Smart Plug:**
   - Obtain a 15A smart plug (e.g., Kasa KP125M / Tapo P125M).
   - Place between the UPS battery outlet and `athena`'s power supply.
   - Test remote reboot: Shut down `athena`, toggle smart plug off for 20 seconds via the smartphone app, toggle on, and verify `athena` automatically powers up.
4. *(Optional Long-Term):* If frequent out-of-town travel requires full BIOS and recovery console access, deploy a **NanoKVM** or **PiKVM**.

---
*Report completed and verified by researcher gem.*
