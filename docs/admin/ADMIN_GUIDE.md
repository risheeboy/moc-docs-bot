# Admin Guide

**Version:** 1.0.0
**Audience:** Administrators & Content Managers
**Last Updated:** February 24, 2026

---

## Dashboard Access

**URL:** `https://culture.gov.in/admin`

**Login:**
1. Email: your-email@culture.gov.in
2. Password: (provided during account creation)
3. Two-factor authentication (if enabled)

---

## Admin Roles & Permissions

| Role | Permissions | Use Case |
|---|---|---|
| **Admin** | All operations, user management, system config | Site administrator |
| **Editor** | Document management, content updates, analytics | Content manager |
| **Viewer** | Read-only analytics, audit logs | Executive, auditor |
| **API Consumer** | Chat, search, feedback only | External integrations |

---

## Dashboard Overview

### Key Metrics (Home)

- **Active Users:** Current logged-in users
- **Conversations Today:** Chat volume
- **Documents:** Total ingested documents
- **Avg Response Time:** API latency (target <2s)
- **Error Rate:** System health
- **GPU Utilization:** Real-time GPU memory usage

### Navigation Menu

1. **Conversations** — View and manage user chats
2. **Documents** — Upload, delete, manage documents
3. **Analytics** — Usage metrics and insights
4. **Models** — Fine-tuning and evaluation
5. **Ingestion Jobs** — Monitor scraping progress
6. **Users** — Manage staff accounts
7. **Settings** — Configuration and preferences
8. **Audit Logs** — Compliance and security

---

## Document Management

### Upload Documents

1. **Documents** → **Upload New**
2. Select file (PDF, DOCX, PPTX, images)
3. Add metadata:
   - **Title** (required)
   - **Description** (optional)
   - **Language** (English/Hindi)
   - **Source URL** (if applicable)
   - **Tags** (heritage, monuments, etc.)
4. Click **Upload**
5. System shows: `Status: Processing` → `Completed`
6. Takes 2-10 minutes depending on file size

### Delete Documents

1. **Documents** → Search for document
2. Click **Delete** button
3. Confirm: "This action cannot be undone"
4. Document removed from search and vector DB

### View Document Details

1. Click document title
2. See:
   - Extracted text
   - Embeddings status
   - Source metadata
   - Related documents
3. Edit metadata or description

### Bulk Operations

1. Select multiple documents (checkboxes)
2. **Bulk Actions** → Choose:
   - Add tags
   - Change language
   - Change status
   - Delete

---

## Data Ingestion

### Configure Scraping Targets

1. **Ingestion** → **Targets**
2. Add Ministry website URLs:
   ```
   https://culture.gov.in
   https://asi.nic.in
   https://sangeet-nrityam.gov.in
   ```
3. Set spider type: Auto, Culture, ASI, etc.
4. Set crawl depth (1-5 levels)
5. Save

### Start Ingestion Job

1. **Ingestion** → **New Job**
2. Select targets to crawl
3. Options:
   - **Force rescrape:** Re-crawl even if recently done
   - **Max concurrent spiders:** Balance speed vs. load
4. Click **Start**
5. Monitor progress in real-time

### Monitor Job Status

Progress displayed:
- Pages crawled / total
- Documents ingested
- Errors encountered
- Estimated time remaining

---

## Analytics & Reporting

### Conversation Analytics

**Metrics:**
- Total conversations
- Total turns
- Average response time
- Languages used
- Top queries
- User satisfaction (ratings)

**Actions:**
- Export to CSV
- Filter by date range
- View trends over time

### Search Analytics

**Metrics:**
- Search volume
- Unique users
- Average results per search
- Popular search terms
- Top content types accessed

### Document Analytics

**Metrics:**
- Documents per source
- Language distribution
- Ingestion trends
- Size distribution

---

## Model Management

### View Models

1. **Models** → **Installed**
2. Shows:
   - Model name and version
   - Parameters (8B, 12B, etc.)
   - Status (loaded, unloaded)
   - GPU memory usage
   - Last used date

### Fine-tune Model

1. **Models** → **Fine-tune**
2. Select base model (Llama, Mistral, etc.)
3. Upload training dataset (JSONL format)
4. Set hyperparameters:
   - LoRA rank (16-64)
   - Learning rate (1e-4 to 1e-3)
   - Epochs (2-5)
5. Click **Start Training**
6. Monitor progress (can take 1-4 hours)

### Evaluate Model

1. **Models** → **Evaluate**
2. Select model version
3. Upload evaluation dataset
4. Select metrics:
   - Exact match
   - F1 score
   - BLEU
   - NDCG
   - Hallucination rate
5. View results with score and recommendations

---

## User Management

### Create User

1. **Users** → **New User**
2. Enter:
   - Email (ministry email)
   - Full name
   - Department
   - Role (admin/editor/viewer)
   - Send invite: Yes/No
3. System generates temporary password
4. User receives email with login link

### Manage Permissions

1. Click user name
2. **Permissions** tab
3. Toggle access for:
   - Chat management
   - Document upload
   - Analytics view
   - Model training
   - User management

### Deactivate User

1. Click user
2. **Deactivate** button
3. User cannot log in but data preserved
4. Can reactivate later

---

## System Configuration

### Settings Overview

1. **Settings** → **General**
2. Configure:
   - Organization name
   - Default language
   - Timezone
   - Logo and branding

### API Configuration

1. **Settings** → **API**
2. Manage:
   - Rate limits per role
   - Token expiration times
   - CORS allowed origins
   - API documentation

### Email Notifications

1. **Settings** → **Email**
2. Configure:
   - Admin alert email
   - Notification triggers
   - Digest frequency

---

## Monitoring & Health

### System Health

**Check real-time health:**

1. **Settings** → **System Health**
2. Shows status of:
   - PostgreSQL
   - Redis
   - Milvus
   - S3
   - LLM service
   - GPU status

**Green = Healthy, Yellow = Degraded, Red = Down**

### Service Logs

1. **Monitoring** → **Logs**
2. Filter by:
   - Service (api-gateway, rag-service, etc.)
   - Log level (INFO, WARNING, ERROR)
   - Time range
3. Search for specific errors
4. Export for analysis

### Performance Metrics

1. **Monitoring** → **Metrics**
2. View:
   - API response times
   - Token generation rate
   - Cache hit rate
   - Error rate

---

## Troubleshooting

### Service Down

1. Check **System Health** dashboard
2. If red, click service name for logs
3. Look for error messages
4. If stuck, click **Restart Service**
5. Monitor health until green

### High Latency

1. Check **Metrics** → API latency
2. If high, check:
   - GPU utilization (should be <95%)
   - Database queries (check slow log)
   - Network connectivity
3. Reduce concurrency if needed

### Disk Full

1. Check **Settings** → **Storage**
2. See disk usage by component
3. If >90%, delete old documents or clear caches
4. Or expand storage

---

## Backup Management

### Automatic Backups

Enabled by default:
- PostgreSQL: Daily at 2 AM
- Milvus: Daily at 2 AM
- S3: Continuous sync
- Redis: Hourly snapshots

### Manual Backup

1. **Settings** → **Backup**
2. Click **Backup Now**
3. Backup created and stored in `/mnt/backup`
4. Shows size and completion status

### Restore Backup

1. **Settings** → **Backup** → **Restore**
2. Select backup date
3. Click **Restore**
4. System restores and restarts services
5. Monitor logs during restore

---

## Audit & Compliance

### Audit Logs

1. **Audit Logs** → View all actions
2. Filter by:
   - User
   - Action (create, update, delete)
   - Resource type
   - Date range
3. Export to CSV for compliance

### Example Audit Events

- Document uploaded
- User role changed
- Model fine-tuning started
- Backup created
- Configuration changed
- API key generated

---

## Common Tasks

### Task: Add new content source

1. Go to **Ingestion** → **Targets**
2. Click **Add Target**
3. Enter URL: `https://new-site.nic.in`
4. Set crawl depth: 3
5. Click **Save**
6. Go to **New Job** → select new target → **Start**

### Task: Give editor access to staff member

1. Go to **Users** → select user
2. Change role from "Viewer" to "Editor"
3. Save
4. User now has document upload access

### Task: Export chat analytics

1. Go to **Analytics** → **Conversations**
2. Select date range
3. Click **Export as CSV**
4. Downloads to computer

### Task: Evaluate new model version

1. Upload training data to S3
2. Go to **Models** → **Fine-tune**
3. Select base model, upload data
4. Click **Start Training**
5. After 2-4 hours, go to **Evaluate**
6. Select new model version
7. View metrics and compare to baseline

---

## Best Practices

1. **Regular Backups:** Verify backups complete daily
2. **Monitor Health:** Check dashboard every morning
3. **Review Audit Logs:** Weekly for security
4. **Update Content:** Rescrape sources monthly
5. **Test Updates:** Use staging before production
6. **Archive Old Data:** Delete docs >1 year old quarterly
7. **Review Analytics:** Monthly for insights

---

**For support:** arit-culture@gov.in
**Last Updated:** February 24, 2026
