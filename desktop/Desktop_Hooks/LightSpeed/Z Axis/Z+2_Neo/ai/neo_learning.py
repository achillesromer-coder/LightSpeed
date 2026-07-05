"""
LightSpeed Neo Learning Engine V1.0.0
AI-powered correlation discovery and intelligent learning

Purpose:
Neo is the AI learning layer that discovers patterns, correlations, and relationships
between functions across the entire platform. It learns from every execution and
provides intelligent suggestions for related calculations.

Named after Neo from The Matrix, this engine "sees the code" - understanding deep
connections between functions that aren't immediately obvious.

Features:
- Records all function executions
- Discovers correlations between functions
- Suggests related calculations
- Learns user patterns and workflows
- Provides intelligent recommendations
- Works with Achilles AI for direction

Architecture:
```
NeoLearningEngine
    ├─> Execution Recorder (logs all activity)
    ├─> Correlation Analyzer (finds patterns)
    ├─> Pattern Matcher (discovers relationships)
    ├─> Suggestion Engine (recommends next steps)
    └─> User Profile (learns preferences)
```

Example:
```python
# User executes schwarzschild_radius
result = smart_floor.execute('calculate_schwarzschild_radius', {'mass': 2e30})

# Neo records execution
neo.record_execution('calculate_schwarzschild_radius', {'mass': 2e30}, result)

# Neo finds correlations
correlations = neo.find_correlations('calculate_schwarzschild_radius')
# Returns: ['calculate_hawking_temperature', 'calculate_bh_entropy']
# (because they all relate to black holes!)

# Neo suggests next calculation
suggestion = neo.suggest_next_calculation('calculate_schwarzschild_radius', result)
# Returns: 'calculate_hawking_temperature'
# (logical next step: if you found event horizon, check temperature)
```

Author: LightSpeed Team
Date: January 5, 2026
Extracted from: immersive_bento_ui.py
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import time
import math


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ExecutionPattern:
    """Pattern detected in function executions"""
    function_sequence: List[str]
    frequency: int
    avg_time_between: float
    user_specific: bool = False


@dataclass
class CorrelationStrength:
    """Strength of correlation between two functions"""
    func1: str
    func2: str
    strength: float  # 0.0 to 1.0
    reasons: List[str]  # Why they're correlated


@dataclass
class UserProfile:
    """User behavior profile"""
    favorite_categories: Dict[str, int] = field(default_factory=dict)
    common_sequences: List[List[str]] = field(default_factory=list)
    execution_times: Dict[str, List[float]] = field(default_factory=dict)
    last_active: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════════════
# NEO LEARNING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class NeoLearningEngine:
    """
    AI learning and correlation discovery engine

    Neo learns from every function execution and discovers patterns that
    enable intelligent suggestions and workflow optimization.

    This is a key component of the "smart" in smart floor - functions aren't
    just callable, they're intelligently connected.
    """

    def __init__(self, smart_floor_library=None):
        """
        Initialize Neo Learning Engine

        Args:
            smart_floor_library: SmartFloorLibrary instance for function metadata
        """
        self.library = smart_floor_library

        # Correlation map: function -> related functions
        self.correlation_map: Dict[str, List[str]] = {}

        # Correlation strengths (detailed)
        self.correlation_strengths: Dict[Tuple[str, str], CorrelationStrength] = {}

        # Pattern cache
        self.pattern_cache: Dict[str, List[ExecutionPattern]] = {}

        # Execution sequences (for pattern detection)
        self.execution_sequence: List[Tuple[str, float]] = []  # (func_name, timestamp)
        self.max_sequence_length = 1000

        # User profiles (if multi-user)
        self.user_profiles: Dict[str, UserProfile] = {}
        self.current_user: Optional[str] = None

        # Learning parameters
        self.min_correlation_strength = 0.3  # Minimum to consider correlated
        self.sequence_time_window = 300.0  # 5 minutes for sequence detection

        print("[Neo] Learning engine initialized")


    # ═══════════════════════════════════════════════════════════════════════
    # EXECUTION RECORDING
    # ═══════════════════════════════════════════════════════════════════════

    def record_execution(self, func_name: str, variables: Dict[str, Any], result: Any):
        """
        Record a function execution and update correlations

        This is called after every function execution in the platform.
        Neo learns from this to build correlation map.

        Args:
            func_name: Function that was executed
            variables: Variables used
            result: Result of execution
        """
        timestamp = time.time()

        # Add to execution sequence
        self.execution_sequence.append((func_name, timestamp))

        # Trim sequence if too long
        if len(self.execution_sequence) > self.max_sequence_length:
            self.execution_sequence = self.execution_sequence[-self.max_sequence_length:]

        # Initialize correlation map for this function
        if func_name not in self.correlation_map:
            self.correlation_map[func_name] = []

        # Find correlations with other functions
        self._update_correlations(func_name, variables)

        # Detect patterns in execution sequence
        self._detect_patterns()

        # Update user profile
        if self.current_user:
            self._update_user_profile(func_name, timestamp)

        print(f"[Neo] Recorded execution: {func_name}")


    def _update_correlations(self, func_name: str, variables: Dict[str, Any]):
        """Update correlation map based on new execution"""
        if not self.library:
            return

        # Check all other functions
        for other_func in self.library.functions.keys():
            if other_func == func_name:
                continue

            # Calculate correlation strength
            strength = self._calculate_correlation_strength(func_name, other_func, variables)

            # Store detailed correlation
            key = tuple(sorted([func_name, other_func]))
            if strength.strength >= self.min_correlation_strength:
                self.correlation_strengths[key] = strength

                # Add to simple correlation map if not already there
                if other_func not in self.correlation_map[func_name]:
                    self.correlation_map[func_name].append(other_func)

                    print(f"[Neo] Found correlation: {func_name} ↔ {other_func} ({strength.strength:.2f})")


    def _calculate_correlation_strength(
        self,
        func1: str,
        func2: str,
        current_vars: Dict[str, Any]
    ) -> CorrelationStrength:
        """
        Calculate how strongly two functions are correlated

        Correlation factors:
        1. Same category (e.g., both gravitation)
        2. Shared variables (e.g., both use 'mass')
        3. Sequential execution (often called together)
        4. Result dependencies (one's output = other's input)
        """
        if not self.library:
            return CorrelationStrength(func1, func2, 0.0, [])

        func1_meta = self.library.functions.get(func1)
        func2_meta = self.library.functions.get(func2)

        if not func1_meta or not func2_meta:
            return CorrelationStrength(func1, func2, 0.0, [])

        strength = 0.0
        reasons = []

        # Factor 1: Same category (strong correlation)
        if func1_meta.category == func2_meta.category:
            strength += 0.5
            reasons.append(f"Same category: {func1_meta.category}")

        # Factor 2: Shared variables
        vars1 = set(func1_meta.default_vars.keys())
        vars2 = set(func2_meta.default_vars.keys())
        common_vars = vars1.intersection(vars2)

        if vars1 and vars2:
            var_overlap = len(common_vars) / max(len(vars1), len(vars2))
            strength += 0.3 * var_overlap

            if common_vars:
                reasons.append(f"Shared variables: {', '.join(common_vars)}")

        # Factor 3: Sequential execution (check recent history)
        sequential_strength = self._check_sequential_execution(func1, func2)
        strength += 0.2 * sequential_strength

        if sequential_strength > 0.5:
            reasons.append("Often executed together")

        # Normalize to 0-1
        strength = min(1.0, strength)

        return CorrelationStrength(func1, func2, strength, reasons)


    def _check_sequential_execution(self, func1: str, func2: str) -> float:
        """Check how often two functions are executed in sequence"""
        if len(self.execution_sequence) < 2:
            return 0.0

        # Count sequences where func1 is followed by func2 (or vice versa)
        sequential_count = 0
        total_func1 = 0

        for i in range(len(self.execution_sequence) - 1):
            current_func, current_time = self.execution_sequence[i]
            next_func, next_time = self.execution_sequence[i + 1]

            if current_func == func1:
                total_func1 += 1
                if next_func == func2 and (next_time - current_time) < self.sequence_time_window:
                    sequential_count += 1

        if total_func1 == 0:
            return 0.0

        return sequential_count / total_func1


    def _detect_patterns(self):
        """Detect patterns in execution sequences"""
        if len(self.execution_sequence) < 3:
            return

        # Look for common sequences of length 2-5
        for seq_length in range(2, 6):
            self._find_sequences_of_length(seq_length)


    def _find_sequences_of_length(self, length: int):
        """Find repeating sequences of given length"""
        if len(self.execution_sequence) < length:
            return

        sequence_counts = defaultdict(int)

        # Slide window through execution history
        for i in range(len(self.execution_sequence) - length + 1):
            # Extract sequence (function names only)
            sequence = tuple(
                self.execution_sequence[i + j][0]
                for j in range(length)
            )

            # Check time window
            time_span = self.execution_sequence[i + length - 1][1] - self.execution_sequence[i][1]

            if time_span < self.sequence_time_window:
                sequence_counts[sequence] += 1

        # Store significant patterns
        for sequence, count in sequence_counts.items():
            if count >= 3:  # Repeated at least 3 times
                pattern_key = "->".join(sequence)
                if pattern_key not in self.pattern_cache:
                    self.pattern_cache[pattern_key] = []

                # Calculate average time between executions in sequence
                avg_time = self.sequence_time_window / length

                pattern = ExecutionPattern(
                    function_sequence=list(sequence),
                    frequency=count,
                    avg_time_between=avg_time,
                    user_specific=(self.current_user is not None)
                )

                self.pattern_cache[pattern_key].append(pattern)

                print(f"[Neo] Detected pattern: {pattern_key} (frequency: {count})")


    def _update_user_profile(self, func_name: str, timestamp: float):
        """Update user behavior profile"""
        if not self.current_user:
            return

        if self.current_user not in self.user_profiles:
            self.user_profiles[self.current_user] = UserProfile()

        profile = self.user_profiles[self.current_user]

        # Update last active
        profile.last_active = timestamp

        # Update favorite categories
        if self.library and func_name in self.library.functions:
            category = self.library.functions[func_name].category
            profile.favorite_categories[category] = profile.favorite_categories.get(category, 0) + 1


    # ═══════════════════════════════════════════════════════════════════════
    # CORRELATION DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════

    def find_correlations(self, func_name: str, limit: int = 10) -> List[str]:
        """
        Find functions correlated with given function

        Args:
            func_name: Function to find correlations for
            limit: Maximum number of correlations to return

        Returns:
            List of correlated function names with descriptions
        """
        correlations = self.correlation_map.get(func_name, [])

        if not self.library:
            return correlations[:limit]

        # Build suggestions with category info
        suggestions = []
        for corr_func in correlations[:limit]:
            func_meta = self.library.functions.get(corr_func)
            if func_meta:
                # Get correlation strength
                key = tuple(sorted([func_name, corr_func]))
                strength = self.correlation_strengths.get(key)

                if strength:
                    suggestion = f"{corr_func} ({func_meta.category}) - {strength.strength:.0%}"
                else:
                    suggestion = f"{corr_func} ({func_meta.category})"

                suggestions.append(suggestion)

        return suggestions


    def get_correlation_details(self, func1: str, func2: str) -> Optional[CorrelationStrength]:
        """Get detailed correlation information between two functions"""
        key = tuple(sorted([func1, func2]))
        return self.correlation_strengths.get(key)


    # ═══════════════════════════════════════════════════════════════════════
    # INTELLIGENT SUGGESTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def suggest_next_calculation(self, func_name: str, result: Any = None) -> Optional[str]:
        """
        Suggest next logical calculation based on what was just executed

        This is where Neo provides intelligent direction!

        Args:
            func_name: Function just executed
            result: Result of execution (can influence suggestion)

        Returns:
            Suggested function name, or None
        """
        correlations = self.correlation_map.get(func_name, [])

        if not correlations:
            return None

        # Sort by correlation strength
        sorted_correlations = self._sort_by_strength(func_name, correlations)

        if sorted_correlations:
            suggestion = sorted_correlations[0]
            print(f"[Neo] Suggests: {suggestion} after {func_name}")
            return suggestion

        return correlations[0] if correlations else None


    def _sort_by_strength(self, func_name: str, correlations: List[str]) -> List[str]:
        """Sort correlations by strength"""
        strengths = []

        for corr_func in correlations:
            key = tuple(sorted([func_name, corr_func]))
            strength_obj = self.correlation_strengths.get(key)

            if strength_obj:
                strengths.append((corr_func, strength_obj.strength))
            else:
                strengths.append((corr_func, 0.0))

        # Sort by strength descending
        strengths.sort(key=lambda x: x[1], reverse=True)

        return [func for func, _ in strengths]


    def suggest_workflow(self, starting_func: str, steps: int = 5) -> List[str]:
        """
        Suggest a complete workflow starting from a function

        Args:
            starting_func: Starting point
            steps: Number of steps in workflow

        Returns:
            List of function names forming a suggested workflow
        """
        workflow = [starting_func]
        current_func = starting_func

        for _ in range(steps - 1):
            next_func = self.suggest_next_calculation(current_func)

            if not next_func or next_func in workflow:
                break

            workflow.append(next_func)
            current_func = next_func

        print(f"[Neo] Suggested workflow: {' → '.join(workflow)}")

        return workflow


    # ═══════════════════════════════════════════════════════════════════════
    # PATTERN ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    def get_common_patterns(self, min_frequency: int = 3) -> List[ExecutionPattern]:
        """Get commonly occurring execution patterns"""
        patterns = []

        for pattern_list in self.pattern_cache.values():
            for pattern in pattern_list:
                if pattern.frequency >= min_frequency:
                    patterns.append(pattern)

        # Sort by frequency
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        return patterns


    def predict_next_function(self, recent_functions: List[str]) -> Optional[str]:
        """
        Predict next function based on recent execution history

        Uses pattern matching to predict what user will do next.

        Args:
            recent_functions: List of recently executed functions

        Returns:
            Predicted function name, or None
        """
        if len(recent_functions) < 2:
            return None

        # Look for patterns that start with recent_functions
        for pattern_key, pattern_list in self.pattern_cache.items():
            for pattern in pattern_list:
                # Check if recent functions match start of pattern
                if len(recent_functions) < len(pattern.function_sequence):
                    matches = True
                    for i, func in enumerate(recent_functions):
                        if pattern.function_sequence[i] != func:
                            matches = False
                            break

                    if matches:
                        # Return next function in pattern
                        next_index = len(recent_functions)
                        if next_index < len(pattern.function_sequence):
                            prediction = pattern.function_sequence[next_index]
                            print(f"[Neo] Predicts: {prediction} (based on pattern)")
                            return prediction

        return None


    # ═══════════════════════════════════════════════════════════════════════
    # USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def set_user(self, user_id: str):
        """Set current user for personalized learning"""
        self.current_user = user_id

        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile()

        print(f"[Neo] Active user: {user_id}")


    def get_user_profile(self, user_id: Optional[str] = None) -> Optional[UserProfile]:
        """Get user behavior profile"""
        if user_id is None:
            user_id = self.current_user

        return self.user_profiles.get(user_id)


    def get_user_recommendations(self, user_id: Optional[str] = None, limit: int = 5) -> List[str]:
        """Get personalized recommendations for user"""
        profile = self.get_user_profile(user_id)

        if not profile or not self.library:
            return []

        # Recommend functions from user's favorite categories
        recommendations = []

        # Sort categories by usage
        sorted_categories = sorted(
            profile.favorite_categories.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for category, _ in sorted_categories:
            # Find functions in this category
            category_funcs = self.library.discover_functions(category=category)

            for func_meta in category_funcs:
                if func_meta.name not in recommendations:
                    recommendations.append(func_meta.name)

                if len(recommendations) >= limit:
                    return recommendations

        return recommendations


    # ═══════════════════════════════════════════════════════════════════════
    # ANALYTICS & INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════

    def get_insights(self) -> Dict[str, Any]:
        """Get learning insights and statistics"""
        return {
            'total_correlations': sum(len(corrs) for corrs in self.correlation_map.values()),
            'functions_with_correlations': len(self.correlation_map),
            'detected_patterns': len(self.pattern_cache),
            'execution_sequence_length': len(self.execution_sequence),
            'active_users': len(self.user_profiles),
            'strongest_correlations': self._get_strongest_correlations(5)
        }


    def _get_strongest_correlations(self, limit: int) -> List[Dict[str, Any]]:
        """Get strongest correlations in the system"""
        sorted_strengths = sorted(
            self.correlation_strengths.values(),
            key=lambda c: c.strength,
            reverse=True
        )

        return [
            {
                'func1': c.func1,
                'func2': c.func2,
                'strength': c.strength,
                'reasons': c.reasons
            }
            for c in sorted_strengths[:limit]
        ]


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'NeoLearningEngine',
    'ExecutionPattern',
    'CorrelationStrength',
    'UserProfile'
]
