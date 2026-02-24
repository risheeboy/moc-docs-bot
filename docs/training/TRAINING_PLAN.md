# Training Plan — Ministry of Culture Staff

**Version:** 1.0.0
**Duration:** 6 weeks (3 batches × 2 weeks each)
**Audience:** All staff using the system
**Last Updated:** February 24, 2026

---

## Training Strategy

### Three Training Tracks

| Track | Audience | Duration | Delivery |
|---|---|---|---|
| **End-User** | All staff | 2 hours | Online workshop |
| **Administrator** | IT/ops team | 2 days | In-person hands-on |
| **Advanced** | Select staff | 3 days | Technical deep-dive |

### Batch Schedule

**Batch 1:** Week 1-2 (Cohort size: 20-30 people)
**Batch 2:** Week 3-4 (Cohort size: 20-30 people)
**Batch 3:** Week 5-6 (Cohort size: 20-30 people)

---

## End-User Training (2 hours)

### Objective
Enable all Ministry staff to use the chatbot and search features effectively.

### Pre-Training
- No prerequisites
- All staff welcome
- Internet connection required
- Modern browser (Chrome, Firefox, Safari, Edge)

### Agenda

**Session 1: Introduction (30 minutes)**

1. Welcome & overview (5 min)
   - What is the new AI assistant?
   - Why we built it
   - Privacy assurances

2. Demo walkthrough (15 min)
   - Live demonstration of chat
   - Show search in action
   - Answer initial questions

3. Q&A (10 min)
   - Address concerns
   - Set expectations

**Session 2: Hands-On Practice (60 minutes)**

1. Accessing the system (10 min)
   - Navigate to culture.gov.in
   - Find chat widget and search page
   - Mobile access

2. Using the chatbot (20 min)
   - Type a question
   - Read response with sources
   - Rate the response
   - Ask follow-up questions
   - Practice voice input/output

3. Using search (20 min)
   - Enter search query
   - Filter results
   - Navigate pages
   - View images and events
   - Export results

4. Tips & best practices (10 min)
   - How to ask better questions
   - Understanding confidence scores
   - Verifying information
   - Providing feedback

**Session 3: Wrap-up (30 minutes)**

1. Common questions (15 min)
   - Troubleshooting issues
   - What languages are supported?
   - How long are conversations kept?

2. Feedback (10 min)
   - Collect feedback forms
   - Email for follow-up questions

3. Resources (5 min)
   - Provide USER_MANUAL_EN.md link
   - Support email: arit-culture@gov.in

### Materials
- Slide deck (in English and Hindi)
- USER_MANUAL_EN.md and USER_MANUAL_HI.md
- Quick reference card (laminated)
- Feedback form (paper or online)

---

## Administrator Training (2 days)

### Objective
Equip IT staff to manage the system, handle user issues, and maintain operations.

### Prerequisites
- Familiarity with Linux/Docker (basic)
- Admin access to system
- Completion of end-user training

### Day 1: System Fundamentals

**Morning (4 hours)**

1. Architecture overview (1 hour)
   - System components and flow
   - How chat and search work
   - Document ingestion pipeline
   - Where data lives

2. System access & monitoring (2 hours)
   - Log in to admin dashboard
   - View health metrics
   - Monitor GPU usage
   - Check service status
   - Read audit logs

3. Hands-on: Dashboard exploration (1 hour)
   - Navigate to all sections
   - Create test user
   - View sample analytics
   - Practice filtering and exporting

**Afternoon (4 hours)**

1. Document management (2 hours)
   - Upload documents via admin interface
   - Bulk operations (add tags, delete)
   - Monitor ingestion progress
   - Handle failed uploads

2. Hands-on: Upload & manage documents (1.5 hours)
   - Upload a test PDF
   - Upload an image
   - Edit document metadata
   - Delete test documents

3. User management (0.5 hours)
   - Create new user accounts
   - Assign roles (editor, viewer)
   - Deactivate accounts

### Day 2: Operations & Troubleshooting

**Morning (4 hours)**

1. Monitoring & alerts (1.5 hours)
   - View real-time metrics in Grafana
   - Understand key performance metrics
   - Set up notifications
   - Interpret alert messages

2. Troubleshooting (2 hours)
   - Common issues and solutions
   - Where to find logs
   - How to restart services
   - When to escalate to vendor

3. Hands-on: Diagnose simulated issue (0.5 hours)
   - Review error logs
   - Identify problem
   - Take corrective action

**Afternoon (4 hours)**

1. Backups & recovery (2 hours)
   - Understanding backup strategy
   - Running manual backups
   - Verifying backups
   - Restore procedures

2. Security & compliance (1.5 hours)
   - User roles and permissions
   - Audit log review
   - Data retention policies
   - Incident response

3. Hands-on: Backup practice (0.5 hours)
   - Create manual backup
   - Verify backup integrity
   - Practice restore (to staging)

### Materials
- ADMIN_GUIDE.md
- DEPLOYMENT_GUIDE.md
- MONITORING_GUIDE.md
- TROUBLESHOOTING.md
- Operator playbook (runbooks)
- VM/sandbox for hands-on practice

---

## Advanced Technical Training (3 days)

### Objective
Deep technical knowledge for senior IT staff and developers.

### Prerequisites
- Linux/Docker experience (intermediate)
- Completion of admin training
- Python knowledge preferred

### Day 1: Architecture & Code

**Topics:**
1. System design deep-dive
   - RESTful API patterns
   - Service-oriented architecture
   - Data flow and state management
   - Concurrency and performance

2. Code walkthrough
   - API Gateway entry points
   - RAG service implementation
   - Database schemas
   - Key business logic

3. Extending the system
   - Adding new API endpoints
   - Custom document processors
   - Integration with external systems

### Day 2: Models & ML

**Topics:**
1. LLM serving (vLLM)
   - Quantization and inference
   - Parameter-efficient fine-tuning (LoRA)
   - Batch processing
   - Token accounting

2. Embedding models
   - BGE-M3 architecture
   - Vector search optimization
   - Similarity computation

3. Model evaluation
   - Metrics (F1, BLEU, NDCG)
   - Benchmark datasets
   - A/B testing

4. Hands-on: Fine-tune a model
   - Prepare training data
   - Start training job
   - Monitor progress
   - Evaluate results

### Day 3: Deployment & DevOps

**Topics:**
1. Docker & container orchestration
   - Dockerfile optimization
   - Image layering and caching
   - Resource limits and requests

2. Kubernetes (if migrating to K8s in future)
   - Deployment manifests
   - Service discovery
   - StatefulSet for databases
   - Horizontal Pod Autoscaling

3. CI/CD pipelines
   - Automated testing
   - Build optimization
   - Deployment automation
   - Rollback procedures

4. Hands-on labs
   - Build custom Docker image
   - Deploy to staging environment
   - Run performance tests
   - Execute rollback

### Materials
- ARCHITECTURE.md
- API_Reference.md
- Docker Compose source code
- Jupyter notebooks with examples
- Code repository access
- Performance testing toolkit

---

## Training Schedule

### Week 1: Batch 1 (End-users)
- Monday: End-user training session (2 hours)
- Tuesday-Friday: Open office hours for questions
- Friday: Collect feedback

### Week 2: Batch 1 (Admins) + Batch 2 (End-users)
- Monday-Tuesday: Admin training (2 days)
- Wednesday: End-user training for Batch 2
- Thursday-Friday: Support sessions

### Week 3-4: Similar pattern with Batch 2 Admins + Batch 3 End-users

### Week 5-6: Advanced training for selected staff

---

## Training Delivery Methods

### In-Person (Recommended)

**Venue:** NIC training facility or Ministry office
**Equipment:**
- Projector and screen
- 1 computer per 2 participants (hands-on labs)
- Internet connectivity
- Power outlets

**Schedule:**
- Start: 10 AM, End: 5 PM (with breaks)
- Lunch: 1 PM - 2 PM
- Breaks: 15 min mid-morning, 15 min mid-afternoon

### Hybrid (Backup)

**Video Conference:** Zoom, Teams, or Cisco Webex
**Hands-on:** Participants use laptops with shared staging environment
**Asynchronous:** Recorded sessions for those unable to attend

### Online Self-Paced (For individual learners)

**Materials:**
- Video tutorials (5-10 min each)
- Interactive documentation
- Quiz/knowledge checks
- Certification upon completion

---

## Evaluation & Certification

### End-User Training
- Post-training quiz (5 questions)
- Practical demonstration (use search and chat)
- Feedback form
- **Certificate:** "Certified AI Assistant User"

### Administrator Training
- Written exam (30 questions, 80% pass)
- Hands-on lab assessment
- Case study troubleshooting
- **Certificate:** "Certified Administrator, RAG-QA System"

### Advanced Training
- Code review of written assignment
- Design proposal for new feature
- Performance optimization challenge
- **Certificate:** "Advanced Technical Certification"

---

## Ongoing Support

### Office Hours
- **When:** Every Friday 2-4 PM
- **Duration:** 12 weeks (3 months post-launch)
- **Format:** Virtual (Zoom)
- **Topics:** Q&A, advanced questions, feedback

### User Forum
- **Platform:** Internal Slack channel #rag-qa-support
- **Moderation:** IT team
- **Response time:** <24 hours for questions

### Monthly Newsletter
- New features and updates
- Tips and best practices
- Usage analytics and trends
- Maintenance windows

---

## Training ROI Metrics

**Success measures:**
- 95% of staff complete training
- 80% pass knowledge assessment
- Increase in system usage (+200% first month)
- Reduction in support tickets (post-training)
- User satisfaction > 4/5 stars

---

## Trainer Qualifications

**Required:**
- Deep knowledge of system
- Excellent communication skills
- Ability to explain complex concepts simply
- Experience with audience (government staff)

**Recommended:**
- Previous training/teaching experience
- Background in AI/ML (for advanced track)
- Customer support background

---

## Contingency Plan

**If trainer unavailable:**
1. Use recorded video training
2. Provide detailed self-study materials
3. Schedule makeup session within 1 week
4. One-on-one catch-up sessions

**If system unavailable:**
1. Use staging/demo environment
2. Proceed with non-hands-on content
3. Reschedule hands-on labs
4. Provide extended office hours

---

**Training Budget (est. for all 3 batches):**
- Trainer time: 80 hours
- Materials printing: 5,000 INR
- Venue rental: 20,000 INR
- Refreshments: 15,000 INR
- **Total: ~200,000 INR**

---

**Questions?** Contact: arit-culture@gov.in

**Last Updated:** February 24, 2026
