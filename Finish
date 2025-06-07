import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import re
import threading
import os
import sys
import math

# --- Library Imports with User Guidance ---
# --- Library Imports with User Guidance ---
try:
    from spellchecker import SpellChecker
except ImportError:
    print("Error: 'pyspellchecker' library not found. Please run: pip install pyspellchecker")
    sys.exit()
try:
    import pyttsx3
except ImportError:
    # On Windows, you might not need to specify the version.
    # If you face issues, try `pip install pyttsx3`.
    print("Error: 'pyttsx3' library not found. Please run: pip install pyttsx3")
    sys.exit()
try:
    import nltk
    import nltk.downloader as nl_downloader
except ImportError:
    print("Error: 'nltk' library not found. Please run: pip install nltk")
    sys.exit()
try:
    from deep_translator import GoogleTranslator, exceptions
except ImportError:
    # This is now only needed for the analysis page translation, not for TTS.
    print("Error: 'deep_translator' library not found. Please run: pip install deep-translator")
    sys.exit()
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    # Import font registration module
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("Error: 'reportlab' library not found. Please run: pip install reportlab")
    sys.exit()
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    # Import font registration module
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("Error: 'reportlab' library not found. Please run: pip install reportlab")
    sys.exit()

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize


# --- One-time NLTK Data Download ---
def download_nltk_data():
    """Downloads required NLTK data if not already present."""
    required_data = [('tokenizers/punkt', 'punkt'),
                     ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
                     ('sentiment/vader_lexicon', 'vader_lexicon')]

    print("Checking for necessary NLTK data...")
    all_present = True
    for path, pkg_id in required_data:
        try:
            nltk.data.find(path)
            print(f"  - {pkg_id} is already present.")
        except (getattr(nl_downloader, 'DownloadError', Exception)) as e:
            all_present = False
            print(f"  - {pkg_id} not found or download error: {e}. Attempting to download...")
            try:
                nltk.download(pkg_id, quiet=False)
            except Exception as download_e:
                print(
                    f"CRITICAL ERROR: Failed to download NLTK data '{pkg_id}'. Please try running `python -m nltk.downloader {pkg_id}` manually in your terminal.")
                print(f"Details: {download_e}")
                sys.exit(1)

    if all_present:
        print("\nAll NLTK data already present.")
    else:
        print("\nNLTK data download complete.")


download_nltk_data()

# --- Global Font Registration for ReportLab ---
# You need a .ttf font file that supports the desired languages.
# A common choice is Noto Sans (or Noto Serif) which covers many languages.
# For example, NotoSans-Regular.ttf from Google Fonts.
# You might need to place this font file in a known location (e.g., in an 'assets' folder
# next to your script, or a system font directory).
# If this font is not found, the PDF generation for translated text might still show boxes.
try:
    # Attempt to load a font file that supports wide range of Unicode characters
    # You might need to provide the correct path to your .ttf file.
    # For example, if 'NotoSans-Regular.ttf' is in a subfolder named 'fonts'
    # in the same directory as your script:
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts', 'NotoSans-Regular.ttf')
    # Or, if you know a common system font that supports the language, you can try that.
    # For Windows: C:/Windows/Fonts/Arial Unicode MS.ttf
    # For Linux: /usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc (or similar)

    # Let's assume for now, we'll try a common one, or you'd provide one in 'assets/fonts'
    # For demonstration, I'll use a placeholder 'NotoSans-Regular.ttf' name.
    # IMPORTANT: You MUST acquire and place a suitable NotoSans-Regular.ttf (or similar)
    # font file in an 'assets/fonts' directory next to your script, or provide its full path.
    default_font_for_pdf = 'NotoSans'
    pdfmetrics.registerFont(TTFont(default_font_for_pdf,
                                   os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts',
                                                'NotoSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont(f'{default_font_for_pdf}-Bold',
                                   os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts',
                                                'NotoSans-Bold.ttf')))  # If you have a bold variant
    # Register a fallback font for standard English content too if needed, or use built-in Helvetica.
    # We will use 'NotoSans' for the main content to ensure translated text renders.
except Exception as e:
    print(f"WARNING: Could not load custom font for PDF generation: {e}. Translated text in PDF may appear as boxes.")
    # Fallback to a ReportLab built-in font for translated text if custom font fails, but it might not work.
    default_font_for_pdf = 'Helvetica'  # This usually supports Latin characters, but not others.


# --- POPUP WINDOW CLASSES ---

class ExportPdfPopup(tk.Toplevel):
    """A custom-themed pop-up window for PDF export options."""

    def __init__(self, parent, pdf_content_func):
        super().__init__(parent)
        self.parent = parent
        self.pdf_content_func = pdf_content_func
        self.selected_path = tk.StringVar(value=os.path.expanduser("~"))  # Default to user's home directory

        self.withdraw()
        self.overrideredirect(True)
        self.geometry("500x250")
        self.attributes("-alpha", 0.98)

        self.bg_color = "#B48C68"
        self.main_color = "#C7B6A4"
        self.text_color = "#4A4A4A"
        self.button_color = "#E5E5E5"
        self.button_hover_color = "#DCDCDC"

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<B1-Motion>", self.move_window)
        self.canvas.bind("<ButtonPress-1>", self.start_move)

        self.setup_ui()
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
        self.geometry(f'{w}x{h}+{px + (pw // 2) - (w // 2)}+{py + (ph // 2) - (h // 2)}')

    def setup_ui(self):
        self.canvas.configure(bg=self.bg_color)
        self.parent.draw_rounded_rectangle(self.canvas, 5, 5, 495, 245, radius=20, fill=self.main_color,
                                           tags="popup_bg")

        self.close_btn_id = self.canvas.create_text(480, 20, text="X", font=("Georgia", 14, "bold"),
                                                    fill=self.text_color, tags="close_btn")
        self.canvas.tag_bind("close_btn", "<Enter>",
                             lambda e: self.config(cursor="hand2") or self.canvas.itemconfig(self.close_btn_id,
                                                                                             fill="#C0392B"))
        self.canvas.tag_bind("close_btn", "<Leave>",
                             lambda e: self.config(cursor="") or self.canvas.itemconfig(self.close_btn_id,
                                                                                        fill=self.text_color))
        self.canvas.tag_bind("close_btn", "<Button-1>", lambda e: self.destroy())

        self.canvas.create_text(250, 40, text="Export PDF", font=("Georgia", 20, "bold"), fill=self.text_color,
                                anchor="center")

        self.canvas.create_text(100, 90, text="Save to:", font=("Georgia", 12), fill=self.text_color, anchor="w")

        self.path_entry = ttk.Entry(self, textvariable=self.selected_path, width=40, style='TEntry')
        self.canvas.create_window(100, 110, window=self.path_entry, anchor="w")

        # Browse button
        self.parent.create_canvas_button(self.canvas, 400, 95, 470, 125, "Browse", "browse_btn", self.browse_directory,
                                         corner_radius=10, font_size=10,
                                         bg_color=self.button_color, hover_color=self.button_hover_color,
                                         text_color=self.text_color)

        # Convert Button
        self.parent.create_canvas_button(self.canvas, 120, 180, 240, 215, "Convert", "convert_final_btn",
                                         self.convert_and_save,
                                         corner_radius=20, font_size=14,
                                         bg_color=self.button_color, hover_color=self.button_hover_color,
                                         text_color=self.text_color)

        # Cancel Button
        self.parent.create_canvas_button(self.canvas, 260, 180, 380, 215, "Cancel", "cancel_export_btn", self.destroy,
                                         corner_radius=20, font_size=14,
                                         bg_color=self.button_color, hover_color=self.button_hover_color,
                                         text_color=self.text_color)

    def browse_directory(self):
        directory = tk.filedialog.askdirectory(parent=self)
        if directory:
            self.selected_path.set(directory)

    def convert_and_save(self):
        output_dir = self.selected_path.get()
        if not output_dir:
            self.parent.show_temp_message("Please select a directory to save the PDF.", 2000)
            return

        # Call the PDF content generation function passed from parent
        self.pdf_content_func(output_dir)
        self.destroy()


class SpellCheckPopup(tk.Toplevel):
    """A custom-themed pop-up window for spell checking."""

    def __init__(self, parent, misspelled_data, text_widget):
        super().__init__(parent)
        self.parent = parent
        self.misspelled_data = misspelled_data
        self.text_widget = text_widget
        self.current_word_index = 0

        self.withdraw()
        self.overrideredirect(True)
        self.geometry("400x350")
        self.attributes("-alpha", 0.98)

        self.bg_color = "#B48C68"
        self.main_color = "#C7B6A4"
        self.text_color = "#4A4A4A"
        self.button_color = "#E5E5E5"
        self.button_hover_color = "#DCDCDC"

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
        self.geometry(f'{w}x{h}+{px + (pw // 2) - (w // 2)}+{py + (ph // 2) - (h // 2)}')

    def setup_ui(self):
        self.canvas.configure(bg=self.bg_color)
        # Use parent's draw_rounded_rectangle which now returns item IDs
        self.parent.draw_rounded_rectangle(self.canvas, 5, 5, 395, 345, radius=20, fill=self.main_color,
                                           tags="popup_bg")

        self.close_btn_id = self.canvas.create_text(380, 20, text="X", font=("Georgia", 14, "bold"),
                                                    fill=self.text_color, tags="close_btn")
        # Add hover effect for close button
        self.canvas.tag_bind("close_btn", "<Enter>",
                             lambda e: self.config(cursor="hand2") or self.canvas.itemconfig(self.close_btn_id,
                                                                                             fill="#C0392B"))
        self.canvas.tag_bind("close_btn", "<Leave>",
                             lambda e: self.config(cursor="") or self.canvas.itemconfig(self.close_btn_id,
                                                                                        fill=self.text_color))
        self.canvas.tag_bind("close_btn", "<Button-1>", lambda e: self.destroy())

    def display_next_error(self):
        self.canvas.delete("suggestion_elements")
        if self.current_word_index >= len(self.misspelled_data):
            # Ensure "Spell check complete!" text is explicitly centered and higher up
            self.canvas.create_text(200, 70, text="Spell check complete!", font=("Georgia", 16),  # Changed y to 70
                                    fill=self.text_color, tags="suggestion_elements", anchor="center")
            self.after(1500, self.destroy)
            return

        data = self.misspelled_data[self.current_word_index]
        word, suggestions = data['word'], data['suggestions']

        self.canvas.create_text(200, 50, text="Misspelled Word:", font=("Georgia", 12),
                                fill=self.text_color, tags="suggestion_elements")
        self.canvas.create_text(200, 80, text=f"'{word}'", font=("Georgia", 18, "bold"),
                                fill="#C0392B", tags="suggestion_elements")

        y_pos = 120
        for i, sug in enumerate(suggestions[:5]):
            btn_tag = f"sug_{i}"
            # Ensure suggestion buttons are centered at X=200
            self.parent.create_canvas_button(self.canvas, 100, y_pos, 300, y_pos + 30, text=sug, tag=btn_tag,
                                             command=lambda s=sug: self.replace_word(s), corner_radius=15,
                                             bg_color=self.button_color, hover_color=self.button_hover_color,
                                             text_color=self.text_color, font_size=12)
            y_pos += 40

        # Center the "Ignore" button horizontally with the suggestion buttons
        ignore_btn_width = 150
        ignore_btn_x1 = 200 - (ignore_btn_width / 2)
        ignore_btn_x2 = 200 + (ignore_btn_width / 2)
        self.parent.create_canvas_button(self.canvas, ignore_btn_x1, 300, ignore_btn_x2, 330, "Ignore", "ignore_btn",
                                         self.next_error, corner_radius=15, font_size=12,
                                         bg_color=self.button_color, hover_color=self.button_hover_color,
                                         text_color=self.text_color)

    def replace_word(self, suggestion):
        data = self.misspelled_data[self.current_word_index]
        self.parent.replace_text_at_index(data['index'], data['word'], suggestion)
        self.next_error()

    def next_error(self):
        self.current_word_index += 1
        self.display_next_error()


import time

# --- NEW IMPORTS for direct Windows API access ---
try:
    import win32com.client
    import pythoncom
except ImportError:
    print("CRITICAL ERROR: 'pywin32' library not found.")
    print("Please run: pip install pywin32")
    sys.exit()


class TextToSpeechPopup(tk.Toplevel):
    """
    A definitive TTS popup using the pywin32 library for direct, responsive
    control over the native Windows SAPI5 speech engine.
    This version correctly handles settings changes during playback.
    """

    def __init__(self, parent, text_to_speak):
        super().__init__(parent)
        self.parent = parent
        self.full_text = text_to_speak.strip() if text_to_speak.strip() else "There is no text to read."

        # --- State Management ---
        self.is_paused = False
        self.is_stopped = True
        self.check_status_job = None

        # --- SAPI5 Engine Initialization ---
        try:
            pythoncom.CoInitialize()
            self.voice = win32com.client.Dispatch("SAPI.SpVoice")
            self.voice_map, self.default_rate = self._get_windows_voices()
            if not self.voice_map:
                raise RuntimeError("No SAPI5 TTS voices found on this system.")
            self.selected_voice_token = list(self.voice_map.values())[0]
        except Exception as e:
            print(f"Failed to initialize Windows SAPI5 engine: {e}")
            self.parent.show_temp_message(f"TTS Error: {e}", 3000)
            self.after(50, self.destroy)
            return

        self.speed_options = ["0.75x", "1.0x (Normal)", "1.25x", "1.5x", "1.75x", "2.0x"]
        self.sapi_rate_map = {
            "0.75x": -2, "1.0x (Normal)": 0, "1.25x": 2,
            "1.5x": 5, "1.75x": 8, "2.0x": 10
        }
        self.selected_speed_option = tk.StringVar(value="1.0x (Normal)")

        # --- Standard UI Setup ---
        self.withdraw()
        self.overrideredirect(True)
        self.geometry("400x300")
        self.attributes("-alpha", 0.98)
        self.main_color, self.text_color = "#C7B6A4", "#4A4A4A"
        self.button_color, self.button_hover_color = "#E5E5E5", "#DCDCDC"
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

    def _get_windows_voices(self):
        voice_map = {}
        for token in self.voice.GetVoices():
            voice_map[token.GetDescription()] = token
        default_rate = self.voice.Rate
        return voice_map, default_rate

    def setup_ui(self):
        self.parent.draw_rounded_rectangle(self.canvas, 5, 5, 395, 295, radius=20, fill=self.main_color,
                                           tags="popup_bg")
        self.close_btn_id = self.canvas.create_text(380, 20, text="X", font=("Georgia", 14, "bold"),
                                                    fill=self.text_color, tags="tts_close")
        self.canvas.tag_bind("tts_close", "<Button-1>", lambda e: self.on_close())
        self.canvas.tag_bind("tts_close", "<Enter>",
                             lambda e: self.config(cursor="hand2") or self.canvas.itemconfig(self.close_btn_id,
                                                                                             fill="#C0392B"))
        self.canvas.tag_bind("tts_close", "<Leave>",
                             lambda e: self.config(cursor="") or self.canvas.itemconfig(self.close_btn_id,
                                                                                        fill=self.text_color))

        self.canvas.create_text(70, 80, text="Voice:", font=("Georgia", 12), fill=self.text_color, anchor="w")
        self.voice_combo = ttk.Combobox(self.main_frame, values=list(self.voice_map.keys()), state='readonly', width=30,
                                        style='TCombobox')
        default_voice_name = self.selected_voice_token.GetDescription()
        self.voice_combo.set(default_voice_name)
        self.voice_combo.place(x=130, y=70)
        self.voice_combo.bind("<<ComboboxSelected>>", self.on_voice_change)

        self.canvas.create_text(70, 130, text="Speed:", font=("Georgia", 12), fill=self.text_color, anchor="w")
        self.speed_combo = ttk.Combobox(self.main_frame, textvariable=self.selected_speed_option,
                                        values=self.speed_options, state='readonly', width=15, style='TCombobox')
        self.speed_combo.place(x=130, y=120)
        self.speed_combo.bind("<<ComboboxSelected>>", self.on_speed_change)

        self.play_pause_button_id = self.parent.create_canvas_button(self.canvas, 100, 200, 200, 250, "Play",
                                                                     "play_pause_btn", self.toggle_play_pause,
                                                                     corner_radius=25, font_size=18,
                                                                     bg_color=self.button_color,
                                                                     hover_color=self.button_hover_color,
                                                                     text_color=self.text_color)
        self.stop_button_id = self.parent.create_canvas_button(self.canvas, 210, 200, 310, 250, "Stop", "stop_btn",
                                                               self.stop_playback, corner_radius=25, font_size=18,
                                                               bg_color=self.button_color,
                                                               hover_color=self.button_hover_color,
                                                               text_color=self.text_color)

    def on_voice_change(self, event=None):
        """
        Called when a new voice is selected.
        This now STOPS any current playback and resets the state.
        """
        # First, update the selected voice token
        self.selected_voice_token = self.voice_map[self.voice_combo.get()]

        # --- NEW LOGIC TO RESET PLAYBACK ---
        # If we are currently playing or paused, stop everything.
        if not self.is_stopped:
            self.stop_playback()

    def on_speed_change(self, event=None):
        """
        Called when speed dropdown changes.
        This now also STOPS any current playback to apply the new speed from the start.
        """
        # First, apply the new rate setting for the next playback
        new_rate = self.sapi_rate_map[self.selected_speed_option.get()]
        self.voice.Rate = new_rate

        # --- NEW LOGIC TO RESET PLAYBACK ---
        # If we are currently playing or paused, stop everything.
        if not self.is_stopped:
            self.stop_playback()

    def update_play_pause_button(self, text):
        text_item_id = self.canvas.find_withtag("play_pause_btn_text")
        if text_item_id:
            self.canvas.itemconfig(text_item_id, text=text)

    def toggle_play_pause(self):
        if self.is_stopped:
            self.start_playback()
        elif self.is_paused:
            self.resume_playback()
        else:
            self.pause_playback()

    def start_playback(self):
        self.is_stopped = False
        self.is_paused = False
        self.update_play_pause_button("Pause")

        self.voice.Voice = self.selected_voice_token
        self.voice.Rate = self.sapi_rate_map[self.selected_speed_option.get()]

        # SVSF_ASYNC = 1 -> non-blocking
        self.voice.Speak(self.full_text, 1)

        self._check_playback_status()

    def pause_playback(self):
        if not self.is_stopped and not self.is_paused:
            self.is_paused = True
            self.voice.Pause()
            self.update_play_pause_button("Resume")

    def resume_playback(self):
        if self.is_paused:
            self.is_paused = False
            self.voice.Resume()
            self.update_play_pause_button("Pause")

    def stop_playback(self):
        if not self.is_stopped:
            self.is_stopped = True
            self.is_paused = False
            # SVSF_PURGEBEFORESPEAK = 2. Flags combined = 3.
            self.voice.Speak("", 3)

        self.update_play_pause_button("Play")

    def _check_playback_status(self):
        if self.check_status_job:
            self.after_cancel(self.check_status_job)

        if not self.is_stopped and self.voice.Status.RunningState != 1:
            self.check_status_job = self.after(100, self._check_playback_status)
        else:
            if not self.is_stopped:  # If it finished naturally
                self.is_stopped = True
                self.is_paused = False
                self.update_play_pause_button("Play")

    def on_close(self):
        self.stop_playback()
        if self.check_status_job:
            self.after_cancel(self.check_status_job)
        self.destroy()

    # --- Window movement and centering methods (unchanged) ---
    def start_move(self, event):
        self.x, self.y = event.x, event.y

    def move_window(self, event):
        self.geometry(f"+{self.winfo_x() + event.x - self.x}+{self.winfo_y() + event.y - self.y}")

    def center_window(self):
        self.update_idletasks()
        px, py = self.parent.winfo_x(), self.parent.winfo_y()
        pw, ph = self.parent.winfo_width(), self.parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f'{w}x{h}+{px + (pw // 2) - (w // 2)}+{py + (ph // 2) - (h // 2)}')
class LitLoomApp(tk.Tk):
    """
    The main application window for Lit-Loom. This class manages the UI,
    state (which page is active), and all functional logic.
    """

    def __init__(self):
        super().__init__()
        self.title("◆ LitLoom")
        self.geometry("800x600")
        self.minsize(600, 450)
        self.configure(bg="#CBBFAC")

        self.current_page = "welcome"
        self.poem_text = ""
        self.current_font_size = 14
        self.active_analysis_button = "overview"
        self.resize_job_id = None
        self.last_width, self.last_height = 0, 0
        self.current_poem_index = 0

        self.button_bg_color = "#A6876D"
        self.button_hover_color = "#92755E"
        self.control_button_color = "#E5E5E5"
        self.control_button_hover_color = "#DCDCDC"

        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.spell = SpellChecker()
        self.editor_text_widget = None
        self.analysis_text_widget = None

        self.example_poems = [
            (
                "The rose is sick. Invisible worm,\nThat flies in the nyght, in the howling storm,\nHas found out thy bed of crimson joy,\nAnd his dark secret love does thy life destroy."),
            (
                "I wandered lonely as a clowd\nThat floats on high o'er vales and hills,\nWhen all at once I saw a crowd,\nA host, of golden daffodills."),
            (
                "Two roads diverged in a yellow wood,\nAnd sorry I could not travel both\nAnd be one traveler, long I stood\nAnd looked down one as far as I could\nTo where it bent in the undergrowth;\n\nThen took the other, as just as fair,\nAnd having perhaps the better claim,\nBecause it was grassy and wanted wear;\nThough as for that the passing there\nHad worn them really about the same.")
        ]

        self.original_fg_image = None
        self.original_bg_image = None
        self.original_logo_image = None
        self.original_title_image = None
        self.original_bottom_sound_icon_image = None
        self.original_top_sound_icon_image = None
        self.original_welcome_icon_image = None  # New attribute for welcome icon

        self.fg_photo, self.bg_photo, self.logo_photo, self.title_photo, \
            self.bottom_sound_icon_photo, self.top_sound_icon_photo, self.welcome_icon_photo = [None] * 7  # Added welcome_icon_photo

        self.load_images()
        self.setup_styles()

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bind_events()

        self.after(50, self.redraw_canvas, True)

    # Modified draw_rounded_rectangle to use Tkinter primitives
    def draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        # Ensure coordinates are integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        radius = int(radius)

        fill_color = kwargs.get('fill', 'black')
        outline_color = kwargs.get('outline', fill_color)  # use fill_color for outline if not specified
        width = kwargs.get('width', 0)
        tags = kwargs.get('tags', '')

        item_ids = []

        # Draw the rectangular parts
        item_ids.append(canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2,
                                                fill=fill_color, outline=outline_color, width=width, tags=tags))
        item_ids.append(canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius,
                                                fill=fill_color, outline=outline_color, width=width, tags=tags))

        # Draw the corner arcs (pieslice style for solid corners)
        item_ids.append(canvas.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius,
                                          start=90, extent=90, style=tk.PIESLICE,
                                          fill=fill_color, outline=outline_color, width=width, tags=tags))
        item_ids.append(canvas.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius,
                                          start=0, extent=90, style=tk.PIESLICE,
                                          fill=fill_color, outline=outline_color, width=width, tags=tags))
        item_ids.append(canvas.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2,
                                          start=270, extent=90, style=tk.PIESLICE,
                                          fill=fill_color, outline=outline_color, width=width, tags=tags))
        item_ids.append(canvas.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2,
                                          start=180, extent=90, style=tk.PIESLICE,
                                          fill=fill_color, outline=outline_color, width=width, tags=tags))
        return item_ids  # Return all created item IDs

    def load_images(self):
        """Loads all images, with fallbacks if they are not found.
        Combines robust loading from Version A with image list from Version B.
        """
        image_info = {
            'fg': {'attr': 'original_fg_image', 'file': "background.jpeg", 'convert_rgba': False,
                   'apply_rounded': True},
            'bg': {'attr': 'original_bg_image', 'file': "bg.jpeg", 'convert_rgba': False, 'apply_rounded': False},
            'logo': {'attr': 'original_logo_image', 'file': "Quill With Ink.png", 'convert_rgba': False,
                     'apply_rounded': False},
            'title': {'attr': 'original_title_image', 'file': "LitLoom.png", 'convert_rgba': False,
                      'apply_rounded': False},
            'bottom_sound_icon': {'attr': 'original_bottom_sound_icon_image', 'file': "Sound II.png",
                                  'convert_rgba': True, 'apply_rounded': False},
            'top_sound_icon': {'attr': 'original_top_sound_icon_image', 'file': "Sound I.png", 'convert_rgba': True,
                               'apply_rounded': False},
            'welcome_icon': {'attr': 'original_welcome_icon_image', 'file': "open-book.png", 'convert_rgba': True,
                             'apply_rounded': False}  # New image info
        }

        base_dir = os.path.dirname(os.path.abspath(__file__))

        for key, info in image_info.items():
            filename = info['file']
            attr_name = info['attr']

            found_path = None
            asset_path = os.path.join(base_dir, 'assets', filename)
            if os.path.exists(asset_path):
                found_path = asset_path
            else:
                current_dir_path = os.path.join(base_dir, filename)
                if os.path.exists(current_dir_path):
                    found_path = current_dir_path

            if found_path:
                try:
                    img = Image.open(found_path)
                    if info['convert_rgba']:
                        img = img.convert('RGBA')
                    if info['apply_rounded']:
                        img = self.add_rounded_corners_to_image(img, 30)
                    setattr(self, attr_name, img)
                except Exception as e:
                    print(f"ERROR: Could not load image '{filename}' from '{found_path}': {e}")
                    setattr(self, attr_name, None)
            else:
                print(f"WARNING: Image '{filename}' not found in 'assets/' or current directory.")
                setattr(self, attr_name, None)

        if (self.original_bg_image is None) and (self.original_fg_image is None) and (
                self.original_title_image is None):
            print(
                "CRITICAL: Neither background, foreground, nor title image could be loaded. UI may appear incomplete.")

    def setup_styles(self):
        """Configures styles for ttk widgets."""
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground='#F0F0F0', background='#F0F0F0', foreground='#4A4A4A',
                        arrowcolor='#4A4A4A', selectbackground='#D9CFC1', bordercolor="#CBBFAC")
        style.map('TCombobox', fieldbackground=[('readonly', '#F0F0F0')])
        style.configure("Vertical.TScrollbar", gripcount=0, background="#D9CFC1", troughcolor="#F0F0F0",
                        bordercolor="#F0F0F0", arrowcolor="#4A4A4A")

    def bind_events(self):
        """Centralized event binding for consistent hover/click behavior."""
        self.bind("<Configure>", self.handle_resize)

    def _on_button_hover(self, event, tag, bg_color, hover_color):
        self.config(cursor="hand2")
        # Find all items with the background tag and change their fill
        for item_id in self.canvas.find_withtag(f"{tag}_bg"):
            self.canvas.itemconfig(item_id, fill=hover_color)

    def _on_button_leave(self, event, tag, bg_color, hover_color):
        self.config(cursor="")
        # Find all items with the background tag and revert their fill
        for item_id in self.canvas.find_withtag(f"{tag}_bg"):
            self.canvas.itemconfig(item_id, fill=bg_color)

    def _on_icon_button_hover(self, event, tag, bg_color, hover_color):
        self.config(cursor="hand2")
        # Find all items with the background tag and change their fill
        for item_id in self.canvas.find_withtag(f"{tag}_bg"):
            self.canvas.itemconfig(item_id, fill=hover_color)

    def _on_icon_button_leave(self, event, tag, bg_color, hover_color):
        self.config(cursor="")
        # Find all items with the background tag and revert their fill
        for item_id in self.canvas.find_withtag(f"{tag}_bg"):
            self.canvas.itemconfig(item_id, fill=bg_color)

    def handle_resize(self, event):
        if self.resize_job_id: self.after_cancel(self.resize_job_id)
        self.resize_job_id = self.after(50, self.redraw_canvas)

    def redraw_canvas(self, force_redraw=False):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        size_changed = (w != self.last_width or h != self.last_height)
        if not size_changed and not force_redraw: return

        editor_content_before_redraw = ""
        # Check if editor_text_widget exists and is a valid window before trying to get text
        if self.editor_text_widget and self.editor_text_widget.winfo_exists():
            editor_content_before_redraw = self.editor_text_widget.get("1.0", tk.END).strip()

        self.canvas.delete("all")
        # Ensure all window widgets (Text widgets, Comboboxes etc.) are destroyed before redrawing
        for widget_id in self.canvas.find_all():
            if self.canvas.type(widget_id) == 'window':
                window_widget = self.canvas.itemcget(widget_id, 'window')
                # Check if window_widget is a valid Tkinter widget and if it exists
                if isinstance(window_widget, tk.Widget) and window_widget.winfo_exists():
                    window_widget.destroy()
        self.editor_text_widget = None
        self.analysis_text_widget = None

        if self.current_page == "welcome":
            self.draw_welcome_page(w, h, size_changed)
        elif self.current_page == "editor":
            self.draw_poem_editor_page(w, h, size_changed)
            if editor_content_before_redraw:
                self.editor_text_widget.insert("1.0", editor_content_before_redraw)
        elif self.current_page == "analysis":
            self.draw_analysis_page(w, h, size_changed)
            getattr(self, f"_generate_{self.active_analysis_button}_content")()

        self.last_width, self.last_height = w, h

    def create_canvas_button(self, canvas, x1, y1, x2, y2, text, tag, command, corner_radius=20, font_size=12,
                             bg_color=None, hover_color=None, text_color="#4A4A4A"):
        # Ensure coordinates are integers before passing
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        bg_color = bg_color if bg_color is not None else self.control_button_color
        hover_color = hover_color if hover_color is not None else self.control_button_hover_color

        # Draw the rounded rectangle background using the modified draw_rounded_rectangle
        bg_item_ids = self.draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius=corner_radius, fill=bg_color,
                                                  tags=(f"{tag}_bg", tag))

        text_id = canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=("Georgia", font_size, "bold"),
                                     fill=text_color, tags=(f"{tag}_text", tag))

        # Pass event parameter to lambda if command expects it
        import inspect
        if inspect.isfunction(command) or inspect.ismethod(command):
            sig = inspect.signature(command)
            if len(sig.parameters) == 1 and list(sig.parameters.keys())[0] == 'event':
                canvas.tag_bind(tag, "<Button-1>", command)
            else:
                canvas.tag_bind(tag, "<Button-1>", lambda e: command())
        else:
            canvas.tag_bind(tag, "<Button-1>", lambda e: command())

        # Button hover effect: change color only, no movement
        canvas.tag_bind(tag, "<Enter>", lambda e: self._on_button_hover(e, tag, bg_color, hover_color))
        canvas.tag_bind(tag, "<Leave>", lambda e: self._on_button_leave(e, tag, bg_color, hover_color))

        return text_id

    def create_sidebar_button(self, x1, y1, x2, y2, label, tag, command, is_active=None, special_color=False):
        if is_active is None: is_active = (tag == self.active_analysis_button)
        if special_color:
            bg, hover = ("#F3D7CA", "#E2C6BA") if is_active else ("#F3D7CA", "#E2C6BA")
        else:
            bg, hover = ("#D4E2D4", "#C3D1C3") if is_active else ("#E5E5E5", "#DCDCDC")

        # Command should not receive an event from lambda here, as it's for internal call
        self.create_canvas_button(self.canvas, x1, y1, x2, y2, label, tag, lambda: command(), 15, 14, bg_color=bg,
                                  hover_color=hover, text_color="#4A4A4A")

    def create_icon_button(self, x, y, image, tag, command, width=40, height=40, bg_color=None, hover_color=None):
        canvas_ref = self.canvas
        bg_color = bg_color if bg_color is not None else self.control_button_color
        hover_color = hover_color if hover_color is not None else self.control_button_hover_color

        # Calculate bounding box for the background rectangle
        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        # Draw a rounded rectangle background
        bg_item_ids = self.draw_rounded_rectangle(canvas_ref, x1, y1, x2, y2, radius=width / 2, fill=bg_color,
                                                  tags=(f"{tag}_bg", tag))

        # IMPORTANT: Create a COPY of the image before thumbnailing
        if hasattr(image, 'copy'):
            temp_img = image.copy()
        else:
            temp_img = image  # If it's already PhotoImage, no need to copy

        # Thumbnail modifies in-place, returns None. So, use it and then pass temp_img.
        if hasattr(temp_img, 'thumbnail'):
            temp_img.thumbnail((width * 0.7, height * 0.7), Image.Resampling.LANCZOS)  # Scale icon slightly smaller

        # Convert PIL image to PhotoImage (handle cases where image might already be PhotoImage)
        if not isinstance(image, ImageTk.PhotoImage):
            image_to_use = ImageTk.PhotoImage(temp_img)
            # Store reference to prevent garbage collection
            canvas_ref.image_references = getattr(canvas_ref, 'image_references', [])
            canvas_ref.image_references.append(image_to_use)
        else:
            image_to_use = image  # If it's already PhotoImage, use it directly

        item_id = canvas_ref.create_image(int(x), int(y), image=image_to_use, anchor="center",
                                          tags=(f"{tag}_image", tag))

        import inspect
        if inspect.isfunction(command) or inspect.ismethod(command):
            sig = inspect.signature(command)
            if len(sig.parameters) == 1 and list(sig.parameters.keys())[0] == 'event':
                canvas_ref.tag_bind(tag, "<Button-1>", command)
            else:
                canvas_ref.tag_bind(tag, "<Button-1>", lambda e: command())
        else:
            canvas_ref.tag_bind(tag, "<Button-1>", lambda e: command())

        # Bind hover/leave events to the new background and image (color change only)
        canvas_ref.tag_bind(tag, "<Enter>", lambda e: self._on_icon_button_hover(e, tag, bg_color, hover_color))
        canvas_ref.tag_bind(tag, "<Leave>", lambda e: self._on_icon_button_leave(e, tag, bg_color, hover_color))
        return item_id

    def draw_welcome_page(self, w, h, size_changed):
        if (size_changed or not self.bg_photo) and self.original_bg_image:
            if self.original_bg_image:
                img = self.original_bg_image.resize((w, h), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(img)
            else:
                self.bg_photo = None
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        else:
            self.canvas.configure(bg="#FDFDFD")

        # Add icon to top left of welcome page
        if (size_changed or not self.welcome_icon_photo) and self.original_welcome_icon_image:
            if self.original_welcome_icon_image:
                img_copy = self.original_welcome_icon_image.copy().convert('RGBA')
                icon_size = 50
                img_copy.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
                self.welcome_icon_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.welcome_icon_photo = None
        if self.welcome_icon_photo:
            # Create a dummy command as this icon is probably just for decoration
            self.create_icon_button(30, 30, self.welcome_icon_photo, "welcome_app_icon", lambda: None,
                                    width=50, height=50, bg_color="#C7B6A4", hover_color="#D9CFC1")

        if (size_changed or not self.fg_photo) and self.original_fg_image:
            if self.original_fg_image:
                img = self.original_fg_image.copy()
                img.thumbnail((w * 0.85, h * 0.75), Image.Resampling.LANCZOS)
                self.fg_photo = ImageTk.PhotoImage(self.add_rounded_corners_to_image(img, 30))
            else:
                self.fg_photo = None
        if self.fg_photo: self.canvas.create_image(w / 2, h / 2 + h * 0.05, image=self.fg_photo)  # Centered better

        if (size_changed or not self.title_photo) and self.original_title_image:
            if self.original_title_image:
                img = self.original_title_image.copy()
                img.thumbnail((w * 0.4, 100), Image.Resampling.LANCZOS)
                self.title_photo = ImageTk.PhotoImage(img)
            else:
                self.title_photo = None
        if self.title_photo:
            self.canvas.create_image(w / 2, h * 0.15, image=self.title_photo)
        else:
            self.canvas.create_text(w / 2, h * 0.15, text="Lit-Loom", font=("Georgia", 60, "bold"), fill="white")

        btn_w, btn_h, btn_cx, btn_cy = 200, 50, w / 2, h * 0.55
        self.create_canvas_button(self.canvas, btn_cx - btn_w / 2, btn_cy - btn_h / 2, btn_cx + btn_w / 2,
                                  btn_cy + btn_h / 2, text="Let's Go!", tag="start_btn", command=self.go_to_editor_page,
                                  corner_radius=25, font_size=16, bg_color=self.button_bg_color,
                                  hover_color=self.button_hover_color, text_color="white")

    def draw_poem_editor_page(self, w, h, size_changed):
        self.current_page = "editor"
        bg, sidebar, content, text_color = "#B48C68", "#C7B6A4", "#E5E5E5", "#4A4A4A"
        self.canvas.configure(bg=bg)
        border = 20
        self.draw_rounded_rectangle(self.canvas, border, border, w - border, h - border, radius=25, fill=sidebar,
                                    tags="main_bg")

        sidebar_w, top_m, content_p = 220, 80, 40
        self.draw_rounded_rectangle(self.canvas, sidebar_w, top_m, w - content_p, h - content_p, radius=20,
                                    fill=content, tags="content_bg")

        heading_y = (top_m + border) / 2
        self.canvas.create_text((w + sidebar_w) / 2, heading_y, text="Write Your Poem", font=("Georgia", 22, "bold"),
                                fill=text_color)

        if (size_changed or not self.logo_photo) and self.original_logo_image:
            if self.original_logo_image:
                img_copy = self.original_logo_image.copy()  # Make a copy
                img_copy.thumbnail((45, 45), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.logo_photo = None
        if self.logo_photo: self.canvas.create_image(60, 60, image=self.logo_photo)

        text_frame = tk.Frame(self, bg=content, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
        self.editor_text_widget = tk.Text(text_frame, bg=content, fg=text_color, font=("Georgia", 14), bd=0,
                                          highlightthickness=0, wrap="word", insertbackground=text_color,
                                          selectbackground=sidebar, undo=True, yscrollcommand=scrollbar.set,
                                          relief="flat")
        scrollbar.config(command=self.editor_text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self.editor_text_widget.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(sidebar_w + 10, top_m + 10, window=text_frame, anchor="nw",
                                  width=w - sidebar_w - content_p - 20, height=h - top_m - content_p - 20)

        btn_w, btn_h, btn_cx = 150, 40, sidebar_w / 2 + 10
        buttons = {
            "example_btn": {"y": 120, "text": "Add Example", "command": self.show_example_poem},
            "spell_btn": {"y": 180, "text": "Spell Correct", "command": self.run_spell_correct},
            "clear_editor_btn": {"y": 240, "text": "Clear", "command": self.clear_editor_text},
            "analyze_btn": {"y": h - 100, "text": "Analyze", "font_size": 14, "command": self.run_analyze}
        }
        for tag, props in buttons.items():
            font_size = props.get("font_size", 12)
            self.create_canvas_button(self.canvas, btn_cx - btn_w / 2, props['y'], btn_cx + btn_w / 2,
                                      props['y'] + btn_h, text=props['text'], tag=tag,
                                      command=props['command'],
                                      corner_radius=20, font_size=font_size,
                                      bg_color=self.control_button_color, hover_color=self.control_button_hover_color,
                                      text_color=text_color)

        if (size_changed or not self.bottom_sound_icon_photo) and self.original_bottom_sound_icon_image:
            if self.original_bottom_sound_icon_image:
                img_copy = self.original_bottom_sound_icon_image.copy().convert('RGBA')  # Make a copy
                icon_width = 60
                icon_height = 60
                img_copy.thumbnail((icon_width, icon_height), Image.Resampling.LANCZOS)
                self.bottom_sound_icon_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.bottom_sound_icon_photo = None
        if self.bottom_sound_icon_photo:
            self.create_icon_button(w - content_p - 35, h - content_p - 35, self.bottom_sound_icon_photo,
                                    "sound_icon_btn_bottom", self.open_tts_popup,
                                    width=60, height=60,  # Pass explicit size
                                    bg_color=self.control_button_color, hover_color=self.control_button_hover_color)

        # Alignment for top sound icon (adjusted X and Y to be within header bar)
        if (size_changed or not self.top_sound_icon_photo) and self.original_top_sound_icon_image:
            if self.original_top_sound_icon_image:
                img_copy = self.original_top_sound_icon_image.copy().convert('RGBA')  # Make a copy
                icon_width = 40
                icon_height = 40
                img_copy.thumbnail((icon_width, icon_height), Image.Resampling.LANCZOS)
                self.top_sound_icon_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.top_sound_icon_photo = None
        if self.top_sound_icon_photo:
            self.create_icon_button(w - 70, heading_y, self.top_sound_icon_photo, "sound_icon_btn_top",
                                    self.open_tts_popup,
                                    width=40, height=40,  # Pass explicit size
                                    bg_color=self.control_button_color, hover_color=self.control_button_hover_color)

    def draw_analysis_page(self, w, h, size_changed):
        self.current_page = "analysis"
        self.canvas.configure(bg="#CBBFAC")
        self.draw_rounded_rectangle(self.canvas, 240, 40, w - 40, h - 40, radius=20, fill="#F0F0F0", outline="",
                                    tags="analysis_main_bg")

        if (size_changed or not self.logo_photo) and hasattr(self, 'original_logo_image'):
            if hasattr(self, 'original_logo_image') and self.original_logo_image:
                img_copy = self.original_logo_image.copy()  # Make a copy
                img_copy.thumbnail((45, 45), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.logo_photo = None

        # Adjusted icon position for better alignment after removing "Lit-loom" text
        if self.logo_photo: self.canvas.create_image(125, 55, image=self.logo_photo)
        # Removed the Lit-loom text as requested
        # self.canvas.create_text(135, 55, text="Lit-loom", font=("Georgia", 22, "bold"), fill="#4A4A4A")

        btn_y = 120
        btn_config = {"overview": "Overview", "parts_of_speech": "Parts of speech",
                      "figure_of_speech": "Figure of speech", "tone": "Tone"}
        for tag, label in btn_config.items():
            # For sidebar buttons, the command should call switch_active_analysis with the tag
            self.create_sidebar_button(30, btn_y, 210, btn_y + 45, label, tag,
                                       command=lambda t=tag: self.switch_active_analysis(t),
                                       is_active=(self.active_analysis_button == tag))
            btn_y += 60
        # "Back to poem" button
        self.create_sidebar_button(30, btn_y, 210, btn_y + 45, "Back to poem", "back_to_poem", self.go_back_to_editor,
                                   is_active=False)

        # Adjusted "Language" label and dropdown positions for better alignment and spacing
        self.canvas.create_text(125, h - 190, text="Language", font=("Georgia", 14), fill="#5a5a5a")  # Moved up

        self.create_sidebar_button(30, h - 170, 210, h - 125, "Translation", "translation",  # Adjusted y for button
                                   command=lambda: self.switch_active_analysis("translation"),
                                   is_active=(self.active_analysis_button == 'translation'), special_color=True)

        supported_langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)
        self.all_langs_display_names = sorted(list(supported_langs_dict.keys()))
        self.all_langs_codes = supported_langs_dict

        self.lang_var = tk.StringVar(self)
        self.lang_dropdown = ttk.Combobox(self, textvariable=self.lang_var, values=self.all_langs_display_names,
                                          state='readonly', width=18,
                                          style='TCombobox', font=("Georgia", 10))
        self.lang_dropdown.set("Select Language...")
        self.lang_dropdown.bind("<<ComboboxSelected>>", self.translate_poem_for_display)
        # Adjusted y position to be below the Translation button, with some spacing
        self.canvas.create_window(125, h - 100,
                                  window=self.lang_dropdown)  # This was h - 100 before, now shifted to avoid overlap

        # Add "Convert to PDF" button - calls open_pdf_export_dialog
        self.create_sidebar_button(30, h - 60, 210, h - 15, "Convert to PDF", "convert_pdf_btn",
                                   self.open_pdf_export_dialog,  # Adjusted y position
                                   is_active=False)

        text_frame = tk.Frame(self, bg="#F0F0F0", bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
        self.analysis_text_widget = tk.Text(text_frame, bg="#F0F0F0", fg="#4A4A4A",
                                            font=("Georgia", self.current_font_size), bd=0, highlightthickness=0,
                                            wrap="word", yscrollcommand=scrollbar.set, relief="flat", state='disabled')
        scrollbar.config(command=self.analysis_text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self.analysis_text_widget.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(250, 90, window=text_frame, anchor="nw", width=w - 300, height=h - 140)

        if (size_changed or not self.top_sound_icon_photo) and hasattr(self, 'original_top_sound_icon_image'):
            if hasattr(self, 'original_top_sound_icon_image') and self.original_top_sound_icon_image:
                img_copy = self.original_top_sound_icon_image.copy()  # Make a copy
                icon_width = 35
                icon_height = 35
                img_copy.thumbnail((icon_width, icon_height), Image.Resampling.LANCZOS)
                self.top_sound_icon_photo = ImageTk.PhotoImage(img_copy)
            else:
                self.top_sound_icon_photo = None

        # Adjusted icon position for better alignment
        self.create_icon_button(w - 60, 60, self.top_sound_icon_photo, "audio_btn",
                                self.open_tts_popup,
                                width=35, height=35,  # Pass explicit size
                                bg_color=self.control_button_color, hover_color=self.control_button_hover_color)

        self.canvas.create_text(w - 260, h - 60, text="size:", font=("Georgia", 12), fill="#5a5a5a")
        # Font size and clear buttons
        self.create_canvas_button(self.canvas, w - 220, h - 75, w - 180, h - 45, "–", "font_dec", self.decrease_font,
                                  10, 16, bg_color=self.control_button_color,
                                  hover_color=self.control_button_hover_color)
        self.create_canvas_button(self.canvas, w - 170, h - 75, w - 130, h - 45, "+", "font_inc", self.increase_font,
                                  10, 16, bg_color=self.control_button_color,
                                  hover_color=self.control_button_hover_color)
        self.create_canvas_button(self.canvas, w - 110, h - 75, w - 50, h - 45, "Clear", "clear_an",
                                  self.clear_analysis_text, 10, 10, bg_color=self.control_button_color,
                                  hover_color=self.control_button_hover_color)

    def add_rounded_corners_to_image(self, img, radius):
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        safe_radius = min(radius, img.width // 2, img.height // 2)
        draw.rounded_rectangle((0, 0) + img.size, radius=safe_radius, fill=255)
        img.putalpha(mask)
        return img

    def go_to_editor_page(self, event=None):
        self.current_page = "editor"
        self.redraw_canvas(force_redraw=True)

    def run_analyze(self, event=None):
        text = self.editor_text_widget.get("1.0", tk.END).strip()
        if not text:
            self.show_temp_message("Please enter a poem to analyze.", duration_ms=2000)
            return
        self.poem_text = text
        self.current_page = "analysis"
        self.active_analysis_button = "overview"
        self.redraw_canvas(force_redraw=True)

    def go_back_to_editor(self, event=None):
        self.current_page = "editor"
        self.redraw_canvas(force_redraw=True)

    def clear_editor_text(self, event=None):
        if hasattr(self, 'editor_text_widget') and self.editor_text_widget.winfo_exists():
            self.editor_text_widget.delete("1.0", tk.END)

    def show_example_poem(self, event=None):
        if not hasattr(self, 'editor_text_widget') or not self.editor_text_widget.winfo_exists(): return
        self.editor_text_widget.delete("1.0", tk.END)
        self.editor_text_widget.insert("1.0", self.example_poems[self.current_poem_index])
        self.current_poem_index = (self.current_poem_index + 1) % len(self.example_poems)

    def run_spell_correct(self, event=None):
        if not hasattr(self, 'editor_text_widget') or not self.editor_text_widget.winfo_exists(): return
        content = self.editor_text_widget.get("1.0", tk.END)
        if not content.strip():
            self.show_temp_message("No text to spell check.", duration_ms=2000)
            return

        words = set(re.findall(r'\b\w+\b', content.lower()))
        misspelled = self.spell.unknown(words)
        misspelled_data = []
        if misspelled:
            for word_lower in sorted(list(misspelled)):
                start_pos = "1.0"
                while True:
                    idx = self.editor_text_widget.search(word_lower, start_pos, stopindex=tk.END, nocase=1,
                                                         regexp=False)
                    if not idx:
                        break
                    end_idx = f"{idx}+{len(word_lower)}c"
                    actual_word_in_text = self.editor_text_widget.get(idx, end_idx)
                    misspelled_data.append({
                        'word': actual_word_in_text,
                        'index': idx,
                        'suggestions': list(self.spell.candidates(word_lower))
                    })
                    start_pos = end_idx
            if misspelled_data:
                SpellCheckPopup(self, misspelled_data, self.editor_text_widget)
            else:
                self.show_temp_message("No misspelled words found.", duration_ms=2000)

    def replace_text_at_index(self, index, old, new):
        if hasattr(self, 'editor_text_widget') and self.editor_text_widget.winfo_exists():
            self.editor_text_widget.delete(index, f"{index}+{len(old)}c")
            self.editor_text_widget.insert(index, new)

    def open_tts_popup(self, event=None):
        content = ""
        if self.current_page == "editor" and hasattr(self,
                                                     'editor_text_widget') and self.editor_text_widget.winfo_exists():
            content = self.editor_text_widget.get("1.0", tk.END).strip()
        elif self.current_page == "analysis" and hasattr(self,
                                                         'analysis_text_widget') and self.analysis_text_widget.winfo_exists():
            content = self.analysis_text_widget.get("1.0", tk.END).strip()

        if content:
            TextToSpeechPopup(self, content)
        else:
            self.show_temp_message("No text to read aloud.", duration_ms=2000)

    def increase_font(self):
        self.current_font_size = min(32, self.current_font_size + 2)
        self.redraw_canvas(force_redraw=True)

    def decrease_font(self):
        self.current_font_size = max(8, self.current_font_size - 2)
        self.redraw_canvas(force_redraw=True)

    def clear_analysis_text(self):
        self.update_analysis_widget("", "")

    def show_temp_message(self, message, duration_ms=2000):
        message_tag = "temp_message"
        self.canvas.delete(message_tag)

        cx, cy = self.winfo_width() / 2, self.winfo_height() / 2

        self.canvas.create_text(cx, cy, text=message, font=("Georgia", 16, "bold"),
                                fill="#C0392B", tags=message_tag, justify="center")
        self.canvas.after(duration_ms, lambda: self.canvas.delete(message_tag))

    def update_analysis_widget(self, content, title=""):
        if not hasattr(self, 'analysis_text_widget') or not self.analysis_text_widget.winfo_exists(): return
        self.analysis_text_widget.config(state='normal')
        self.analysis_text_widget.delete('1.0', tk.END)
        self.analysis_text_widget.tag_configure("h1", font=("Georgia", self.current_font_size + 4, "bold"), spacing3=15)
        self.analysis_text_widget.tag_configure("content", lmargin1=15, lmargin2=15)
        if title: self.analysis_text_widget.insert('1.0', title + "\n\n", "h1")
        self.analysis_text_widget.insert(tk.END, content, "content")
        self.analysis_text_widget.config(state='disabled')

    def switch_active_analysis(self, button_tag):
        self.active_analysis_button = button_tag
        self.redraw_canvas(force_redraw=True)

    def _generate_overview_content(self):
        lines = self.poem_text.strip().split('\n')
        num_lines = len(lines)
        num_words = len(word_tokenize(self.poem_text))
        scheme, rhymes = self.analyze_rhyme_scheme(lines)

        # Add a brief content overview of the poem
        poem_snippet = self.poem_text[:200] + "..." if len(self.poem_text) > 200 else self.poem_text
        content_overview = f"Content Snippet:\n  \"{poem_snippet}\"\n\n"

        overview_text = f"The poem has {num_lines} lines and {num_words} words."
        rhyme_scheme_text = f"Rhyme Scheme: {scheme if scheme else 'Not detected'}"
        rhyming_words_text = "Rhyming Word Groups:\n" + (
            '\n'.join(f"  - {' / '.join(g)}" for g in rhymes) if rhymes else "  - None detected")
        self.update_analysis_widget(f"{content_overview}{overview_text}\n\n{rhyme_scheme_text}\n\n{rhyming_words_text}",
                                    "Poem Overview")

    def _generate_parts_of_speech_content(self):
        pos_map = {
            'CC': 'Coordinating Conjunction', 'CD': 'Cardinal Number', 'DT': 'Determiner',
            'EX': 'Existential There', 'FW': 'Foreign Word', 'IN': 'Preposition/Subord. Conjunction',
            'JJ': 'Adjective', 'JJR': 'Adjective, comparative', 'JJS': 'Adjective, superlative',
            'LS': 'List Item Marker', 'MD': 'Modal Verb', 'NN': 'Noun, singular or mass',
            'NNS': 'Noun, plural', 'NNP': 'Proper Noun, singular', 'NNPS': 'Proper Noun, plural',
            'PDT': 'Predeterminer', 'POS': 'Possessive Ending', 'PRP': 'Personal Pronoun',
            'PRP$': 'Possessive Pronoun', 'RB': 'Adverb', 'RBR': 'Adverb, comparative',
            'RBS': 'Adverb, superlative', 'RP': 'Particle', 'SYM': 'Symbol', 'TO': 'To',
            'UH': 'Interjection', 'VB': 'Verb, base form', 'VBD': 'Verb, past tense',
            'VBG': 'Verb, gerund/present participle', 'VBN': 'Verb, past participle',
            'VBP': 'Verb, non-3rd pers singular present', 'VBZ': 'Verb, 3rd pers singular present',
            'WDT': 'Wh-determiner', 'WP': 'Wh-pronoun', 'WP$': 'Possessive Wh-pronoun',
            'WRB': 'Wh-adverb'
        }
        pos_groups = {}
        tokens = word_tokenize(self.poem_text)
        tagged_words = nltk.pos_tag(tokens)

        for word, tag in tagged_words:
            if re.match(r'[a-zA-Z0-9]', word):
                mapped_tag = pos_map.get(tag, 'Other')
                if mapped_tag not in pos_groups: pos_groups[mapped_tag] = set()
                pos_groups[mapped_tag].add(word.lower())

        pos_text_lines = []
        for name in sorted(pos_groups.keys()):
            words = sorted(list(pos_groups[name]))
            pos_text_lines.append(f"{name}:\n  - {', '.join(words)}")

        self.update_analysis_widget('\n\n'.join(pos_text_lines), "Parts of Speech")

    def _generate_figure_of_speech_content(self):
        sentences = sent_tokenize(self.poem_text)
        similes = []
        metaphors = []
        alliterations = []

        for s in sentences:
            if " like " in f" {s.lower()} " or " as " in f" {s.lower()} ":
                similes.append(s.strip())

        for s in sentences:
            words = word_tokenize(s.lower())
            tagged_words = nltk.pos_tag(words)
            for i in range(len(tagged_words) - 2):
                if tagged_words[i][1].startswith('NN') and tagged_words[i + 1][0] in ['is', 'are'] and \
                        tagged_words[i + 2][1].startswith('NN'):
                    if tagged_words[i][0] != tagged_words[i + 2][0] and \
                            tagged_words[i + 2][0] not in ['man', 'woman', 'person', 'thing', 'animal', 'human', 'boy',
                                                           'girl']:
                        metaphors.append(s.strip())
                        break

        for s in sentences:
            words = [w.lower() for w in word_tokenize(s) if re.match(r'[a-z]', w)]
            if len(words) < 3: continue

            initial_consonants = {}
            for word in words:
                if word and word[0] not in 'aeiou':
                    char = word[0]
                    initial_consonants.setdefault(char, []).append(word)

            for char, word_list in initial_consonants.items():
                if len(word_list) >= 3:
                    alliterations.append(
                        f"'{s.strip()}' (Words: {', '.join(sorted(list(set(word_list))))})")
                    break

        fos_text_parts = []
        fos_text_parts.append("Simile (comparison using 'like' or 'as'):")
        fos_text_parts.append('\n'.join(f'  - "{s}"' for s in similes) if similes else "  - No clear similes detected.")

        fos_text_parts.append("\n\nBasic Metaphor Detection (e.g., 'X is Y'):")
        fos_text_parts.append('\n'.join(
            f'  - "{s}"' for s in sorted(list(set(metaphors)))) if metaphors else "  - No simple metaphors detected.")

        fos_text_parts.append("\n\nBasic Alliteration Detection (repeated initial consonant sounds):")
        fos_text_parts.append('\n'.join(f'  - {a}' for a in sorted(
            list(set(alliterations)))) if alliterations else "  - No clear alliterations detected.")

        fos_text_parts.append(
            "\n\nNote: Figure of speech detection is complex and these are basic heuristics. They may not catch all instances and might have false positives.")
        self.update_analysis_widget('\n'.join(fos_text_parts), "Figures of Speech")

    def _generate_tone_content(self):
        scores = self.sentiment_analyzer.polarity_scores(self.poem_text)
        if scores['compound'] >= 0.05:
            tone, mood = "Positive", "This may suggest a mood of joy, love, or hope."
        elif scores['compound'] <= -0.05:
            tone, mood = "Negative", "This may suggest a mood of sadness, anger, or despair."
        else:
            tone, mood = "Neutral", "The language is balanced, suggesting an objective or descriptive mood."
        description = f"The overall tone appears to be {tone}.\n\n{mood}\n\nTechnical Scores:\n  - Positive: {scores['pos']:.1%}\n  - Neutral: {scores['neu']:.1%}\n  - Negative: {scores['neg']:.1%}"
        self.update_analysis_widget(description, "Sentimental Tone")

    def _generate_translation_content(self):
        self.update_analysis_widget("Please select a language from the dropdown menu below to translate the poem.",
                                    "Translation")

    def translate_poem_for_display(self, event=None):
        lang_display_name = self.lang_var.get()
        # Find the language code from the map. The map uses display_name:code.
        lang_code = None
        for display, code in self.all_langs_codes.items():
            if display == lang_display_name:
                lang_code = code
                break

        if not lang_display_name or not lang_code: return

        def do_translate():
            try:
                self.after(0, self.update_analysis_widget, "Translating...", f"Translation to {lang_display_name}")
                translated = GoogleTranslator(source='auto', target=lang_code).translate(self.poem_text)
                self.after(0, self.update_analysis_widget, translated, f"Translation to {lang_display_name}")
            except Exception as e:
                self.after(0, self.update_analysis_widget,
                           f"Translation failed. Check internet connection.\n\nError: {e}",
                           "Translation Error")

        threading.Thread(target=do_translate, daemon=True).start()

    def analyze_rhyme_scheme(self, lines):
        if not lines: return "", []

        end_words = []
        for line in lines:
            stripped_line = line.strip()
            words_in_line = stripped_line.split()
            if words_in_line:
                last_word = re.sub(r'[^\w\s]', '', words_in_line[-1]).lower()
                if last_word:
                    end_words.append(last_word)

        if not end_words: return "", []

        rhyme_labels = {}
        next_rhyme_char_code = ord('A')

        word_endings = [word[-3:] for word in end_words]

        for i, ending in enumerate(word_endings):
            word = end_words[i]
            if word in rhyme_labels:
                continue

            found_rhyme = False
            for j in range(i):
                prev_word = end_words[j]
                if prev_word[-3:] == ending:
                    rhyme_labels[word] = rhyme_labels.get(prev_word, chr(next_rhyme_char_code))
                    found_rhyme = True
                    break

            if not found_rhyme:
                rhyme_labels[word] = chr(next_rhyme_char_code)
                next_rhyme_char_code += 1

        scheme = "".join([rhyme_labels.get(word, '?') for word in end_words])

        grouped_rhymes = {}
        for word, label in rhyme_labels.items():
            if label not in grouped_rhymes:
                grouped_rhymes[label] = set()
            grouped_rhymes[label].add(word)

        return scheme, [sorted(list(g)) for g in grouped_rhymes.values()]

    def open_pdf_export_dialog(self):
        if not self.poem_text.strip():
            self.show_temp_message("No poem text to convert to PDF.", 2000)
            return
        ExportPdfPopup(self, self._generate_pdf_content)

    def _generate_pdf_content(self, output_dir):
        # This function will be called by the ExportPdfPopup with the selected directory
        pdf_filename = os.path.join(output_dir, "LitLoom_Analysis.pdf")
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        Story = []
        styles = getSampleStyleSheet()

        # Define styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['h1'],
            fontName=default_font_for_pdf,  # Use the registered font
            fontSize=18,
            leading=22,
            alignment=1,  # TA_CENTER
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['h2'],
            fontName=default_font_for_pdf,  # Use the registered font
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6
        )

        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName=default_font_for_pdf,  # Use the registered font
            fontSize=10,
            leading=12,
            spaceAfter=6
        )

        # Add overall title
        Story.append(Paragraph("LitLoom Poem Analysis Report", title_style))
        Story.append(Spacer(1, 0.2 * inch))
        Story.append(Paragraph(f"Analysis of: '{self.poem_text.splitlines()[0][:50]}...' (first line)", normal_style))
        Story.append(Spacer(1, 0.2 * inch))

        # Overview Content
        Story.append(Paragraph("1. Poem Overview", heading_style))
        lines = self.poem_text.strip().split('\n')
        num_lines = len(lines)
        num_words = len(word_tokenize(self.poem_text))
        scheme, rhymes = self.analyze_rhyme_scheme(lines)
        poem_snippet = self.poem_text[:200] + "..." if len(self.poem_text) > 200 else self.poem_text
        Story.append(Paragraph(f"Content Snippet: \"{poem_snippet}\"", normal_style))
        Story.append(Paragraph(f"The poem has {num_lines} lines and {num_words} words.", normal_style))
        Story.append(Paragraph(f"Rhyme Scheme: {scheme if scheme else 'Not detected'}", normal_style))
        rhyming_words_text = "Rhyming Word Groups:\n" + (
            '\n'.join(f"  - {' / '.join(g)}" for g in rhymes) if rhymes else "  - None detected")
        Story.append(Paragraph(rhyming_words_text.replace('\n', '<br/>'), normal_style))
        Story.append(Spacer(1, 0.2 * inch))

        # Parts of Speech Content
        Story.append(Paragraph("2. Parts of Speech", heading_style))
        pos_map = {
            'CC': 'Coordinating Conjunction', 'CD': 'Cardinal Number', 'DT': 'Determiner',
            'EX': 'Existential There', 'FW': 'Foreign Word', 'IN': 'Preposition/Subord. Conjunction',
            'JJ': 'Adjective', 'JJR': 'Adjective, comparative', 'JJS': 'Adjective, superlative',
            'LS': 'List Item Marker', 'MD': 'Modal Verb', 'NN': 'Noun, singular or mass',
            'NNS': 'Noun, plural', 'NNP': 'Proper Noun, singular', 'NNPS': 'Proper Noun, plural',
            'PDT': 'Predeterminer', 'POS': 'Possessive Ending', 'PRP': 'Personal Pronoun',
            'PRP$': 'Possessive Pronoun', 'RB': 'Adverb', 'RBR': 'Adverb, comparative',
            'RBS': 'Adverb, superlative', 'RP': 'Particle', 'SYM': 'Symbol', 'TO': 'To',
            'UH': 'Interjection', 'VB': 'Verb, base form', 'VBD': 'Verb, past tense',
            'VBG': 'Verb, gerund/present participle', 'VBN': 'Verb, past participle',
            'VBP': 'Verb, non-3rd pers singular present', 'VBZ': 'Verb, 3rd pers singular present',
            'WDT': 'Wh-determiner', 'WP': 'Wh-pronoun', 'WP$': 'Possessive Wh-pronoun',
            'WRB': 'Wh-adverb'
        }
        tokens = word_tokenize(self.poem_text)
        tagged_words = nltk.pos_tag(tokens)
        pos_groups = {}
        for word, tag in tagged_words:
            if re.match(r'[a-zA-Z0-9]', word):
                mapped_tag = pos_map.get(tag, 'Other')
                pos_groups.setdefault(mapped_tag, set()).add(word.lower())
        pos_text_lines = [f"{name}:<br/>  - {', '.join(sorted(list(pos_groups[name])))}" for name in
                          sorted(pos_groups.keys())]
        Story.append(Paragraph('<br/><br/>'.join(pos_text_lines), normal_style))
        Story.append(Spacer(1, 0.2 * inch))

        # Figure of Speech Content
        Story.append(Paragraph("3. Figures of Speech", heading_style))
        sentences = sent_tokenize(self.poem_text)
        similes = [s.strip() for s in sentences if " like " in f" {s.lower()} " or " as " in f" {s.lower()} "]
        metaphors = []
        for s in sentences:
            words = word_tokenize(s.lower())
            tagged_words = nltk.pos_tag(words)
            for i in range(len(tagged_words) - 2):
                if tagged_words[i][1].startswith('NN') and tagged_words[i + 1][0] in ['is', 'are'] and \
                        tagged_words[i + 2][1].startswith('NN'):
                    if tagged_words[i][0] != tagged_words[i + 2][0] and tagged_words[i + 2][0] not in ['man', 'woman',
                                                                                                       'person',
                                                                                                       'thing',
                                                                                                       'animal',
                                                                                                       'human', 'boy',
                                                                                                       'girl']:
                        metaphors.append(s.strip())
                        break
        alliterations = []
        for s in sentences:
            words = [w.lower() for w in word_tokenize(s) if re.match(r'[a-z]', w)]
            if len(words) >= 3:
                initial_consonants = {}
                for word in words:
                    if word and word[0] not in 'aeiou':
                        initial_consonants.setdefault(word[0], []).append(word)
                for char, word_list in initial_consonants.items():
                    if len(word_list) >= 3:
                        alliterations.append(f"'{s.strip()}' (Words: {', '.join(sorted(list(set(word_list))))})")
                        break
        fos_text_parts = []
        fos_text_parts.append("Simile (comparison using 'like' or 'as'):")
        fos_text_parts.append(
            '<br/>'.join(f'  - "{s}"' for s in similes) if similes else "  - No clear similes detected.")
        fos_text_parts.append("<br/><br/>Basic Metaphor Detection (e.g., 'X is Y'):")
        fos_text_parts.append('<br/>'.join(
            f'  - "{s}"' for s in sorted(list(set(metaphors)))) if metaphors else "  - No simple metaphors detected.")
        fos_text_parts.append("<br/><br/>Basic Alliteration Detection (repeated initial consonant sounds):")
        fos_text_parts.append('<br/>'.join(f'  - {a}' for a in sorted(
            list(set(alliterations)))) if alliterations else "  - No clear alliterations detected.")
        fos_text_parts.append(
            "<br/><br/>Note: Figure of speech detection is complex and these are basic heuristics. They may not catch all instances and might have false positives.")
        Story.append(Paragraph(''.join(fos_text_parts), normal_style))
        Story.append(Spacer(1, 0.2 * inch))

        # Tone Content
        Story.append(Paragraph("4. Sentimental Tone", heading_style))
        scores = self.sentiment_analyzer.polarity_scores(self.poem_text)
        if scores['compound'] >= 0.05:
            tone, mood = "Positive", "This may suggest a mood of joy, love, or hope."
        elif scores['compound'] <= -0.05:
            tone, mood = "Negative", "This may suggest a mood of sadness, anger, or despair."
        else:
            tone, mood = "Neutral", "The language is balanced, suggesting an objective or descriptive mood."
        description = f"The overall tone appears to be {tone}.<br/><br/>{mood}<br/><br/>Technical Scores:<br/>  - Positive: {scores['pos']:.1%}<br/>  - Neutral: {scores['neu']:.1%}<br/>  - Negative: {scores['neg']:.1%}"
        Story.append(Paragraph(description, normal_style))
        Story.append(Spacer(1, 0.2 * inch))

        # Translated Content (if available)
        if self.active_analysis_button == 'translation' and self.analysis_text_widget and self.lang_var.get() != "Select Language...":
            translated_title_text = self.analysis_text_widget.get("1.0", "1.end").strip()
            # Get content excluding the title and first two newlines, then split into lines
            translated_content_lines = self.analysis_text_widget.get("3.0", tk.END).strip().splitlines()

            # Sort translated content lines if they are not empty
            if translated_content_lines:
                sorted_translated_lines = sorted(translated_content_lines)
            else:
                sorted_translated_lines = []

            if sorted_translated_lines:  # Check if there's content after sorting
                Story.append(Paragraph("5. Translation", heading_style))
                Story.append(Paragraph(translated_title_text, normal_style))
                # Join sorted lines with <br/> for PDF rendering
                Story.append(Paragraph('<br/>'.join(sorted_translated_lines), normal_style))
                Story.append(Spacer(1, 0.2 * inch))

        try:
            doc.build(Story)
            self.show_temp_message(f"PDF saved as {pdf_filename}", 3000)
        except Exception as e:
            self.show_temp_message(f"Failed to create PDF: {e}", 3000)


if __name__ == "__main__":
    app = LitLoomApp()
    app.mainloop()
