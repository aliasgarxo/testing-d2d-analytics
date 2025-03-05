import sys
import time

def run_campaign():
    campaign_name = sys.argv[1]
    campaign_description = sys.argv[2]
    
    print(f"Executing campaign: {campaign_name}")
    print(f"Description: {campaign_description}")
    time.sleep(5)  # Simulate work
    print("Campaign execution completed.")

if __name__ == "__main__":
    run_campaign()

