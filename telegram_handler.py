import asyncio
import logging
from pathlib import Path
from datetime import datetime

from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config

logger = logging.getLogger(__name__)


class TelegramHandler:
    """Handles Telegram bot functionality for sending/receiving videos and commands"""

    def __init__(self, video_callback=None, analysis_callback=None, stop_callback=None):
        self.bot: Bot | None = None
        self.application: Application | None = None
        self.video_callback = video_callback              # Callable[[], str|None]
        self.analysis_callback = analysis_callback        # Callable[[str], dict|None]
        self.stop_callback = stop_callback                # Callable[[], None]
        self._stop_event: asyncio.Event | None = None

    async def initialize_bot(self) -> bool:
        """Initialize the Telegram bot and register handlers"""
        try:
            self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

            # Command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("record", self.record_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("analyze", self.analyze_command))
            self.application.add_handler(CommandHandler("help", self.help_command))

            # Media handlers
            self.application.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

            # Custom keyboard actions (buttons)
            self.application.add_handler(
                MessageHandler(filters.TEXT & filters.Regex(r'^Start Recording$'), self.start_button_handler)
            )
            self.application.add_handler(
                MessageHandler(filters.TEXT & filters.Regex(r'^Stop Recording$'), self.stop_button_handler)
            )

            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot initialized successfully: @{bot_info.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            return False

    # =========================
    # Command Handlers
    # =========================

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command: greet and show Start/Stop buttons"""
        welcome_message = (
            "\n🤖 Smart Glasses Demo Bot Started!\n\n"
            "Available commands:\n"
            "/record - Start video recording\n"
            "/status - Check system status\n"
            "/analyze - Analyze latest video\n"
            "/help - Show this help message\n\n"
            "Use the buttons below to Start/Stop recording."
        )
        keyboard = [[KeyboardButton("Start Recording"), KeyboardButton("Stop Recording")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def record_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /record: record now, then analyze, send processed video + summary"""
        try:
            await update.message.reply_text("🎥 Starting video recording...")
            if not self.video_callback:
                await update.message.reply_text("❌ Video recording not configured")
                return

            # Record video (blocking in executor)
            video_path = await asyncio.get_event_loop().run_in_executor(None, self.video_callback)
            if not video_path or not Path(video_path).exists():
                await update.message.reply_text("❌ Failed to record video")
                return

            # Analyze and send results
            if self.analysis_callback:
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self.analysis_callback, str(video_path)
                )
                await self.send_analysis_results(results, update.effective_chat.id)
            else:
                await update.message.reply_text("ℹ️ Analysis not configured")
        except Exception as e:
            logger.error(f"Error in record command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_info = {
            "timestamp": datetime.now().isoformat(),
            "bot_status": "✅ Active",
            "storage_path": str(Config.VIDEO_STORAGE_PATH),
            "model_path": Config.MODEL_PATH,
            "confidence_threshold": Config.CONFIDENCE_THRESHOLD,
        }
        status_text = "🔍 System Status:\n\n" + "\n".join(f"{k}: {v}" for k, v in status_info.items())
        await update.message.reply_text(status_text)

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command: analyze latest video and send results"""
        await update.message.reply_text("🔍 Starting analysis of latest video...")
        video_files = list(Config.VIDEO_STORAGE_PATH.glob("*.mp4"))
        if not video_files:
            await update.message.reply_text("❌ No video files found to analyze")
            return
        latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
        if not self.analysis_callback:
            await update.message.reply_text("❌ Analysis not configured")
            return
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None, self.analysis_callback, str(latest_video)
            )
            await self.send_analysis_results(results, update.effective_chat.id)
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            await update.message.reply_text(f"❌ Analysis failed: {str(e)}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "\n🤖 Smart Glasses Demo Bot Help\n\n"
            "Commands:\n"
            "/start - Initialize the bot\n"
            "/record - Start a new video recording\n"
            "/status - Check current system status\n"
            "/analyze - Analyze the latest video for hazards\n"
            "/help - Show this help message\n\n"
            "Features:\n"
            "• Automatic oil leak detection\n"
            "• Hazard identification\n"
            "• Real-time analysis alerts\n"
            "• Video storage and processing\n\n"
            "Send me a video file and I'll analyze it automatically!"
        )
        await update.message.reply_text(help_text)

    # =========================
    # Button Handlers
    # =========================

    async def start_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Start Recording' button: record, analyze, and send results"""
        try:
            await update.message.reply_text("▶️ Recording started...")
            if not self.video_callback:
                await update.message.reply_text("❌ Video recording not configured")
                return
            video_path = await asyncio.get_event_loop().run_in_executor(None, self.video_callback)
            if video_path and Path(video_path).exists():
                if self.analysis_callback:
                    results = await asyncio.get_event_loop().run_in_executor(
                        None, self.analysis_callback, str(video_path)
                    )
                    await self.send_analysis_results(results, update.effective_chat.id)
                else:
                    await update.message.reply_text("ℹ️ Analysis not configured")
            else:
                await update.message.reply_text("❌ Failed to record video")
        except Exception as e:
            logger.error(f"Error in start button handler: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def stop_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Stop Recording' button: stop current recording"""
        try:
            if self.stop_callback:
                await asyncio.get_event_loop().run_in_executor(None, self.stop_callback)
                await update.message.reply_text("⏹️ Stop requested. Finalizing video...")
            else:
                await update.message.reply_text("❌ Stop not configured")
        except Exception as e:
            logger.error(f"Error in stop button handler: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    # =========================
    # Media Handlers
    # =========================

    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received video files: save and analyze"""
        try:
            await update.message.reply_text("📥 Video received! Processing...")
            video_file = await update.message.video.get_file()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = Config.VIDEO_STORAGE_PATH / f"received_{timestamp}.mp4"
            await video_file.download_to_drive(local_path)
            await update.message.reply_text("✅ Video downloaded successfully!")

            if self.analysis_callback:
                await update.message.reply_text("🔍 Starting analysis...")
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self.analysis_callback, str(local_path)
                )
                await self.send_analysis_results(results, update.effective_chat.id)
        except Exception as e:
            logger.error(f"Error handling video: {e}")
            await update.message.reply_text(f"❌ Error processing video: {str(e)}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle received photo files (download only)"""
        try:
            await update.message.reply_text("📸 Photo received! Processing...")
            photo_file = await update.message.photo[-1].get_file()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_path = Config.VIDEO_STORAGE_PATH / f"received_{timestamp}.jpg"
            await photo_file.download_to_drive(local_path)
            await update.message.reply_text("✅ Photo downloaded successfully!")
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text(f"❌ Error processing photo: {str(e)}")

    # =========================
    # Send helpers
    # =========================

    async def send_video(self, video_path: str, caption: str = "", chat_id: int | None = None) -> bool:
        """Send video file to Telegram with optional caption"""
        try:
            target_chat_id = chat_id or Config.TELEGRAM_CHAT_ID
            with open(video_path, 'rb') as video_file:
                await self.bot.send_video(
                    chat_id=target_chat_id,
                    video=video_file,
                    caption=caption,
                    supports_streaming=True
                )
            logger.info(f"Video sent successfully: {video_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
            return False

    async def send_message(self, message: str, chat_id: int | None = None) -> bool:
        """Send text message to Telegram"""
        try:
            target_chat_id = chat_id or Config.TELEGRAM_CHAT_ID
            await self.bot.send_message(chat_id=target_chat_id, text=message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def send_analysis_results(self, results: dict | None, chat_id: int | None = None):
        """Send analysis results to Telegram, ideally as caption of the processed video"""
        try:
            if not results:
                await self.send_message("🔍 Analysis completed - No hazards detected!", chat_id)
                return

            detections = results.get('detections', [])
            total = len(detections)
            high = len([d for d in detections if d.get('confidence', 0) > Config.ALERT_THRESHOLD])
            analysis_time = results.get('analysis_time', 'N/A')

            caption_lines = [
                "🚨 Analysis Results",
                f"📊 Total: {total} | High risk: {high}",
                f"⏰ Time: {analysis_time}s"
            ]
            for d in detections[:5]:
                cls = d.get('class', 'Unknown')
                conf = d.get('confidence', 0)
                mark = '⚠️' if conf > Config.ALERT_THRESHOLD else 'ℹ️'
                caption_lines.append(f"{mark} {cls} ({conf:.2f})")
            caption = "\n".join(caption_lines)
            if len(caption) > 1024:
                caption = caption[:1020] + "..."

            processed = results.get('processed_video_path')
            if processed and Path(processed).exists():
                await self.send_video(processed, caption, chat_id)
            else:
                await self.send_message(caption, chat_id)

            types = results.get('summary', {}).get('detection_types', {})
            if types:
                breakdown = ["📑 Breakdown by type:"]
                for name, info in types.items():
                    breakdown.append(
                        f"• {name}: {info.get('count', 0)} "
                        f"(max {info.get('max_confidence', 0):.2f}, avg {info.get('avg_confidence', 0):.2f})"
                    )
                await self.send_message("\n".join(breakdown), chat_id)
        except Exception as e:
            logger.error(f"Error sending analysis results: {e}")
            await self.send_message(f"❌ Error sending results: {str(e)}", chat_id)

    # =========================
    # Lifecycle
    # =========================

    async def run_bot(self):
        """Initialize and run the Telegram bot within the existing event loop"""
        if not await self.initialize_bot():
            logger.error("Failed to initialize bot")
            return
        self._stop_event = asyncio.Event()
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            await self._stop_event.wait()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            try:
                await self.application.updater.stop()
            except Exception:
                pass
            try:
                await self.application.stop()
            except Exception:
                pass
            try:
                await self.application.shutdown()
            except Exception:
                pass
            logger.info("Telegram bot stopped")

    async def stop_bot(self):
        """Signal the bot to stop"""
        if self._stop_event and not self._stop_event.is_set():
            self._stop_event.set()
