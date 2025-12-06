from pylx16a.lx16a import LX16A
import time

# ================================
# Servo limits + target angles
# ================================

SERVOS = {
    1: {"min": 110, "max": 190, "target": 160},  # back left hip
    2: {"min": 110, "max": 150, "target": 130},  # back left knee
    3: {"min": 30,  "max": 100, "target": 60},   # front left hip
    4: {"min": 10,  "max": 100, "target": 40},   # front left knee
    5: {"min": 20,  "max": 100, "target": 60},   # back right hip
    6: {"min": 60,  "max": 160, "target": 110},  # back right knee
    7: {"min": 130, "max": 210, "target": 160},  # front right hip
    8: {"min": 50,  "max": 150, "target": 120},  # front right knee
}

print("Connecting to COM4...")
LX16A.initialize("COM4")
print("Connected.\n")

# ================================
# Safe smooth-move function
# ================================

def safe_smooth_move(servo, target, lo, hi, steps=40, delay=0.02):

    cur = float(servo.get_physical_angle())

    # Clamp current angle
    cur = max(lo, min(hi, cur))

    # Clamp target
    target = max(lo, min(hi, target))

    # Create safe steps
    diff = target - cur
    step = diff / steps

    for i in range(steps):
        angle = cur + step * (i+1)
        angle = max(lo, min(hi, angle))
        servo.move(angle)
        time.sleep(delay)

# ================================
# Initialize each servo
# ================================

for sid, cfg in SERVOS.items():

    print(f"\nInitializing Servo {sid} → {cfg['target']}°")

    try:
        s = LX16A(sid)
        s.enable_torque()
        s.servo_mode()

        safe_smooth_move(
            servo=s,
            target=cfg["target"],
            lo=cfg["min"],
            hi=cfg["max"]
        )

        print(f"  ➤ Reached final angle: {s.get_physical_angle():.1f}°")

    except Exception as e:
        print(f"  ❌ Servo {sid} failed: {e}")

print("\n✅ ONYX initialized.")
