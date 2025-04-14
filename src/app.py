import logging
import pandas as pd
from telegram import Update
from telegram.ext import(
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from global_settings import (
    QUIZ_FILE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_GROUP_CHAT_ID,
    TELEGRAM_PRIVATE_CHAT_IDS,
)
from answer_evaluator import evaluate_answer

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class LoveQuest:
    """
    Class to orchestrate the Love Quest quiz game via Telegram.
    """
    def __init__(self):
        self.current_question = None
        self.quiz_data = []
        self.load_quiz_data()
        self.partner_answers = {} # Store answers from both parnters

    def load_quiz_data(self):
        """Load quiz data from CSV file."""
        try:
            self.quiz_df = pd.read_csv(QUIZ_FILE)
        except Exception as e:
            logger.error(f"Error loading quiz data: {str(e)}")
            self.quiz_df = pd.DataFrame()

    def get_question(self):
        """Extract a quiz record <randomly>."""
        if self.quiz_df.empty:
            return None
        return self.quiz_df.sample(n=1).iloc[0].to_dict()
    
    async def start_quest(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Start the quiz from the group chat.
        """
        
        # Check if command is from the authorized group chat
        if str(update.effective_chat.id) != TELEGRAM_GROUP_CHAT_ID:
            await update.message.reply_text("This command can only be used in our main group chat! 💕")
            return
        
        # Check if there's quiz question
        self.current_question = self.get_question()
        if not self.current_question:
            await update.message.reply_text("Quiz data is unavailable!")
            return
        
        # Clear previous answers
        self.partner_answers = {}
        
        # Send question to both partner via their private chats
        q = self.current_question
        message = (
            f"<b>Question #{q['Question_no']}:</b> {q['Question_text']}\n\n"
            f"1️⃣ {q['Option1']}\n"
            f"2️⃣ {q['Option2']}\n"
            f"3️⃣ {q['Option3']}\n"
            f"4️⃣ {q['Option4']}\n\n"
            "Reply with the number of your answer (1-4)."
        )
        for chat_id in TELEGRAM_PRIVATE_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                logger.info(f"Success to send question to private chat: {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send message to {chat_id}: {e:str}")
                update.message.reply_text("Failed to send message to {chat_id}: {e:str}")

        await update.message.reply_text("Question has been sent to both of your private chats! 💌")
    
    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle answers from private chats.
        """

        chat_id = str(update.effective_chat.id)
        user_first_name = str(update.effective_chat.first_name)
        partner_id = f"{chat_id}-{user_first_name}"

        # Ignore if not a private or not expecting answers
        if chat_id not in TELEGRAM_PRIVATE_CHAT_IDS:
            return

        user_answer = update.message.text
        logger.info(f"Received answer from chat_id: {chat_id}")
        logger.info(f"Message content: {user_answer}")

        self.partner_answers[partner_id] = user_answer
        await update.message.reply_text("Thank for your answer! 💝")
        no_answers = len(self.partner_answers)
        logger.info(f"[{no_answers}] answer[s] has been received: {self.partner_answers}")

        # Check if both partners have answered
        if no_answers == 2:
            # Get both answer
            answers = list(self.partner_answers.values())
            partners = list(self.partner_answers.keys())

            # Evalutate answers
            _, feedback = evaluate_answer(answers[0], answers[1], partners[0], partners[1])

            # Send result to group chat
            await context.bot.send_message(
                chat_id=TELEGRAM_GROUP_CHAT_ID,
                text=feedback,
                parse_mode="HTML"
            )
            logger.info(f"The result has been feedbacked to the group chat")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for canceling the quest."""
        chat_id = str(update.effective_chat.id)
        if chat_id != TELEGRAM_GROUP_CHAT_ID:
            await update.message.reply_text("This command can only be used in the group chat.")
            return

        await update.message.reply_text("Quiz cancelled. Goodbye!")


def main():
    """Run the Love Quest by Telegram bot."""
    love_quest = LoveQuest()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handler for starting the quest in the group chat
    app.add_handler(
        CommandHandler(
            "love_quest", 
            love_quest.start_quest
            # filters=filters.Chat(TELEGRAM_GROUP_CHAT_ID)
        )
    )

    # Handler for answers in private chats
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            love_quest.answer_handler
        )
    )

    app.add_handler(CommandHandler("cancel", love_quest.cancel))

    logger.info("Starting Love Quest ...")
    app.run_polling(poll_interval=5)


if __name__ == "__main__":
    main()


        
    