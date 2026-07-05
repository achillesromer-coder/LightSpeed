"""
LightSpeed Achilles AI Assistant V1.0.0
Intelligent guidance and direction system

Purpose:
Achilles is the AI assistant that provides intelligent direction and guidance
throughout the LightSpeed platform. Working with Neo's learning engine,
Achilles helps users navigate the system, discover functions, and achieve goals.

Named after Achilles (ultimate warrior), this AI is your strategic advisor,
helping you find the most effective path to your objectives.

Features:
- Natural language understanding
- Context-aware suggestions
- Floor navigation assistance
- Function recommendations
- Smart search across platform
- Learning from user behavior
- Integration with Neo AI

Architecture:
```
AchillesAssistant
    ├─> Context Manager (understands current state)
    ├─> Query Processor (interprets user requests)
    ├─> Recommendation Engine (suggests actions)
    ├─> Navigation Guide (helps find resources)
    └─> Learning Integration (works with Neo)
```

Example Interactions:
```
User: "I need to calculate gravitational effects"
Achilles: "I can help! Try these functions on Z0 (TheConstruct):
          - calculate_schwarzschild_radius
          - calculate_time_dilation
          - calculate_einstein_ring
          Navigate to Z0 floor to access physics simulations."

User: "What should I do next?"
Achilles: "Based on your schwarzschild_radius calculation,
          Neo suggests calculate_hawking_temperature to determine
          the temperature of this black hole. Would you like me
          to execute that?"

User: "Show me all documents about AI"
Achilles: "Found 15 documents across 3 floors:
          Z+2 (Neo): 8 documents
          Z-1 (Oracle): 5 documents
          Z+1 (Architect): 2 documents
          Navigate to Z+2 to see AI research library."
```

Author: LightSpeed Team
Date: January 5, 2026
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import time


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class QueryIntent:
    """Interpreted user intent from query"""
    intent_type: str  # navigate, calculate, search, help, suggest
    entities: Dict[str, Any]
    confidence: float
    original_query: str


@dataclass
class Suggestion:
    """Suggestion from Achilles"""
    suggestion_type: str  # function, floor, document, workflow
    content: str
    reason: str
    priority: int  # 1-10


@dataclass
class ConversationContext:
    """Current conversation context"""
    last_query: str = ""
    last_function: str = ""
    current_floor: str = "Z0_TheConstruct"
    active_topic: str = ""
    conversation_history: List[Tuple[str, str]] = None  # (query, response)

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


# ═══════════════════════════════════════════════════════════════════════════
# ACHILLES AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════

class AchillesAssistant:
    """
    Achilles AI - Intelligent assistant for LightSpeed platform

    Provides strategic guidance, smart suggestions, and helps users
    navigate and utilize the platform effectively.
    """

    def __init__(self, orchestrator=None):
        """
        Initialize Achilles Assistant

        Args:
            orchestrator: InterfaceOrchestrator for system access
        """
        self.orchestrator = orchestrator
        self.context = ConversationContext()

        # Quick access to services
        self.smart_floor = orchestrator.smart_floor if orchestrator else None
        self.neo_ai = orchestrator.neo_ai if orchestrator else None
        self.db = orchestrator.db if orchestrator else None

        # Intent patterns (simple keyword-based for now)
        self._setup_intent_patterns()

        print("[Achilles] AI Assistant initialized and ready")


    def _setup_intent_patterns(self):
        """Setup patterns for intent recognition"""
        self.intent_patterns = {
            'navigate': [
                r'go to (.*)',
                r'navigate to (.*)',
                r'show me (.*) floor',
                r'take me to (.*)',
                r'where is (.*)',
            ],
            'calculate': [
                r'calculate (.*)',
                r'compute (.*)',
                r'find (.*) for (.*)',
                r'what is (.*)',
            ],
            'search': [
                r'search (.*)',
                r'find (.*)',
                r'show me (.*)',
                r'look for (.*)',
            ],
            'suggest': [
                r'what should I do',
                r'what.*next',
                r'suggest (.*)',
                r'recommend (.*)',
                r'help me with (.*)',
            ],
            'help': [
                r'help',
                r'how do I (.*)',
                r'how to (.*)',
                r'what can you do',
            ]
        }


    # ═══════════════════════════════════════════════════════════════════════
    # QUERY PROCESSING
    # ═══════════════════════════════════════════════════════════════════════

    def process_query(self, query: str, user_context: Optional[Dict] = None) -> str:
        """
        Process user query and provide intelligent response

        Args:
            query: User's natural language query
            user_context: Additional context (current floor, etc.)

        Returns:
            Achilles response
        """
        # Update context
        if user_context:
            if 'current_floor' in user_context:
                self.context.current_floor = user_context['current_floor']

        # Parse intent
        intent = self._parse_intent(query)

        # Generate response based on intent
        if intent.intent_type == 'navigate':
            response = self._handle_navigation(intent)
        elif intent.intent_type == 'calculate':
            response = self._handle_calculation(intent)
        elif intent.intent_type == 'search':
            response = self._handle_search(intent)
        elif intent.intent_type == 'suggest':
            response = self._handle_suggestion(intent)
        elif intent.intent_type == 'help':
            response = self._handle_help(intent)
        else:
            response = self._handle_general(intent)

        # Update conversation history
        self.context.last_query = query
        self.context.conversation_history.append((query, response))

        # Keep history reasonable size
        if len(self.context.conversation_history) > 50:
            self.context.conversation_history = self.context.conversation_history[-50:]

        print(f"[Achilles] Query: '{query}' → Intent: {intent.intent_type}")

        return response


    def _parse_intent(self, query: str) -> QueryIntent:
        """Parse query to understand user intent"""
        query_lower = query.lower().strip()

        # Try to match patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    entities = {}
                    if match.groups():
                        entities['target'] = match.group(1)

                    return QueryIntent(
                        intent_type=intent_type,
                        entities=entities,
                        confidence=0.8,
                        original_query=query
                    )

        # No match - general intent
        return QueryIntent(
            intent_type='general',
            entities={},
            confidence=0.5,
            original_query=query
        )


    # ═══════════════════════════════════════════════════════════════════════
    # INTENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════

    def _handle_navigation(self, intent: QueryIntent) -> str:
        """Handle navigation requests"""
        target = intent.entities.get('target', '').lower()

        # Check if target is a floor
        if self.orchestrator:
            floors = self.orchestrator.get_all_floors()

            # Match floor by name or ID
            for floor_id, floor_def in floors.items():
                if target in floor_def.name.lower() or target in floor_id.lower():
                    # Build response
                    response = f"Navigating to {floor_def.name} ({floor_id})\n\n"
                    response += f"📍 Floor Y: {floor_def.y_position}m\n"
                    response += f"🎨 Color: {floor_def.color}\n"
                    response += f"📖 {floor_def.description}\n\n"

                    # Add what's on this floor
                    if self.smart_floor:
                        floor_funcs = self.smart_floor.discover_functions(floor=floor_id)
                        if floor_funcs:
                            response += f"⚡ {len(floor_funcs)} functions available on this floor\n"

                    response += "\n💡 Use WASD to move, Space to jump"

                    return response

        return f"I'm not sure where '{target}' is. Try:\n" \
               f"- 'Navigate to Neo' (AI floor)\n" \
               f"- 'Navigate to TheConstruct' (Physics floor)\n" \
               f"- 'Navigate to Oracle' (Document library)"


    def _handle_calculation(self, intent: QueryIntent) -> str:
        """Handle calculation requests"""
        target = intent.entities.get('target', '')

        if not self.smart_floor:
            return "Smart Floor library not available. Cannot execute calculations."

        # Find matching functions
        all_functions = self.smart_floor.discover_functions()

        matches = []
        for func_meta in all_functions:
            if target.lower() in func_meta.name.lower():
                matches.append(func_meta)

        if not matches:
            # Fuzzy match on category
            categories = self.smart_floor.get_categories()
            for category in categories:
                if target.lower() in category.lower():
                    cat_funcs = self.smart_floor.discover_functions(category=category)
                    response = f"Found {len(cat_funcs)} functions in category '{category}':\n\n"

                    for func_meta in cat_funcs[:5]:
                        response += f"  • {func_meta.name}\n"
                        if func_meta.description:
                            response += f"    {func_meta.description}\n"

                    return response

            return f"I couldn't find a calculation for '{target}'.\n\n" \
                   f"Available categories:\n" + "\n".join(f"  • {cat}" for cat in categories)

        # Found matches
        if len(matches) == 1:
            func = matches[0]
            response = f"📊 {func.name}\n\n"
            response += f"Category: {func.category}\n"
            response += f"Floor: {func.floor}\n\n"
            response += f"Default variables:\n"

            for var, val in func.default_vars.items():
                response += f"  • {var}: {val}\n"

            response += f"\n💡 Interact with the function widget to execute"

            return response
        else:
            response = f"Found {len(matches)} matching functions:\n\n"
            for func in matches[:5]:
                response += f"  • {func.name} ({func.category})\n"

            return response


    def _handle_search(self, intent: QueryIntent) -> str:
        """Handle search requests"""
        target = intent.entities.get('target', '')

        results = []

        # Search functions
        if self.smart_floor:
            all_funcs = self.smart_floor.discover_functions()
            for func in all_funcs:
                if target.lower() in func.name.lower() or target.lower() in func.category.lower():
                    results.append(('function', func.name, func.floor))

        if not results:
            return f"No results found for '{target}'.\n\n" \
                   f"Try searching for:\n" \
                   f"  • Function names (e.g., 'schwarzschild')\n" \
                   f"  • Categories (e.g., 'quantum', 'gravitation')\n" \
                   f"  • Floors (e.g., 'Neo', 'TheConstruct')"

        # Build results
        response = f"🔍 Found {len(results)} results for '{target}':\n\n"

        # Group by floor
        by_floor = {}
        for result_type, name, floor in results:
            if floor not in by_floor:
                by_floor[floor] = []
            by_floor[floor].append((result_type, name))

        for floor, items in by_floor.items():
            response += f"📍 {floor}:\n"
            for result_type, name in items[:5]:
                response += f"  • {name} ({result_type})\n"
            response += "\n"

        return response


    def _handle_suggestion(self, intent: QueryIntent) -> str:
        """Handle suggestion requests"""
        suggestions = []

        # Get suggestions from Neo AI
        if self.neo_ai and self.context.last_function:
            correlations = self.neo_ai.find_correlations(self.context.last_function)
            if correlations:
                suggestions.append(Suggestion(
                    suggestion_type='function',
                    content=f"Based on your last calculation ({self.context.last_function}), " \
                            f"Neo suggests:\n" + "\n".join(f"  • {c}" for c in correlations[:3]),
                    reason="Neo AI correlation analysis",
                    priority=9
                ))

        # User-specific suggestions
        if self.neo_ai and self.neo_ai.current_user:
            user_recs = self.neo_ai.get_user_recommendations(limit=3)
            if user_recs:
                suggestions.append(Suggestion(
                    suggestion_type='function',
                    content=f"Based on your interests:\n" + \
                            "\n".join(f"  • {r}" for r in user_recs),
                    reason="Your usage patterns",
                    priority=7
                ))

        # Floor-based suggestions
        if self.smart_floor:
            current_floor_funcs = self.smart_floor.discover_functions(
                floor=self.context.current_floor
            )
            if current_floor_funcs:
                suggestions.append(Suggestion(
                    suggestion_type='floor',
                    content=f"On current floor ({self.context.current_floor}):\n" + \
                            "\n".join(f"  • {f.name}" for f in current_floor_funcs[:3]),
                    reason=f"Available on {self.context.current_floor}",
                    priority=5
                ))

        # Build response
        if suggestions:
            # Sort by priority
            suggestions.sort(key=lambda s: s.priority, reverse=True)

            response = "💡 Here are my suggestions:\n\n"
            for i, sug in enumerate(suggestions[:3], 1):
                response += f"{i}. {sug.content}\n"
                response += f"   _{sug.reason}_\n\n"

            return response

        return "I don't have specific suggestions right now. Try:\n" \
               "  • Execute a function to get related suggestions\n" \
               "  • Navigate to different floors to discover more\n" \
               "  • Ask 'what can you do' for capabilities"


    def _handle_help(self, intent: QueryIntent) -> str:
        """Handle help requests"""
        response = "🤖 **Achilles AI Assistant**\n\n"
        response += "I can help you with:\n\n"

        response += "**Navigation**\n"
        response += "  • 'Navigate to Neo' - Go to specific floor\n"
        response += "  • 'Where is the library' - Find locations\n\n"

        response += "**Calculations**\n"
        response += "  • 'Calculate schwarzschild radius' - Execute functions\n"
        response += "  • 'What is gravitational time dilation' - Learn about functions\n\n"

        response += "**Search**\n"
        response += "  • 'Find quantum functions' - Search platform\n"
        response += "  • 'Show me all physics simulations' - Discover resources\n\n"

        response += "**Suggestions**\n"
        response += "  • 'What should I do next' - Get recommendations\n"
        response += "  • 'Suggest related calculations' - Find correlations\n\n"

        response += "**Current Context**\n"
        response += f"  • Floor: {self.context.current_floor}\n"

        if self.smart_floor:
            stats = self.smart_floor.get_global_stats()
            response += f"  • Total Functions: {stats['total_functions']}\n"
            response += f"  • Total Executions: {stats['total_executions']}\n"

        return response


    def _handle_general(self, intent: QueryIntent) -> str:
        """Handle general/unclear queries"""
        return "I'm not sure what you're asking. Try:\n" \
               "  • 'Help' - See what I can do\n" \
               "  • 'Navigate to [floor name]' - Go somewhere\n" \
               "  • 'Calculate [function name]' - Execute calculations\n" \
               "  • 'What should I do next' - Get suggestions"


    # ═══════════════════════════════════════════════════════════════════════
    # SMART SUGGESTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def suggest_floor(self, task_description: str) -> Optional[str]:
        """Suggest which floor to visit for a task"""
        task_lower = task_description.lower()

        # Simple keyword matching for floors
        floor_keywords = {
            'Z+3_Trinity': ['dashboard', 'ui', 'settings', 'profile', 'control'],
            'Z+2_Neo': ['ai', 'learning', 'neural', 'intelligence', 'correlation'],
            'Z+1_Architect': ['plan', 'mission', 'strategy', 'okr', 'goal'],
            'Z0_TheConstruct': ['physics', 'simulation', 'quantum', 'gravity', 'calculate'],
            'Z-1_Morpheus': ['knowledge', 'search', 'docs', 'index', 'analysis'],
            'Z-2_Oracle': ['document', 'library', 'vault', 'archive', 'ip'],
            'Z-3_Smith': ['task', 'automation', 'background', 'schedule'],
            'Z-4_Merovingian': ['log', 'monitor', 'alert', 'system', 'debug', 'health'],
        }

        for floor_id, keywords in floor_keywords.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return floor_id

        return None


    def recommend_function(self, task: str, limit: int = 5) -> List[str]:
        """Recommend functions for a task"""
        if not self.smart_floor:
            return []

        task_lower = task.lower()

        # Find functions matching task keywords
        all_funcs = self.smart_floor.discover_functions()

        matches = []
        for func in all_funcs:
            score = 0

            # Check function name
            if any(word in func.name.lower() for word in task_lower.split()):
                score += 3

            # Check category
            if any(word in func.category.lower() for word in task_lower.split()):
                score += 2

            if score > 0:
                matches.append((func.name, score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)

        return [name for name, _ in matches[:limit]]


    def provide_direction(self, context: Optional[Dict] = None) -> str:
        """Provide general direction/guidance"""
        if context and 'last_action' in context:
            last_action = context['last_action']

            if last_action == 'calculation':
                return "Great! Now that you've performed a calculation, " \
                       "you might want to explore related functions. " \
                       "Ask me 'what should I do next' for Neo AI suggestions."

            elif last_action == 'navigation':
                return "You've moved to a new floor. Use 'show me functions on this floor' " \
                       "to see what's available here."

        # General direction
        if self.smart_floor:
            stats = self.smart_floor.get_global_stats()

            if stats['total_executions'] == 0:
                return "Welcome to LightSpeed! Start by:\n" \
                       "  1. Navigate to Z0 (TheConstruct) for physics\n" \
                       "  2. Try a calculation to see Neo AI in action\n" \
                       "  3. Ask me for suggestions as you explore"

            elif stats['total_executions'] < 10:
                return "You're getting started! Keep exploring:\n" \
                       "  • Try functions in different categories\n" \
                       "  • Visit different floors (use WASD + elevators)\n" \
                       "  • Neo AI learns from your usage patterns"

        return "Explore the 8 Z-floors of the LightSpeed tower. " \
               "Each floor has unique functions and capabilities. " \
               "Ask me for help anytime!"


    # ═══════════════════════════════════════════════════════════════════════
    # CONTEXT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════

    def update_context(self, updates: Dict[str, Any]):
        """Update conversation context"""
        if 'current_floor' in updates:
            self.context.current_floor = updates['current_floor']

        if 'last_function' in updates:
            self.context.last_function = updates['last_function']

        if 'active_topic' in updates:
            self.context.active_topic = updates['active_topic']


    def get_context(self) -> ConversationContext:
        """Get current conversation context"""
        return self.context


    def reset_context(self):
        """Reset conversation context"""
        self.context = ConversationContext()
        print("[Achilles] Context reset")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'AchillesAssistant',
    'QueryIntent',
    'Suggestion',
    'ConversationContext'
]
