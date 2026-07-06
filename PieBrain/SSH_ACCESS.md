# CheddarPi — SSH Access

```bash
ssh adamprobert@cheddarpi
```

- **User is `adamprobert`, NOT `pi`** (the gotcha — `pi` doesn't exist).
- Public-key auth only, no password. Private key: `C:\Users\adamp\.ssh\id_ed25519`.
- OS: Debian 13 (trixie), Raspberry Pi 3B. User is in `dialout` (serial), `sudo`, `gpio`, `i2c`.

**Locked out after a re-image?** Public-key auth has no password fallback. Restore access by
dropping a `firstrun.sh` on the SD card's boot partition that appends the public key to
`/home/adamprobert/.ssh/authorized_keys`, armed by appending this to `cmdline.txt` (one line):
`systemd.run=/boot/firmware/firstrun.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target`
