import asyncio
import json
import os
import random
import re
import shutil
import tempfile
from datetime import time as dtime
from pathlib import Path

import pytz
import yt_dlp
from hijri_converter import Gregorian
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    MenuButtonCommands,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

MAINTENANCE_MESSAGE = (
    "🛠️ البوت تحت الصيانة الآن لإضافة مزيد من المميزات "
    "الخاصة بنظام الطيبات.\n"
    "جرّب مرة أخرى لاحقًا ❤️🥰"
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TOKEN")

TIMEZONE = pytz.timezone("Africa/Cairo")
SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"
USERS_FILE = Path(__file__).parent / "users.json"

REQUIRED_CHANNELS = [
    {
        "username": "@diaa_alawady_videos",
        "url": "https://t.me/diaa_alawady_videos",
        "title": "قناة د. ضياء العوضي",
    },
    {
        "username": "@nezamaltaybat",
        "url": "https://t.me/nezamaltaybat",
        "title": "قناة نظام الطيبات",
    },
]

MENU_FB_DOWNLOAD = "📥 تحميل فيديو فيسبوك (مجاني)"
MENU_ALLOWED = "✅ المسموحات"
MENU_FORBIDDEN = "❌ الممنوعات"
MENU_RULES = "📜 القواعد العامة"
MENU_MEALS = "🍽️ اقتراح وجبات اليوم"
MENU_TOAST = "🍞 وصفة توست الشعير"
MENU_ABOUT = "👤 من هو د. ضياء العوضي؟"
MENU_REMINDERS_ON = "🔔 تفعيل تذكير الصيام"
MENU_REMINDERS_OFF = "🔕 إيقاف تذكير الصيام"

KEYBOARD = [
    [MENU_FB_DOWNLOAD],
    [MENU_ALLOWED, MENU_FORBIDDEN],
    [MENU_RULES, MENU_MEALS],
    [MENU_TOAST],
    [MENU_ABOUT],
    [MENU_REMINDERS_ON, MENU_REMINDERS_OFF],
]

FB_DOWNLOAD_INFO = (
    "📥 تحميل فيديوهات فيسبوك مجانًا\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "تقدر تحمّل أي فيديو من فيسبوك بكل سهولة 🎬\n\n"
    "📝 طريقة الاستخدام:\n\n"
    "1️⃣ افتح الفيديو في تطبيق فيسبوك\n"
    "2️⃣ اضغط على زر «مشاركة» (Share)\n"
    "3️⃣ اختر «نسخ الرابط» (Copy Link)\n"
    "4️⃣ ارجع للبوت وألصق الرابط هنا 👇\n"
    "5️⃣ استنى ثواني والفيديو هيوصلك تلقائيًا ✅\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "⚠️ ملاحظات هامة:\n"
    "• الفيديو لازم يكون عام (Public)\n"
    "• الحد الأقصى للحجم 50 ميجا\n"
    "• التحميل قد يستغرق دقيقة حسب حجم الفيديو\n\n"
    "ابعث الرابط الآن وجرّب 🚀"
)

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

TOAST_RECIPE = (
    "🍞 وصفة توست الشعير كامل الحبة\n"
    "وفق نظام الطيبات للدكتور ضياء العوضي\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "🌾 المقادير:\n\n"
    "• 3 أكواب دقيق شعير كامل الحبة (مع النخالة)\n"
    "• كوب ونصف ماء دافئ\n"
    "• ملعقة كبيرة خميرة فورية\n"
    "• ملعقة صغيرة ملح\n"
    "• ملعقة صغيرة عسل أبيض طبيعي\n"
    "• 3 ملاعق كبيرة زيت زيتون\n"
    "• ملعقة كبيرة سمسم (اختياري للوش)\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "👩‍🍳 طريقة التحضير:\n\n"
    "1️⃣ في كوب الماء الدافئ، ذوّب الخميرة مع العسل،\n"
    "   اتركها 10 دقائق حتى تتفاعل وتظهر فقاعات.\n\n"
    "2️⃣ في وعاء كبير، ضع الدقيق والملح وقلّبهم جيدًا.\n\n"
    "3️⃣ أضف زيت الزيتون ثم خليط الخميرة المذابة.\n\n"
    "4️⃣ اعجن الخليط جيدًا لمدة 10 دقائق حتى تحصل على\n"
    "   عجينة طريّة متماسكة لا تلتصق باليد\n"
    "   (لو لزجة أضف قليل من الدقيق).\n\n"
    "5️⃣ غطّي العجينة بقطعة قماش نظيفة واتركها في\n"
    "   مكان دافئ لمدة ساعة حتى يتضاعف حجمها.\n\n"
    "6️⃣ ادهن صينية التوست بقليل من زيت الزيتون،\n"
    "   ثم افرد العجينة فيها وسوّيها بيدك.\n\n"
    "7️⃣ ادهن الوجه بزيت الزيتون ورش السمسم.\n"
    "   اتركها ترتاح 20 دقيقة أخرى.\n\n"
    "8️⃣ سخّن الفرن على 180°م، واخبزي 25-30 دقيقة\n"
    "   حتى تصبح ذهبية اللون من الأعلى والأسفل.\n\n"
    "9️⃣ اتركها تبرد تمامًا، ثم قطّعها لشرائح بالحجم\n"
    "   المناسب وضعها في المحمصة (التوستر) عند\n"
    "   الاستخدام لتصبح مقرمشة.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "💡 نصائح للحفظ:\n\n"
    "• تحفظ في كيس محكم في الثلاجة لأسبوع\n"
    "• يمكن تجميدها لمدة شهر، تخرج عند الحاجة\n"
    "  وتُحمّص مباشرة\n"
    "• قسّمها لشرائح قبل التجميد لسهولة الاستخدام\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "🌿 يمكن تقديمها مع:\n"
    "- العسل والسمن البلدي\n"
    "- الحلاوة الطحينية الغامقة\n"
    "- الجبن المطبوخ والزيتون\n"
    "- زيت الزيتون والمربى\n\n"
    "بالهنا والشفاء 🤍"
)


MEAL_PLANS = [
    (
        "🍽️ اقتراح وجبات اليوم - خطة 1\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالعسل وزيت الزيتون\n"
        "- 5 تمرات\n"
        "- كوب شاي أخضر\n\n"
        "🌞 الغداء:\n"
        "- أرز أبيض\n"
        "- لحم ضأن مسلوق (كمية متوسطة)\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- توست نخالة بالجبن المطبوخ والزيتون\n"
        "- موزة\n"
        "- مشروب أعشاب دافئ"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 2\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالحلاوة الطحينية الغامقة\n"
        "- 7 تمرات مع حبات عنب\n"
        "- كوب قهوة تركي\n\n"
        "🌞 الغداء:\n"
        "- بطاطس مشوية في الفرن\n"
        "- كبدة بقري مسلوقة بزيت الزيتون\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- توست نخالة بالعسل والسمن البلدي\n"
        "- جوافة بدون بذر\n"
        "- شاي أخضر"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 3\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالموتزاريلا والزيتون\n"
        "- تين طازج أو مجفف\n"
        "- كوب شاي أخضر\n\n"
        "🌞 الغداء:\n"
        "- أرز أبيض\n"
        "- حمام مشوي أو مسلوق\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- بطاطس مسلوقة بزيت الزيتون والملح\n"
        "- 5 تمرات\n"
        "- مشروب أعشاب"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 4\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالنوتيلا (كمية صغيرة)\n"
        "- موزة + 5 تمرات\n"
        "- قهوة تركي\n\n"
        "🌞 الغداء:\n"
        "- أرز أبيض\n"
        "- لحم بقري مفروم مسلوق\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- توست نخالة بالجبنة الشيدر والزيتون\n"
        "- رمان بدون بذر أو فراولة\n"
        "- شاي أخضر"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 5\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالمربى وزيت الزيتون\n"
        "- 7 تمرات\n"
        "- مشروب أعشاب دافئ\n\n"
        "🌞 الغداء:\n"
        "- بطاطس مشوية\n"
        "- لحم ضأن مهروس مسلوق\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- أرز بحليب جوز الهند (إن أمكن) أو أرز ساده\n"
        "- مشمش أو برقوق (بخارة)\n"
        "- قهوة تركي"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 6\n"
        "وفق نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- 9 تمرات مع زيتون\n"
        "- توست نخالة بالسمن البلدي والعسل\n"
        "- شاي أخضر\n\n"
        "🌞 الغداء:\n"
        "- أرز أبيض\n"
        "- أرانب مشوية أو مسلوقة\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- توست نخالة بالجبن الجودة\n"
        "- عنب أو فراولة\n"
        "- مشروب أعشاب"
    ),
    (
        "🍽️ اقتراح وجبات اليوم - خطة 7\n"
        "وفق نظام الطيبات (يوم السمك الشهري)\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "🌅 الفطور:\n"
        "- توست نخالة بالحلاوة الطحينية\n"
        "- 5 تمرات\n"
        "- قهوة تركي\n\n"
        "🌞 الغداء:\n"
        "- أرز أبيض\n"
        "- سمك مشوي بزيت الزيتون (مرة في الشهر)\n"
        "- ماء عند العطش\n\n"
        "🌙 العشاء:\n"
        "- بطاطس مسلوقة بالسمن البلدي\n"
        "- موزة + تين\n"
        "- شاي أخضر"
    ),
]

MEALS_NOTE = (
    "\n\nـــــــــــــــــــــــــــــــــ\n"
    "📌 ملاحظات هامة:\n"
    "- كُل عند الجوع فقط، لا تصل للشبع\n"
    "- اشرب الماء فقط عند العطش\n"
    "- اللحوم: مرتين أسبوعيًا، السمك: مرة شهريًا\n"
    "- اضغط الزر مرة أخرى لاقتراح وجبات مختلفة 🔄"
)


ABOUT_TEXT_PART1 = (
    "👤 من هو د. ضياء العوضي؟\n"
    "ـــــــــــــــــــــــــــــــــ\n\n"
    "د. ضياء الدين العوضي ❤️\n\n"
    "إن الناظر المتدبر إلى حياة هذا الرجل يرى أنه قد تم تهيئته "
    "للسبب الذي عاش عليه ومات من أجله.\n\n"
    "في السطور التالية بعض التدبرات في سماته الشخصية ومسيرته العلمية، "
    "مستندًا إلى ما حكاه بنفسه وما حكاه عنه المقربون، وخصوصًا في الأيام "
    "الأخيرة قبل وفاته رحمه الله:\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "🔬 أولًا: السمات العلمية\n\n"
    "1. اتسم بنبوغ علمي لافت منذ صغره، واستمر تفوقه حتى تخرجه من الجامعة.\n\n"
    "2. بلغ مكانة علمية رفيعة جعلته أستاذًا في مجاله ومعلمًا للأطباء "
    "وأبنائهم وطلابهم؛ فلا يستطيع أحد أن يشكك فيه أو يتهمه بالجهل، "
    "ولم يكن طبيبًا تقليديًا محدود الأثر.\n\n"
    "3. تحرر من القيود الاجتماعية والعائلية التي قد تُعيق التفكير الحر، "
    "وكان ناقدًا لأخطاء من حوله.\n\n"
    "4. امتلك عقلًا تحليليًا متسائلًا، خاصة خلال دراسته الطبية، فلم يكتفِ "
    "بتلقي المعلومة بل بحث في أسباب المرض ومنطق العلاج.\n\n"
    "5. ربط بين الماضي والحاضر؛ كيف كان تأثير الغذاء على الإنسان قديمًا "
    "وحديثًا، وما الأمراض التي استجدت ومسبباتها الحقيقية وعلاقتها "
    "بالعادات الغذائية.\n\n"
    "6. تخصصه في الرعاية المركزة صقل تلك العوامل، فهو من التخصصات النادرة "
    "التي يتسنى فيها للطبيب اتخاذ الإجراء ومتابعته وقياس أثره مباشرة.\n\n"
    "7. أتيح له الوقت الكافي للمطالعة والتدبر والتجريب، مع خلفية علمية راسخة "
    "بأجهزة الجسم.\n\n"
    "8. كان متفرغًا عاشقًا للطب، ولم يكن مهنة فقط بالنسبة له.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "💎 ثانيًا: السمات الشخصية\n\n"
    "1. كان متحررًا من الانقياد للمجتمع.\n\n"
    "2. وفّر لنفسه استقلالًا ماليًا مكّنه من اتخاذ مواقفه دون خوف، ونشر "
    "أفكاره علنًا، ومواجهة التحديات بلا تردد.\n\n"
    "3. كان يرى أن الاستقلال المادي من أهم عوامل التحرر من الضغوط.\n\n"
    "4. كان مؤمنًا بالله تمام الإيمان، يشع الإيمان في كلماته، ويعكس فهمًا "
    "حقيقيًا لمراد الله من الخلق.\n\n"
    "5. قوة شخصية في مواجهة التحديات، له حدة شديدة ضد المشككين والجهلة "
    "والمنتفعين.\n\n"
    "6. هذه الحدة جعلته لا يسلك مسلكًا علميًا بحتًا تنتهي أبحاثه في "
    "غيابات الأدراج.\n\n"
    "7. مع حدته يحمل قلبًا طاهرًا بريئًا، كالأب الذي يريد حماية أطفاله "
    "من الضرر."
)

ABOUT_TEXT_PART2 = (
    "🧪 ثالثًا: الجانب العلمي التطبيقي\n\n"
    "1. وضع تصورًا علميًا للقضاء على مسببات الأمراض عن طريق الامتناع عن "
    "الغذاء الملوث بالمبيدات والهندسة الجينية والهرمونات.\n\n"
    "2. ركّز على شفاء المرضى بعيدًا عن البروتوكولات المعتادة، وله نتائج "
    "شفاء بالآلاف.\n\n"
    "3. أنكر نظرية المرض المزمن وأثبت أن لكل مرض سببًا ودواء، وذلك في "
    "تجارب المرضى وشهادات الأطباء العاملين بنظامه.\n\n"
    "4. حاول جمع الأطباء وإقناعهم باستخدام نظريته العلاجية، فمنهم من تشكك "
    "ومنهم من استجاب علنًا أو سرًا، ومنهم من أعرض.\n\n"
    "5. من أبرز التحديات: عدم وجود فريق علمي كافٍ لتوثيق تجاربه منهجيًا.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "🌍 رابعًا: أثره العام\n\n"
    "1. صدع بالحق وأعلم الناس أن هناك أملًا في الشفاء لا ينتهي بإعلان "
    "الطبيب أنك مصاب بمرض مزمن.\n\n"
    "2. بصّر العامة بمسممات تمارس عليهم في صناعات الدواء والطعام.\n\n"
    "3. أقام الحجة على أطباء الطب الحديث ووضع لهم طريقًا للعذر أمام الله.\n\n"
    "4. حرر مرضى استعبدتهم أكياس الأدوية، وعلّمهم أن المرض ناتج عما وضعوه "
    "في أفواههم.\n\n"
    "5. له محاضرات يشرح فيها ميكانيزمات الالتهاب والحساسية وانسداد الأمعاء "
    "وتكاثر الخلايا، تحتاج لدراسة جادة.\n\n"
    "6. شرح الأعراض التي قيل إنها أمراض، وفسّرها كميكانيزمات دفاعية يتخذها "
    "الجسم للحماية.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "⚔️ خامسًا: التحديات والانتقادات\n\n"
    "كان يواجه أمرًا جللًا يصعب على شخص مجابهته وحده:\n\n"
    "• منظومة منتجي الغذاء البروتيني والصناعات المرتبطة\n"
    "• منظومة منتجي الألبان وسلاسل الإمداد\n"
    "• منظومة الزراعات والصناعات المرتبطة\n"
    "• منظومة الصناعات الدوائية\n"
    "• مجموعات من المتنمرين والساخرين\n\n"
    "والأخطر: مواجهة الأطباء أنفسهم، الذين خلقوا جانبًا دفاعيًا للإنكار، "
    "كل واحد منهم يخرج للإعلام لينفي أبحاث الدكتور.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "💡 كيف تتفاعل مع دعوته؟\n\n"
    "جرّب بنفسك نظامه؛ فإن استفدت منه فقد ربحت، وإن لم تستفد فلن يضرك، "
    "فما هو إلا امتناع عن بعض عاداتك الغذائية.\n\n"
    "ـــــــــــــــــــــــــــــــــ\n"
    "🤍 رحم الله عبده ضياء العوضي وأسكنه فسيح جناته\n\n"
    "#ضياء_العوضي #نظام_الطيبات"
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


def load_users() -> set[int]:
    if not USERS_FILE.exists():
        return set()
    try:
        return set(json.loads(USERS_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_users(users: set[int]) -> None:
    USERS_FILE.write_text(json.dumps(sorted(users)), encoding="utf-8")


def track_user(user_id: int) -> None:
    """Add user to the tracked users set if not already present."""
    if not user_id:
        return
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)


async def is_channel_member(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, channel_username: str
) -> bool:
    """Check whether the user is a member of a specific channel."""
    try:
        member = await context.bot.get_chat_member(
            chat_id=channel_username, user_id=user_id
        )
        return member.status in ("creator", "administrator", "member", "owner")
    except Exception as e:
        print(
            f"Membership check failed for {user_id} on {channel_username}: {e}",
            flush=True,
        )
        return False


async def get_missing_channels(
    context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> list[dict]:
    """Return the list of required channels the user has NOT joined."""
    missing = []
    for ch in REQUIRED_CHANNELS:
        if not await is_channel_member(context, user_id, ch["username"]):
            missing.append(ch)
    return missing


def subscription_required_markup() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"📢 {ch['title']}", url=ch["url"])]
        for ch in REQUIRED_CHANNELS
    ]
    rows.append(
        [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")]
    )
    return InlineKeyboardMarkup(rows)


SUBSCRIPTION_PROMPT = (
    "🔒 لاستخدام البوت يجب الاشتراك أولًا في القنوات التالية:\n\n"
    + "\n".join(f"• {ch['title']}\n   {ch['url']}" for ch in REQUIRED_CHANNELS)
    + "\n\nبعد الاشتراك في كل القنوات اضغط «تحققت من الاشتراك» 👇"
)


async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if user is subscribed to all channels; else prompt and return False."""
    user_id = update.effective_user.id
    missing = await get_missing_channels(context, user_id)
    if not missing:
        return True
    await update.message.reply_text(
        SUBSCRIPTION_PROMPT,
        reply_markup=subscription_required_markup(),
        disable_web_page_preview=True,
    )
    return False


def get_admin_ids() -> set[int]:
    """Read admin Telegram user IDs from ADMIN_USER_ID env var (comma-separated)."""
    raw = os.environ.get("ADMIN_USER_ID", "").strip()
    if not raw:
        return set()
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        track_user(user.id)
    admin_ids = get_admin_ids()
    if not user or user.id not in admin_ids:
        # Silently ignore for non-admins (don't reveal the command exists).
        return
    total_users = len(load_users())
    reminder_subs = len(load_subscribers())
    text = (
        "📊 إحصائيات البوت\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        f"👥 إجمالي المستخدمين: {total_users}\n"
        f"🔔 المشتركون في تذكير الصيام: {reminder_subs}\n"
    )
    await update.message.reply_text(text)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    await update.message.reply_text(
        f"🆔 رقم تليجرام بتاعك:\n<code>{user.id}</code>",
        parse_mode="HTML",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if user:
        track_user(user.id)
    if not await require_subscription(update, context):
        return
    add_subscriber(chat_id)
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "🌿 أهلاً بك في بوت د. ضياء العوضي\n"
        "نظام الطيبات\n"
        "ـــــــــــــــــــــــــــــــــ\n\n"
        "📖 من خلال هذا البوت يمكنك:\n\n"
        "✅ معرفة الأطعمة المسموحة\n"
        "❌ معرفة الأطعمة الممنوعة\n"
        "📜 الاطلاع على القواعد العامة للنظام\n"
        "🍽️ اقتراح ٣ وجبات يومية وفق النظام\n"
        "🍞 وصفة عمل توست الشعير كامل الحبة\n"
        "👤 التعرف على د. ضياء العوضي\n"
        "🔔 تفعيل/إيقاف تذكيرات الصيام\n"
        "    (الاثنين والخميس + الأيام البيض 13/14/15 هجريًا)\n"
        "📥 تحميل أي فيديو من فيسبوك\n"
        "    (ابعث الرابط فقط وسيتم التحميل تلقائيًا)\n\n"
        "ـــــــــــــــــــــــــــــــــ\n"
        "📱 طريقة الاستخدام:\n"
        "اضغط على أي زر من الأزرار الموجودة بالأسفل ⬇️\n"
        "ولو الأزرار مش ظاهرة، اضغط على أيقونة ⌨️ بجانب خانة الكتابة.\n\n"
        "🔔 ملاحظة: تذكيرات الصيام مفعّلة تلقائيًا،\n"
        "وتُرسل الساعة 8 مساءً بتوقيت القاهرة قبل يوم الصيام.\n\n"
        "بالتوفيق إن شاء الله 🤍",
        reply_markup=reply_markup,
    )


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'I've subscribed' inline button."""
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    missing = await get_missing_channels(context, user_id)
    if not missing:
        await query.answer("✅ تم التحقق، أهلًا بك!")
        try:
            await query.edit_message_text("✅ تم التحقق من اشتراكك. تفضّل بالقائمة 👇")
        except Exception:
            pass
        add_subscriber(chat_id)
        reply_markup = ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="اختر من القائمة:",
            reply_markup=reply_markup,
        )
    else:
        names = "، ".join(ch["title"] for ch in missing)
        await query.answer(
            f"لم تشترك بعد في: {names}. اشترك ثم حاول مرة أخرى.",
            show_alert=True,
        )


FACEBOOK_URL_PATTERN = re.compile(
    r"(https?://(?:www\.|m\.|web\.|mbasic\.)?"
    r"(?:facebook\.com|fb\.watch|fb\.com)/\S+)",
    re.IGNORECASE,
)

# Telegram bot API limit for sending video files is 50 MB
TELEGRAM_VIDEO_SIZE_LIMIT = 50 * 1024 * 1024


def _ytdl_download(url: str, out_dir: str) -> tuple[str, dict]:
    """Run yt-dlp synchronously and return (file_path, info)."""
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "format": "best[ext=mp4][filesize<50M]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
    return file_path, info


async def handle_facebook_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    chat_id = update.effective_chat.id
    status = await update.message.reply_text(
        "⏳ جاري تحميل الفيديو من فيسبوك، انتظر لحظات..."
    )

    tmp_dir = tempfile.mkdtemp(prefix="fbvideo_")
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        loop = asyncio.get_running_loop()
        file_path, info = await loop.run_in_executor(
            None, _ytdl_download, url, tmp_dir
        )

        if not file_path or not os.path.exists(file_path):
            await status.edit_text(
                "⚠️ لم أتمكن من تحميل الفيديو. تأكد أن الرابط عام (Public)."
            )
            return

        size = os.path.getsize(file_path)
        title = (info.get("title") or "").strip()
        caption = title[:200] if title else None

        if size > TELEGRAM_VIDEO_SIZE_LIMIT:
            mb = size / (1024 * 1024)
            await status.edit_text(
                f"⚠️ حجم الفيديو {mb:.1f} ميجا، أكبر من الحد المسموح في تيليجرام (50 ميجا).\n"
                "جرّب فيديو أقصر."
            )
            return

        await status.edit_text("📤 جاري إرسال الفيديو...")
        with open(file_path, "rb") as f:
            await context.bot.send_video(
                chat_id=chat_id,
                video=f,
                caption=caption,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=300,
            )
        await status.delete()
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        print(f"yt-dlp DownloadError for {url}: {msg}", flush=True)
        await status.edit_text(
            "⚠️ فشل تحميل الفيديو. تأكد أن الرابط صحيح، وأن الفيديو عام وليس خاصًا."
        )
    except Exception as e:
        print(f"Facebook download failed for {url}: {e}", flush=True)
        await status.edit_text(
            "⚠️ حدث خطأ أثناء تحميل الفيديو. حاول مرة أخرى لاحقًا."
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id
    user = update.effective_user
    if user:
        track_user(user.id)

    if not await require_subscription(update, context):
        return

    fb_match = FACEBOOK_URL_PATTERN.search(text)
    if fb_match:
        await handle_facebook_url(update, context, fb_match.group(1))
        return

    if text == MENU_FB_DOWNLOAD:
        await update.message.reply_text(FB_DOWNLOAD_INFO)
        return

    if text == MENU_ALLOWED:
        await update.message.reply_text(ALLOWED_TEXT)
        return

    if text == MENU_FORBIDDEN:
        await update.message.reply_text(FORBIDDEN_TEXT)
        return

    if text == MENU_RULES:
        await update.message.reply_text(RULES_TEXT)
        return

    if text == MENU_MEALS:
        plan = random.choice(MEAL_PLANS)
        await update.message.reply_text(plan + MEALS_NOTE)
        return

    if text == MENU_TOAST:
        await update.message.reply_text(TOAST_RECIPE)
        return

    if text == MENU_ABOUT:
        await update.message.reply_text(ABOUT_TEXT_PART1)
        await update.message.reply_text(ABOUT_TEXT_PART2)
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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch all unhandled errors and notify the user politely."""
    print(f"Exception while handling an update: {context.error}", flush=True)

    chat_id = None
    if isinstance(update, Update):
        if update.effective_chat:
            chat_id = update.effective_chat.id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat_id

    if chat_id is None:
        return

    try:
        await context.bot.send_message(chat_id=chat_id, text=MAINTENANCE_MESSAGE)
    except Exception as e:
        print(f"Failed to send maintenance message to {chat_id}: {e}", flush=True)


async def post_init(app: Application) -> None:
    """Set up the bot's command menu so /start always shows in Telegram."""
    await app.bot.set_my_commands(
        [
            BotCommand("start", "ابدأ البوت / عرض القائمة الرئيسية"),
        ]
    )
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await app.bot.set_my_description(
        "بوت د. ضياء العوضي - نظام الطيبات\n"
        "اضغط /start للبدء وعرض القائمة."
    )
    await app.bot.set_my_short_description(
        "نظام الطيبات للدكتور ضياء العوضي - اضغط /start"
    )


def main():
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

    # Backfill: any existing reminder subscribers count as known users.
    existing_subs = load_subscribers()
    if existing_subs:
        users = load_users()
        before = len(users)
        users.update(existing_subs)
        if len(users) > before:
            save_users(users)

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))
    app.add_error_handler(error_handler)

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
