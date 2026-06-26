import json
import random

seed_jobs = [
    {
        "id": "seed-1",
        "title": "Computer Vision / ML Intern",
        "company": "TechNova AI",
        "category": "Machine Learning",
        "experience_years": 0,
        "skills": ["Python", "PyTorch", "YOLO", "Computer Vision", "Explainable AI"],
        "description": "We are seeking a Computer Vision / ML Intern to help us implement advanced object detection pipelines. You will work with PyTorch, YOLO, and Python. A key area of focus will be integrating Explainable AI methods to interpret neural network decisions.",
        "location": "San Francisco, CA (Hybrid)",
        "type": "Internship"
    },
    {
        "id": "seed-2",
        "title": "Robotics Software Engineer Intern",
        "company": "RoboWorks Systems",
        "category": "Robotics",
        "experience_years": 0,
        "skills": ["C++", "ROS", "Kinematics", "Python", "Linux"],
        "description": "RoboWorks is looking for a Robotics Software Engineer Intern. You will design kinematics control algorithms, work with ROS, program in C++, and test modules in physical simulation platforms.",
        "location": "Boston, MA (On-site)",
        "type": "Internship"
    },
    {
        "id": "seed-3",
        "title": "SDE Intern",
        "company": "AppForge Technologies",
        "category": "Software Engineering",
        "experience_years": 0,
        "skills": ["React Native", "Flutter", "Node.js", "RESTful APIs", "Mobile App Architecture", "Backend Integration"],
        "description": "Join AppForge as an SDE Intern. You will contribute to our core mobile app architecture, implement seamless backend integration, write reusable React Native components, and design RESTful APIs.",
        "location": "New York, NY (Hybrid)",
        "type": "Internship"
    },
    {
        "id": "seed-4",
        "title": "Senior React Developer",
        "company": "WebCorp Solutions",
        "category": "Frontend Development",
        "experience_years": 5,
        "skills": ["React", "Redux", "Webpack", "TypeScript", "TailwindCSS", "HTML5", "CSS3"],
        "description": "We are seeking a Senior React Developer with 5+ years of production experience. You must be an expert in state management using Redux, bundle optimization with Webpack, and modern frontend design principles.",
        "location": "Remote (US)",
        "type": "Full-time"
    },
    {
        "id": "seed-5",
        "title": "IT Helpdesk Technician",
        "company": "SupportCorp",
        "category": "IT & Support",
        "experience_years": 1,
        "skills": ["Windows Server", "Active Directory", "Troubleshooting", "Network Support", "Customer Service"],
        "description": "Provide IT and support desk assistance to remote employees. Maintain Active Directory accounts, perform hardware troubleshooting, and configure local network routers.",
        "location": "Austin, TX (On-site)",
        "type": "Full-time"
    }
]

categories = ["Machine Learning", "Robotics", "Software Engineering", "Frontend Development", "IT & Support", "Data Science", "Cloud & DevOps", "Full Stack Development"]
companies = ["DeepMinded", "AeroVelo", "DataPulse", "NexWeb", "CloudShield", "SysAdmin Pro", "QuantumCode", "StackForge", "CyberGuard", "InnovaTech", "LogiCorp", "NetScale", "SoftGrid", "VectorLabs"]
skills_pool = {
    "Machine Learning": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Keras", "Transformers", "NLP", "LLMs", "Explainable AI", "Data Analysis"],
    "Robotics": ["C++", "Python", "ROS", "ROS2", "Kinematics", "Gazebo", "SLAM", "Path Planning", "Computer Vision", "Control Systems"],
    "Software Engineering": ["Python", "Java", "C#", "Go", "RESTful APIs", "PostgreSQL", "MongoDB", "Data Structures", "Docker", "Git"],
    "Frontend Development": ["JavaScript", "TypeScript", "React", "Next.js", "Vue", "Redux", "Webpack", "TailwindCSS", "CSS", "HTML"],
    "IT & Support": ["Troubleshooting", "Windows Server", "Linux", "Active Directory", "Network Support", "Hardware Management", "Jira", "Customer Service"],
    "Data Science": ["Python", "R", "Pandas", "SQL", "Tableau", "PowerBI", "Matplotlib", "Seaborn", "Machine Learning", "Statistics"],
    "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "GitHub Actions", "Linux", "Bash", "Prometheus", "Grafana"],
    "Full Stack Development": ["TypeScript", "Node.js", "React", "Express", "Next.js", "MongoDB", "PostgreSQL", "GraphQL", "Redis", "Docker"]
}

types = ["Full-time", "Contract", "Internship", "Part-time"]
locations = ["Remote (US)", "San Francisco, CA (Hybrid)", "Boston, MA (On-site)", "New York, NY (Hybrid)", "Austin, TX (On-site)", "Seattle, WA (Hybrid)", "Chicago, IL (Hybrid)", "Denver, CO (Remote)"]

jobs = list(seed_jobs)
for i in range(len(jobs) + 1, 151):
    category = random.choice(categories)
    company = random.choice(companies)
    job_type = random.choice(types)
    location = random.choice(locations)
    exp = 0 if job_type == "Internship" else random.randint(1, 6)
    
    # Select random skills matching category
    possible_skills = skills_pool[category]
    num_skills = random.randint(3, 6)
    selected_skills = list(set(random.sample(possible_skills, min(num_skills, len(possible_skills)))))
    
    title = f"{category} Engineer" if job_type != "Internship" else f"{category} Intern"
    if category == "Machine Learning":
        title = random.choice(["ML Engineer", "Machine Learning Researcher", "Computer Vision Specialist", "NLP Engineer", "Data Scientist (ML)"])
    elif category == "Robotics":
        title = random.choice(["Robotics Software Engineer", "Control Systems Engineer", "Perception Engineer", "SLAM Specialist"])
    elif category == "Software Engineering":
        title = random.choice(["Software Engineer", "Backend Developer", "Systems Programmer", "Java Developer", "SDE"])
    elif category == "Frontend Development":
        title = random.choice(["Frontend Engineer", "React Developer", "UI Developer", "Next.js Engineer"])
    
    if job_type == "Internship":
        title += " Intern"
        
    description = f"We are looking for a skilled {title} to join the team at {company}. In this role, you will apply technologies such as {', '.join(selected_skills[:-1])} and {selected_skills[-1]} to solve interesting problems. Candidates should have {exp} years of relevant experience."

    jobs.append({
        "id": f"job-{i}",
        "title": title,
        "company": company,
        "category": category,
        "experience_years": exp,
        "skills": selected_skills,
        "description": description,
        "location": location,
        "type": job_type
    })

with open("jobs_db.json", "w") as f:
    json.dump(jobs, f, indent=4)

print(f"Successfully generated {len(jobs)} jobs inside jobs_db.json")
