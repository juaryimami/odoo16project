# Implementation Guide: "Orbit Heights" Residential Tower
### Step-by-Step Walkthrough: From Mobilization to Quality-Approved Handover

This guide simulates the execution of a 10-story residential building project using the **Construction ERP**'s advanced closed-loop workflow.

---

## Phase 1: Preparation & Blueprinting

### Step 1: Define the Construction Lifecycle
- **Action**: `Configuration > Construction Lifecycles`.
- **Logic**: Create "Standard High-Rise". Add phases: `Mobilization`, `Substructure`, `Superstructure`, `MEP`, `Finishes`.
- **Outcome**: Your project ROADMAP is now standardized.

### Step 2: Create the Project
- **Action**: `Project Management > Projects > New`.
- **Data**: Project: `Orbit Heights`, Lifecycle: `Standard High-Rise`.
- **Outcome**: The status bar at the top of the project form now shows your 5 phases in real-time.

---

## Phase 2: Commercial Scoping (High-Precision BOQ)

### Step 3: The Specialized Estimate
- **Action**: `Commercial Management > Estimates > New`.
- **Logic**: Use the specialized tabs to isolate costs:
    - **Materials**: `Cement` (2000 bags), `Steel` (50 Tons). Set **Lead Time** (e.g. 15 days).
    - **Labor**: `Mason` (10 persons), `Foreman` (2 persons).
    - **Equipment**: `Excavator` (100 hours).
- **Outcome**: Your budget is now scientifically categorized for surgical auditing.

### Step 4: Initialize the Master Budget
- **Action**: Click **Initialize Project Cost Sheet**.
- **Outcome**: The "Brain" of the project is created. Every future dollar spent will be checked against this BOQ baseline.

---

## Phase 3: Sourcing & Site Mobilization

### Step 5: Proactive Risk Check
- **Action**: Go to the **Project Dashboard**.
- **Logic**: Check the **Procurement Risks** counter.
- **Alert**: If it shows "Steel" as a risk, it means your lead time is approaching and no PO exists.
- **Action**: Use the **Smart Sourcing Wizard** to generate a Purchase Order for the steel immediately.

### Step 6: The Contractor "Start/Stop" Workflow
- **Action**: `Site Operations > Job Orders > New`.
- **Task**: "Piling Foundations". Assign to `Star Foundations Ltd`.
- **Action**: Click **Offer Job**. Contractor receives a notification with technical specs.
- **Action**: Contractor clicks **Accept Job**, then **Start Work** upon arrival on site.
- **Outcome**: The system captures the **Actual Start** timestamp, officially moving the project into the "Mobilization" state.

---

## Phase 4: Execution & Quality Gate

### Step 7: Site Usage & Consumables
- **Action**: Record daily fuel and machine hours in **Site Usage Logs**.
- **Outcome**: The **Equipment** tab on the Cost Sheet updates instantly with actual running costs.

### Step 8: Reporting Completion & Auto-Inspection
- **Action**: Once piling is finished, Contractor clicks **Report Finished**.
- **System Automation**: The status moves to `Ready for Inspection`, and a **Quality Inspection** record is automatically created for the Site Engineer.
- **The Gate**: 
    - **Engineer Action**: Reviews work. Clicks **Pass**.
    - **Outcome**: Job Order moves to **Quality Approved**. The system instantly marks the financial milestone as "Approved".
    - **Failure Logic**: Clicking "Failed" would move the job to **Rework Required** and notify the contractor.

---

## Phase 5: Financial Realization & Payment

### Step 9: Automated Payment Trigger
- **Action**: Because the inspection passed, you can now click **Generate Vendor Bill** on the Job Order.
- **Audit Logic**: The bill is created in **Draft**, ready for Finance. It is pre-linked to the specialized budget line for foundation materials/labor.

### Step 10: Executive Profitability Review
- **Action**: `Reporting > Project Profitability Dashboard`.
- **Analysis**: Review the **Specialized Rollup**. 
- **Check**: Is the "Actual Labor Spent" higher than the "Budgeted Labor"? 
- **Outcome**: You have 100% visibility into where every dollar of profit is being gained or lost.

### Step 11: Real-Time Command Center Oversight
- **Action**: Open the **Executive Intelligence Command**.
- **Oversight Logic**:
    - **Visual Audit**: Scroll to the **Site Intelligence Visuals** section. Click on the `Orbit Heights` album to launch the immersive gallery and verify piling progress visually.
    - **Resource Demand**: Check the **Mat Requests** card in the sticky sidebar to see if the site team has requested additional concrete or steel.
    - **Activity Monitoring**: Monitor the **Job Orders** counter to ensure all planned substructure activities are assigned and active.
- **Outcome**: You are no longer managing from an office; you are commanding the project with real-time visual and operational data.

---

## 🏆 Key To Success
The **Quality Inspection** is the master key. No work is "Done" until the engineer says so, and no bill is "Paid" until the work is "Done". This cycle ensures **Progress Integrity**.
