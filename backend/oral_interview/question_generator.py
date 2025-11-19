"""
Oral Interview Module - Conversational Interview Engine
Handles natural dialogue-based technical interviews with real-time flow
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
import json
import os
import yaml
import re

# Import from shared modules
from shared.models import StructuredCV, WorkExperience
from shared.information_extraction import extract_technologies_from_cv
from shared.llm_setup import get_llm


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class DialogueState(TypedDict):
    """State for conversational interview (simplified from InterviewState)"""
    # Basic state
    complete: bool
    job_description: str
    structured_cv: StructuredCV
    difficulty_score: int  # 1-10 difficulty level

    # Dialogue tracking
    conversation_history: List[Dict[str, Any]]  # All exchanges
    current_turn: int
    interview_start_time: str

    # Context tracking
    matched_technologies: List[str]
    topics_covered: List[str]
    depth_scores: Dict[str, int]  # Track depth per topic

    # Question tracking (NEW)
    asked_question_categories: List[str]  # Track question types asked
    current_section: str  # Current interview section: opening/hr/cv/job/closing

    # Audio tracking
    audio_files: List[str]

    # Interview metadata
    interview_filename: str


# Global prompts storage (will be initialized by load_oral_prompts)
oral_prompts: Optional[Dict] = None


# ============================================================================
# PROMPT LOADING
# ============================================================================

def load_oral_prompts():
    """Load oral interview prompts from YAML file"""
    global oral_prompts
    try:
        # Load system prompts file
        prompts_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config',
            'oral_system_prompts.yaml'
        )
        print(f"📂 Loading prompts from: {prompts_path}")
        print(f"✅ File exists: {os.path.exists(prompts_path)}")

        with open(prompts_path, 'r', encoding='utf-8') as f:
            oral_prompts = yaml.safe_load(f)

        if oral_prompts:
            print(f"✅ Loaded {len(oral_prompts)} prompt templates")
            print(f"📋 Available prompts: {list(oral_prompts.keys())}")
        else:
            print("⚠️  Prompts loaded but dictionary is empty")

        return oral_prompts
    except Exception as e:
        print(f"❌ Error loading oral interview prompts: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_oral_prompt(prompt_key: str) -> str:
    """Get a specific prompt template from loaded prompts"""
    global oral_prompts

    print(f"🔍 get_oral_prompt() called with key: '{prompt_key}'")

    if not oral_prompts:
        print("⚠️  Prompts not loaded, loading now...")
        oral_prompts = load_oral_prompts()

    if not oral_prompts:
        print("❌ ERROR: Failed to load prompts!")
        return ""

    try:
        prompt = oral_prompts.get(prompt_key, "")
        if prompt:
            print(f"✅ Prompt retrieved: {len(prompt)} chars")
        else:
            print(f"❌ ERROR: Prompt key '{prompt_key}' not found in oral_prompts!")
            print(f"Available keys: {list(oral_prompts.keys())}")
        return prompt
    except Exception as e:
        print(f"❌ Error getting prompt template {prompt_key}: {e}")
        return ""


# ============================================================================
# CONTEXT BUILDING FUNCTIONS
# ============================================================================

def build_cv_context(structured_cv: StructuredCV) -> str:
    """Build concise CV context for prompts"""
    context_parts = []

    # Personal info
    if structured_cv.personal_info.name:
        context_parts.append(f"Name: {structured_cv.personal_info.name}")

    # Top experiences (limit to 2 most relevant)
    if structured_cv.experiences:
        context_parts.append("\nKey Experience:")
        for i, exp in enumerate(structured_cv.experiences[:2], 1):
            context_parts.append(
                f"{i}. {exp.position} at {exp.company} ({exp.duration or 'Duration not specified'})"
            )
            if exp.technologies:
                context_parts.append(f"   Technologies: {', '.join(exp.technologies[:5])}")

    # Skills summary
    if structured_cv.skills:
        tech_skills = [s.name for s in structured_cv.skills if s.category.lower() in ['programming', 'tool', 'framework']]
        if tech_skills:
            context_parts.append(f"\nKey Skills: {', '.join(tech_skills[:10])}")

    return "\n".join(context_parts)


def build_conversation_context(state: DialogueState) -> str:
    """Format conversation history for LLM context"""
    if not state["conversation_history"]:
        return "No previous conversation."

    context_parts = []
    for entry in state["conversation_history"][-10:]:  # Last 10 exchanges
        speaker = "Interviewer" if entry["speaker"] == "interviewer" else "Candidate"
        context_parts.append(f"{speaker}: {entry['text']}")

    return "\n".join(context_parts)


def build_qa_pairs_context(state: DialogueState) -> str:
    """
    Format conversation history as explicit Q&A pairs
    Shows previous questions and answers clearly to prevent repetition
    """
    if not state["conversation_history"]:
        return "No previous Q&A pairs."

    # Group into Q&A pairs
    qa_pairs = []
    current_question = None

    for entry in state["conversation_history"]:
        if entry["speaker"] == "interviewer":
            current_question = entry["text"]
        elif entry["speaker"] == "candidate" and current_question:
            qa_pairs.append({
                "question": current_question,
                "answer": entry["text"]
            })
            current_question = None

    if not qa_pairs:
        return "No previous Q&A pairs."

    # Format with clear structure (show all pairs to prevent repetition)
    formatted = []
    for i, qa in enumerate(qa_pairs, 1):
        formatted.append(f"═══ Q&A {i} ═══")
        formatted.append(f"YOUR QUESTION: {qa['question']}")
        formatted.append(f"CANDIDATE'S ANSWER: {qa['answer']}")
        formatted.append("")

    return "\n".join(formatted)


def get_difficulty_description(difficulty_score: int) -> str:
    """Convert difficulty score to description"""
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


def extract_technologies_from_answer(answer: str, cv_technologies: List[str]) -> List[str]:
    """Extract technologies mentioned in answer"""
    # Simple keyword matching against CV technologies
    mentioned_tech = []
    answer_lower = answer.lower()

    for tech in cv_technologies:
        if tech.lower() in answer_lower:
            mentioned_tech.append(tech)

    return mentioned_tech


def extract_key_topics_from_answer(answer: str) -> List[str]:
    """Extract key topics from answer (simple keyword extraction)"""
    # Common technical topics
    topics = [
        'architecture', 'design', 'testing', 'deployment', 'performance',
        'security', 'scalability', 'database', 'api', 'frontend', 'backend',
        'agile', 'team', 'project', 'leadership', 'problem-solving'
    ]

    answer_lower = answer.lower()
    found_topics = [topic for topic in topics if topic in answer_lower]

    return found_topics


# ============================================================================
# QUESTION GENERATION
# ============================================================================

def determine_next_question_type(state: DialogueState) -> tuple[str, str, str]:
    """
    Determine question section and category based on 15-question flow

    Returns: (section, category, prompt_type)

    Flow:
    - Q0: Opening
    - Q1-4: HR Behavioral (4 questions)
    - Q5: Transition to CV
    - Q6-9: CV Experience (4 questions)
    - Q10: Transition to Job
    - Q11-13: Job Description (3 questions)
    - Q14: Closing
    """
    turn = state["current_turn"]

    # Q0: Opening
    if turn == 0:
        return ("opening", "intro", "opening")

    # Q1-4: HR Behavioral section (4 questions)
    elif 1 <= turn <= 4:
        # Define HR categories and select unused ones
        hr_categories = ["teamwork", "problem_solving", "adaptability", "communication",
                        "leadership", "work_style", "conflict_resolution", "learning"]

        used = [cat for cat in state.get("asked_question_categories", []) if cat in hr_categories]
        available = [cat for cat in hr_categories if cat not in used]

        if available:
            category = available[0]  # Pick first available to maintain order
        else:
            category = "motivation"  # Fallback

        return ("hr", category, "hr_behavioral")

    # Q5: Transition from HR to CV
    elif turn == 5:
        return ("transition", "hr_to_cv", "transition")

    # Q6-9: CV Experience section (4 questions)
    elif 6 <= turn <= 9:
        cv_categories = ["role_experience", "projects", "achievements", "challenges",
                        "skills", "impact", "learning_growth"]

        used = [cat for cat in state.get("asked_question_categories", []) if cat in cv_categories]
        available = [cat for cat in cv_categories if cat not in used]

        if available:
            category = available[0]
        else:
            category = "experience"  # Fallback

        return ("cv", category, "cv_experience")

    # Q10: Transition from CV to Job Description
    elif turn == 10:
        return ("transition", "cv_to_job", "transition")

    # Q11-13: Job Description section (3 questions)
    elif 11 <= turn <= 13:
        job_categories = ["role_requirements", "culture_fit", "motivation", "expectations"]

        used = [cat for cat in state.get("asked_question_categories", []) if cat in job_categories]
        available = [cat for cat in job_categories if cat not in used]

        if available:
            category = available[0]
        else:
            category = "role_fit"  # Fallback

        return ("job", category, "job_description")

    # Q14: Closing
    elif turn >= 14:
        return ("closing", "wrap_up", "closing")

    # Fallback (should not reach here)
    return ("hr", "general", "hr_behavioral")


def generate_transition_question(state: DialogueState, from_section: str, to_section: str) -> str:
    """
    Generate smooth transitional question between interview sections
    """
    # Get LLM instance
    llm = get_llm()

    # Build context
    cv_context = build_cv_context(state["structured_cv"])
    qa_history = build_qa_pairs_context(state)

    # Get transition prompt template
    prompt_template = get_oral_prompt("transition_prompt")

    if not prompt_template:
        # Fallback transitions
        if to_section == "cv":
            return "Great! Now I'd like to learn more about your work experience. Tell me about your role at your most recent position."
        elif to_section == "job":
            return "Thank you for sharing that. Now let's talk about this specific role. What interests you most about this position?"
        else:
            return "Let's move on to the next topic."

    try:
        # Map section names to readable labels
        section_labels = {
            "hr": "behavioral and soft skills",
            "cv": "your work experience and projects",
            "job": "this specific role and fit"
        }

        formatted_prompt = prompt_template.format(
            from_section=section_labels.get(from_section, from_section),
            to_section=section_labels.get(to_section, to_section),
            qa_history=qa_history,
            cv_context=cv_context
        )

        response = llm.invoke(formatted_prompt)
        return clean_generated_question(response.content)

    except Exception as e:
        print(f"❌ Error generating transition: {e}")
        # Fallback
        if to_section == "cv":
            return "Now I'd like to learn more about your work experience. Tell me about your most recent role."
        elif to_section == "job":
            return "Let's talk about this specific position. What interests you about this role?"
        return "Let's continue."


def generate_dialogue_question(state: DialogueState) -> str:
    """
    Generate next question using section-based prompts and explicit Q&A history
    """
    print("=" * 60)
    print("🔍 DEBUG: generate_dialogue_question() called")

    # Get LLM instance
    llm = get_llm()

    # Determine question section and category
    section, category, prompt_type = determine_next_question_type(state)
    print(f"📌 Section: {section}, Category: {category}, Prompt: {prompt_type}")

    # Update current section in state
    state["current_section"] = section

    # Build contexts
    cv_context = build_cv_context(state["structured_cv"])
    qa_history = build_qa_pairs_context(state)
    topics_covered = ", ".join(state["topics_covered"]) if state["topics_covered"] else "None yet"

    print(f"📄 CV context: {len(cv_context)} chars")
    print(f"💬 Q&A pairs: {qa_history.count('═══')} pairs")

    # Handle opening question (hardcoded)
    if prompt_type == "opening":
        print("📝 Using opening question")
        question = "Hello! Thank you for joining us today. To start, could you please introduce yourself and tell me a bit about your background?"
        return question

    # Handle transitions
    if prompt_type == "transition":
        print(f"🔄 Generating transition: {category}")
        if category == "hr_to_cv":
            from_section = "hr"
            to_section = "cv"
        elif category == "cv_to_job":
            from_section = "cv"
            to_section = "job"
        else:
            from_section = "general"
            to_section = "general"

        question = generate_transition_question(state, from_section, to_section)
        return question

    # Handle closing question (hardcoded, simple)
    if prompt_type == "closing":
        print("🎬 Using closing question")
        question = "Do you have any questions for us?"
        return question

    # Handle section-based questions (HR, CV, Job)
    print(f"📝 Using {prompt_type}_prompt")
    prompt_template = get_oral_prompt(f"{prompt_type}_prompt")

    if not prompt_template:
        print(f"❌ ERROR: Prompt '{prompt_type}_prompt' not found!")
        return "Can you tell me more about that?"

    try:
        # Format prompt based on type
        if prompt_type == "hr_behavioral":
            formatted_prompt = prompt_template.format(
                qa_history=qa_history,
                topics_covered=topics_covered,
                cv_context=cv_context,
                category=category
            )
        elif prompt_type == "cv_experience":
            formatted_prompt = prompt_template.format(
                qa_history=qa_history,
                topics_covered=topics_covered,
                cv_context=cv_context,
                category=category
            )
        elif prompt_type == "job_description":
            formatted_prompt = prompt_template.format(
                qa_history=qa_history,
                job_description=state["job_description"],
                cv_context=cv_context,
                category=category
            )
        else:
            # Fallback
            formatted_prompt = prompt_template.format(
                qa_history=qa_history,
                cv_context=cv_context,
                category=category
            )

        print(f"✅ Formatted prompt: {len(formatted_prompt)} chars")

        # Generate question using LLM
        print("🤖 Calling LLM...")
        response = llm.invoke(formatted_prompt)
        print(f"✅ LLM response: {len(response.content)} chars")

        question = clean_generated_question(response.content)
        print(f"✨ Generated question: {question}")

        # Track category as used
        if category not in state.get("asked_question_categories", []):
            state["asked_question_categories"].append(category)
            print(f"✅ Marked '{category}' as used")

        print("=" * 60)
        return question

    except Exception as e:
        print(f"❌ ERROR generating question: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return "Can you tell me more about your experience?"


def clean_generated_question(raw_text: str) -> str:
    """Clean up LLM-generated question text"""
    # Remove markdown formatting
    text = re.sub(r'\*\*', '', raw_text)
    text = re.sub(r'^\s*[-*]\s*', '', text, flags=re.MULTILINE)

    # Remove "Question:" prefix if present
    text = re.sub(r'^(?:Question|Interviewer):\s*', '', text, flags=re.IGNORECASE)

    # Remove quotes
    text = text.strip('"\'')

    # Clean whitespace
    text = ' '.join(text.split())

    return text.strip()


# ============================================================================
# CONVERSATION FLOW
# ============================================================================

def decide_interview_continuation(state: DialogueState) -> bool:
    """
    Decide if interview should continue or end
    Fixed 15-question structure: Always ends at turn 15
    """
    # Interview ends after 15 questions (turns 0-14)
    # Turn 14 is the closing question
    return state["current_turn"] < 15


def process_dialogue_turn(state: DialogueState, candidate_response: str) -> Dict[str, Any]:
    """
    Process one turn of conversation:
    1. Save candidate response
    2. Analyze response for topics/tech
    3. Special handling for Q14 (closing) response
    4. Increment turn counter
    5. Decide if continue or end
    6. Generate next question
    """
    # Save response to history
    state["conversation_history"].append({
        "speaker": "candidate",
        "text": candidate_response,
        "timestamp": datetime.now().isoformat(),
        "turn": state["current_turn"]
    })

    # Special handling: If responding to Q14 (closing question), end with standard message
    if state["current_turn"] == 14:
        print("🎬 Candidate responded to closing question - ending interview")
        return {
            "complete": True,
            "message": "You'll hear from us in two weeks. Thank you!"
        }

    # Analyze response
    cv_technologies = extract_technologies_from_cv(state["structured_cv"])
    extracted_tech = extract_technologies_from_answer(candidate_response, cv_technologies)
    topics = extract_key_topics_from_answer(candidate_response)

    # Update state
    state["topics_covered"].extend(topics)
    state["topics_covered"] = list(set(state["topics_covered"]))  # Remove duplicates

    # Track depth per topic
    for topic in topics:
        state["depth_scores"][topic] = state["depth_scores"].get(topic, 0) + 1

    # Increment turn BEFORE generating next question (FIX for duplicate opening)
    state["current_turn"] += 1

    # Decide if interview should continue
    should_continue = decide_interview_continuation(state)

    if not should_continue:
        return {
            "complete": True,
            "message": "Thank you for your time! That was a great conversation. Your interview responses have been saved."
        }

    # Generate next question (with incremented turn)
    next_question = generate_dialogue_question(state)

    # Save question to history
    state["conversation_history"].append({
        "speaker": "interviewer",
        "text": next_question,
        "timestamp": datetime.now().isoformat(),
        "turn": state["current_turn"]
    })

    return {
        "complete": False,
        "question": next_question,
        "turn": state["current_turn"]
    }


# ============================================================================
# CONVERSATION SAVING
# ============================================================================

def save_oral_interview(state: DialogueState, interviews_folder: str) -> str:
    """Save conversation with audio file references"""
    filepath = os.path.join(interviews_folder, state['interview_filename'])

    # Associate audio files with candidate responses
    conversation = state['conversation_history']
    audio_index = 0

    for entry in conversation:
        if entry['speaker'] == 'candidate':
            if audio_index < len(state['audio_files']):
                entry['audio_file'] = state['audio_files'][audio_index]
                audio_index += 1
            else:
                entry['audio_file'] = None
        else:
            entry['audio_file'] = None

    # Calculate duration
    start_time = datetime.fromisoformat(state['interview_start_time'])
    duration_minutes = round((datetime.now() - start_time).total_seconds() / 60, 1)

    output = {
        "metadata": {
            "candidate_name": state['structured_cv'].personal_info.name or "Unknown",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "duration_minutes": duration_minutes,
            "total_turns": state['current_turn'],
            "difficulty_score": state['difficulty_score'],
            "topics_covered": state['topics_covered'],
            "job_description": state['job_description'][:200] + "..." if len(state['job_description']) > 200 else state['job_description']
        },
        "conversation": conversation
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath
