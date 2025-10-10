# 🚀 Project Setup Guide

This guide walks you through setting up the **frontend** and **backend** for the project.

---

## 🟢 Frontend Setup

The frontend contains the **user interface** and **client-side logic**.

<details>
<summary>Steps to run the frontend</summary>

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
bun install
```

3. Start the development server:
```bash
bun run dev
```

> **Tip:** Keep this terminal running while you work on the frontend.

</details>

---

## 🔵 Backend Setup

The backend contains the **MCP server** and **API client**.

<details>
<summary>1️⃣ Create a Python Virtual Environment</summary>

Navigate to your backend directory and set up a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment (Linux/macOS)
source venv/bin/activate
```

</details>

<details>
<summary>2️⃣ Install Backend Dependencies</summary>

Make sure you are in the backend directory:

```bash
cd Backend/MCP
```

Install required packages:

```bash
pip install -r requirements.txt
```

</details>

<details>
<summary>3️⃣ Run the MCP Server</summary>

```bash
python mcp_server_new.py
```

> Keep this terminal running to serve the MCP backend.

</details>

<details>
<summary>4️⃣ Run the Client API Server</summary>

Open a **new terminal** and run the FastAPI client:

```bash
cd Backend/MCP
uvicorn mcp_client_new_2:app --reload --host 0.0.0.0 --port 5000
```

> This server handles API requests from the frontend.

</details>

---

## ✅ Summary

| Component | Command |
|-----------|---------|
| **Frontend** | `bun run dev` |
| **Backend MCP Server** | `python mcp_server_new.py` |
| **Backend API Client** | `uvicorn mcp_client_new_2:app --reload --host 0.0.0.0 --port 5000` |

> Make sure all three terminals are running for the full project to work correctly.
