"""
Lightweight, dependency-free i18n layer.

We deliberately don't use Django's gettext-based translation framework
here: it needs the `gettext` system binary (msgfmt) to compile .po -> .mo
files, which isn't reliably available on Render's free Python runtime or
guaranteed on a dev machine. Plain Python dictionaries work identically
everywhere and need no build step.

The active language is stored in the session (see core.views.set_language)
and exposed to every template via core.context_processors.language as `t`
(the string table for the active language) and `LANG` (its code).
"""

LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
    ("uz", "Oʻzbekcha"),
    ("kaa", "Qaraqalpaqsha"),
]
LANGUAGE_CODES = [code for code, _ in LANGUAGES]
DEFAULT_LANGUAGE = "en"

# Full language names used inside the OpenRouter prompt so the model knows
# what to write the quiz content in.
AI_LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "uz": "Uzbek",
    "kaa": "Karakalpak (Qaraqalpaq)",
}

TRANSLATIONS = {
    "en": {
        "nav_new_test": "New Test",
        "nav_history": "History",
        "nav_logout": "Logout",
        "nav_login": "Login",
        "nav_get_started": "Get Started",

        "landing_title": "Tests that actually feel alive.",
        "landing_sub": "Pick a subject, tell the AI how many questions you want, and solve them your way — drag, match, slide, and type your way through instead of clicking the same four boxes.",
        "landing_cta_start": "Start a Test",
        "landing_cta_register": "Create Free Account",
        "landing_cta_login": "I already have one",
        "badge_matching": "🔗 Drag & Drop Matching",
        "badge_ordering": "🔢 Sequence Ordering",
        "badge_numeric": "🎚️ Numeric Sliders",
        "badge_code": "💻 Code Completion",
        "badge_multiselect": "🧩 Multi-Select",
        "badge_fillblank": "✏️ Fill in the Blank",

        "register_heading": "Create your account",
        "label_username": "Username",
        "label_email": "Email (optional)",
        "label_password": "Password",
        "label_password_confirm": "Confirm password",
        "btn_create_account": "Create Account",
        "already_have_account": "Already have an account?",
        "login_link": "Log in",

        "login_heading": "Welcome back",
        "btn_login": "Log In",
        "new_here": "New here?",
        "register_link": "Create an account",

        "history_heading": "Your history",
        "history_empty": "No completed tests yet.",
        "history_start_first": "Start your first test",
        "history_questions_suffix": "questions",

        "setup_heading": "Build your test",
        "setup_lead": "Choose a subject, how many questions you want, and which interactive formats the AI should use.",
        "setup_section_subject": "1. Subject",
        "setup_section_count": "2. How many questions?",
        "setup_section_types": "3. Interactive formats — pick at least 2 (no boring multiple choice here)",
        "setup_submit": "Generate My Test →",
        "setup_alert_min_types": "Pick at least 2 interactive formats.",
        "setup_starting": "Starting…",

        "generating_headline": "Conjuring your questions…",
        "generating_starting": "Starting up…",
        "generating_progress": "{generated} / {target} questions ready",
        "generating_done": "Done! Loading your test…",
        "generating_failed_headline": "Generation failed",
        "generating_failed_body": "Couldn't reach the AI. Please try again in a moment.",
        "generating_retry": "Connection hiccup, retrying…",

        "quiz_back": "← Back",
        "quiz_next": "Next →",
        "quiz_finish": "Finish →",
        "quiz_grading": "Grading…",
        "quiz_unsupported_type": "This question type isn't supported yet.",
        "quiz_submit_error": "Could not submit your test — check your connection and try again.",
        "quiz_terms": "Terms",
        "quiz_definitions": "Definitions",
        "quiz_no_answer": "(no answer)",
        "quiz_unmatched": "(unmatched)",

        "results_scored_prefix": "You scored",
        "results_scored_infix": "out of",
        "results_review_btn": "Review Answers",
        "results_another_btn": "Take Another Test",

        "review_suffix": "Review",
        "review_score_label": "Score",
        "review_correct": "Correct",
        "review_incorrect": "Incorrect",
        "review_your_answer": "Your answer:",
        "review_correct_answer": "Correct answer:",
        "review_back_history": "Back to History",
        "review_another": "Take Another Test",

        "msg_welcome": "Welcome, {username}!",
        "msg_logged_out": "You've been logged out.",
        "msg_choose_subject": "Please choose a subject.",
        "msg_count_range": "Question count must be between {min} and {max}.",
        "msg_min_types": "Pick at least 2 interactive question formats.",

        "type_label_fill_blank": "Fill in the Blank",
        "type_label_matching": "Drag & Drop Matching",
        "type_label_ordering": "Sequence Ordering",
        "type_label_multi_select": "Select All That Apply",
        "type_label_numeric": "Numeric / Slider Answer",
        "type_label_code_complete": "Code Completion",

        "type_desc_fill_blank": "Type the missing word or phrase into a sentence.",
        "type_desc_matching": "Drag each term onto its matching definition.",
        "type_desc_ordering": "Drag items into the correct order or sequence.",
        "type_desc_multi_select": "Tap every option that is correct — there may be several.",
        "type_desc_numeric": "Drag a slider or type an exact number to answer.",
        "type_desc_code_complete": "Complete the missing piece of code.",
    },
    "ru": {
        "nav_new_test": "Новый тест",
        "nav_history": "История",
        "nav_logout": "Выйти",
        "nav_login": "Войти",
        "nav_get_started": "Начать",

        "landing_title": "Тесты, которые по-настоящему увлекают.",
        "landing_sub": "Выберите предмет, скажите ИИ, сколько вопросов вам нужно, и решайте их по-своему — перетаскивайте, сопоставляйте, двигайте ползунки и печатайте, а не кликайте одни и те же четыре варианта.",
        "landing_cta_start": "Начать тест",
        "landing_cta_register": "Создать бесплатный аккаунт",
        "landing_cta_login": "У меня уже есть аккаунт",
        "badge_matching": "🔗 Сопоставление перетаскиванием",
        "badge_ordering": "🔢 Расстановка по порядку",
        "badge_numeric": "🎚️ Числовые ползунки",
        "badge_code": "💻 Дополнение кода",
        "badge_multiselect": "🧩 Множественный выбор",
        "badge_fillblank": "✏️ Заполнение пропуска",

        "register_heading": "Создайте аккаунт",
        "label_username": "Имя пользователя",
        "label_email": "Email (необязательно)",
        "label_password": "Пароль",
        "label_password_confirm": "Подтвердите пароль",
        "btn_create_account": "Создать аккаунт",
        "already_have_account": "Уже есть аккаунт?",
        "login_link": "Войти",

        "login_heading": "С возвращением",
        "btn_login": "Войти",
        "new_here": "Впервые здесь?",
        "register_link": "Создать аккаунт",

        "history_heading": "Ваша история",
        "history_empty": "Пока нет завершённых тестов.",
        "history_start_first": "Начать первый тест",
        "history_questions_suffix": "вопросов",

        "setup_heading": "Соберите свой тест",
        "setup_lead": "Выберите предмет, количество вопросов и интерактивные форматы, которые должен использовать ИИ.",
        "setup_section_subject": "1. Предмет",
        "setup_section_count": "2. Сколько вопросов?",
        "setup_section_types": "3. Интерактивные форматы — выберите минимум 2 (никакого скучного выбора из вариантов)",
        "setup_submit": "Сгенерировать тест →",
        "setup_alert_min_types": "Выберите минимум 2 интерактивных формата.",
        "setup_starting": "Запускаем…",

        "generating_headline": "Создаём ваши вопросы…",
        "generating_starting": "Запуск…",
        "generating_progress": "{generated} / {target} вопросов готово",
        "generating_done": "Готово! Загружаем ваш тест…",
        "generating_failed_headline": "Не удалось создать тест",
        "generating_failed_body": "Не удалось связаться с ИИ. Попробуйте ещё раз через минуту.",
        "generating_retry": "Сбой соединения, повторяем попытку…",

        "quiz_back": "← Назад",
        "quiz_next": "Далее →",
        "quiz_finish": "Завершить →",
        "quiz_grading": "Проверяем…",
        "quiz_unsupported_type": "Этот тип вопроса пока не поддерживается.",
        "quiz_submit_error": "Не удалось отправить тест — проверьте соединение и попробуйте снова.",
        "quiz_terms": "Термины",
        "quiz_definitions": "Определения",
        "quiz_no_answer": "(нет ответа)",
        "quiz_unmatched": "(не сопоставлено)",

        "results_scored_prefix": "Вы набрали",
        "results_scored_infix": "из",
        "results_review_btn": "Посмотреть ответы",
        "results_another_btn": "Пройти ещё тест",

        "review_suffix": "Разбор",
        "review_score_label": "Результат",
        "review_correct": "Верно",
        "review_incorrect": "Неверно",
        "review_your_answer": "Ваш ответ:",
        "review_correct_answer": "Правильный ответ:",
        "review_back_history": "К истории",
        "review_another": "Пройти ещё тест",

        "msg_welcome": "Добро пожаловать, {username}!",
        "msg_logged_out": "Вы вышли из аккаунта.",
        "msg_choose_subject": "Пожалуйста, выберите предмет.",
        "msg_count_range": "Количество вопросов должно быть от {min} до {max}.",
        "msg_min_types": "Выберите минимум 2 интерактивных формата вопросов.",

        "type_label_fill_blank": "Заполнение пропуска",
        "type_label_matching": "Сопоставление перетаскиванием",
        "type_label_ordering": "Расстановка по порядку",
        "type_label_multi_select": "Множественный выбор",
        "type_label_numeric": "Числовой ответ / ползунок",
        "type_label_code_complete": "Дополнение кода",

        "type_desc_fill_blank": "Впишите пропущенное слово или фразу в предложение.",
        "type_desc_matching": "Перетащите каждый термин к нужному определению.",
        "type_desc_ordering": "Перетащите элементы в правильном порядке.",
        "type_desc_multi_select": "Отметьте все правильные варианты — их может быть несколько.",
        "type_desc_numeric": "Передвиньте ползунок или введите точное число.",
        "type_desc_code_complete": "Допишите недостающую часть кода.",
    },
    "uz": {
        "nav_new_test": "Yangi test",
        "nav_history": "Tarix",
        "nav_logout": "Chiqish",
        "nav_login": "Kirish",
        "nav_get_started": "Boshlash",

        "landing_title": "Haqiqatan ham qiziqarli testlar.",
        "landing_sub": "Fanni tanlang, sun'iy intellektga nechta savol kerakligini ayting va o'zingizga qulay usulda yeching — sudrab, moslashtirib, slayder bilan va yozib, doim bir xil to'rtta variantni bosish o'rniga.",
        "landing_cta_start": "Testni boshlash",
        "landing_cta_register": "Bepul hisob ochish",
        "landing_cta_login": "Hisobim allaqachon bor",
        "badge_matching": "🔗 Sudrab moslashtirish",
        "badge_ordering": "🔢 Ketma-ketlikka joylash",
        "badge_numeric": "🎚️ Sonli slayderlar",
        "badge_code": "💻 Kodni to'ldirish",
        "badge_multiselect": "🧩 Ko'p tanlovli",
        "badge_fillblank": "✏️ Bo'sh joyni to'ldirish",

        "register_heading": "Hisob yarating",
        "label_username": "Foydalanuvchi nomi",
        "label_email": "Email (ixtiyoriy)",
        "label_password": "Parol",
        "label_password_confirm": "Parolni tasdiqlang",
        "btn_create_account": "Hisob yaratish",
        "already_have_account": "Hisobingiz bormi?",
        "login_link": "Kirish",

        "login_heading": "Xush kelibsiz",
        "btn_login": "Kirish",
        "new_here": "Birinchi marta shu yerdamisiz?",
        "register_link": "Hisob yaratish",

        "history_heading": "Sizning tarixingiz",
        "history_empty": "Hozircha tugallangan testlar yo'q.",
        "history_start_first": "Birinchi testni boshlash",
        "history_questions_suffix": "ta savol",

        "setup_heading": "Testingizni tuzing",
        "setup_lead": "Fanni, nechta savol kerakligini va sun'iy intellekt qaysi interaktiv formatlardan foydalanishini tanlang.",
        "setup_section_subject": "1. Fan",
        "setup_section_count": "2. Nechta savol?",
        "setup_section_types": "3. Interaktiv formatlar — kamida 2 tasini tanlang (zerikarli test savollari emas)",
        "setup_submit": "Testimni yaratish →",
        "setup_alert_min_types": "Kamida 2 ta interaktiv formatni tanlang.",
        "setup_starting": "Boshlanmoqda…",

        "generating_headline": "Savollaringiz tayyorlanmoqda…",
        "generating_starting": "Ishga tushmoqda…",
        "generating_progress": "{generated} / {target} savol tayyor",
        "generating_done": "Tayyor! Testingiz yuklanmoqda…",
        "generating_failed_headline": "Yaratib bo'lmadi",
        "generating_failed_body": "Sun'iy intellektga ulanib bo'lmadi. Birozdan so'ng qayta urinib ko'ring.",
        "generating_retry": "Ulanishda uzilish, qayta urinilmoqda…",

        "quiz_back": "← Orqaga",
        "quiz_next": "Keyingisi →",
        "quiz_finish": "Yakunlash →",
        "quiz_grading": "Tekshirilmoqda…",
        "quiz_unsupported_type": "Bu savol turi hali qo'llab-quvvatlanmaydi.",
        "quiz_submit_error": "Testni yuborib bo'lmadi — internetingizni tekshirib, qayta urinib ko'ring.",
        "quiz_terms": "Atamalar",
        "quiz_definitions": "Ta'riflar",
        "quiz_no_answer": "(javob yo'q)",
        "quiz_unmatched": "(moslashtirilmagan)",

        "results_scored_prefix": "Siz to'pladingiz:",
        "results_scored_infix": "dan",
        "results_review_btn": "Javoblarni ko'rish",
        "results_another_btn": "Yana test topshirish",

        "review_suffix": "Ko'rib chiqish",
        "review_score_label": "Natija",
        "review_correct": "To'g'ri",
        "review_incorrect": "Noto'g'ri",
        "review_your_answer": "Sizning javobingiz:",
        "review_correct_answer": "To'g'ri javob:",
        "review_back_history": "Tarixga qaytish",
        "review_another": "Yana test topshirish",

        "msg_welcome": "Xush kelibsiz, {username}!",
        "msg_logged_out": "Hisobingizdan chiqdingiz.",
        "msg_choose_subject": "Iltimos, fanni tanlang.",
        "msg_count_range": "Savollar soni {min} va {max} orasida bo'lishi kerak.",
        "msg_min_types": "Kamida 2 ta interaktiv savol formatini tanlang.",

        "type_label_fill_blank": "Bo'sh joyni to'ldirish",
        "type_label_matching": "Sudrab moslashtirish",
        "type_label_ordering": "Ketma-ketlikka joylash",
        "type_label_multi_select": "Ko'p javobni tanlash",
        "type_label_numeric": "Sonli javob / slayder",
        "type_label_code_complete": "Kodni to'ldirish",

        "type_desc_fill_blank": "Gapdagi tushirib qoldirilgan so'z yoki iborani yozing.",
        "type_desc_matching": "Har bir atamani mos ta'rifiga sudrab olib boring.",
        "type_desc_ordering": "Elementlarni to'g'ri tartibda joylashtiring.",
        "type_desc_multi_select": "To'g'ri bo'lgan barcha variantlarni belgilang — ular bir nechta bo'lishi mumkin.",
        "type_desc_numeric": "Slayderni suring yoki aniq sonni kiriting.",
        "type_desc_code_complete": "Kodning yetishmayotgan qismini to'ldiring.",
    },
    "kaa": {
        "nav_new_test": "Jańa test",
        "nav_history": "Tariyx",
        "nav_logout": "Shig'iw",
        "nav_login": "Kiriw",
        "nav_get_started": "Baslaw",

        "landing_title": "Haqıyqattan da qızıqlı testler.",
        "landing_sub": "Páninnen birewin tańlań, jasalma intellektke qansha soraw kerek ekenin aytıń hám olardı óz usılıńızda sheshiń — súyrep, sáykestirip, slayder penen hám jazıp, hár dayım sol tórt variantti basıwdıń ornına.",
        "landing_cta_start": "Testti baslaw",
        "landing_cta_register": "Biykar akkaunt ashıw",
        "landing_cta_login": "Akkauntım bar",
        "badge_matching": "🔗 Súyrep sáykestiriw",
        "badge_ordering": "🔢 Retke jaylastırıw",
        "badge_numeric": "🎚️ San slayderleri",
        "badge_code": "💻 Kodti tolıqtırıw",
        "badge_multiselect": "🧩 Kóp tańlaw",
        "badge_fillblank": "✏️ Bos orındı toltırıw",

        "register_heading": "Akkaunt jaratıń",
        "label_username": "Paydalanıwshı atı",
        "label_email": "Email (májbúriy emes)",
        "label_password": "Parol",
        "label_password_confirm": "Paroldi tastıyıqlań",
        "btn_create_account": "Akkaunt jaratıw",
        "already_have_account": "Akkauntıńız barma?",
        "login_link": "Kiriw",

        "login_heading": "Qaytıp kelgeningizge qıwanıshlımız",
        "btn_login": "Kiriw",
        "new_here": "Birinshi ret usı jerdesizbe?",
        "register_link": "Akkaunt jaratıw",

        "history_heading": "Sizdiń tariyxıńız",
        "history_empty": "Házirshe tamamlanǵan testler joq.",
        "history_start_first": "Birinshi testti baslań",
        "history_questions_suffix": "soraw",

        "setup_heading": "Testińizdi dúzıń",
        "setup_lead": "Pánin, qansha soraw kerekligin hám jasalma intellekt qaysı interaktiv formatlardı qollanıwın tańlań.",
        "setup_section_subject": "1. Pán",
        "setup_section_count": "2. Qansha soraw?",
        "setup_section_types": "3. Interaktiv formatlar — keminde 2-wın tańlań (zerikerli test soraw emes)",
        "setup_submit": "Testimdi jaratıw →",
        "setup_alert_min_types": "Keminde 2 interaktiv formattı tańlań.",
        "setup_starting": "Baslanbaqta…",

        "generating_headline": "Sorawlarıńız tayarlanbaqta…",
        "generating_starting": "Iske qosılmaqta…",
        "generating_progress": "{generated} / {target} soraw tayar",
        "generating_done": "Tayar! Testińiz júklenbekte…",
        "generating_failed_headline": "Jaratıw sátsiz boldı",
        "generating_failed_body": "Jasalma intellekt penen baylanıs ornatılmadı. Sál waqıttan soń qayta urınıp kóriń.",
        "generating_retry": "Baylanıs úzildi, qayta urınbaqta…",

        "quiz_back": "← Artqa",
        "quiz_next": "Keyingi →",
        "quiz_finish": "Juwmaqlaw →",
        "quiz_grading": "Tekseribekte…",
        "quiz_unsupported_type": "Bul soraw túri házirshe qollap-quwatlanbaydı.",
        "quiz_submit_error": "Testti jiberip bolmadı — internetińizdi tekserip, qayta urınıń.",
        "quiz_terms": "Atamalar",
        "quiz_definitions": "Anıqlamalar",
        "quiz_no_answer": "(juwap joq)",
        "quiz_unmatched": "(sáykestirilmegen)",

        "results_scored_prefix": "Siz jıynadıńız:",
        "results_scored_infix": "dan",
        "results_review_btn": "Juwaplardı kóriw",
        "results_another_btn": "Basqa test tapsırıw",

        "review_suffix": "Kóriw",
        "review_score_label": "Nátiyje",
        "review_correct": "Durıs",
        "review_incorrect": "Nadurıs",
        "review_your_answer": "Sizdiń juwabıńız:",
        "review_correct_answer": "Durıs juwap:",
        "review_back_history": "Tariyxqa qaytıw",
        "review_another": "Basqa test tapsırıw",

        "msg_welcome": "Qosh keldińiz, {username}!",
        "msg_logged_out": "Akkauntıńızdan shıqtıńız.",
        "msg_choose_subject": "Iltimas, pándi tańlań.",
        "msg_count_range": "Sorawlar sanı {min} penen {max} arasında bolıwı kerek.",
        "msg_min_types": "Keminde 2 interaktiv soraw formatın tańlań.",

        "type_label_fill_blank": "Bos orındı toltırıw",
        "type_label_matching": "Súyrep sáykestiriw",
        "type_label_ordering": "Retke jaylastırıw",
        "type_label_multi_select": "Kóp juwaptı tańlaw",
        "type_label_numeric": "San juwabı / slayder",
        "type_label_code_complete": "Kodti tolıqtırıw",

        "type_desc_fill_blank": "Sóylemdegi túsip qalǵan sóz yamasa ibarani jazıń.",
        "type_desc_matching": "Hár bir atamanı sáykes anıqlamasına súyrep bariń.",
        "type_desc_ordering": "Elementlerdi durıs tártipte jaylastırıń.",
        "type_desc_multi_select": "Durıs bolǵan barlıq variantlardı belgileń — olar bir neshe bolıwı múmkin.",
        "type_desc_numeric": "Slayderdi júrgiziń yamasa anıq sandı kiritiń.",
        "type_desc_code_complete": "Kodtıń jetispey turǵan bólegin tolıqtırıń.",
    },
}


def get_strings(lang_code):
    return TRANSLATIONS.get(lang_code, TRANSLATIONS[DEFAULT_LANGUAGE])


SUBJECT_NAMES = {
    "math": {"en": "Mathematics", "ru": "Математика", "uz": "Matematika", "kaa": "Matematika"},
    "programming": {"en": "Programming", "ru": "Программирование", "uz": "Dasturlash", "kaa": "Programmalastırıw"},
    "physics": {"en": "Physics", "ru": "Физика", "uz": "Fizika", "kaa": "Fizika"},
    "chemistry": {"en": "Chemistry", "ru": "Химия", "uz": "Kimyo", "kaa": "Ximiya"},
    "biology": {"en": "Biology", "ru": "Биология", "uz": "Biologiya", "kaa": "Biologiya"},
    "history": {"en": "History", "ru": "История", "uz": "Tarix", "kaa": "Tariyx"},
    "geography": {"en": "Geography", "ru": "География", "uz": "Geografiya", "kaa": "Geografiya"},
    "english": {"en": "English Language", "ru": "Английский язык", "uz": "Ingliz tili", "kaa": "Ingliz tili"},
    "computer-science": {"en": "Computer Science", "ru": "Информатика", "uz": "Kompyuter fanlari", "kaa": "Kompyuter ilimi"},
    "economics": {"en": "Economics", "ru": "Экономика", "uz": "Iqtisodiyot", "kaa": "Ekonomika"},
    "astronomy": {"en": "Astronomy", "ru": "Астрономия", "uz": "Astronomiya", "kaa": "Astronomiya"},
    "psychology": {"en": "Psychology", "ru": "Психология", "uz": "Psixologiya", "kaa": "Psixologiya"},
    "art-design": {"en": "Art & Design", "ru": "Искусство и дизайн", "uz": "San'at va dizayn", "kaa": "Óner hám dizayn"},
    "philosophy": {"en": "Philosophy", "ru": "Философия", "uz": "Falsafa", "kaa": "Filosofiya"},
}


def subject_name(subject, lang_code):
    names = SUBJECT_NAMES.get(subject.slug)
    if not names:
        return subject.name
    return names.get(lang_code, names[DEFAULT_LANGUAGE])
