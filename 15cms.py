  GNU nano 8.4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  tog.py
"""
ONYX_walking.py — smooth simultaneous hip+knee gait (full file)

- Moves each hip+knee pair together using interpolation for smooth arcs.
- Diagonal order: (7+8 & 1+2) then (3+4 & 5+6).
- Tuning knobs at the top: HIP_OFF, KNEE_OFF, INTERP_STEPS, MOVE_DURATION, RETURN_DURATION, SETTLE.
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
    print("⚠️ No FINAL_ANGLES found. Running initializer…")
    initialize_ONYX.initialize_onyx()
    MID = initialize_ONYX.FINAL_ANGLES

print("\n🟢 Using MID angles from initialize_ONYX:")
for sid, angle in MID.items():
    print(f"  Servo {sid} = {angle:.1f}°")

# ============================
# 2) CREATE SERVO OBJECTS
# ============================
SERVOS_IDS = MID.keys()
servos = {}
for sid in SERVOS_IDS:
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
# 4) TUNING KNOBS (edit these)
# ============================
# Hip vs knee magnitude (you said knee > hip)
HIP_OFF = 15.0        # degrees, controls stride (increase to go farther)
KNEE_OFF = 25.0       # degrees, controls leg clearance/pull

# Smooth interpolation timing (start with these; tune gradually)
INTERP_STEPS = 6     # more steps -> smoother, but more commands
MOVE_DURATION = 0.08  # seconds to go from MID -> FORWARD/LIFT
RETURN_DURATION = 0.06 # seconds to return MID
SETTLE = 0.02          # short settle between diagonals

# Safety: lower bound for per-step delay
MIN_PER_STEP = 0.004

# ============================
# 5) DERIVED TARGETS (from MID)
# ============================
LIFT = {
    2: MID[2] - KNEE_OFF,
    4: MID[4] - KNEE_OFF,
    6: MID[6] - KNEE_OFF,
    8: MID[8] - KNEE_OFF,
}

FORWARD = {
    1: MID[1] - HIP_OFF,
    3: MID[3] - HIP_OFF,
    5: MID[5] + HIP_OFF,
    7: MID[7] + HIP_OFF,
}

# ============================
# 6) HELPERS: clamping, raw move, interp
# ============================
def clamp_angle(sid, angle):
    lo, hi = LIMITS.get(sid, (0, 300))
    return max(lo, min(hi, angle))

def safe_move_instant(sid, angle):
    """Issue a single move command if servo exists, clipped to limits."""
    if sid not in servos:
        return
    try:
        servos[sid].move(int(round(angle)))
    except Exception as e:
        print(f"Error moving servo {sid} to {angle}: {e}")

def interp_values(start, end, steps):
    for i in range(1, steps+1):
        t = i / steps
        yield start + (end - start) * t

def get_current_angle(sid):
    """Best-effort current angle; fallback to MID."""
    return MID.get(sid, 90)

# ============================
# 7) Smooth simultaneous pair mover
# ============================
def smooth_pair_move(hip_sid, hip_start, hip_target,
                     knee_sid, knee_start, knee_target,
                     duration=MOVE_DURATION, steps=INTERP_STEPS):
    """
    Smoothly move hip and knee from start->target in parallel over duration seconds.
    Sends both servo commands each small timestep to create continuous motion.
    """
    hip_start = clamp_angle(hip_sid, hip_start)
    hip_target = clamp_angle(hip_sid, hip_target)
    knee_start = clamp_angle(knee_sid, knee_start)
    knee_target = clamp_angle(knee_sid, knee_target)

    if steps <= 0 or duration <= 0:
        safe_move_instant(hip_sid, hip_target)
        safe_move_instant(knee_sid, knee_target)
        return

    per = max(MIN_PER_STEP, duration / steps)
    hip_seq = list(interp_values(hip_start, hip_target, steps))
    knee_seq = list(interp_values(knee_start, knee_target, steps))

    for i in range(steps):
        if hip_sid in servos:
            safe_move_instant(hip_sid, hip_seq[i])
        if knee_sid in servos:
            safe_move_instant(knee_sid, knee_seq[i])
        time.sleep(per)

# ============================
# 8) Diagonal move that uses smooth_pair_move
# ============================
def move_diagonal_pair(pair):
    hip1, knee1, hip2, knee2 = pair

    # read starts (use MID as fallback)
    h1_start = get_current_angle(hip1)
    h2_start = get_current_angle(hip2)
    k1_start = get_current_angle(knee1)
    k2_start = get_current_angle(knee2)

    # targets
    h1_t = FORWARD[hip1]
    h2_t = FORWARD[hip2]
    k1_t = LIFT[knee1]
    k2_t = LIFT[knee2]

    # 1) move both hip+knee pairs toward their forward/lift targets.
    # We call smooth_pair_move for each pair sequentially; each call smoothly moves hip & knee together.
    smooth_pair_move(hip1, h1_start, h1_t, knee1, k1_start, k1_t, duration=MOVE_DURATION, steps=INTERP_STEPS)
    smooth_pair_move(hip2, h2_start, h2_t, knee2, k2_start, k2_t, duration=MOVE_DURATION, steps=INTERP_STEPS)

    # tiny overlap/hold at the top of lift
    time.sleep(0.01)

    # 2) return both pairs to MID smoothly
    smooth_pair_move(hip1, h1_t, MID[hip1], knee1, k1_t, MID[knee1], duration=RETURN_DURATION, steps=INTERP_STEPS)
    smooth_pair_move(hip2, h2_t, MID[hip2], knee2, k2_t, MID[knee2], duration=RETURN_DURATION, steps=INTERP_STEPS)

    # settle briefly
    time.sleep(SETTLE)

# ============================
# 9) DIAGONAL ORDER & main cycle
# ============================
DIAGONAL_A = (7, 8, 1, 2)  # front right + back left
DIAGONAL_B = (3, 4, 5, 6)  # front left + back right

def walk_cycle():
    move_diagonal_pair(DIAGONAL_A)
    move_diagonal_pair(DIAGONAL_B)

# ============================
# 10) MAIN — run cycles for testing
# ============================
if __name__ == "__main__":
    print("\nONYX_smooth_gait starting with parameters:")
    print(f"HIP_OFF={HIP_OFF}, KNEE_OFF={KNEE_OFF}, INTERP_STEPS={INTERP_STEPS}")
    print(f"MOVE_DURATION={MOVE_DURATION}, RETURN_DURATION={RETURN_DURATION}, SETTLE={SETTLE}\n")

    # simple safety: ensure MID contains required servos
    required_ids = [1,2,3,4,5,6,7,8]
    missing = [s for s in required_ids if s not in MID]
    if missing:
        print(f"⚠️ WARNING: MID missing servos: {missing} — check initialize_ONYX output")

    try:
        cycles = 12
        for i in range(cycles):
            print(f"\n--- Cycle {i+1}/{cycles} ---")
            walk_cycle()
    except KeyboardInterrupt:
        print("\nInterrupted by user — stopping.")
    finally:
        print("\n🏁 Done. Measure distance traveled over {cycles} cycles to compute stride.")










