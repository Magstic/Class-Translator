# Try to import the requests library. If it fails, this plugin will be unavailable.
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

import json
import re
import time
from html import unescape
from .base_translator import BaseTranslator


class LightGoogleTranslator(BaseTranslator):
    """
    Translator plugin using a direct Google Translate API endpoint.
    This is a lightweight, unofficial implementation.
    """

    # This API key was extracted from the user-provided file.
    API_KEY = ""
    API_URL = "https://translate-pa.googleapis.com/v1/translateHtml"

    @property
    def name(self):
        return "Google Translate (Light)"

    def __init__(self):
        self.split_chars = [";", "|"]
        self.prefix_chars = ["-"]

    def is_available(self):
        """Check if the requests library is installed."""
        return REQUESTS_AVAILABLE

    def get_configurable_rules(self):
        """Returns the rules that the user can configure for this translator."""
        return {
            "split_chars": {
                "label": "句子分割符 (用英文逗號隔開)",
                "type": "string",
                "value": ",".join(self.split_chars),
            },
            "prefix_chars": {
                "label": "保留前綴符 (用英文逗號隔開)",
                "type": "string",
                "value": ",".join(self.prefix_chars),
            },
        }

    def update_rules(self, new_rules):
        """Updates the rules from the settings dialog."""
        if "split_chars" in new_rules:
            self.split_chars = new_rules["split_chars"].split(",")
        if "prefix_chars" in new_rules:
            self.prefix_chars = new_rules["prefix_chars"].split(",")

    def translate(self, text, src_lang="auto", dest_lang="zh-cn"):
        """Translate the given text using the direct Google Translate API."""
        if not self.is_available():
            return "The 'requests' library is not installed. Please run: pip install requests"

        if not text:
            return ""

        retries = 3
        delay = 1  # seconds

        for attempt in range(retries):
            try:
                split_pattern = f"([{''.join(re.escape(c) for c in self.split_chars)}])"
                parts = re.split(split_pattern, text)
                translated_parts = []

                headers = {
                    "Accept": "*/*",
                    "Content-Type": "application/json+protobuf",
                    "X-Goog-Api-Key": self.API_KEY,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                }

                for part in parts:
                    if not part or part in self.split_chars:
                        translated_parts.append(part)
                        continue

                    stripped_part = part.strip()
                    if stripped_part:
                        prefix = ""
                        for char in self.prefix_chars:
                            if stripped_part.startswith(char):
                                prefix = char + " "
                                stripped_part = stripped_part[len(char) :].lstrip()
                                break

                        if not stripped_part:
                            translated_parts.append(prefix)
                            continue

                        data = json.dumps(
                            [[[stripped_part], src_lang, dest_lang], "wt_lib"]
                        )
                        response = requests.post(
                            self.API_URL, headers=headers, data=data, timeout=10
                        )
                        response.raise_for_status()
                        translated_text = unescape(response.json()[0][0])
                        translated_parts.append(prefix + translated_text)
                    else:
                        translated_parts.append(part)

                return "".join(translated_parts)

            except requests.exceptions.RequestException as e:
                print(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    return "[翻译失败: 网络错误]"
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return f"[翻译失败，請檢查 API_KEY: {e}]"
