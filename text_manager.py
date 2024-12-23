#!/usr/bin/env python3

import os
import random
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from art import text2art, art_list
import pyfiglet
from rich.text import Text
from rich.style import Style
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from prompt_toolkit.styles import Style as PromptStyle
import emoji

@dataclass
class FontStyle:
    """Professional font style configuration"""
    name: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    dim: bool = False
    blink: bool = False
    reverse: bool = False

    def to_ansi(self) -> str:
        """Convert to ANSI escape sequence"""
        styles = []
        if self.bold: styles.append('1')
        if self.dim: styles.append('2')
        if self.italic: styles.append('3')
        if self.underline: styles.append('4')
        if self.blink: styles.append('5')
        if self.reverse: styles.append('7')
        if self.strike: styles.append('9')
        return f"\033[{';'.join(styles)}m" if styles else ""

    def to_rich_style(self) -> Style:
        """Convert to Rich style"""
        return Style(
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            strike=self.strike,
            dim=self.dim,
            blink=self.blink,
            reverse=self.reverse
        )

class TextManager:
    """Professional text and banner management"""
    
    # Professional banner templates
    BANNER_TEMPLATES = {
        'welcome': [
            "Welcome to {name}'s Terminal",
            "Terminal Session - {name}",
            "{name}'s Development Environment",
            "Welcome Back, {name}!",
            "Terminal Pro - {name}'s Workspace"
        ],
        'motivational': [
            "Code with Purpose",
            "Build Something Amazing",
            "Create • Develop • Deploy",
            "Think • Code • Innovate",
            "Debug like a Detective",
            "Code with Excellence"
        ],
        'status': [
            "System Status: Optimal",
            "All Systems Operational",
            "Environment Ready",
            "Development Mode Active",
            "Terminal Pro Ready"
        ]
    }

    # Professional font collections
    FONT_COLLECTIONS = {
        'modern': ['slant', 'banner3-D', 'larry3d', 'colossal'],
        'clean': ['standard', 'thin', 'small', 'mini'],
        'decorative': ['block', 'cosmic', 'roman', 'broadway'],
        'tech': ['cyberlarge', 'cybermedium', 'digital']
    }

    def __init__(self):
        self.console = Console()
        self.available_fonts = pyfiglet.FigletFont.getFonts()
        self.available_arts = art_list()
        self._load_custom_fonts()

    def _load_custom_fonts(self):
        """Load custom font configurations"""
        self.font_styles = {
            'header': FontStyle('modern', bold=True),
            'subheader': FontStyle('clean', italic=True),
            'emphasis': FontStyle('standard', bold=True, underline=True),
            'code': FontStyle('monospace', dim=True),
            'alert': FontStyle('standard', bold=True, blink=True),
            'success': FontStyle('standard', bold=True),
            'error': FontStyle('standard', bold=True, reverse=True)
        }

    def create_banner(self, text: str, style: str = 'modern', font: Optional[str] = None,
                     color: Optional[str] = None, width: Optional[int] = None) -> Panel:
        """Create a professional banner with advanced styling"""
        if font is None:
            font = random.choice(self.FONT_COLLECTIONS[style])

        # Create ASCII art text
        if font in self.available_fonts:
            art_text = pyfiglet.figlet_format(text, font=font)
        else:
            art_text = text2art(text, font=font)

        # Apply color and styling
        styled_text = Text(art_text)
        if color:
            styled_text.stylize(color)

        # Create panel with proper alignment
        return Panel(
            Align.center(styled_text),
            border_style=color or "bright_blue",
            padding=(1, 2),
            width=width
        )

    def create_motivational_banner(self) -> Panel:
        """Create a random motivational banner"""
        quote = random.choice(self.BANNER_TEMPLATES['motivational'])
        return self.create_banner(
            quote,
            style='decorative',
            color="bright_magenta"
        )

    def create_welcome_banner(self, name: str) -> Panel:
        """Create a personalized welcome banner"""
        template = random.choice(self.BANNER_TEMPLATES['welcome'])
        text = template.format(name=name)
        return self.create_banner(
            text,
            style='modern',
            color="bright_cyan"
        )

    def create_status_banner(self) -> Panel:
        """Create a system status banner"""
        status = random.choice(self.BANNER_TEMPLATES['status'])
        return self.create_banner(
            status,
            style='tech',
            color="bright_green"
        )

    def style_prompt_text(self, text: str, style: Union[str, FontStyle]) -> str:
        """Apply professional styling to prompt text"""
        if isinstance(style, str):
            style = self.font_styles.get(style, FontStyle('standard'))
        return f"{style.to_ansi()}{text}\033[0m"

    def create_dynamic_prompt(self, components: List[Dict[str, str]]) -> str:
        """Create a professional dynamic prompt"""
        prompt_parts = []
        
        for comp in components:
            text = comp.get('text', '')
            style = comp.get('style', 'standard')
            icon = comp.get('icon', '')
            
            if icon:
                text = f"{emoji.emojize(icon, use_aliases=True)} {text}"
            
            prompt_parts.append(self.style_prompt_text(text, style))
        
        return " ".join(prompt_parts)

    def preview_fonts(self, text: str = "Sample Text"):
        """Preview available font styles"""
        table = self.console.table(
            title="Available Font Styles",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Style Name")
        table.add_column("Preview")

        for collection, fonts in self.FONT_COLLECTIONS.items():
            for font in fonts:
                if font in self.available_fonts:
                    preview = pyfiglet.figlet_format(text, font=font, width=40)
                    table.add_row(font, preview)

        self.console.print(table)

    def preview_font_styles(self, text: str = "Sample Text"):
        """Preview font styling options"""
        table = self.console.table(
            title="Font Style Previews",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Style Name")
        table.add_column("Preview")

        for name, style in self.font_styles.items():
            preview = self.style_prompt_text(text, style)
            table.add_row(name, preview)

        self.console.print(table)

if __name__ == "__main__":
    # Example usage
    manager = TextManager()
    
    # Show welcome banner
    print("\nWelcome Banner:")
    console.print(manager.create_welcome_banner("Developer"))
    
    # Show motivational banner
    print("\nMotivational Banner:")
    console.print(manager.create_motivational_banner())
    
    # Show status banner
    print("\nStatus Banner:")
    console.print(manager.create_status_banner())
    
    # Show dynamic prompt example
    print("\nDynamic Prompt Example:")
    prompt = manager.create_dynamic_prompt([
        {'text': 'user', 'style': 'emphasis', 'icon': ':user:'},
        {'text': 'in', 'style': 'standard'},
        {'text': '~/projects', 'style': 'code', 'icon': ':file_folder:'},
        {'text': 'git(main)', 'style': 'success', 'icon': ':branch:'}
    ])
    print(prompt)
    
    # Preview fonts
    print("\nFont Preview:")
    manager.preview_fonts("Hello")
    
    # Preview styles
    print("\nStyle Preview:")
    manager.preview_font_styles() 