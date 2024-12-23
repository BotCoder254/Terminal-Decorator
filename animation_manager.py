#!/usr/bin/env python3

import yaml
import time
import math
import threading
import queue
import curses
import sys
from typing import Dict, List, Any, Callable, Optional
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.progress import Progress, SpinnerColumn
from rich.live import Live
from dataclasses import dataclass
import numpy as np

@dataclass
class AnimationState:
    running: bool = True
    current_frame: int = 0
    start_time: float = time.time()
    duration: float = 0.0
    frame_count: int = 0
    callback: Optional[Callable] = None

class AnimationManager:
    def __init__(self, config_path: str = "animation_config.yaml"):
        self.console = Console()
        self.animations: Dict[str, AnimationState] = {}
        self.animation_queue = queue.Queue()
        self.load_config(config_path)
        self.running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()

    def load_config(self, config_path: str) -> None:
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.global_settings = self.config['global']
        self.fps = self.global_settings['fps']
        self.frame_time = 1.0 / self.fps

    def _get_easing_function(self, name: str) -> Callable[[float], float]:
        easing_funcs = self.config['easing']['functions']
        if name not in easing_funcs:
            return lambda x: x  # Linear easing as fallback
        
        # Convert string representation to lambda function
        return eval(f"lambda x: {easing_funcs[name]}")

    def create_spinner(self, style: str = "dots", text: str = "", **kwargs) -> None:
        spinner_config = self.config['spinners']
        frames = spinner_config['styles'].get(style, spinner_config['styles']['dots'])
        
        def spinner_animation():
            idx = 0
            while self.running:
                frame = frames[idx % len(frames)]
                if spinner_config['settings']['color_cycle']:
                    color = spinner_config['settings']['colors'][idx % len(spinner_config['settings']['colors'])]
                    self.console.print(f"[{color}]{frame}[/] {text}", end='\r')
                else:
                    self.console.print(f"{frame} {text}", end='\r')
                idx += 1
                time.sleep(spinner_config['settings']['speed'])

        return threading.Thread(target=spinner_animation, daemon=True)

    def create_progress_bar(self, style: str = "default", total: int = 100) -> Progress:
        progress_config = self.config['progress_bars']['styles'][style]
        
        progress = Progress(
            SpinnerColumn(),
            *([
                "{task.description}",
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                "{task.completed}/{task.total}",
                "•",
                "ETA: {task.time_remaining}",
            ] if self.config['progress_bars']['settings']['show_time_remaining'] else []),
            style=progress_config['complete_style'],
            refresh_per_second=self.fps
        )
        
        return progress

    def create_text_effect(self, effect: str, text: str, **kwargs) -> None:
        effect_config = self.config['text_effects'][effect]
        
        if effect == "typing":
            def typing_animation():
                for i in range(len(text) + 1):
                    if not self.running:
                        break
                    display_text = text[:i]
                    if effect_config['cursor_blink']:
                        display_text += effect_config['cursor']
                    self.console.print(display_text, end='\r')
                    time.sleep(effect_config['speed'])
            
            return threading.Thread(target=typing_animation, daemon=True)
        
        elif effect == "marquee":
            def marquee_animation():
                width = effect_config['width']
                padded_text = " " * effect_config['padding'] + text + " " * effect_config['padding']
                position = 0
                direction = 1
                
                while self.running:
                    display_text = padded_text[position:position + width]
                    self.console.print(display_text, end='\r')
                    
                    if effect_config['bounce']:
                        if position + width >= len(padded_text):
                            direction = -1
                        elif position <= 0:
                            direction = 1
                    
                    position = (position + direction) % len(padded_text)
                    time.sleep(effect_config['speed'])
            
            return threading.Thread(target=marquee_animation, daemon=True)

    def create_status_indicator(self, status: str, message: str = "") -> None:
        status_config = self.config['status_indicators']
        
        if status not in status_config['styles']:
            return
        
        indicator = status_config['styles'][status]
        animation_config = status_config['animations'].get(status)
        
        if animation_config:
            if animation_config['type'] == "spinner":
                return self.create_spinner(
                    style=animation_config['style'],
                    text=message,
                    color=animation_config['color']
                )
            elif animation_config['type'] in ["fade", "pulse", "blink"]:
                def status_animation():
                    while self.running:
                        self.console.print(f"[{animation_config['color']}]{indicator}[/] {message}", end='\r')
                        time.sleep(animation_config.get('speed', 0.5))
                
                return threading.Thread(target=status_animation, daemon=True)
        
        # Static indicator
        self.console.print(f"{indicator} {message}")

    def handle_event(self, event: str, **kwargs) -> None:
        if event not in self.config['events']:
            return
        
        event_config = self.config['events'][event]
        animation_type = event_config['type']
        
        if animation_type == "spinner":
            spinner = self.create_spinner(
                style=event_config['style'],
                text=event_config['text'].format(**kwargs)
            )
            spinner.start()
            return spinner
        
        elif animation_type == "progress":
            progress = self.create_progress_bar(
                style=event_config['style']
            )
            return progress
        
        elif animation_type in ["fade", "pulse", "typing"]:
            text_effect = self.create_text_effect(
                animation_type,
                event_config['text'].format(**kwargs),
                **event_config
            )
            text_effect.start()
            return text_effect

    def _animation_loop(self) -> None:
        while self.running:
            try:
                # Process any queued animations
                while not self.animation_queue.empty():
                    anim_id, frame_func = self.animation_queue.get_nowait()
                    if anim_id in self.animations and self.animations[anim_id].running:
                        frame_func()
                
                # Maintain frame rate
                time.sleep(self.frame_time)
            
            except Exception as e:
                print(f"Animation error: {e}", file=sys.stderr)

    def stop(self) -> None:
        self.running = False
        self.animation_thread.join()

    def __del__(self) -> None:
        self.stop()

# Example usage:
if __name__ == "__main__":
    # Create animation manager
    animation_manager = AnimationManager()
    
    try:
        # Example: Create a spinner
        spinner = animation_manager.create_spinner(text="Loading...")
        spinner.start()
        time.sleep(2)
        
        # Example: Create a progress bar
        with animation_manager.create_progress_bar() as progress:
            task = progress.add_task("[cyan]Processing...", total=100)
        for i in range(100):
                progress.update(task, advance=1)
        time.sleep(0.05)
        
        # Example: Create a typing effect
        typing = animation_manager.create_text_effect("typing", "Hello, World!")
        typing.start()
        time.sleep(2)
        
        # Example: Handle an event
        animation_manager.handle_event("command_start")
        time.sleep(1)
        animation_manager.handle_event("command_success")
    
    finally:
        animation_manager.stop() 