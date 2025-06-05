# main.py - Full Desktop Application for Poem Analysis
import tkinter as tk
from tkinter import scrolledtext, ttk, font, messagebox, colorchooser, simpledialog
from PIL import Image, ImageTk
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
import string
from nltk.corpus import cmudict, stopwords
from googletrans import Translator
import os
import time
from collections import defaultdict
from spellchecker import SpellChecker  # For spell checking

# --- Download NLTK Resources ---
nltk_resource_map = {
    'tokenizers/punkt': 'punkt',
    'taggers/averaged_perceptron_tagger': 'averaged_perceptron_tagger',
    'sentiment/vader_lexicon.zip': 'vader_lexicon',
    'corpora/cmudict.zip': 'cmudict',
    'corpora/stopwords': 'stopwords'
}

for path_to_find, download_id in nltk_resource_map.items():
    try:
        nltk.data.find(path_to_find)
        print(f"NLTK resource '{download_id}' (checked at '{path_to_find}') found.")
    except LookupError:
        print(
            f"NLTK resource '{download_id}' (path: '{path_to_find}') not found. Attempting to download '{download_id}'...")
        try:
            nltk.download(download_id)
            print(f"Successfully downloaded NLTK resource '{download_id}'.")
            nltk.data.find(path_to_find)  # Re-verify
            print(f"Verified '{download_id}' (path: '{path_to_find}') after download.")
        except Exception as e_download:
            print(f"Error downloading or verifying NLTK resource '{download_id}'. Error: {e_download}")
            print(
                f"Please try manually downloading it: open a Python console and run:\nimport nltk\nnltk.download('{download_id}')")
            if download_id in ['punkt', 'averaged_perceptron_tagger', 'vader_lexicon', 'stopwords']:
                raise RuntimeError(
                    f"Critical NLTK resource '{download_id}' could not be obtained. Application cannot continue.") from e_download

try:
    pronouncing_dict = cmudict.dict()
except LookupError:
    print(
        "Warning: CMU Pronouncing Dictionary (cmudict.dict()) failed to load. Rhyme/syllable analysis may be limited.")
    pronouncing_dict = {}

try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    print("Warning: NLTK English Stopwords not found/loaded. Some text processing features might be affected.")
    stop_words = set()

translator = Translator()
spell = SpellChecker()

# --- UI Theming and Fonts ---
# To use a "Wednesday series font" for the title, replace "Georgia" with the exact name of that font
# Ensure the font is installed on your system.
APP_TITLE_FONT_FAMILY = "Georgia"  # Example: "Wednesday Addams Font Name" or "Garamond"
APP_TITLE_FONT = (APP_TITLE_FONT_FAMILY, 26, "bold")  # Increased size
HEADING_FONT = ("Segoe UI Semibold", 16)
SUBHEADING_FONT = ("Segoe UI", 12, "bold")
BODY_FONT_FAMILY = "Segoe UI"
BODY_FONT_SIZE = 11
BODY_FONT_STYLE = "normal"  # Can be "bold", "italic", "bold italic"
BODY_FONT_COLOR = "#343A40"  # Initial text color
BODY_FONT = (BODY_FONT_FAMILY, BODY_FONT_SIZE, BODY_FONT_STYLE)
ITALIC_FONT = ("Segoe UI Italic", 10)
BUTTON_FONT = ("Segoe UI Semibold", 10)
SMALL_TEXT_FONT = ("Segoe UI", 9)  # Added definition for SMALL_TEXT_FONT

# Available font families for user selection (common system fonts)
AVAILABLE_FONT_FAMILIES = ["Arial", "Times New Roman", "Verdana", "Courier New", "Georgia", "Palatino Linotype",
                           "Segoe UI"]

# Color Palette
COLOR_PRIMARY_BG_CANVAS = "#EAE7DC"
COLOR_FRAME_BG = "#F8F9FA"
COLOR_SECONDARY_BG = "#FFFFFF"
COLOR_TEXT_PRIMARY = BODY_FONT_COLOR
COLOR_TEXT_SECONDARY = "#6C757D"
COLOR_ACCENT = "#5E8B7E"
COLOR_ACCENT_HOVER = "#4F7A6C"
COLOR_ACCENT_PRESSED = "#3E6055"
COLOR_BUTTON_SECONDARY_BG = "#D8C3A5"
COLOR_BUTTON_SECONDARY_HOVER = "#C6B192"
COLOR_BORDER = "#BFB08F"

# --- POS Tag Mapping for Human-Readable Output ---
POS_CATEGORY_MAP = {
    'NN': 'Noun', 'NNS': 'Noun (Plural)', 'NNP': 'Proper Noun', 'NNPS': 'Proper Noun (Plural)',
    'VB': 'Verb (Base Form)', 'VBD': 'Verb (Past Tense)', 'VBG': 'Verb (Gerund/Present Participle)',
    'VBN': 'Verb (Past Participle)', 'VBP': 'Verb (Non-3rd Person Singular Present)',
    'VBZ': 'Verb (3rd Person Singular Present)',
    'JJ': 'Adjective', 'JJR': 'Adjective (Comparative)', 'JJS': 'Adjective (Superlative)',
    'RB': 'Adverb', 'RBR': 'Adverb (Comparative)', 'RBS': 'Adverb (Superlative)', 'WRB': 'Adverb (Wh-)',
    'PRP': 'Pronoun (Personal)', 'PRP$': 'Pronoun (Possessive)', 'WP': 'Pronoun (Wh-)',
    'WP$': 'Pronoun (Possessive Wh-)',
    'IN': 'Preposition/Subordinating Conjunction', 'DT': 'Determiner', 'CC': 'Conjunction (Coordinating)',
    'CD': 'Cardinal Number', 'EX': 'Existential There', 'FW': 'Foreign Word', 'LS': 'List Item Marker',
    'MD': 'Modal', 'PDT': 'Predeterminer', 'POS': 'Possessive Ending', 'RP': 'Particle',
    'SYM': 'Symbol', 'TO': 'To', 'UH': 'Interjection',
}


# --- Core Functions ---
def count_syllables_in_word(word):
    if not word: return 0
    word_lower = word.lower()
    if pronouncing_dict and word_lower in pronouncing_dict:
        return max([len([syl for syl in pron if syl[-1].isdigit()]) for pron in pronouncing_dict[word_lower]])
    word_lower = re.sub(r"[^a-z]", "", word_lower)
    if not word_lower: return 0
    if len(word_lower) <= 3: return 1
    if word_lower.endswith('e') and len(re.findall(r'[aeiouy]', word_lower[:-1])) > 0:
        word_lower = word_lower[:-1]
    vowel_groups = re.findall(r'[aeiouy]+', word_lower)
    count = len(vowel_groups)
    if word_lower.endswith('le') and len(word_lower) > 2 and word_lower[-3] not in 'aeiouy':
        if len(re.findall(r'[aeiouy]', word_lower[:-2])) > 0: count += 1
    if count == 0 and len(word_lower) > 0: return 1
    return count if count > 0 else 1


def count_syllables_in_line(line_text):
    words = word_tokenize(line_text)
    return sum(count_syllables_in_word(word) for word in words)


def analyze_parts_of_speech_grouped(text):
    words = word_tokenize(text)
    tagged_words = pos_tag(words)
    grouped_pos = defaultdict(list)
    for word, tag in tagged_words:
        category = POS_CATEGORY_MAP.get(tag, tag)
        if word.isalnum(): grouped_pos[category].append(word)
    for category in grouped_pos:
        grouped_pos[category] = sorted(list(set(grouped_pos[category])))
    return grouped_pos


def get_detailed_tone(text, sentiment_compound_score):
    text_lower, words = text.lower(), word_tokenize(text.lower())
    current_stop_words = stop_words if stop_words else set()
    words = [w for w in words if w.isalpha() and w not in current_stop_words]
    if sentiment_compound_score >= 0.05:
        if any(k in words for k in ["love", "heart", "passion", "darling", "beloved", "kiss", "adore",
                                    "cherish"]): return "Romantic / Affectionate"
        if any(k in words for k in ["joy", "happy", "smile", "laugh", "glee", "delight", "celebrate",
                                    "elation"]): return "Joyful / Celebratory"
        if any(k in words for k in
               ["hope", "dream", "future", "believe", "dawn", "aspire", "faith"]): return "Hopeful / Optimistic"
        if any(k in words for k in ["nature", "beauty", "serene", "peace", "calm", "meadow", "stars", "moon", "sun",
                                    "wonder"]): return "Reflective / Nature-focused (Positive)"
        return "Generally Positive"
    elif sentiment_compound_score <= -0.05:
        if any(k in words for k in ["sad", "sorrow", "tear", "cry", "grief", "lost", "lonely", "mourn",
                                    "despair"]): return "Sad / Melancholic"
        if any(k in words for k in ["anger", "hate", "rage", "fury", "resent", "fight", "war", "scorn",
                                    "bitter"]): return "Angry / Conflict-focused"
        if any(k in words for k in
               ["fear", "scared", "terror", "horror", "anxious", "dark", "shadow", "dread"]): return "Fearful / Anxious"
        if any(k in words for k in ["loss", "end", "farewell", "past", "memory", "forgotten", "vanish",
                                    "fade"]): return "Nostalgic / Reflecting on Loss"
        return "Generally Negative"
    else:
        if any(k in words for k in ["observe", "describe", "think", "ponder", "question", "world", "life", "examine",
                                    "consider"]): return "Observational / Contemplative"
        return "Neutral / Descriptive"


def generate_interpretive_summary(overall_sentiment, detailed_tone, poem_text_lower):
    summary = f"The poem's overall emotional leaning appears to be {overall_sentiment.lower()}."
    summary += f" The predominant tone detected is '{detailed_tone}'.\n\n"
    summary += "This suggests the poem might be exploring themes of...\n"
    # ... (interpretive summary logic remains the same) ...
    if detailed_tone == "Romantic / Affectionate":
        summary += "...deep affection, love, or passionate connection. It could be celebrating a cherished bond or expressing heartfelt adoration for someone or something."
    elif detailed_tone == "Joyful / Celebratory":
        summary += "...happiness, elation, or celebration. It might be capturing a moment of triumph, pure joy, or a festive spirit, aiming to uplift."
    elif detailed_tone == "Hopeful / Optimistic":
        summary += "...hope, positive expectation, or belief in a brighter future. It might inspire perseverance or look forward with a sense of aspiration."
    elif detailed_tone == "Reflective / Nature-focused (Positive)":
        summary += "...the beauty and serenity of the natural world to evoke positive feelings. It could be a calm contemplation, finding peace or wonder in nature's elements."
    elif detailed_tone == "Generally Positive":
        summary += "...a general sense of positivity. While the specific focus might be varied, it aims to leave a pleasant or uplifted impression."
    elif detailed_tone == "Sad / Melancholic":
        summary += "...sadness, sorrow, or introspection on more somber emotions. It might grapple with loss, loneliness, or a sense of despair."
        if "flower" in poem_text_lower and ("die" in poem_text_lower or "wilt" in poem_text_lower) and (
                "water" in poem_text_lower or "thirst" in poem_text_lower or "neglect" in poem_text_lower):
            summary += "\n\nFor instance, if there's imagery like a 'flower dying from lack of water,' this could metaphorically represent a relationship or hope fading due to neglect, the pain of an unmet need, or the consequences of emotional 'thirst' – much like a personal connection withering without care or affirmation."
        elif (
                "reject" in poem_text_lower or "alone" in poem_text_lower or "unloved" in poem_text_lower or "abandon" in poem_text_lower) and not (
                "not alone" in poem_text_lower):
            summary += "\n\nIt might also touch upon feelings of rejection, isolation, or the pain of being unwanted, exploring the ache of solitude or the sting of abandonment."
    elif detailed_tone == "Angry / Conflict-focused":
        summary += "...strong emotions like anger, resentment, or a sense of conflict. It might be challenging an injustice, expressing frustration, or depicting an internal or external struggle."
    elif detailed_tone == "Fearful / Anxious":
        summary += "...fear, anxiety, or dread. The poem could be exploring a threatening situation, an inner turmoil, or the unsettling nature of the unknown."
    elif detailed_tone == "Nostalgic / Reflecting on Loss":
        summary += "...the past, perhaps with longing or wistfulness, often tinged with the sadness of something lost, changed, or gone forever. Themes of memory and impermanence are likely."
        if "fade" in poem_text_lower or "vanish" in poem_text_lower or "gone" in poem_text_lower or "no more" in poem_text_lower:
            summary += "\n\nImagery of things fading or disappearing might emphasize the transient nature of experiences, relationships, or even life itself."
    elif detailed_tone == "Generally Negative":
        summary += "...a general sense of negativity. The specific reasons might vary, but it likely evokes feelings of discomfort, dissatisfaction, or concern."
    elif detailed_tone == "Observational / Contemplative":
        summary += "...a detached or thoughtful stance, observing aspects of life, the world, or human nature. It likely encourages reflection rather than strong emotional display."
    elif detailed_tone == "Neutral / Descriptive":
        summary += "...describing a scene, person, or event without a strong emotional charge. Its primary aim might be to paint a vivid picture or present observations objectively."
    return summary


def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    vs = analyzer.polarity_scores(text)
    overall_sentiment = "Neutral"
    if vs['compound'] >= 0.05:
        overall_sentiment = "Positive"
    elif vs['compound'] <= -0.05:
        overall_sentiment = "Negative"
    detailed_tone = get_detailed_tone(text, vs['compound'])
    interpretive_summary = generate_interpretive_summary(overall_sentiment, detailed_tone, text.lower())
    return overall_sentiment, detailed_tone, interpretive_summary


def identify_figures_of_speech(text):
    figures, sentences = [], sent_tokenize(text)
    inanimate_keywords = ["wind", "moon", "stars", "trees", "sun", "time", "river", "ocean", "mountain", "earth"]
    human_verbs = ["whispered", "sang", "danced", "cried", "laughed", "spoke", "wept", "sighed", "called"]
    for sentence_text in sentences:
        original_sentence_strip, sentence_lower = sentence_text.strip(), sentence_text.lower()
        tokenized_sentence, tagged_sentence = word_tokenize(sentence_lower), pos_tag(word_tokenize(sentence_lower))
        for i, (word, tag) in enumerate(tagged_sentence):
            if word in inanimate_keywords and tag.startswith("NN"):
                limit = min(len(tagged_sentence), i + 4)
                for k in range(i + 1, limit):
                    next_word, next_tag = tagged_sentence[k]
                    if next_tag.startswith("VB") and next_word in human_verbs:
                        figures.append(
                            f"Personification: \"{word.capitalize()} {next_word}\" (in \"{original_sentence_strip}\")");
                        break
        if " like " in sentence_lower: figures.append(f"Simile (using 'like'): Found in \"{original_sentence_strip}\"")
        for match in re.finditer(r'\b(as\s+\w+\s+as)\b', sentence_lower):
            if len(match.group(1).split()) == 3: figures.append(
                f"Simile (using 'as...as'): \"{match.group(1)}\" in \"{original_sentence_strip}\"")
        words_in_sentence = [w for w in tokenized_sentence if w.isalpha() and len(w) > 1]
        if len(words_in_sentence) > 2:
            for i in range(len(words_in_sentence) - 1):
                if words_in_sentence[i][0] == words_in_sentence[i + 1][0] and words_in_sentence[i][0] not in 'aeiou':
                    if i + 2 < len(words_in_sentence) and words_in_sentence[i + 2][0] == words_in_sentence[i][0]:
                        figures.append(
                            f"Alliteration: e.g., \"{words_in_sentence[i]} {words_in_sentence[i + 1]} {words_in_sentence[i + 2]}\" in \"{original_sentence_strip}\"");
                        break
                    elif i + 2 >= len(words_in_sentence):
                        figures.append(
                            f"Alliteration: e.g., \"{words_in_sentence[i]} {words_in_sentence[i + 1]}\" in \"{original_sentence_strip}\""); break
    return list(set(figures))


def get_last_word_from_line(line):
    line = line.strip().rstrip(string.punctuation);
    words = line.split()
    return words[-1].lower() if words else None


def get_rhyme_sound_cmu(word):
    if not word or not pronouncing_dict: return None
    word_lower = word.lower()
    if word_lower in pronouncing_dict:
        for pron in pronouncing_dict[word_lower]:
            for i in range(len(pron)):
                if '1' in pron[i] or '2' in pron[i]: return tuple(p.rstrip('012') for p in pron[i:])
            return tuple(p.rstrip('012') for p in pron[-2:])
    return word[-3:]


def analyze_rhyme_scheme_and_words(text):
    lines = [line for line in text.split('\n') if line.strip()]
    if len(lines) < 1: return "N/A (Not enough lines)", {}, []
    last_words = [get_last_word_from_line(line) for line in lines]
    sounds = [get_rhyme_sound_cmu(word) if word else None for word in last_words]
    rhyme_groups, labels, label_map, current_label_char_code = {}, [], {}, ord('A')
    for i, sound in enumerate(sounds):
        current_last_word = last_words[i]
        if current_last_word is None: labels.append("-"); continue
        if sound is None:
            unique_non_rhyme_label = f"X{len(label_map)}"
            labels.append(unique_non_rhyme_label);
            label_map[sound] = unique_non_rhyme_label
            rhyme_groups[unique_non_rhyme_label] = [current_last_word];
            continue
        found_match = False
        for s_key, lbl in label_map.items():
            if s_key is not None and sound == s_key:
                labels.append(lbl);
                rhyme_groups[lbl].append(current_last_word);
                found_match = True;
                break
        if not found_match:
            new_label = chr(current_label_char_code)
            label_map[sound] = new_label;
            labels.append(new_label)
            rhyme_groups[new_label] = [current_last_word];
            current_label_char_code += 1
            if current_label_char_code > ord('Z'): current_label_char_code = ord('a')
    scheme_str = "".join(labels)
    rhyming_words_display = {k: list(set(v)) for k, v in rhyme_groups.items() if
                             len(list(set(v))) > 1 and not k.startswith("X")}
    return scheme_str, rhyming_words_display, lines


def identify_poem_type(text):
    scheme, _, lines_raw = analyze_rhyme_scheme_and_words(text)
    lines = [line for line in text.split('\n') if line.strip()]
    num_lines = len(lines)
    if num_lines == 0: return "Unknown (No text provided)"
    syllables_per_line = [count_syllables_in_line(line) for line in lines_raw]
    poem_types = []
    if num_lines == 3 and syllables_per_line == [5, 7, 5]: poem_types.append("Haiku")
    if num_lines == 5 and len(scheme) == 5 and scheme[0] == scheme[1] == scheme[4] and scheme[2] == scheme[3] and \
            scheme[0] != scheme[2]:
        if (7 <= syllables_per_line[0] <= 10 and 7 <= syllables_per_line[1] <= 10 and 7 <= syllables_per_line[
            4] <= 10 and \
                5 <= syllables_per_line[2] <= 7 and 5 <= syllables_per_line[3] <= 7): poem_types.append("Limerick")
    if num_lines == 14:
        if len(scheme) == 14 and scheme[0] == scheme[2] and scheme[1] == scheme[3] and scheme[0] != scheme[1] and \
                scheme[4] == scheme[6] and scheme[5] == scheme[7] and scheme[4] != scheme[5] and scheme[0] != scheme[
            4] and \
                scheme[8] == scheme[10] and scheme[9] == scheme[11] and scheme[8] != scheme[9] and scheme[4] != scheme[
            8] and \
                scheme[12] == scheme[13] and scheme[8] != scheme[12]:
            poem_types.append("Sonnet (likely Shakespearean)")
        elif len(scheme) == 14 and scheme[0] == scheme[3] == scheme[4] == scheme[7] and scheme[1] == scheme[2] == \
                scheme[5] == scheme[6] and scheme[0] != scheme[1] and \
                ((scheme[8] == scheme[10] == scheme[12] and scheme[9] == scheme[11] == scheme[13] and scheme[8] !=
                  scheme[9]) or \
                 (scheme[8] == scheme[11] and scheme[9] == scheme[12] and scheme[10] == scheme[13] and scheme[8] !=
                  scheme[9] and scheme[9] != scheme[10])):
            poem_types.append("Sonnet (likely Petrarchan)")
        else:
            poem_types.append("Sonnet (Unspecified or other form)")
    if not poem_types:
        if all(s == '-' or s.startswith('X') for s in scheme) and num_lines > 1:
            poem_types.append("Free Verse")
        elif num_lines > 1:
            poem_types.append("Rhyming Verse (specific form undetermined)")
        else:
            poem_types.append("Short Verse / Stanza")
    return ", ".join(poem_types) if poem_types else "Undetermined Form"


def translate_poem(text, lang='en'):
    try:
        return translator.translate(text, dest=lang).text
    except Exception as e:
        return f"Translation error: {str(e)}"


LANGUAGES = {
    'Afrikaans': 'af', 'Albanian': 'sq', 'Amharic': 'am', 'Arabic': 'ar', 'Armenian': 'hy', 'Assamese': 'as',
    'Aymara': 'ay', 'Azerbaijani': 'az',
    'Bambara': 'bm', 'Basque': 'eu', 'Belarusian': 'be', 'Bengali': 'bn', 'Bhojpuri': 'bho', 'Bosnian': 'bs',
    'Bulgarian': 'bg', 'Catalan': 'ca',
    'Cebuano': 'ceb', 'Chichewa': 'ny', 'Chinese (Simplified)': 'zh-cn', 'Chinese (Traditional)': 'zh-tw',
    'Corsican': 'co', 'Croatian': 'hr',
    'Czech': 'cs', 'Danish': 'da', 'Dhivehi': 'dv', 'Dogri': 'doi', 'Dutch': 'nl', 'English': 'en', 'Esperanto': 'eo',
    'Estonian': 'et', 'Ewe': 'ee',
    'Filipino': 'tl', 'Finnish': 'fi', 'French': 'fr', 'Frisian': 'fy', 'Galician': 'gl', 'Georgian': 'ka',
    'German': 'de', 'Greek': 'el',
    'Guarani': 'gn', 'Gujarati': 'gu', 'Haitian Creole': 'ht', 'Hausa': 'ha', 'Hawaiian': 'haw', 'Hebrew': 'iw',
    'Hindi': 'hi', 'Hmong': 'hmn',
    'Hungarian': 'hu', 'Icelandic': 'is', 'Igbo': 'ig', 'Ilocano': 'ilo', 'Indonesian': 'id', 'Irish': 'ga',
    'Italian': 'it', 'Japanese': 'ja',
    'Javanese': 'jw', 'Kannada': 'kn', 'Kazakh': 'kk', 'Khmer': 'km', 'Kinyarwanda': 'rw', 'Konkani': 'gom',
    'Korean': 'ko', 'Krio': 'kri',
    'Kurdish (Kurmanji)': 'ku', 'Kurdish (Sorani)': 'ckb', 'Kyrgyz': 'ky', 'Lao': 'lo', 'Latin': 'la', 'Latvian': 'lv',
    'Lingala': 'ln',
    'Lithuanian': 'lt', 'Luganda': 'lg', 'Luxembourgish': 'lb', 'Macedonian': 'mk', 'Maithili': 'mai', 'Malagasy': 'mg',
    'Malay': 'ms',
    'Malayalam': 'ml', 'Maltese': 'mt', 'Maori': 'mi', 'Marathi': 'mr', 'Meiteilon (Manipuri)': 'mni-Mtei',
    'Mizo': 'lus', 'Mongolian': 'mn',
    'Myanmar (Burmese)': 'my', 'Nepali': 'ne', 'Norwegian': 'no', 'Odia (Oriya)': 'or', 'Oromo': 'om', 'Pashto': 'ps',
    'Persian': 'fa',
    'Polish': 'pl', 'Portuguese (Brazil)': 'pt', 'Portuguese (Portugal)': 'pt-PT', 'Punjabi': 'pa', 'Quechua': 'qu',
    'Romanian': 'ro',
    'Russian': 'ru', 'Samoan': 'sm', 'Sanskrit': 'sa', 'Scots Gaelic': 'gd', 'Serbian': 'sr', 'Sesotho': 'st',
    'Shona': 'sn', 'Sindhi': 'sd',
    'Sinhala': 'si', 'Slovak': 'sk', 'Slovenian': 'sl', 'Somali': 'so', 'Spanish': 'es', 'Sundanese': 'su',
    'Swahili': 'sw', 'Swedish': 'sv',
    'Tajik': 'tg', 'Tamil': 'ta', 'Tatar': 'tt', 'Telugu': 'te', 'Thai': 'th', 'Tigrinya': 'ti', 'Tsonga': 'ts',
    'Turkish': 'tr',
    'Turkmen': 'tk', 'Ukrainian': 'uk', 'Urdu': 'ur', 'Uyghur': 'ug', 'Uzbek': 'uz', 'Vietnamese': 'vi', 'Welsh': 'cy',
    'Xhosa': 'xh',
    'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
}
SORTED_LANGUAGES_ITEMS = sorted(LANGUAGES.items())


# --- Utility function for background image ---
def load_and_place_background(parent_widget, image_path):
    """Loads an image, creates a canvas, places the image, and returns the canvas."""
    try:
        img_pil = Image.open(image_path)
        parent_widget.bg_img_pil_original = img_pil
    except FileNotFoundError:
        print(f"Background image not found: {image_path}. Using solid color.")
        parent_widget.bg_photo = None
        return None
    except Exception as e:
        print(f"Error loading background image {image_path}: {e}")
        parent_widget.bg_photo = None
        return None

    canvas = tk.Canvas(parent_widget, highlightthickness=0, bg=COLOR_PRIMARY_BG_CANVAS)
    canvas.pack(fill="both", expand=True)

    def _resize_bg(event):
        if not hasattr(parent_widget, 'bg_img_pil_original') or not parent_widget.bg_img_pil_original: return
        new_width = getattr(event, 'width', parent_widget.winfo_width())
        new_height = getattr(event, 'height', parent_widget.winfo_height())
        if new_width <= 1 or new_height <= 1: return
        resized_pil_img = parent_widget.bg_img_pil_original.resize((new_width, new_height), Image.LANCZOS)
        parent_widget.bg_photo_resized = ImageTk.PhotoImage(resized_pil_img)
        canvas.itemconfig("bg_image_tag", image=parent_widget.bg_photo_resized)
        canvas.coords("bg_image_tag", 0, 0)

    temp_img = parent_widget.bg_img_pil_original.copy().resize((1, 1), Image.LANCZOS)
    parent_widget.bg_photo_initial_placeholder = ImageTk.PhotoImage(temp_img)
    canvas.create_image(0, 0, anchor="nw", image=parent_widget.bg_photo_initial_placeholder, tags="bg_image_tag")
    canvas.bind("<Configure>", _resize_bg)

    def initial_resize_trigger():
        if parent_widget.winfo_width() > 1 and parent_widget.winfo_height() > 1:
            simulated_event = type('Event', (),
                                   {'width': parent_widget.winfo_width(), 'height': parent_widget.winfo_height()})()
            _resize_bg(simulated_event)

    parent_widget.after(50, initial_resize_trigger)
    return canvas


class PoemAnalyzerApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Poem Analyzer Pro")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLOR_PRIMARY_BG_CANVAS)

        self.poem_text = ""
        self.current_page = None
        self.pages = {}

        # Variables for font customization - MOVED EARLIER
        self.current_body_font_family = tk.StringVar(value=BODY_FONT_FAMILY)
        self.current_body_font_size = tk.IntVar(value=BODY_FONT_SIZE)
        self.current_body_font_style = tk.StringVar(value=BODY_FONT_STYLE)
        self.current_body_font_color = tk.StringVar(value=BODY_FONT_COLOR)

        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            print("Clam theme not available, using default.")
            self.style.theme_use(self.style.theme_names()[0] if self.style.theme_names() else 'default')

        self._configure_styles()
        self.create_pages()
        self.show_page("input")

    def _configure_styles(self):
        self.style.configure("TFrame", background=COLOR_FRAME_BG)
        self.style.configure("Content.TFrame", background=COLOR_FRAME_BG)
        self.style.configure("CanvasPage.TFrame", background=COLOR_PRIMARY_BG_CANVAS)

        self.style.configure("TLabel", background=COLOR_FRAME_BG, foreground=COLOR_TEXT_PRIMARY, font=BODY_FONT)
        # Use the user-configurable APP_TITLE_FONT for the main title
        self.style.configure("Title.TLabel", font=APP_TITLE_FONT, foreground=COLOR_TEXT_PRIMARY,
                             background=COLOR_FRAME_BG)
        self.style.configure("Subtitle.TLabel", font=(BODY_FONT_FAMILY, 14, "italic"), foreground=COLOR_TEXT_SECONDARY,
                             background=COLOR_FRAME_BG)
        self.style.configure("Heading.TLabel", font=HEADING_FONT, foreground=COLOR_TEXT_PRIMARY,
                             background=COLOR_FRAME_BG)

        self.style.configure("TButton", font=BUTTON_FONT, padding=(12, 8), relief="flat",
                             background=COLOR_ACCENT, foreground=COLOR_SECONDARY_BG,
                             borderwidth=0, focuscolor=COLOR_ACCENT)
        self.style.map("TButton",
                       background=[('pressed', COLOR_ACCENT_PRESSED), ('active', COLOR_ACCENT_HOVER)],
                       foreground=[('pressed', COLOR_SECONDARY_BG), ('active', COLOR_SECONDARY_BG)])

        self.style.configure("Secondary.TButton", background=COLOR_BUTTON_SECONDARY_BG, foreground=COLOR_TEXT_PRIMARY)
        self.style.map("Secondary.TButton",
                       background=[('pressed', COLOR_BORDER), ('active', COLOR_BUTTON_SECONDARY_HOVER)])

        self.style.configure("TNotebook", background=COLOR_PRIMARY_BG_CANVAS, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=BUTTON_FONT, padding=(10, 5), background=COLOR_FRAME_BG,
                             foreground=COLOR_TEXT_SECONDARY, borderwidth=1)
        self.style.map("TNotebook.Tab",
                       background=[("selected", COLOR_SECONDARY_BG), ('active', COLOR_BUTTON_SECONDARY_HOVER)],
                       foreground=[("selected", COLOR_ACCENT)],
                       expand=[("selected", [1, 1, 1, 0])])

        self.style.configure("TCombobox", font=(BODY_FONT_FAMILY, 10), padding=6)  # Use BODY_FONT_FAMILY
        self.style.map("TCombobox", fieldbackground=[('readonly', COLOR_SECONDARY_BG)],
                       selectbackground=[('readonly', COLOR_ACCENT)],
                       selectforeground=[('readonly', COLOR_SECONDARY_BG)])

        self.style.configure("TMenubutton", font=BUTTON_FONT, padding=(6, 3), background=COLOR_BUTTON_SECONDARY_BG)

    def _set_hand_cursor(self, widget):
        widget.bind("<Enter>", lambda e: widget.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: widget.config(cursor=""))

    def create_pages(self):
        self.pages["input"] = self.create_input_page_frame(self.root)
        self.pages["analysis"] = self.create_analysis_page_frame(self.root)

    def show_page(self, page_name):
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].pack_forget()

        frame_to_show = self.pages.get(page_name)
        if frame_to_show:
            frame_to_show.pack(fill="both", expand=True)
            self.current_page = page_name
        else:
            print(f"Error: Page '{page_name}' not found.")

    def _update_text_widgets_font(self):
        new_font = (self.current_body_font_family.get(),
                    self.current_body_font_size.get(),
                    self.current_body_font_style.get())
        new_color = self.current_body_font_color.get()

        if hasattr(self, 'input_text'):
            self.input_text.config(font=new_font, fg=new_color)

        if hasattr(self, 'analysis_tab_frames'):
            for result_area in self.analysis_tab_frames.values():
                # Store current content and re-insert because font change can affect ScrolledText content display
                current_content = result_area.get(1.0, tk.END)
                is_disabled = result_area.cget("state") == tk.DISABLED
                if is_disabled: result_area.config(state=tk.NORMAL)
                result_area.config(font=new_font, fg=new_color)
                result_area.delete(1.0, tk.END)
                result_area.insert(tk.END, current_content)
                if is_disabled: result_area.config(state=tk.DISABLED)

    def change_font_size(self, delta):
        new_size = self.current_body_font_size.get() + delta
        if 8 <= new_size <= 30:  # Min/max font size
            self.current_body_font_size.set(new_size)
            self._update_text_widgets_font()

    def change_font_family(self, event=None):  # event is passed by Combobox
        # self.current_body_font_family is already updated by its textvariable
        self._update_text_widgets_font()

    def change_font_style(self, style):
        self.current_body_font_style.set(style)
        self._update_text_widgets_font()

    def change_font_color(self):
        color_code = colorchooser.askcolor(title="Choose Text Color", initialcolor=self.current_body_font_color.get())
        if color_code and color_code[1]:  # Check if a color was chosen (color_code[1] is the hex string)
            self.current_body_font_color.set(color_code[1])
            self._update_text_widgets_font()

    def create_font_controls(self, parent_frame):
        controls_frame = ttk.Frame(parent_frame, style="Content.TFrame")

        ttk.Label(controls_frame, text="Font:", style="TLabel", font=SMALL_TEXT_FONT).pack(side=tk.LEFT, padx=(0, 5))
        font_family_combo = ttk.Combobox(controls_frame, textvariable=self.current_body_font_family,
                                         values=AVAILABLE_FONT_FAMILIES, width=15, state="readonly",
                                         font=SMALL_TEXT_FONT)
        font_family_combo.pack(side=tk.LEFT, padx=5)
        font_family_combo.bind("<<ComboboxSelected>>", self.change_font_family)
        self._set_hand_cursor(font_family_combo)

        ttk.Label(controls_frame, text="Size:", style="TLabel", font=SMALL_TEXT_FONT).pack(side=tk.LEFT, padx=(10, 0))
        btn_font_decrease = ttk.Button(controls_frame, text="-", command=lambda: self.change_font_size(-1),
                                       style="Secondary.TButton", width=3)
        btn_font_decrease.pack(side=tk.LEFT, padx=(0, 2))
        self._set_hand_cursor(btn_font_decrease)
        btn_font_increase = ttk.Button(controls_frame, text="+", command=lambda: self.change_font_size(1),
                                       style="Secondary.TButton", width=3)
        btn_font_increase.pack(side=tk.LEFT, padx=(0, 5))
        self._set_hand_cursor(btn_font_increase)

        # Font Style (Normal, Bold, Italic)
        style_menu_btn = ttk.Menubutton(controls_frame, text="Style", style="Secondary.TButton")
        style_menu = tk.Menu(style_menu_btn, tearoff=0, font=SMALL_TEXT_FONT)
        style_menu_btn["menu"] = style_menu
        styles = ["normal", "bold", "italic", "bold italic"]
        for s in styles:
            style_menu.add_radiobutton(label=s.capitalize(), variable=self.current_body_font_style, value=s,
                                       command=self._update_text_widgets_font)
        style_menu_btn.pack(side=tk.LEFT, padx=5)
        self._set_hand_cursor(style_menu_btn)

        btn_font_color = ttk.Button(controls_frame, text="Color", command=self.change_font_color,
                                    style="Secondary.TButton")
        btn_font_color.pack(side=tk.LEFT, padx=5)
        self._set_hand_cursor(btn_font_color)

        return controls_frame

    def create_input_page_frame(self, parent):
        input_page_base_frame = ttk.Frame(parent, style="CanvasPage.TFrame")
        input_canvas = load_and_place_background(input_page_base_frame, "input_page_background.jpg")
        parent_for_content = input_canvas if input_canvas else input_page_base_frame

        content_frame = ttk.Frame(parent_for_content, style="Content.TFrame", padding=(40, 30))
        if input_canvas:
            content_frame_window_id = input_canvas.create_window(0, 0, window=content_frame, anchor="nw")

            def _recenter_input_content(event=None):
                input_canvas.update_idletasks();
                content_frame.update_idletasks()
                cw, ch = input_canvas.winfo_width(), input_canvas.winfo_height()
                fw, fh = content_frame.winfo_reqwidth(), content_frame.winfo_reqheight()
                if cw <= 1 or ch <= 1 or fw <= 1 or fh <= 1:
                    if hasattr(input_canvas, 'after_id_recenter_input'):
                        input_canvas.after_cancel(input_canvas.after_id_recenter_input)
                    input_canvas.after_id_recenter_input = input_canvas.after(50, _recenter_input_content)
                    return
                x, y = (cw - fw) // 2, (ch - fh) // 2
                input_canvas.coords(content_frame_window_id, max(0, x), max(0, y))

            input_canvas.bind("<Configure>", _recenter_input_content, add="+")
            content_frame.bind("<Configure>", _recenter_input_content, add="+")
            input_page_base_frame.after(100, _recenter_input_content)
        else:
            content_frame.place(relx=0.5, rely=0.5, anchor="center")

        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=0)
        content_frame.rowconfigure(1, weight=0)
        content_frame.rowconfigure(2, weight=0)  # Font controls
        content_frame.rowconfigure(3, weight=1)  # Text area
        content_frame.rowconfigure(4, weight=0)  # Buttons

        ttk.Label(content_frame, text="Poem Analyzer Pro", style="Title.TLabel").grid(row=0, column=0, pady=(0, 5),
                                                                                      sticky="n")
        ttk.Label(content_frame, text="Craft your verse, then unveil its secrets.", style="Subtitle.TLabel").grid(row=1,
                                                                                                                  column=0,
                                                                                                                  pady=(
                                                                                                                      0,
                                                                                                                      20),
                                                                                                                  sticky="n")

        font_controls_input = self.create_font_controls(content_frame)
        font_controls_input.grid(row=2, column=0, pady=(0, 10), sticky="ew")

        self.input_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, height=15,
                                                    relief=tk.SOLID, borderwidth=1, padx=10, pady=10,
                                                    bg=COLOR_SECONDARY_BG,
                                                    bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER,
                                                    highlightcolor=COLOR_ACCENT)
        self.input_text.grid(row=3, column=0, sticky="nsew", pady=(0, 20))
        self._update_text_widgets_font()  # Apply initial font settings

        input_button_frame = ttk.Frame(content_frame, style="Content.TFrame")
        input_button_frame.grid(row=4, column=0, sticky="ew")
        input_button_frame.columnconfigure(0, weight=1)
        input_button_frame.columnconfigure(1, weight=0)
        input_button_frame.columnconfigure(2, weight=0)  # Spell Check button
        input_button_frame.columnconfigure(3, weight=1)

        btn_example = ttk.Button(input_button_frame, text="Load Example", command=self.load_example,
                                 style="Secondary.TButton")
        btn_example.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self._set_hand_cursor(btn_example)

        btn_spell_check = ttk.Button(input_button_frame, text="Check Spelling", command=self.check_spelling,
                                     style="Secondary.TButton")
        btn_spell_check.grid(row=0, column=1, padx=10)
        self._set_hand_cursor(btn_spell_check)

        btn_analyze_input = ttk.Button(input_button_frame, text="Analyze Poem", command=self.run_analysis,
                                       style="TButton")
        btn_analyze_input.grid(row=0, column=2, padx=10, ipady=5)
        self._set_hand_cursor(btn_analyze_input)

        btn_clear_input = ttk.Button(input_button_frame, text="Clear",
                                     command=lambda: self.input_text.delete(1.0, tk.END), style="Secondary.TButton")
        btn_clear_input.grid(row=0, column=3, sticky="e", padx=(10, 0))
        self._set_hand_cursor(btn_clear_input)

        return input_page_base_frame

    def check_spelling(self):
        text_to_check = self.input_text.get(1.0, tk.END)
        words = word_tokenize(re.sub(r'[^\w\s]', '', text_to_check))  # Remove punctuation for spell check
        misspelled = spell.unknown(words)

        if not misspelled:
            messagebox.showinfo("Spell Check", "No spelling errors found!", parent=self.root)
            return

        # Create a new Toplevel window for spelling suggestions
        spell_window = tk.Toplevel(self.root)
        spell_window.title("Spelling Suggestions")
        spell_window.geometry("500x400")
        spell_window.configure(bg=COLOR_FRAME_BG)
        spell_window.grab_set()

        ttk.Label(spell_window, text="Misspelled Words & Suggestions:", font=HEADING_FONT).pack(pady=10)

        text_area = scrolledtext.ScrolledText(spell_window, wrap=tk.WORD, font=BODY_FONT, bg=COLOR_SECONDARY_BG,
                                              fg=COLOR_TEXT_PRIMARY)
        text_area.pack(fill="both", expand=True, padx=10, pady=5)
        text_area.config(state=tk.DISABLED)

        output = ""
        for word in misspelled:
            suggestions = list(spell.candidates(word))
            output += f"Word: {word}\n"
            if suggestions:
                output += f"  Suggestions: {', '.join(suggestions[:5])}\n"  # Show top 5
            else:
                output += "  No suggestions found.\n"
            output += "-" * 30 + "\n"

        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, output)
        text_area.config(state=tk.DISABLED)

        ttk.Button(spell_window, text="Close", command=spell_window.destroy, style="Secondary.TButton").pack(pady=10)

    def create_analysis_page_frame(self, parent):
        analysis_page_base_frame = ttk.Frame(parent, style="CanvasPage.TFrame")
        analysis_canvas = load_and_place_background(analysis_page_base_frame, "analysis_page_background.jpg")
        parent_for_content = analysis_canvas if analysis_canvas else analysis_page_base_frame

        content_frame = ttk.Frame(parent_for_content, style="Content.TFrame", padding=20)
        if analysis_canvas:
            content_frame_window_id = analysis_canvas.create_window(0, 0, window=content_frame, anchor="nw")

            def _resize_analysis_page_content(event=None):
                analysis_canvas.update_idletasks();
                content_frame.update_idletasks()
                cw, fw = analysis_canvas.winfo_width(), content_frame.winfo_reqwidth()
                if cw <= 1 or fw <= 1:
                    if hasattr(analysis_canvas, 'after_id_recenter_analysis'): analysis_canvas.after_cancel(
                        analysis_canvas.after_id_recenter_analysis)
                    analysis_canvas.after_id_recenter_analysis = analysis_canvas.after(50,
                                                                                       _resize_analysis_page_content)
                    return
                x_pos = (cw - fw) // 2 if cw > fw else 0
                analysis_canvas.coords(content_frame_window_id, x_pos, 0)
                content_frame.config(width=min(cw - 20, 900))

            analysis_canvas.bind("<Configure>", _resize_analysis_page_content, add="+")
            content_frame.bind("<Configure>", _resize_analysis_page_content, add="+")
            analysis_page_base_frame.after(100, _resize_analysis_page_content)
        else:
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=0)
        content_frame.rowconfigure(1, weight=0)  # Font controls for analysis
        content_frame.rowconfigure(2, weight=1)  # Notebook
        content_frame.rowconfigure(3, weight=0)

        ttk.Label(content_frame, text="Analysis Breakdown", style="Heading.TLabel").grid(row=0, column=0, sticky="w",
                                                                                         pady=(0, 5))

        font_controls_analysis = self.create_font_controls(content_frame)  # Add font controls here too
        font_controls_analysis.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        self.analysis_notebook = ttk.Notebook(content_frame, style="TNotebook")
        self.analysis_notebook.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        self.analysis_tab_frames = {}
        self._create_analysis_tabs_widgets()

        btn_back_to_input = ttk.Button(content_frame, text="« Back to Input", command=lambda: self.show_page("input"),
                                       style="Secondary.TButton")
        btn_back_to_input.grid(row=3, column=0, sticky="e", pady=(10, 0))
        self._set_hand_cursor(btn_back_to_input)
        return analysis_page_base_frame

    def _create_analysis_tabs_widgets(self):
        tab_configs = ["Overview", "Language & Style", "Rhyme & Structure", "Sentiment & Interpretation", "Translation"]
        for text in tab_configs:
            tab_frame = ttk.Frame(self.analysis_notebook, style="Content.TFrame", padding=15)
            self.analysis_notebook.add(tab_frame, text=text)
            result_area = scrolledtext.ScrolledText(tab_frame, wrap=tk.WORD,
                                                    relief=tk.SOLID, borderwidth=1, padx=10, pady=10,
                                                    bg=COLOR_SECONDARY_BG, bd=1, highlightthickness=0)
            result_area.pack(fill="both", expand=True)
            result_area.config(state=tk.DISABLED)
            self.analysis_tab_frames[text] = result_area
        self._add_translation_controls_to_tab()
        self._update_text_widgets_font()  # Apply initial font to new text areas

    def _add_translation_controls_to_tab(self):
        for i in range(self.analysis_notebook.index("end")):
            if self.analysis_notebook.tab(i, "text") == "Translation":
                translation_tab_frame = self.analysis_notebook.nametowidget(self.analysis_notebook.tabs()[i])
                break
        else:
            return
        if "Translation" in self.analysis_tab_frames: self.analysis_tab_frames["Translation"].pack_forget()
        controls_frame = ttk.Frame(translation_tab_frame, style="Content.TFrame")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        self.lang_var = tk.StringVar()
        lang_options = [f"{name} ({code})" for name, code in SORTED_LANGUAGES_ITEMS]
        self.lang_dropdown = ttk.Combobox(controls_frame, textvariable=self.lang_var, values=lang_options,
                                          width=35, state="readonly", style="TCombobox")
        self.lang_dropdown.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        self.lang_dropdown.set("Select Language for Translation")
        self._set_hand_cursor(self.lang_dropdown)
        btn_translate = ttk.Button(controls_frame, text="Translate", command=self.show_translate_in_tab,
                                   style="TButton")
        btn_translate.pack(side=tk.LEFT)
        self._set_hand_cursor(btn_translate)
        if "Translation" in self.analysis_tab_frames: self.analysis_tab_frames["Translation"].pack(fill="both",
                                                                                                   expand=True)

    def load_example(self):
        example_poem = ("The rose is sick. Invisible worm,\nThat flies in the night, in the howling storm,\n"
                        "Has found out thy bed of crimson joy,\nAnd his dark secret love does thy life destroy.\n\n"
                        "A flower dies, when water it does lack,\nA heart may break, with no turning back.\n"
                        "The sun shines bright, but shadows still may fall,\nOn love's sweet dream, beyond recall.")
        self.input_text.delete(1.0, tk.END);
        self.input_text.insert(tk.END, example_poem)

    def run_analysis(self):
        poem_text = self.input_text.get(1.0, tk.END).strip()
        if not poem_text: messagebox.showwarning("Input Error", "Please enter a poem to analyze."); return
        self.poem_text = poem_text
        self.show_page("analysis")
        for tab_name in self.analysis_tab_frames.keys():
            self.display_result_in_tab(tab_name, "Processing...")
        self.root.update_idletasks()
        self.root.after(50, self._perform_all_analyses_on_page)

    def _perform_all_analyses_on_page(self):
        if not self.poem_text: return
        overall_sentiment, detailed_tone, _ = analyze_sentiment(self.poem_text)
        poem_type = identify_poem_type(self.poem_text)
        lines = [line for line in self.poem_text.split('\n') if line.strip()]
        overview_content = f"--- Poem Overview ---\n\nDetected Form: {poem_type}\nNumber of Lines: {len(lines)}\nOverall Sentiment: {overall_sentiment}\nPredominant Tone: {detailed_tone}\n\nThis poem appears to be a "
        if poem_type != "Undetermined Form": overview_content += f"{poem_type.lower()} "
        overview_content += f"conveying a {detailed_tone.lower()} feeling. Further details can be found in the respective analysis tabs."
        self.display_result_in_tab("Overview", overview_content)

        grouped_pos = analyze_parts_of_speech_grouped(self.poem_text)
        fos = identify_figures_of_speech(self.poem_text)
        language_content = "--- Parts of Speech (Grouped) ---\n"
        for category, words in grouped_pos.items(): language_content += f"\n{category}:\n  {', '.join(words)}\n"
        if not grouped_pos: language_content += "No distinct parts of speech identified.\n"
        language_content += "\n--- Figures of Speech ---\n"
        language_content += "\n".join(f"- {item}" for item in fos) if fos else "No common figures of speech detected."
        self.display_result_in_tab("Language & Style", language_content)

        scheme, words_dict, _ = analyze_rhyme_scheme_and_words(self.poem_text)
        rhyme_structure_content = f"--- Rhyme Scheme ---\nCalculated Scheme: {scheme}\n\n"
        if words_dict:
            rhyme_structure_content += "--- Rhyming Word Groups ---\n" + "\n".join(
                f"  Group {k}: {', '.join(sorted(list(set(v))))}" for k, v in words_dict.items())
        else:
            rhyme_structure_content += "No distinct rhyme groups found."
        rhyme_structure_content += f"\n\n--- Syllables per Line (approximate) ---\n" + "\n".join(
            f"  Line {i + 1}: {count_syllables_in_line(line)}" for i, line in enumerate(lines))
        self.display_result_in_tab("Rhyme & Structure", rhyme_structure_content)

        _, _, interpretive_summary = analyze_sentiment(self.poem_text)
        self.display_result_in_tab("Sentiment & Interpretation",
                                   f"--- Emotional Interpretation ---\n\n{interpretive_summary}")
        self.display_result_in_tab("Translation", "Select language to translate.")
        if hasattr(self, 'analysis_notebook'): self.analysis_notebook.select(0)

    def display_result_in_tab(self, tab_name, content):
        if tab_name in self.analysis_tab_frames:
            result_area = self.analysis_tab_frames[tab_name]
            is_disabled = result_area.cget("state") == tk.DISABLED
            if is_disabled: result_area.config(state=tk.NORMAL)
            result_area.delete(1.0, tk.END)
            result_area.insert(tk.END, content)
            if is_disabled: result_area.config(state=tk.DISABLED)
        else:
            print(f"Warning: Tab '{tab_name}' not found.")

    def show_translate_in_tab(self):
        if not self.poem_text: messagebox.showinfo("No Poem", "Please enter a poem first."); return
        selected_lang_display = self.lang_var.get()
        if not selected_lang_display or selected_lang_display == "Select Language for Translation":
            messagebox.showwarning("Language Not Selected", "Please select a target language.");
            return
        match = re.search(r'\((\w{2,5}(?:-\w{2,5})?)\)$', selected_lang_display)
        if not match: messagebox.showerror("Language Error", "Could not parse language code."); return
        lang_code = match.group(1)
        self.display_result_in_tab("Translation", "Translating, please wait...")
        self.root.update_idletasks()

        def do_translation():
            translated_text = translate_poem(self.poem_text, lang_code)
            full_lang_name = next((name for name, code in SORTED_LANGUAGES_ITEMS if code == lang_code), lang_code)
            self.display_result_in_tab("Translation",
                                       f"--- Translation to {full_lang_name} ({lang_code}) ---\n\n{translated_text}")

        self.root.after(50, do_translation)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError):
        pass
    app = PoemAnalyzerApp(root)
    root.mainloop()