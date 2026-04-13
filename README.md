# Lunar Tear

Private server research project for **NieR Reincarnation**.

## How To Launch The Server

### Prerequisites

- Go 1.24+
- Populated `server/assets/` directory

### Regenerate protobuf stubs

```bash
cd server
make proto
```

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
