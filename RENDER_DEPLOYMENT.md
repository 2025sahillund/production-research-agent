# Render Deployment Guide

This guide walks you through deploying the **Production-Oriented AI Research Agent** on [Render](https://render.com) in under 3 minutes.

---

## Method 1: Automatic Blueprint Deployment (Recommended)

1. Sign in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top right, then select **Blueprint**.
3. Connect your GitHub account and select your repository:
   - **Repository**: `2025sahillund/production-research-agent`
   - **Branch**: `master`
4. Render will automatically read the `render.yaml` configuration file included in the repository.
5. Click **Apply**.
6. Render will automatically:
   - Provision a Python 3.11 web service.
   - Run `pip install -r requirements.txt`.
   - Start Streamlit with the command:
     ```bash
     streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false
     ```
7. Once the build completes (approx. 1-2 minutes), your live public URL will be ready at:
   `https://production-research-agent.onrender.com` (or similar Render subdomain).

---

## Method 2: Manual Web Service Setup

If you prefer to configure the service manually on Render:

1. In the Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Select **Build and deploy from a Git repository**.
3. Connect repository: `https://github.com/2025sahillund/production-research-agent`.
4. Enter the following parameters:
   - **Name**: `production-research-agent`
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Branch**: `master`
   - **Runtime**: `Python`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false
     ```
   - **Instance Type**: `Free`
5. Under **Advanced** $\rightarrow$ **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - *(Optional)* `OPENAI_API_KEY`: `<your-openai-key>` (if using OpenAI provider)
   - *(Optional)* `GEMINI_API_KEY`: `<your-gemini-key>` (if using Gemini provider)
   - *(Optional)* `GROQ_API_KEY`: `<your-groq-key>` (if using Groq provider)
   > *Note: If no API keys are provided, the system seamlessly operates in **Deterministic High-Fidelity Local Engine mode** with zero external API costs!*
6. Click **Create Web Service**.

---

## Verifying the Deployment
- Check the **Logs** tab in Render to observe:
  ```text
  Collecting streamlit...
  Successfully installed ...
  You can now view your Streamlit app in your browser.
  URL: http://0.0.0.0:10000
  ```
- Open the assigned `.onrender.com` URL in your browser.
- Run one of the preset benchmark queries (e.g. *Vector DB Comparison*) to verify end-to-end execution on the live cloud server.

