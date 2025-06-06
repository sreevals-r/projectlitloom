import tkinter as tk
from tkinter import ttk  # We need this for the dropdown menu
from tkinter import font as tkFont
from PIL import Image, ImageTk, ImageDraw
import re
import threading
import os
import time

# --- Library Imports with User Guidance ---
try:
    from spellchecker import SpellChecker#spelling correction
except ImportError:
    print("Error: 'pyspellchecker' library not found. Please run: pip install pyspellchecker")
    exit()
try:
    import pyttsx3#offline text to speech
except ImportError:
    print("Error: 'pyttsx3' library not found. Please run: pip install pyttsx3")
    exit()
try:
    from deep_translator import GoogleTranslator #translating text between languages
except ImportError:
    print("Error: 'deep_translator' library not found. Please run: pip install deep-translator")
    exit()
try:
    from gtts import gTTS#for google text to speech online
except ImportError:
    print("Error: 'gTTS' library not found. Please run: pip install gTTS")
    exit()
try:
    from playsound import playsound# for playing sound 
except ImportError:
    print("Error: 'playsound' library not found. Please run: pip install playsound==1.2.2")
    exit()


# (SpellCheckPopup class is unchanged, so it is omitted for brevity)
class SpellCheckPopup(tk.Toplevel):     #spelling check pop up window
    """A custom-themed pop-up window for spell checking."""

    def __init__(self, parent, misspelled_data):#parent:-main window, misspelled_data:-dictoinary of words with spelling mistakes
        super().__init__(parent)
        self.parent = parent
        self.misspelled_data = misspelled_data
        self.current_word_index = 0
        self.withdraw()#temp hide window
        self.overrideredirect(True)
        self.geometry("400x350")
        self.attributes("-alpha", 0.98)
        self.bg_color, self.main_color, self.text_color = "#B48C68", "#C7B6A4", "#4A4A4A"
        self.button_color, self.button_hover_color = "#E5E5E5", "#DCDCDC"
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<B1-Motion>", self.move_window)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.setup_ui()
        self.display_next_error()
        self.center_window()
        self.deiconify()

    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def move_window(self, event):
        deltax, deltay = event.x - self.x, event.y - self.y
        x, y = self.winfo_x() + deltax, self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def center_window(self):
        self.update_idletasks()
        px, py = self.parent.winfo_x(), self.parent.winfo_y()
        pw, ph = self.parent.winfo_width(), self.parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = px + (pw // 2) - (w // 2), py + (ph // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

    def setup_ui(self):
        self.canvas.configure(bg=self.bg_color)
        self.parent.draw_rounded_rectangle_on_canvas(self.canvas, 5, 5, 395, 345, radius=20, fill=self.main_color)
        self.canvas.create_text(380, 20, text="X", font=("Georgia", 14, "bold"), fill=self.text_color, tags="close_btn")
        self.canvas.tag_bind("close_btn", "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind("close_btn", "<Leave>", lambda e: self.config(cursor=""))
        self.canvas.tag_bind("close_btn", "<Button-1>", lambda e: self.destroy())

    def display_next_error(self):
        self.canvas.delete("suggestion")
        if self.current_word_index >= len(self.misspelled_data):
            self.canvas.create_text(200, 150, text="Spell check complete!", font=("Georgia", 16), fill=self.text_color,
                                    tags="suggestion")
            self.after(1500, self.destroy)
            return
        data = self.misspelled_data[self.current_word_index]
        word, suggestions = data['word'], data['suggestions']
        self.canvas.create_text(200, 50, text="Misspelled Word:", font=("Georgia", 12), fill=self.text_color,
                                tags="suggestion")
        self.canvas.create_text(200, 80, text=f"'{word}'", font=("Georgia", 18, "bold"), fill="#C0392B",
                                tags="suggestion")
        y_pos = 120
        for i, sug in enumerate(suggestions[:5]):
            btn_tag = f"sug_{i}"
            self.parent.draw_rounded_rectangle_on_canvas(self.canvas, 100, y_pos, 300, y_pos + 30, radius=15,
                                                         fill=self.button_color, outline="",
                                                         tags=(f"{btn_tag}_bg", btn_tag, "sug_btn"))
            self.canvas.create_text(200, y_pos + 15, text=sug, font=("Georgia", 12), fill=self.text_color,
                                    tags=(btn_tag, "sug_btn"))
            self.canvas.tag_bind(btn_tag, "<Enter>", lambda e, t=btn_tag: self.on_sug_hover(t))
            self.canvas.tag_bind(btn_tag, "<Leave>", lambda e, t=btn_tag: self.on_sug_leave(t))
            self.canvas.tag_bind(btn_tag, "<Button-1>", lambda e, s=sug: self.replace_word(s))
            y_pos += 40
        self.parent.draw_rounded_rectangle_on_canvas(self.canvas, 220, 300, 350, 330, radius=15, fill=self.button_color,
                                                     tags=("ignore_bg", "ignore_btn", "sug_btn"))
        self.canvas.create_text(285, 315, text="Ignore", font=("Georgia", 12, "bold"), tags=("ignore_btn", "sug_btn"))
        self.canvas.tag_bind("ignore_btn", "<Button-1>", lambda e: self.next_error())
        self.canvas.tag_bind("ignore_btn", "<Enter>", lambda e: self.on_sug_hover("ignore_btn"))
        self.canvas.tag_bind("ignore_btn", "<Leave>", lambda e: self.on_sug_leave("ignore_btn"))

    def on_sug_hover(self, tag):
        self.config(cursor="hand2")
        self.canvas.itemconfig(f"{tag}_bg", fill=self.button_hover_color)
        self.canvas.move(tag, 1, 1)

    def on_sug_leave(self, tag):
        self.config(cursor="")
        self.canvas.itemconfig(f"{tag}_bg", fill=self.button_color)
        self.canvas.move(tag, -1, -1)

    def replace_word(self, suggestion):
        data = self.misspelled_data[self.current_word_index]
        self.parent.replace_text(data['index'], data['word'], suggestion)
        self.next_error()

    def next_error(self):
        self.current_word_index += 1
        self.display_next_error()


class TextToSpeechPopup(tk.Toplevel):
    def __init__(self, parent, text_to_speak):
        super().__init__(parent)
        self.parent = parent
        self.text_to_speak = text_to_speak
        self.is_playing = False
        self.audio_thread = None

        try:
            self.engine = pyttsx3.init()
            self.male_voice_id, self.female_voice_id = self.find_voices()
            self.current_rate = self.engine.getProperty('rate')
            self.default_rate = self.current_rate
            self.min_rate, self.max_rate = self.default_rate - 80, self.default_rate + 80
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
            self.destroy();
            return

        self.selected_voice_gender = tk.StringVar(value="female")
        # --- NEW: Language data and selection variable ---
        self.languages = {"English": "en", "Spanish": "es", "French": "fr", "German": "de", "Hindi": "hi",
                          "Japanese": "ja", "Korean": "ko", "Russian": "ru"}
        self.selected_language = tk.StringVar(value="English")

        self.withdraw()
        self.overrideredirect(True)
        self.geometry("400x350")  # Increased size for language dropdown
        self.attributes("-alpha", 0.98)

        self.bg_color, self.main_color, self.text_color = "#B48C68", "#C7B6A4", "#4A4A4A"
        self.button_color, self.button_hover_color = "#E5E5E5", "#DCDCDC"

        # Using a frame to hold both canvas and the standard ttk widget
        self.main_frame = tk.Frame(self, bg=self.main_color)
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_frame, highlightthickness=0, bg=self.main_color)
        self.canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self.canvas.bind("<B1-Motion>", self.move_window)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()
        self.center_window()
        self.deiconify()

    def on_close(self):
        self.is_playing = False  # Signal thread to stop
        if self.engine._inLoop:
            self.engine.endLoop()
        self.destroy()

    def find_voices(self):
        voices = self.engine.getProperty('voices')
        male_id, female_id = None, None

        for v in voices:
            name = v.name.lower()
            if ('male' in name or 'man' in name) and not male_id:
                male_id = v.id
            if ('female' in name or 'woman' in name) and not female_id:
                female_id = v.id

        if not female_id and voices:
            female_id = voices[0].id
        if not male_id and voices:
            male_id = voices[1].id if len(voices) > 1 else female_id

        return male_id, female_id


    def setup_ui(self):
        self.parent.draw_rounded_rectangle_on_canvas(self.canvas, 5, 5, 395, 345, radius=20, fill=self.main_color)
        self.canvas.create_text(200, 30, text="Read Aloud", font=("Georgia", 20, "bold"), fill=self.text_color)
        self.canvas.create_text(380, 20, text="X", font=("Georgia", 14, "bold"), fill=self.text_color,
                            tags="tts_close_btn")
        self.canvas.tag_bind("tts_close_btn", "<Button-1>", lambda e: self.on_close())

    # Language Dropdown
        self.canvas.create_text(100, 80, text="Language:", font=("Georgia", 12), fill=self.text_color)
        self.lang_combo = ttk.Combobox(self.main_frame, textvariable=self.selected_language,
                                   values=list(self.languages.keys()), state='readonly', width=15)
        self.lang_combo.place(x=180, y=70)
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)

    # Voice selection
        self.voice_label = self.canvas.create_text(100, 120, text="Voice:", font=("Georgia", 12), fill=self.text_color)
        self.female_radio = self.draw_radio_button(180, 110, "Female", "female")
        self.male_radio = self.draw_radio_button(270, 110, "Male", "male")

    # Speed dropdown
        self.canvas.create_text(100, 175, text="Speed:", font=("Georgia", 12), fill=self.text_color)
        self.speed_var = tk.StringVar(value="1x")
        self.speed_combo = ttk.Combobox(self.main_frame, textvariable=self.speed_var,
                                    values=["0.75x", "1x", "1.25x", "1.5x", "2x"],
                                    state='readonly', width=10)
        self.speed_combo.place(x=180, y=165)

    # Play button
        self.play_button_bg = self.parent.draw_rounded_rectangle_on_canvas(self.canvas, 125, 250, 275, 300, radius=25,
                                                                        fill=self.button_color)
        self.play_button_text = self.canvas.create_text(200, 275, text="Play", font=("Georgia", 18, "bold"),
                                                    fill=self.text_color)
        self.canvas.tag_bind(self.play_button_bg, "<Button-1>", self.toggle_play)
        self.canvas.tag_bind(self.play_button_text, "<Button-1>", self.toggle_play)

        self.on_language_change()
  # Set initial UI state

    def on_language_change(self, event=None):
        """Shows or hides the voice selection based on the chosen language."""
        is_english = self.selected_language.get() == "English"
        new_state = "normal" if is_english else "hidden"
        self.canvas.itemconfigure(self.voice_label, state=new_state)
        for item in self.female_radio + self.male_radio:
            self.canvas.itemconfigure(item, state=new_state)

    def map_rate_to_x(self, rate):
        percentage = (rate - self.min_rate) / (self.max_rate - self.min_rate)
        return self.slider_x_start + percentage * (self.slider_x_end - self.slider_x_start)

    def drag_slider(self, event):
        if self.is_playing:
            return
    # Convert root x to canvas x if needed
        x = max(self.slider_x_start, min(event.x, self.slider_x_end))
        self.canvas.coords(self.slider_handle, x - 8, self.slider_y - 8, x + 8, self.slider_y + 8)
        percentage = (x - self.slider_x_start) / (self.slider_x_end - self.slider_x_start)
        self.current_rate = self.min_rate + percentage * (self.max_rate - self.min_rate)

    def draw_radio_button(self, x, y, text, value):
        tag, text_tag = f"radio_{value}", f"radio_{value}_text"
        oval = self.canvas.create_oval(x, y, x + 20, y + 20, fill=self.button_color, outline=self.text_color, width=2,
                                       tags=tag)
        txt = self.canvas.create_text(x + 55, y + 10, text=text, font=("Georgia", 12), fill=self.text_color,
                                      tags=text_tag)
        self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.select_voice(value))
        self.canvas.tag_bind(text_tag, "<Button-1>", lambda e: self.select_voice(value))
        check = None
        if self.selected_voice_gender.get() == value:
            check = self.canvas.create_oval(x + 5, y + 5, x + 15, y + 15, fill=self.text_color, outline="",
                                            tags=f"check_{value}")
        return [oval, txt, check] if check else [oval, txt]

    def select_voice(self, value):
        if self.is_playing: return
        self.selected_voice_gender.set(value)
        self.canvas.delete("check_male", "check_female")
        x = 270 if value == 'female' else 180
        y = 110
        self.canvas.create_oval(x + 5, y + 5, x + 15, y + 15, fill=self.text_color, outline="", tags=f"check_{value}")

    def toggle_play(self, event=None):
        if self.is_playing:
            self.is_playing = False
            return

        self.is_playing = True

    # Set speed based on dropdown
        speed_map = {
            "0.75x": 125,
            "1x": 150,
            "1.25x": 175,
            "1.5x": 200,
            "2x": 250
        }
        selected_speed = self.speed_var.get()
        self.current_rate = speed_map.get(selected_speed, 150)

        if self.selected_language.get() == "English":
            voice_gender = self.selected_voice_gender.get()
            if voice_gender == "male":
                self.engine.setProperty('voice', self.male_voice_id)
            else:
                self.engine.setProperty('voice', self.female_voice_id)

            self.engine.setProperty('rate', int(self.current_rate))
            self.engine.say(self.text_to_speak)
            self.engine.runAndWait()
            self.is_playing = False
        else:
            lang_code = self.languages[self.selected_language.get()]
            tts = gTTS(text=self.text_to_speak, lang=lang_code)
            filename = "temp_audio.mp3"
            tts.save(filename)

            def play_and_cleanup():
                try:
                    playsound(filename)
                finally:
                    if os.path.exists(filename):
                        try:
                            os.remove(filename)
                        except PermissionError:
                            pass
                self.is_playing = False

            threading.Thread(target=play_and_cleanup).start()

    def play_english_tts(self):
        """Uses pyttsx3 for offline English playback."""
        voice_id = self.male_voice_id if self.selected_voice_gender.get() == 'female' else self.female_voice_id
        self.engine.setProperty('rate', self.current_rate)
        self.engine.setProperty('voice', voice_id)
        self.engine.say(self.text_to_speak)
        self.engine.runAndWait()
        self.is_playing = False
        self.parent.after(0, self.canvas.itemconfig, self.play_button_text, {"text": "Play"})

    def play_translated_tts(self, lang_code):
        try:
            text = self.poem_text.strip()
            if not text:
                return

            translated = GoogleTranslator(source='auto', target=lang_code).translate(text)
            tts = gTTS(text=translated, lang=lang_code)
            tts.save("temp_audio.mp3")

            playsound("temp_audio.mp3")

            # Wait and then remove safely
            time.sleep(1)
            os.remove("temp_audio.mp3")

        except Exception as e:
            print(f"Error in play_translated_tts: {e}")

    # Other methods like start_move, move_window, center_window are the same
    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def move_window(self, event):
        deltax, deltay = event.x - self.x, event.y - self.y
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def center_window(self):
        self.update_idletasks()
        px, py = self.parent.winfo_x(), self.parent.winfo_y()
        pw, ph = self.parent.winfo_width(), self.parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f'{w}x{h}+{px + (pw // 2) - (w // 2)}+{py + (ph // 2) - (h // 2)}')


# --- Main Application Class (No changes below this line) ---
class LitLoomApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("◆ LitLoom")
        self.geometry("800x600")
        self.minsize(600, 450)
        self.current_page = "welcome"
        self.resize_job_id = None
        self.last_width, self.last_height = 0, 0
        self.button_bg_color, self.button_hover_color = "#A6876D", "#92755E"
        self.control_button_color, self.control_button_hover_color = "#E5E5E5", "#DCDCDC"

        self.spell = SpellChecker()
        self.text_widget = None

        self.example_poems = [
            (
                "The rose is sick. Invisible worm,\nThat flies in the nyght, in the howling storm,\nHas found out thy bed of crimson joy,\nAnd his dark secret love does thy life distroy."),
            (
                "I wandered lonely as a clowd\nThat floats on high o'er vales and hills,\nWhen all at once I saw a crowd,\nA host, of golden daffodills."),
            (
                "Two roads diverged in a yellow wood,\nAnd sorry I could not travel both\nAnd be one traveler, long I stood\nAnd looked down one as far as I could\nTo where it bent in the undergrowth;\n\nThen took the other, as just as fair,\nAnd having perhaps the better claim,\nBecause it was grassy and wanted wear;\nThough as for that the passing there\nHad worn them really about the same.")
        ]
        self.current_poem_index = 0

        self.load_images()
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind_events()
        self.redraw_canvas(force_redraw=True)

    def load_images(self):
        self.original_fg_image, self.original_bg_image, self.original_logo_image, self.original_title_image, self.original_bottom_sound_icon_image, self.original_top_sound_icon_image = None, None, None, None, None, None
        self.fg_photo, self.bg_photo, self.logo_photo, self.title_photo, self.bottom_sound_icon_photo, self.top_sound_icon_photo = None, None, None, None, None, None

        try:
            self.original_fg_image = Image.open("background.jpeg")
        except FileNotFoundError:
            print("Error: 'background.jpeg' not found.")
        try:
            self.original_bg_image = Image.open("bg.jpeg")
        except FileNotFoundError:
            print("Error: 'bg.jpeg' not found.")
        try:
            self.original_logo_image = Image.open("Quill With Ink.png")
        except FileNotFoundError:
            print("Error: 'Quill With Ink.png' not found.")
        try:
            self.original_title_image = Image.open("LitLoom.png")
        except FileNotFoundError:
            print("Error: 'LitLoom.png' not found.")

        try:
            self.original_bottom_sound_icon_image = Image.open("Sound II.png")
        except FileNotFoundError:
            print("Error: 'Sound II.png' (bottom icon) not found.")

        try:
            self.original_top_sound_icon_image = Image.open("Sound I.png")
        except FileNotFoundError:
            print("Error: 'Sound I.png' (top icon) not found.")

    def bind_events(self):
        self.bind("<Configure>", self.handle_resize)
        self.canvas.tag_bind("button", "<Button-1>", self.go_to_next_page)
        self.canvas.tag_bind("button", "<Enter>", self.on_button_hover)
        self.canvas.tag_bind("button", "<Leave>", self.on_button_leave)
        self.canvas.tag_bind("control_btn", "<Enter>", self.on_control_btn_hover)
        self.canvas.tag_bind("control_btn", "<Leave>", self.on_control_btn_leave)
        self.canvas.tag_bind("example_btn", "<Button-1>", self.show_example_poem)
        self.canvas.tag_bind("spell_correct_btn", "<Button-1>", self.run_spell_correct)
        self.canvas.tag_bind("analyze_btn", "<Button-1>", self.run_analyze)
        self.canvas.tag_bind("clear_btn", "<Button-1>", self.clear_text)

        self.canvas.tag_bind("sound_icon_btn", "<Button-1>", self.open_tts_popup)
        self.canvas.tag_bind("sound_icon_btn", "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind("sound_icon_btn", "<Leave>", lambda e: self.config(cursor=""))

    def go_to_next_page(self, event=None):
        self.current_page = "next"
        self.redraw_canvas(force_redraw=True)

    def on_button_hover(self, event=None):
        self.config(cursor="hand2")
        self.canvas.move("button", 1, 1)
        self.canvas.itemconfig("button_bg", fill=self.button_hover_color)

    def on_button_leave(self, event=None):
        self.config(cursor="")
        self.canvas.move("button", -1, -1)
        self.canvas.itemconfig("button_bg", fill=self.button_bg_color)

    def on_control_btn_hover(self, event):
        self.config(cursor="hand2")
        tags = self.canvas.gettags("current")
        unique_tag = next((t for t in tags if t.endswith('_btn')), None)
        if unique_tag:
            self.canvas.itemconfig(f"{unique_tag}_bg", fill=self.control_button_hover_color)
            self.canvas.move(unique_tag, 1, 1)

    def on_control_btn_leave(self, event):
        self.config(cursor="")
        tags = self.canvas.gettags("current")
        unique_tag = next((t for t in tags if t.endswith('_btn')), None)
        if unique_tag:
            self.canvas.itemconfig(f"{unique_tag}_bg", fill=self.control_button_color)
            self.canvas.move(unique_tag, -1, -1)

    def show_example_poem(self, event=None):
        if not self.text_widget: return
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", self.example_poems[self.current_poem_index])
        self.current_poem_index = (self.current_poem_index + 1) % len(self.example_poems)

    def clear_text(self, event=None):
        if self.text_widget: self.text_widget.delete("1.0", tk.END)

    def run_spell_correct(self, event=None):
        if not self.text_widget or not self.text_widget.get("1.0", tk.END).strip(): return
        content = self.text_widget.get("1.0", tk.END)
        words = set(re.findall(r'\b\w+\b', content.lower()))
        misspelled = self.spell.unknown(words)
        misspelled_data = []
        if misspelled:
            for word in sorted(list(misspelled)):
                start_pos = "1.0"
                while True:
                    start_pos = self.text_widget.search(word, start_pos, stopindex=tk.END, nocase=1, exact=True)
                    if not start_pos: break
                    end_pos = f"{start_pos}+{len(word)}c"
                    original_casing = self.text_widget.get(start_pos, end_pos)
                    misspelled_data.append(
                        {'word': original_casing, 'index': start_pos, 'suggestions': list(self.spell.candidates(word))})
                    start_pos = end_pos
            if misspelled_data: SpellCheckPopup(self, misspelled_data)

    def run_analyze(self, event=None):
        print("Analyze button clicked!")
        if self.text_widget: self.text_widget.delete("1.0", tk.END)

    def replace_text(self, index, old, new):
        if self.text_widget:
            self.text_widget.delete(index, f"{index}+{len(old)}c")
            self.text_widget.insert(index, new)

    def handle_resize(self, event):
        if self.resize_job_id: self.after_cancel(self.resize_job_id)
        self.resize_job_id = self.after(50, self.redraw_canvas)

    def redraw_canvas(self, force_redraw=False):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2: return
        size_changed = (w != self.last_width or h != self.last_height)
        if not size_changed and not force_redraw: return

        text_content = self.text_widget.get("1.0", tk.END) if self.text_widget else ""
        self.canvas.delete("all")
        if self.text_widget: self.text_widget.destroy()

        if self.current_page == "welcome":
            self.draw_welcome_page(w, h, size_changed)
        elif self.current_page == "next":
            self.draw_next_page(w, h, size_changed)
            if text_content.strip(): self.text_widget.insert("1.0", text_content)
        self.last_width, self.last_height = w, h

    def draw_rounded_rectangle_on_canvas(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2,
                  y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2, x1 + radius,
                  y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1,
                  y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def draw_background(self, w, h, size_changed):
        if (size_changed or not self.bg_photo) and self.original_bg_image:
            img = self.original_bg_image.resize((w, h), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        else:
            self.canvas.configure(bg="#FDFDFD")

    def draw_next_page(self, w, h, size_changed):
        bg, sidebar, content, text_color = "#B48C68", "#C7B6A4", "#E5E5E5", "#4A4A4A"
        self.canvas.configure(bg=bg)
        border = 20
        self.draw_rounded_rectangle_on_canvas(self.canvas, border, border, w - border, h - border, radius=25,
                                              fill=sidebar)

        sidebar_w, top_m, content_p = 220, 80, 40
        self.draw_rounded_rectangle_on_canvas(self.canvas, sidebar_w, top_m, w - content_p, h - content_p, radius=20,
                                              fill=content)

        heading_y = (top_m + border) / 2
        self.canvas.create_text((w + sidebar_w) / 2, heading_y, text="Write-Poem", font=("Georgia", 22, "bold"),
                                fill=text_color)

        if (size_changed or not self.logo_photo) and self.original_logo_image:
            img = self.original_logo_image.copy()
            img.thumbnail((45, 45), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(img)
        if self.logo_photo: self.canvas.create_image(60, 60, image=self.logo_photo)

        text_frame = tk.Frame(self, bg=content, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=lambda *args: self.text_widget.yview(*args))
        self.text_widget = tk.Text(text_frame, bg=content, fg=text_color, font=("Georgia", 14), bd=0,
                                   highlightthickness=0, wrap="word", insertbackground=text_color,
                                   selectbackground=sidebar, undo=True, yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text_widget.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(sidebar_w + 10, top_m + 10, window=text_frame, anchor="nw",
                                  width=w - sidebar_w - content_p - 20, height=h - top_m - content_p - 20)

        btn_w, btn_h, btn_cx = 150, 40, sidebar_w / 2 + 10
        buttons = {"example_btn": {"y": 120, "text": "Add Poem"},
                   "spell_correct_btn": {"y": 180, "text": "Spell Correct"}, "clear_btn": {"y": 240, "text": "Clear"},
                   "analyze_btn": {"y": h - 100, "text": "Analyze"}}
        for tag, props in buttons.items():
            font = ("Georgia", 14, "bold") if tag == "analyze_btn" else ("Georgia", 12, "bold")
            self.draw_rounded_rectangle_on_canvas(self.canvas, btn_cx - btn_w / 2, props['y'], btn_cx + btn_w / 2,
                                                  props['y'] + btn_h, radius=20, fill=self.control_button_color,
                                                  tags=(f"{tag}_bg", tag, "control_btn"))
            self.canvas.create_text(btn_cx, props['y'] + btn_h / 2, text=props['text'], font=font, fill=text_color,
                                    tags=(tag, "control_btn"))

        if (size_changed or not self.bottom_sound_icon_photo) and self.original_bottom_sound_icon_image:
            img = self.original_bottom_sound_icon_image.copy().convert('RGBA')
            img.thumbnail((60, 60), Image.Resampling.LANCZOS)
            self.bottom_sound_icon_photo = ImageTk.PhotoImage(img)
        if self.bottom_sound_icon_photo:
            self.canvas.create_image(w - content_p - 35, h - content_p - 35, image=self.bottom_sound_icon_photo,
                                     anchor="center", tags="sound_icon_btn")

        if (size_changed or not self.top_sound_icon_photo) and self.original_top_sound_icon_image:
            img = self.original_top_sound_icon_image.copy().convert('RGBA')
            img.thumbnail((40, 40), Image.Resampling.LANCZOS)
            self.top_sound_icon_photo = ImageTk.PhotoImage(img)
        if self.top_sound_icon_photo:
            self.canvas.create_image(w - content_p - 30, heading_y, image=self.top_sound_icon_photo, anchor="center",
                                     tags="sound_icon_btn")

    def open_tts_popup(self, event=None):
        if not self.text_widget: return
        content = self.text_widget.get("1.0", tk.END).strip()
        if content:
            TextToSpeechPopup(self, content)
        else:
            print("Text area is empty. Nothing to speak.")

    def draw_welcome_page(self, w, h, size_changed):
        self.draw_background(w, h, size_changed)
        if (size_changed or not self.logo_photo) and self.original_logo_image:
            img = self.original_logo_image.copy()
            img.thumbnail((45, 45), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(img)
        if self.logo_photo: self.canvas.create_image(50, 50, image=self.logo_photo, anchor="center")

        if (size_changed or not self.fg_photo) and self.original_fg_image:
            img = self.original_fg_image.copy()
            img.thumbnail((w * 0.85, h * 0.75), Image.Resampling.LANCZOS)
            self.fg_photo = ImageTk.PhotoImage(self.add_rounded_corners(img, 30))
        if self.fg_photo: self.canvas.create_image(w / 2, h * 0.55, image=self.fg_photo)

        if (size_changed or not self.title_photo) and self.original_title_image:
            img = self.original_title_image.copy()
            img.thumbnail((w * 0.4, 100), Image.Resampling.LANCZOS)
            self.title_photo = ImageTk.PhotoImage(img)
        if self.title_photo: self.canvas.create_image(w / 2, h * 0.15, image=self.title_photo)

        btn_w, btn_h, btn_cx, btn_cy = 200, 50, w / 2, h * 0.55
        self.draw_rounded_rectangle_on_canvas(self.canvas, btn_cx - btn_w / 2, btn_cy - btn_h / 2, btn_cx + btn_w / 2,
                                              btn_cy + btn_h / 2, radius=25, fill=self.button_bg_color,
                                              tags=("button", "button_bg"))
        self.canvas.create_text(btn_cx, btn_cy, text="Let's Go!", font=("Helvetica", 16, "bold"), fill="white",
                                tags="button")

    def add_rounded_corners(self, img, radius):
        mask = Image.new('L', img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0) + img.size, radius=radius, fill=255)
        img.putalpha(mask)
        return img


# --- Running the Application ---
if __name__ == "__main__":
    app = LitLoomApp()
    app.mainloop()
