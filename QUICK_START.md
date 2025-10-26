# 🚀 Quick Start Guide - Smart Glasses Demo

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- Camera (webcam, USB camera, or integrated camera)
- Telegram account

## Step 1: Install Dependencies

### Option A: Automatic Installation (Recommended)
```bash
./install.sh
```

### Option B: Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Telegram Bot

1. **Create a Telegram Bot**:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy your bot token

2. **Get your Chat ID**:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your chat ID

3. **Configure the system**:
   ```bash
   cp .env.example .env
   nano .env  # or your preferred editor
   ```
   
   Update these lines in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

## Step 3: Test System

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run system test
python test_system.py
```

## Step 4: Run Demo

```bash
python main.py --mode demo
```

This will:
- Record a 10-second video from your camera
- Send it to your Telegram bot
- Analyze it for hazards
- Show results

## Usage Modes

### Demo Mode (Quick Test)
```bash
python main.py --mode demo
```

### Continuous Monitoring
```bash
python main.py --mode monitor
```

### API Only
```bash
python main.py --mode api
```

## Telegram Bot Commands

Once running, use these commands in Telegram:

- `/start` - Initialize bot
- `/record` - Start recording
- `/analyze` - Analyze latest video  
- `/status` - System status
- `/help` - Show help

## Web Interface

Access the web dashboard at: http://localhost:8000

## Docker Quick Start

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your Telegram credentials

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## Troubleshooting

### Camera Issues
- Check camera permissions
- Try different camera index (0, 1, 2) in `.env`
- On Linux: `ls /dev/video*` to see available cameras

### Telegram Issues
- Verify bot token and chat ID
- Make sure bot is not blocked
- Check internet connection

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version`

### Performance Issues
- For GPU acceleration: Install CUDA and run `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`
- Reduce video quality in `.env`: `VIDEO_QUALITY=480p`
- Lower FPS: `FPS=15`

## Next Steps

1. **Customize Detection**: Modify `cv_analyzer.py` for your specific use case
2. **Add More Cameras**: Configure multiple camera sources
3. **Deploy Production**: Use Docker Compose with monitoring
4. **Integrate**: Use the REST API for external systems

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Run `python test_system.py` to diagnose issues
- Review logs in the `logs/` directory

## Production Deployment

For production use:

1. **Use Docker**:
   ```bash
   docker-compose -f docker-compose.yml --profile production up -d
   ```

2. **Set up reverse proxy** (nginx configuration included)

3. **Enable monitoring** with Prometheus/Grafana:
   ```bash
   docker-compose --profile monitoring up -d
   ```

4. **Configure systemd service** for auto-start

---

**Happy monitoring! 🛡️ Stay safe with AI-powered hazard detection.**
