import re
import os
import pypdf

# Comprehensive Skill Taxonomy for Keyword Matching
SKILL_TAXONOMY = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Golang", 
        "Rust", "PHP", "Ruby", "Swift", "Kotlin", "R", "Scala", "Dart", "HTML", "CSS", "SQL", "Bash", "Shell"
    ],
    "Frameworks & Libraries": [
        "Flask", "Django", "FastAPI", "React", "React.js", "React Native", "Vue", "Vue.js", 
        "Angular", "Next.js", "Express", "Express.js", "Node.js", "Spring", "Spring Boot", 
        "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-Learn", "Keras", "Tailwind CSS", "Bootstrap",
        "Hibernate", "ASP.NET", ".NET"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", "Elasticsearch", 
        "Cassandra", "DynamoDB", "Oracle", "SQL Server", "Vector Database", "Pinecone", "ChromaDB", "Neo4j"
    ],
    "Cloud & DevOps": [
        "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", 
        "Terraform", "Ansible", "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI", "Linux", 
        "Nginx", "Apache", "Serverless", "Kafka", "RabbitMQ"
    ],
    "AI & Data Engineering": [
        "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP", "Natural Language Processing", 
        "Computer Vision", "LLM", "Generative AI", "LangChain", "RAG", "Data Mining", 
        "Data Warehousing", "Spark", "Apache Spark", "Hadoop", "Airflow", "ETL"
    ],
    "Tools & Platforms": [
        "Git", "GitHub", "GitLab", "Jira", "Postman", "Swagger", "Figma", "VS Code", "IntelliJ", "Vite"
    ],
    "Concepts & Soft Skills": [
        "REST API", "GraphQL", "Microservices", "System Design", "Object-Oriented Programming", "OOP", 
        "Agile", "Scrum", "CI/CD", "TDD", "Test-Driven Development", "Data Structures", "Algorithms", 
        "Problem Solving", "Leadership", "Team Collaboration", "Project Management", "Communication"
    ]
}


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extracts raw text from a PDF file using pypdf.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
        
    return text.strip()


def extract_skills_from_text(text: str) -> list:
    """
    Scans text for skills from the predefined taxonomy and returns a sorted list of unique extracted skills.
    """
    if not text:
        return []

    found_skills = set()
    cleaned_text = " " + re.sub(r'[^a-zA-Z0-9+#.\s]', ' ', text) + " "

    for category, skill_list in SKILL_TAXONOMY.items():
        for skill in skill_list:
            # Special regex handling for skills with symbols like C++, C#, .NET, Node.js
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, cleaned_text, re.IGNORECASE):
                # Preserve standard display capitalization
                found_skills.add(skill)
            elif re.search(r'(?i)\b' + re.escape(skill.lower()) + r'\b', text):
                found_skills.add(skill)

    # Convert to sorted list
    return sorted(list(found_skills), key=lambda s: s.lower())


def process_resume(filepath: str) -> dict:
    """
    Helper function to parse a resume PDF file and extract text & skills.
    """
    extracted_text = extract_text_from_pdf(filepath)
    skills = extract_skills_from_text(extracted_text)
    return {
        "text": extracted_text,
        "skills": skills
    }
