#!/usr/bin/env python3

import colorsys
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from rich.color import Color
from rich.style import Style
from rich.theme import Theme
import yaml
from blessed import Terminal

@dataclass
class ColorRGB:
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex_color: str) -> 'ColorRGB':
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return cls(
            r=int(hex_color[0:2], 16),
            g=int(hex_color[2:4], 16),
            b=int(hex_color[4:6], 16)
        )

    def to_hex(self) -> str:
        """Convert RGB to hex color"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_ansi(self) -> str:
        """Convert RGB to ANSI color code"""
        return f"\033[38;2;{self.r};{self.g};{self.b}m"

    def blend(self, other: 'ColorRGB', factor: float) -> 'ColorRGB':
        """Blend with another color using given factor (0-1)"""
        return ColorRGB(
            r=int(self.r + (other.r - self.r) * factor),
            g=int(self.g + (other.g - self.g) * factor),
            b=int(self.b + (other.b - self.b) * factor)
        )

class ThemeDefinition:
    """Professional theme definition with color palette"""
    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = {k: ColorRGB.from_hex(v) if v.startswith('#') else v 
                      for k, v in colors.items()}
        self.styles = {}
        self._setup_styles()

    def _setup_styles(self):
        """Setup Rich styles for the theme"""
        for name, color in self.colors.items():
            if isinstance(color, ColorRGB):
                self.styles[name] = Style(color=color.to_hex())
            else:
                self.styles[name] = Style(color=color)

    def get_color(self, name: str) -> Optional[ColorRGB]:
        """Get color by name"""
        return self.colors.get(name)

    def get_style(self, name: str) -> Optional[Style]:
        """Get Rich style by name"""
        return self.styles.get(name)

class ThemeManager:
    """Professional theme management with dynamic transitions"""
    
    # Built-in themes
    BUILTIN_THEMES = {
        'default': {
            'primary': '#4B9CD3',
            'secondary': '#13294B',
            'success': '#2ECC71',
            'error': '#E74C3C',
            'warning': '#F1C40F',
            'info': '#3498DB',
            'text': '#2C3E50',
            'muted': '#95A5A6',
            'background': '#FFFFFF',
            'border': '#BDC3C7',
            'accent': '#9B59B6'
        },
        'dark': {
            'primary': '#61AFEF',
            'secondary': '#C678DD',
            'success': '#98C379',
            'error': '#E06C75',
            'warning': '#E5C07B',
            'info': '#56B6C2',
            'text': '#ABB2BF',
            'muted': '#5C6370',
            'background': '#282C34',
            'border': '#3E4451',
            'accent': '#C678DD'
        },
        'neon': {
            'primary': '#00FF9C',
            'secondary': '#00B8FF',
            'success': '#00FF9C',
            'error': '#FF3333',
            'warning': '#FFB000',
            'info': '#00B8FF',
            'text': '#FFFFFF',
            'muted': '#4D4D4D',
            'background': '#1A1A1A',
            'border': '#333333',
            'accent': '#FF00FF'
        },
        'minimal': {
            'primary': '#000000',
            'secondary': '#404040',
            'success': '#008000',
            'error': '#FF0000',
            'warning': '#808000',
            'info': '#000080',
            'text': '#000000',
            'muted': '#808080',
            'background': '#FFFFFF',
            'border': '#C0C0C0',
            'accent': '#404040'
        },
        'ocean': {
            'primary': '#006994',
            'secondary': '#2E8B57',
            'success': '#20B2AA',
            'error': '#CD5C5C',
            'warning': '#DAA520',
            'info': '#4682B4',
            'text': '#2F4F4F',
            'muted': '#778899',
            'background': '#F0F8FF',
            'border': '#B0C4DE',
            'accent': '#483D8B'
        }
    }

    def __init__(self):
        self.term = Terminal()
        self.current_theme = None
        self.themes: Dict[str, ThemeDefinition] = {}
        self._load_builtin_themes()

    def _load_builtin_themes(self):
        """Load built-in themes"""
        for name, colors in self.BUILTIN_THEMES.items():
            self.themes[name] = ThemeDefinition(name, colors)

    def load_custom_theme(self, name: str, colors: Dict[str, str]):
        """Load a custom theme"""
        self.themes[name] = ThemeDefinition(name, colors)

    def load_theme_file(self, filepath: str):
        """Load themes from YAML file"""
        with open(filepath, 'r') as f:
            theme_data = yaml.safe_load(f)
            for name, colors in theme_data.items():
                self.load_custom_theme(name, colors)

    def get_theme(self, name: str) -> Optional[ThemeDefinition]:
        """Get theme by name"""
        return self.themes.get(name)

    def set_theme(self, name: str, transition: bool = True, duration: float = 0.5):
        """Set current theme with optional transition"""
        if name not in self.themes:
            raise ValueError(f"Theme '{name}' not found")

        new_theme = self.themes[name]
        if transition and self.current_theme:
            self._transition_to_theme(new_theme, duration)
        else:
            self.current_theme = new_theme

    def _transition_to_theme(self, new_theme: ThemeDefinition, duration: float):
        """Smooth transition between themes"""
        old_theme = self.current_theme
        steps = int(duration * 60)  # 60 FPS
        
        for i in range(steps + 1):
            factor = i / steps
            transition_colors = {}
            
            for name, new_color in new_theme.colors.items():
                if isinstance(new_color, ColorRGB):
                    old_color = old_theme.colors.get(name)
                    if isinstance(old_color, ColorRGB):
                        transition_colors[name] = old_color.blend(new_color, factor)
            
            # Apply transition colors
            self._apply_transition_colors(transition_colors)
            time.sleep(duration / steps)
        
        self.current_theme = new_theme

    def _apply_transition_colors(self, colors: Dict[str, ColorRGB]):
        """Apply transition colors to terminal"""
        for name, color in colors.items():
            if hasattr(self.term, name):
                setattr(self.term, name, color.to_ansi())

    def get_rich_theme(self) -> Theme:
        """Get current theme as Rich Theme object"""
        if not self.current_theme:
            self.set_theme('default', transition=False)
        
        return Theme({
            name: Style(color=color.to_hex() if isinstance(color, ColorRGB) else color)
            for name, color in self.current_theme.colors.items()
        })

    def list_themes(self) -> List[str]:
        """List available themes"""
        return list(self.themes.keys())

    def preview_theme(self, name: str):
        """Preview a theme"""
        theme = self.get_theme(name)
        if not theme:
            return
        
        print(f"\nTheme Preview: {name}")
        print("=" * 40)
        
        for color_name, color in theme.colors.items():
            if isinstance(color, ColorRGB):
                print(f"{color.to_ansi()}{color_name}: {color.to_hex()}\\033[0m")
            else:
                print(f"{color_name}: {color}")
        
        print("=" * 40)

if __name__ == "__main__":
    # Example usage
    manager = ThemeManager()
    
    # Preview all built-in themes
    for theme_name in manager.list_themes():
        manager.preview_theme(theme_name)
        print() 