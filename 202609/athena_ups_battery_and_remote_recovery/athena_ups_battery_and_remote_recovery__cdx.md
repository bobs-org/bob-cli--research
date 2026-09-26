# UPS recovery and remote power-on plan for `athena`

**Research date:** 2026-09-26  
**Scope:** identify the likely UPS, decide whether to replace its battery or the whole unit, restore graceful outage handling, and make `athena` remotely recoverable when it is powered off.

## Bottom line

The UPS is almost certainly a **CyberPower**. The best single-model guess is a **CyberPower CP1500PFCLCD**, but that part is only a low-confidence inference and must not be used to order a battery. Read the model and serial-number label on the back or bottom first.

The best implementation is layered:

1. **Restore the UPS itself:** identify it physically, replace the exact manufacturer-specified battery if the UPS is less than about eight years old and otherwise healthy, or replace the entire UPS if it is eight-plus years old, damaged, simulated-sine, or too small under measured peak load.
2. **Reconnect its USB cable and use Network UPS Tools (NUT)** on Debian for monitoring, notification, graceful shutdown, and the UPS output-off/output-return sequence. Do not resurrect the obsolete `pwrstat` 1.3.3 installation.
3. **Set the motherboard to start automatically after AC returns** and enable PCIe Wake-on-LAN. This costs nothing and covers the normal outage-return path.
4. **Use a PiKVM V4 Mini as the primary remote-power path.** Wire its ATX board across the case power/reset headers, connect HDMI and USB, power it independently from a battery-backed UPS outlet, and put it on the existing Tailscale tailnet. This provides a real remote power button plus pre-boot/UEFI console access even when `athena` is off.
5. Keep the **ONT/modem, router, Ethernet switch, and PiKVM** on battery-backed outlets too. A powered-off server cannot be reached through Tailscale, and cloud host `apollo` cannot directly deliver an Ethernet magic packet into the home LAN.

This combines automatic recovery, a cheap fallback (WoL), and true out-of-band control. A smart plug alone is not a good primary solution: it cannot show POST/UEFI failures and encourages unsafe hard power cuts.

## What the machine itself reveals

These are direct observations made on `athena`, not guesses:

| Observation | Result | Consequence |
| --- | --- | --- |
| Host/OS | `athena`, Debian 13, kernel 6.12 | NUT 2.8.1 is available from the configured Debian repository. |
| Motherboard | ASUS PRIME TRX40-PRO, BIOS 1101 dated 2020-06-05 | Consumer board with no BMC/IPMI, but documented AC-restore and WoL firmware options. |
| CPU/GPU | Threadripper 3970X and GeForce RTX 3080 Ti | Potentially heavy load; UPS watts and measured headroom matter. |
| Live NIC | Intel I211 (`igb`), `enp67s0`, MAC `A8:5E:45:D0:74:53` | Good WoL candidate. Kernel PCI wake is currently `enabled`; NetworkManager still uses its unspecified `default` policy. |
| LAN | `192.168.1.156/24`, gateway `192.168.1.1`; Tailscale is active | A local always-on sender is required for WoL. |
| Current USB devices | No UPS present | The remembered UPS USB cable is not attached now. |
| Old software | Debian database retains `powerpanel` 1.3.3 as removed/config-files only | Package metadata identifies CyberPower Systems as its maker and says `pwrstat` was its CLI. |
| Shell history | `sudo apt install ./PPL-1.3.3-64bit.deb`, several `pwrstat -status` calls, then removal of `powerpanel` in 2023 | Strong corroboration that the UPS was controlled locally through CyberPower's Linux package. |
| Current UPS software | No NUT, `apcupsd`, PowerPanel daemon, or `pwrstat` installed | Monitoring and graceful shutdown are absent today. |

The motherboard manual independently confirms **WOL by PME** and exposes these exact UEFI choices under Advanced → APM Configuration:

- `Restore On AC Power Loss`: `Power On`, `Power Off`, or `Last State`
- `ErP Ready`: enabling this switches off PME options, so leave it **Disabled**
- `Power On By PCI-E`: enables Wake-on-LAN for onboard or add-in PCIe NICs

The current UEFI values cannot safely be read from the running OS, so they still need to be checked in setup.

## UPS identification: what is known and what is not

### Manufacturer: CyberPower, very high confidence

`pwrstat` came from CyberPower's PowerPanel for Linux package. The installed package record is explicit:

> PowerPanel for Linux ... monitors the status of your CyberPower Systems UPS ... `pwrstatd` ... communicates with the UPS while `pwrstat` is an interface.

This is substantially stronger evidence than a generic recollection of a command name. I would assign **greater than 95% confidence** to CyberPower.

### Model guess: CP1500PFCLCD, low confidence

My best guess is **CyberPower CP1500PFCLCD** (roughly 40–50% confidence), with CP1500AVRLCD and another 1350/1500 VA CyberPower tower as the main alternatives. Reasons:

- A 32-core Threadripper workstation with a 3080 Ti is the kind of active-PFC, high-wattage system for which the 1500 VA pure-sine PFC model is commonly selected.
- The current CP1500PFCLCD is 1500 VA / 1000 W, USB HID capable, Linux-manageable, and NUT has model-specific reports for it.
- The adjacent shell-history context suggests the CyberPower Linux package was sought around the 2020 system-build era. If the battery is original, a failure in 2026 is exactly in the expected age range.

Why confidence is not higher: `pwrstat` supported many CyberPower models, no old status output or USB descriptor survives locally, and no CyberPower/model purchase message was found in the read-only Gmail search. Hardware suitability is evidence for what probably was bought, not proof of what was bought.

### The physical check that resolves this

CyberPower says the white serial-number label is on the **back or bottom** and may also include the model. Photograph the entire label and the front/rear panel, then record:

- exact model, including all suffixes;
- complete serial prefix and manufacture date;
- VA and watt rating;
- whether it says sine wave/PFC and whether it has a remote-management expansion slot;
- battery/replacement-cartridge code if shown;
- LCD load percentage or watts while `athena` is doing representative work.

Do not order by appearance or by `CP1500PFCLCD` alone. Even the current CP1500PFCLCD page lists different cartridges by serial prefix: `RB1290X2` for CXX, and `RB1280X2B` for CR9/CXF/CQC. The current unit is also explicitly **not hot-swappable**. Older revisions may differ, so follow the manual matching the label.

## Replace the battery or replace the UPS?

CyberPower puts typical sealed-lead-acid battery life at **three to five years**, describes years five to seven as the aging/degradation stage, and recommends retiring a UPS at about eight-plus years because surge protection and electronics have aged too. That yields a practical decision rule:

### Replace only the battery when all are true

- the label shows the UPS is under roughly eight years old;
- it is a pure-sine model with enough measured watt capacity;
- there is no swelling, corrosion, burnt smell, excess heat, fan fault, or outlet/relay problem;
- it has not already had repeated battery changes or damaging overloads;
- an exact OEM cartridge is readily available.

If the guess is correct, CyberPower currently lists the CP1500PFCLCD at 1500 VA / 1000 W, with 2.5 minutes at full load and 10 minutes at half load. Its cartridge uses two 12 V batteries. CyberPower lists `RB1280X2B` at a $127 MSRP; the actual cartridge still depends on serial prefix. After replacement, charge for at least the manual's specified interval (the current model specifies eight hours), then run both a self-test and a real controlled outage test.

### Replace the whole UPS when any are true

- manufacture age is eight-plus years or unknown but clearly old;
- the case/battery is swollen, leaking, corroded, hot, or electrically suspect;
- it is a simulated-sine model and this workstation has ever been unstable on battery;
- peak measured load exceeds about 65–70% of rated watts;
- the replacement cartridge is a large fraction of a new suitable UPS's cost;
- reliable independent network management is desired and the existing revision has no expansion slot.

For context, the CPU alone has a 280 W default TDP and the reference 3080 Ti is a 350 W card. Drives, RAM, fans, motherboard, conversion loss, and transient GPU/CPU peaks are additional. Their nameplate figures cannot predict wall draw, but they show why a 600–900 W UPS could be marginal and why the LCD/NUT load reading must be measured under the real simultaneous workload. CyberPower itself recommends 30–35% capacity headroom. If peak load is above roughly 700 W, prefer a unit with at least 1200 W output rather than merely another nominal “1500 VA” model.

The UPS is for ride-through and orderly shutdown, not for continuing maximum CPU/GPU work through a long outage. Configure an early clean shutdown while ample runtime remains.

## UPS software: use NUT over USB

### Why NUT

- Debian 13 currently offers `nut`, `nut-client`, and `nut-server` 2.8.1 directly.
- NUT's `usbhid-ups` driver supports CyberPower HID devices.
- Its CP1500PFCLCD compatibility record includes charge/runtime/load telemetry, self-tests, beeper control, `load.off.delay`, `load.on.delay`, and `shutdown.return`.
- `shutdown.return` is the key outage-recovery behavior: after the OS shuts down, the UPS drops its output and turns it back on when utility power returns. That gives firmware `Restore On AC Power Loss = Power On` a real off→on edge.
- The removed PowerPanel 1.3.3 is very old; CyberPower declared PowerPanel Business 4.10 and older end-of-life in 2025. Current PowerPanel Business is a valid vendor alternative, but NUT is smaller, open, in Debian, and demonstrably supports the likely model.

### Configuration outline

After the exact UPS is known and USB is directly connected:

1. Install Debian's NUT packages and set standalone mode.
2. Detect the device with `nut-scanner -U`; verify vendor/product/model/serial with `upsc` rather than hard-coding a guessed model.
3. Configure a `usbhid-ups` stanza in `/etc/nut/ups.conf`. A CyberPower starting point is `port = auto`, with the detected `vendorid`/`productid` only if needed to disambiguate.
4. Configure a local monitor user, `upsmon`, a shutdown command, and the power-down flag. Use `upssched` if the policy should shut down after a fixed on-battery interval rather than waiting for the UPS's low-battery assertion.
5. For CyberPower, heed NUT's documented timing quirk: many models divide delay values by 60 and round down. NUT recommends at least `offdelay = 60` and `ondelay = 120` for CPS devices. Confirm which commands the actual UPS reports before relying on output cycling.
6. Alert on communication loss, on-battery, low-battery, replace-battery, and recovery-to-line events.

A sensible initial policy for this workstation is: notify immediately on battery, allow only a short ride-through (for example 2–3 minutes), begin clean shutdown while runtime is still comfortably above five minutes, and then let NUT request UPS output shutdown/return. Tune the thresholds from measured runtime, not the new-battery marketing curve.

### Acceptance test (maintenance window)

Do not call the installation finished merely because `upsc` prints values.

1. Charge fully and run the UPS's quick self-test.
2. Confirm `OL`, load percentage, charge, runtime, model, serial, and supported instant commands.
3. Shut `athena` down and prove a local WoL packet can start it.
4. With utility present and filesystems quiescent, perform NUT's documented forced-shutdown drill (`upsmon -c fsd`) and prove that the UPS cycles output and the UEFI boots the host again. This command intentionally shuts the machine down; use a maintenance window.
5. In a second drill, remove **utility input to the UPS**, not the UPS's output cable to the running PC. Verify `OB`, alerts, the chosen shutdown delay, clean halt, output-off behavior, and automatic boot only after utility is restored.
6. Repeat a shortened drill after every battery replacement or major NUT/firmware change, and do a runtime/self-test at least twice a year.

## Remote power-on: options and recommendation

| Option | Handles normal outage return | Turns on an intentionally shut-down host | Works before OS boot | Needs another powered LAN device | Assessment |
| --- | ---: | ---: | ---: | ---: | --- |
| UEFI AC restore + NUT UPS power cycle | Yes | No | N/A | No | Essential free baseline. |
| Wake-on-LAN | Sometimes | Yes | No console | Yes | Useful free fallback, not sufficient alone. |
| Cloud smart plug + AC restore | Yes, if network/cloud returns | Yes, by hard cycling AC | No console | Usually | Avoid as primary; unsafe if OS is live and awkward behind a UPS. |
| UPS network card / switched PDU | Yes | Often via output cycle | No console | Network infrastructure | Good power telemetry, but existing-model compatibility is uncertain and it still lacks a BIOS console. |
| **PiKVM V4 Mini ATX control** | **Yes, as fallback** | **Yes, via a real power-button action** | **Yes: video, keyboard, UEFI** | It is the powered LAN device | **Recommended primary out-of-band path.** |

### Free baseline: configure AC restore and WoL

In ASUS UEFI Advanced → APM Configuration:

- `Restore On AC Power Loss` → **Power On**
- `ErP Ready` → **Disabled**
- `Power On By PCI-E` → **Enabled**

Then make NetworkManager's policy explicit rather than leaving it at `default`:

```sh
sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.wake-on-lan magic
```

Reboot or reactivate the connection, shut down cleanly, and send a magic packet to `A8:5E:45:D0:74:53` from another device on `192.168.1.0/24`.

Tailscale explains the important limitation: WoL is Layer 2 while Tailscale is Layer 3, so a remote Tailscale client cannot simply broadcast the magic packet into the home LAN, even with subnet routing. A powered local helper must transmit it. A PiKVM, small Raspberry Pi, Home Assistant host, supported router, or Tailscale-accessible UpSnap service can do that. `apollo`, by itself in DigitalOcean, cannot.

### Recommended out-of-band path: PiKVM V4 Mini

The official PiKVM V4 Mini bundle includes an ATX control board and cables. It can emulate short/long power-button presses and reset, capture HDMI video, provide keyboard/mouse and virtual media, and expose UEFI/POST before Linux starts. The official project currently lists it around **$250–270 before tax** from in-stock US-facing sellers.

Install it as follows:

- Put the ATX adapter inline/parallel with `athena`'s front-panel power and reset leads; preserve the physical case buttons.
- Connect an `athena` GPU HDMI output and the PiKVM USB emulation cable.
- Power PiKVM from its own adapter plugged into a battery-backed UPS outlet—**not** from `athena`'s USB port.
- Wire PiKVM Ethernet to the same protected switch/router path.
- Install Tailscale on PiKVM, enroll it in `tail297af1.ts.net`, use a narrowly scoped tailnet ACL, enable PiKVM 2FA, and avoid public port forwarding. PiKVM's own guide suggests disabling Tailscale key expiry for this unattended device; compensate with tight ACLs and an asset/recovery record.
- Also power the ISP ONT/modem, router, and required Ethernet switch from battery-backed outlets. When utility returns after total battery exhaustion, these devices and PiKVM boot independently, after which PiKVM can press `athena`'s power button if automatic AC restore failed.

The V4 Mini is preferable to a relay-only board because a failure that prevents boot is exactly when remote video and keyboard access are most valuable. If remote access must survive an ISP-wide outage too, add an independently powered cellular router; that is a separate availability tier and probably unnecessary initially.

### Why not make a smart plug the main control?

A smart plug between the UPS and PC can force an AC edge for `Restore On AC Power Loss`, but it has four drawbacks: hard-off risks data loss, the plug must tolerate workstation inrush/current, cloud control may be unavailable during the same outage, and it provides no diagnosis when POST fails. If one is used at all, it should be a locally controllable, correctly rated last-resort device, and it should only be switched off after independent confirmation that the OS has halted. PiKVM's ATX control is safer and more capable.

## Expected behavior after implementation

1. **Brief outage:** UPS carries the load; NUT reports/alerts; no reboot.
2. **Long outage:** NUT cleanly shuts Debian down while battery remains, then commands the UPS output off/return.
3. **Utility returns:** protected network gear and PiKVM boot automatically; UPS restores load; ASUS `Power On` starts `athena`.
4. **Automatic boot fails:** connect to PiKVM through Tailscale, inspect POST/UEFI, and issue an ATX power-button press or reset.
5. **Host was intentionally shut down while AC stayed on:** use PiKVM ATX control; WoL from PiKVM/local helper is the secondary path.

This is a much stronger recovery chain than any one of USB shutdown, WoL, a smart plug, or AC-restore firmware alone.

## Recommended purchase/implementation order

1. Today: photograph the UPS label/front/rear and reconnect its USB cable; treat the current battery as failed until proven otherwise.
2. Measure actual idle and peak load from the LCD after identification. If practical, also use a true-watt wall meter under representative simultaneous CPU/GPU load.
3. If under eight years old, healthy, pure-sine, and adequately sized, buy the exact OEM cartridge matched by model **and serial prefix**. Otherwise buy a new pure-sine UPS with at least 30–35% measured headroom; for a peak above about 700 W, target at least 1200 W output.
4. Configure and test NUT over USB.
5. Set the three UEFI power options and explicitly configure/test WoL.
6. Buy/install a PiKVM V4 Mini, place it and the home network path on backed-up power, and enroll it in Tailscale.
7. Run the complete outage/restore drill and record the verified runtime and recovery procedure.

## Final recommendation and model guess

**Recommended solution:** restore or replace the UPS based on its physical label, age, condition, and measured load; manage it with NUT over a direct USB connection; set ASUS AC restore to `Power On`; enable WoL as a secondary method; and install a separately powered PiKVM V4 Mini on the tailnet as the authoritative remote power button and pre-boot console. Back up the ONT/router/switch/PiKVM alongside the server and validate the entire shutdown/output-cycle/restart chain under controlled conditions.

**Best UPS guess:** **CyberPower CP1500PFCLCD**, probably a 2020-era revision. Manufacturer confidence is very high; exact-model confidence is low. The physical model/serial label is required before buying any battery.

## Sources

- [ASUS PRIME TRX40-PRO user manual](https://dlcdnets.asus.com/pub/ASUS/mb/SocketTRX4/PRIME_TRX40-PRO/E16115_PRIME_TRX40-PRO_UM_V2_WEB.pdf?model=PRIME+TRX40-PRO) — WOL capability and APM options.
- [CyberPower CP1500PFCLCD product page](https://www.cyberpowersystems.com/product/ups/pfc-sinewave/cp1500pfclcd/) — current capacity, runtime, USB, cartridges, and management specifications.
- [CyberPower: where the UPS serial number is located](https://www.cyberpowersystems.com/faqs/where-is-the-serial-number-located-on-the-unit/) — label location.
- [CyberPower: the lifecycle of a UPS system](https://www.cyberpowersystems.com/blog/the-lifecycle-of-a-ups-system/) — battery aging and retirement guidance.
- [CyberPower RB1280X2B product page](https://www.cyberpowersystems.com/product/ups/replacement-batteries/rb1280x2b/) — cartridge construction, capacity, and current MSRP.
- [CyberPower PowerPanel EOL notice](https://www.cyberpowersystems.com/advisory-notices/power-panel-personal-business-version-eol/) — older PowerPanel support status.
- [NUT `usbhid-ups` manual](https://networkupstools.org/docs/man/usbhid-ups.html) — CyberPower support, shutdown/restart behavior, delay caveats, and test procedure.
- [NUT CP1500PFCLCD compatibility report](https://networkupstools.org/ddl/Cyber_Power_Systems/CP1500PFCLCD.html) — observed telemetry and supported commands.
- [Tailscale: Wake-on-LAN with a local sender](https://tailscale.com/blog/wake-on-lan-tailscale-upsnap) — Layer-2 limitation and relay design.
- [PiKVM V4 quickstart](https://docs.pikvm.org/v4/) and [PiKVM ATX board guide](https://docs.pikvm.org/atx_board/) — included hardware and physical power control.
- [PiKVM Tailscale guide](https://docs.pikvm.org/tailscale/) — tailnet enrollment and unattended-device considerations.
- [Official PiKVM reseller/price list](https://pikvm.org/buy/) — current V4 Mini availability and price range.
- [AMD Threadripper 3970X specifications](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen-threadripper/ryzen-threadripper-3000-series/amd-ryzen-threadripper-3970x.html) and [NVIDIA RTX 3080 Ti specifications](https://www.nvidia.com/en-gb/geforce/graphics-cards/30-series/rtx-3080-3080ti/) — component power context.

