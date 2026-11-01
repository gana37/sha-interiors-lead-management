# SHA Interface Interiors &mdash; 5 to 7 Minute Demonstration Script

This structured script is designed for live walkthroughs, assessments, or client presentations.

---

### Step 1: Introduction & Executive Dashboard (1 Minute)
* **Navigate to:** `Home Dashboard`
* **Talking Points:**
  - Introduce **SHA Interface Interiors Lead Management System** as an AI-powered intelligence platform tailored to residential and commercial interior design.
  - Highlight the top KPI cards: 250 active CRM leads, pipeline stages (55 New, 70 Qualified, 81 Follow-up, 26 Converted, 18 Lost).
  - Point to the AI Qualification metrics: **Average Score of 72.4/100**, with **94 High Priority leads** ready for immediate sales rep outreach.
  - Show the Priority Distribution Bar Chart and City Inquiries table.

---

### Step 2: Ingesting & Deduplicating Inquiries (1 Minute)
* **Navigate to:** `Import Leads`
* **Talking Points:**
  - Explain multi-channel intake. Click the **"Quick Import Synthetic Leads"** tab.
  - Demonstrate deduplication: click **"Import 250 Synthetic Leads"**. Notice that the system detects all 250 records already exist in SQLite and safely skips them with zero duplicate records created.
  - Explain the Data Segregation Guardrail: show that attempting to import the legacy education benchmark dataset (`Leads.csv`) is rejected to protect CRM integrity.

---

### Step 3: Capturing a New Customer with Real-Time AI Scoring (1.5 Minutes)
* **Navigate to:** `Add New Lead`
* **Action:** Enter a live customer inquiry:
  - **Customer Name:** `Vikramaditya Roy`
  - **Phone:** `+91 98450 77123`
  - **Email:** `vikram.roy@example.com`
  - **City:** `Bangalore`
  - **Lead Source:** `Direct Walk-in`
  - **Project Type:** `Villa`
  - **Budget Range:** `Above ₹25 lakh`
  - **Property Status:** `Ready to Move`
  - **Project Timeline:** `Immediately`
  - **Scope of Work:** `Full Turnkey Interior`
  - **Purchase Readiness:** `Ready to Start`
  - **Notes:** `Looking for luxury Italian marble flooring, master bedroom walk-in closet, and smart home lighting.`
* **Action:** Click **Submit & Save Customer Enquiry**.
* **Talking Points:**
  - Observe instant feedback: Lead assigned ID `SHA-2026-0252`.
  - Notice the **instant AI Qualification Banner**: Classified as **High Priority (100/100 Points)** with a generated plain-English rationale explaining that the customer is ready to start with a prime budget in a primary service hub.

---

### Step 4: AI Qualification Engine & Explainability (1 Minute)
* **Navigate to:** `AI Lead Scoring`
* **Talking Points:**
  - Demonstrate the 100-point transparent formula: Budget (30), Location (20), Requirements (20), Readiness (30).
  - Filter by **"High"** Priority. The table instantly sorts leads by score.
  - Select any lead from the dropdown to inspect the **Explainable Scoring Breakdown**.
  - Show the 4 individual factor cards (`Budget Suitability`, `Location Suitability`, `Requirements Clarity`, `Purchase Readiness`) and the clear explanation.
  - Emphasize: **Zero language model hallucination** &mdash; scoring is 100% deterministic and auditable.

---

### Step 5: Follow-Up Management & Stop Condition Simulation (1.5 Minutes)
* **Navigate to:** `Follow-up Management`
* **Talking Points:**
  - Show the 600+ scheduled touchpoint tasks generated across High, Medium, and Low priority cadences.
  - Filter by **"Scheduled"** and pick any upcoming WhatsApp or Phone task.
  - Click **"Simulate Send Message"**: observe that the task transitions to **Sent**, logs the timestamp in `Asia/Kolkata` time, and records an entry in `LEAD_ACTIVITY_LOG`.
  - Try clicking **"Simulate Send Message"** again: observe the **Idempotency Guard** in action, preventing duplicate dispatches.
* **Demonstrate the Stop Condition:**
  - Click the **"Customer Response Simulation"** tab.
  - Select the client who was just messaged. Enter a realistic customer response: *"Hi, I received your message. I want to book a design consultation this Sunday."*
  - Click **"Record Customer Response & Halt Automated Outreach"**.
  - Show that future automated tasks are **cancelled immediately**, preventing awkward automated follow-ups after the client has engaged.

---

### Step 6: Reports & Conversion Analytics (30 Seconds)
* **Navigate to:** `Reports and Analytics`
* **Talking Points:**
  - Review the **9 analytical dimensions**: Leads by City, Project Type, Budget Range, Lead Source, and Daily/Weekly creation trends.
  - Explain the documented conversion rate calculation: **Engaged Conversion Rate** (13.33%) vs **Overall Conversion Rate** (10.4%).
  - Show the **1-click CSV Export** button.

---

### Step 7: AI Assistant & Wrap-Up (30 Seconds)
* **Navigate to:** `AI Assistant`
* **Talking Points:**
  - Click the prompt button: *"🔥 High-Priority Leads?"*.
  - Show the instant factual summary generated from real CRM records.
  - Click the **"Client Requirement Summarizer"** tab to display structured bullets and the **Recommended Next Sales Action** for design consultants.
  - Conclude: The system provides an end-to-end, tested, and reliable lead operating system for SHA Interface Interiors.
