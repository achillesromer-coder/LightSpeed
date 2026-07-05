#!/usr/bin/env python
"""
Portal Animations - Advanced UI Animation Library
LightSpeed Type I Civilization Platform

Comprehensive animation system for portal glass components:
- Smooth transitions and easing functions
- Particle effects and shaders
- Holographic animations
- Data flow visualizations
- Hover and interaction effects
- Matrix-style cascading effects

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

import math
import time
import random
from typing import List, Tuple, Callable, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class EasingFunction(Enum):
    """Animation easing functions"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"


@dataclass
class AnimationState:
    """Animation state tracker"""
    start_time: float
    duration: float
    start_value: float
    end_value: float
    easing: EasingFunction

    def get_progress(self) -> float:
        """Get animation progress (0.0 to 1.0)"""
        elapsed = time.time() - self.start_time
        return min(1.0, elapsed / self.duration)

    def is_complete(self) -> bool:
        """Check if animation is complete"""
        return self.get_progress() >= 1.0

    def get_value(self) -> float:
        """Get current animated value"""
        progress = self.get_progress()
        eased = apply_easing(progress, self.easing)
        return self.start_value + (self.end_value - self.start_value) * eased


def apply_easing(t: float, easing: EasingFunction) -> float:
    """
    Apply easing function to progress value

    Args:
        t: Progress value (0.0 to 1.0)
        easing: Easing function to apply

    Returns:
        Eased value (0.0 to 1.0)
    """
    if easing == EasingFunction.LINEAR:
        return t

    elif easing == EasingFunction.EASE_IN:
        return t * t

    elif easing == EasingFunction.EASE_OUT:
        return 1 - (1 - t) * (1 - t)

    elif easing == EasingFunction.EASE_IN_OUT:
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - (-2 * t + 2) ** 2 / 2

    elif easing == EasingFunction.BOUNCE:
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    elif easing == EasingFunction.ELASTIC:
        if t == 0 or t == 1:
            return t
        return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

    elif easing == EasingFunction.BACK:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)

    return t


@dataclass
class Particle:
    """Single particle for effects"""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: str
    size: float

    def update(self, dt: float = 0.016):
        """Update particle position and life"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0

    def get_alpha(self) -> float:
        """Get particle opacity based on life"""
        return max(0.0, min(1.0, self.life / self.max_life))


class ParticleSystem:
    """Particle system for visual effects"""

    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x: float, y: float, count: int = 10,
             velocity_range: Tuple[float, float] = (-50, 50),
             life_range: Tuple[float, float] = (0.5, 2.0),
             color: str = "#00ff88",
             size: float = 3.0):
        """Emit particles from position"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(10, 50)

            particle = Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(*life_range),
                max_life=random.uniform(*life_range),
                color=color,
                size=size
            )
            self.particles.append(particle)

    def update(self, dt: float = 0.016):
        """Update all particles"""
        # Update particles
        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive()]

    def get_particles(self) -> List[Particle]:
        """Get all active particles"""
        return self.particles

    def clear(self):
        """Clear all particles"""
        self.particles.clear()


class MatrixRain:
    """Matrix-style cascading rain effect"""

    def __init__(self, width: int, height: int, column_count: int = 20):
        self.width = width
        self.height = height
        self.column_count = column_count

        # Initialize columns
        self.columns: List[Dict[str, Any]] = []
        for i in range(column_count):
            self.columns.append({
                'x': (i / column_count) * width,
                'y': random.uniform(-height, 0),
                'speed': random.uniform(50, 200),
                'length': random.uniform(50, 200),
                'chars': self._generate_chars(20)
            })

    def _generate_chars(self, count: int) -> List[str]:
        """Generate random matrix characters"""
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
        return [random.choice(chars) for _ in range(count)]

    def update(self, dt: float = 0.016):
        """Update rain columns"""
        for column in self.columns:
            column['y'] += column['speed'] * dt

            # Reset column if it goes off screen
            if column['y'] > self.height + column['length']:
                column['y'] = -column['length']
                column['speed'] = random.uniform(50, 200)
                column['chars'] = self._generate_chars(20)

    def get_columns(self) -> List[Dict[str, Any]]:
        """Get all rain columns"""
        return self.columns


class HolographicEffect:
    """Holographic shimmer effect"""

    def __init__(self):
        self.time = 0.0
        self.noise_scale = 0.1

    def update(self, dt: float = 0.016):
        """Update effect time"""
        self.time += dt

    def get_color_offset(self, x: float, y: float) -> Tuple[int, int, int]:
        """Get color offset for holographic effect"""
        # Create interference pattern
        offset_x = math.sin(self.time * 2 + x * self.noise_scale) * 10
        offset_y = math.cos(self.time * 3 + y * self.noise_scale) * 10

        # RGB shift for chromatic aberration
        r_offset = int(offset_x)
        g_offset = 0
        b_offset = int(-offset_x)

        return (r_offset, g_offset, b_offset)

    def get_opacity(self, x: float, y: float) -> float:
        """Get opacity for scan line effect"""
        scan_line = math.sin(y * 0.1 + self.time * 5) * 0.5 + 0.5
        return 0.7 + scan_line * 0.3


class DataFlowAnimation:
    """Animated data flow visualization"""

    def __init__(self):
        self.flows: List[Dict[str, Any]] = []

    def add_flow(self, start_x: float, start_y: float,
                 end_x: float, end_y: float,
                 duration: float = 2.0,
                 color: str = "#00ff88"):
        """Add data flow animation"""
        self.flows.append({
            'start_x': start_x,
            'start_y': start_y,
            'end_x': end_x,
            'end_y': end_y,
            'start_time': time.time(),
            'duration': duration,
            'color': color
        })

    def update(self):
        """Update flows (remove completed)"""
        current_time = time.time()
        self.flows = [
            flow for flow in self.flows
            if (current_time - flow['start_time']) < flow['duration']
        ]

    def get_flows(self) -> List[Dict[str, Any]]:
        """Get all active flows"""
        active = []
        current_time = time.time()

        for flow in self.flows:
            elapsed = current_time - flow['start_time']
            progress = min(1.0, elapsed / flow['duration'])

            # Calculate current position
            x = flow['start_x'] + (flow['end_x'] - flow['start_x']) * progress
            y = flow['start_y'] + (flow['end_y'] - flow['start_y']) * progress

            active.append({
                **flow,
                'x': x,
                'y': y,
                'progress': progress
            })

        return active


class GlowEffect:
    """Pulsing glow effect"""

    def __init__(self, frequency: float = 1.0, min_opacity: float = 0.3,
                 max_opacity: float = 1.0):
        self.frequency = frequency
        self.min_opacity = min_opacity
        self.max_opacity = max_opacity
        self.time = 0.0

    def update(self, dt: float = 0.016):
        """Update glow time"""
        self.time += dt

    def get_opacity(self) -> float:
        """Get current glow opacity"""
        wave = (math.sin(self.time * self.frequency * 2 * math.pi) + 1) / 2
        return self.min_opacity + (self.max_opacity - self.min_opacity) * wave

    def get_size_multiplier(self) -> float:
        """Get size multiplier for glow"""
        return 1.0 + math.sin(self.time * self.frequency * 2 * math.pi) * 0.1


class RippleEffect:
    """Expanding ripple effect"""

    def __init__(self):
        self.ripples: List[Dict[str, Any]] = []

    def add_ripple(self, x: float, y: float, max_radius: float = 100,
                   duration: float = 1.0, color: str = "#00ff88"):
        """Add ripple at position"""
        self.ripples.append({
            'x': x,
            'y': y,
            'max_radius': max_radius,
            'start_time': time.time(),
            'duration': duration,
            'color': color
        })

    def update(self):
        """Update ripples (remove completed)"""
        current_time = time.time()
        self.ripples = [
            ripple for ripple in self.ripples
            if (current_time - ripple['start_time']) < ripple['duration']
        ]

    def get_ripples(self) -> List[Dict[str, Any]]:
        """Get all active ripples"""
        active = []
        current_time = time.time()

        for ripple in self.ripples:
            elapsed = current_time - ripple['start_time']
            progress = min(1.0, elapsed / ripple['duration'])

            active.append({
                **ripple,
                'radius': ripple['max_radius'] * progress,
                'opacity': 1.0 - progress
            })

        return active


class AnimationManager:
    """
    Central animation manager

    Manages all animation effects and provides simple API
    for portal glass components.
    """

    def __init__(self):
        self.particle_system = ParticleSystem()
        self.matrix_rain: Optional[MatrixRain] = None
        self.holographic = HolographicEffect()
        self.data_flow = DataFlowAnimation()
        self.glow = GlowEffect()
        self.ripple = RippleEffect()

        self.animations: Dict[str, AnimationState] = {}

    def animate_value(self, name: str, start: float, end: float,
                     duration: float = 1.0,
                     easing: EasingFunction = EasingFunction.EASE_IN_OUT) -> str:
        """Start value animation"""
        self.animations[name] = AnimationState(
            start_time=time.time(),
            duration=duration,
            start_value=start,
            end_value=end,
            easing=easing
        )
        return name

    def get_animated_value(self, name: str) -> Optional[float]:
        """Get current animated value"""
        if name in self.animations:
            state = self.animations[name]
            if state.is_complete():
                value = state.end_value
                del self.animations[name]
                return value
            return state.get_value()
        return None

    def enable_matrix_rain(self, width: int, height: int, column_count: int = 20):
        """Enable matrix rain effect"""
        self.matrix_rain = MatrixRain(width, height, column_count)

    def emit_particles(self, x: float, y: float, **kwargs):
        """Emit particles from position"""
        self.particle_system.emit(x, y, **kwargs)

    def add_data_flow(self, start_x: float, start_y: float,
                     end_x: float, end_y: float, **kwargs):
        """Add data flow animation"""
        self.data_flow.add_flow(start_x, start_y, end_x, end_y, **kwargs)

    def add_ripple(self, x: float, y: float, **kwargs):
        """Add ripple effect"""
        self.ripple.add_ripple(x, y, **kwargs)

    def update(self, dt: float = 0.016):
        """Update all animations"""
        self.particle_system.update(dt)
        if self.matrix_rain:
            self.matrix_rain.update(dt)
        self.holographic.update(dt)
        self.data_flow.update()
        self.glow.update(dt)
        self.ripple.update()

    def get_effects(self) -> Dict[str, Any]:
        """Get all active effects for rendering"""
        return {
            'particles': self.particle_system.get_particles(),
            'matrix_rain': self.matrix_rain.get_columns() if self.matrix_rain else [],
            'data_flows': self.data_flow.get_flows(),
            'ripples': self.ripple.get_ripples(),
            'holographic': self.holographic,
            'glow': self.glow
        }


# Singleton instance
_animation_manager: Optional[AnimationManager] = None


def get_animation_manager() -> AnimationManager:
    """Get global animation manager"""
    global _animation_manager
    if _animation_manager is None:
        _animation_manager = AnimationManager()
    return _animation_manager


if __name__ == "__main__":
    # Test animation system
    print("Portal Animation System Test")
    print("=" * 60)

    manager = get_animation_manager()

    # Test value animation
    print("\nTest: Value Animation")
    print("-" * 60)

    manager.animate_value('test', 0, 100, duration=2.0, easing=EasingFunction.EASE_IN_OUT)

    for i in range(21):
        time.sleep(0.1)
        value = manager.get_animated_value('test')
        if value is not None:
            print(f"  Progress: {i*5}% = Value: {value:.2f}")

    # Test particle system
    print("\nTest: Particle System")
    print("-" * 60)

    manager.emit_particles(100, 100, count=20, color='#00ff88')

    for i in range(5):
        manager.update(dt=0.2)
        particles = manager.particle_system.get_particles()
        print(f"  Time {i*0.2:.1f}s: {len(particles)} particles alive")

    # Test data flow
    print("\nTest: Data Flow")
    print("-" * 60)

    manager.add_data_flow(0, 0, 100, 100, duration=1.0, color='#ff8800')

    for i in range(11):
        time.sleep(0.1)
        flows = manager.data_flow.get_flows()
        if flows:
            flow = flows[0]
            print(f"  Progress: {i*10}% = Position: ({flow['x']:.1f}, {flow['y']:.1f})")

    print("\n" + "=" * 60)
    print("Animation system ready for portal glass components!")
