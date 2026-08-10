import os
import requests

file_path = "playlist.m3u8"
timeout_seconds = 4  # Fast timeout to keep the script moving quickly

if not os.path.exists(file_path):
    print(f"Error: Could not find '{file_path}' in the current directory.")
    exit(1)

print(f"Reading '{file_path}'...")
with open(file_path, "r", encoding="utf-8") as f:
    raw_lines = f.readlines()

# Clean up empty lines and trailing spaces
lines = [line.strip() for line in raw_lines if line.strip()]

cleaned_lines = []
# Ensure the standard M3U header is preserved at the top
if lines and lines[0].startswith("#EXTM3U"):
    cleaned_lines.append(lines[0] + "\n")

print("Validating streams and removing dead links...")

# Loop through the list to parse metadata entries paired with their URLs
i = 1
while i < len(lines):
    current_line = lines[i]
    
    # Check if the line is a channel metadata header
    if current_line.startswith("#EXTINF"):
        # Ensure there is a following line for the URL
        if i + 1 < len(lines):
            url_line = lines[i+1]
            
            # Verify the next line is a valid network link string
            if url_line.startswith("http://") or url_line.startswith("https://"):
                channel_name = current_line.split(",")[-1].strip()
                try:
                    # Use a fast HEAD request to check stream availability
                    response = requests.head(url_line, timeout=timeout_seconds, allow_redirects=True)
                    
                    # Status codes below 400 mean the stream endpoint is active
                    if response.status_code < 400:
                        cleaned_lines.append(current_line + "\n")
                        cleaned_lines.append(url_line + "\n")
                        print(f"✅ ALIVE: {channel_name}")
                    else:
                        print(f"❌ REMOVED (HTTP {response.status_code}): {channel_name}")
                except Exception:
                    print(f"❌ REMOVED (Connection Timeout): {channel_name}")
                
                i += 2  # Advance past both the metadata and the URL
                continue
    i += 1

# Overwrite the original playlist file directly with the cleaned streams
print(f"\nOverwriting {file_path} with working links...")
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(cleaned_lines)

print("Playlist update complete!")
