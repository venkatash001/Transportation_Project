# GCP Authentication Setup Guide
# CES IND Transport Roster

The app fetches schedule data directly from Google BigQuery.
To do this, it needs your GCP credentials on this machine.
You have **two options** — pick whichever is easier for you.

---

## Option A: Service Account Key (Recommended for production)

This is the standard approach for automated/server apps.
Ask your GCP admin or do it yourself in the GCP Console.

### Steps

1. Open the GCP Console in your browser:
   https://console.cloud.google.com/iam-admin/serviceaccounts?project=wmt-cc-datasphere-prod

2. Find an existing service account that has BigQuery access, OR create a new one:
   - Click **"Create Service Account"**
   - Give it a name like `transport-roster-app`
   - Grant roles: **BigQuery Data Viewer** + **BigQuery Job User**

3. Click on the service account -> **"Keys"** tab -> **"Add Key"** -> **"JSON"**

4. A `.json` file will download to your machine.

5. Move the JSON file into this project folder and rename it:
   ```
   28.Transportation_Roster_Project\gcp_service_account.json
   ```

6. Run the app — it will auto-detect the key file. Done!

---

## Option B: Your Personal Google Account (gcloud CLI)

This uses the same Google account you log into console.cloud.google.com with.

### Step 1: Install Google Cloud SDK

Download the installer from your browser (this bypasses proxy restrictions):
```
https://cloud.google.com/sdk/docs/install-sdk#windows
```
Click the **"Windows"** installer link and run it.

### Step 2: Login after install

Open a new Command Prompt and run:
```
gcloud auth application-default login
```

This opens your browser. Log in with your Walmart Google account.
A credentials file gets saved automatically.

### Step 3: Restart the app

Double-click **Run Me.bat** — the app will now connect to BigQuery.

---

## How the app detects credentials (in order)

1. Looks for `gcp_service_account.json` in the project root folder
2. Checks the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Falls back to Application Default Credentials (gcloud login)

---

## Troubleshooting

| Error | Fix |
|---|---|
| `DefaultCredentialsError` | Run Option A or Option B above |
| `403 Forbidden` | Service account lacks BigQuery roles |
| `404 Not Found` | Check project ID: `wmt-cc-datasphere-prod` |
| `0 rows returned` | Check the date range and SITE_NM filter in the SQL |

---

*Last updated: 2026-06-26*
