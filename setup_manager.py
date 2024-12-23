#!/usr/bin/env python3

import os
import sys
import yaml
import json
import curses
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.style import Style
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.markdown import Markdown
from rich.align import Align
import questionary
from security_manager import SecurityManager
from theme_manager import ThemeManager
from animation_manager import AnimationManager

LOGO = """[bold blue]
████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
                                                                   
██████╗ ███████╗ ██████╗ ██████╗ ██████╗  █████╗ ████████╗ ██████╗ ██████╗ 
██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
██║  ██║█████╗  ██║     ██║   ██║██████╔╝███████║   ██║   ██║   ██║██████╔╝
██║  ██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗
██████╔╝███████╗╚██████╗╚██████╔╝██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝[/]
"""

WELCOME_MESSAGE = """
[cyan]Welcome to Terminal Decorator![/]

This setup wizard will guide you through configuring your terminal enhancement suite.
We'll help you customize:

[green]• Performance settings[/] - Optimize for your system
[green]• Appearance settings[/] - Choose themes and visual elements
[green]• Security settings[/] - Configure protection features
[green]• Feature settings[/] - Enable/disable components

[yellow]Use arrow keys to navigate and Enter to select.[/]
Press Ctrl+C at any time to exit.
"""

class SetupWizard:
    def __init__(self):
        self.console = Console()
        self.security_manager = SecurityManager()
        self.theme_manager = ThemeManager()
        self.animation_manager = AnimationManager()
        self.config: Dict[str, Any] = {}
        self.default_config = {
            'performance': {
                'fps': 60,
                'max_concurrent': 5,
                'hardware_acceleration': True,
                'smooth_transitions': True,
                'buffer_size': 1024,
                'vsync': True,
                'gpu_acceleration': False,
                'process_priority': 'normal'
            },
            'appearance': {
                'theme': 'default',
                'font_size': 14,
                'show_animations': True,
                'show_icons': True,
                'transparency': 0,
                'cursor_style': 'block',
                'color_scheme': 'dark',
                'font_family': 'default'
            },
            'security': {
                'sandbox_enabled': True,
                'auto_backup': True,
                'backup_interval': 3600,
                'restricted_mode': False,
                'command_validation': True,
                'secure_clipboard': True,
                'audit_logging': False
            },
            'features': {
                'git_integration': True,
                'task_monitoring': True,
                'system_stats': True,
                'network_monitoring': True,
                'auto_completion': True,
                'syntax_highlighting': True,
                'file_preview': True,
                'command_suggestions': True
            }
        }

    async def show_welcome(self):
        """Show welcome screen with ASCII art and animation"""
        self.console.clear()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="logo"),
            Layout(name="welcome"),
            Layout(name="footer")
        )
        
        # Add content
        layout["logo"].update(Panel(
            Align.center(Text(LOGO)),
            border_style="cyan",
            padding=(1, 2)
        ))
        
        layout["welcome"].update(Panel(
            Markdown(WELCOME_MESSAGE),
            title="Setup Wizard",
            border_style="green",
            padding=(1, 2)
        ))
        
        layout["footer"].update(Panel(
            "[cyan]Press Enter to continue...[/]",
            border_style="blue"
        ))
        
        # Show layout with animation
        with Live(layout, refresh_per_second=4) as live:
            await self.animation_manager.animate_text(live, layout["welcome"])
            input()

    def create_menu(self, title: str, options: List[Dict[str, Any]], style: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create an interactive menu with custom styling"""
        default_style = {
            'qmark': '#6C6C6C',
            'question': '#FF9D00 bold',
            'answer': '#00FF00 bold',
            'pointer': '#FF9D00 bold',
            'highlighted': '#FF9D00 bold',
            'selected': '#00FF00',
            'separator': '#6C6C6C',
            'instruction': '#808080',
            'text': '#FFFFFF',
        }
        
        menu_style = {**default_style, **(style or {})}

        choices = [
            {
                'name': f"{opt['name']} [dim]{opt.get('description', '')}[/]",
                'value': opt['value']
            }
            for opt in options
        ]

        result = questionary.select(
            title,
            choices=choices,
            style=questionary.Style(menu_style)
        ).ask()

        return next((opt for opt in options if opt['value'] == result), None)

    async def run_setup(self):
        """Run the interactive setup wizard with progress tracking"""
        try:
            await self.show_welcome()
            
            # Configuration sections with descriptions
            sections = [
                ('Performance', 'Optimize terminal performance', self._setup_performance),
                ('Appearance', 'Customize visual elements', self._setup_appearance),
                ('Security', 'Configure protection features', self._setup_security),
                ('Features', 'Enable/disable components', self._setup_features)
            ]

            # Create progress bar
            progress_bar = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=True
            )

            with progress_bar:
                main_task = progress_bar.add_task(
                    "[cyan]Setting up Terminal Decorator...",
                    total=len(sections)
                )
                
                for section_name, description, setup_func in sections:
                    # Show section header
                    self.console.rule(f"[yellow]{section_name}[/] - {description}")
                    
                    # Create subtask
                    subtask = progress_bar.add_task(
                        f"Configuring {section_name.lower()}...",
                        total=100
                    )
                    
                    # Run setup function
                    await setup_func(progress_bar, subtask)
                    
                    # Update main progress
                    progress_bar.advance(main_task)

            # Preview and save
            if await self._preview_and_confirm():
                await self._save_config_with_animation()
                self.console.print(Panel(
                    "[green]Setup completed successfully![/]\n\n"
                    "Your terminal is now enhanced with professional features.\n"
                    "Type [cyan]'terminal-decorator --help'[/] to see available commands.",
                    title="Setup Complete",
                    border_style="green"
                ))
            else:
                self.console.print(Panel(
                    "[yellow]Setup cancelled. No changes were made.[/]",
                    title="Setup Cancelled",
                    border_style="yellow"
                ))

        except KeyboardInterrupt:
            self.console.print(Panel(
                "[red]Setup cancelled by user.[/]",
                title="Setup Cancelled",
                border_style="red"
            ))
            sys.exit(1)
        except Exception as e:
            self.console.print(Panel(
                f"[red]Error during setup: {e}[/]\n\n"
                "Please report this issue on our GitHub repository.",
                title="Error",
                border_style="red"
            ))
            sys.exit(1)

    async def _setup_performance(self, progress: Progress, task_id: int):
        """Configure performance settings with real-time preview"""
        self.config['performance'] = {}
        
        # FPS Selection with preview
        fps_options = [
            {'name': '30 FPS', 'value': 30, 'description': 'Better battery life'},
            {'name': '60 FPS', 'value': 60, 'description': 'Smooth animations'},
            {'name': '120 FPS', 'value': 120, 'description': 'Ultra smooth (higher CPU usage)'}
        ]
        
        with Live(self._create_preview_panel("FPS Preview"), refresh_per_second=4) as live:
            fps = self.create_menu("Select refresh rate:", fps_options)
            self.config['performance']['fps'] = fps['value']
            progress.update(task_id, advance=25)
        
        # Hardware Settings
        hardware_panel = Panel(
            "Hardware acceleration uses your GPU for better performance\n"
            "Process priority affects system resource allocation",
            title="Hardware Settings",
            border_style="blue"
        )
        
        self.console.print(hardware_panel)
        
        self.config['performance']['hardware_acceleration'] = questionary.confirm(
            "Enable hardware acceleration?",
            default=True
        ).ask()
        progress.update(task_id, advance=25)
        
        priority_options = [
            {'name': 'Low', 'value': 'low', 'description': 'Minimal system impact'},
            {'name': 'Normal', 'value': 'normal', 'description': 'Balanced performance'},
            {'name': 'High', 'value': 'high', 'description': 'Maximum performance'}
        ]
        
        priority = self.create_menu("Select process priority:", priority_options)
        self.config['performance']['process_priority'] = priority['value']
        progress.update(task_id, advance=25)
        
        # Animation Settings
        self.config['performance']['smooth_transitions'] = questionary.confirm(
            "Enable smooth transitions?",
            default=True
        ).ask()
        progress.update(task_id, advance=25)

    async def _setup_appearance(self, progress: Progress, task_id: int):
        """Configure appearance settings with live preview"""
        self.config['appearance'] = {}
        
        # Theme Selection with live preview
        themes = self.theme_manager.list_themes()
        theme_options = [
            {'name': theme, 'value': theme, 'description': self.theme_manager.get_theme_description(theme)}
            for theme in themes
        ]
        
        with Live(self._create_theme_preview(), refresh_per_second=4) as live:
            theme = self.create_menu("Select theme:", theme_options)
            self.config['appearance']['theme'] = theme['value']
            progress.update(task_id, advance=20)
        
        # Font Settings
        font_panel = Panel(
            "Choose font settings that match your terminal capabilities",
            title="Font Settings",
            border_style="blue"
        )
        self.console.print(font_panel)
        
        font_options = [
            {'name': 'Small (12)', 'value': 12, 'description': 'Compact view'},
            {'name': 'Medium (14)', 'value': 14, 'description': 'Balanced readability'},
            {'name': 'Large (16)', 'value': 16, 'description': 'Enhanced visibility'}
        ]
        font = self.create_menu("Select font size:", font_options)
        self.config['appearance']['font_size'] = font['value']
        progress.update(task_id, advance=20)
        
        # Visual Effects
        effects_panel = Panel(
            "Configure visual effects and animations",
            title="Visual Effects",
            border_style="blue"
        )
        self.console.print(effects_panel)
        
        self.config['appearance']['show_animations'] = questionary.confirm(
            "Enable animations?",
            default=True
        ).ask()
        progress.update(task_id, advance=20)
        
        self.config['appearance']['show_icons'] = questionary.confirm(
            "Show icons?",
            default=True
        ).ask()
        progress.update(task_id, advance=20)
        
        # Transparency
        transparency_options = [
            {'name': 'None', 'value': 0, 'description': 'Solid background'},
            {'name': 'Light', 'value': 10, 'description': 'Slight transparency'},
            {'name': 'Medium', 'value': 20, 'description': 'Balanced transparency'},
            {'name': 'High', 'value': 30, 'description': 'Maximum transparency'}
        ]
        transparency = self.create_menu("Select transparency level:", transparency_options)
        self.config['appearance']['transparency'] = transparency['value']
        progress.update(task_id, advance=20)

    def _create_preview_panel(self, title: str) -> Panel:
        """Create a preview panel for settings"""
        return Panel(
            Align.center(
                Text("Preview will update in real-time", style="cyan")
            ),
            title=title,
            border_style="blue",
            padding=(1, 2)
        )

    def _create_theme_preview(self) -> Panel:
        """Create a theme preview panel"""
        preview_text = (
            "[title]Sample Title[/]\n\n"
            "[text]This is how your terminal text will look[/]\n"
            "[command]$ sample command[/]\n"
            "[output]Command output example[/]\n"
            "[error]Error message example[/]"
        )
        
        return Panel(
            preview_text,
            title="Theme Preview",
            border_style="blue",
            padding=(1, 2)
        )

    async def _save_config_with_animation(self):
        """Save configuration with animation"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True
        ) as progress:
            save_task = progress.add_task("[cyan]Saving configuration...", total=100)
            
            # Create config directory
            config_dir = Path.home() / '.terminal_decorator'
            config_dir.mkdir(parents=True, exist_ok=True)
            progress.update(save_task, advance=30)
            
            # Backup existing config
            config_file = config_dir / 'config.yaml'
            if config_file.exists():
                self.security_manager.backup_manager.create_backup(config_file)
            progress.update(save_task, advance=30)
            
            # Save new config
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            progress.update(save_task, advance=40)

    async def _setup_security(self, progress: Progress, task_id: int):
        """Configure security settings with real-time preview"""
        self.config['security'] = {}
        
        # Sandbox Mode
        self.config['security']['sandbox_enabled'] = questionary.confirm(
            "Enable sandboxed command execution? (Recommended for security)",
            default=True
        ).ask()
        progress.update(task_id, advance=25)
        
        # Backup Settings
        self.config['security']['auto_backup'] = questionary.confirm(
            "Enable automatic backup of configuration files?",
            default=True
        ).ask()
        progress.update(task_id, advance=25)
        
        if self.config['security']['auto_backup']:
            backup_options = [
                {'name': 'Every hour', 'value': 3600, 'description': 'Every hour'},
                {'name': 'Every 6 hours', 'value': 21600, 'description': 'Every 6 hours'},
                {'name': 'Every 24 hours', 'value': 86400, 'description': 'Every 24 hours'}
            ]
            backup = self.create_menu("Select backup interval:", backup_options)
            self.config['security']['backup_interval'] = backup['value']
            progress.update(task_id, advance=25)
        
        # Restricted Mode
        self.config['security']['restricted_mode'] = questionary.confirm(
            "Enable restricted mode? (Limits command execution to safe commands only)",
            default=False
        ).ask()
        progress.update(task_id, advance=25)

    async def _setup_features(self, progress: Progress, task_id: int):
        """Configure feature settings with real-time preview"""
        self.config['features'] = {}
        
        feature_options = [
            {
                'name': 'Git Integration',
                'description': 'Show git status and branch information',
                'value': 'git_integration'
            },
            {
                'name': 'Task Monitoring',
                'description': 'Monitor system tasks and services',
                'value': 'task_monitoring'
            },
            {
                'name': 'System Statistics',
                'description': 'Show CPU, memory, and disk usage',
                'value': 'system_stats'
            },
            {
                'name': 'Network Monitoring',
                'description': 'Show network usage and connections',
                'value': 'network_monitoring'
            },
            {
                'name': 'Auto Completion',
                'description': 'Automatically complete commands',
                'value': 'auto_completion'
            },
            {
                'name': 'Syntax Highlighting',
                'description': 'Highlight syntax in code',
                'value': 'syntax_highlighting'
            },
            {
                'name': 'File Preview',
                'description': 'Preview files in the terminal',
                'value': 'file_preview'
            },
            {
                'name': 'Command Suggestions',
                'description': 'Suggest commands based on input',
                'value': 'command_suggestions'
            }
        ]
        
        self.console.print("\n[yellow]Select features to enable:[/]")
        for option in feature_options:
            enabled = questionary.confirm(
                f"Enable {option['name']}? ({option['description']})",
                default=True
            ).ask()
            self.config['features'][option['value']] = enabled
            progress.update(task_id, advance=10)

    async def _preview_and_confirm(self) -> bool:
        """Show configuration preview and get confirmation"""
        self.console.clear()
        self.console.rule("[yellow]Configuration Preview")
        
        # Create a pretty preview
        preview = yaml.dump(self.config, default_flow_style=False)
        self.console.print(Panel(
            Syntax(preview, "yaml", theme="monokai"),
            title="Configuration Preview",
            border_style="cyan"
        ))
        
        # Show what will change
        changes = self._get_config_changes()
        if changes:
            self.console.print("\n[yellow]The following changes will be made:[/]")
            for change in changes:
                self.console.print(f"• {change}")
        
        return questionary.confirm(
            "\nApply these settings?",
            default=True
        ).ask()

    def _get_config_changes(self) -> List[str]:
        """Get list of changes from default configuration"""
        changes = []
        
        def compare_dict(new: Dict, default: Dict, path: str = "") -> None:
            for key, value in new.items():
                full_path = f"{path}.{key}" if path else key
                if key not in default:
                    changes.append(f"[green]Added[/] {full_path}")
                elif isinstance(value, dict):
                    compare_dict(value, default[key], full_path)
                elif value != default[key]:
                    changes.append(
                        f"[yellow]Changed[/] {full_path}: "
                        f"[red]{default[key]}[/] → [green]{value}[/]"
                    )

        compare_dict(self.config, self.default_config)
        return changes

class SettingsMenu:
    def __init__(self):
        self.console = Console()
        self.config_file = Path.home() / '.terminal_decorator' / 'config.yaml'
        self.security_manager = SecurityManager()
        self.theme_manager = ThemeManager()
        self.animation_manager = AnimationManager()

    async def show_menu(self):
        """Show the main settings menu with animations"""
        while True:
            self.console.clear()
            
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="logo", size=12),
                Layout(name="menu", size=10),
                Layout(name="footer", size=3)
            )
            
            # Add content
            layout["logo"].update(Panel(
                Align.center(Text(LOGO)),
                border_style="cyan",
                padding=(1, 2)
            ))
            
            options = [
                {
                    'name': 'Performance Settings',
                    'value': 'performance',
                    'description': 'Optimize terminal performance'
                },
                {
                    'name': 'Appearance Settings',
                    'value': 'appearance',
                    'description': 'Customize visual elements'
                },
                {
                    'name': 'Security Settings',
                    'value': 'security',
                    'description': 'Configure protection features'
                },
                {
                    'name': 'Feature Settings',
                    'value': 'features',
                    'description': 'Enable/disable components'
                },
                {
                    'name': 'Backup Management',
                    'value': 'backup',
                    'description': 'Manage configuration backups'
                },
                {
                    'name': 'Exit',
                    'value': 'exit',
                    'description': 'Return to terminal'
                }
            ]
            
            # Create menu table
            table = Table(
                title="Terminal Decorator Settings",
                show_header=True,
                header_style="bold cyan",
                border_style="blue"
            )
            table.add_column("Option")
            table.add_column("Description")
            
            for opt in options:
                table.add_row(
                    f"[cyan]{opt['name']}[/]",
                    f"[dim]{opt['description']}[/]"
                )
            
            layout["menu"].update(Panel(
                table,
                border_style="blue",
                padding=(1, 2)
            ))
            
            layout["footer"].update(Panel(
                "[yellow]Use arrow keys to navigate and Enter to select[/]",
                border_style="blue"
            ))
            
            # Show layout with animation
            with Live(layout, refresh_per_second=4) as live:
                await self.animation_manager.animate_text(live, layout["menu"])
            
            choice = questionary.select(
                "Select an option:",
                    choices=[opt['name'] for opt in options],
                    style=questionary.Style({
                        'question': '#FF9D00 bold',
                        'answer': '#00FF00 bold',
                        'pointer': '#FF9D00 bold',
                        'highlighted': '#FF9D00 bold',
                        'selected': '#00FF00'
                    })
            ).ask()
            
            if choice == 'Exit':
                self.console.clear()
                self.console.print(Panel(
                    "[green]Thank you for using Terminal Decorator![/]",
                    border_style="green"
                ))
                break
            
            section = next(opt['value'] for opt in options if opt['name'] == choice)
            await self._handle_section(section)

    async def _handle_section(self, section: str):
        """Handle selected menu section with animations"""
        if section == 'backup':
            await self._show_backup_menu()
        else:
            wizard = SetupWizard()
            setup_func = getattr(wizard, f'_setup_{section}')
            
            # Show section header
            self.console.rule(f"[yellow]{section.title()} Settings[/]")
            
            # Create progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=True
            ) as progress:
                task = progress.add_task(f"Configuring {section}...", total=100)
                await setup_func(progress, task)
            
            if await wizard._preview_and_confirm():
                await wizard._save_config_with_animation()
                self.console.print(Panel(
                    f"[green]{section.title()} settings updated successfully![/]",
                    border_style="green"
                ))
            
            self.console.print("\n[cyan]Press Enter to return to the main menu...[/]")
            input()

    async def _show_backup_menu(self):
        """Show backup management menu with animations"""
        while True:
            self.console.clear()
            
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="backups", size=15),
                Layout(name="options", size=6)
            )
            
            # Add header
            layout["header"].update(Panel(
                "[cyan bold]Backup Management[/]",
                border_style="blue"
            ))
            
            # Get backups
            backups = self.security_manager.backup_manager.list_backups()
            
            # Create backup table
            table = Table(
                title="Available Backups",
                show_header=True,
                header_style="bold cyan",
                border_style="blue"
            )
            table.add_column("Timestamp", style="cyan")
            table.add_column("File", style="green")
            table.add_column("Size", justify="right", style="yellow")
            
            for backup in backups:
                table.add_row(
                    backup['timestamp'],
                    backup['original_path'],
                    f"{backup['size'] / 1024:.1f} KB"
                )
            
            layout["backups"].update(Panel(table, border_style="blue"))
            
            # Create options
            options = [
                'Create Backup',
                'Restore Backup',
                'Delete Backup',
                'Back to Main Menu'
            ]
            
            options_text = "\n".join(
                f"[cyan]• {option}[/]"
                for option in options
            )
            
            layout["options"].update(Panel(
                options_text,
                title="Options",
                border_style="blue"
            ))
            
            # Show layout with animation
            with Live(layout, refresh_per_second=4) as live:
                await self.animation_manager.animate_text(live, layout["backups"])
            
            choice = questionary.select(
                "Select an option:",
                    choices=options,
                    style=questionary.Style({
                        'question': '#FF9D00 bold',
                        'answer': '#00FF00 bold',
                        'pointer': '#FF9D00 bold',
                        'highlighted': '#FF9D00 bold',
                        'selected': '#00FF00'
                    })
            ).ask()
            
            if choice == 'Back to Main Menu':
                break
            elif choice == 'Create Backup':
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                ) as progress:
                    task = progress.add_task("Creating backup...", total=100)
                self.security_manager.backup_manager.create_backup(self.config_file)
                progress.update(task, completed=100)
                
                self.console.print(Panel(
                    "[green]Backup created successfully![/]",
                    border_style="green"
                ))
            elif choice == 'Restore Backup':
                if backups:
                    backup_choices = [
                        f"{b['timestamp']} - {b['original_path']}"
                        for b in backups
                    ]
                    selected = questionary.select(
                        "Select backup to restore:",
                        choices=backup_choices,
                        style=questionary.Style({
                            'question': '#FF9D00 bold',
                            'answer': '#00FF00 bold',
                            'pointer': '#FF9D00 bold',
                            'highlighted': '#FF9D00 bold',
                            'selected': '#00FF00'
                        })
                    ).ask()
                    
                    if selected:
                        idx = backup_choices.index(selected)
                        backup_path = Path(backups[idx]['backup_path'])
                        
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            BarColumn(),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                        ) as progress:
                            task = progress.add_task("Restoring backup...", total=100)
                            success = self.security_manager.backup_manager.restore_backup(
                            self.config_file, backup_path
                            )
                            progress.update(task, completed=100)
                        
                        if success:
                            self.console.print(Panel(
                                "[green]Backup restored successfully![/]",
                                border_style="green"
                            ))
                        else:
                            self.console.print(Panel(
                                "[red]Failed to restore backup.[/]",
                                border_style="red"
                            ))
                else:
                    self.console.print(Panel(
                        "[yellow]No backups available.[/]",
                        border_style="yellow"
                    ))
            elif choice == 'Delete Backup':
                if backups:
                    backup_choices = [
                        f"{b['timestamp']} - {b['original_path']}"
                        for b in backups
                    ]
                    selected = questionary.select(
                        "Select backup to delete:",
                        choices=backup_choices,
                        style=questionary.Style({
                            'question': '#FF9D00 bold',
                            'answer': '#00FF00 bold',
                            'pointer': '#FF9D00 bold',
                            'highlighted': '#FF9D00 bold',
                            'selected': '#00FF00'
                        })
                    ).ask()
                    
                    if selected:
                        idx = backup_choices.index(selected)
                        backup_path = Path(backups[idx]['backup_path'])
                        
                        if questionary.confirm(
                            "Are you sure you want to delete this backup?",
                            default=False
                        ).ask():
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                BarColumn(),
                                TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
                            ) as progress:
                                task = progress.add_task("Deleting backup...", total=100)
                                success = self.security_manager.backup_manager.delete_backup(backup_path)
                                progress.update(task, completed=100)
                            
                            if success:
                                self.console.print(Panel(
                                    "[green]Backup deleted successfully![/]",
                                    border_style="green"
                                ))
                            else:
                                self.console.print(Panel(
                                    "[red]Failed to delete backup.[/]",
                                    border_style="red"
                                ))
                else:
                    self.console.print(Panel(
                        "[yellow]No backups available.[/]",
                        border_style="yellow"
                    ))
            
            self.console.print("\n[cyan]Press Enter to continue...[/]")
            input()

async def main():
    """Main entry point with error handling"""
    try:
        if not (Path.home() / '.terminal_decorator' / 'config.yaml').exists():
            # First-time setup
            wizard = SetupWizard()
            await wizard.run_setup()
        else:
            # Settings menu
            menu = SettingsMenu()
            await menu.show_menu()
    except KeyboardInterrupt:
        print("\n\nExiting Terminal Decorator...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        print("Please report this issue on our GitHub repository.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1) 