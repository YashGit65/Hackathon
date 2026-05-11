import os
import shutil
import time
import math
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
import extractor

def haversine(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance in kilometers using built-in math."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r

def get_location_name(lat, lon, geolocator):
    try:
        time.sleep(1) 
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en')
        if location and location.raw.get('address'):
            addr = location.raw['address']
            name = (addr.get('tourism') or addr.get('leisure') or addr.get('beach') or 
                    addr.get('suburb') or addr.get('neighbourhood') or addr.get('village') or 
                    addr.get('town') or addr.get('city') or addr.get('county'))
            if name: return name.replace(" ", "").lower()
    except Exception as e:
        print(f"Geocoding error: {e}")
    return "unknown_location"

def create_folders_and_copy(df, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    geolocator = Nominatim(user_agent="my_personal_photo_organizer")
    clusters = df.groupby('cluster_id')
    used_folder_paths = {} 
    cluster_centroids = [] 

    for cluster_id, cluster_df in clusters:
        if cluster_id == -1 or pd.isna(cluster_id):
            final_folder_path = os.path.join(dest_dir, "Needs_Manual_Sorting")
        else:
            avg_timestamp = cluster_df['timestamp'].median()
            dt = datetime.fromtimestamp(avg_timestamp)
            date_folder = dt.strftime("%d %b").lower() 
            
            avg_lat = cluster_df['lat'].mean()
            avg_lon = cluster_df['lon'].mean()
            loc_name = get_location_name(avg_lat, avg_lon, geolocator)
            
            base_sub_folder = loc_name
            sub_folder = base_sub_folder
            counter = 2
            
            final_folder_path = os.path.join(dest_dir, date_folder, sub_folder)
            
            while final_folder_path in used_folder_paths and used_folder_paths[final_folder_path] != cluster_id:
                sub_folder = f"{base_sub_folder} ({counter})"
                final_folder_path = os.path.join(dest_dir, date_folder, sub_folder)
                counter += 1
                
            used_folder_paths[final_folder_path] = cluster_id
            
            cluster_centroids.append({
                'path': final_folder_path,
                'time': avg_timestamp,
                'lat': avg_lat,
                'lon': avg_lon
            })

        if not os.path.exists(final_folder_path):
            os.makedirs(final_folder_path)
            
        for _, row in cluster_df.iterrows():
            filepath = row['filepath']
            filename = os.path.basename(filepath)
            dest_path = os.path.join(final_folder_path, filename)
            try: shutil.copy2(filepath, dest_path)
            except Exception: pass

    return cluster_centroids

def rescue_leftovers(manual_dir, centroids, max_hours=72, max_km=5):
    if not os.path.exists(manual_dir): return
        
    for file in os.listdir(manual_dir):
        filepath = os.path.join(manual_dir, file)
        
        # --- NEW: Add video extensions here ---
        if not os.path.isfile(filepath) or not file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.heif', '.mp4', '.mov', '.avi', '.mkv')):
            continue
            
        data = extractor.extract_partial_data(filepath)
        if not data: continue
            
        best_folder = None
        
        # CASE 1: Has Time
        if data['timestamp']:
            best_diff = float('inf')
            for c in centroids:
                diff_hours = abs(c['time'] - data['timestamp']) / 3600
                if diff_hours < best_diff and diff_hours <= max_hours:
                    best_diff = diff_hours
                    best_folder = c['path']
                    
        # CASE 2: Has GPS, Missing Time
        elif data['lat'] is not None and data['timestamp'] is None:
            best_dist = float('inf')
            for c in centroids:
                dist_km = haversine(data['lat'], data['lon'], c['lat'], c['lon'])
                if dist_km < best_dist and dist_km <= max_km:
                    best_dist = dist_km
                    best_folder = c['path']
                    
        if best_folder:
            dest_path = os.path.join(best_folder, file)
            # Use shutil.move to pull it out of the manual folder
            shutil.move(filepath, dest_path) 
            print(f"Rescued {file} -> {os.path.relpath(best_folder, start=os.path.dirname(manual_dir))}")
            
def cleanup_manual_folder(manual_dir):
    """Sweeps any leftover, unrescued files into a Miscellaneous folder."""
    if not os.path.exists(manual_dir): 
        return
        
    misc_dir = os.path.join(manual_dir, "Miscellaneous")
    
    # Check everything currently sitting in the root of the manual folder
    for item in os.listdir(manual_dir):
        item_path = os.path.join(manual_dir, item)
        
        # We only want to move FILES. We skip FOLDERS (like the 'Videos' folder)
        if os.path.isfile(item_path):
            # Create the Miscellaneous folder only if we actually need it
            if not os.path.exists(misc_dir):
                os.makedirs(misc_dir)
                
            dest_path = os.path.join(misc_dir, item)
            try:
                shutil.move(item_path, dest_path)
            except Exception as e:
                print(f"   [!] Error moving {item} to Miscellaneous: {e}")            