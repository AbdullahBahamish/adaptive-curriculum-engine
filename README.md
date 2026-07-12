# AI Curriculum Recommendation System

## 1. Project Title

**AI Curriculum Recommendation System: An Intelligent Platform for Personalised Academic Roadmaps Based on Global University Curricula**

---

## 2. Abstract

The AI Curriculum Recommendation System is an intelligent educational platform designed to assist students, universities, and academic advisors in constructing structured learning roadmaps. By analysing curricula from prestigious universities worldwide, the system identifies knowledge gaps, prerequisite relationships, and essential competencies required for a chosen academic or career objective.

Unlike traditional recommendation systems that merely suggest courses, this platform generates comprehensive learning pathways by considering prerequisite dependencies, topic importance, skill acquisition, estimated learning time, and institutional curriculum comparisons. The architecture has been designed to accommodate future integration with machine learning models, knowledge graphs, and large language models.

---

## 3. Motivation

Students frequently encounter difficulties when determining what to learn, in which sequence, and to what depth. Academic programmes differ substantially between universities, while online learning resources often lack coherent progression.

This project addresses these challenges by providing an intelligent recommendation engine capable of synthesising curricula from multiple institutions into a unified, personalised roadmap. The long-term objective is to reduce uncertainty in educational planning while promoting evidence-based learning pathways informed by internationally recognised academic standards.

---

## 4. Features

* Personalised learning roadmap generation
* Curriculum comparison across multiple universities
* Prerequisite dependency analysis
* Topic importance scoring
* Skill extraction and recommendation
* Semester-by-semester roadmap planning
* University curriculum database
* Course and topic relationship modelling
* Estimated learning duration calculation
* Extensible object-oriented architecture
* Machine learning integration support
* Knowledge graph compatibility
* Exportable roadmap generation
* Developer-friendly modular design

---

## 5. System Architecture

The system follows a modular architecture in which each component is responsible for a specific stage of the recommendation pipeline.

```
Student Profile
        │
        ▼
Curriculum Database
        │
        ▼
Curriculum Parser
        │
        ▼
Knowledge Representation
        │
        ▼
Recommendation Engine
        │
        ▼
Roadmap Generator
        │
        ▼
Visualisation / Export
```

Primary modules include:

* Student Management
* University Repository
* Course Repository
* Topic Repository
* Skill Repository
* Recommendation Engine
* Roadmap Generator
* Data Export Module

---

## 6. Data Model

The platform is centred around several core entities.

### Student

Represents an individual learner together with completed courses, acquired skills, learning objectives, and academic profile.

### University

Stores institutional information together with its curriculum and course catalogue.

### Course

Represents a university course including prerequisites, topics, credits, and learning outcomes.

### Topic

Represents an individual concept or subject covered by one or more courses.

### Skill

Represents practical or theoretical competencies developed through course completion.

### Resource

Contains recommended books, articles, videos, and online materials associated with particular topics.

### Roadmap

Represents the generated personalised learning pathway organised into sequential stages.

---

## 7. Installation

Clone the repository.

```bash
git clone https://github.com/AbdullahBahamish/adaptive-curriculum-engine.git
```

Navigate to the project directory.

```bash
cd AI-Curriculum-Recommendation-System
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate the environment.

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the application.

```bash
python main.py
```

---

## 8. Example Usage

Create a student profile.

```python
student = Student(
    name="Abdullah",
    university="Hadhramout University"
)
```

Load university curricula.

```python
universities = load_universities()
```

Generate recommendations.

```python
roadmap = generate_roadmap(student, universities)
```

Display the roadmap.

```python
print(roadmap)
```

---

## 9. Folder Structure

```
AI-Curriculum-Recommendation-System/

├── data/
│
├── docs/
│
├── src/
│   ├── models/
│   ├── recommendation/
│   ├── services/
│   ├── utils/
│   └── visualization/
│
├── tests/
│
├── notebooks/
│
├── requirements.txt
├── README.md
├── LICENSE
└── main.py
```

---

## 10. Future Improvements

Future development directions include:

* Machine learning–based recommendation ranking
* Knowledge graph construction
* Curriculum similarity analysis
* Automatic syllabus extraction from university websites
* PDF curriculum parsing
* Career-oriented recommendation engine
* Scholarship recommendation module
* Large language model integration
* Interactive web application
* REST API
* Mobile application
* Real-time curriculum updates
* Learning analytics dashboard
* Recommendation explainability
* Reinforcement learning for adaptive roadmap optimisation

---

## 11. License

This project is distributed under the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and its associated documentation files to use, modify, distribute, and publish the software, subject to the conditions specified in the license.
