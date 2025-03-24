import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, filters

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            positive_votes INTEGER DEFAULT 0,
            negative_votes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_fact(text: str):
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO facts (text) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def get_random_fact():
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, text FROM facts ORDER BY RANDOM() LIMIT 1")
    fact = cursor.fetchone()
    conn.close()
    return fact if fact else (None, "Фактов пока нет. Добавьте свой первым!")

def search_fact(keyword: str):
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, text FROM facts WHERE text LIKE ?", (f"%{keyword}%",))
    facts = cursor.fetchall()
    conn.close()
    return facts if facts else [(None, "Совпадений не найдено.")]

def vote_fact(fact_id: int, vote_type: str):
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    if vote_type == "up":
        cursor.execute("UPDATE facts SET positive_votes = positive_votes + 1 WHERE id = ?", (fact_id,))
    elif vote_type == "down":
        cursor.execute("UPDATE facts SET negative_votes = negative_votes + 1 WHERE id = ?", (fact_id,))
    conn.commit()
    conn.close()

def get_sorted_facts(order_by: str):
    conn = sqlite3.connect("dream_facts.db")
    cursor = conn.cursor()
    if order_by == "positive":
        cursor.execute("SELECT text FROM facts ORDER BY positive_votes DESC")
    elif order_by == "negative":
        cursor.execute("SELECT text FROM facts ORDER BY negative_votes DESC")
    else:
        cursor.execute("SELECT text FROM facts ORDER BY created_at DESC")
    facts = cursor.fetchall()
    conn.close()
    return [fact[0] for fact in facts] if facts else ["Фактов пока нет."]

# Команды бота
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Привет! Я бот с интересными фактами. Напиши /fact, чтобы получить случайный факт!")

async def fact(update: Update, context: CallbackContext) -> None:
    fact_id, text = get_random_fact()
    await update.message.reply_text(f"{text}\nЧтобы оценить: /up {fact_id} или /down {fact_id}")

async def add(update: Update, context: CallbackContext) -> None:
    text = " ".join(context.args)
    if text:
        add_fact(text)
        await update.message.reply_text("Факт добавлен! Спасибо!")
    else:
        await update.message.reply_text("Использование: /add <факт>")

async def search(update: Update, context: CallbackContext) -> None:
    keyword = " ".join(context.args)
    if keyword:
        facts = search_fact(keyword)
        await update.message.reply_text("\n".join([fact[1] for fact in facts]))
    else:
        await update.message.reply_text("Использование: /search <ключевое слово>")

async def vote(update: Update, context: CallbackContext) -> None:
    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Использование: /up <id> или /down <id>")
        return
    fact_id = int(args[0])
    command = update.message.text.split()[0][1:]
    vote_type = "up" if command == "up" else "down"
    vote_fact(fact_id, vote_type)
    await update.message.reply_text("Ваш голос учтён!")

async def sorted_facts(update: Update, context: CallbackContext) -> None:
    args = context.args
    if not args or args[0] not in ["positive", "negative", "recent"]:
        await update.message.reply_text("Использование: /sort positive|negative|recent")
        return
    facts = get_sorted_facts(args[0])
    await update.message.reply_text("\n".join(facts[:5]))

def main():
    init_db()
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fact", fact))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("up", vote))
    application.add_handler(CommandHandler("down", vote))
    application.add_handler(CommandHandler("sort", sorted_facts))
    
    application.run_polling()

if __name__ == "__main__":
    main()
