"""
Font discovery and loading for international text support.

This module handles finding and loading appropriate fonts for different
languages and scripts, including Arabic, Hebrew, CJK, and Latin scripts.
"""

import platform
from pathlib import Path
from typing import Optional
from PIL import ImageFont


class FontManager:
    """
    Manages font discovery and loading for multi-language support.

    This class searches platform-specific font directories to find appropriate
    fonts for different languages and scripts. It supports:
    - Latin scripts (English, French, Spanish, etc.)
    - Arabic script (Arabic, Farsi, Urdu)
    - Hebrew script
    - CJK scripts (Chinese, Japanese, Korean)

    Examples:
        >>> font_mgr = FontManager()
        >>> # Find default font
        >>> default_font = font_mgr.find_font()

        >>> # Find Arabic font
        >>> arabic_font = font_mgr.find_font(language_code='ar')

        >>> # Load font with fallback
        >>> font = font_mgr.load_font_with_fallback(48, language_code='zh')
    """

    def __init__(self, default_font_path: Optional[str] = None):
        """
        Initialize the font manager.

        Args:
            default_font_path: Optional path to a default font file.
                             If not provided, searches system fonts.
        """
        self.default_font_path = default_font_path or self.find_font()

    def find_font(self, language_code: Optional[str] = None) -> Optional[str]:
        """
        Find a suitable font for text overlays with international script support.

        Searches platform-specific font directories, prioritizing fonts that support
        the requested language/script. Falls back to general Unicode fonts.

        Args:
            language_code: Optional ISO language code (e.g., 'ar', 'he', 'zh', 'ja', 'ko')
                         to prioritize language-specific fonts

        Returns:
            Path to font file if found, None to use PIL default font

        Examples:
            >>> font_mgr = FontManager()
            >>> font_mgr.find_font('ar')  # Arabic
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf'

            >>> font_mgr.find_font('zh')  # Chinese
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
        """
        system = platform.system()

        # Check if we need international script support
        needs_arabic = language_code and language_code.startswith(('ar', 'fa', 'ur'))
        needs_hebrew = language_code and language_code.startswith('he')
        needs_cjk = language_code and language_code.startswith(('zh', 'ja', 'ko'))

        font_candidates = []

        if system == "Darwin":  # macOS
            font_candidates = self._get_macos_fonts(needs_arabic, needs_hebrew, needs_cjk, language_code)
        elif system == "Windows":
            font_candidates = self._get_windows_fonts(needs_arabic, needs_hebrew, needs_cjk)
        else:  # Linux / Docker
            font_candidates = self._get_linux_fonts(needs_arabic, needs_hebrew, needs_cjk)

        # Find first font that exists
        for font in font_candidates:
            if Path(font).exists():
                return font

        return None  # Will use PIL default

    def _get_macos_fonts(self, needs_arabic: bool, needs_hebrew: bool,
                        needs_cjk: bool, language_code: Optional[str]) -> list[str]:
        """Get macOS font candidates based on language requirements."""
        fonts = []

        if needs_cjk:
            if language_code and language_code.startswith('ko'):
                # Korean-specific fonts
                fonts.extend([
                    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                ])
            else:
                # Chinese and Japanese
                fonts.extend([
                    "/System/Library/Fonts/Hiragino Sans GB.ttc",
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                ])

        if needs_arabic or needs_hebrew:
            fonts.extend([
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/Library/Fonts/Arial.ttf",
            ])

        # Default macOS fonts
        fonts.extend([
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
        ])

        return fonts

    def _get_windows_fonts(self, needs_arabic: bool, needs_hebrew: bool,
                          needs_cjk: bool) -> list[str]:
        """Get Windows font candidates based on language requirements."""
        fonts = []

        if needs_arabic:
            fonts.extend([
                "C:/Windows/Fonts/arialuni.ttf",
                "C:/Windows/Fonts/tahoma.ttf",
            ])

        if needs_hebrew:
            fonts.extend([
                "C:/Windows/Fonts/arialuni.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ])

        # Default Windows fonts
        fonts.extend([
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ])

        return fonts

    def _get_linux_fonts(self, needs_arabic: bool, needs_hebrew: bool,
                        needs_cjk: bool) -> list[str]:
        """Get Linux/Docker font candidates based on language requirements."""
        fonts = []

        # Noto fonts have excellent international support
        if needs_arabic:
            fonts.extend([
                "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
            ])

        if needs_hebrew:
            fonts.extend([
                "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
            ])

        if needs_cjk:
            fonts.extend([
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            ])

        # General fonts with good Unicode coverage
        fonts.extend([
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ])

        return fonts

    def load_font_with_fallback(
        self,
        font_size: int,
        language_code: Optional[str] = None
    ) -> ImageFont.FreeTypeFont:
        """
        Load a font with automatic fallback chain.

        Tries to load fonts in this order:
        1. Language-specific font (if language_code provided)
        2. Default font path
        3. Generic font search
        4. PIL default font (last resort)

        Args:
            font_size: Font size in pixels
            language_code: Optional language code for language-specific fonts

        Returns:
            Loaded PIL ImageFont object

        Examples:
            >>> font_mgr = FontManager()
            >>> font = font_mgr.load_font_with_fallback(48, 'ar')
            >>> # Font automatically selected for Arabic text
        """
        # Try language-specific font first
        if language_code:
            font_path = self.find_font(language_code)
            if font_path:
                try:
                    return ImageFont.truetype(font_path, font_size)
                except (OSError, IOError):
                    pass  # Try next option

        # Try default font path
        if self.default_font_path:
            try:
                return ImageFont.truetype(self.default_font_path, font_size)
            except (OSError, IOError):
                pass  # Try next option

        # Try generic font search
        font_path = self.find_font()
        if font_path:
            try:
                return ImageFont.truetype(font_path, font_size)
            except (OSError, IOError):
                pass  # Use default

        # Final fallback: PIL default font
        return ImageFont.load_default()
