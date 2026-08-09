import os
import re
import json

# Pre-built Role-Skill Question Bank for Intelligent Fallback Generation
DEFAULT_QUESTION_BANK = {
    "Python Backend Engineer": [
        {"question": "How do Python's Global Interpreter Lock (GIL) and asyncio concurrency model affect high-throughput backend applications, and how would you optimize database connections under heavy load?", "category": "Technical"},
        {"question": "Describe how you design RESTful APIs and handle request authentication, rate limiting, and exception management in Flask or Django.", "category": "System Design"},
        {"question": "Walk me through a time when you diagnosed a slow database query or memory leak in production. What tools did you use and how was it resolved?", "category": "Problem Solving"},
        {"question": "How do you structure database migrations and maintain data integrity when deploying breaking schema changes in a continuous deployment pipeline?", "category": "Technical"},
        {"question": "Tell me about a situation where you had a strong technical disagreement with a teammate regarding system architecture. How did you resolve it?", "category": "Behavioral"}
    ],
    "Data Scientist / AI Engineer": [
        {"question": "Explain the difference between Fine-tuning, Retrieval-Augmented Generation (RAG), and Prompt Engineering when building domain-specific LLM solutions.", "category": "Technical"},
        {"question": "How do you address data drift, overfitting, and missing values when training predictive models on real-world noisy datasets?", "category": "Problem Solving"},
        {"question": "Describe an end-to-end Machine Learning pipeline you designed. How did you handle data pre-processing, feature engineering, and model deployment?", "category": "System Design"},
        {"question": "How do you evaluate model metrics beyond accuracy (e.g., Precision, Recall, F1-Score, ROC-AUC) when dealing with severely imbalanced datasets?", "category": "Technical"},
        {"question": "Describe a project where an ML model did not perform as expected in production. What post-mortem analysis did you conduct?", "category": "Behavioral"}
    ],
    "DevOps / Cloud Engineer": [
        {"question": "How do you implement container orchestration with Kubernetes and ensure automated zero-downtime rolling deployments using CI/CD pipelines?", "category": "Technical"},
        {"question": "Explain Infrastructure as Code (IaC) using Terraform or Ansible. How do you handle state locking, secrets management, and drift detection?", "category": "System Design"},
        {"question": "Walk me through your incident response strategy when a critical microservice experiences high CPU usage and cascading latency spikes.", "category": "Problem Solving"},
        {"question": "What security best practices do you enforce in cloud environments (AWS/Azure/GCP) regarding IAM, VPC peering, and secrets management?", "category": "Technical"},
        {"question": "Give an example of how you successfully automated a repetitive infrastructure bottleneck to improve developer productivity.", "category": "Behavioral"}
    ],
    "Full Stack Developer": [
        {"question": "How do you manage state and optimize render performance in modern frontend applications (React/Vue/Next.js) while integrating with a REST or GraphQL backend?", "category": "Technical"},
        {"question": "Describe how you secure web applications against common vulnerabilities like Cross-Site Scripting (XSS), CSRF, and SQL Injection.", "category": "System Design"},
        {"question": "Walk me through a complex bug that spanned both frontend rendering and backend backend logic. How did you trace and resolve it?", "category": "Problem Solving"},
        {"question": "What strategies do you use for asset caching, lazy loading, and database indexing to optimize end-to-end page load speed?", "category": "Technical"},
        {"question": "Tell me about a challenging tight deadline feature release. How did you prioritize technical debt versus speed to market?", "category": "Behavioral"}
    ],
    "Software Engineer (General)": [
        {"question": "Explain SOLID principles and Object-Oriented Design patterns, giving a concrete example of how they make code maintainable and extensible.", "category": "Technical"},
        {"question": "How do you design a scalable microservices system that handles asynchronous background tasks, retries, and message queues (e.g., Celery/RabbitMQ)?", "category": "System Design"},
        {"question": "Describe your approach to writing clean code, unit testing, and conducting code reviews within an Agile team.", "category": "Behavioral"},
        {"question": "How do you analyze the Time and Space complexity (Big-O) of an algorithm before deciding on the data structures to use?", "category": "Technical"},
        {"question": "Tell me about a time you made a significant mistake in production code. What was the impact, and how did you mitigate and prevent it from recurring?", "category": "Behavioral"}
    ]
}


def generate_questions(skills: list, target_role: str, experience_level: str = "Mid Level", count: int = 5) -> list:
    """
    Generates personalized interview questions matching target role and extracted candidate skills.
    Attempts Gemini API call if key is available, otherwise uses smart custom question generator.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Generate exactly {count} personalized interview questions for a candidate applying for the target role: "{target_role}" ({experience_level} level).
            The candidate's resume highlights these skills: {', '.join(skills) if skills else 'General Software Engineering'}.

            Return ONLY valid JSON format with an array of objects having keys:
            - "question": string
            - "category": string (one of "Technical", "Behavioral", "System Design", "Problem Solving")

            Ensure questions range across technical core skills, real-world scenario handling, and system architecture.
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            raw_text = response.text
            match = re.search(r'\[.*\]', raw_text, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
                if isinstance(questions, list) and len(questions) > 0:
                    return questions[:count]
        except Exception as e:
            print(f"Gemini API Question Generation error (falling back to smart engine): {e}")

    # --- Smart Fallback Question Generator ---
    base_questions = DEFAULT_QUESTION_BANK.get(target_role)
    if not base_questions:
        # Match closest role
        if "data" in target_role.lower() or "ai" in target_role.lower() or "ml" in target_role.lower():
            base_questions = DEFAULT_QUESTION_BANK["Data Scientist / AI Engineer"]
        elif "devops" in target_role.lower() or "cloud" in target_role.lower() or "sys" in target_role.lower():
            base_questions = DEFAULT_QUESTION_BANK["DevOps / Cloud Engineer"]
        elif "stack" in target_role.lower() or "front" in target_role.lower() or "web" in target_role.lower():
            base_questions = DEFAULT_QUESTION_BANK["Full Stack Developer"]
        elif "python" in target_role.lower() or "back" in target_role.lower():
            base_questions = DEFAULT_QUESTION_BANK["Python Backend Engineer"]
        else:
            base_questions = DEFAULT_QUESTION_BANK["Software Engineer (General)"]

    questions = [dict(q) for q in base_questions[:count]]
    
    # Customize questions with top extracted skills if present
    if skills:
        top_skills = skills[:3]
        for i, q in enumerate(questions):
            skill_to_inject = top_skills[i % len(top_skills)]
            if "Technical" in q["category"] and skill_to_inject.lower() not in q["question"].lower():
                q["question"] = f"Based on your experience with {skill_to_inject}: {q['question']}"
                
    return questions


def evaluate_answer(question_text: str, category: str, user_answer: str, skills: list = None, target_role: str = "") -> dict:
    """
    Evaluates candidate's user answer against the question.
    Returns:
    {
        "score": float (0-100),
        "feedback": str,
        "strengths": list of str,
        "improvements": list of str,
        "sample_answer": str
    }
    """
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            "score": 15.0,
            "feedback": "The answer provided was very brief or blank. In technical and behavioral interviews, comprehensive answers demonstrating your thought process, implementation steps, and concrete results are essential.",
            "strengths": ["Submitted response for evaluation."],
            "improvements": [
                "Provide a detailed structured response.",
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions.",
                "Mention specific technologies, methodologies, or algorithmic complexity for technical questions."
            ],
            "sample_answer": get_sample_answer(question_text, category, target_role)
        }

    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are an expert technical interviewer evaluating an interview response for a {target_role or 'Software Engineer'} role.

            Question ({category}): "{question_text}"
            Candidate Answer: "{user_answer}"

            Evaluate the candidate's answer and return ONLY a JSON object with keys:
            - "score": number between 0 and 100
            - "feedback": constructive summary string (3-4 sentences)
            - "strengths": array of 2-3 specific positive aspects
            - "improvements": array of 2-3 actionable improvement tips
            - "sample_answer": a high-scoring sample model response for this question (4-5 sentences)
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            raw_text = response.text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "score": float(data.get("score", 75)),
                    "feedback": data.get("feedback", "Good effort on answering this question."),
                    "strengths": data.get("strengths", ["Clear explanation."]),
                    "improvements": data.get("improvements", ["Elaborate with deeper technical examples."]),
                    "sample_answer": data.get("sample_answer", get_sample_answer(question_text, category, target_role))
                }
        except Exception as e:
            print(f"Gemini Evaluation error (falling back to smart evaluator): {e}")

    # --- Smart Local NLP Evaluation Engine ---
    words = user_answer.split()
    word_count = len(words)
    lower_ans = user_answer.lower()
    
    score = 60.0
    strengths = []
    improvements = []
    
    # Word count & completeness check
    if word_count >= 80:
        score += 18.0
        strengths.append("Comprehensive response length demonstrating thorough elaboration.")
    elif word_count >= 40:
        score += 10.0
        strengths.append("Decent response depth covering core points.")
    else:
        improvements.append("Expand your response with more specific context, architectural details, and metrics.")

    # Structure & Keywords (STAR method or Technical terminology)
    star_keywords = ["situation", "task", "action", "result", "when", "project", "team", "challenge", "resolved", "improved", "percent", "reduced", "led"]
    found_star = [kw for kw in star_keywords if kw in lower_ans]
    if len(found_star) >= 3:
        score += 12.0
        strengths.append("Good narrative structure showcasing problem context and tangible outcomes.")
    else:
        improvements.append("Use structured storytelling (e.g. state the problem, your exact technical actions, and quantitative results achieved).")

    # Technical concepts & clarity
    tech_keywords = ["architecture", "scale", "performance", "database", "api", "test", "security", "optimization", "deploy", "ci/cd", "algorithm", "design", "metric"]
    found_tech = [kw for kw in tech_keywords if kw in lower_ans]
    if len(found_tech) >= 2:
        score += 10.0
        strengths.append("Effective incorporation of technical terminology and operational practices.")
    else:
        improvements.append("Highlight specific tools, frameworks, and performance metrics relevant to the target role.")

    # Cap score at 98
    score = min(98.0, round(score, 1))

    # Construct constructive feedback text
    feedback = f"Your answer scored {score}/100. "
    if score >= 85:
        feedback += "Outstanding response! You clearly articulated key concepts, demonstrated practical experience, and structured your explanation effectively."
    elif score >= 70:
        feedback += "Solid response covering the main points. To elevate your answer to senior level, incorporate specific quantitative results and trade-offs considered."
    else:
        feedback += "A decent foundational start. Enhance your response by providing concrete technical examples, step-by-step methodologies, and lessons learned."

    if not strengths:
        strengths = ["Responded directly to the interviewer's prompt."]

    sample_answer = get_sample_answer(question_text, category, target_role)

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths,
        "improvements": improvements,
        "sample_answer": sample_answer
    }


def get_sample_answer(question_text: str, category: str, target_role: str) -> str:
    """
    Generates a structured, model sample answer for learning and reference.
    """
    if "gil" in question_text.lower() or "python" in question_text.lower():
        return ("In Python, the Global Interpreter Lock (GIL) ensures thread safety by allowing only one native thread to execute Python bytecode at a time. "
                "For I/O-bound tasks like web APIs, `asyncio` or multi-threading works efficiently as the GIL is released during socket operations. "
                "For CPU-bound bottlenecks, I utilize multi-processing (`multiprocessing` or Celery workers). "
                "To optimize database performance under heavy traffic, I implement connection pooling (e.g., via SQLAlchemy/pgBouncer) and asynchronous ORM queries.")
    
    if "rag" in question_text.lower() or "llm" in question_text.lower():
        return ("Prompt Engineering involves crafting precise instructions to guide LLM outputs without modifying model weights. "
                "RAG dynamically retrieves real-time private contextual data from vector databases (like ChromaDB or Pinecone) and feeds it to the prompt. "
                "Fine-tuning recalibrates model weights on custom domain datasets for specialized tone and syntax. "
                "In enterprise production systems, RAG is ideal for factual accuracy and dynamic knowledge bases, while Fine-Tuning is best for domain-specific formatting.")
    
    if "kubernetes" in question_text.lower() or "docker" in question_text.lower():
        return ("To achieve zero-downtime deployments, I structure CI/CD pipelines using GitHub Actions to build immutable Docker containers, execute unit and integration tests, and push tagged images to ECR. "
                "In Kubernetes, I configure RollingUpdate deployment strategies alongside readiness and liveness probes. "
                "This ensures traffic is routed to new pods only when health checks pass, seamlessly gracefully draining old pods without dropped user requests.")

    if category == "Behavioral":
        return ("In my previous project, we faced a tight release deadline while scaling an API service under 3x expected load (Situation/Task). "
                "I organized an immediate triage meeting, analyzed APM telemetry, and identified unindexed database queries (Action). "
                "We introduced Redis caching and composite database indexes, reducing p99 latency by 65% and delivering the release on schedule (Result).")

    return (f"A comprehensive answer for this {category} question in a {target_role or 'engineering'} role should begin by stating the overarching principle or architecture. "
            "Next, walk through the step-by-step implementation, highlighting trade-offs (such as latency vs throughput). "
            "Finally, conclude with how you validate performance through automated testing and monitoring telemetry.")
