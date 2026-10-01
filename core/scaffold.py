"""
Content of the SCAFFOLD methodological toolkit, used by the lesson-design
assistant and the built-in guide.

Source: European Commission, Joint Research Centre, Bacigalupo, M., Binasco, A.,
Bekh, O., Israel, H. and Weikert García, L., "Scaffold", a deck of cards to
design competence-oriented learning experiences, Publications Office of the
European Union, Luxembourg, 2024, https://data.europa.eu/doi/10.2760/057661,
JRC136622. Licensed under CC BY 4.0. Changes: the texts were shortened and
translated into Russian and Uzbek for this platform.

Competence names follow the EU frameworks DigComp 2.2, EntreComp, LifeComp and
GreenComp, which the deck is built on.

Every translatable value is a dict {"en": ..., "ru": ..., "uz": ...};
Karakalpak falls back to Uzbek, anything else to English (see `tr`).
"""

SOURCE_TITLE = '“Scaffold”, a deck of cards to design competence-oriented learning experiences (JRC & ETF, 2024)'
SOURCE_URL = "https://data.europa.eu/doi/10.2760/057661"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

_FALLBACKS = {"kaa": ["uz", "en"], "uz": ["en"], "ru": ["en"], "en": []}


def tr(value, lang):
    """Picks the best available translation from a {"en": ..., "ru": ..., "uz": ...} dict."""
    if not isinstance(value, dict):
        return value
    for code in [lang, *_FALLBACKS.get(lang, ["en"])]:
        if code in value:
            return value[code]
    return value.get("en", "")


def L(en, ru, uz):
    return {"en": en, "ru": ru, "uz": uz}


# ----------------------------------------------------------------- principles

PRINCIPLES = [
    {
        "code": "real_life",
        "title": L("Engage learners in real-life learning experiences",
                   "Вовлекайте обучающихся в реальный учебный процесс",
                   "Oʻquvchilarni real hayotiy taʼlim tajribasiga jalb qiling"),
        "tips": L(
            ["Create a plan for action, considering what matters to your learners.",
             "Establish the right climate for experimentation and flexible adaptation.",
             "Create opportunities to fail, reflect and recover.",
             "Practise and learn in a real-world setting with real-world purposes.",
             "Ensure numerous iterations to guarantee learning through experience.",
             "Test ideas and progressively refine assumptions based on what works and what does not."],
            ["Составьте план действий с учётом того, что важно для обучающихся.",
             "Создайте атмосферу для экспериментов и гибкой адаптации.",
             "Дайте возможность ошибаться, размышлять и восстанавливаться.",
             "Практикуйтесь и учитесь в реальной среде с реальными целями.",
             "Обеспечьте многократные повторения, чтобы учиться на опыте.",
             "Проверяйте идеи и уточняйте предположения на основе того, что работает, а что нет."],
            ["Oʻquvchilar uchun muhim narsalarni hisobga olib, harakat rejasini tuzing.",
             "Tajriba va moslashuvchan yondashuv uchun qulay muhit yarating.",
             "Xato qilish, fikrlash va qayta tiklanish uchun imkon bering.",
             "Real hayotiy maqsadlar bilan real muhitda mashq qiling va oʻrganing.",
             "Tajriba orqali oʻrganish uchun koʻp marta takrorlashni taʼminlang.",
             "Nima ishlashi va nima ishlamasligiga qarab gʻoyalarni sinab, farazlarni aniqlashtiring."],
        ),
        "try_method": "pbl",
        "try_assessments": ["authentic"],
    },
    {
        "code": "reflection",
        "title": L("Use reflection to enhance learners’ understanding of how they learn",
                   "Используйте рефлексию, чтобы обучающиеся понимали, как они учатся",
                   "Oʻquvchilar qanday oʻrganishini tushunishi uchun refleksiyadan foydalaning"),
        "tips": L(
            ["Build in regular opportunities for reflection.",
             "Promote use of reflection to refine assumptions and improve ideas at each step.",
             "Support use of reflection to extract general principles to apply to new situations."],
            ["Регулярно встраивайте возможности для рефлексии.",
             "Используйте рефлексию, чтобы уточнять предположения и улучшать идеи на каждом шаге.",
             "Помогайте извлекать общие принципы и применять их в новых ситуациях."],
            ["Refleksiya uchun muntazam imkoniyatlar yarating.",
             "Har bir bosqichda farazlarni aniqlashtirish va gʻoyalarni yaxshilash uchun refleksiyadan foydalaning.",
             "Umumiy qoidalarni ajratib olib, ularni yangi vaziyatlarda qoʻllashga yordam bering."],
        ),
        "try_method": "cl",
        "try_assessments": ["peer_feedback"],
    },
    {
        "code": "learner_centre",
        "title": L("Place the learner at the centre",
                   "Поставьте обучающегося в центр процесса",
                   "Oʻquvchini markazga qoʻying"),
        "tips": L(
            ["Allow learners to make decisions about what to learn and how to learn it.",
             "Involve learners in planning, resourcing, evaluation and recognition.",
             "Foster meaningful learning.",
             "Facilitate peer and team learning.",
             "Develop personalised learning experiences."],
            ["Позвольте обучающимся решать, что и как изучать.",
             "Вовлекайте их в планирование, подбор ресурсов, оценивание и признание результатов.",
             "Способствуйте осмысленному обучению.",
             "Поддерживайте обучение в парах и командах.",
             "Создавайте персонализированный опыт обучения."],
            ["Oʻquvchilarga nimani va qanday oʻrganishni oʻzlari hal qilishga imkon bering.",
             "Ularni rejalashtirish, resurslar, baholash va natijalarni eʼtirof etishga jalb qiling.",
             "Mazmunli oʻrganishni qoʻllab-quvvatlang.",
             "Juftlik va jamoada oʻrganishga koʻmaklashing.",
             "Shaxsiylashtirilgan taʼlim tajribasini yarating."],
        ),
        "try_method": "led",
        "try_assessments": ["self_reflection"],
    },
    {
        "code": "facilitate",
        "title": L("Shift the focus from teaching a subject to facilitating learning",
                   "Смещайте фокус с преподавания предмета на содействие обучению",
                   "Eʼtiborni fanni oʻqitishdan oʻrganishga koʻmaklashishga qarating"),
        "tips": L(
            ["Reduce learner dependency on you as an educator.",
             "Prompt learners to draw upon their previous experience and assume new roles.",
             "Develop learner self-efficacy and capacity to cope with uncertain, complex situations."],
            ["Снижайте зависимость обучающихся от вас как педагога.",
             "Побуждайте опираться на прошлый опыт и пробовать новые роли.",
             "Развивайте самоэффективность и умение справляться с неопределённостью и сложностью."],
            ["Oʻquvchilarning oʻqituvchiga qaramligini kamaytiring.",
             "Oʻtgan tajribasiga tayanib, yangi rollarni sinab koʻrishga undang.",
             "Oʻziga ishonch va noaniq, murakkab vaziyatlarda harakat qilish qobiliyatini rivojlantiring."],
        ),
        "try_method": "ll",
        "try_assessments": ["questions"],
    },
    {
        "code": "community",
        "title": L("Open the classroom to the community and engage others",
                   "Откройте класс для сообщества и вовлекайте других",
                   "Sinfni jamiyatga oching va boshqalarni jalb qiling"),
        "tips": L(
            ["Cultivate relationships with local businesses, NGOs or community associations as a source of real challenges.",
             "Map local stakeholders who can act as mentors.",
             "Interact closely with those expected to benefit from an idea.",
             "Keep opening the classroom to the real world a safe learning experience.",
             "Create cooperative groups with clear goals, roles and responsibilities.",
             "Join a learning community with your peers: plan together and exchange feedback."],
            ["Сотрудничайте с местным бизнесом, НКО и сообществами как источником реальных задач.",
             "Найдите местных партнёров, которые могут стать наставниками.",
             "Тесно взаимодействуйте с теми, для кого создаётся идея.",
             "Следите, чтобы выход в реальный мир оставался безопасным.",
             "Создавайте группы с чёткими целями, ролями и обязанностями.",
             "Участвуйте в сообществе коллег: планируйте вместе и обменивайтесь отзывами."],
            ["Real vazifalar manbai sifatida mahalliy biznes, NNT va jamoat birlashmalari bilan hamkorlik qiling.",
             "Murabbiy boʻla oladigan mahalliy hamkorlarni aniqlang.",
             "Gʻoyadan foyda koʻradigan odamlar bilan yaqin muloqot qiling.",
             "Real dunyoga chiqish xavfsiz taʼlim tajribasi boʻlib qolishini taʼminlang.",
             "Aniq maqsad, rol va masʼuliyatga ega hamkorlik guruhlarini tuzing.",
             "Hamkasblar hamjamiyatida ishtirok eting: birga rejalashtiring va fikr almashing."],
        ),
        "try_method": "vcp",
        "try_assessments": ["authentic"],
    },
    {
        "code": "emotions",
        "title": L("Embed triggers for emotional learning",
                   "Встраивайте триггеры эмоционального обучения",
                   "Hissiy oʻrganish uchun turtki beruvchi elementlarni qoʻshing"),
        "tips": L(
            ["Identify the emotions present in learning processes.",
             "Anticipate and plan to manage emotions in ill-defined, time-constrained tasks.",
             "Leverage the emotional dimension of learning to promote motivation and resilience."],
            ["Определите эмоции, возникающие в процессе обучения.",
             "Предусмотрите управление эмоциями в задачах с неясными условиями и ограничением времени.",
             "Используйте эмоциональную сторону обучения для мотивации и устойчивости."],
            ["Oʻrganish jarayonidagi hissiyotlarni aniqlang.",
             "Noaniq va vaqt cheklangan vazifalarda hissiyotlarni boshqarishni oldindan rejalashtiring.",
             "Motivatsiya va chidamlilikni oshirish uchun oʻrganishning hissiy tomonidan foydalaning."],
        ),
        "try_method": "spl",
        "try_assessments": ["self_reflection"],
    },
    {
        "code": "assess_progress",
        "title": L("Assess progress through multiple methods and make it visible",
                   "Оценивайте прогресс разными методами и делайте его видимым",
                   "Rivojlanishni turli usullar bilan baholang va uni koʻrinadigan qiling"),
        "tips": L(
            ["Determine the starting point.",
             "Use the baseline to help learners reflect on the progress they have made.",
             "Provide frequent, timely and actionable feedback.",
             "Give feedback that triggers the desire to improve.",
             "Celebrate progress with your learners."],
            ["Определите стартовый уровень.",
             "Используйте его, чтобы обучающиеся видели свой прогресс.",
             "Давайте частую, своевременную и практичную обратную связь.",
             "Давайте обратную связь, которая мотивирует улучшаться.",
             "Отмечайте успехи вместе с обучающимися."],
            ["Boshlangʻich darajani aniqlang.",
             "Oʻquvchilar erishgan yutuqlarini koʻrishi uchun undan foydalaning.",
             "Tez-tez, oʻz vaqtida va amaliy fikr-mulohaza bering.",
             "Yaxshilanishga undaydigan fikr-mulohaza bering.",
             "Yutuqlarni oʻquvchilar bilan birga nishonlang."],
        ),
        "try_method": "sl",
        "try_assessments": ["evidence", "observation", "self_reflection"],
    },
]


# ----------------------------------------------------------- teaching methods

TEACHING_METHODS = [
    {
        "code": "pbl", "abbr": "PBL",
        "title": L("Project-based learning", "Проектное обучение", "Loyihaviy taʼlim"),
        "description": L(
            "Learners develop knowledge and skills through projects based on real-world challenges and problems that matter to them, giving learning purpose and stimulating autonomy.",
            "Обучающиеся развивают знания и навыки через проекты, основанные на реальных и значимых для них задачах; это придаёт обучению смысл и развивает самостоятельность.",
            "Oʻquvchilar oʻzlari uchun muhim boʻlgan real muammolarga asoslangan loyihalar orqali bilim va koʻnikma egallaydi; bu oʻqishga maqsad beradi va mustaqillikni rivojlantiradi.",
        ),
        "steps": L(
            ["Identify and frame a real-world problem, question or challenge.",
             "Identify and sequence tasks to support sustained enquiry.",
             "Generate and evaluate ideas.",
             "Create a product to test, refine and present the work.",
             "Reflect and celebrate learning."],
            ["Определить и сформулировать реальную проблему, вопрос или задачу.",
             "Выделить и упорядочить задачи для последовательного исследования.",
             "Генерировать и оценивать идеи.",
             "Создать продукт, протестировать, доработать и представить его.",
             "Провести рефлексию и отметить результаты."],
            ["Real muammo, savol yoki vazifani aniqlash va shakllantirish.",
             "Izchil tadqiqot uchun vazifalarni belgilash va tartiblash.",
             "Gʻoyalarni ishlab chiqish va baholash.",
             "Mahsulot yaratish, sinash, takomillashtirish va taqdim etish.",
             "Refleksiya qilish va yutuqlarni nishonlash."],
        ),
        "ideas": [
            L("Sustainable Development Goals — frame a project around one of the 17 UN SDGs.",
              "Цели устойчивого развития — проект вокруг одной из 17 целей ООН.",
              "Barqaror rivojlanish maqsadlari — BMTning 17 maqsadidan biri atrofida loyiha."),
            L("Exhibition — learners showcase their work and progress to a real audience.",
              "Выставка — обучающиеся представляют свои работы и прогресс реальной аудитории.",
              "Koʻrgazma — oʻquvchilar ishlari va yutuqlarini real auditoriyaga namoyish etadi."),
        ],
    },
    {
        "code": "led", "abbr": "LED",
        "title": L("Learner-led learning", "Обучение под руководством обучающихся", "Oʻquvchi boshqaradigan taʼlim"),
        "description": L(
            "Learners actively contribute their experience to make learning relevant and meaningful to their own needs, interests and aspirations.",
            "Обучающиеся активно привносят свой опыт, делая обучение значимым для своих потребностей, интересов и устремлений.",
            "Oʻquvchilar oʻz tajribasini faol qoʻshib, taʼlimni oʻz ehtiyojlari, qiziqishlari va intilishlariga mos va mazmunli qiladi.",
        ),
        "steps": L(
            ["Learners identify topics or challenges to explore.",
             "They identify preferred teaching and assessment methods.",
             "They set personal competence development goals.",
             "They choose how to select, apply and evaluate competence in specific tasks.",
             "They are supported to relate competences to diverse purposes and contexts."],
            ["Обучающиеся выбирают темы или задачи для изучения.",
             "Определяют предпочтительные методы обучения и оценивания.",
             "Ставят личные цели развития компетенций.",
             "Решают, как применять и оценивать компетенции в конкретных задачах.",
             "Получают поддержку в связывании компетенций с разными целями и контекстами."],
            ["Oʻquvchilar oʻrganiladigan mavzu yoki vazifalarni tanlaydi.",
             "Maʼqul oʻqitish va baholash usullarini belgilaydi.",
             "Kompetensiyalarni rivojlantirish boʻyicha shaxsiy maqsad qoʻyadi.",
             "Aniq vazifalarda kompetensiyani qanday qoʻllash va baholashni tanlaydi.",
             "Kompetensiyalarni turli maqsad va vaziyatlarga bogʻlashda yordam oladi."],
        ),
        "ideas": [
            L("Individual learning plans — personal next-step goals for each learner.",
              "Индивидуальные планы обучения — личные цели следующего шага для каждого.",
              "Individual oʻquv rejalari — har bir oʻquvchi uchun shaxsiy keyingi maqsadlar."),
            L("Ikigai — connect learning with what learners love, are good at and what the world needs.",
              "Икигай — связать обучение с тем, что любят, умеют и что нужно миру.",
              "Ikigai — oʻqishni sevgan, uddalaydigan va dunyoga kerak narsalar bilan bogʻlash."),
        ],
    },
    {
        "code": "vcp", "abbr": "VCP",
        "title": L("Value creation pedagogy", "Педагогика создания ценности", "Qadriyat yaratish pedagogikasi"),
        "description": L(
            "Learners apply their competences to create something of economic, social or cultural value for at least one stakeholder outside their own group, class or school.",
            "Обучающиеся применяют компетенции, чтобы создать экономическую, социальную или культурную ценность хотя бы для одного человека вне своей группы, класса или школы.",
            "Oʻquvchilar oʻz kompetensiyalarini qoʻllab, guruhi, sinfi yoki maktabidan tashqaridagi kamida bitta manfaatdor uchun iqtisodiy, ijtimoiy yoki madaniy qadriyat yaratadi.",
        ),
        "steps": L(
            ["Learners reflect on who could benefit from their learning.",
             "They spot opportunities to create value for others.",
             "They decide how they will create value and take action.",
             "They use feedback from the intended beneficiaries to refine their work.",
             "They reflect on their learning experience."],
            ["Обучающиеся думают, кому может быть полезно их обучение.",
             "Находят возможности создать ценность для других.",
             "Решают, как создать ценность, и действуют.",
             "Используют отзывы получателей для доработки.",
             "Проводят рефлексию своего опыта."],
            ["Oʻquvchilar oʻz bilimidan kim foyda koʻrishi mumkinligini oʻylaydi.",
             "Boshqalar uchun qadriyat yaratish imkoniyatlarini topadi.",
             "Qanday qadriyat yaratishni hal qilib, harakat qiladi.",
             "Ishini takomillashtirish uchun foydalanuvchilar fikridan foydalanadi.",
             "Oʻz tajribasi boʻyicha refleksiya qiladi."],
        ),
        "ideas": [
            L("Creating value for animals — act to protect local biodiversity (SDG 15).",
              "Ценность для животных — действия по защите местного биоразнообразия (ЦУР 15).",
              "Hayvonlar uchun qadriyat — mahalliy bioxilma-xillikni himoya qilish (BRM 15)."),
            L("Video tutorial — learners create a lesson on this year’s topic for next year’s learners.",
              "Видеоурок — обучающиеся создают урок по теме года для следующего набора.",
              "Video dars — oʻquvchilar keyingi yil oʻquvchilari uchun mavzu boʻyicha dars tayyorlaydi."),
        ],
    },
    {
        "code": "cl", "abbr": "CL",
        "title": L("Cooperative learning", "Кооперативное обучение", "Hamkorlikda oʻrganish"),
        "description": L(
            "Learners learn with and from each other, considering diverse perspectives and needs, to motivate and support each other to go further.",
            "Обучающиеся учатся вместе и друг у друга, учитывая разные точки зрения и потребности, мотивируя и поддерживая друг друга.",
            "Oʻquvchilar turli qarash va ehtiyojlarni hisobga olib, bir-biri bilan va bir-biridan oʻrganadi, bir-birini ragʻbatlantiradi va qoʻllab-quvvatlaydi.",
        ),
        "steps": L(
            ["Learners work in groups.",
             "They define or receive individual and group goals.",
             "They work together to co-create solutions.",
             "They help define success criteria and shared expectations.",
             "They ‘teach’ each other."],
            ["Обучающиеся работают в группах.",
             "Определяют или получают индивидуальные и групповые цели.",
             "Вместе создают решения.",
             "Участвуют в определении критериев успеха и общих ожиданий.",
             "«Обучают» друг друга."],
            ["Oʻquvchilar guruhlarda ishlaydi.",
             "Shaxsiy va guruh maqsadlarini belgilaydi yoki oladi.",
             "Yechimlarni birgalikda yaratadi.",
             "Muvaffaqiyat mezonlari va umumiy kutilmalarni belgilashda qatnashadi.",
             "Bir-birini „oʻqitadi“."],
        ),
        "ideas": [
            L("Group note taking — learners build shared notes during a lecture.",
              "Групповой конспект — общий конспект во время лекции.",
              "Guruhli konspekt — maʼruza davomida umumiy konspekt tuzish."),
            L("World Café — small-table rounds of dialogue on key questions.",
              "Мировое кафе — диалог за небольшими столами по ключевым вопросам.",
              "Jahon kafesi — kichik stollarda asosiy savollar boʻyicha suhbat."),
        ],
    },
    {
        "code": "spl", "abbr": "SPL",
        "title": L("Seriously playful learning", "Серьёзное игровое обучение", "Jiddiy oʻyinli taʼlim"),
        "description": L(
            "Learners take a creative, explorative, active and immersive attitude to learning, stimulating intrinsic motivation and a flow state.",
            "Обучающиеся проявляют творческий, исследовательский и активный подход, что стимулирует внутреннюю мотивацию и состояние потока.",
            "Oʻquvchilar oʻrganishga ijodiy, izlanuvchan va faol yondashadi; bu ichki motivatsiya va „oqim“ holatini uygʻotadi.",
        ),
        "steps": L(
            ["Learners learn from failure in a safe space.",
             "They engage in playful activities designed for learning.",
             "They understand the learning purpose of the activity.",
             "They are emotionally engaged in learning.",
             "They envision sustainable futures and frame problems in a novel way."],
            ["Обучающиеся учатся на ошибках в безопасной среде.",
             "Участвуют в игровых учебных активностях.",
             "Понимают учебную цель активности.",
             "Эмоционально вовлечены в обучение.",
             "Представляют устойчивое будущее и по-новому формулируют проблемы."],
            ["Oʻquvchilar xavfsiz muhitda xatolardan oʻrganadi.",
             "Oʻrganish uchun moʻljallangan oʻyinli faoliyatda qatnashadi.",
             "Faoliyatning taʼlimiy maqsadini tushunadi.",
             "Oʻrganishga hissiy jihatdan jalb qilinadi.",
             "Barqaror kelajakni tasavvur qilib, muammolarni yangicha shakllantiradi."],
        ),
        "ideas": [
            L("Simple gamification — points, badges and short energisers between tasks.",
              "Простая геймификация — баллы, значки и короткие разминки между заданиями.",
              "Oddiy geymifikatsiya — ballar, nishonlar va vazifalar orasida qisqa dam olish."),
            L("Making failing fun — challenges where failing and retrying is part of mastery.",
              "Ошибаться весело — задания, где ошибка и новая попытка — путь к мастерству.",
              "Xato qilish qiziqarli — xato va qayta urinish mahorat yoʻli boʻlgan topshiriqlar."),
        ],
    },
    {
        "code": "ll", "abbr": "LL",
        "title": L("Laboratory learning", "Лабораторное обучение", "Laboratoriya taʼlimi"),
        "description": L(
            "Learners learn through hands-on, trial-and-error experimentation with objects, materials and phenomena, where they observe, practise and test solutions.",
            "Обучающиеся учатся на практике, методом проб и ошибок экспериментируя с объектами, материалами и явлениями.",
            "Oʻquvchilar narsalar, materiallar va hodisalar bilan sinov-xato usulida amaliy tajriba oʻtkazib oʻrganadi.",
        ),
        "steps": L(
            ["Learners experiment using available resources.",
             "They learn by making.",
             "They learn from failures and setbacks.",
             "They document their laboratory practice.",
             "They reflect on their learning experience."],
            ["Обучающиеся экспериментируют с доступными ресурсами.",
             "Учатся, создавая.",
             "Учатся на неудачах.",
             "Документируют свою практику.",
             "Проводят рефлексию."],
            ["Oʻquvchilar mavjud resurslar bilan tajriba oʻtkazadi.",
             "Yaratish orqali oʻrganadi.",
             "Muvaffaqiyatsizliklardan oʻrganadi.",
             "Laboratoriya amaliyotini hujjatlashtiradi.",
             "Oʻz tajribasi boʻyicha refleksiya qiladi."],
        ),
        "ideas": [
            L("Imagine If — make an everyday object more effective, efficient, ethical or beautiful.",
              "«Представь, если» — сделать предмет эффективнее, этичнее или красивее.",
              "„Tasavvur qil“ — kundalik buyumni samaraliroq, axloqiyroq yoki chiroyliroq qilish."),
            L("Science simulations — run experiments in a virtual laboratory.",
              "Научные симуляции — эксперименты в виртуальной лаборатории.",
              "Ilmiy simulyatsiyalar — virtual laboratoriyada tajribalar."),
        ],
    },
    {
        "code": "sl", "abbr": "SL",
        "title": L("Service learning", "Обучение через служение", "Xizmat orqali oʻrganish"),
        "description": L(
            "Learners turn ideas into action to meet real-world needs in their local community.",
            "Обучающиеся воплощают идеи в действия, отвечая на реальные потребности местного сообщества.",
            "Oʻquvchilar mahalliy jamiyatning real ehtiyojlarini qondirish uchun gʻoyalarni amalga oshiradi.",
        ),
        "steps": L(
            ["Learners engage with their communities and identify needs.",
             "They explore how to create value for the community.",
             "They take action to create value for the community.",
             "They reflect on feedback from beneficiaries.",
             "They demonstrate learning and celebrate progress."],
            ["Обучающиеся взаимодействуют с сообществом и выявляют потребности.",
             "Изучают, как принести пользу сообществу.",
             "Действуют, чтобы создать ценность.",
             "Анализируют отзывы получателей.",
             "Демонстрируют результаты и отмечают прогресс."],
            ["Oʻquvchilar jamiyat bilan muloqot qilib, ehtiyojlarni aniqlaydi.",
             "Jamiyat uchun qanday foyda keltirishni oʻrganadi.",
             "Qadriyat yaratish uchun harakat qiladi.",
             "Foydalanuvchilar fikrini tahlil qiladi.",
             "Natijalarni namoyish etib, yutuqlarni nishonlaydi."],
        ),
        "ideas": [
            L("Let’s not eat the planet — a sustainable-nutrition campaign for local families.",
              "«Не будем съедать планету» — кампания об устойчивом питании для местных семей.",
              "„Sayyorani yeb qoʻymaylik“ — mahalliy oilalar uchun barqaror ovqatlanish kampaniyasi."),
            L("Digital competence for the elderly — learners teach older people digital skills.",
              "Цифровые навыки для пожилых — обучающиеся учат пожилых людей.",
              "Keksalar uchun raqamli savodxonlik — oʻquvchilar keksalarni oʻqitadi."),
        ],
    },
]


# --------------------------------------------------------- assessment methods

ASSESSMENT_METHODS = [
    {
        "code": "peer_feedback",
        "title": L("Peer feedback", "Взаимная обратная связь", "Oʻzaro fikr-mulohaza"),
        "description": L(
            "Learners give and receive feedback to and from their peers on where they are in their learning and what next steps could be taken.",
            "Обучающиеся дают и получают отзывы друг от друга о том, где они находятся в обучении и какие шаги сделать дальше.",
            "Oʻquvchilar bir-biriga oʻrganishdagi holati va keyingi qadamlar haqida fikr bildiradi va fikr oladi.",
        ),
        "hints": L(
            ["Create frequent opportunities to give and receive feedback on each other’s work.",
             "Learn to receive criticism and give constructive feedback.",
             "Use feedback to make learning visible and describe desired outcomes."],
            ["Часто давайте возможность обмениваться отзывами о работах друг друга.",
             "Учите принимать критику и давать конструктивную обратную связь.",
             "Используйте отзывы, чтобы сделать обучение видимым."],
            ["Bir-birining ishiga tez-tez fikr bildirish imkonini yarating.",
             "Tanqidni qabul qilish va konstruktiv fikr bildirishni oʻrgating.",
             "Oʻrganishni koʻrinadigan qilish uchun fikr-mulohazadan foydalaning."],
        ),
    },
    {
        "code": "self_reflection",
        "title": L("Self-reflection", "Саморефлексия", "Oʻz-oʻzini tahlil qilish"),
        "description": L(
            "Learners reflect on feedback and evidence to assess themselves against set criteria.",
            "Обучающиеся анализируют отзывы и свидетельства, оценивая себя по заданным критериям.",
            "Oʻquvchilar fikr-mulohaza va dalillar asosida oʻzini belgilangan mezonlar boʻyicha baholaydi.",
        ),
        "hints": L(
            ["Provide regular opportunities for learners to judge their achievements.",
             "Help learners identify standards or criteria to apply to their work.",
             "Train learners to evidence competence in different modes."],
            ["Регулярно давайте возможность оценивать свои достижения.",
             "Помогайте определить критерии для оценки своей работы.",
             "Учите подтверждать компетенции разными способами."],
            ["Oʻquvchilarga yutuqlarini muntazam baholash imkonini bering.",
             "Ishiga qoʻllanadigan mezonlarni aniqlashga yordam bering.",
             "Kompetensiyani turli shakllarda isbotlashni oʻrgating."],
        ),
    },
    {
        "code": "evidence",
        "title": L("Generating assessment evidence", "Создание доказательств компетенций", "Baholash uchun dalillar yaratish"),
        "description": L(
            "Learners use a variety of media to claim and give evidence for their competence, presenting to diverse audiences.",
            "Обучающиеся с помощью разных медиа заявляют и подтверждают свои компетенции перед разной аудиторией.",
            "Oʻquvchilar turli media vositalari orqali kompetensiyasini turli auditoriyaga namoyish etib isbotlaydi.",
        ),
        "hints": L(
            ["Help learners figure out which evidence is needed to demonstrate learning.",
             "Give learners choice and flexibility in presenting their learning.",
             "Use online tools as repositories of evidence."],
            ["Помогите понять, какие доказательства нужны.",
             "Дайте свободу выбора формы представления.",
             "Используйте онлайн-инструменты как хранилище доказательств."],
            ["Qanday dalillar kerakligini aniqlashga yordam bering.",
             "Natijani taqdim etish shaklini tanlash erkinligini bering.",
             "Dalillarni saqlash uchun onlayn vositalardan foydalaning."],
        ),
    },
    {
        "code": "authentic",
        "title": L("Authentic assessment", "Аутентичное оценивание", "Autentik baholash"),
        "description": L(
            "Learners apply what they have learned in a meaningful situation that mirrors real-world expectations, with real stakeholders.",
            "Обучающиеся применяют знания в значимой ситуации, отражающей реальные ожидания, с участием реальных людей.",
            "Oʻquvchilar bilimini real hayot talablariga mos, real ishtirokchilar bilan mazmunli vaziyatda qoʻllaydi.",
        ),
        "hints": L(
            ["Link assessment to real-world issues, problems and applications.",
             "Use simulations and role plays.",
             "Offer multiple opportunities to get feedback and refine work."],
            ["Связывайте оценивание с реальными проблемами.",
             "Используйте симуляции и ролевые игры.",
             "Давайте несколько возможностей получить отзыв и доработать."],
            ["Baholashni real muammolar bilan bogʻlang.",
             "Simulyatsiya va rolli oʻyinlardan foydalaning.",
             "Fikr olish va ishni yaxshilash uchun bir necha imkon bering."],
        ),
    },
    {
        "code": "automated",
        "title": L("Automated assessment", "Автоматизированное оценивание", "Avtomatlashtirilgan baholash"),
        "description": L(
            "Learners complete digital assessments that include feedback, reporting and/or portfolio functions.",
            "Обучающиеся проходят цифровые оценивания с обратной связью, отчётами и/или портфолио.",
            "Oʻquvchilar fikr-mulohaza, hisobot yoki portfolio funksiyalariga ega raqamli baholashlarni topshiradi.",
        ),
        "hints": L(
            ["Use feedback functions to give constructive feedback and next-step goals.",
             "Tailor teaching to learners’ needs using timely feedback.",
             "Create real-world scenarios to make competence visible."],
            ["Используйте обратную связь для конструктивных советов и следующих целей.",
             "Адаптируйте обучение с помощью своевременной обратной связи.",
             "Создавайте реальные сценарии, чтобы компетенции были видны."],
            ["Konstruktiv fikr va keyingi maqsadlar uchun fikr-mulohaza funksiyalaridan foydalaning.",
             "Oʻz vaqtidagi fikr-mulohaza asosida oʻqitishni moslashtiring.",
             "Kompetensiyani koʻrsatish uchun real vaziyatli topshiriqlar yarating."],
        ),
        "platform_note": L(
            "TeachX tests are automated assessment: instant grading, explanations and results for the teacher.",
            "Тесты TeachX — это автоматизированное оценивание: мгновенная проверка, пояснения и результаты для учителя.",
            "TeachX testlari — avtomatlashtirilgan baholash: darhol tekshirish, izohlar va oʻqituvchi uchun natijalar.",
        ),
    },
    {
        "code": "observation",
        "title": L("Observation", "Наблюдение", "Kuzatish"),
        "description": L(
            "Observe learners in action with a variety of methods to monitor progress, interest, competence, strengths and needs.",
            "Наблюдайте за обучающимися разными методами, отслеживая прогресс, интерес, компетенции, сильные стороны и потребности.",
            "Oʻquvchilarni turli usullar bilan kuzatib, rivojlanishi, qiziqishi, kompetensiyasi, kuchli tomonlari va ehtiyojlarini kuzating.",
        ),
        "hints": L(
            ["Create and follow an observation plan with a variety of techniques.",
             "Document observations with evidence to discuss with learners.",
             "Observe periodically to capture evidence of progress."],
            ["Составьте план наблюдения с разными техниками.",
             "Фиксируйте наблюдения и обсуждайте их с обучающимися.",
             "Наблюдайте регулярно, чтобы видеть прогресс."],
            ["Turli usullarni oʻz ichiga olgan kuzatuv rejasini tuzing.",
             "Kuzatuvlarni hujjatlashtirib, oʻquvchilar bilan muhokama qiling.",
             "Rivojlanishni koʻrish uchun muntazam kuzating."],
        ),
    },
    {
        "code": "questions",
        "title": L("Questions for learning", "Вопросы для обучения", "Oʻrganish uchun savollar"),
        "description": L(
            "Questioning builds trust and prompts learners to exchange ideas, refine thinking and improve performance.",
            "Вопросы укрепляют доверие и побуждают обмениваться идеями, уточнять мышление и улучшать результаты.",
            "Savollar ishonch hosil qiladi va oʻquvchilarni fikr almashishga, fikrlashni aniqlashtirishga undaydi.",
        ),
        "hints": L(
            ["Ask open questions to promote engagement and active learning.",
             "Sequence questions to build depth and complexity.",
             "Train learners to ask critical questions to themselves and others."],
            ["Задавайте открытые вопросы для вовлечения.",
             "Выстраивайте вопросы по нарастающей сложности.",
             "Учите задавать критические вопросы себе и другим."],
            ["Faollikni oshirish uchun ochiq savollar bering.",
             "Savollarni murakkablik boʻyicha ketma-ket tuzing.",
             "Oʻziga va boshqalarga tanqidiy savol berishni oʻrgating."],
        ),
    },
]


# --------------------------------------------------------------- competences

FRAMEWORKS = [
    {
        "code": "digcomp", "prefix": "d", "color": "#f97316", "icon": "💻",
        "title": L("Digital competence (DigComp)", "Цифровая компетенция (DigComp)", "Raqamli kompetensiya (DigComp)"),
        "competences": [
            L("Browsing, searching and filtering information", "Поиск и фильтрация информации", "Maʼlumotni qidirish va saralash"),
            L("Evaluating data, information and digital content", "Оценка данных и цифрового контента", "Maʼlumot va raqamli kontentni baholash"),
            L("Managing data, information and digital content", "Управление данными и контентом", "Maʼlumot va kontentni boshqarish"),
            L("Interacting through digital technologies", "Взаимодействие с помощью цифровых технологий", "Raqamli texnologiyalar orqali muloqot"),
            L("Sharing through digital technologies", "Обмен с помощью цифровых технологий", "Raqamli texnologiyalar orqali ulashish"),
            L("Engaging in citizenship through digital technologies", "Гражданское участие через цифровые технологии", "Raqamli texnologiyalar orqali fuqarolik faolligi"),
            L("Collaborating through digital technologies", "Сотрудничество с помощью цифровых технологий", "Raqamli texnologiyalar orqali hamkorlik"),
            L("Netiquette", "Сетевой этикет", "Tarmoq odobi"),
            L("Managing digital identity", "Управление цифровой идентичностью", "Raqamli shaxsni boshqarish"),
            L("Developing digital content", "Создание цифрового контента", "Raqamli kontent yaratish"),
            L("Integrating and re-elaborating digital content", "Интеграция и переработка контента", "Raqamli kontentni birlashtirish va qayta ishlash"),
            L("Copyright and licences", "Авторское право и лицензии", "Mualliflik huquqi va litsenziyalar"),
            L("Programming", "Программирование", "Dasturlash"),
            L("Protecting devices", "Защита устройств", "Qurilmalarni himoya qilish"),
            L("Protecting personal data and privacy", "Защита персональных данных", "Shaxsiy maʼlumotlarni himoya qilish"),
            L("Protecting health and well-being", "Защита здоровья и благополучия", "Salomatlik va farovonlikni himoya qilish"),
            L("Protecting the environment", "Защита окружающей среды", "Atrof-muhitni himoya qilish"),
            L("Solving technical problems", "Решение технических проблем", "Texnik muammolarni hal qilish"),
            L("Identifying needs and technological responses", "Определение потребностей и технологических решений", "Ehtiyoj va texnologik yechimlarni aniqlash"),
            L("Creatively using digital technologies", "Творческое использование технологий", "Raqamli texnologiyalardan ijodiy foydalanish"),
            L("Identifying digital competence gaps", "Выявление пробелов в цифровых навыках", "Raqamli koʻnikmalardagi boʻshliqlarni aniqlash"),
        ],
    },
    {
        "code": "entrecomp", "prefix": "e", "color": "#8b5cf6", "icon": "🚀",
        "title": L("Entrepreneurship (EntreComp)", "Предпринимательская компетенция (EntreComp)", "Tadbirkorlik kompetensiyasi (EntreComp)"),
        "competences": [
            L("Spotting opportunities", "Поиск возможностей", "Imkoniyatlarni koʻra bilish"),
            L("Creativity", "Креативность", "Ijodkorlik"),
            L("Vision", "Видение", "Kelajakni koʻrish"),
            L("Valuing ideas", "Оценка идей", "Gʻoyalarni qadrlash"),
            L("Ethical and sustainable thinking", "Этичное и устойчивое мышление", "Axloqiy va barqaror fikrlash"),
            L("Self-awareness and self-efficacy", "Самосознание и самоэффективность", "Oʻzini anglash va oʻziga ishonch"),
            L("Motivation and perseverance", "Мотивация и настойчивость", "Motivatsiya va qatʼiyat"),
            L("Mobilising resources", "Мобилизация ресурсов", "Resurslarni safarbar qilish"),
            L("Financial and economic literacy", "Финансовая и экономическая грамотность", "Moliyaviy va iqtisodiy savodxonlik"),
            L("Mobilising others", "Вовлечение других", "Boshqalarni safarbar qilish"),
            L("Taking the initiative", "Инициативность", "Tashabbuskorlik"),
            L("Planning and management", "Планирование и управление", "Rejalashtirish va boshqaruv"),
            L("Coping with uncertainty, ambiguity and risk", "Работа с неопределённостью и риском", "Noaniqlik va xavf bilan ishlash"),
            L("Working with others", "Работа с другими", "Boshqalar bilan ishlash"),
            L("Learning through experience", "Обучение на опыте", "Tajriba orqali oʻrganish"),
        ],
    },
    {
        "code": "lifecomp", "prefix": "l", "color": "#a3e635", "icon": "🌱",
        "title": L("Personal, social & learning to learn (LifeComp)", "Личностные, социальные и учебные (LifeComp)", "Shaxsiy, ijtimoiy va oʻrganishni oʻrganish (LifeComp)"),
        "competences": [
            L("Self-regulation", "Саморегуляция", "Oʻzini boshqarish"),
            L("Flexibility", "Гибкость", "Moslashuvchanlik"),
            L("Wellbeing", "Благополучие", "Farovonlik"),
            L("Empathy", "Эмпатия", "Hamdardlik"),
            L("Communication", "Коммуникация", "Muloqot"),
            L("Collaboration", "Сотрудничество", "Hamkorlik"),
            L("Growth mindset", "Мышление роста", "Oʻsish tafakkuri"),
            L("Critical thinking", "Критическое мышление", "Tanqidiy fikrlash"),
            L("Managing learning", "Управление обучением", "Oʻrganishni boshqarish"),
        ],
    },
    {
        "code": "greencomp", "prefix": "g", "color": "#22c55e", "icon": "🌍",
        "title": L("Sustainability / green (GreenComp)", "Устойчивое развитие / «зелёные» (GreenComp)", "Barqarorlik / „yashil“ (GreenComp)"),
        "competences": [
            L("Valuing sustainability", "Ценность устойчивости", "Barqarorlikni qadrlash"),
            L("Supporting fairness", "Поддержка справедливости", "Adolatni qoʻllab-quvvatlash"),
            L("Promoting nature", "Забота о природе", "Tabiatni asrash"),
            L("Systems thinking", "Системное мышление", "Tizimli fikrlash"),
            L("Critical thinking", "Критическое мышление", "Tanqidiy fikrlash"),
            L("Problem framing", "Постановка проблемы", "Muammoni shakllantirish"),
            L("Futures literacy", "Грамотность в отношении будущего", "Kelajak savodxonligi"),
            L("Adaptability", "Адаптивность", "Moslashish qobiliyati"),
            L("Exploratory thinking", "Исследовательское мышление", "Izlanuvchan fikrlash"),
            L("Political agency", "Гражданская активность", "Fuqarolik faolligi"),
            L("Collective action", "Коллективные действия", "Jamoaviy harakat"),
            L("Individual initiative", "Личная инициатива", "Shaxsiy tashabbus"),
        ],
    },
]

TRANSVERSAL = [
    {"code": "critical_thinking", "icon": "🧐", "title": L("Critical thinking", "Критическое мышление", "Tanqidiy fikrlash")},
    {"code": "analytical", "icon": "📊", "title": L("Analytical skills", "Аналитические навыки", "Tahliliy koʻnikmalar")},
    {"code": "problem_solving", "icon": "🧩", "title": L("Problem solving", "Решение проблем", "Muammolarni hal qilish")},
    {"code": "creativity", "icon": "💡", "title": L("Creativity", "Креативность", "Ijodkorlik")},
    {"code": "teamwork", "icon": "🤝", "title": L("Teamwork", "Работа в команде", "Jamoada ishlash")},
    {"code": "intercultural", "icon": "🌐", "title": L("Intercultural skills", "Межкультурные навыки", "Madaniyatlararo koʻnikmalar")},
    {"code": "communication", "icon": "🗣️", "title": L("Communication and negotiation", "Коммуникация и переговоры", "Muloqot va muzokara")},
]


# ------------------------------------------------ setting cards & the 9 steps

SETTING_CARDS = [
    {"code": "duration", "title": L("Duration", "Длительность", "Davomiyligi"),
     "question": L("How long will the activity last?", "Сколько продлится занятие?", "Mashgʻulot qancha davom etadi?")},
    {"code": "aim", "title": L("Aim", "Цель", "Maqsad"),
     "question": L("What is the aim of the activity?", "Какова цель занятия?", "Mashgʻulotning maqsadi nima?")},
    {"code": "audience", "title": L("Target audience", "Целевая аудитория", "Maqsadli auditoriya"),
     "question": L("Who are the learners and how many?", "Кто обучающиеся и сколько их?", "Oʻquvchilar kimlar va nechta?")},
    {"code": "needs", "title": L("Needs", "Потребности", "Ehtiyojlar"),
     "question": L("What needs of the learners will be addressed?", "Какие потребности обучающихся учитываются?", "Oʻquvchilarning qaysi ehtiyojlari hisobga olinadi?")},
    {"code": "resources", "title": L("Resources", "Ресурсы", "Resurslar"),
     "question": L("What resources, equipment or people are available?", "Какие ресурсы, оборудование или люди доступны?", "Qanday resurslar, jihozlar yoki odamlar mavjud?")},
    {"code": "space", "title": L("Space", "Пространство", "Joy"),
     "question": L("Where will the lesson take place (classroom, lab, online)?", "Где пройдёт занятие (класс, лаборатория, онлайн)?", "Dars qayerda oʻtadi (sinf, laboratoriya, onlayn)?")},
    {"code": "real_world", "title": L("Real-world links", "Связь с реальной жизнью", "Real hayot bilan bogʻliqlik"),
     "question": L("What real-life issues will be addressed?", "Какие реальные проблемы будут затронуты?", "Qaysi real hayotiy muammolar koʻrib chiqiladi?")},
]

STEPS = [
    L("Define the setting with the Setting cards", "Определите условия с помощью карточек «Условия»", "„Sharoit“ kartalari bilan sharoitni belgilang"),
    L("Lay down the Planning cards", "Разложите карточки планирования", "Rejalashtirish kartalarini joylashtiring"),
    L("Choose the Competence cards (at least three)", "Выберите карточки компетенций (не менее трёх)", "Kompetensiya kartalarini tanlang (kamida uchta)"),
    L("Appraise the starting level with an assessment method", "Оцените стартовый уровень одним из методов оценивания", "Boshlangʻich darajani baholash usuli bilan aniqlang"),
    L("Select the teaching method", "Выберите метод обучения", "Oʻqitish usulini tanlang"),
    L("Establish the desired output / evidence", "Определите ожидаемый результат / доказательства", "Kutilgan natija / dalillarni belgilang"),
    L("Pick the assessment method", "Выберите метод оценивания", "Baholash usulini tanlang"),
    L("Gather the necessary resources", "Соберите необходимые ресурсы", "Kerakli resurslarni toʻplang"),
    L("Draft the lesson plan (timeline)", "Составьте план урока (хронологию)", "Dars rejasini (vaqt jadvalini) tuzing"),
]


# ------------------------------------------------------------------- lookups

def competence_catalog():
    """Flat list of {code, framework, title} for every competence, with deck-style codes (d.1, e.15, ...)."""
    items = []
    for fw in FRAMEWORKS:
        for i, title in enumerate(fw["competences"], start=1):
            items.append({"code": f"{fw['prefix']}.{i}", "framework": fw["code"], "title": title})
    return items


COMPETENCES = {c["code"]: c for c in competence_catalog()}
METHODS_BY_CODE = {m["code"]: m for m in TEACHING_METHODS}
ASSESSMENTS_BY_CODE = {a["code"]: a for a in ASSESSMENT_METHODS}
TRANSVERSAL_BY_CODE = {t["code"]: t for t in TRANSVERSAL}
PRINCIPLES_BY_CODE = {p["code"]: p for p in PRINCIPLES}


def localized(lang):
    """All SCAFFOLD content resolved into one language, ready for templates."""
    def card(obj, **extra_keys):
        out = {"code": obj["code"]}
        for key, value in obj.items():
            if key == "code":
                continue
            if isinstance(value, dict) and "en" in value:
                out[key] = tr(value, lang)
            elif isinstance(value, list) and value and isinstance(value[0], dict) and "en" in value[0]:
                out[key] = [tr(v, lang) for v in value]
            else:
                out[key] = value
        return out

    frameworks = []
    for fw in FRAMEWORKS:
        entry = card(fw)
        entry["competences"] = [
            {"code": f"{fw['prefix']}.{i}", "title": tr(title, lang)}
            for i, title in enumerate(fw["competences"], start=1)
        ]
        frameworks.append(entry)

    principles = []
    for p in PRINCIPLES:
        entry = card(p)
        entry["try_method_title"] = tr(METHODS_BY_CODE[p["try_method"]]["title"], lang)
        entry["try_assessment_titles"] = [tr(ASSESSMENTS_BY_CODE[a]["title"], lang) for a in p["try_assessments"]]
        principles.append(entry)

    return {
        "principles": principles,
        "methods": [card(m) for m in TEACHING_METHODS],
        "assessments": [card(a) for a in ASSESSMENT_METHODS],
        "frameworks": frameworks,
        "transversal": [card(t) for t in TRANSVERSAL],
        "setting_cards": [card(s) for s in SETTING_CARDS],
        "steps": [tr(s, lang) for s in STEPS],
    }


def english_digest():
    """Compact English description of the toolkit for the AI lesson-design prompt."""
    lines = ["TEACHING METHODS (code: title — description):"]
    for m in TEACHING_METHODS:
        lines.append(f"- {m['code']}: {m['title']['en']} — {m['description']['en']} Steps: " + "; ".join(m["steps"]["en"]))
    lines.append("\nASSESSMENT METHODS (code: title — description):")
    for a in ASSESSMENT_METHODS:
        lines.append(f"- {a['code']}: {a['title']['en']} — {a['description']['en']}")
    lines.append("\nPRINCIPLES and their suggested method + assessment pairings:")
    for p in PRINCIPLES:
        lines.append(f"- {p['code']}: {p['title']['en']} (try {p['try_method']} with {', '.join(p['try_assessments'])})")
    return "\n".join(lines)
