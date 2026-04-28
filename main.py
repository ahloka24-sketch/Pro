import json
import os
from datetime import time as dtime
from pathlib import Path

import pytz
from hijri_converter import Gregorian
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TOKEN")

TIMEZONE = pytz.timezone("Africa/Cairo")
SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"

MENU_ALLOWED = "✅ المسموحات"
MENU_FORBIDDEN = "❌ الممنوعات"
MENU_RULES = "📜 القواعد العامة"
MENU_REMINDERS_ON = "🔔 تفعيل تذكير الصيام"
MENU_REMINDERS_OFF = "🔕 إيقاف تذكير الصيام"

KEYBOARD = [
    [MENU_ALLOWED, MENU_FORBIDDEN],
    [MENU_RULES],
    [MENU_REMINDERS_ON, MENU_REMINDERS_OFF],
]

ALLOWED_TEXT = (
    "✅ المسموحات في نظام الطيبات\n"
    "للدكتور ضياء العوضي\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "🍞 الخبز:\n"
    "- خبز توست النخالة فقط\n\n"
    "🧀 الأجبان والألبان:\n"
    "- الجبن المطبوخ (شيدر، جودة، فلمنك)\n"
    "- موتزاريلا\n"
    "- سمن بلدي\n"
    "- حلاوة طحينية غامقة\n\n"
    "🫒 إضافات:\n"
    "- زيتون\n"
    "- زبدة\n"
    "- مربى\n"
    "- نوتيلا\n"
    "- عسل\n"
    "- زيت زيتون\n\n"
    "🥔 النشويات:\n"
    "- البطاطس بجميع أشكالها (مطبوخة بأي طريقة)\n"
    "- الأرز بجميع أشكاله\n\n"
    "🥩 اللحوم:\n"
    "- لحم الضأن (خروف)\n"
    "- اللحم البقري\n"
    "- اللحم الجملي\n"
    "- الحمام\n"
    "- الأرانب\n"
    "- الكبدة\n"
    "- السمك (يفضل مرة في الشهر)\n\n"
    "🍇 الفواكه:\n"
    "- التمور والرطب (أفضل الفواكه)\n"
    "- العنب\n"
    "- الجوافة بدون بذر\n"
    "- الرمان بدون بذر\n"
    "- التين\n"
    "- الموز\n"
    "- الفراولة\n"
    "- المشمش\n"
    "- البخارة (البرقوق)\n\n"
    "🍵 المشروبات:\n"
    "- الشاي الأخضر\n"
    "- قهوة تركي (نوع موثوق)\n"
    "- مشروبات عشبية مفيدة\n"
    "- مياه"
)

FORBIDDEN_TEXT = (
    "❌ الممنوعات في نظام الطيبات\n"
    "للدكتور ضياء العوضي\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "🚫 الدقيق ومشتقاته:\n"
    "- جميع أنواع الدقيق الأبيض\n"
    "- المخبوزات (كرواسون، كيك، دونتس...)\n"
    "- المكرونة بكل أنواعها\n\n"
    "🚫 الألبان الطازجة ومشتقاتها:\n"
    "- الحليب الطازج\n"
    "- الجبنة القريش\n"
    "- الزبادي والرايب\n"
    "- جميع منتجات الألبان الطازجة\n\n"
    "🚫 البيض والدجاج:\n"
    "- البيض بجميع أنواعه\n"
    "- الدجاج وجميع الطيور (عدا الحمام)\n\n"
    "🚫 الأسماك الممنوعة:\n"
    "- الجمبري\n"
    "- الحبار (الكاليماري)\n"
    "- جميع الأسماك المخفوقة\n\n"
    "🚫 البقوليات (كاملة):\n"
    "- الفول\n"
    "- العدس\n"
    "- البسلة\n"
    "- اللوبيا\n"
    "- الحمص\n"
    "- الفاصوليا\n"
    "- الفول السوداني\n\n"
    "🚫 الخضروات الورقية والممنوعة:\n"
    "- جميع الخضروات الورقية (خس، سبانخ، جرجير...)\n"
    "- الكوسة، القرع\n"
    "- الخيار، الخس، البقدونس، الكرفس، الكرنب،\n"
    "  الفلفل الأخضر، الفلفل الأحمر، الفلفل الألوان،\n"
    "  الطماطم، الباذنجان، الفاصوليا البيضاء، اللوبيا، فول أخضر\n\n"
    "🚫 فواكه ممنوعة:\n"
    "- البطيخ\n"
    "- الشمام\n"
    "- جميع أنواع التين الشوكي\n\n"
    "🚫 المشروبات:\n"
    "- المشروبات الغازية\n"
    "- مشروبات الطاقة\n"
    "- العصائر (برتقال، مانجو، بطيخ...)\n"
    "- الشاي الأحمر\n\n"
    "🚫 أخرى:\n"
    "- الشوكولاتة المصنعة\n"
    "- الأدوية المعينة (مضادات الالتهاب،\n"
    "  الأسبرين، أدوية الكوليسترول، مضادات الاكتئاب)"
)

RULES_TEXT = (
    "📜 القواعد العامة لنظام الطيبات\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "🌙 الصيام:\n"
    "- صيام يومي الإثنين والخميس\n"
    "- صيام الأيام البيض (13، 14، 15) من الشهر القمري\n\n"
    "💧 الشرب:\n"
    "- اشرب الماء فقط عند العطش\n\n"
    "🍽️ الأكل:\n"
    "- كُل عند الجوع فقط\n"
    "- حدد كمية الطعام التي تستعمل أمامك\n"
    "  لتنتهي منها دون الوصول إلى الشبع\n\n"
    "🥩 البروتين:\n"
    "- لحوم: مرة واحدة أسبوعيًا (شرعي أو جاموسي)،\n"
    "  يُفضل لحم مهروس مسلوقة جدًا\n"
    "- مرتين أسبوعيًا (لحم أو ماعز أو حمل)\n"
    "- مسموح: لحم مفروم، كبدة، مخ\n"
    "- ويُفضل: كوارع، لحمة رأس، صياد، علاوي\n"
    "- الكميات: ليست كبيرة جدًا\n\n"
    "⚖️ تنظيم البروتين:\n"
    "- البروتين اللحوم: مرتين يوميًا\n"
    "- الدواجن (الحمام): مسموح\n"
    "- الأسماك: مرة في الشهر\n\n"
    "ℹ️ المخللات: الزيتون فقط مسموح\n\n"
    "⚠️ ملاحظات هامة:\n"
    "لا تأكل أي توست، بطيخ، شكلاتة، برتقال،\n"
    "يوسفي، مانجو، كيوي، كاكا، باباز، أفوكادو\n\n"
    "📌 تنويه: هذا النظام إرشادي ويحتاج\n"
    "لتقييم فردي واستشارة طبية مختصة."
)


def load_subscribers() -> set[int]:
    if not SUBSCRIBERS_FILE.exists():
        return set()
    try:
        return set(json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_subscribers(subs: set[int]) -> None:
    SUBSCRIBERS_FILE.write_text(json.dumps(sorted(subs)), encoding="utf-8")


def add_subscriber(chat_id: int) -> bool:
    subs = load_subscribers()
    if chat_id in subs:
        return False
    subs.add(chat_id)
    save_subscribers(subs)
    return True


def remove_subscriber(chat_id: int) -> bool:
    subs = load_subscribers()
    if chat_id not in subs:
        return False
    subs.discard(chat_id)
    save_subscribers(subs)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك في بوت د. ضياء العوضي 👋\n"
        "تم تفعيل تذكير صيام الاثنين والخميس والأيام البيض تلقائيًا.\n"
        "اختر من القائمة:",
        reply_markup=reply_markup,
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id

    if text == MENU_ALLOWED:
        await update.message.reply_text(ALLOWED_TEXT)
        return

    if text == MENU_FORBIDDEN:
        await update.message.reply_text(FORBIDDEN_TEXT)
        return

    if text == MENU_RULES:
        await update.message.reply_text(RULES_TEXT)
        return

    if text == MENU_REMINDERS_ON:
        added = add_subscriber(chat_id)
        if added:
            await update.message.reply_text(
                "✅ تم تفعيل تذكير صيام الاثنين والخميس والأيام البيض."
            )
        else:
            await update.message.reply_text(
                "🔔 التذكيرات مفعّلة لديك بالفعل."
            )
        return

    if text == MENU_REMINDERS_OFF:
        removed = remove_subscriber(chat_id)
        if removed:
            await update.message.reply_text("🔕 تم إيقاف تذكيرات الصيام.")
        else:
            await update.message.reply_text("التذكيرات غير مفعّلة لديك.")
        return


def build_reminder_message(now_local) -> str | None:
    """Return the reminder text to send tonight, or None if nothing to send.

    Sent in the evening for the *next* day's fast.
    """
    from datetime import timedelta

    weekday = now_local.weekday()  # Monday=0 .. Sunday=6
    tomorrow_date = (now_local + timedelta(days=1)).date()
    hijri_tomorrow = Gregorian(
        tomorrow_date.year, tomorrow_date.month, tomorrow_date.day
    ).to_hijri()

    parts: list[str] = []

    # Tomorrow weekday: Monday=0, Thursday=3
    tomorrow_weekday = (weekday + 1) % 7
    if tomorrow_weekday == 0:
        parts.append(
            "🌙 تذكير: غدًا الإثنين، يُستحب صيامه.\n"
            "قال ﷺ: (تُعرض الأعمال يوم الإثنين والخميس فأحب أن يُعرض عملي وأنا صائم)."
        )
    elif tomorrow_weekday == 3:
        parts.append(
            "🌙 تذكير: غدًا الخميس، يُستحب صيامه.\n"
            "قال ﷺ: (تُعرض الأعمال يوم الإثنين والخميس فأحب أن يُعرض عملي وأنا صائم)."
        )

    # White days (Ayyam al-Beed): 13, 14, 15 of Hijri month
    if hijri_tomorrow.day in (13, 14, 15):
        parts.append(
            f"🤍 تذكير: غدًا {hijri_tomorrow.day} {hijri_tomorrow.month_name('ar')} "
            f"{hijri_tomorrow.year}هـ، من الأيام البيض.\n"
            "قال ﷺ: (صيام ثلاثة أيام من كل شهر صيام الدهر، أيام البيض: ثلاث عشرة، "
            "وأربع عشرة، وخمس عشرة)."
        )

    if not parts:
        return None
    return "\n\n".join(parts)


async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    from datetime import datetime
    now_local = datetime.now(TIMEZONE)
    message = build_reminder_message(now_local)
    if not message:
        return
    subs = load_subscribers()
    for chat_id in list(subs):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}", flush=True)


def main():
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))

    # Schedule a daily check at 8:00 PM Cairo time.
    app.job_queue.run_daily(
        send_daily_reminders,
        time=dtime(hour=20, minute=0, tzinfo=TIMEZONE),
        name="daily_fasting_reminder",
    )

    print("Bot is running...", flush=True)
    app.run_polling()


if __name__ == "__main__":
    main()
