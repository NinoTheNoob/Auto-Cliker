import pyautogui
import time

pyautogui.PAUSE = 0

def auto_clicker(target_x, target_y, cps, duration):
    # Calculate the delay between clicks
    # Formula: Interval = 1 / Click Per Seconds
    interval = 1/cps


    print(f"Starting in 3 secounds... GET READY")
    time.sleep(3)

    start_time = time.time()
    end_time = start_time + duration

    print("Clicking started !")

    count = 1

    while start_time < end_time:
        pyautogui.click(x=target_x, y=target_y)
        print(f"clicked here at {time.time()}")
        print(f"click number: {count}")
        #We use a small sleep to control the CPS
        # time.sleep(interval)
        count = count + 1
    
    print("Done!")

# --- SETTINGS ---
# Change these numbers to whatever you need!
X_COORD = 500
Y_COORD = 500
CLICKS_PER_SECOND = 10000
SECONDS_TO_RUN = 30

auto_clicker(X_COORD, Y_COORD, CLICKS_PER_SECOND, SECONDS_TO_RUN)