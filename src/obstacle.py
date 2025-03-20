from ursina import Entity, color
import random


def spawn_obstacle_at(obstacle_z, lanes, current_level, obstacles):
    # ensure at least one free lane.
    open_lane = random.randint(0, len(lanes)-1)

    # occasionally spawn jump-obstacles (block all lanes) from lvl 3
    if current_level >= 3 and random.random() < 0.2:
        for lane in lanes:
            obstacle = Entity(
                model='cube',
                scale=(1.5, 0.8, 0.5),
                color=color.orange,
                position=(lane, 0.5, obstacle_z),
                collider='box'
            )
            obstacles.append(obstacle)
        return

    # where to spawn medium high objects
    for idx, lane in enumerate(lanes):
        if idx == open_lane:
            continue
        spawn_probability = 0.5 + (current_level - 1) * 0.1
        if random.random() < spawn_probability:
            obstacle = Entity(
                model='cube',
                scale=(1.5, 1.3, 0.5),
                color=color.black90,
                position=(lane, 0.5, obstacle_z),
                collider='box'
            )
            obstacles.append(obstacle)
