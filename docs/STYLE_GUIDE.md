# Persian Translation Style Guide — Steins;Gate

## 1. General Principles

- **Target audience:** Iranian visual novel fans, ages 16-35, familiar with anime/gaming culture
- **Register:** Natural conversational Persian, not overly formal. Match the character's tone.
- **Source priority:** Japanese is the primary source; English (Steam official) is the pivot/secondary reference
- **Translation approach:** Dynamic equivalence — convey meaning and emotion, not literal word-for-word

## 2. Character Voice Guide

| Character | Personality | Persian Voice |
|-----------|------------|---------------|
| Okabe Rintaro | Grandiose, chuunibyou, dramatic | حماسی و نمایشی — با اصطلاحات بزرگ‌نمایی مثل «نقاب‌دار» و «ارتش نظم تک‌جهانی» |
| Mayuri | Innocent, cheerful, childlike | ساده و معصوم — جملات کوتاه، لحن کودکانه |
| Kurisu | Intellectual, tsundere, sarcastic | هوشمند و کنایه‌آمیز — اصطلاحات علمی دقیق |
| Daru | Otaku hacker, perverted humor | گیک و شوخ — اسلنگ اینترنتی، شوخی‌های آگاهانه |
| Suzuha | Serious, determined, soldier-like | جدی و قاطع — جملات نظامی‌وار |
| Moeka | Shy, phone-obsessed, quiet | کم‌حرف و مضطرب — جملات قطعه‌قطعه |
| Faris | Cat-like, playful, mew-mew | بازیگوش و گربه‌وار — با پسوندهای `-نیا` |
| Luka | Feminine, gentle, timid | ظریف و محجوب — لحن مؤدبانه |

## 3. Terminology Rules

### 3.1 Core Terms (MANDATORY — do not deviate)

| Japanese | English | Persian (locked) | Notes |
|----------|---------|-------------------|-------|
| 世界線 | Worldline | خط جهان | Physics term — always «خط جهان» |
| 世界線変動率 | Divergence rate | نرخ انحراف خط جهان | |
| ダイアルアップ | D-Mail | دی‌میل | Keep as transliteration — it's a proper noun |
| タイムリープ | Time Leap | جهش زمانی | |
| タイムマシン | Time Machine | ماشین زمان | |
| 読心 | Reading Steiner | ریدینگ اشتاینر | Keep Okabe's ability name in phonetic form |
| ラボメン | Lab Member | عضو آزمایشگاه | |
| 未来ガジェット | Future Gadget | گجت آینده | |
| 電話レンジ（仮） | PhoneWave (name pending) | فون‌ویو (نام موقت) | |
| IBN 5100 | IBN 5100 | IBM ۵۱۰۰ | Use real name — it's a real computer |
| @チャンネル | @channel | @چنل | Transliterate — it's a fictional 2ch |
| ニコ動 | Niconico | نیکوکو | |

### 3.2 Scientific Terms

| Japanese | Persian | Notes |
|----------|---------|-------|
| ブラックホール | سیاه‌چاله | |
| タキオン | تاکیون | |
| ジョン・タイター | جان تایتور | |
| ニュートリノ | نوترینو | |
| 量子力学 | مکانیک کوانتوم | |
| 並行世界 | جهان موازی | |
| 特異点 | تکینگی | |

## 4. Formatting Rules

### 4.1 Punctuation
- Use Persian numerals (۱۲۳۴۵۶۷۸۹۰) in dialog
- Use Persian quotation marks («») for speech
- Use «ـ» (ZWNJ) between words that shouldn't join: «می‌رود» not «میرود»
- Keep Latin terms in LTR within RTL text: D-Mail, IBN 5100, SERN

### 4.2 Honorifics
- Keep Japanese honorifics untranslated: «اوکابه‌سنپای», «مایوری‌شان»
- Transliterate names phonetically: اوکابه رینتارو، ماکاره کوریسو، آمانه سوزوها

### 4.3 Code/System Text
- Menu items: short, imperative form: «شروع بازی», «بارگذاری», «تنظیمات»
- System messages: polite but concise: «ذخیره شد», «خطا در بارگذاری»
- D-Mail subject lines: keep under 20 characters

## 5. Text Expansion Management

- **Hard limit:** Persian text must not exceed 1.5x the Japanese character count per string
- **Strategies:** Use abbreviations, drop redundant politeness markers, merge clauses
- **Line breaks:** Use `\n` in SCX to split long dialog into multiple clicks
- **Never truncate meaning** — if a string is too long, split the dialog across multiple display windows

## 6. Quality Checklist (per string)

- [ ] Meaning preserved (no information lost)
- [ ] Character voice maintained
- [ ] Terminology matches glossary
- [ ] No text expansion beyond 1.5x
- [ ] ZWNJ used correctly
- [ ] Latin terms wrapped in LRM markers
- [ ] No machine-translation-only output (all strings reviewed by human)
- [ ] D-Mail keywords validated against trigger table
