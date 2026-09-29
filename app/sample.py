"""Entirely fictional demo. Never contains the user's uploaded resume."""
from .parsing import parse_text

SAMPLE_JD = '''Senior Java Full Stack Developer - Example Organization
Build reliable applications using Java, Spring Boot, React and TypeScript. Design REST APIs and event-driven microservices using Kafka. Work with PostgreSQL, Docker and Kubernetes on AWS. Maintain automated tests with JUnit and Mockito, CI/CD with GitHub Actions, and operational monitoring. Collaborate with stakeholders to clarify requirements, review designs and improve accessibility. Document technical decisions and communicate clearly across engineering teams. Experience with Terraform and OAuth is useful. GraphQL is preferred. Candidates should be able to explain project trade-offs with concrete examples from their own work.'''


def sample_document():
    lines = ['Alex Morgan', 'Senior Full Stack Developer', 'Email: alex.morgan@example.com',
             'Location: Austin, TX | Phone: +1 (555) 010-2020', 'PROFESSIONAL SUMMARY']
    summaries = [
        'Full stack developer with experience delivering Java services and responsive web applications across several fictional enterprise projects. This sample is for testing the application; replace it with your own verified career history.',
        'Designs Spring Boot services around clear interfaces, validation rules and observable failure modes, pairing backend implementation with React and TypeScript interfaces for operational users.',
        'Works with product stakeholders to turn ambiguous requests into reviewable delivery increments, documenting assumptions and keeping business decisions separate from infrastructure concerns.',
        'Builds maintainable automated tests and deployment checks so teams can review changes with confidence, reproduce reported problems and identify regressions before releasing new versions.',
        'Uses PostgreSQL, REST APIs and Kafka to connect workflow components, choosing synchronous or asynchronous communication according to consistency, failure handling and user-experience requirements.',
        'Supports cloud deployments with Docker, Kubernetes and AWS while maintaining clear operational documentation for configuration, access control, monitoring and incident response.',
        'Collaborates through design reviews, pairing and written proposals to make technical trade-offs visible and keep project teams aligned on constraints and acceptance criteria.',
        'Reviews accessibility and responsive behavior in everyday UI work, including keyboard navigation, validation feedback and predictable recovery from unsuccessful requests.'
    ]
    lines += ['- ' + s for s in summaries]
    lines += ['TECHNICAL SKILLS',
              'Languages: Java, TypeScript, JavaScript, SQL, Python',
              'Backend: Spring Boot, REST, Microservices, Hibernate, JPA',
              'Frontend: React, Angular, HTML, CSS, accessibility',
              'Data: PostgreSQL, Redis, Kafka',
              'Cloud: AWS, Docker, Kubernetes, Terraform',
              'Delivery: GitHub Actions, Jenkins, CI/CD, Git',
              'Testing: JUnit, Mockito, Selenium, integration testing',
              'Security: OAuth, JWT, authorization, secure configuration',
              'PROFESSIONAL EXPERIENCE']
    jobs = [
        ('Meridian Systems (fictional)', 'Senior Full Stack Developer', '2023 - Present', 'Operations Workspace', 'operations'),
        ('Cedar Digital (fictional)', 'Full Stack Developer', '2020 - 2023', 'Service Coordination Portal', 'service coordination'),
        ('Northwind Labs (fictional)', 'Java Developer', '2017 - 2020', 'Customer Account Platform', 'customer accounts'),
        ('Harbor Software (fictional)', 'Application Developer', '2014 - 2017', 'Internal Reporting Tools', 'reporting')
    ]
    bullets = [
        'Designed Java and Spring Boot services for {area}, separating business rules, persistence and external integration layers so changes could be reviewed and tested independently. Documented interface contracts and exception behavior alongside implementation decisions.',
        'Built React and TypeScript screens for the {project}, translating product requirements into accessible forms, review panels and task-status views. Added clear loading, empty and error states to make long-running workflows understandable to users.',
        'Implemented REST endpoints with request validation, consistent error responses and stable pagination behavior. Worked with consuming teams to clarify data ownership, compatibility expectations and the rollout of changes to shared interfaces.',
        'Developed PostgreSQL queries and schema updates for {area} workflows, reviewing indexes and transaction boundaries against actual access patterns. Added migration checks and documented rollback considerations for database changes.',
        'Created JUnit and Mockito tests around business decisions, boundary conditions and integration failures. Added fixtures for representative user workflows and used code reviews to keep tests readable and useful during future maintenance.',
        'Integrated Kafka events for asynchronous workflow updates, defining event payloads, consumer retry behavior and failure handling with downstream teams. Kept synchronous validation separate from work that could safely complete in the background.',
        'Containerized services with Docker and maintained Kubernetes deployment configuration, including resource settings, readiness checks and environment-specific variables. Reviewed changes with the platform team before promoting them between environments.',
        'Maintained CI/CD workflows in GitHub Actions and Jenkins to compile code, run tests and assemble release artifacts. Added explicit failure messages and documented manual recovery steps for exceptional deployment conditions.',
        'Implemented OAuth-based access checks and JWT validation in service boundaries. Reviewed which roles could read or modify operational records and added tests for unauthorized requests rather than relying only on interface controls.',
        'Worked with product and design partners to review {area} journeys before development, identifying missing requirements and recording trade-offs. Broke work into increments with clear acceptance criteria and reviewable outcomes.',
        'Added application logs and monitoring for important workflow transitions, external service errors and request latency. Wrote troubleshooting notes so another engineer could connect user-reported symptoms with relevant operational evidence.',
        'Investigated production defects by reproducing the original request, comparing expected and observed state transitions and reviewing available logs. Added regression coverage for resolved problems and shared the findings in team reviews.',
        'Reviewed pull requests for readability, transaction safety and consistent API behavior. Suggested smaller changes where necessary and used pairing sessions to transfer context without leaving critical implementation knowledge with one person.',
        'Prepared release notes, operational runbooks and support handoffs for the {project}. Documented known limitations, configuration dependencies and verification steps so releases could be evaluated against an explicit checklist.',
        'Refined expensive data-access paths after examining representative request traces and database execution plans. Evaluated caching and batching selectively, keeping invalidation behavior and correctness requirements visible during design review.'
    ]
    for company, role, dates, project, area in jobs:
        lines += [f'CLIENT: {company} | {dates}', f'ROLE: {role}', f'PROJECT: {project}', 'RESPONSIBILITIES']
        lines += ['- ' + b.format(area=area, project=project) for b in bullets]
        lines += ['ENVIRONMENT', 'Java, Spring Boot, React, TypeScript, PostgreSQL, Docker, Git, JUnit, REST APIs']
    lines += ['EDUCATION', 'Example degree - replace with your institution and completion details.',
              'CERTIFICATIONS', 'Add only credentials you have earned. This fictional profile contains no certification claims.']
    document, _ = parse_text('\n'.join(lines))
    for b in document.blocks:
        if b.text.startswith(('Languages:', 'Backend:', 'Frontend:', 'Data:', 'Cloud:', 'Delivery:', 'Testing:', 'Security:')):
            b.kind = 'skill'
    return document.model_dump()
