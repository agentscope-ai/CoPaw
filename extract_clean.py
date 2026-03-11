import subprocess
import os

repo_dir = r"C:\Users\Administrator\Downloads\Antigravity\项目\CoPaw"
out_path = os.path.join(repo_dir, "src", "copaw", "app", "channels", "discord_", "channel.py")

# Extract exactly as bytes from git
output = subprocess.check_output(
    ["git", "show", "upstream/main:src/copaw/app/channels/discord_/channel.py"],
    cwd=repo_dir
)

with open(out_path, "wb") as f:
    f.write(output)

print("Extracted cleanly to", out_path)
