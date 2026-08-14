import subprocess
import urllib.request
import os

print("\n🚀 [LegacyLink] Initializing Autonomous Middleware Engine...")

# 1. Fetch XML from legacy server
print("📡 Probing legacy system at http://localhost:8085/GetCustomerData...")
try:
    req = urllib.request.Request("http://localhost:8085/GetCustomerData", method="POST")
    with urllib.request.urlopen(req) as response:
        xml_data = response.read().decode('utf-8')
    
    with open("raw_schema.xml", "w") as f:
        f.write(xml_data)
    print("✅ Legacy XML schema extracted and saved.")
except Exception as e:
    print("❌ Failed to connect to legacy server. Is it running?", e)
    exit(1)

# 2. Create isolated worktree for REST wrapper
print("🌳 Creating isolated Git worktree for modern REST API...")
if not os.path.exists("../rest-wrapper"):
    subprocess.run(["git", "worktree", "add", "../rest-wrapper", "-b", "feature-rest-api"], capture_output=True)

# Copy the XML schema over into the new worktree (Windows command)
subprocess.run(["cmd.exe", "/c", "copy", "raw_schema.xml", "..\\rest-wrapper\\raw_schema.xml"], capture_output=True)

# 3. Dispatch Codex
print("🧠 Dispatching Codex Agent to generate FastAPI wrapper & Dodo Payments integration...")
codex_prompt = (
    "Read raw_schema.xml. Generate a production-ready REST API using Python FastAPI. "
    "Create Pydantic models that strictly type the JSON response mapped from this XML. "
    "Include a dummy Dodo Payments middleware function for API usage metering."
)

try:
    subprocess.run(["codex.cmd", "--approve-for-me", codex_prompt], cwd="../rest-wrapper", check=True)
    print("\n✨ [LegacyLink] Mission Complete! Modern REST API successfully generated in '../rest-wrapper'.")
except subprocess.CalledProcessError:
    print("❌ Codex Agent failed.")