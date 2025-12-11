  GNU nano 8.4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                walking.py
"""
ONYX_walking.py — quick, small, overlapping diagonal gait

Behavior:
- Diagonal pairs: (7+8) & (1+2) then (3+4) & (5+6)
- Hips move first (brief), knees lift, knees extend (pull), hips return
- Overlapped moves and short sleeps for quick, rhythmic steps

Tuning knobs at top:
 - STEP_SCALE: multiply KNEE_OFF/HIP_OFF for more/less aggressiveness
 - HIP_DELAY, KNEE_DELAY, SETTLE: timing for quicker vs more stable gait

If servos stall or complain, increase HIP_DELAY/KNEE_DELAY by +0.03 and/or
reduce STEP_SCALE.
"""

import time
from pylx16a.lx16a import LX16A

# Import your initializer (expected to define initialize_onyx() and FINAL_ANGLES)
import initialize_ONYX

# ============================
# 1) LOAD MID (final angles) FROM INITIALIZER
# ============================
MID = initialize_ONYX.FINAL_ANGLES

if not MID:
    print("⚠️ No final angles found, running initialization now...")
    initialize_ONYX.initialize_onyx()
    MID = initialize_ONYX.FINAL_ANGLES

print("\n🟢 Using MID angles from initialize_ONYX:")
for sid, angle in MID.items():
    print(f"  Servo {sid} = {angle:.1f}°")

# ============================
# 2) CREATE SERVO OBJECTS
# ============================
SERVO_IDS = MID.keys()

servos = {}
for sid in SERVO_IDS:
    try:
        s = LX16A(sid)
        s.enable_torque()
        s.servo_mode()
        servos[sid] = s
    except Exception as e:
        print(f"Error creating servo {sid}: {e}")

# ============================
# 3) LIMITS (same as init)
# ============================
LIMITS = {
    1: (110, 190),
    2: (110, 150),
    3: (30, 100),
    4: (10, 100),
    5: (20, 100),
    6: (60, 160),
    7: (130, 210),
    8: (50, 150),
}

# ============================
# 4) QUICK-STEP DEFAULTS (change these to tune)
# ============================
STEP_SCALE = 1.0     # 1.0 = baseline; increase to amplify KNEE_OFF/HIP_OFF
BASE_KNEE_OFF = 23.0 # baseline knee bend
BASE_HIP_OFF  = 12.0  # baseline hip swing

KNEE_OFF = BASE_KNEE_OFF * STEP_SCALE
HIP_OFF  = BASE_HIP_OFF  * STEP_SCALE

# Timing for quick, small steps
HIP_DELAY = 0.05
KNEE_DELAY = 0.05
SETTLE = 0.03

# ============================
# 5) DERIVED MOTION TARGETS
# ============================
# Knee lift (bending up) -> smaller angle = lifted
LIFT = {
    2: MID[2] - KNEE_OFF,
    4: MID[4] - KNEE_OFF,
    6: MID[6] - KNEE_OFF,
    8: MID[8] - KNEE_OFF,
}

# Hip forward/backward (left: smaller = forward; right: larger = forward)
FORWARD = {
    1: MID[1] - HIP_OFF,   # back left hip forward
    3: MID[3] - HIP_OFF,   # front left hip forward
    5: MID[5] + HIP_OFF,   # back right hip forward
    7: MID[7] + HIP_OFF,   # front right hip forward
}

# ============================
# 6) SAFETY MOVERS / HELPERS
# ============================
def clamp_angle(sid, angle):
    lo, hi = LIMITS.get(sid, (0, 300))
    return max(lo, min(hi, angle))

def safe_move(sid, angle, suppress_msg=False):
    """Move servo if present and clip to limits. Non-blocking (no extra sleep)."""
    if sid not in servos:
        if not suppress_msg:
            print(f"⚠️ Servo {sid} not available; skipping")
        return
    angle = clamp_angle(sid, angle)
    try:
        servos[sid].move(angle)
    except Exception as e:
        print(f"Error moving servo {sid} to {angle}: {e}")

def move_servo(sid, angle, delay=0.06):
    """Move single servo and wait a short time (default tuned for quick steps)."""
    safe_move(sid, angle)
    time.sleep(delay)

def move_two(sid_a, angle_a, sid_b, angle_b, delay=0.03):
    """Issue two moves rapidly (attempt near-simultaneous) then wait."""
    safe_move(sid_a, angle_a, suppress_msg=True)
    safe_move(sid_b, angle_b, suppress_msg=True)
    time.sleep(delay)

# ============================
# 7) QUICK, OVERLAPPED DIAGONAL PAIR
#    - Hips forward briefly
#    - Immediately lift knees (overlap)
#    - Short hold
#    - Extend knees back to MID AND return hips to MID almost simultaneously
#    - Very brief settle then next diagonal
# ============================
def move_diagonal_pair_quick(pair):
    hip1, knee1, hip2, knee2 = pair

    # 1) quick hips forward for both legs (small bias)
    #    small delay so hips start moving
    move_two(hip1, FORWARD[hip1], hip2, FORWARD[hip2], delay=HIP_DELAY)

    # 2) immediately bend both knees (overlap hip/knee)
    move_two(knee1, LIFT[knee1], knee2, LIFT[knee2], delay=KNEE_DELAY)

    # 3) very short hold at top of lift so the lift is noticeable
    time.sleep(0.03)

    # 4) extend both knees to MID AND return hips to MID quickly (issued together)
    safe_move(knee1, MID[knee1], suppress_msg=True)
    safe_move(knee2, MID[knee2], suppress_msg=True)
    safe_move(hip1, MID[hip1], suppress_msg=True)
    safe_move(hip2, MID[hip2], suppress_msg=True)

    # Wait a short period that allows the larger of the hip/knee motions to finish
    time.sleep(max(HIP_DELAY, KNEE_DELAY, 0.04))

    # 5) tiny settle before next diagonal
    time.sleep(SETTLE)

# ============================
# 8) DIAGONAL PAIR DEFINITIONS (user requested order)
#    First: front right (7+8) & back left (1+2)
#    Then: front left (3+4) & back right (5+6)
# ============================
DIAGONAL_A = (7, 8, 1, 2)  # front right + back left
DIAGONAL_B = (3, 4, 5, 6)  # front left + back right

def walk_cycle_quick():
    print("\n🚶 Quick diagonal walk cycle (overlapped hips+knees)…")
    move_diagonal_pair_quick(DIAGONAL_A)
    move_diagonal_pair_quick(DIAGONAL_B)

# ============================
# 9) MAIN — run a few cycles for testing
# ============================
if __name__ == "__main__":
    print(f"\nSTEP_SCALE={STEP_SCALE}, KNEE_OFF={KNEE_OFF:.1f}, HIP_OFF={HIP_OFF:.1f}")
    print(f"HIP_DELAY={HIP_DELAY}, KNEE_DELAY={KNEE_DELAY}, SETTLE={SETTLE}")
    # safety check: ensure MID contains required servos
    required_ids = [1,2,3,4,5,6,7,8]
    missing = [s for s in required_ids if s not in MID]
    if missing:
        print(f"⚠️ WARNING: MID missing servos: {missing} — check initialize_ONYX output")

    # Run multiple cycles to let gait stabilize
    try:
        for i in range(15):
            print(f"\n--- Cycle {i+1} ---")
            walk_cycle_quick()
    except KeyboardInterrupt:
        print("\nInterrupted by user — stopping.")
    finally:
        print("\n🏁 Done.")





