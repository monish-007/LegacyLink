import subprocess
import urllib.request
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
WORKTREE = ROOT.parent / "rest-wrapper"

print("\n🚀 [LegacyLink] Initializing verifiable modernization workflow...")

# 1. Fetch XML from legacy server
print("📡 Probing legacy system at http://localhost:8085/GetCustomerData...")
try:
    req = urllib.request.Request("http://localhost:8085/GetCustomerData", method="POST")
    with urllib.request.urlopen(req) as response:
        xml_data = response.read().decode('utf-8')
    
    (ROOT / "raw_schema.xml").write_text(xml_data, encoding="utf-8")
    print("✅ Legacy XML schema extracted and saved.")
except Exception as e:
    print("❌ Failed to connect to legacy server. Is it running?", e)
    exit(1)

# 2. Create isolated worktree for REST wrapper
print("🌳 Preparing isolated Git worktree for a reviewable REST API draft...")
if not WORKTREE.exists():
    subprocess.run(
        ["git", "worktree", "add", str(WORKTREE), "-b", "feature-rest-api"],
        cwd=ROOT,
        check=True,
    )

# Keep the source fixture inside the generated project so its mapping can be
# tested and reviewed. No SOAP header is exposed by the resulting REST API.
shutil.copy2(ROOT / "raw_schema.xml", WORKTREE / "raw_schema.xml")

# 3. Dispatch Codex
print("🧠 Dispatching Codex Agent to generate FastAPI wrapper & Dodo Payments integration...")
codex_prompt = (
    "Read raw_schema.xml and create a reviewable FastAPI REST API draft. "
    "Generate strict Pydantic models for the JSON projection, tests for valid and "
    "invalid XML, and an OpenAPI-friendly dashboard. Never expose SOAP authentication "
    "headers. Treat all changes as a draft: run the test suite, summarize the mapping "
    "and limitations, and do not deploy or make external calls."
)

try:
    subprocess.run(["codex.cmd", codex_prompt], cwd=WORKTREE, check=True)
    print("\n✨ [LegacyLink] Draft generated. Review the diff and test results before deployment.")
except subprocess.CalledProcessError:
    print("❌ Codex Agent failed.")
