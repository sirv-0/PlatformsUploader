import os
import sys
import json
import time
import datetime
import threading
import signal
import logging
import pytz
import requests
import schedule
import re

class Config:
    def __init__(self):
        self.config_file = 'config.json'
        self.log_file = 'upload.log'
        self.history_file = 'upload_history.json'
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                self.folders = config_data.get('folders', [])
                self.morning_time = config_data.get('morning_time', '08:00')
                self.night_time = config_data.get('night_time', '20:00')
                self.timezone = config_data.get('timezone', 'UTC')
                self.platforms = config_data.get('platforms', {})
                self.testing_mode = config_data.get('testing_mode', False)
                
                if 'facebook' in self.platforms or 'instagram' in self.platforms:
                    fb_config = self.platforms.get('facebook', {})
                    if fb_config.get('enabled'):
                        self.platforms['meta'] = fb_config
                    if 'facebook' in self.platforms:
                        del self.platforms['facebook']
                    if 'instagram' in self.platforms:
                        del self.platforms['instagram']
                    self.save_config()
        else:
            self.folders = []
            self.morning_time = '08:00'
            self.night_time = '20:00'
            self.timezone = 'UTC'
            self.platforms = {}
            self.testing_mode = False
    
    def save_config(self):
        config_data = {
            'folders': self.folders,
            'morning_time': self.morning_time,
            'night_time': self.night_time,
            'timezone': self.timezone,
            'platforms': self.platforms,
            'testing_mode': self.testing_mode
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

class VideoFile:
    def __init__(self, path):
        self.path = path
        self.filename = os.path.basename(path)
        self.size = os.path.getsize(path)
        self.extension = os.path.splitext(path)[1].lower()
        filename_without_ext = os.path.splitext(self.filename)[0]
        self.name = self._extract_description(filename_without_ext)
    
    def _extract_description(self, filename):
        pattern = r'＂([^＂]+)＂'
        match = re.search(pattern, filename)
        
        if match:
            extracted_text = match.group(1).strip()
            extracted_text = re.sub(r'\s*[\[\(][^\]\)]*[\]\)]\s*', ' ', extracted_text)
            return extracted_text.strip()
        
        pattern = r'"([^"]+)"'
        match = re.search(pattern, filename)
        
        if match:
            extracted_text = match.group(1).strip()
            extracted_text = re.sub(r'\s*[\[\(][^\]\)]*[\]\)]\s*', ' ', extracted_text)
            return extracted_text.strip()
        
        cleaned = re.sub(r'\s*[\[\(][^\]\)]*[\]\)]\s*', ' ', filename)
        return cleaned.strip()
    
    def validate(self):
        errors = []
        
        if not os.path.exists(self.path):
            errors.append(f"File does not exist: {self.path}")
        
        max_size = 4 * 1024 * 1024 * 1024
        if self.size > max_size:
            errors.append(f"File too large: {self.size / (1024*1024):.2f}MB (max 4GB)")
        
        if self.size == 0:
            errors.append("File is empty")
        
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        if self.extension not in valid_extensions:
            errors.append(f"Invalid file format: {self.extension}")
        
        return len(errors) == 0, errors

class PlatformUploader:
    def __init__(self, credentials, testing_mode):
        self.credentials = credentials
        self.testing_mode = testing_mode
    
    def validate_credentials(self):
        return True
    
    def upload(self, video_file):
        raise NotImplementedError()

class FacebookUploader(PlatformUploader):
    def validate_credentials(self):
        if not self.credentials.get('access_token'):
            return False, "Missing access_token"
        if not self.credentials.get('page_id'):
            return False, "Missing page_id"
        
        try:
            test_url = f"https://graph.facebook.com/v18.0/{self.credentials['page_id']}"
            params = {'access_token': self.credentials['access_token'], 'fields': 'id,name'}
            response = requests.get(test_url, params=params, timeout=10)
            
            if response.status_code == 200:
                page_data = response.json()
                page_name = page_data.get('name', 'Unknown')
                logging.info(f"Facebook credentials valid. Connected to page: {page_name}")
                return True, f"Connected to: {page_name}"
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                logging.error(f"Facebook credential validation failed: {error_msg}")
                return False, f"API Error: {error_msg}"
        except Exception as e:
            logging.error(f"Facebook credential validation error: {e}")
            return False, f"Connection error: {str(e)}"
    
    def upload(self, video_file):
        if self.testing_mode:
            print("  [Testing Mode] Simulating upload...")
            time.sleep(2)
            return True
        
        is_valid, errors = video_file.validate()
        if not is_valid:
            raise Exception(f"Invalid video: {', '.join(errors)}")
        
        cred_valid, cred_error = self.validate_credentials()
        if not cred_valid:
            raise Exception(f"Invalid credentials: {cred_error}")
        
        video_title = video_file.name
        video_description = video_file.name
        
        url = f"https://graph.facebook.com/v18.0/{self.credentials['page_id']}/videos"
        
        print(f"  Uploading {video_file.size / (1024*1024):.2f}MB...")
        
        with open(video_file.path, 'rb') as video:
            files = {'source': video}
            
            data = {
                'access_token': self.credentials['access_token'],
                'title': video_title,
                'description': video_description,
            }
            
            if self.credentials.get('creative_folder_id'):
                data['creative_folder_id'] = self.credentials['creative_folder_id']
            
            if self.credentials.get('crosspost_to_instagram', False):
                data['crossposting_actions'] = json.dumps([{
                    'page': self.credentials['page_id'],
                    'should_upload_video_to_instagram': True
                }])
            
            timeout = max(600, video_file.size / (1024 * 512))
            response = requests.post(url, files=files, data=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                
                if video_id:
                    print(f"  Upload successful! Video ID: {video_id}")
                    return True
                else:
                    raise Exception("Upload succeeded but no video ID returned")
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Upload failed: {error_msg}")

class TikTokUploader(PlatformUploader):
    def validate_credentials(self):
        if not self.credentials.get('access_token'):
            return False, "Missing access_token"
        return True, "OK"
    
    def upload(self, video_file):
        if self.testing_mode:
            print("  [Testing Mode] Simulating TikTok upload...")
            time.sleep(2)
            return True
        
        is_valid, errors = video_file.validate()
        if not is_valid:
            raise Exception(f"Invalid video: {', '.join(errors)}")
        
        cred_valid, cred_error = self.validate_credentials()
        if not cred_valid:
            raise Exception(f"Invalid credentials: {cred_error}")
        
        raise Exception("TikTok upload requires API implementation")

class YouTubeUploader(PlatformUploader):
    def validate_credentials(self):
        if not self.credentials.get('client_id'):
            return False, "Missing client_id"
        if not self.credentials.get('client_secret'):
            return False, "Missing client_secret"
        if not self.credentials.get('refresh_token'):
            return False, "Missing refresh_token"
        return True, "OK"
    
    def upload(self, video_file):
        if self.testing_mode:
            print("  [Testing Mode] Simulating YouTube upload...")
            time.sleep(2)
            return True
        
        is_valid, errors = video_file.validate()
        if not is_valid:
            raise Exception(f"Invalid video: {', '.join(errors)}")
        
        cred_valid, cred_error = self.validate_credentials()
        if not cred_valid:
            raise Exception(f"Invalid credentials: {cred_error}")
        
        raise Exception("YouTube upload requires google-api-python-client library")

class Statistics:
    def __init__(self, config):
        self.config = config
        self.upload_history = self.load_history()
    
    def load_history(self):
        if os.path.exists(self.config.history_file):
            try:
                with open(self.config.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        with open(self.config.history_file, 'w') as f:
            json.dump(self.upload_history, f, indent=2)
    
    def is_uploaded(self, video_path, platform):
        for entry in self.upload_history:
            if entry['video_path'] == video_path and entry['platform'] == platform:
                return True
        return False
    
    def record_upload(self, video_path, platform, status='success'):
        entry = {
            'video_path': video_path,
            'platform': platform,
            'upload_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status
        }
        self.upload_history.append(entry)
        self.save_history()
    
    def get_stats(self):
        stats = {'meta': 0, 'tiktok': 0, 'youtube': 0, 'total': 0}
        
        for entry in self.upload_history:
            platform = entry['platform']
            if platform == 'facebook' or platform == 'instagram':
                platform = 'meta'
            
            if platform in stats:
                stats[platform] += 1
            stats['total'] += 1
        
        return stats
    
    def clear_history(self):
        self.upload_history = []
        self.save_history()

class VideoUploadManager:
    def __init__(self):
        self.config = Config()
        self.tracker = Statistics(self.config)
        self.uploaders = {}
        self.running = False
        
        logging.basicConfig(
            filename=self.config.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.init_uploaders()
    
    def init_uploaders(self):
        self.uploaders = {}
        
        if self.config.platforms.get('meta', {}).get('enabled'):
            creds = self.config.platforms['meta']['credentials']
            self.uploaders['meta'] = FacebookUploader(creds, self.config.testing_mode)
        
        if self.config.platforms.get('tiktok', {}).get('enabled'):
            creds = self.config.platforms['tiktok']['credentials']
            self.uploaders['tiktok'] = TikTokUploader(creds, self.config.testing_mode)
        
        if self.config.platforms.get('youtube', {}).get('enabled'):
            creds = self.config.platforms['youtube']['credentials']
            self.uploaders['youtube'] = YouTubeUploader(creds, self.config.testing_mode)
    
    def get_videos_from_folders(self):
        folder_videos = {}
        
        for folder in self.config.folders:
            if os.path.exists(folder):
                videos = []
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
                            videos.append(file_path)
                folder_videos[folder] = videos
        
        return folder_videos
    
    def upload_batch(self, batch_type="scheduled"):
        print(f"\nStarting {batch_type} upload batch...")
        
        if not self.uploaders:
            print("No platforms enabled!")
            return
        
        folder_videos = self.get_videos_from_folders()
        
        if not folder_videos:
            print("No videos found")
            return
        
        upload_count = 0
        successful_platforms = set()
        
        for folder, videos in folder_videos.items():
            if not videos:
                continue
            
            video_to_upload = None
            
            for video_path in videos:
                uploaded_to_all = True
                for platform_name in self.uploaders.keys():
                    if not self.tracker.is_uploaded(video_path, platform_name):
                        uploaded_to_all = False
                        break
                
                if not uploaded_to_all:
                    video_to_upload = video_path
                    break
            
            if video_to_upload is None:
                video_to_upload = videos[0]
            
            filename = os.path.basename(video_to_upload)
            print(f"\nFrom folder: {os.path.basename(folder)}")
            print(f"Video: {filename}")
            
            try:
                video_file = VideoFile(video_to_upload)
                is_valid, validation_errors = video_file.validate()
                
                if not is_valid:
                    print(f"  Validation failed")
                    continue
                
                print(f"  Description: {video_file.name}")
            
            except Exception as e:
                print(f"  Error: {e}")
                continue
            
            for platform_name, uploader in self.uploaders.items():
                if self.tracker.is_uploaded(video_to_upload, platform_name):
                    print(f"  {platform_name}: Already uploaded")
                    continue
                
                print(f"  Uploading to {platform_name}...")
                
                try:
                    success = uploader.upload(video_file)
                    
                    if success:
                        self.tracker.record_upload(video_to_upload, platform_name, 'success')
                        upload_count += 1
                        successful_platforms.add(platform_name)
                        print(f"  {platform_name}: Success")
                    else:
                        print(f"  {platform_name}: Failed")
                
                except Exception as e:
                    print(f"  {platform_name}: {str(e)}")
                
                time.sleep(5)
        
        if successful_platforms:
            platform_map = {'meta': 'Meta', 'tiktok': 'TikTok', 'youtube': 'YouTube'}
            display_names = set()
            for platform in successful_platforms:
                display_names.add(platform_map.get(platform, platform))
            
            platforms_text = ', '.join(sorted(display_names))
            print(f"\nSuccessfully uploaded to {platforms_text}. Done")
        
        print(f"\nBatch complete. Uploaded: {upload_count}")
    
    def run_scheduler(self):
        self.running = True
        schedule.clear()
        
        schedule.every().day.at(self.config.morning_time).do(self.upload_batch, "morning")
        schedule.every().day.at(self.config.night_time).do(self.upload_batch, "night")
        
        print(f"Scheduler running. Uploads at {self.config.morning_time} and {self.config.night_time}")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def stop_scheduler(self):
        self.running = False
        schedule.clear()

class CLI:
    def __init__(self):
        self.manager = VideoUploadManager()
        self.scheduler_thread = None
    
    def run(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 50)
            print("  Video Upload Scheduler")
            print("  Meta - TikTok - YouTube")
            print("=" * 50)
            print("\n1. Manage Folders")
            print("2. Configure Meta")
            print("3. Configure TikTok")
            print("4. Configure YouTube")
            print("5. Upload Now")
            print("6. Start Scheduler")
            print("7. View Stats")
            print("8. Testing Mode")
            print("0. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                self.manage_folders()
            elif choice == '2':
                self.configure_meta()
            elif choice == '3':
                self.configure_tiktok()
            elif choice == '4':
                self.configure_youtube()
            elif choice == '5':
                self.manager.upload_batch('manual')
                input("\nPress Enter...")
            elif choice == '6':
                self.scheduler_thread = threading.Thread(target=self.manager.run_scheduler, daemon=True)
                self.scheduler_thread.start()
                input("\nScheduler started! Press Enter...")
            elif choice == '7':
                stats = self.manager.tracker.get_stats()
                print(f"\nMeta: {stats['meta']}")
                print(f"TikTok: {stats['tiktok']}")
                print(f"YouTube: {stats['youtube']}")
                print(f"Total: {stats['total']}")
                input("\nPress Enter...")
            elif choice == '8':
                self.manager.config.testing_mode = not self.manager.config.testing_mode
                self.manager.config.save_config()
                self.manager.init_uploaders()
                status = "Enabled" if self.manager.config.testing_mode else "Disabled"
                print(f"\nTesting mode: {status}")
                input("\nPress Enter...")
            elif choice == '0':
                break
    
    def manage_folders(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("MANAGE FOLDERS")
            print("=" * 50)
            for i, folder in enumerate(self.manager.config.folders, 1):
                print(f"{i}. {folder}")
            print("\n1. Add Folder")
            print("2. Remove Folder")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                folder = input("Folder path: ").strip()
                if os.path.exists(folder):
                    self.manager.config.folders.append(folder)
                    self.manager.config.save_config()
                    print("Added!")
                else:
                    print("Folder not found!")
                input("\nPress Enter...")
            elif choice == '2':
                try:
                    idx = int(input("Folder number: ")) - 1
                    if 0 <= idx < len(self.manager.config.folders):
                        self.manager.config.folders.pop(idx)
                        self.manager.config.save_config()
                        print("Removed!")
                    input("\nPress Enter...")
                except:
                    pass
            elif choice == '0':
                break
    
    def configure_meta(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("CONFIGURE META")
        print("=" * 50)
        token = input("Access Token: ").strip()
        page_id = input("Page ID: ").strip()
        folder_id = input("Creative Folder ID: ").strip()
        crosspost = input("Enable Instagram? (y/n): ").strip().lower()
        
        self.manager.config.platforms['meta'] = {
            'enabled': True,
            'credentials': {
                'access_token': token,
                'page_id': page_id,
                'creative_folder_id': folder_id,
                'crosspost_to_instagram': crosspost == 'y'
            }
        }
        self.manager.config.save_config()
        self.manager.init_uploaders()
        print("Configured!")
        input("\nPress Enter...")
    
    def configure_tiktok(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("CONFIGURE TIKTOK")
        print("=" * 50)
        token = input("Access Token: ").strip()
        
        self.manager.config.platforms['tiktok'] = {
            'enabled': True,
            'credentials': {
                'access_token': token
            }
        }
        self.manager.config.save_config()
        self.manager.init_uploaders()
        print("Configured!")
        input("\nPress Enter...")
    
    def configure_youtube(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("CONFIGURE YOUTUBE")
        print("=" * 50)
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        refresh_token = input("Refresh Token: ").strip()
        
        self.manager.config.platforms['youtube'] = {
            'enabled': True,
            'credentials': {
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token
            }
        }
        self.manager.config.save_config()
        self.manager.init_uploaders()
        print("Configured!")
        input("\nPress Enter...")

def main():
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
