📸 Smart Photo Organizer
Have a massive, chaotic folder of unorganized photos and videos? Smart Photo Organizer is a lightweight, local desktop application that uses machine learning to automatically sort your memories into neat, beautifully named folders based on when and where they were taken.

Instead of scrolling through thousands of files named IMG_1023.JPG, this app turns your mess into organized events like 27 feb / bagabeach.



✨ Key Features
🧠 Smart Clustering: Uses DBSCAN machine learning to group photos together based on time gaps and physical distance.

🌍 Automatic Folder Naming: Translates raw GPS coordinates into real-world location names (e.g., beaches, towns, neighborhoods).

🚑 The "Rescue Bot": Videos and downloaded photos often lose their GPS data. The built-in Rescue Bot analyzes their timestamps and intelligently "snaps" them into the correct event folders alongside your perfect photos.

📦 ZIP Support: Don't want to extract your backups? Just drop a .zip file into the app, and it will handle the extraction for you.

🔒 100% Private: No cloud uploads. No subscriptions. Everything processes locally on your own machine.



🚀 How to Use
You don't need to install Python or know how to code to use this tool!

Download and Open: Double-click the Organizer.exe file.

Setup: The app will automatically create a folder named raw_photos right next to it, along with a quick Instructions.txt file.

Add Photos: Copy and paste all your messy photos, videos, or .zip files into the raw_photos folder.

Organize: Double-click Organizer.exe one more time.

Enjoy: Grab a coffee and watch the console do the heavy lifting!



📁 Where Do My Files Go?
Once the pipeline finishes, your files will be safely moved into two main areas:

✅ organized_events: Your flawless, finished gallery. Folders are nested by Date, and then by Location.

⚠️ Needs_Manual_Sorting: Any files that had absolutely zero metadata, or videos that were taken days apart from any other photos, are safely placed here. They are neatly divided into Videos and Miscellaneous folders so they don't get lost.



🛠️ Troubleshooting
"Why are my folders named unknown_location?"
To automatically name your folders (like "Central Park"), the app needs to securely ask OpenStreetMap for the street names. Sometimes, Windows Defender Firewall blocks unknown apps from accessing the Wi-Fi.

The Fix:

Open Windows Defender Firewall from your Start menu.

Click Allow an app or feature through Windows Defender Firewall.

Click Change settings, then Allow another app...

Browse for your Organizer.exe file and add it.

Check both the Private and Public boxes next to the app, click OK, and run it again!
