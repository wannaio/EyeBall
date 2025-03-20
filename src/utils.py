def apply_gravity(y_velocity, gravity, dt):
    return y_velocity - gravity * dt


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
