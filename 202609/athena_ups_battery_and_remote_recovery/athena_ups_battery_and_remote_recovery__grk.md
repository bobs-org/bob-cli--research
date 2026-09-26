# Athena UPS identity, battery replacement, and remote power-on

- **Researcher:** grk
- **Host:** `athena` (Debian 13, kernel 6.12.107+deb13-amd64)
- **Date:** 2026-09-26
- **Question:** What UPS is powering this machine, how should the failed battery be handled, and how can the machine be powered on remotely after an outage?

## Headline

This machine is almost certainly on a **CyberPower Personal-series USB HID UPS**, most likely a **CP1500PFCLCD** (or the later `CP1500PFCLCDa`). The `pwrstat` command the user remembers is CyberPower PowerPanel for Linux; leftover dpkg state still names that package. USB monitoring is currently disconnected. The failed-battery alarm at ~6 years of service is the expected end of life for the sealed lead-acid pack, so a cartridge swap is the first hardware move if the LCD still reads as a 1350–1500 VA PFC Sinewave unit.

Remote power-on after a wall-power outage is a motherboard problem, not a UPS-USB problem. This ASUS PRIME TRX40-PRO has no BMC/IPMI. The setting that actually brings the box back after a blackout is **Advanced → APM Configuration → Restore On AC Power Loss = Power On**, with **ErP Ready = Disabled** and **Power On By PCI-E = Enabled**. Wake-on-LAN on the live Intel I211 NIC is a useful second path for a clean shutdown while AC is still present; it does not by itself recover a machine that lost 5V standby.

## What this machine actually is

| Item | Value | Source |
| --- | --- | --- |
| Hostname | `athena` | `hostname` |
| CPU | AMD Ryzen Threadripper 3970X (32C/64T, 280 W TDP) | `/sys` + `lscpu` |
| Motherboard | ASUSTeK PRIME TRX40-PRO, BIOS 1101 (2020-06-05) | `/sys/class/dmi/id` |
| GPU | NVIDIA GeForce RTX 3080 Ti | `lspci` |
| RAM | 62 GiB visible | `free` |
| Storage | 2× Samsung 970 PRO 1 TB NVMe, 3× WDC 4 TB HDD, 250 GB SATA SSD | `lsblk` |
| Live NIC | `enp67s0`, Intel I211 `[8086:1539]`, MAC `a8:5e:45:d0:74:53`, 192.168.1.156, sysfs wakeup **enabled** | sysfs, `ip` |
| Idle NIC | `enp1s0`, Realtek RTL8111, no carrier, wakeup disabled | sysfs |
| BMC / IPMI | None (`/dev/ipmi0` missing; `ipmitool mc info` cannot open a device) | local probe |
| Tailscale | `athena` 100.87.31.114; peers `apollo` (remote Linux VPS), `kellys-macbook-pro`, `pixel-10-pro-xl` (offline) | `tailscale status` |

Peak wall draw for a 3970X + 3080 Ti workstation is commonly in the 700–1000 W region under simultaneous CPU+GPU load, with idle often a couple of hundred watts. A 1500 VA / 900 W CyberPower PFC unit is a typical 2020 enthusiast purchase for graceful shutdown. It is tight if the machine is compiling and gaming at the moment the lights go out.

## Evidence that the UPS is CyberPower, and that USB is unplugged

### PowerPanel / `pwrstat`

- Interactive shell has `alias pwrstat='sudo pwrstat'` in chezmoi (`home/dot_config/aliases.sh`).
- dpkg still records **`powerpanel` 1.3.3** in `rc` state (removed, config-files leftover). Maintainer line: `Cyber Power Systems, Inc. <tech@cpsww.com>`. Description names `pwrstatd` plus `pwrstat`.
- zsh history records the original install as:

  ```text
  sudo apt install ./PPL-1.3.3-64bit.deb
  apt show powerpanel
  pwrstat -status
  ```

  Adjacent history also searched `pwrstat` / `power.*panel` around **2020-09-04–2020-09-05**, which is the likely first-install window. Motherboard BIOS date is 2020-06-05, so the UPS was part of the original Threadripper build, not a later leftover.
- Later history: `pwrstat -status` on 2023-07-29; `del powerpanel ...` on 2023-09-03 (package removal). The binary is gone: `/usr/sbin/pwrstat` does not exist. No `/etc/pwrstatd.conf` remains.
- `PPL-1.3.3-64bit.deb` is CyberPower **PowerPanel Personal for Linux**, which talks to CyberPower USB-HID (and some serial) Personal/home units. It is not APC `apcupsd`, not Eaton IPP, and not PowerPanel Business (RMCARD / SNMP).

### USB today

`lsusb` shows only hubs, ASUS USB audio, AURA LED, ASUS USB-BT500, Das Keyboard, and ASMedia storage. **No `0764:` CyberPower HID device.** Current hidraw nodes belong to the keyboard and ASUS devices. That matches the user's memory: the UPS is still in the power path, the USB management cable is not.

CyberPower's own Linux manual says to connect the UPS USB cable **directly to the PC, not through a hub**. Athena has several powered hubs (Genesys, ASMedia, VIA). When the cable goes back in, it should land on a rear I/O motherboard port.

### What is not present

- No Network UPS Tools install (`nut-server` / `nut-client` candidate is Debian 2.8.1-5, currently not installed).
- No `/etc/nut`.
- No APC, Eaton, or Tripp Lite USB IDs.
- Gmail search of this account found **no CyberPower / UPS-battery retail receipt** (Amazon/Newegg hits were parcel-tracking or unrelated). Identification has to come from software leftovers plus the physical LCD, not an invoice.

## UPS model guess

**Primary guess: CyberPower CP1500PFCLCD** (1500 VA / 900–1000 W, PFC Sinewave, front LCD, USB HID, vendor ID `0764`, product ID usually `0501`).

**Close variants, in descending order:**

1. **CP1500PFCLCDa** — later hardware revision of the same product, same role, NUT still uses `usbhid-ups`.
2. **CP1350PFCLCD** — same chassis family, slightly less wattage (replacement pack is RB1270X2C rather than RB1290X2).
3. **GX1500U** — also 900 W sinewave USB HID; less common in 2020 build photos.
4. **CP1500AVRLCD** — same era, simulated sine. Possible, but a 2020 Threadripper + RTX 30-series PSU is an active-PFC load, and the PFC Sinewave SKU was the default recommendation in that community.

### Why CP1500PFCLCD specifically

- PowerPanel Personal + `pwrstat` ⇒ CyberPower **Personal** USB unit, not a Smart App LCD with an RMCARD (those are managed with PowerPanel Business / SNMP).
- The user is getting a **battery-failed alert they can see/hear** ⇒ LCD/beeper tower, not a silent no-display brick.
- First use around September 2020, next to a PRIME TRX40-PRO / 3970X / 3080 Ti build ⇒ the 1500 VA PFC Sinewave tower was the default "serious PC" CyberPower SKU on Amazon in that window.
- Sealed-lead-acid packs in these units are specified at **3–6 years**; a replace-battery alarm in 2026 is on schedule for a 2020 purchase.
- NUT's hardware compatibility list documents CP1500PFCLCD on `usbhid-ups` with `ups.vendorid: 0764` and `ups.realpower.nominal: 900`.

Confirm in 30 seconds once you can see the chassis: the LCD or the rear silkscreen prints the SKU. After the USB cable is in, `upsc` or `pwrstat -status` prints `Model Name`.

## Battery: replace the pack, keep the UPS (unless the LCD says otherwise)

For CP1500PFCLCD-class hardware:

| Item | Detail |
| --- | --- |
| Chemistry | Two 12 V ~9 Ah VRLA/SLA in series (24 V pack) |
| OEM cartridge | CyberPower **RB1290X2** / **RB1290X2C** (some serial prefixes use **RB1280X2B**) |
| CP1350PFCLCD pack | **RB1270X2C** |
| Job | Front-panel screws, slide cover, swap both cells, 8–16 h recharge, then run the LCD battery test and reset the battery-replacement date |
| Cost band | OEM cartridge roughly the price of a cheap new no-name UPS; generic 12 V 9 Ah pairs are cheaper if you reuse the harness |
| When to replace the whole UPS | Overload at this workstation's full load, swollen/leaking cells, UPS that will not pass AC with a dead pack, or a desire for 1500 W+ / lithium / switched outlets |

A dead pack usually still **passes utility power through**. Backup time is what is gone. That is why the machine is up now and why a blackout currently means a hard crash.

Do not buy an AVR simulated-sine replacement for this PSU. Stay on PFC sinewave (CyberPower "PFC Sinewave", APC "Sinewave", Eaton 5P/9PX, etc.).

If the physical label is a 1500 VA / 900 W unit and this box is often at high CPU+GPU load, treat the current UPS as **shutdown insurance**, not "keep compiling through the outage." A later upgrade target is a ~2000–2200 VA / ~1800–2000 W PFC or online unit (CyberPower OR2200PFCLCD / CP2200PFCLCD class, or equivalent). That is optional; it is not required to stop the beeping or to get remote power-on.

## Software: reconnect USB, then run NUT, not both NUT and PowerPanel

Two Linux stacks talk to this hardware. Only one should own the USB device.

| | Network UPS Tools (recommended) | PowerPanel Personal (`pwrstat`) |
| --- | --- | --- |
| Package | Debian `nut-server` + `nut-client` **2.8.1-5** in Trixie | CyberPower `.deb`, current **v1.4.2** (Debian 13 is listed); old leftover was 1.3.3 |
| Driver | `usbhid-ups`, `port = auto` | `pwrstatd` |
| Model print | `upsc athenaups` → `device.model` | `pwrstat -status` |
| Shutdown | `upsmon` + `SHUTDOWNCMD` | `pwrstat -lowbatt -shutdown on` |
| Distro fit | Native systemd units, no vendor cloud | Proprietary daemon; current AUR notes include OpenSSL 1.1 / SNI friction |
| Extra | Can later publish the UPS to other LAN hosts | Matches the user's muscle memory |

**Recommendation:** `apt install nut-server nut-client`, `MODE=standalone` in `/etc/nut/nut.conf`, and:

```ini
# /etc/nut/ups.conf
[athenaups]
    driver = usbhid-ups
    port = auto
    desc = "Athena CyberPower USB UPS"
    # CyberPower quirk: offdelay is interpreted in minutes on many units.
    # 60 seconds is the usual safe minimum if you enable kill-power.
    offdelay = 60
    pollinterval = 2
```

Then `nut-scanner -U` after the cable is in, `systemctl enable --now nut-server nut-monitor`, and `upsc athenaups`. Set `SHUTDOWNCMD "/sbin/shutdown -h now"` and a low-battery / on-battery delay that matches measured runtime (likely only a few minutes at this workstation's idle draw until the new pack is proven).

PowerPanel 1.4.2 is a reasonable **identification/debug** tool (`pwrstat -status` prints the SKU even if you do not keep the daemon). Do not run `pwrstatd` and `usbhid-ups` at the same time.

NUT notes specific to CyberPower: some CPS firmware treats `offdelay` as minutes; values under 60 can cut output immediately. Test a fake shutdown (`upsmon -c fsd`) on AC **once**, during a sitting where a reboot is acceptable, before trusting it on a real outage.

## Remote power-on

### What this board can and cannot do

The PRIME TRX40-PRO APM menu (manual §3.6.9) exposes:

- **Restore On AC Power Loss:** Power On / Power Off / Last State
- **Power On By PCI-E:** Wake-on-LAN for the onboard Intel I211 and other PCI-E NICs
- **Power On By RTC**
- **ErP Ready:** when enabled, other PME/wake options are forced off

There is no AST BMC, no `/dev/ipmi0`, no vPro/AMT (this is AMD). Prometheus's `prometheus-node-exporter-ipmitool-sensor.timer` is a generic unit and is inactive.

### Path A — after a real blackout (the case the user asked about)

When wall power dies long enough that the PSU loses 5VSB:

1. Wake-on-LAN cannot fire; the NIC is unpowered.
2. When utility returns, a healthy or even battery-failed CyberPower Personal UPS typically **re-energizes the outlets**.
3. If BIOS **Restore On AC Power Loss = Power On**, the workstation boots by itself.
4. If that setting is still the ASUS default **Power Off**, the box stays dark until someone pushes the case button — which is the current remote-access hole.

**This is the one BIOS change that solves "power came back and I am elsewhere."** Use **Power On**, not Last State, so a crash-during-outage still comes back.

Also set **ErP Ready = Disabled** and **Power On By PCI-E = Enabled**. Fast Boot can skip NIC init; leave it conservative until WoL is proven.

### Path B — after a clean `shutdown -h` while wall power is present

Intel I211 on `enp67s0` already has sysfs `power/wakeup = enabled`. Magic-packet WoL is the right tool here.

- MAC: `a8:5e:45:d0:74:53`
- LAN: `192.168.1.156/24`, gateway `192.168.1.1`
- Broadcast WoL: `wakeonlan a8:5e:45:d0:74:53` from another host on `192.168.1.0/24`

Debian package `wakeonlan` is available and not installed. After `ethtool` is installed, confirm `Wake-on: g`. Persist with a udev rule or `ip link set enp67s0 wol g` if the driver drops the flag.

**Who can send the packet today**

- `kellys-macbook-pro` on Tailscale, **if it is on the home LAN** (L2 magic packets do not cross Tailscale by themselves).
- Phone on home Wi-Fi, same constraint.
- `apollo` is a remote VPS (`159.223.165.54`). It cannot send a LAN magic packet unless you add a subnet-router/WoL helper on the LAN.

A cheap always-on helper (router WoL UI, a Raspberry Pi, or later a PiKVM) is the durable way to trigger Path B from the internet. Tailscale Serve/subnet on that helper is enough; do not port-forward UDP/9 from the WAN.

### Path C — true remote ATX (optional, later)

PiKVM, NanoKVM, or JetKVM on the front-panel ATX headers plus HDMI gives power-button, BIOS, and boot-failure recovery. That is the right extra hardware if this box must be recoverable after a hung POST, a BIOS reset, or ErP/WoL misconfiguration. It is more than is needed for "the power came back after an outage."

A smart plug **on the PC PSU** is a bad idea (inrush, and it fights the UPS). A smart plug on the **UPS wall inlet**, combined with Restore-On-AC = Power On, can hard-cycle a wedged PSU; treat that as a last resort.

### How the two problems compose

```text
outage, dead battery  →  hard power cut (no NUT shutdown)
utility returns       →  UPS pass-through restores PSU 5VSB/12V
Restore AC = Power On →  athena boots without a person in the room
USB + NUT restored    →  next outage gets a graceful halt first
new battery           →  enough minutes for that halt
WoL                   →  recover from a deliberate shutdown, not from G3
```

## Recommended implementation (ordered)

1. **Read the LCD / rear label.** Photograph model, serial, and rating (VA/W). That confirms or kills the CP1500PFCLCD guess before buying parts.
2. **BIOS (one physical visit):** Advanced → APM Configuration:
   - Restore On AC Power Loss = **Power On**
   - Power On By PCI-E = **Enabled**
   - ErP Ready = **Disabled**
3. **USB:** Plug the UPS HID cable into a **rear motherboard USB port**. Confirm `lsusb` shows `ID 0764:...`.
4. **Software:** Install NUT 2.8.1 (`nut-server`, `nut-client`). Configure `usbhid-ups` as above. `upsc` should print `device.model`. Keep PowerPanel uninstalled unless you want a one-shot `pwrstat -status`.
5. **Battery:** If the SKU is CP1500PFCLCD/a, order RB1290X2 / RB1290X2C (or a quality 12 V 9 Ah pair), replace both cells, charge 8–16 h, run the self-test, silence the alarm, reset the battery date on the LCD.
6. **Shutdown policy:** On-battery, shut down after a short, measured window (start around 60–120 s on-battery *or* at ~30–40 % charge / 5 min remaining — pick one after `upsc` shows real runtime). The goal is a clean halt, not riding through a long outage on 900 W.
7. **WoL:** `apt install wakeonlan`, document MAC `a8:5e:45:d0:74:53`, test from a LAN client after `shutdown -h now`. Optional: a LAN-side helper reachable over Tailscale.
8. **Prove the outage path once:** with USB+NUT in place and a good battery, pull the **UPS wall plug** (not the PC power switch) and confirm: on-battery status → graceful shutdown → UPS holds or cuts → plug wall back in → machine powers on from Restore-AC. Do this on a day a reboot is fine.
9. **Optional later:** PiKVM for ATX-level remote power; larger PFC sinewave UPS if measured load sits near 900 W.

## Confidence and remaining unknowns

| Claim | Confidence | Why it could be wrong |
| --- | --- | --- |
| Vendor is CyberPower | High | `PPL-1.3.3-64bit.deb` / `powerpanel` 1.3.3 / `pwrstat` alias |
| USB HID Personal series (not RMCARD) | High | PowerPanel Personal, no SNMP/NUT leftover |
| Exact SKU is CP1500PFCLCD or CP1500PFCLCDa | Medium-high | No receipt, no live USB, no saved `pwrstat -status` dump; LCD will settle it |
| Battery is user-replaceable SLA, aged out | High if the SKU guess holds | Age + typical CPS SLA spec |
| Restore-On-AC is the remote-outage solution | High | Board manual; no BMC |
| I211 WoL is already armed in the OS | Medium | sysfs wakeup is enabled; BIOS Power-On-By-PCI-E and `ethtool` Wake-on:g were not read (no `ethtool` binary, no root BIOS dump) |

The cheapest way to raise SKU confidence to certainty is looking at the LCD, then plugging USB in and running `upsc` or a one-shot PowerPanel `pwrstat -status`.

## Sources

### Local (this host, 2026-09-26)

- `/sys/class/dmi/id/{board_vendor,board_name,bios_version,bios_date}`
- `lsusb`, `/sys/class/hidraw`, `/sys/class/net/enp67s0/{address,device/power/wakeup}`
- `dpkg -l powerpanel` / `dpkg -s powerpanel` (status `rc`, version 1.3.3)
- `~/.zsh_history` (`PPL-1.3.3-64bit.deb`, `pwrstat -status`, `del powerpanel`)
- chezmoi `home/dot_config/aliases.sh` (`alias pwrstat='sudo pwrstat'`)
- `apt-cache policy nut-server` → 2.8.1-5
- `ipmitool mc info` (no device), `tailscale status`, `ip route`

### External

- CyberPower PowerPanel for Linux / Personal Linux v1.4.2 (Debian 13 support, `pwrstat` / `pwrstatd`): [advisory](https://www.cyberpowersystems.com/advisory-notices/powerpanel-personal-v1-4-2-for-linux-released/), [download page](https://www.cyberpowersystems.com/product/software/power-panel-personal/powerpanel-for-linux/)
- ArchWiki [CyberPower UPS](https://wiki.archlinux.org/title/CyberPower_UPS) (PowerPanel vs NUT; do not run both)
- NUT [usbhid-ups(8) on Debian Trixie](https://manpages.debian.org/trixie/nut-server/usbhid-ups.8.en.html) (CyberPower `offdelay` quirk)
- NUT device page [CP1500PFCLCD](https://networkupstools.org/ddl/Cyber_Power_Systems/CP1500PFCLCD.html) (`0764` / `usbhid-ups` / 900 W)
- NUT HCL [stable-hcl.html](https://networkupstools.org/stable-hcl.html) (Cyber Power Systems USB HID models)
- ASUS PRIME TRX40-PRO manual APM section: Restore On AC Power Loss, Power On By PCI-E, ErP Ready ([mans.io extract](https://mans.io/files/viewer/1215449/79)); ASUS FAQ [Restore AC Power Loss](https://www.asus.com/support/faq/1049855/)
- CP1500PFCLCD battery procedure: [manual](https://www.manualowl.com/m/CyberPower/CP1500PFCLCD/Manual/673131?page=6), CyberPower [battery-replacement video](https://www.youtube.com/watch?v=wYAQZohN0CY) (CP1350/1500 PFC Sinewave)

## Recommendation (one paragraph)

Treat this as a **CyberPower Personal USB HID tower, very likely CP1500PFCLCD**, with a **worn-out 24 V SLA pack**. Confirm the SKU on the LCD, plug USB into a rear motherboard port, install **NUT 2.8.1** (`usbhid-ups`) for graceful shutdown, and replace the battery cartridge (RB1290X2 / RB1290X2C for the 1500 VA PFC model). For remote power after outages, set **Restore On AC Power Loss = Power On** (and enable Power On By PCI-E, disable ErP). Keep Intel I211 WoL on `a8:5e:45:d0:74:53` for clean-shutdown wakeups from the LAN. Add PiKVM only if you also want remote ATX/BIOS. Replace the whole UPS only if the label shows a non-sinewave AVR unit, the hardware is damaged, or measured load is against the 900 W ceiling.
