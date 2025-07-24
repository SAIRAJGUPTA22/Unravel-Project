Setup and Usage
1. Install Required Python Packages:
    pip install -r requirements.txt
   Dependencies include: requests, beautifulsoup4, schedule, pydantic, etc.

2. Run the Pipeline Manually:
    python main.py

3. Schedule the Pipeline to Run Hourly:
    python main.py --schedule

4. View Logs:
    - Main Logs: news_pipeline.log
    - Duplicate Article Warnings: logs/duplicates.log
