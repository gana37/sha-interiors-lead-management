# AI-Powered Lead Management System for SHA Interface Interiors

**Project Report**

**Prepared by:** Matta Ganesh  
**Project:** AI Agentic Engineer Intern – Assessment Project  
**Organization:** SHA Interface Interiors  
**Project Type:** AI-Powered CRM and Lead Management System  

**Live Application:** https://sha-interiors-lead-management-br7ctesnqk6iaktyakzsbz.streamlit.app/  
**GitHub Repository:** https://github.com/gana37/sha-interiors-lead-management  

---

## 1. Project Overview

The AI-Powered Lead Management System is a web-based application designed to help SHA Interface Interiors manage, organize, qualify, and track potential interior design customers.

In a typical interior design business, leads may come from different sources. Managing these leads manually can make it difficult to identify high-priority customers, maintain follow-up schedules, track customer responses, and understand overall business performance.

To address these challenges, I developed a centralized lead management application that combines customer information management, rule-based lead scoring, automated follow-up scheduling, reporting, and an AI-assisted interface.

The application is built using Python and Streamlit, with SQLite used for data storage. It is designed to work with sample data and does not require paid APIs for its core functionality.

## 2. Project Objectives

The main objectives of this project are:

1. Centralize customer lead information in one application.
2. Capture new leads through manual entry and CSV imports.
3. Automatically evaluate and prioritize leads.
4. Maintain customer records and lead statuses.
5. Schedule follow-up activities based on lead priority.
6. Prevent unnecessary follow-ups when customers respond or opt out.
7. Generate reports to understand lead performance.
8. Provide an AI-assisted interface for querying lead information.
9. Build a cost-effective solution using free and open-source technologies.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Web application and user interface |
| SQLite | Database for storing lead information |
| Pandas | Data processing and CSV operations |
| Python modules | Lead capture, scoring, and follow-up logic |
| Google Gemini API | Optional AI assistant integration |
| n8n | Optional workflow automation |
| Git and GitHub | Version control and source code hosting |
| Streamlit Community Cloud | Application deployment |

The core application can run locally without requiring a paid AI API or a live n8n connection.

## 4. Project Development – Step by Step

### Step 1: Understanding the Requirements

The first step was to understand the business requirements provided by SHA Interface Interiors.

The system needed to support:

- Lead collection.
- Lead qualification and scoring.
- CRM record management.
- Follow-up scheduling.
- Daily and weekly reporting.
- AI-assisted interaction.

Based on these requirements, I planned a modular application where each feature could operate independently while using a common lead database.

### Step 2: Dataset Preparation

I worked with an existing sample dataset and prepared a separate synthetic dataset for the interior design business.

The original education-sector dataset contained 9,240 records and was retained separately. It was not treated as actual interior design customer data.

A synthetic interior design dataset was generated with 250 fictional lead records.

The synthetic dataset includes fields such as:

- Lead ID
- Customer name
- Email address
- Phone number
- Location
- Property type
- Project requirements
- Budget
- Purchase readiness
- Lead source
- Lead status

The data was cleaned, validated, and organized before importing it into the CRM.

**Important:** The 250 records are fictional demonstration data, not real SHA customer records.

### Step 3: Database and Lead Management

I developed the database layer using SQLite.

The application supports:

- Adding new leads manually.
- Importing leads from CSV files.
- Validating email addresses and Indian phone numbers.
- Preventing duplicate lead records.
- Searching and filtering customer information.
- Updating and tracking lead records.
- Exporting lead information as CSV.

SQLite was selected because it is lightweight, free, and suitable for a demonstration application.

### Step 4: Lead Qualification and Scoring

I implemented a rule-based lead scoring engine to evaluate the quality and purchase readiness of each lead.

The scoring system uses four main factors:

| Scoring Factor | Maximum Score |
|---|---:|
| Budget suitability | 30 |
| Location suitability | 20 |
| Requirements clarity | 20 |
| Purchase readiness | 30 |
| **Total** | **100** |

The final score determines the lead priority:

- **High Priority:** 80–100
- **Medium Priority:** 50–79
- **Low Priority:** 0–49

For example, a customer with a suitable budget, supported location, clearly defined requirements, and strong purchase readiness receives a higher score.

The scoring logic is transparent and explainable. It is a rule-based system, not a machine learning prediction model.

The budget and location rules are configurable demonstration assumptions and would need confirmation from SHA Interface Interiors before production use.

### Step 5: Follow-Up Management

I developed a follow-up management module to help sales representatives track customer communication activities.

The system creates follow-up tasks based on lead priority.

**Demonstration follow-up schedules:**

| Priority | Follow-Up Schedule |
|---|---|
| High | 1, 3, and 7 days |
| Medium | 2, 5, and 10 days |
| Low | 7 and 14 days |

The application supports follow-up task tracking, communication templates, status updates, and simulated customer responses.

The system includes important stop conditions:

- Stop follow-ups when a customer responds.
- Stop when a customer opts out.
- Stop when the lead is marked Converted or Lost.
- Stop when a sales representative pauses follow-ups.

Duplicate follow-up task creation is also guarded against.

**Note:** Follow-ups are simulated in this demonstration. The application does not currently claim to send real WhatsApp messages, emails, or calls.

### Step 6: Workflow Automation with n8n

I prepared n8n workflow definitions for common CRM activities.

The included workflow files cover:

1. New lead notifications.
2. High-priority lead alerts.
3. Follow-up reminders.
4. Lead status updates.

These workflow definitions provide a foundation for connecting the application to external automation services.

The application also includes a dispatcher with a local fallback so that its core functionality does not depend on n8n being online.

The workflow JSON files are prepared for integration; a live external n8n connection is not claimed as completed.

### Step 7: Reports and Analytics

I developed a reporting and analytics module to help understand lead performance.

The dashboard provides information such as:

- Total number of leads.
- High-, medium-, and low-priority lead counts.
- Lead distribution by location.
- Lead status information.
- Lead scoring statistics.
- Follow-up activity information.

The reporting module supports daily, weekly, and custom reporting views, along with CSV export.

These reports help sales teams understand the lead pipeline and identify areas requiring attention.

### Step 8: AI Assistant

An AI assistant module was added to make it easier to interact with CRM information.

Users can ask questions such as:

- How many high-priority leads are available?
- Which leads are located in Hyderabad?
- Show the top five leads.
- What is the status of a particular customer?
- Help me draft a follow-up message.

The assistant is designed to use CRM information to answer lead-related questions.

Google Gemini API integration is optional. When an API key is not configured, the application uses a deterministic local fallback for supported queries.

The AI assistant is intended to assist users; important CRM changes should still be reviewed by the sales representative.

## 5. Application Modules

The completed application contains the following modules:

1. **Home Dashboard:** Displays overall lead statistics and business insights.
2. **Import Leads:** Imports customer information through CSV files.
3. **Add New Lead:** Allows users to create new customer records.
4. **View All Leads:** Provides lead search, filtering, and record management.
5. **AI Lead Scoring:** Evaluates and prioritizes leads.
6. **Follow-Up Management:** Displays scheduled tasks and follow-up statuses.
7. **Reports and Analytics:** Provides charts, summaries, and report exports.
8. **AI Assistant:** Supports natural-language questions about CRM information.
9. **Settings:** Provides configurable application settings.

## 6. System Architecture

The application follows a modular architecture.

**Application flow:**

Customer Lead Data → Lead Capture → Data Validation → SQLite Database → Lead Scoring → Follow-Up Management → Reports and AI Assistant

The main components are:

- **Frontend:** Streamlit interface.
- **Backend logic:** Python modules.
- **Database:** SQLite.
- **Data processing:** Pandas.
- **Optional AI service:** Google Gemini API.
- **Optional automation:** n8n.

The modular structure makes the system easier to maintain and extend.

## 7. Testing and Validation

Testing was performed throughout development to verify the application's core functionality.

The reported automated test results are:

| Test Suite | Tests Passed |
|---|---:|
| Lead capture and database | 9 |
| Lead scoring | 12 |
| Follow-up management | 8 |
| End-to-end testing | 10 |
| **Total** | **39** |

The test cases cover areas such as:

- Lead creation and validation.
- CSV import.
- Duplicate prevention.
- Lead scoring calculations.
- Follow-up scheduling.
- Follow-up stop conditions.
- Database operations.
- End-to-end application workflows.

The development test report recorded 39 out of 39 tests passing.

The demonstration database contains 250 synthetic leads and approximately 603 scheduled follow-up tasks.

## 8. Deployment

After completing the application, I uploaded the source code to GitHub and deployed the application using Streamlit Community Cloud.

**GitHub Repository:**

https://github.com/gana37/sha-interiors-lead-management

**Live Application:**

https://sha-interiors-lead-management-br7ctesnqk6iaktyakzsbz.streamlit.app/

The deployment uses:

- Repository: `gana37/sha-interiors-lead-management`
- Branch: `main`
- Main application file: `app.py`
- Python version: `3.12`

The application is accessible through a web browser.

## 9. Security and Cost Considerations

The project was designed to be cost-effective and suitable for a demonstration environment.

Important considerations include:

- SQLite avoids the need for a separate database server.
- Core lead management does not require a paid API.
- Synthetic data is used instead of real customer information.
- API keys should be stored in environment variables or deployment secrets.
- Real customer information should only be used with appropriate authorization.
- Follow-up communications are simulated in the current demonstration.
- External AI and automation services are optional.

Before production deployment, additional security controls, access management, backups, and data protection measures should be implemented.

## 10. Business Benefits

The proposed system can provide several benefits to SHA Interface Interiors:

1. **Centralized lead management:** Customer information can be managed in one place.
2. **Faster lead prioritization:** Sales representatives can identify high-priority prospects.
3. **Better follow-up tracking:** Scheduled activities help reduce missed follow-ups.
4. **Improved visibility:** Reports provide an overview of the sales pipeline.
5. **Reduced manual work:** CSV imports, scoring, and task scheduling reduce repetitive activities.
6. **AI-assisted interaction:** Users can ask questions about CRM information more easily.
7. **Cost-effective implementation:** The core system uses lightweight technologies and can operate without paid API services.

## 11. Limitations and Future Enhancements

The current project is a working demonstration and can be extended further.

Potential future improvements include:

- Integration with actual WhatsApp Business APIs.
- Email and SMS automation.
- Live n8n workflow deployment.
- Integration with a production database.
- User authentication and role-based access control.
- Advanced machine learning-based lead conversion prediction.
- Integration with website enquiry forms.
- Real-time notifications for sales representatives.
- Production-grade monitoring, backups, and security.

These improvements would help transform the demonstration into a production-ready lead management platform.

## 12. Conclusion

The AI-Powered Lead Management System was developed to demonstrate how AI-assisted tools and automation can improve the lead management process for an interior design business.

The project brings together lead capture, customer record management, rule-based qualification, follow-up scheduling, reporting, and an AI-assisted interface in one centralized application.

The development focused on simplicity, modularity, explainable scoring, cost-effectiveness, and reliable core functionality.

The final application has been deployed through Streamlit Community Cloud and its source code is available on GitHub.

This project demonstrates my practical understanding of Python application development, database management, AI-assisted systems, workflow automation concepts, testing, and application deployment.

---

**Project Links**

- Live Demo: https://sha-interiors-lead-management-br7ctesnqk6iaktyakzsbz.streamlit.app/
- GitHub: https://github.com/gana37/sha-interiors-lead-management

**End of Report**
