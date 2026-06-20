# Marketman Ubuntu Deployment Guide

## Quick Start (5 minutes)

### 1. Install Python and dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 2. Clone and navigate
```bash
cd /path/to/marketman
```

### 3. Setup (create directories, test)
```bash
bash scripts/deploy.sh
```

### 4. Configure your data feed
Create `data/live-feed.csv` with columns: `open,high,low,close,volume`

### 5. Choose execution method

#### Option A: Run once (backtest/test)
```bash
python3 -m marketman.runner \
  --config config/thresholds.json \
  --data data/live-feed.csv \
  --symbol MNQ \
  --output logs/signals.json
```

#### Option B: Run every 5 minutes (cron)
```bash
crontab -e
# Add line from CRONTAB.example
```

#### Option C: Run as system service (systemd)
```bash
sudo bash scripts/deploy.sh  # Must run as root
systemctl start marketman
systemctl status marketman
systemctl enable marketman  # Auto-start on boot
```

## File Structure
```
/workspaces/marketman/
├── config/
│   └── thresholds.json      # MNQ/MES tuning
├── data/
│   ├── sample.csv           # Example data
│   └── live-feed.csv        # Your trading data (create this)
├── logs/
│   ├── test-signals.json    # Output signals
│   └── cron.log             # Cron execution log
├── scripts/
│   ├── deploy.sh            # One-time setup
│   └── run-signals.sh       # Automated runner
├── marketman/
│   ├── runner.py            # Main entry point
│   ├── config.py            # Config loader
│   └── signals.py           # Signal serializer
└── strategy.py              # Core algorithm
```

## Monitoring

### Check recent signals
```bash
tail -f logs/cron.log
ls -lh logs/signals_*.json
cat logs/signals_*.json | jq
```

### Test with sample data
```bash
python3 -m marketman.runner \
  --config config/thresholds.json \
  --data data/sample.csv \
  --symbol MNQ \
  --warmup 25 \
  --format json
```

### Adjust thresholds
Edit `config/thresholds.json` and re-run. Each change:
1. Update JSON
2. Test with `--output test.json`
3. Deploy when validated

## Troubleshooting

### "No signals generated"
- Increase `--warmup` bars for more indicator data
- Check that data has enough rows (>50 minimum recommended)

### CSV format error
- Ensure CSV has columns: `open,high,low,close,volume`
- No header modification needed (header expected)

### Cron not running
```bash
crontab -l                      # List active jobs
grep CRON /var/log/syslog       # Check system logs
```

### Memory/CPU concerns
- Service runs ~50MB
- Each run takes <500ms
- Safe to run every 1 minute if needed

## Production Checklist
- [ ] Data feed is live and updating
- [ ] Logs directory has >100GB free
- [ ] Test run produces expected signals
- [ ] Cron or systemd configured
- [ ] Monitoring in place (log tail, alerts)
- [ ] Config thresholds tuned per contract

---
**For support**: See `.github/instructions/marketman-strategy.instructions.md`
