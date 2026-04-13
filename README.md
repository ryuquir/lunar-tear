# Lunar Tear

Private server research project for **NieR Reincarnation**.

Lunar Tear emulates key game backend services so a patched client can connect to a local/private server instead of official endpoints.

Current project direction:

- Keep client changes minimal (prefer static APK patching over heavy runtime hooks).
- Implement missing game behavior on the server.
- Use Frida mainly for investigation/debugging, not as a permanent runtime dependency.

## Assets Layout

The server reads game data from `server/assets/` at runtime.

```
server/
  assets/                # game data — NOT checked in
    master_data/         # JSON master tables (quest, gacha, weapons, etc.)
    release/             # MasterMemory database.bin.e
    revisions/           # Octo revision dirs with list.bin + asset bundles
```

## How To Patch An APK

Static patcher: `scripts/patch_apk.py`.

It patches:

1. `global-metadata.dat` URL/hostname strings
2. `libil2cpp.so` (SSL bypass + crypto passthrough + Octo list behavior)
3. `AndroidManifest.xml` (`networkSecurityConfig`)
4. `res/xml/network_security_config.xml` (allow cleartext HTTP)

### Prerequisites

- Python 3
- `apktool`
- Android build tools (`apksigner`, `zipalign`)
- A decompiled APK directory (from `apktool d`)

### Steps

1. Decompile APK:

```bash
apktool d client/3.7.1.apk -o client/patched
```

2. Run patcher (example for emulator host):

```bash
python3 scripts/patch_apk.py client/patched --server-ip 10.0.2.2 --http-port 8080
```

3. Rebuild:

```bash
apktool b client/patched -o client/patched.apk
```

4. Generate signing key (one-time):

```bash
keytool -genkeypair \
  -v \
  -keystore client/debug.keystore \
  -alias androiddebugkey \
  -storepass android \
  -keypass android \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"
```

5. Align + sign:

```bash
apksigner sign --ks client/debug.keystore --ks-pass pass:android client/patched.apk
```

Notes:

- `--server-ip` replacement must fit existing metadata string lengths (the script validates this).
- The client hardcodes gRPC to port 443. HTTP port is baked into the patched URL.

## How To Setup Frida

Frida is mainly for local debugging/probing.

### Prerequisites

- Android emulator/device with `adb`
- `frida-tools` on host
- `frida-server` binary on device (commonly `/data/local/tmp/frida-server`)

### Setup Steps

1. Start `frida-server` on device:

```bash
adb shell "su -c /data/local/tmp/frida-server" &
```

2. Launch game with a script:

```bash
tail -f /dev/null | frida -Uf com.square_enix.android_googleplay.nierspww -l frida/hooks.js
```

Useful references:

- `docs/FRIDA_GUIDE.md`

## How To Launch The Server

### Prerequisites

- Go 1.24+
- Populated `server/assets/` directory

### Run

```bash
cd server
sudo go run ./cmd/lunar-tear \
  --host 10.0.2.2 \
  --http-port 8080 \
  --scene 13
```

`sudo` is needed because gRPC binds to port 443 (privileged). On Linux you can use `setcap` instead:

```bash
go build -o lunar-tear ./cmd/lunar-tear
sudo setcap cap_net_bind_service=+ep ./lunar-tear
./lunar-tear --host 10.0.2.2 --http-port 8080 --scene 13
```

### Ports

| Protocol | Port | Notes                                                |
| -------- | ---- | ---------------------------------------------------- |
| gRPC     | 443  | hardcoded by the client, not configurable            |
| HTTP     | 8080 | Octo asset API + game web pages (`--http-port` flag) |

### Flags

| Flag                   | Default             | Description                                              |
| ---------------------- | ------------------- | -------------------------------------------------------- |
| `--host`               | `127.0.0.1`         | hostname/IP given to the client                          |
| `--http-port`          | `8080`              | HTTP/Octo server port                                    |
| `--resources-base-url` | (derived from host) | base URL for list.bin rewrite (must be exactly 43 chars) |
| `--scene`              | `0`                 | bootstrap new users to scene N (0 = fresh start)         |

### Optional: Regenerate protobuf stubs

```bash
cd server
make proto
```

## ⚠️ Legal Disclaimer & Notice

**Lunar Tear** is an independent **research and preservation project** for the now-discontinued mobile game _NieR Re[in]carnation_.

- This project is **not affiliated with**, **endorsed by**, or **approved by** Square Enix Co., Ltd. or any of its subsidiaries.
- All trademarks, copyrights, and intellectual property related to _NieR Re[in]carnation_, _NieR_ series, and associated assets belong to their respective owners (Square Enix and relevant parties).
- The code in this repository is original work developed through clean-room reverse engineering and interoperability research.

**This project is provided strictly for educational, research, and private preservation purposes.**

### Important Warnings:

- Using this software requires modifying the official game client (APK patching). Such modifications may violate Square Enix's End User License Agreement (EULA) and Terms of Service.
- Running a private server or using a patched client can constitute unauthorized access or derivative works under copyright law in some jurisdictions.
- **I do not encourage or condone any use that violates applicable laws, EULAs, or Square Enix's rights.**
- No copyrighted game assets, binaries, or master data are provided in this repository. Users must obtain and provide their own legitimate copies of the game files.
- The project may bypass technical protection measures (e.g., SSL pinning) solely for research and local interoperability.

**Use at your own risk.** The author assumes no liability for any damages, legal consequences, or account issues that may arise from using this software.

This project is released under the [MIT License](LICENSE). By using or contributing to this repository, you agree that you are solely responsible for ensuring your usage complies with all applicable laws in your jurisdiction.

**If you are Square Enix or a representative:** Please contact me directly if you have any concerns regarding this project.
