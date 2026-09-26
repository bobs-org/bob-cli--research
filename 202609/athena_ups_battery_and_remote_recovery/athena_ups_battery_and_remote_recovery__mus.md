# UPS battery replacement + remote power-on for `athena` (Debian desktop)

**Research question:** A UPS that is probably powering this machine (but likely no
longer USB-connected to it) is beeping a dead-battery alert. The owner once
controlled it from this machine via the `pwrstat` command. (1) What UPS is it,
and how should the battery be replaced? (2) What is the best way to remotely
turn this machine back on after a power outage?

**Bottom line up front:**
- The UPS is almost certainly a **CyberPower** unit (`pwrstat` is CyberPower's
  PowerPanel CLI; a `powerpanel 1.3.3` package record is still on this machine).
  My best guess at the model family is the **PFC Sinewave LCD series
  (e.g. CP1000PFCLCD / CP1500PFCLCD class)** — see §2 for why, and how to
  confirm in 30 seconds by reading the sticker on the unit.
- Replace just the **battery cartridge**, not the whole UPS, unless the unit is
  very old or shows other faults (§3).
- For remote power-on after an outage, set **BIOS → APM Configuration →
  Restore On AC Power Loss = [Power On]** (with **ErP Ready = Disabled**). That
  single setting covers the outage case with no extra hardware. Add
  **Wake-on-LAN on the wired Intel NIC** as a secondary path for the
  "machine is soft-off but mains power is present" case (§4).

All local evidence below was gathered on 2026-09-26 from the machine itself
(hostname `athena`, Debian 13, ASUS PRIME TRX40-PRO); external claims cite
vendor docs / community sources in §6.

## 1. Local evidence

| Check | Result |
|---|---|
| `which pwrstat` | Not found (currently uninstalled) |
| `dpkg -s powerpanel` | `deinstall ok config-files`, version **1.3.3**, description: "PowerPanel for Linux … monitors the status of your **CyberPower Systems UPS**" |
| `lsusb` | No UPS device present (no CyberPower 0764:xxxx, no APC/Eaton). Consistent with "USB cord no longer connected" |
| `/etc/powerpanel/` | Absent (config purged or never re-created after removal) |
| NICs | `enp67s0` UP (Intel I211, MAC `a8:5e:45:d0:74:53`); `enp1s0` DOWN (Realtek 8111). Wired link available for WoL |
| Board | ASUS PRIME TRX40-PRO (workstation board — **no BMC/IPMI**, so no out-of-band management; BIOS + WoL are the levers) |
| `tailscale0` | Present — useful as a remote-access path *to the LAN*, but note Tailscale cannot itself carry a WoL magic packet (L2 broadcast, §4.3) |

The `powerpanel` dpkg record is the decisive clue: `pwrstat`/`pwrstatd` ship
only with CyberPower PowerPanel for Linux. No other mainstream vendor uses a
`pwrstat` CLI (APC uses `apcupsd`/`apctest`; NUT uses `upsc`/`upsmon`; Eaton
uses IPP). So the UPS make is **CyberPower, high confidence**.

## 2. Guess at the exact UPS: CyberPower PFC Sinewave LCD family

**Guess: a CyberPower PFC Sinewave model, most likely in the CP850–CP1500PFCLCD
range (e.g. CP1000PFCLCD or CP1500PFCLCD). Confidence: medium-low on the exact
model, high on make + family.** Reasoning:

- The PFC Sinewave (CP-PFCLCD) line is CyberPower's best-selling desktop/workstation
  UPS and the one most commonly paired with a high-end desktop like this
  (Threadripper TRX40 board,加大 PSU with Active PFC — simulated-sine UPS units
  can cause Active-PFC PSUs to shut down on transfer, so PFC-sine is what a
  careful buyer picks).
- PowerPanel for Linux + `pwrstat` is the documented companion software for
  exactly this line.
- The dead-battery beep pattern the owner describes matches CyberPower's
  documented "battery fault / replace battery" alert (rapid or repeating beeps;
  CyberPower's FAQ notes repeating beeps every ~15–45 s as a status/battery
  warning).

**Confirm in 30 seconds (do this before ordering anything):** the model and
serial number are on a small white barcode sticker on the **back or bottom
panel** of the UPS. Note the model (e.g. `CP1500PFCLCD`) and the S/N. The
model determines the exact replacement cartridge (§3). If the sticker is
unreadable, reconnect the USB cable and run `pwrstat -status` (after
reinstalling PowerPanel) or NUT's `upsc` — both report the UPS model string.

## 3. Battery replacement

### 3.1 Replace the battery, not the UPS (probably)

- CyberPower consumer UPS batteries are **user-replaceable sealed lead-acid
  (SLA) cartridges**, typically pairs of 12 V 7 Ah or 12 V 9 Ah cells
  (e.g. cartridge **RB1290 / RB1280X2A** for the CP850/CP1000PFCLCD class —
  verify against your exact model on CyberPower's product page).
- Typical service life is **3–5 years**; a "replace battery" alert at that age
  is normal wear, not a reason to scrap the unit. Replace the whole UPS only
  if: the unit is 6+ years old, shows other faults (won't pass self-test with
  a fresh battery, swollen case, burnt smell), or a genuine-battery cartridge
  costs close to a new unit.
- While the battery is dead, **the UPS is currently providing surge protection
  but effectively no ride-through**: on a mains dip the load drops immediately,
  so treat every outage as an unclean-shutdown risk until the battery is
  replaced.

### 3.2 Procedure (generic; follow the model's user manual)

1. Read the model/SN sticker; order the matching **CyberPower RB-series
   cartridge** (or an equivalent-spec third-party SLA pair — same voltage,
   same Ah, same terminal type; genuine cartridges are plug-and-play, bare
   cells are cheaper but require moving over the wiring/fuse harness).
2. Silence/acknowledge the alarm per the manual if needed (usually a
   Display/Mute button; `pwrstat -alarm off` only mutes the software side).
3. Power down the connected load, switch the UPS off, unplug it from the wall.
4. Lay it on its side, remove the front/battery-compartment panel, slide out
   the old cartridge, disconnect the leads (note polarity), connect the new
   one, slide in, reattach the panel.
5. Plug back into the **wall outlet directly** (never into a surge strip or
   another UPS), power on, charge **8+ hours** before trusting runtime, then
   run a self-test (Display button or `pwrstat -test` / PowerPanel).
6. **Recycle the old SLA battery** — electronics/hardware stores and battery
   retailers take them free; do not bin them.

### 3.3 Reconnect USB monitoring afterward

- Reconnect the USB cable (UPS data port → this machine) and either reinstall
  **PowerPanel for Linux** (`pwrstat -status`, `pwrstat -config`) or, my
  preference, use **NUT (Network UPS Tools)** from Debian (`nut-server`,
  `usbhid-ups` driver with `port = auto`): NUT is distro-maintained,
  transparent, and the better-supported path on modern Debian; the old
  proprietary `powerpanel 1.3.3` .deb is stale. Only run **one** of them.
- Configure a graceful-shutdown policy (e.g. shut down when on battery > N
  minutes or battery < ~35%), so the next outage ends in a clean shutdown
  instead of a hard crash when the new battery eventually exhausts.

## 4. Remote power-on after a power outage

There are two distinct cases: (A) mains failed and returned (machine lost
power), and (B) mains is present but the machine is shut down. They need
different mechanisms. The board has no IPMI/BMC, so the answer is BIOS
behavior + Wake-on-LAN, optionally plus a LAN-side helper.

### 4.1 Primary (covers case A): BIOS "Restore On AC Power Loss"

The PRIME TRX40-PRO manual documents **Advanced → APM Configuration → Restore
On AC Power Loss** with options **[Power On] / [Power Off] / [Last State]**.
Set it to **[Power On]**, and also set **ErP Ready = Disabled** (ErP modes cut
standby power and disable the wake circuitry WoL depends on).

Why this is the right primary: when mains return, the UPS restores output
power; the board sees "AC restored" and boots by itself. No network, no phone,
no extra hardware, and it works even during an extended outage that fully
drains the (replacement) battery — as long as the UPS is left switched on.
This single setting is the whole case-A solution.

Caveats:
- It must be set **before** the outage (requires one physical or
  firmware-setup visit; there is no OS-level way to change it remotely).
- It triggers on any AC restoration, including brief flickers — that is
  normally what you want for a server-ish desktop, but combined with a
  graceful-shutdown policy (§3.3) it means: outage → clean shutdown → mains
  return → auto-boot. Correct behavior.
- Keep the UPS's own power switch ON; some UPS units need their output
  enabled to pass restored mains to the load.

### 4.2 Secondary (covers case B): Wake-on-LAN on `enp67s0`

For "power is present but the machine is off/suspended", enable WoL on the
wired Intel I211 (`enp67s0`, MAC `a8:5e:45:d0:74:53`):

1. BIOS: enable **Power On By PCI-E / PCI-E wake** (same APM page; requires
   ErP Disabled per §4.1).
2. OS: `ethtool -s enp67s0 wol g` (magic-packet mode), made persistent — e.g.
   a `systemd.link` file with `WakeOnLan=magic`, or a oneshot systemd unit
   re-applying it at boot (the setting resets on reboot/link renegotiation
   otherwise). Use the **wired** interface; Wi-Fi WoL is unreliable and this
   machine's link is wired.
3. Test from another host on the same LAN with any WoL client aimed at the
   Intel NIC's MAC + broadcast address, while the machine is shut down (S5)
   but plugged in.

### 4.3 Remote-WoL topology (important limitation)

A magic packet is a **LAN broadcast** — it does not cross routers or
Tailscale/WireGuard tunnels by itself. So "remote" WoL needs a sender *inside*
the LAN. In decreasing order of preference:

1. **Router with built-in WoL** (many ASUS routers have a "wake" button in
   their admin UI / app) — expose the router admin via VPN or use its app.
2. **Any always-on LAN device** (Pi, NAS, another host) you can SSH into over
   Tailscale, sending the packet locally. This machine already runs Tailscale,
   so any Tailscale-reachable LAN peer works as the relay.
3. Phone/laptop on the home LAN (or on a VPN that bridges L2 / permits
   directed broadcast).

If none of these exists yet, note that case A (the actual outage scenario the
owner asked about) is already solved by §4.1 alone — WoL is only needed for
case B, where the owner presumably also has some path to reach the LAN.

### 4.4 What NOT to do

- **No smart plug between wall and UPS.** The UPS must be plugged directly
  into the wall; switching its input remotely defeats the UPS and risks
  confusing its charger/relay logic. A smart plug between UPS and PC is
  technically possible as a last-resort power-cycle, but it is a hack —
  BIOS auto-on + WoL covers both cases without it.
- Don't rely on "Last State" if the machine might have been soft-off before
  the outage; [Power On] is the deterministic choice for a machine you want
  reachable.

## 5. Recommended solution (in order)

1. **Read the UPS sticker** (model + S/N) and order the matching RB-series
   replacement battery cartridge; install per §3.2, charge, self-test.
2. **Reconnect the UPS USB cable** to `athena`; install and configure **NUT**
   (`usbhid-ups`) with a graceful-shutdown policy; remove/stop any
   conflicting PowerPanel install.
3. **One BIOS visit**: APM → **Restore On AC Power Loss = [Power On]**,
   **ErP Ready = Disabled**, enable **PCI-E/PCI wake**; save.
4. **Enable persistent WoL** (`wol g`) on `enp67s0`; record the MAC
   (`a8:5e:45:d0:74:53`); test a wake from another LAN host.
5. **Designate a LAN-side WoL sender** (router WoL feature or an always-on
   peer reachable over Tailscale) for case B; document the exact command.
6. Until the battery arrives: assume **zero ride-through** — avoid leaving
   unsaved work / unclean-shutdown-sensitive services running unattended.

## 6. Sources

- Local: `dpkg -s powerpanel` (1.3.3, "…your CyberPower Systems UPS", status
  `deinstall ok config-files`), `lsusb` (no UPS attached), `ip link`
  (enp67s0 Intel I211 UP), `hostnamectl` (PRIME TRX40-PRO, Debian 13).
- CyberPower PowerPanel-for-Linux / `pwrstat` usage (`pwrstat -status`,
  `-config`, `-pwrfail`, `-lowbatt`) — PowerPanel docs, ArchWiki "CyberPower
  UPS", and multiple Linux setup guides.
- CyberPower beep/FAQ ("unit beeping twice every 15–45 seconds") and
  "serial number on white barcode label on bottom/back panel" — CyberPower
  support FAQs.
- Battery replacement (RB-series cartridges, e.g. RB1290/RB1280A class for
  CP-PFCLCD models; same-size SLA swap procedure) — CyberPower PFC Sinewave
  user manuals.
- ASUS PRIME TRX40-PRO manual, APM Configuration p.79: "Restore On AC Power
  Loss … [Power On] [Power Off] [Last State]"; ErP Ready disables PME wake
  options.
- NUT as the maintained alternative to PowerPanel for CyberPower USB HID
  (`usbhid-ups`, `port = auto`) — ArchWiki, NUT user manual, Debian manpages.
- Persistent WoL on Debian (`ethtool … wol g` + systemd.link
  `WakeOnLan=magic` or oneshot unit; resets without persistence) — ArchWiki
  "Wake-on-LAN" and Debian/Ubuntu guides.
