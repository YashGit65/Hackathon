import os
import re
import sys
import subprocess
import json
from datetime import datetime
from PIL import Image, ExifTags
import pillow_heif

pillow_heif.register_heif_opener()

def get_timestamp_from_filename(filename):
    """Scans the filename for a YYYY_MM_DD_HH_MM_SS pattern."""
    match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', filename)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, '%Y_%m_%d_%H_%M_%S').timestamp()
        except Exception:
            return None
    return None

def get_decimal_from_dms(dms, ref):
    """Converts raw GPS degrees/minutes/seconds into decimal coordinates."""
    if dms is None: return None
    try:
        if isinstance(dms, (float, int)):
            decimal = float(dms)
        elif isinstance(dms, (tuple, list)):
            def clean_val(val):
                if isinstance(val, (tuple, list)) and len(val) == 2:
                    return float(val[0]) / float(val[1]) if val[1] != 0 else 0.0
                if hasattr(val, 'numerator') and hasattr(val, 'denominator'):
                     return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
                return float(val)

            d = clean_val(dms[0]) if len(dms) > 0 else 0.0
            m = clean_val(dms[1]) if len(dms) > 1 else 0.0
            s = clean_val(dms[2]) if len(dms) > 2 else 0.0
            decimal = d + (m / 60.0) + (s / 3600.0)
        else:
            decimal = float(dms)
            
        if ref and str(ref).strip("b'\"").upper() in ['S', 'W']:
            decimal = -decimal
        return decimal
    except Exception:
        return None

import sys
import os
import subprocess
import json
from datetime import datetime

def get_video_metadata(file_path):
    """Uses ExifTool to rip the true GPS and Time out of a video file."""
    
    # --- THE MAGIC EXE PATH FINDER ---
    if getattr(sys, 'frozen', False):
        # If running as an .exe, look in the folder where the .exe is sitting
        base_dir = os.path.dirname(sys.executable)
    else:
        # If running as a Python script, look where the script is
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    exiftool_path = os.path.join(base_dir, 'exiftool.exe')

    if not os.path.exists(exiftool_path):
        print(f"DEBUG: Could not find ExifTool at {exiftool_path}")
        return None, None, None

    try:
        cmd = [exiftool_path, '-j', '-n', '-CreationDate', '-CreateDate', '-MediaCreateDate', '-GPSLatitude', '-GPSLongitude', file_path]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Notice cwd=base_dir !
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, cwd=base_dir)
        
        # ... (keep the rest of your extraction logic exactly the same below here)
        if not result.stdout:
            return None, None, None
            
        metadata = json.loads(result.stdout)[0]
# ... [rest of the function remains identical]
        
        # 1. Extract Time
        timestamp = None
        date_str = metadata.get('CreationDate') or metadata.get('CreateDate') or metadata.get('MediaCreateDate')
        if date_str:
            date_str = str(date_str)[:19] 
            try: timestamp = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').timestamp()
            except Exception: pass
                
        # 2. Extract GPS
        lat, lon = None, None
        if metadata.get('GPSLatitude') is not None and metadata.get('GPSLongitude') is not None:
            lat = float(metadata['GPSLatitude'])
            lon = float(metadata['GPSLongitude'])
        
        return timestamp, lat, lon
        
    except Exception as e:
        print(f"ExifTool error on {os.path.basename(file_path)}: {e}")
        return None, None, None
    
        
def extract_exif_data(file_path):
    """STRICT: Requires both Time and GPS for the clustering phase."""
    
    # --- VIDEO HANDLING ---
    if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        timestamp, lat, lon = get_video_metadata(file_path)
        if timestamp and lat is not None and lon is not None:
            return {'filepath': file_path, 'timestamp': timestamp, 'lat': lat, 'lon': lon}
        return None

    # --- PHOTO HANDLING ---
    try:
        img = Image.open(file_path)
        dt_str, gps_info = None, None

        if hasattr(img, 'getexif'):
            exif = img.getexif()
            if exif:
                dt_str = exif.get(306) 
                try:
                    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                    if exif_ifd and 36867 in exif_ifd: dt_str = exif_ifd[36867]
                    gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
                except AttributeError: pass
        
        if not dt_str and hasattr(img, '_getexif'):
            raw_exif = img._getexif()
            if raw_exif:
                exif_data = {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}
                dt_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                gps_info = exif_data.get('GPSInfo')

        if not dt_str: return None
        timestamp = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S').timestamp()

        if not gps_info or not isinstance(gps_info, dict) or 2 not in gps_info or 4 not in gps_info:
            return None

        lat = get_decimal_from_dms(gps_info.get(2), gps_info.get(1))
        lon = get_decimal_from_dms(gps_info.get(4), gps_info.get(3))

        if lat is None or lon is None: return None
        return {'filepath': file_path, 'timestamp': timestamp, 'lat': lat, 'lon': lon}
    except Exception:
        return None

def extract_partial_data(file_path):
    """FORGIVING: For the Rescue Bot."""
    filename = os.path.basename(file_path)
    
    # 1. Grab the filename date as our baseline safety net
    timestamp = get_timestamp_from_filename(filename)

    # --- VIDEO HANDLING ---
    if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        exif_time, _, _ = get_video_metadata(file_path)
        if exif_time:
            timestamp = exif_time # ExifTool time is the most accurate
            
        if not timestamp:
            timestamp = os.path.getmtime(file_path) # Absolute last resort
            
        return {'filepath': file_path, 'timestamp': timestamp, 'lat': None, 'lon': None}

    # --- PHOTO HANDLING ---
    img = None
    try:
        img = Image.open(file_path)
        dt_str, gps_info = None, None

        if hasattr(img, 'getexif'):
            exif = img.getexif()
            if exif:
                dt_str = exif.get(306) 
                try:
                    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                    if exif_ifd and 36867 in exif_ifd: dt_str = exif_ifd[36867]
                    gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
                except AttributeError: pass
        
        if not dt_str and hasattr(img, '_getexif'):
            raw_exif = img._getexif()
            if raw_exif:
                exif_data = {ExifTags.TAGS.get(k, k): v for k, v in raw_exif.items()}
                dt_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                gps_info = exif_data.get('GPSInfo')

        # 2. Try EXIF Time
        if not timestamp and dt_str:
            try: timestamp = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S').timestamp()
            except Exception: pass
            
        # 3. FALLBACK: Use Windows File Date
        if not timestamp:
            timestamp = os.path.getmtime(file_path)

        # Try to get GPS
        lat, lon = None, None
        if gps_info and isinstance(gps_info, dict) and 2 in gps_info and 4 in gps_info:
            lat = get_decimal_from_dms(gps_info.get(2), gps_info.get(1))
            lon = get_decimal_from_dms(gps_info.get(4), gps_info.get(3))

        if timestamp or (lat is not None and lon is not None):
            return {'filepath': file_path, 'timestamp': timestamp, 'lat': lat, 'lon': lon}
        return None
        
    except Exception as e:
        print(f"Could not read data from {filename}: {e}")
        return None
    finally:
        if img:
            img.close()