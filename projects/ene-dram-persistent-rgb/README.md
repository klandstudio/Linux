# ENE DRAM Persistent RGB Save

Persistent cold-boot RGB for ENE/Aura-compatible memory, documented from a real Silicon Power XPOWER Zenith DDR5 test on an ASRock X870 Taichi Creator.

## Status

**Confirmed working.** A DIMM that repeatedly returned to the factory rainbow effect after complete power loss was successfully changed to persistent static green. The final test survived a full Windows shutdown and ~30 seconds with PSU power removed, with the saved color visible again before Windows or any RGB software started.

This project is intentionally narrow: it documents the ENE nonvolatile-save path and a conservative SignalRGB plugin patch. It is **not** a general RAM firmware flasher.

## Hardware and software used

- ASRock X870 Taichi Creator
- Silicon Power XPOWER Zenith RGB DDR5, 64 GB (2x32 GB), DDR5-6000 CL30
- ENE/Aura-compatible RGB controller on each DIMM
- OpenRGB 1.0rc3.x on Ubuntu
- SignalRGB 2.5.74 on Windows 11
- Stock SignalRGB plugin: `Plugins\Asus\ENE_RAM.js`

The two DIMMs appeared in OpenRGB on AMD SMBus addresses `0x71` and `0x73`. Swapping the DIMMs between slots showed that the already-saved color followed the physical DIMM, confirming that the persistent state is stored on the RAM module's ENE RGB controller rather than in motherboard BIOS settings.

## Important safety warning

The stock SignalRGB plugin itself begins with this warning:

> Modifying SMBUS plugins is dangerous and can destroy devices.

Treat that literally.

- Do not use this on unknown SMBus devices.
- Do not probe arbitrary I2C/SMBus addresses.
- Do not repeatedly issue persistent writes for experimentation.
- Keep an untouched copy of the original plugin.
- This patch deliberately refuses the XTREEM path and unknown ENE protocol versions.
- Use the one-shot control only when you intentionally want to change the DIMM's cold-boot color.

## Discovery 1: OpenRGB already has an ENE save path

OpenRGB contains a persistent ENE save operation, but ENE saving is gated by a setting that is not normally exposed in the GUI.

On Linux, with OpenRGB fully closed, add this to `~/.config/OpenRGB/OpenRGB.json`:

```json
"ENESMBusSettings": {
    "enable_save": true
}
```

After restarting OpenRGB, ENE DRAM modes such as **Static** expose an enabled **Save To Device** button.

The relevant OpenRGB behavior is:

1. Write the effect/static color buffer.
2. Select Static mode.
3. Disable Direct mode so the controller uses its internal effect/static state.
4. Save by writing `0xAA` to ENE register `0x80A0`.

OpenRGB source references:

- `ENE_REG_APPLY = 0x80A0`
- `ENE_SAVE_VAL = 0xAA`
- `SaveMode()` writes the save value to the apply register.

Upstream source:

- https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/ENESMBusController/ENESMBusController.h
- https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/ENESMBusController/ENESMBusController.cpp
- https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/ENESMBusController/RGBController_ENESMBus.cpp

### What happened in testing

One DIMM accepted the OpenRGB save and reliably booted green after complete loss of standby power. The second DIMM did not, even after:

- repeating the OpenRGB save,
- rebuilding the hidden JSON setting from scratch,
- moving the stubborn DIMM into the slot previously occupied by the working DIMM,
- and testing ASRock Polychrome Sync in Windows.

Polychrome controlled both DIMMs at runtime but did not expose or perform a verified persistent DRAM save.

That asymmetry motivated the SignalRGB experiment below.

## Discovery 2: stock SignalRGB uses volatile Direct mode

SignalRGB's stock `ENE_RAM.js` detects and controls the memory correctly, but its normal initialization calls `SetDirectMode()` and its runtime path sends RGB data to the controller's direct-color buffer. That is appropriate for live effects, but it does not perform the ENE persistent-save sequence.

The patch in this directory adds only the missing one-shot persistent path.

## SignalRGB persistent-save patch

File:

[`signalrgb-ene-persistent.patch`](signalrgb-ene-persistent.patch)

It was developed and tested against SignalRGB 2.5.74's `ENE_RAM.js`.

The patch adds two controls to **Devices -> Aura Compatible RAM -> Lighting**:

- **Persistent Static Color**
- **Write Persistent Static (ONE SHOT)**

When the one-shot toggle changes to ON, the patched plugin:

1. Converts the selected color to ENE's `R, B, G` byte order.
2. Writes that color to the ENE internal effect/static color buffer:
   - V1: `0x8010`
   - V2: `0x8160`
3. Applies changes with `0x80A0 <- 0x01`.
4. Sets Static mode with `0x8021 <- 0x01`.
5. Sets Direct mode OFF with `0x8020 <- 0x00`.
6. Issues the nonvolatile save with `0x80A0 <- 0xAA`.
7. Waits briefly.
8. Restores SignalRGB's normal Direct mode with `0x8020 <- 0x01`, **without issuing another persistent save**.

That last step lets SignalRGB resume normal runtime/canvas effects without changing what the DIMM will use at the next cold boot.

## Installing as a SignalRGB user override

SignalRGB supports user plugins under:

```text
%USERPROFILE%\Documents\WhirlwindFX\Plugins
```

The user override should be named exactly:

```text
ENE_RAM.js
```

Do not edit SignalRGB's versioned application copy in place. On the test machine the built-in file was located at:

```text
%LOCALAPPDATA%\VortxEngine\app-2.5.74\Signal-x64\Plugins\Asus\ENE_RAM.js
```

That path changes when SignalRGB updates.

A safe workflow is:

1. Fully quit SignalRGB.
2. Copy the stock `ENE_RAM.js` somewhere safe.
3. Apply [`signalrgb-ene-persistent.patch`](signalrgb-ene-persistent.patch) to a copy.
4. Place the patched copy at `%USERPROFILE%\Documents\WhirlwindFX\Plugins\ENE_RAM.js`.
5. Start SignalRGB.
6. Verify the new controls appear on the RAM device's Lighting page.

## Using the one-shot save

For the successful green test:

1. Select the target **Aura Compatible RAM** device.
2. Set **Persistent Static Color** to `#00FF00`.
3. Toggle **Write Persistent Static (ONE SHOT)** ON.
4. Wait a few seconds.
5. Toggle it back OFF.
6. Fully quit SignalRGB.
7. Shut Windows down.
8. Remove PSU power for ~30 seconds.
9. Restore power and watch the DIMM before Windows starts.

The previously stubborn DIMM came up green during pre-OS startup, confirming persistence.

### Returning the RAM to normal SignalRGB effects

The persistent-save color is independent of SignalRGB's normal runtime mode.

After saving, set the device's **Lighting Mode** back to **Canvas** if you want the RAM to participate in the active SignalRGB effect. Using **Forced** intentionally exempts that device from the canvas and holds it at the forced runtime color.

## Rollback

To return to SignalRGB's stock plugin:

1. Fully quit SignalRGB.
2. Delete or rename:

```text
%USERPROFILE%\Documents\WhirlwindFX\Plugins\ENE_RAM.js
```

3. Restart SignalRGB.

SignalRGB will fall back to its built-in plugin. No application reinstall is required.

## Why this lives in the KLand Studio Linux repository

The project began with Linux/OpenRGB reverse engineering, and the actual ENE register behavior came from OpenRGB's Linux-capable SMBus implementation. The Windows SignalRGB patch is a companion tool used to reproduce the same hardware save operation on a DIMM that did not persist reliably through OpenRGB's GUI path.

It fits this repository's purpose: practical hardware reverse engineering and reusable tooling, even though the final companion implementation runs in Windows.

## Scope and caveats

This was validated on one Silicon Power XPOWER Zenith RGB DDR5 kit using ENE/Aura-compatible controllers. It should not be assumed safe for every RAM family that SignalRGB can detect.

In particular:

- the patch does not attempt firmware updates,
- it does not write SPD data,
- it does not change memory timings or voltages,
- it does not touch the motherboard BIOS,
- and it deliberately avoids the SignalRGB XTREEM branch.

The only persistent operation added is the ENE RGB controller's documented-by-OpenRGB save/apply register sequence.
