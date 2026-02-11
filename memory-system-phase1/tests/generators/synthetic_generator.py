"""
Synthetic Conversation Generator

Generates realistic test conversations with known ground truth
for evaluating memory extraction and retrieval quality.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.evaluation.evaluator import GroundTruth, TestCase
from .ground_truth import GroundTruthBuilder


class ConversationStyle(Enum):
    """Conversation styles for generation"""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    SUPPORT = "customer_support"


@dataclass
class ConversationTemplate:
    """Template for generating conversations"""
    style: ConversationStyle
    
    # Name variations
    names: List[str] = field(default_factory=lambda: [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey",
        "Sam", "Chris", "Jamie", "Riley", "Quinn"
    ])
    
    # Location variations
    locations: List[str] = field(default_factory=lambda: [
        "New York", "San Francisco", "London", "Tokyo", "Sydney",
        "Berlin", "Toronto", "Singapore", "Paris", "Seattle"
    ])
    
    # Language preferences
    languages: List[str] = field(default_factory=lambda: [
        "Python", "JavaScript", "TypeScript", "Go", "Rust",
        "Java", "C++", "Ruby", "Swift", "Kotlin"
    ])
    
    # Time preferences
    time_prefs: List[str] = field(default_factory=lambda: [
        "morning", "afternoon", "evening", "late night",
        "early morning", "after lunch"
    ])
    
    # Communication preferences
    comm_prefs: List[str] = field(default_factory=lambda: [
        "email", "Slack", "phone calls", "video calls",
        "text messages", "async messages"
    ])


class SyntheticGenerator:
    """
    Generates synthetic test conversations with ground truth.
    
    Creates realistic conversations containing:
    - Personal information (name, location, etc.)
    - Preferences (languages, tools, times)
    - Instructions (always do X, never do Y)
    - Constraints (hard rules)
    - Entities (people, projects, companies)
    """
    
    def __init__(self, template: ConversationTemplate = None, seed: int = None):
        """
        Initialize generator.
        
        Args:
            template: Conversation template with variations
            seed: Random seed for reproducibility
        """
        self.template = template or ConversationTemplate(style=ConversationStyle.CASUAL)
        if seed is not None:
            random.seed(seed)
        
        # Message templates by type
        self._preference_templates = [
            ("I prefer {value} for {context}.", "preference", "{context}"),
            ("I'd like to use {value}.", "preference", "tool"),
            ("My favorite is {value}.", "preference", "favorite"),
            ("{value} is my go-to choice.", "preference", "default"),
            ("I always choose {value}.", "preference", "default"),
            ("I really like {value}.", "preference", "like"),
        ]
        
        self._constraint_templates = [
            ("Never {action}.", "constraint", "never"),
            ("Don't ever {action}.", "constraint", "never"),
            ("I absolutely need {requirement}.", "constraint", "requirement"),
            ("It's critical that {requirement}.", "constraint", "critical"),
            ("You must always {action}.", "constraint", "must"),
        ]
        
        self._instruction_templates = [
            ("Always {action} when {context}.", "instruction", "always"),
            ("Make sure to {action}.", "instruction", "always"),
            ("Remember to {action}.", "instruction", "always"),
            ("Please {action} every time.", "instruction", "always"),
        ]
        
        self._entity_templates = [
            ("My name is {name}.", "entity", "user_name"),
            ("I'm {name}.", "entity", "user_name"),
            ("I work at {company}.", "entity", "company"),
            ("My manager is {manager}.", "entity", "manager"),
            ("I'm working on {project}.", "entity", "project"),
            ("I live in {location}.", "entity", "location"),
        ]
        
        self._empty_messages = [
            "Hi",
            "Hello",
            "Thanks",
            "Thank you",
            "Okay",
            "Got it",
            "Sure",
            "Sounds good",
            "Perfect",
            "Great",
            "Alright",
            "Yes",
            "No",
            "Maybe",
            "I see",
        ]
    
    def generate_preference_message(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a preference message with ground truth"""
        template, mem_type, key = random.choice(self._preference_templates)
        
        # Random preference value
        value = random.choice([
            random.choice(self.template.languages),
            random.choice(self.template.time_prefs),
            random.choice(self.template.comm_prefs),
        ])
        
        context = random.choice([
            "work", "coding", "communication", "meetings",
            "development", "collaboration", "daily tasks"
        ])
        
        message = template.format(value=value, context=context)
        
        expected = {
            'type': mem_type,
            'key': key if key != "{context}" else context,
            'value': value,
            'confidence': 0.8,
        }
        
        return message, expected
    
    def generate_constraint_message(self) -> Tuple[str, Dict[str, Any]]:
        """Generate a constraint message with ground truth"""
        template, mem_type, key = random.choice(self._constraint_templates)
        
        actions = [
            "call me before 9 AM",
            "schedule meetings on Fridays",
            "use deprecated APIs",
            "push directly to main",
            "skip code review",
            "send messages after 6 PM",
        ]
        
        requirements = [
            "code review before merging",
            "tests pass before deployment",
            "documentation for new features",
            "approval before major changes",
        ]
        
        if "{action}" in template:
            action = random.choice(actions)
            message = template.format(action=action)
            value = action
        else:
            requirement = random.choice(requirements)
            message = template.format(requirement=requirement)
            value = requirement
        
        expected = {
            'type': mem_type,
            'key': key,
            'value': value,
            'confidence': 0.9,
        }
        
        return message, expected
    
    def generate_instruction_message(self) -> Tuple[str, Dict[str, Any]]:
        """Generate an instruction message with ground truth"""
        template, mem_type, key = random.choice(self._instruction_templates)
        
        actions = [
            "check for typos",
            "run tests",
            "update the documentation",
            "notify the team",
            "create a backup",
            "log the changes",
            "validate the input",
        ]
        
        contexts = [
            "I make changes",
            "deploying",
            "starting a meeting",
            "finishing a task",
            "reviewing code",
        ]
        
        action = random.choice(actions)
        context = random.choice(contexts)
        
        message = template.format(action=action, context=context)
        
        expected = {
            'type': mem_type,
            'key': key,
            'value': action,
            'confidence': 0.85,
        }
        
        return message, expected
    
    def generate_entity_message(self) -> Tuple[str, Dict[str, Any]]:
        """Generate an entity message with ground truth"""
        template, mem_type, key = random.choice(self._entity_templates)
        
        name = random.choice(self.template.names)
        company = random.choice(["TechCorp", "DataSystems", "CloudBiz", "AI Labs", "DevPro"])
        manager = random.choice(self.template.names)
        project = random.choice(["Project Alpha", "Platform Upgrade", "Mobile App", "API Gateway"])
        location = random.choice(self.template.locations)
        
        message = template.format(
            name=name,
            company=company,
            manager=manager,
            project=project,
            location=location,
        )
        
        # Determine actual value based on key
        value_map = {
            'user_name': name,
            'company': company,
            'manager': manager,
            'project': project,
            'location': location,
        }
        
        expected = {
            'type': mem_type,
            'key': key,
            'value': value_map.get(key, name),
            'confidence': 0.85,
        }
        
        return message, expected
    
    def generate_empty_message(self) -> str:
        """Generate a message that shouldn't produce memories"""
        return random.choice(self._empty_messages)
    
    def generate_conversation(
        self,
        num_info_turns: int = 10,
        num_empty_turns: int = 5,
        include_queries: bool = True,
        name: str = "synthetic_test",
    ) -> TestCase:
        """
        Generate a complete test conversation.
        
        Args:
            num_info_turns: Number of turns with information to extract
            num_empty_turns: Number of empty/filler turns
            include_queries: Whether to add query turns at the end
            name: Test case name
            
        Returns:
            TestCase with conversation and ground truth
        """
        builder = GroundTruthBuilder(name, "Synthetically generated test conversation")
        builder.add_tag("synthetic")
        builder.add_tag(self.template.style.value)
        
        # Generate info turns
        generators = [
            self.generate_preference_message,
            self.generate_constraint_message,
            self.generate_instruction_message,
            self.generate_entity_message,
        ]
        
        # Track generated info for queries
        generated_info = []
        
        for i in range(num_info_turns):
            gen = random.choice(generators)
            message, expected = gen()
            builder.add_turn(message, expected_memories=[expected])
            generated_info.append((message, expected))
        
        # Add empty turns interspersed
        for _ in range(num_empty_turns):
            message = self.generate_empty_message()
            builder.add_empty_turn(message)
        
        # Add query turns
        if include_queries and generated_info:
            # Query for preferences
            builder.add_turn(
                "What are my preferences?",
                expected_memories=[],
                tags=['query'],
            )
            
            # Query for constraints
            builder.add_turn(
                "What are my rules and constraints?",
                expected_memories=[],
                tags=['query'],
            )
        
        return builder.build()
    
    def generate_edge_case_tests(self) -> List[TestCase]:
        """Generate test cases for edge cases"""
        tests = []
        
        # Test: Contradictory information
        builder = GroundTruthBuilder("contradiction_test", "Test handling contradictions")
        builder.add_tag("edge_case")
        builder.add_info_turn(
            "I prefer Python for coding.",
            "preference", "coding", "Python", 0.8, "pref_1"
        )
        builder.add_info_turn(
            "Actually, I prefer JavaScript now.",
            "preference", "coding", "JavaScript", 0.85, "pref_2"
        )
        tests.append(builder.build())
        
        # Test: Very long message
        builder = GroundTruthBuilder("long_message_test", "Test long messages")
        builder.add_tag("edge_case")
        long_message = (
            "Let me tell you about my setup. I work at TechCorp as a senior engineer. "
            "My manager is Sarah. I prefer Python for data analysis, but JavaScript for frontend. "
            "Always run tests before committing. Never push to main directly. "
            "My timezone is PST. I like morning standups but hate long meetings."
        )
        builder.add_turn(
            long_message,
            expected_memories=[
                {'type': 'entity', 'key': 'company', 'value': 'TechCorp'},
                {'type': 'entity', 'key': 'manager', 'value': 'Sarah'},
                {'type': 'preference', 'key': 'data analysis', 'value': 'Python'},
                {'type': 'instruction', 'key': 'always', 'value': 'run tests before committing'},
                {'type': 'constraint', 'key': 'never', 'value': 'push to main directly'},
            ],
        )
        tests.append(builder.build())
        
        # Test: Ambiguous language
        builder = GroundTruthBuilder("ambiguous_test", "Test ambiguous statements")
        builder.add_tag("edge_case")
        builder.add_turn(
            "I kind of like Python, I guess.",
            expected_memories=[
                {'type': 'preference', 'key': 'language', 'value': 'Python', 'confidence': 0.6},
            ],
        )
        builder.add_turn(
            "Maybe call me in the morning?",
            expected_memories=[],  # Too uncertain
        )
        tests.append(builder.build())
        
        # Test: Negations
        builder = GroundTruthBuilder("negation_test", "Test negative statements")
        builder.add_tag("edge_case")
        builder.add_turn(
            "I don't like Java.",
            expected_memories=[
                {'type': 'preference', 'key': 'dislike', 'value': 'Java'},
            ],
        )
        builder.add_turn(
            "Don't call me on weekends.",
            expected_memories=[
                {'type': 'constraint', 'key': 'never', 'value': 'call on weekends'},
            ],
        )
        tests.append(builder.build())
        
        return tests
    
    def generate_benchmark_suite(self, num_conversations: int = 5) -> List[TestCase]:
        """
        Generate a benchmark test suite.
        
        Args:
            num_conversations: Number of conversations to generate
            
        Returns:
            List of test cases
        """
        tests = []
        
        # Vary conversation styles
        styles = list(ConversationStyle)
        
        for i in range(num_conversations):
            style = styles[i % len(styles)]
            template = ConversationTemplate(style=style)
            generator = SyntheticGenerator(template=template, seed=42 + i)
            
            test = generator.generate_conversation(
                num_info_turns=random.randint(5, 15),
                num_empty_turns=random.randint(2, 5),
                include_queries=True,
                name=f"benchmark_{style.value}_{i+1}",
            )
            tests.append(test)
        
        # Add edge case tests
        tests.extend(self.generate_edge_case_tests())
        
        return tests


def generate_test_suite(
    num_standard: int = 5,
    include_edge_cases: bool = True,
    seed: int = 42,
) -> List[TestCase]:
    """
    Convenience function to generate a complete test suite.
    
    Args:
        num_standard: Number of standard conversations
        include_edge_cases: Include edge case tests
        seed: Random seed
        
    Returns:
        List of test cases
    """
    generator = SyntheticGenerator(seed=seed)
    tests = generator.generate_benchmark_suite(num_standard)
    
    if include_edge_cases:
        tests.extend(generator.generate_edge_case_tests())
    
    return tests
