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

## ⚠️ Legal Disclaimer

**Lunar Tear** is a fan-made, non-commercial **preservation and research project** dedicated to keeping the now-discontinued mobile game *NieR Re[in]carnation* playable for educational and archival purposes.

- This project is **not affiliated with**, **endorsed by**, or **approved by** Square Enix Co., Ltd. or any of its subsidiaries.
- All trademarks, copyrights, and intellectual property related to *NieR Re[in]carnation*, the *NieR* series, and associated assets belong to their respective owners.
- All code in this repository is original work developed through clean-room reverse engineering for interoperability with the game client.
- No copyrighted game assets, binaries, or master data are distributed in this repository.

**Use at your own risk.** The author assumes no liability for any damages or legal consequences that may arise from using this software. By using or contributing to this project, you are solely responsible for ensuring your usage complies with all applicable laws in your jurisdiction.

This project is released under the [MIT License](LICENSE).

**If you are a Square Enix representative:** Please contact me directly if you have any concerns regarding this project.
