"""
Text Interview - Utility Functions

Pure utility functions for text interview module:
- Difficulty level mapping
- Text analysis and extraction
- Question cleaning
- Response formatting

No dependencies on Flask or global state.
"""

import re
from typing import List, Dict, Any

# Import from shared module
from shared.models import InterviewQuestion


def get_difficulty_description(difficulty_score: int) -> str:
    """Get difficulty description from score"""
    if difficulty_score <= 2:
        return "entry-level/junior"
    elif difficulty_score <= 4:
        return "junior to mid-level"
    elif difficulty_score <= 6:
        return "mid-level"
    elif difficulty_score <= 8:
        return "senior-level"
    else:
        return "expert/principal-level"


def extract_metrics_from_responsibilities(responsibilities: List[str]) -> List[str]:
    """Extract quantitative metrics and achievements from responsibilities"""
    metrics = []
    metric_patterns = [
        r'(\d+)%',  # Percentages
        r'(\d+(?:,\d+)*)\s*(?:users|customers|clients)',  # User counts
        r'(\d+(?:\.\d+)?)\s*(?:million|k|thousand)',  # Scale indicators
        r'(\d+(?:,\d+)*)\s*(?:requests|transactions|records)',  # Volume metrics
        r'reduced.*?by\s*(\d+%|\d+\s*(?:seconds|minutes|hours))',  # Performance improvements
        r'increased.*?by\s*(\d+%|\d+\s*(?:fold|times))',  # Growth metrics
        r'(\d+)\s*(?:fold|times)\s*(?:improvement|increase)',  # Multiplier improvements
    ]

    for responsibility in responsibilities:
        for pattern in metric_patterns:
            matches = re.findall(pattern, responsibility, re.IGNORECASE)
            for match in matches:
                if match not in metrics:
                    metrics.append(match)

    return metrics


def extract_technologies_from_answer(answer: str, experience_technologies: List[str] = None) -> List[str]:
    """Extract technologies mentioned in candidate's answer with enhanced detection"""
    if experience_technologies is None:
        experience_technologies = []

    mentioned_techs = []
    answer_lower = answer.lower()

    # Check for experience technologies mentioned in answer
    for tech in experience_technologies:
        if tech.lower() in answer_lower:
            mentioned_techs.append(tech)

    # Enhanced technology patterns for better detection
    tech_patterns = {
        # Programming Languages
        'languages': [
            r'\b(python|java|javascript|typescript|go|rust|c\+\+|c#|kotlin|swift|scala|r)\b',
            r'\b(php|ruby|perl|julia|haskell|elixir|erlang)\b'
        ],

        # Frameworks and Libraries
        'frameworks': [
            r'\b(react|angular|vue|svelte|next\.?js|nuxt|gatsby)\b',
            r'\b(flask|django|fastapi|spring|rails|express|koa)\b',
            r'\b(tensorflow|pytorch|scikit-learn|keras|pandas|numpy)\b',
            r'\b(langchain|langgraph|openai|anthropic|hugging face)\b'
        ],

        # Tools and Platforms
        'tools': [
            r'\b(docker|kubernetes|k8s|git|jenkins|terraform)\b',
            r'\b(aws|azure|gcp|google cloud)\b',
            r'\b(mongodb|postgresql|mysql|redis|elasticsearch)\b',
            r'\b(jupyter|notebook|vscode|pycharm)\b'
        ],

        # Concepts and Methods
        'concepts': [
            r'\b(machine learning|ml|ai|artificial intelligence|deep learning|dl)\b',
            r'\b(nlp|natural language processing|computer vision|cv)\b',
            r'\b(api|rest|graphql|microservices|devops|ci/cd)\b',
            r'\b(agile|scrum|tdd|bdd|testing|debugging)\b'
        ]
    }

    # Extract technologies using patterns
    for category, patterns in tech_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, answer_lower)
            for match in matches:
                # Normalize the match
                normalized_tech = match.strip()
                if normalized_tech and normalized_tech not in [t.lower() for t in mentioned_techs]:
                    mentioned_techs.append(normalized_tech.title() if len(normalized_tech) > 3 else normalized_tech.upper())

    return list(set(mentioned_techs))  # Remove duplicates


def extract_key_topics_from_answer(answer: str) -> List[str]:
    """Extract key topics and themes from candidate's answer"""
    answer_lower = answer.lower()
    topics = []

    # Common project/work topics
    topic_patterns = {
        'challenges': r'\b(challenge|problem|issue|difficulty|obstacle|bug|error)\w*\b',
        'solutions': r'\b(solution|solve|fix|resolve|implement|approach|method)\w*\b',
        'improvements': r'\b(improve|optimize|enhance|better|efficient|performance|scale)\w*\b',
        'collaboration': r'\b(team|collaborate|work together|pair|review|meeting)\w*\b',
        'learning': r'\b(learn|study|research|understand|discover|explore)\w*\b',
        'architecture': r'\b(architecture|design|structure|pattern|framework|system)\w*\b',
        'data': r'\b(data|database|analysis|pipeline|processing|model)\w*\b',
        'testing': r'\b(test|testing|debug|quality|validation|verification)\w*\b',
        'deployment': r'\b(deploy|production|release|ci|cd|pipeline|build)\w*\b',
        'metrics': r'\b(\d+%|\d+\s*times|improved|increased|reduced|faster|slower)\b'
    }

    for topic_name, pattern in topic_patterns.items():
        if re.search(pattern, answer_lower):
            topics.append(topic_name)

    # Extract specific metrics or quantifiable results
    metrics_patterns = [
        r'(\d+)%\s*(improvement|increase|decrease|faster|slower)',
        r'(\d+)\s*times (faster|slower|better|more efficient)',
        r'reduced.*?by\s*(\d+%|\d+\s*(?:seconds|minutes|hours|days))',
        r'increased.*?by\s*(\d+%|\d+\s*(?:fold|times|users|requests))'
    ]

    for pattern in metrics_patterns:
        matches = re.findall(pattern, answer_lower)
        if matches:
            topics.append('quantifiable_results')
            break

    return topics


def clean_generated_question(raw_question: str) -> str:
    """Clean up generated question text"""
    question = raw_question.strip()

    # Remove common prefixes
    prefixes_to_remove = [
        "here's a potential question:",
        "question:",
        "here's the question:",
        "here's a suitable question:"
    ]

    for prefix in prefixes_to_remove:
        if question.lower().startswith(prefix):
            question = question[len(prefix):].strip()

    # Remove quotes if wrapped
    if question.startswith('"') and question.endswith('"'):
        question = question[1:-1]

    return question


def prepare_question_response(question: InterviewQuestion, phase: str, question_count: int) -> dict:
    """Prepare the response data for different question types"""
    base_response = {
        'question_id': question.question_id,
        'question_type': question.question_type,
        'phase': phase,
        'question_count': question_count,
        'difficulty_level': question.difficulty_level,
        'complete': False
    }

    if question.question_type == "open":
        base_response.update({
            'question': question.question_text,
            'technology_focus': question.technology_focus
        })

    elif question.question_type == "qcm":
        if question.qcm_data:
            base_response.update({
                'question': question.qcm_data.question,
                'options': [{'option': opt.option, 'text': opt.text} for opt in question.qcm_data.options],
                'technology_focus': question.qcm_data.technology_focus,
                'is_multiple_choice': question.qcm_data.is_multiple_choice
            })
        else:
            base_response['question'] = question.question_text
            base_response['is_multiple_choice'] = False

    return base_response
