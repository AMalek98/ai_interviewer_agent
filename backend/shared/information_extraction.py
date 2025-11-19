"""
Information Extraction Functions for AI Interview System

This module contains all CV and job description parsing and extraction functions:
- CV parsing from PDF files
- Job description parsing from TXT files
- Technology extraction from CV and job descriptions
- Technology matching between CV and job requirements
"""

import json
import os
import re
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader

from shared.models import (
    StructuredCV, StructuredJobDescription,
    WorkExperience, Education, Skill, Project, PersonalInfo
)


# ============================================================================
# CV Extraction Functions
# ============================================================================

def parse_pdf_cv(pdf_path: str, llm) -> StructuredCV:
    """
    Parse a PDF CV and extract structured information using LLM

    Args:
        pdf_path: Path to the PDF CV file
        llm: Language model instance for extraction

    Returns:
        StructuredCV object with parsed CV data
    """
    try:
        # Load PDF content
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        cv_text = "\n".join([page.page_content for page in pages])

        # Clean text to handle Unicode characters that might cause issues
        # Replace problematic Unicode characters with safe alternatives
        cv_text = cv_text.replace('\u2642', '[Male]')  # Male symbol
        cv_text = cv_text.replace('\u2640', '[Female]')  # Female symbol
        cv_text = cv_text.replace('\u2022', '•')  # Bullet point
        # Remove other potentially problematic characters
        cv_text = cv_text.encode('utf-8', errors='replace').decode('utf-8')

        # Safely print CV text avoiding Unicode encoding issues
        try:
            print(f"Loaded CV text (first 500 chars): {cv_text[:500]}...")
        except UnicodeEncodeError:
            print(f"Loaded CV text: {len(cv_text)} characters (contains Unicode characters)")

        # Create structured extraction prompt
        extraction_prompt = f"""
You are an expert CV parser. Extract structured information from the following CV text and return it in the exact JSON format specified.

CV Text:
{cv_text}

Extract the following information and return as valid JSON:

{{
  "personal_info": {{
    "name": "candidate name if found",
    "email": "email if found",
    "phone": "phone if found",
    "location": "location if found"
  }},
  "experiences": [
    {{
      "company": "company name",
      "position": "job title",
      "start_date": "start date in format like 'February 2024' or 'Feb 2024'",
      "end_date": "end date in format like 'July 2024' or 'Present'",
      "duration": "duration mentioned like '6 months' or '2 years'",
      "responsibilities": ["list of responsibilities and achievements"],
      "technologies": ["technologies, tools, frameworks mentioned"]
    }}
  ],
  "education": [
    {{
      "institution": "school/university name",
      "degree": "degree type",
      "field_of_study": "field of study",
      "start_date": "start date",
      "end_date": "end date",
      "grade": "grade or GPA if mentioned"
    }}
  ],
  "skills": [
    {{
      "name": "skill name",
      "category": "programming|tool|framework|soft_skill|language",
      "proficiency": "proficiency level if mentioned"
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "project description",
      "technologies": ["technologies used"],
      "duration": "duration if mentioned",
      "achievements": ["achievements or metrics like accuracy percentages"]
    }}
  ],
  "achievements": ["notable achievements, awards, certifications"],
  "languages": ["languages spoken"]
}}

IMPORTANT: Return ONLY the JSON object, no additional text or explanations.
"""

        # Get structured extraction from LLM
        response = llm.invoke(extraction_prompt)
        extracted_json = response.content.strip()

        # Clean up response if it has markdown formatting
        if extracted_json.startswith("```json"):
            extracted_json = extracted_json.replace("```json", "").replace("```", "").strip()
        elif extracted_json.startswith("```"):
            extracted_json = extracted_json.replace("```", "").strip()

        # Safely print extracted JSON avoiding Unicode encoding issues
        try:
            print(f"Extracted JSON: {extracted_json[:500]}...")
        except UnicodeEncodeError:
            print(f"Extracted JSON: {len(extracted_json)} characters (contains Unicode characters)")

        # Parse JSON and create StructuredCV object
        try:
            cv_data = json.loads(extracted_json)
            structured_cv = StructuredCV(**cv_data)
            print("Successfully created StructuredCV object")
            return structured_cv
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Return basic structure if JSON parsing fails
            return StructuredCV()
        except Exception as e:
            print(f"Error creating StructuredCV: {e}")
            return StructuredCV()

    except Exception as e:
        print(f"Error parsing PDF CV: {e}")
        return StructuredCV()


def extract_technologies_from_cv(structured_cv: StructuredCV) -> List[str]:
    """
    Extract all technologies mentioned in the CV

    Args:
        structured_cv: StructuredCV object to extract technologies from

    Returns:
        List of unique technology names (lowercase)
    """
    technologies = set()

    # From skills
    for skill in structured_cv.skills:
        if skill.category.lower() in ['programming', 'tool', 'framework']:
            technologies.add(skill.name.lower())

    # From experiences
    for exp in structured_cv.experiences:
        technologies.update([tech.lower() for tech in exp.technologies])

    # From projects
    for proj in structured_cv.projects:
        technologies.update([tech.lower() for tech in proj.technologies])

    return list(technologies)


# ============================================================================
# Job Description Extraction Functions
# ============================================================================

def parse_txt_job_description(txt_path: str, llm) -> StructuredJobDescription:
    """
    Parse a TXT job description file and extract structured information using LLM

    Args:
        txt_path: Path to the TXT job description file
        llm: Language model instance for extraction

    Returns:
        StructuredJobDescription object with parsed job data
    """
    try:
        # Load TXT content
        print(f"Loading job description from: {txt_path}")
        with open(txt_path, 'r', encoding='utf-8') as f:
            job_text = f.read()

        print(f"Loaded job description text (first 200 chars): {job_text[:200]}...")

        # Create structured extraction prompt
        extraction_prompt = f"""
You are an expert job description parser. Extract structured information from the following job posting and return it in the exact JSON format specified.

Job Description Text:
{job_text}

Extract the following information and return as valid JSON:

{{
  "job_title": "position title",
  "company_name": "company name if mentioned",
  "location": "location if mentioned",
  "job_type": "Full-time|Part-time|Contract|Remote|Hybrid",
  "seniority_level": "Junior|Mid-level|Senior|Lead|Principal|Entry-level",
  "required_skills": ["list of required technical skills and technologies"],
  "preferred_skills": ["list of preferred/nice-to-have skills"],
  "responsibilities": ["list of job responsibilities and duties"],
  "requirements": ["list of requirements like years of experience, education, etc."],
  "experience_years": number or null,
  "education_requirements": ["education requirements like Bachelor's, Master's, etc."],
  "domain": "ai_ml|web_development|data_science|mobile|devops|general",
  "technologies": ["all technologies, frameworks, tools, languages mentioned"],
  "benefits": ["benefits and perks mentioned"],

  "industry": "banking|healthcare|e-commerce|fintech|insurance|retail|logistics|education|manufacturing|general or null if not clear",
  "business_context": ["business problems like: fraud detection, risk analysis, recommendation systems, customer segmentation, predictive maintenance, etc."],
  "domain_specific_challenges": ["domain-specific challenges like: regulatory compliance, data privacy, real-time processing, scalability, high availability, security, etc."]
}}

INSTRUCTIONS FOR NEW FIELDS:
- "industry": Infer from company name, job title, or job description context. Examples:
  * "Data Scientist at JPMorgan" → "banking"
  * "ML Engineer - Healthcare" → "healthcare"
  * "Backend Developer for e-commerce platform" → "e-commerce"
  * If unclear, set to null

- "business_context": Extract specific business problems or use cases mentioned:
  * "build fraud detection models" → ["fraud detection"]
  * "improve recommendation algorithms" → ["recommendation systems"]
  * "analyze customer churn" → ["customer segmentation", "churn prediction"]

- "domain_specific_challenges": Extract technical/business constraints:
  * "ensure HIPAA compliance" → ["regulatory compliance", "data privacy"]
  * "handle millions of transactions per second" → ["real-time processing", "scalability"]
  * "maintain 99.99% uptime" → ["high availability"]

IMPORTANT: Return ONLY the JSON object, no additional text or explanations.
"""

        # Get structured extraction from LLM
        print("Sending extraction prompt to LLM...")
        response = llm.invoke(extraction_prompt)
        extracted_json = response.content.strip()

        # Clean up response if it has markdown formatting
        if extracted_json.startswith("```json"):
            extracted_json = extracted_json.replace("```json", "").replace("```", "").strip()
        elif extracted_json.startswith("```"):
            extracted_json = extracted_json.replace("```", "").strip()

        print(f"Extracted JSON (first 300 chars): {extracted_json[:300]}...")

        # Parse JSON and create StructuredJobDescription object
        try:
            job_data = json.loads(extracted_json)
            structured_job = StructuredJobDescription(**job_data)
            print("Successfully created StructuredJobDescription object")
            print(f"Job Title: {structured_job.job_title}")
            print(f"Seniority: {structured_job.seniority_level}")
            print(f"Technologies: {len(structured_job.technologies)} found")
            return structured_job
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Return basic structure if JSON parsing fails
            return StructuredJobDescription(
                job_title="Unknown Position",
                seniority_level="mid",
                domain="general"
            )
        except Exception as e:
            print(f"Error creating StructuredJobDescription: {e}")
            return StructuredJobDescription(
                job_title="Unknown Position",
                seniority_level="mid",
                domain="general"
            )

    except Exception as e:
        print(f"Error parsing job description: {e}")
        return StructuredJobDescription(
            job_title="Unknown Position",
            seniority_level="mid",
            domain="general"
        )


def extract_technologies_from_job(job_description: str) -> List[str]:
    """
    Extract technologies mentioned in job description with enhanced domain-specific patterns

    Args:
        job_description: Raw job description text

    Returns:
        List of unique technology names (lowercase)
    """
    # Enhanced technology patterns by domain
    tech_patterns = {
        # Programming Languages
        'languages': [
            r'\b(python|java|javascript|typescript|go|rust|c\+\+|c#|kotlin|swift|scala|r)\b',
            r'\b(php|ruby|perl|julia|haskell|elixir|erlang)\b'
        ],

        # Web Development
        'web_frontend': [
            r'\b(react|angular|vue|svelte|next\.?js|nuxt|gatsby)\b',
            r'\b(html|css|sass|scss|less|tailwind|bootstrap|chakra)\b',
            r'\b(webpack|vite|parcel|rollup|esbuild)\b'
        ],

        'web_backend': [
            r'\b(node\.?js|express|koa|fastify|nest\.?js)\b',
            r'\b(flask|django|fastapi|pyramid|tornado)\b',
            r'\b(spring|spring boot|struts|hibernate)\b',
            r'\b(rails|sinatra|grape)\b'
        ],

        # Databases
        'databases': [
            r'\b(sql|mysql|postgresql|postgres|sqlite|mariadb)\b',
            r'\b(mongodb|redis|cassandra|dynamodb|neo4j)\b',
            r'\b(elasticsearch|solr|influxdb|clickhouse)\b',
            r'\b(pgvector|pinecone|weaviate|chroma|qdrant)\b'
        ],

        # Cloud & DevOps
        'cloud': [
            r'\b(aws|azure|gcp|google cloud|oracle cloud)\b',
            r'\b(ec2|s3|lambda|rds|dynamodb|cloudformation)\b',
            r'\b(kubernetes|k8s|docker|containerd|podman)\b',
            r'\b(terraform|ansible|puppet|chef|helm)\b'
        ],

        'devops': [
            r'\b(ci/cd|jenkins|github actions|gitlab ci|bamboo)\b',
            r'\b(git|svn|mercurial|bitbucket|jira)\b',
            r'\b(monitoring|prometheus|grafana|datadog|newrelic)\b',
            r'\b(nginx|apache|haproxy|cloudflare)\b'
        ],

        # AI/ML & Data Science
        'ai_ml': [
            r'\b(machine learning|ml|artificial intelligence|ai|deep learning|dl)\b',
            r'\b(langchain|langgraph|llamaindex|haystack|semantic kernel)\b',
            r'\b(pytorch|tensorflow|keras|scikit-learn|xgboost|lightgbm)\b',
            r'\b(hugging face|transformers|diffusers|peft|lora)\b',
            r'\b(openai|anthropic|claude|gpt|chatgpt|llama|gemini)\b',
            r'\b(embeddings?|vector database|rag|fine-tuning|prompt engineering)\b'
        ],

        'data_science': [
            r'\b(pandas|numpy|scipy|matplotlib|seaborn|plotly)\b',
            r'\b(jupyter|notebook|data analysis|etl|data pipeline)\b',
            r'\b(spark|hadoop|kafka|airflow|dbt|snowflake)\b',
            r'\b(tableau|power bi|looker|metabase)\b'
        ],

        'computer_vision': [
            r'\b(opencv|yolo|computer vision|cv|image processing)\b',
            r'\b(cnn|convolutional|object detection|segmentation)\b',
            r'\b(pillow|pil|imageio|albumentations)\b'
        ],

        'nlp': [
            r'\b(nlp|natural language processing|text processing)\b',
            r'\b(spacy|nltk|gensim|word2vec|bert|roberta)\b',
            r'\b(tokenization|stemming|lemmatization|ner)\b'
        ],

        # Mobile Development
        'mobile': [
            r'\b(react native|flutter|ionic|xamarin)\b',
            r'\b(android|ios|swift|kotlin|objective-c)\b',
            r'\b(expo|cordova|phonegap)\b'
        ],

        # Testing & Quality
        'testing': [
            r'\b(pytest|unittest|jest|mocha|cypress|selenium)\b',
            r'\b(testing|unit test|integration test|e2e|tdd|bdd)\b',
            r'\b(postman|insomnia|swagger|openapi)\b'
        ]
    }

    technologies = set()
    job_desc_lower = job_description.lower()

    # Extract technologies by domain
    for domain, patterns in tech_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, job_desc_lower)
            technologies.update(matches)

    # Clean up extracted technologies
    cleaned_technologies = []
    for tech in technologies:
        if tech and len(tech) > 1:  # Filter out single characters
            cleaned_technologies.append(tech.strip())

    return list(set(cleaned_technologies))  # Remove duplicates


def extract_job_requirements(job_description: str) -> Dict[str, Any]:
    """
    Extract structured requirements from job description (basic text-based extraction)

    Note: This function provides basic extraction. For more accurate results,
    use parse_txt_job_description() with LLM.

    Args:
        job_description: Raw job description text

    Returns:
        Dictionary with seniority, required_skills, experience_years, domain, raw_text
    """
    job_lower = job_description.lower()

    # Detect seniority level
    seniority = "mid"  # default
    if any(indicator in job_lower for indicator in ["senior", "lead", "principal", "architect"]):
        seniority = "senior"
    elif any(indicator in job_lower for indicator in ["junior", "entry", "intern", "graduate"]):
        seniority = "junior"

    # Extract experience years
    experience_years = 0
    year_matches = re.findall(r'(\d+)\s*(?:\+)?\s*years?', job_lower)
    if year_matches:
        experience_years = max(int(year) for year in year_matches)

    # Detect domain
    domain = "general"
    if any(term in job_lower for term in ["ai", "machine learning", "nlp", "computer vision"]):
        domain = "ai_ml"
    elif any(term in job_lower for term in ["data scientist", "data analysis", "analytics"]):
        domain = "data_science"
    elif any(term in job_lower for term in ["web", "frontend", "backend", "full stack"]):
        domain = "web_development"

    return {
        "seniority": seniority,
        "required_skills": extract_technologies_from_job(job_description),
        "experience_years": experience_years,
        "domain": domain,
        "raw_text": job_description[:200] + "..." if len(job_description) > 200 else job_description
    }


# ============================================================================
# Technology Matching
# ============================================================================

def find_matching_technologies(cv_technologies: List[str], job_technologies: List[str]) -> List[str]:
    """
    Find technologies that appear in both CV and job description

    Args:
        cv_technologies: List of technologies from CV
        job_technologies: List of technologies from job description

    Returns:
        List of matching technologies (intersection)
    """
    cv_set = set(tech.lower() for tech in cv_technologies)
    job_set = set(tech.lower() for tech in job_technologies)

    matched = cv_set.intersection(job_set)
    return list(matched)
