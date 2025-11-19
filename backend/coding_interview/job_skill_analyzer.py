"""
Job Skill Analyzer - Extracts and ranks skills from job descriptions
Uses LLM to create structured analysis of skill importance for coding interviews
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import json
import os


class SkillImportance(BaseModel):
    """Represents a single skill with its importance ranking"""
    skill_name: str = Field(description="Name of the skill or technology")
    importance_rank: int = Field(description="Importance rank: 1 (critical) to 5 (nice to have)")
    required_proficiency_level: str = Field(description="Required proficiency: expert, advanced, intermediate, basic, familiarity")
    category: str = Field(description="Skill category: programming_language, framework, database, devops, tool, soft_skill")
    mentions_count: int = Field(default=1, description="How many times mentioned in job description")
    context_clues: List[str] = Field(default=[], description="Context phrases that indicate importance")


class DatabaseRequirement(BaseModel):
    """Specific database skill requirements"""
    has_db_requirement: bool = Field(description="Whether job requires database skills")
    db_technologies: List[str] = Field(default=[], description="Specific database technologies mentioned")
    complexity_level: str = Field(default="basic", description="Required complexity: basic, intermediate, advanced, expert")
    specific_skills: List[str] = Field(default=[], description="Specific database skills: schema design, query optimization, NoSQL, etc.")


class JobSkillAnalysis(BaseModel):
    """Complete structured analysis of job description skills"""
    primary_skills: List[SkillImportance] = Field(description="Top priority skills (rank 1-2)")
    secondary_skills: List[SkillImportance] = Field(description="Important but not critical skills (rank 3)")
    tertiary_skills: List[SkillImportance] = Field(description="Nice to have skills (rank 4-5)")
    database_requirement: DatabaseRequirement = Field(description="Database-specific requirements")
    all_ranked_skills: List[SkillImportance] = Field(description="All skills sorted by importance")
    job_level: str = Field(description="Job level: junior, mid-level, senior, principal")
    overall_difficulty: int = Field(description="Overall technical difficulty 1-10")


def analyze_job_description_skills(job_description: str, llm_instance=None) -> JobSkillAnalysis:
    """
    Analyze job description using LLM to extract and rank skills

    Args:
        job_description: The job description text
        llm_instance: Optional LLM instance (uses global llm if not provided)

    Returns:
        JobSkillAnalysis with structured skill rankings
    """
    if llm_instance is None:
        llm_instance = llm

    # Create extraction prompt
    extraction_prompt = f"""
You are an expert technical recruiter analyzing job descriptions to identify and rank required skills.

JOB DESCRIPTION:
{job_description}

Analyze this job description and extract ALL technical skills, ranking them by importance.

IMPORTANCE RANKING CRITERIA:
- Rank 1 (Critical): Skills explicitly marked as "required", "must have", "expert in", appear multiple times, or are central to the role
- Rank 2 (Very Important): Skills mentioned prominently in key responsibilities or qualifications
- Rank 3 (Important): Skills mentioned in requirements but not emphasized
- Rank 4 (Preferred): Skills marked as "nice to have", "plus", "preferred"
- Rank 5 (Optional): Skills mentioned briefly or in passing

PROFICIENCY LEVEL INDICATORS:
- "Expert": "expert in", "deep knowledge", "mastery of"
- "Advanced": "strong skills", "proficient", "extensive experience"
- "Intermediate": "experience with", "working knowledge", "solid understanding"
- "Basic": "familiarity with", "exposure to", "basic knowledge"
- "Familiarity": "plus if", "nice to have", "bonus"

DATABASE DETECTION:
Look for: SQL, PostgreSQL, MySQL, MongoDB, Oracle, Cassandra, Redis, DynamoDB, ElasticSearch, NoSQL, etc.
Assess required complexity: schema design, query optimization, indexing, transactions, etc.

JOB LEVEL DETECTION:
- Junior: 0-2 years, entry-level, junior in title
- Mid-level: 3-5 years, intermediate, mid-level in title
- Senior: 5-10 years, senior in title, lead responsibilities
- Principal: 10+ years, principal/staff/architect in title, strategic role

Return ONLY valid JSON in this exact format:
{{
    "primary_skills": [
        {{
            "skill_name": "SQL",
            "importance_rank": 1,
            "required_proficiency_level": "expert",
            "category": "database",
            "mentions_count": 3,
            "context_clues": ["must have expert SQL skills", "complex query optimization required"]
        }}
    ],
    "secondary_skills": [
        {{
            "skill_name": "Python",
            "importance_rank": 3,
            "required_proficiency_level": "intermediate",
            "category": "programming_language",
            "mentions_count": 2,
            "context_clues": ["experience with Python for scripting"]
        }}
    ],
    "tertiary_skills": [
        {{
            "skill_name": "Docker",
            "importance_rank": 4,
            "required_proficiency_level": "basic",
            "category": "devops",
            "mentions_count": 1,
            "context_clues": ["familiarity with containerization is a plus"]
        }}
    ],
    "database_requirement": {{
        "has_db_requirement": true,
        "db_technologies": ["SQL", "PostgreSQL", "MongoDB"],
        "complexity_level": "expert",
        "specific_skills": ["schema design", "query optimization", "indexing", "complex joins"]
    }},
    "all_ranked_skills": [
        {{
            "skill_name": "SQL",
            "importance_rank": 1,
            "required_proficiency_level": "expert",
            "category": "database",
            "mentions_count": 3,
            "context_clues": ["must have expert SQL skills"]
        }},
        {{
            "skill_name": "Python",
            "importance_rank": 3,
            "required_proficiency_level": "intermediate",
            "category": "programming_language",
            "mentions_count": 2,
            "context_clues": ["experience with Python"]
        }}
    ],
    "job_level": "senior",
    "overall_difficulty": 8
}}

IMPORTANT: Return ONLY the JSON object, no additional text, markdown formatting, or code blocks.
"""

    try:
        # Invoke LLM
        response = llm_instance.invoke(extraction_prompt)
        structured_json = response.content.strip()

        # Clean response
        if structured_json.startswith("```json"):
            structured_json = structured_json.replace("```json", "").replace("```", "").strip()
        elif structured_json.startswith("```"):
            structured_json = structured_json.replace("```", "").strip()

        # Parse JSON
        parsed_data = json.loads(structured_json)

        # Create and return JobSkillAnalysis
        return JobSkillAnalysis(**parsed_data)

    except json.JSONDecodeError as e:
        print(f"JSON decode error in job skill analysis: {e}")
        print(f"LLM response (first 500 chars): {structured_json[:500]}")
        return create_fallback_analysis(job_description)
    except Exception as e:
        print(f"Error analyzing job description skills: {e}")
        return create_fallback_analysis(job_description)


def create_fallback_analysis(job_description: str) -> JobSkillAnalysis:
    """Create basic fallback analysis when LLM extraction fails"""
    # Simple keyword-based extraction as fallback
    job_lower = job_description.lower()

    # Check for database requirement
    db_keywords = ['sql', 'database', 'postgresql', 'mysql', 'mongodb', 'oracle', 'nosql']
    has_db = any(keyword in job_lower for keyword in db_keywords)

    db_techs = []
    if 'sql' in job_lower or 'postgresql' in job_lower or 'mysql' in job_lower:
        db_techs.append('SQL')
    if 'mongodb' in job_lower or 'nosql' in job_lower:
        db_techs.append('MongoDB')

    # Basic programming language detection
    primary_skills = []
    if 'python' in job_lower:
        primary_skills.append(SkillImportance(
            skill_name="Python",
            importance_rank=1,
            required_proficiency_level="intermediate",
            category="programming_language",
            mentions_count=1,
            context_clues=[]
        ))

    if 'javascript' in job_lower or 'js' in job_lower:
        primary_skills.append(SkillImportance(
            skill_name="JavaScript",
            importance_rank=2,
            required_proficiency_level="intermediate",
            category="programming_language",
            mentions_count=1,
            context_clues=[]
        ))

    # Default to Python if nothing found
    if not primary_skills:
        primary_skills.append(SkillImportance(
            skill_name="Python",
            importance_rank=1,
            required_proficiency_level="intermediate",
            category="programming_language",
            mentions_count=1,
            context_clues=[]
        ))

    return JobSkillAnalysis(
        primary_skills=primary_skills,
        secondary_skills=[],
        tertiary_skills=[],
        database_requirement=DatabaseRequirement(
            has_db_requirement=has_db,
            db_technologies=db_techs,
            complexity_level="intermediate" if has_db else "basic",
            specific_skills=[]
        ),
        all_ranked_skills=primary_skills,
        job_level="mid-level",
        overall_difficulty=5
    )


def save_skill_analysis(analysis: JobSkillAnalysis, output_path: str):
    """Save skill analysis to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"✅ Skill analysis saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving skill analysis: {e}")


def load_skill_analysis(input_path: str) -> Optional[JobSkillAnalysis]:
    """Load skill analysis from JSON file"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return JobSkillAnalysis(**data)
    except Exception as e:
        print(f"Error loading skill analysis: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    # Test with sample job description
    sample_job = """
    Senior Backend Developer - Database Focus

    We are looking for an expert SQL developer with strong Python skills.

    Required Skills:
    - Expert-level SQL (PostgreSQL, MySQL) - MUST HAVE
    - Advanced query optimization and schema design
    - Strong Python programming for backend services
    - Experience with Django or Flask
    - Docker and Kubernetes knowledge is a plus

    Qualifications:
    - 5+ years of software development experience
    - Deep understanding of relational database design
    - Proven track record of optimizing complex SQL queries
    """

    print("Testing Job Skill Analyzer...")
    analysis = analyze_job_description_skills(sample_job)

    print("\n=== ANALYSIS RESULTS ===")
    print(f"Job Level: {analysis.job_level}")
    print(f"Overall Difficulty: {analysis.overall_difficulty}/10")
    print(f"\nPrimary Skills ({len(analysis.primary_skills)}):")
    for skill in analysis.primary_skills:
        print(f"  - {skill.skill_name} (Rank {skill.importance_rank}, {skill.required_proficiency_level})")

    print(f"\nDatabase Requirement: {analysis.database_requirement.has_db_requirement}")
    if analysis.database_requirement.has_db_requirement:
        print(f"  Technologies: {', '.join(analysis.database_requirement.db_technologies)}")
        print(f"  Complexity: {analysis.database_requirement.complexity_level}")

    # Save to file
    save_skill_analysis(analysis, "test_structured_skills.json")
