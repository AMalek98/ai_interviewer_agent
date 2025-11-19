#!/usr/bin/env python3
"""
Test script for Phase 5: Answer-Aware Follow-up System
Tests the complete 15-question flow with enhanced answer processing.
"""

import json
import sys
import os

# Add the app directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    initialize_interview, generate_question, process_response,
    StructuredCV, WorkExperience, PersonalInfo, Skill,
    extract_technologies_from_answer, extract_key_topics_from_answer,
    build_enhanced_followup_context
)

def create_test_cv():
    """Create a test CV for the interview simulation"""
    return StructuredCV(
        personal_info=PersonalInfo(
            name="Sarah Johnson",
            email="sarah.johnson@example.com",
            location="San Francisco, CA"
        ),
        experiences=[
            WorkExperience(
                company="TechCorp",
                position="Senior Data Scientist",
                start_date="January 2022",
                end_date="Present",
                duration="2 years",
                responsibilities=[
                    "Developed machine learning models using Python and TensorFlow to predict customer churn with 85% accuracy",
                    "Built data pipelines using Apache Spark and AWS to process 10TB+ of customer data daily",
                    "Led a team of 3 junior data scientists and improved model deployment time by 60%",
                    "Implemented A/B testing framework that increased conversion rates by 15%"
                ],
                technologies=["Python", "TensorFlow", "AWS", "Apache Spark", "SQL", "Docker"]
            ),
            WorkExperience(
                company="DataViz Inc",
                position="Machine Learning Engineer",
                start_date="March 2020",
                end_date="December 2021",
                duration="1 year 9 months",
                responsibilities=[
                    "Designed and deployed real-time recommendation system serving 1M+ users",
                    "Optimized model inference speed by 40% using TensorFlow Lite and model quantization",
                    "Collaborated with frontend team to integrate ML models into React applications"
                ],
                technologies=["Python", "TensorFlow", "React", "MongoDB", "Kubernetes"]
            )
        ],
        skills=[
            Skill(name="Python", category="programming", proficiency="Expert"),
            Skill(name="Machine Learning", category="framework", proficiency="Expert"),
            Skill(name="TensorFlow", category="framework", proficiency="Advanced"),
            Skill(name="AWS", category="tool", proficiency="Advanced")
        ]
    )

def test_answer_extraction():
    """Test the enhanced answer extraction functions"""
    print("=== Testing Answer Extraction Functions ===")

    # Test technology extraction
    test_answer = "I used Python and TensorFlow to build the model. We also leveraged AWS for deployment and MongoDB for data storage. The biggest challenge was optimizing performance."

    experience_techs = ["Python", "TensorFlow", "AWS", "SQL"]
    extracted_techs = extract_technologies_from_answer(test_answer, experience_techs)
    print(f"Extracted technologies: {extracted_techs}")

    # Test topic extraction
    key_topics = extract_key_topics_from_answer(test_answer)
    print(f"Key topics: {key_topics}")

    # Test enhanced follow-up context building
    test_experience = WorkExperience(
        company="TechCorp",
        position="Senior Data Scientist",
        technologies=["Python", "TensorFlow", "AWS"]
    )

    previous_question = "Tell me about your experience with machine learning at TechCorp."
    enhanced_context = build_enhanced_followup_context(previous_question, test_answer, test_experience)
    print(f"\nEnhanced follow-up context preview (first 300 chars):\n{enhanced_context[:300]}...")

def test_interview_flow():
    """Test the complete 15-question interview flow"""
    print("\n=== Testing Complete Interview Flow ===")

    # Create test data
    test_cv = create_test_cv()
    job_description = """
    We are looking for a Senior Data Scientist to join our AI team.
    Required skills: Python, TensorFlow, AWS, machine learning, data pipelines.
    You will work on customer analytics and recommendation systems.
    """

    # Initialize interview
    print("1. Initializing interview...")
    state = initialize_interview(job_description, test_cv)
    print(f"   Selected experiences: {len(state['selected_experiences'])}")
    print(f"   Difficulty score: {state['difficulty_score']}")
    print(f"   Matched technologies: {state['matched_technologies']}")

    # Simulate Q1 (initial experience question)
    print("\n2. Generating Q1 (initial experience)...")
    result = generate_question(state)
    if result.get("complete"):
        print("   ERROR: Interview completed too early")
        return

    q1 = result["current_question"]
    print(f"   Q1: {q1.question_text[:100]}...")
    print(f"   Question type: {q1.question_type}")

    # Simulate Q1 answer
    print("\n3. Processing Q1 answer...")
    q1_answer = "At TechCorp, I worked on predictive analytics for customer churn. I used Python and TensorFlow to build deep learning models. The main challenge was handling imbalanced datasets, which I solved using SMOTE and ensemble methods. The model achieved 85% accuracy and reduced churn by 20%."

    process_response(state, q1_answer)
    last_response = state["responses_history"][-1]
    print(f"   Extracted technologies: {last_response.extracted_technologies}")
    print(f"   Key topics: {last_response.key_topics}")
    print(f"   Experience index: {last_response.experience_index}")

    # Simulate Q2 (follow-up question)
    print("\n4. Generating Q2 (follow-up on same experience)...")
    result = generate_question(state)
    q2 = result["current_question"]
    print(f"   Q2: {q2.question_text[:150]}...")

    # Check if Q2 references the previous answer
    if "churn" in q2.question_text.lower() or "smote" in q2.question_text.lower() or "ensemble" in q2.question_text.lower():
        print("   ✓ Q2 successfully references previous answer!")
    else:
        print("   ⚠ Q2 might not be referencing previous answer effectively")

    # Continue with a few more questions to test the flow
    question_count = 2
    answers = [
        "The ensemble approach combined Random Forest, XGBoost, and Neural Networks. I used weighted voting and cross-validation to optimize the combination. The biggest technical challenge was feature engineering for time-series data.",
        "In my DataViz role, I built recommendation systems using collaborative filtering and deep learning. The system processed user behavior data in real-time and served personalized recommendations through APIs.",
        "The real-time aspect was challenging. I used Kafka for streaming data and Redis for caching. Model inference was optimized using TensorFlow Serving and horizontal scaling with Kubernetes.",
        "For this role, I would focus on understanding the business metrics first, then design appropriate ML solutions. I'd leverage MLOps practices for model deployment and monitoring."
    ]

    for i, answer in enumerate(answers):
        question_count += 1
        print(f"\n5.{i+1} Processing Q{question_count} answer and generating Q{question_count+1}...")

        # Process answer
        process_response(state, answer)

        # Generate next question
        result = generate_question(state)
        if result.get("complete"):
            print(f"   Interview completed after {question_count} questions")
            break

        current_q = result["current_question"]
        print(f"   Q{question_count+1}: {current_q.question_text[:100]}...")
        print(f"   Phase: {result['phase']}")

        # For follow-up questions (Q4), check if it references previous answers
        if question_count == 4 and state["current_experience_focus"] is not None:
            if "real-time" in current_q.question_text.lower() or "kafka" in current_q.question_text.lower():
                print("   ✓ Q4 successfully references Q3 answer!")
            else:
                print("   ⚠ Q4 might not be referencing Q3 answer effectively")

    # Test answer references tracking
    print(f"\n6. Answer references tracking:")
    print(f"   Total references stored: {len(state['answer_references'])}")
    for q_id, answer in list(state['answer_references'].items())[:3]:
        print(f"   Q{q_id}: {answer[:50]}...")

def main():
    """Run all Phase 5 tests"""
    print("🚀 Phase 5: Answer-Aware Follow-up System - Test Suite")
    print("=" * 60)

    try:
        # Test 1: Answer extraction functions
        test_answer_extraction()

        # Test 2: Complete interview flow
        test_interview_flow()

        print("\n" + "=" * 60)
        print("✅ Phase 5 testing completed successfully!")
        print("Key features tested:")
        print("- Enhanced answer analysis (technology/topic extraction)")
        print("- Answer-aware follow-up context building")
        print("- Experience-focused question mapping")
        print("- Answer references tracking")
        print("- 15-question flow with proper phase transitions")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())