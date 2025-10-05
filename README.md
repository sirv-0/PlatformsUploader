# PlatformsUploader TG: @V_12_0
Automated video upload tool for Meta (Facebook/Instagram), TikTok, and YouTube with scheduling capabilities.
Core Functionality

Multi-Platform Support: Upload videos to Meta (Facebook + Instagram), TikTok, and YouTube
Automated Scheduling: Schedule uploads for morning and night (10 videos per day total)
Smart Video Selection: Automatically selects one video from each configured folder
Duplicate Prevention: Tracks uploaded videos to prevent re-uploading
Description Extraction: Automatically extracts video descriptions from filenames

Video Management

Multiple Folders: Configure up to 5 video folders
Format Support: MP4, AVI, MOV, MKV, WMV, FLV, WEBM
File Validation: Checks file size, format, and existence before upload
Upload History: Maintains complete upload history with timestamps

Platform Features
Meta (Facebook + Instagram)

Direct API integration with Facebook Graph API
Instagram cross-posting support (posts to both platforms simultaneously)
Creative folder organization
Video status verification
Automatic retry on failure

TikTok

API framework ready
Requires TikTok for Developers access token
Description support from filename

YouTube

OAuth2 authentication
Automatic token refresh
Category and privacy settings
Video metadata support

Scheduling

Morning Uploads: Configurable time (default 08:00)
Night Uploads: Configurable time (default 20:00)
Timezone Support: Configure your timezone (default UTC)
Manual Upload: Upload on-demand without waiting for schedule

User Interface

Clean command-line interface
Easy configuration menus
Real-time upload progress
Upload statistics and history
Testing mode for dry runs

Description Extraction
The script automatically extracts video descriptions from filenames:

Supports full-width quotes: ＂Description Here＂ [code].mp4 → Description Here
Supports standard quotes: "Description Here" [code].mp4 → Description Here
Removes bracketed codes: [v3IGge5jVg0] and (abc123) automatically
Falls back to full filename if no quotes found

Installation
Requirements
bashpip install -r requirements.txt
Dependencies

Python 3.7+
requests
schedule
pytz
logging (built-in)

Configuration
1. Add Video Folders
Add your 5 video folders through the menu:
Main Menu → 1. Manage Folders → 1. Add Folder
2. Configure Meta (Facebook + Instagram)
Main Menu → 2. Configure Meta
Required:

Access Token (from Facebook Graph API)
Page ID
Creative Folder ID (from Meta Business Suite)
Instagram Cross-posting (yes/no)

3. Configure TikTok (Optional)
Main Menu → 3. Configure TikTok
Required:

Access Token (from TikTok for Developers)

4. Configure YouTube (Optional)
Main Menu → 4. Configure YouTube
Required:

Client ID
Client Secret
Refresh Token

Usage
Run the Script
bashpython upload.py
Quick Start

Add your video folders
Configure at least one platform (Meta recommended)
Test with "Upload Now" to verify setup
Enable "Start Scheduler" for automatic uploads
Script runs in background and uploads at scheduled times

Testing Mode
Enable testing mode to simulate uploads without actually posting:
Main Menu → 8. Testing Mode
How It Works
Upload Process

Morning Upload (default 08:00):

Selects 1 video from each of the 5 folders
Uploads to all enabled platforms
Total: 5 videos


Night Upload (default 20:00):

Selects 1 video from each of the 5 folders
Uploads to all enabled platforms
Total: 5 videos



Daily Total: 10 videos across all platforms
Video Selection

Randomly selects one video per folder
Skips already uploaded videos
Cycles through all videos before repeating
Maintains upload history to prevent duplicates

Upload Tracking

Saves upload history to upload_history.json
Tracks video path, platform, date, and status
Prevents duplicate uploads
Can be cleared if needed

File Structure
upload.py                 # Main script
config.json              # Configuration file (auto-created)
upload_history.json      # Upload history (auto-created)
upload.log               # Log file (auto-created)
requirements.txt         # Python dependencies
README.md               # This file
API Setup Guides
Facebook/Meta

Go to https://developers.facebook.com
Create an app
Add "Facebook Login" and "Pages API"
Generate access token with permissions:

pages_manage_posts
pages_read_engagement


Get Page ID from your Facebook page settings
Create a Creative Folder in Meta Business Suite

Instagram

Must be a Business or Creator account
Link Instagram to Facebook page in Meta Business Suite
Instagram cross-posting works through Facebook API
No separate Instagram credentials needed

TikTok

Register at https://developers.tiktok.com
Create an app
Request video upload permissions
Generate access token via OAuth flow

YouTube

Create project at https://console.cloud.google.com
Enable YouTube Data API v3
Create OAuth 2.0 credentials
Use OAuth Playground to get refresh token

Troubleshooting
Videos Not Uploading

Check credentials are valid
Verify access token hasn't expired
Ensure video files are in supported format
Check logs in upload.log

Instagram Cross-posting Not Working

Verify Instagram account is linked in Meta Business Suite
Ensure Instagram is a Business/Creator account
Check access token has Instagram permissions

Schedule Not Running

Keep terminal/command prompt open
Script must remain running for scheduler to work
Check timezone settings match your location

Limitations
Meta (Facebook/Instagram)

Video must be under 4GB
Requires Facebook page (not personal profile)
Instagram must be Business/Creator account
Rate limits apply (avoid uploading too frequently)

TikTok

Requires approved developer account
API access may be limited by region
Upload permissions must be granted

YouTube

Daily quota limits apply
OAuth tokens may expire
Verification may be required for some features

Security Notes

Keep config.json secure (contains access tokens)
Never share your access tokens
Regenerate tokens if compromised
Use .gitignore if version controlling

Support
For issues related to:

Facebook API: https://developers.facebook.com/support
TikTok API: https://developers.tiktok.com/doc
YouTube API: https://developers.google.com/youtube

License
This is a personal automation tool. Use responsibly and in accordance with each platform's Terms of Service.
Changelog
Version 1.0

Initial release
Meta (Facebook/Instagram) support
TikTok framework
YouTube framework
Automated scheduling
Description extraction
Upload tracking
Testing mode
