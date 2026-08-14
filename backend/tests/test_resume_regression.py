"""
Regression test for the PII detector against the user's resume.
Ensures we have high precision and zero false positives on known
technical terms, projects, and education.
"""

import pytest
from app.services.pii_detector import detect_pii

RESUME_TEXT = """Chandra Mohan Gadige

LinkedIn: linkedin.com/in/chandu7313 | Email: chandrgadige@gmail.com | GitHub: github.com/chandu7313 | Mobile: +91-9000540571

PROFESSIONAL SUMMARY

Full-stack developer skilled in React, Node.js, and NestJS, with hands-on experience building event-driven microservices, RESTful API design, AI-integrated platforms, and CI/CD deployment pipelines across agriculture, business-intelligence, and campus-management domains.

TECHNICAL SKILLS

Languages: JavaScript, Python, Java, C++, SQL

Frameworks: React, Node.js, HTML5, CSS3, Tailwind CSS, Express, Spring Boot, NumPy, Pandas

Tools & Platforms: Git, GitHub, Postman, MongoDB, PostgreSQL, Docker, Maven, AWS

Core CS Skills: SQL, OOP, Data Structures and Algorithms, NoSQL, Linux OS

Soft Skills: Problem Solving, Adaptability, Quick Learner, Team Player

PROJECTS

Kisan Mithar - Smart Agriculture & Farmer Advisory Platform | GitHub | Live Jan '26 - Present

Built a cloud-native full-stack agriculture platform using microservices, integrating AI-powered crop disease detection, soil analysis, expert consultation, market insights, and e-commerce.

Engineered 15+ event-driven microservices with REST APIs, RabbitMQ, Redis, Docker, and CI/CD to build a scalable and resilient backend on AWS EC2.

Integrated Gemini AI and Plant.id AI services for intelligent crop disease detection, real-time notifications, role-based authentication across 13 user roles, and live communication to enhance platform automation and user experience.

Tech: Node.js, Express.js, React.js, PostgreSQL, Redis, RabbitMQ, Docker, Nginx, Jenkins, AWS EC2

VentureForge AI - Multi-Agent AI Business & Intelligence System | GitHub | Live May '26 - Jun '26

Designed an AI-powered business platform that transforms startup ideas into investor-ready business blueprints through automated market research, financial forecasting, and compliance analysis.

Implemented a scalable multi-agent AI architecture with parallel orchestration, asynchronous job processing, and real-time progress streaming.

Integrated multiple LLMs and AI APIs across 60+ RESTful API endpoints for market research, competitor analysis, financial forecasting, risk analysis, business planning, and document generation.

Tech: Next.js, NestJS, PostgreSQL, Redis, BullMQ, Docker, Nginx, Tailwind CSS, Prometheus, Grafana

CampusOne - University Management System | GitHub | Live Sep '25 - Oct '25

Developed a centralized institutional management platform with hierarchical role-based access control (HRBAC) to streamline identity, user lifecycle, and campus administration.

Designed a secure identity and access management system (IAM) featuring 10-level role hierarchies, JWT authentication, refresh tokens, HTTP-only cookies, and comprehensive audit logging.

Enabled scalable user provisioning through automated username generation, role-specific workflows, registration ID generation, and a Table-per-Role database architecture.

Tech: Node.js, Express.js, React.js, PostgreSQL, Sequelize ORM, JWT, Bcrypt, Cookies

TRAINING

Full-Stack Product Engineering Program - NXTWAVE Jan '23 - Present

Completed hands-on training in MERN Stack, building production-ready applications with scalable backend architectures and RESTful APIs.

Gained proficiency in Python, JavaScript, React.js, Node.js, Express.js, MongoDB, SQL, and software engineering best practices through project-based learning.

Enhanced advanced problem-solving skills through Data Structures & Algorithms, covering graphs, trees, dynamic programming, greedy algorithms, recursion, and algorithmic optimization.

CERTIFICATIONS

React JS Certification - NXTWAVE | Nov '25

Responsive Web Design Certification - NXTWAVE | Jul '23

ACHIEVEMENTS

LeetCode Programmer - Solved 80+ DSA problems across arrays, strings, trees, graphs, and dynamic programming, strengthening problem-solving, algorithm design, and time-space complexity optimization.

EDUCATION

Lovely Professional University, Punjab, India Aug '23 - Present

Bachelor of Technology - Computer Science and Engineering; CGPA: 7.79

Government Junior College, Gadwal, Telangana Apr '21 - Mar '23

Intermediate; Percentage: 95.6%"""

def test_resume_precision_and_recall():
    entities = detect_pii(RESUME_TEXT)
    
    # Check that we only detected the true PII + 2 URLs
    assert len(entities) == 5, f"Expected 5 entities, got {len(entities)}"
    
    # Check types
    types = [e.type for e in entities]
    assert "PERSON" in types
    assert "EMAIL" in types
    assert "PHONE" in types
    assert types.count("URL") == 2
    
    # Explicitly check for false positives
    detected_values = [e.value for e in entities]
    assert "Spring Boot" not in detected_values
    assert "Data Structures" not in detected_values
    assert "Computer Science" not in detected_values
    assert "Lovely Professional" not in detected_values
    assert "Government Junior" not in detected_values
