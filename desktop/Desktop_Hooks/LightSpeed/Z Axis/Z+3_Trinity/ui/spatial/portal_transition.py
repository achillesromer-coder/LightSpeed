"""
LightSpeed V0.9.5 - Portal Transition Effects
Zoom-through dissolve animations between Z-floors

Features:
- Dissolve current grid
- Scale up target floor
- Particle effects
- Ease-in/out motion damping
- Visual feedback (glow, blur)

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time
import math


class TransitionEffect(Enum):
    """Types of portal transition effects"""
    DISSOLVE = "dissolve"
    ZOOM_THROUGH = "zoom_through"
    FADE = "fade"
    WARP = "warp"
    PARTICLE_BURST = "particle_burst"


@dataclass
class DissolveAnimation:
    """Configuration for dissolve animation"""
    start_time: float
    duration: float = 0.8  # seconds
    effect: TransitionEffect = TransitionEffect.ZOOM_THROUGH
    on_complete: Optional[Callable] = None

    # Animation state
    current_opacity: float = 1.0
    current_scale: float = 1.0
    particles: list = None

    def __post_init__(self):
        if self.particles is None:
            self.particles = []


class PortalTransition:
    """
    Portal transition effect system.

    Implements zoom-through transitions where:
    1. Current grid dissolves (fade out)
    2. Target floor scales up from center
    3. Particle effects for visual feedback
    4. Ease-in/out damping
    """

    # Transition constants
    PARTICLE_COUNT = 20
    PARTICLE_SPEED = 200.0  # pixels/second
    PARTICLE_LIFETIME = 0.5  # seconds
    GLOW_INTENSITY = 1.5
    BLUR_RADIUS = 10

    def __init__(self, canvas: tk.Canvas):
        """
        Initialize portal transition system.

        Args:
            canvas: Target canvas for rendering transitions
        """
        self.canvas = canvas
        self.active_animation: Optional[DissolveAnimation] = None
        self.is_animating = False
        self.animation_frame_id = None

    def start_transition(self, effect: TransitionEffect = TransitionEffect.ZOOM_THROUGH,
                        duration: float = 0.8, on_complete: Optional[Callable] = None):
        """
        Start a portal transition animation.

        Args:
            effect: Type of transition effect
            duration: Animation duration in seconds
            on_complete: Callback when animation completes
        """
        # Cancel existing animation
        if self.is_animating:
            self.cancel_transition()

        # Create new animation
        self.active_animation = DissolveAnimation(
            start_time=time.time(),
            duration=duration,
            effect=effect,
            on_complete=on_complete
        )

        # Generate particles
        if effect == TransitionEffect.PARTICLE_BURST:
            self._generate_particles()

        # Start animation loop
        self.is_animating = True
        self._animate_frame()

    def cancel_transition(self):
        """Cancel active transition"""
        if self.animation_frame_id:
            self.canvas.after_cancel(self.animation_frame_id)
            self.animation_frame_id = None

        self.is_animating = False
        self.active_animation = None

        # Clear canvas effects
        self.canvas.delete('transition_effect')

    def _animate_frame(self):
        """Render single animation frame"""
        if not self.is_animating or not self.active_animation:
            return

        # Calculate progress
        elapsed = time.time() - self.active_animation.start_time
        progress = min(1.0, elapsed / self.active_animation.duration)

        # Apply easing
        eased_progress = self._ease_in_out(progress)

        # Update animation state
        self.active_animation.current_opacity = 1.0 - eased_progress
        self.active_animation.current_scale = 1.0 + (eased_progress * 2.0)

        # Render based on effect type
        if self.active_animation.effect == TransitionEffect.DISSOLVE:
            self._render_dissolve(eased_progress)
        elif self.active_animation.effect == TransitionEffect.ZOOM_THROUGH:
            self._render_zoom_through(eased_progress)
        elif self.active_animation.effect == TransitionEffect.FADE:
            self._render_fade(eased_progress)
        elif self.active_animation.effect == TransitionEffect.PARTICLE_BURST:
            self._render_particles(elapsed)

        # Check completion
        if progress >= 1.0:
            self._complete_animation()
        else:
            # Schedule next frame (60 FPS)
            self.animation_frame_id = self.canvas.after(16, self._animate_frame)

    def _render_dissolve(self, progress: float):
        """Render dissolve effect"""
        # Clear previous frame
        self.canvas.delete('transition_effect')

        # Overlay with decreasing opacity
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Calculate alpha (0-255)
        alpha = int(self.active_animation.current_opacity * 255)

        # Create semi-transparent overlay
        # Note: Tkinter doesn't support alpha directly, so we simulate with stipple
        if alpha > 0:
            stipple_patterns = ['gray75', 'gray50', 'gray25', 'gray12']
            stipple_index = min(3, int((1.0 - progress) * 4))

            self.canvas.create_rectangle(
                0, 0, width, height,
                fill='#000000',
                stipple=stipple_patterns[stipple_index],
                tags='transition_effect'
            )

    def _render_zoom_through(self, progress: float):
        """Render zoom-through effect"""
        # Clear previous frame
        self.canvas.delete('transition_effect')

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width // 2
        center_y = height // 2

        # Draw expanding circle (portal)
        radius = int(progress * math.sqrt(width**2 + height**2))

        # Outer glow
        for i in range(3):
            glow_radius = radius + (i * 10)
            glow_alpha = int((1.0 - progress) * 100 * (3 - i) / 3)

            self.canvas.create_oval(
                center_x - glow_radius, center_y - glow_radius,
                center_x + glow_radius, center_y + glow_radius,
                outline='#00FFFF',
                width=2,
                tags='transition_effect'
            )

        # Center portal ring
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline='#00FFFF',
            width=4,
            tags='transition_effect'
        )

        # Radial lines (warp effect)
        num_lines = 12
        for i in range(num_lines):
            angle = (i / num_lines) * 2 * math.pi
            line_length = radius * 0.8

            x1 = center_x + math.cos(angle) * (radius * 0.2)
            y1 = center_y + math.sin(angle) * (radius * 0.2)
            x2 = center_x + math.cos(angle) * line_length
            y2 = center_y + math.sin(angle) * line_length

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill='#0088FF',
                width=2,
                tags='transition_effect'
            )

    def _render_fade(self, progress: float):
        """Render simple fade effect"""
        self.canvas.delete('transition_effect')

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Decreasing opacity overlay
        if progress < 1.0:
            stipple_patterns = ['gray75', 'gray50', 'gray25', 'gray12', '']
            stipple_index = min(4, int(progress * 5))

            if stipple_index < 4:
                self.canvas.create_rectangle(
                    0, 0, width, height,
                    fill='#000B1F',
                    stipple=stipple_patterns[stipple_index],
                    tags='transition_effect'
                )

    def _generate_particles(self):
        """Generate particles for burst effect"""
        if not self.active_animation:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width // 2
        center_y = height // 2

        self.active_animation.particles = []

        for i in range(self.PARTICLE_COUNT):
            angle = (i / self.PARTICLE_COUNT) * 2 * math.pi
            speed = self.PARTICLE_SPEED

            particle = {
                'x': center_x,
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': self.PARTICLE_LIFETIME,
                'birth_time': time.time()
            }

            self.active_animation.particles.append(particle)

    def _render_particles(self, elapsed: float):
        """Render particle burst effect"""
        self.canvas.delete('transition_effect')

        if not self.active_animation or not self.active_animation.particles:
            return

        current_time = time.time()

        for particle in self.active_animation.particles:
            age = current_time - particle['birth_time']

            if age > particle['lifetime']:
                continue

            # Update position
            particle['x'] += particle['vx'] * 0.016  # 16ms frame
            particle['y'] += particle['vy'] * 0.016

            # Fade based on age
            alpha = 1.0 - (age / particle['lifetime'])
            size = int(5 * alpha)

            if size > 0:
                # Draw particle
                self.canvas.create_oval(
                    particle['x'] - size, particle['y'] - size,
                    particle['x'] + size, particle['y'] + size,
                    fill='#00FFFF',
                    outline='',
                    tags='transition_effect'
                )

    def _ease_in_out(self, t: float) -> float:
        """Cubic ease-in-out interpolation"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def _complete_animation(self):
        """Complete the animation"""
        self.is_animating = False

        # Clear effects
        self.canvas.delete('transition_effect')

        # Call completion callback
        if self.active_animation and self.active_animation.on_complete:
            self.active_animation.on_complete()

        self.active_animation = None


# Export
__all__ = ['PortalTransition', 'TransitionEffect', 'DissolveAnimation']
