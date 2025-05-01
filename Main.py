from vpython import *
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Constants
num_robots = 6
num_obstacles = 10
num_moving_obstacles = 8
space_size = 20
max_speed = 1.0
min_speed = 0.5
moving_obstacle_speed = 0.5
neighbor_radius = 5
obstacle_radius = 0.5
robot_radius = 0.5
target_position = vector(space_size - 5, 0, 0)
target_line_y = np.linspace(-space_size / 2, space_size / 2, num_robots)
water_current = vector(0, 0, 0)
current_strength = 0.15
P0 = 101325
rho = 1000
g = 9.81

# Initialize scene
scene = canvas(title="Underwater Swarm Simulation with Water Current Control", width=800, height=600)
scene.range = space_size
scene.background = vector(0, 0.2, 0.4)
scene.ambient = vector(0.3, 0.3, 0.3)
scene.camera.pos = vector(10, 10, 10)
scene.camera.axis = vector(-10, -10, -10)

# Create robots and velocities
robots = []
velocities = []
master_index = random.randint(0, num_robots - 1)
for i in range(num_robots):
    robot = sphere(pos=vector(-space_size / 2, target_line_y[i], 0),
                   radius=robot_radius,
                   color=vector(0, 0, 0.5),
                   make_trail=True,
                   trail_type="points",
                   trail_color=color.white,
                   trail_radius=0.05)
    robots.append(robot)
    velocities.append(vector(random.uniform(0, max_speed), 
                           random.uniform(-max_speed, max_speed), 
                           0))

# Create obstacles
obstacles = []
moving_obstacles = []
for _ in range(num_obstacles):
    obstacle = box(pos=vector(random.uniform(-space_size/2, space_size/2),
                            random.uniform(-space_size/2, space_size/2),
                            0),
                 length=obstacle_radius * 2,
                 height=obstacle_radius * 2,
                 width=obstacle_radius * 2,
                 color=vector(0.5, 0, 0.2))
    obstacles.append(obstacle)
    
for i in range(num_moving_obstacles):
    moving_obstacle = obstacles.pop(random.randint(0, len(obstacles) - 1))
    random_radius = obstacle_radius * random.uniform(1, 3)
    moving_obstacle = cylinder(pos=moving_obstacle.pos,
                             axis=vector(0, 0, 1),
                             radius=random_radius,
                             color=vector(0, 0.8, 0.8),
                             opacity=0.7)
    moving_obstacle.velocity = vector(random.uniform(-moving_obstacle_speed, moving_obstacle_speed), 
                                    random.uniform(-moving_obstacle_speed, moving_obstacle_speed), 
                                    0)
    moving_obstacles.append(moving_obstacle)

# Starting and target lines
starting_line = curve(pos=[vector(-space_size, -space_size/2, 0), vector(-space_size, space_size/2, 0)],
                    color=color.yellow, radius=0.05)
target_line = curve(pos=[vector(target_position.x, -space_size/2, 0), vector(target_position.x, space_size/2, 0)],
                  color=color.yellow, radius=0.05)
current_arrow = arrow(pos=vector(0, space_size / 2 - 1, 0),
                    axis=vector(0, 0, 0),
                    color=color.white,
                    shaftwidth=0.2,
                    visible=False)

# Formations
formations = ['line', 'circle', 'triangle']
current_formation = 0

# Data storage for plotting
time_data = []
positions_data = [[] for _ in range(num_robots)]
velocities_data = [[] for _ in range(num_robots)]
pressure_data = [[] for _ in range(num_robots)]
depth_data = [[] for _ in range(num_robots)]
distance_data = [[] for _ in range(num_robots)]

# Functions
def set_formation(formation):
    if formation == 'line':
        for i, robot in enumerate(robots):
            robot.pos = vector(-space_size/2, target_line_y[i], 0)
            velocities[i] = vector(0, 0, 0)
            robot.clear_trail()
    elif formation == 'circle':
        radius = 5
        for i, robot in enumerate(robots):
            angle = (2 * np.pi / num_robots) * i
            robot.pos = vector(radius * np.cos(angle), radius * np.sin(angle), 0)
            velocities[i] = vector(0, 0, 0)
            robot.clear_trail()
    elif formation == 'triangle':
        side_length = 5
        for i, robot in enumerate(robots):
            if i < 3:
                robot.pos = vector(-side_length/2 + (side_length / 3) * i, -side_length/2, 0)
            else:
                robot.pos = vector(-side_length/2 + (side_length / 3) * (i - 3), side_length/2, 0)
            velocities[i] = vector(0, 0, 0)
            robot.clear_trail()

def change_formation():
    global current_formation
    current_formation = (current_formation + 1) % len(formations)
    set_formation(formations[current_formation])

def deform_swarm():
    for i, robot in enumerate(robots):
        robot.pos = vector(random.uniform(-space_size / 2, space_size / 2), 
                         random.uniform(-space_size / 2, space_size / 2), 
                         0)
        velocities[i] = vector(random.uniform(-max_speed, max_speed), 
                             random.uniform(-max_speed, max_speed), 
                             0)
        robot.clear_trail()

def set_current_left():
    global water_current, current_arrow
    water_current = vector(-current_strength, 0, 0)
    current_arrow.visible = True
    current_arrow.axis = vector(-2, 0, 0)

def set_current_right():
    global water_current, current_arrow
    water_current = vector(current_strength, 0, 0)
    current_arrow.visible = True
    current_arrow.axis = vector(2, 0, 0)

def calculate_pressure(depth):
    base_pressure = P0 + rho * g * depth
    if water_current.x < 0:
        return base_pressure + 5000
    elif water_current.x > 0:
        return base_pressure - 5000
    return base_pressure

def display_pressure():
    selected_robot_index = random.randint(0, num_robots - 1)
    depth = random.uniform(100, 200)
    pressure = calculate_pressure(depth)
    print(f"Robot {selected_robot_index}: Depth = {depth:.2f} m, Pressure = {pressure:.2f} Pa")

def swarm_behavior():
    global water_current
    for i in range(num_robots):
        cohesion = vector(0, 0, 0)
        separation = vector(0, 0, 0)
        alignment = vector(0, 0, 0)
        count = 0
        for j in range(num_robots):
            if i != j:
                distance = mag(robots[i].pos - robots[j].pos)
                if distance < neighbor_radius:
                    count += 1
                    cohesion += robots[j].pos
                    alignment += velocities[j]
                    separation += (robots[i].pos - robots[j].pos) / (distance**2)
        if count > 0:
            cohesion = (cohesion / count - robots[i].pos) * 0.01
            alignment = (alignment / count - velocities[i]) * 0.05
            separation = separation * 0.1
            velocities[i] += cohesion + alignment + separation
        direction_to_target = (target_position - robots[i].pos).norm()
        velocities[i] += direction_to_target * 0.1
        if water_current.x != 0:
            velocity_magnitude = mag(velocities[i])
            if velocity_magnitude > 0:
                if water_current.x < 0:
                    velocities[i] = velocities[i].norm() * min_speed
                elif water_current.x > 0:
                    velocities[i] = velocities[i].norm() * max_speed
        for obstacle in obstacles:
            distance_to_obstacle = mag(robots[i].pos - obstacle.pos)
            safe_distance = robot_radius + obstacle_radius + 0.5
            if distance_to_obstacle < safe_distance * 1.5:
                avoid_direction = (robots[i].pos - obstacle.pos).norm()
                velocities[i] += avoid_direction * 0.5
            if distance_to_obstacle < safe_distance:
                overlap = safe_distance - distance_to_obstacle
                robots[i].pos += avoid_direction * overlap * 1.5
        for moving_obstacle in moving_obstacles:
            distance_to_obstacle = mag(robots[i].pos - moving_obstacle.pos)
            safe_distance = robot_radius + moving_obstacle.radius + 0.5
            if distance_to_obstacle < safe_distance * 1.5:
                avoid_direction = (robots[i].pos - moving_obstacle.pos).norm()
                velocities[i] += avoid_direction * 0.5
            if distance_to_obstacle < safe_distance:
                overlap = safe_distance - distance_to_obstacle
                robots[i].pos += avoid_direction * overlap * 1.5
        if i == master_index:
            direction_to_target = (target_position - robots[i].pos).norm()
            velocities[i] += direction_to_target * 0.1
        else:
            direction_to_master = (robots[master_index].pos - robots[i].pos).norm()
            velocities[i] += direction_to_master * 0.05
        if robots[i].pos.x >= target_position.x:
            robots[i].pos.x = target_position.x
            robots[i].pos.y = target_line_y[i]
            velocities[i] = vector(0, 0, 0)

def show_graph():
    graph_window = tk.Tk()
    graph_window.title("Robot Position Graph")
    fig, ax = plt.subplots(figsize=(10, 6))
    for i in range(num_robots):
        ax.plot(time_data, positions_data[i], label=f'Robot {i+1}')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('X-Position (m)', fontsize=12)
    ax.set_title('Robot X-Position Over Time', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    def on_closing():
        graph_window.destroy()
        plt.close(fig)
    graph_window.protocol("WM_DELETE_WINDOW", on_closing)
    graph_window.mainloop()

def show_velocity_graph():
    graph_window = tk.Tk()
    graph_window.title("Robot Velocity Graph")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, num_robots))
    
    for i in range(num_robots):
        smoothed_velocities = np.convolve(np.abs(velocities_data[i]), np.ones(5)/5, mode='same')
        ax.plot(time_data, smoothed_velocities, 
                color=colors[i],
                linewidth=2,
                label=f'Robot {i+1}')
    
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Speed (m/s)', fontsize=12)
    ax.set_title('Robot Speed Over Time', fontsize=14)
    ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    def on_closing():
        graph_window.destroy()
        plt.close(fig)
    
    graph_window.protocol("WM_DELETE_WINDOW", on_closing)
    graph_window.mainloop()


def show_pressure_graph():
    graph_window = tk.Tk()
    graph_window.title("Robot Pressure Graph")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, num_robots))
    for i in range(num_robots):
        ax.plot(time_data, pressure_data[i], 
                color=colors[i],
                linewidth=2,
                label=f'Robot {i+1}')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Pressure (Pa)', fontsize=12)
    ax.set_title('Robot Pressure Over Time', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    def on_closing():
        graph_window.destroy()
        plt.close(fig)
    graph_window.protocol("WM_DELETE_WINDOW", on_closing)
    graph_window.mainloop()

def show_depth_graph():
    graph_window = tk.Tk()
    graph_window.title("Robot Depth Graph")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, num_robots))
    for i in range(num_robots):
        ax.plot(time_data, depth_data[i], 
                color=colors[i],
                linewidth=2,
                label=f'Robot {i+1}')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Depth (m)', fontsize=12)
    ax.set_title('Robot Depth Over Time', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    def on_closing():
        graph_window.destroy()
        plt.close(fig)
    graph_window.protocol("WM_DELETE_WINDOW", on_closing)
    graph_window.mainloop()

def show_distance_graph():
    graph_window = tk.Tk()
    graph_window.title("Robot Distance Graph")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, num_robots))
    for i in range(num_robots):
        ax.plot(time_data, distance_data[i], 
                color=colors[i],
                linewidth=2,
                label=f'Robot {i+1}')
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Distance to Target (m)', fontsize=12)
    ax.set_title('Distance to Target Over Time', fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    def on_closing():
        graph_window.destroy()
        plt.close(fig)
    graph_window.protocol("WM_DELETE_WINDOW", on_closing)
    graph_window.mainloop()

# Buttons
button(text='Change Formation', pos=scene.title_anchor, bind=change_formation)
button(text='Disperse Swarm', pos=scene.title_anchor, bind=deform_swarm)
button(text='Current Left', pos=scene.title_anchor, bind=set_current_left)
button(text='Current Right', pos=scene.title_anchor, bind=set_current_right)
button(text='Display Pressure', pos=scene.title_anchor, bind=display_pressure)
button(text='Show Position Graph', pos=scene.title_anchor, bind=show_graph)
button(text='Show Velocity Graph', pos=scene.title_anchor, bind=show_velocity_graph)
button(text='Show Pressure Graph', pos=scene.title_anchor, bind=show_pressure_graph)
button(text='Show Depth Graph', pos=scene.title_anchor, bind=show_depth_graph)
button(text='Show Distance Graph', pos=scene.title_anchor, bind=show_distance_graph)

# Set initial formation
set_formation('line')

# Simulation loop with data collection
dt = 0.1
t = 0
while True:
    rate(50)
    swarm_behavior()
    for moving_obstacle in moving_obstacles:
        moving_obstacle.pos += moving_obstacle.velocity * dt
        if abs(moving_obstacle.pos.x) > space_size / 2:
            moving_obstacle.velocity.x *= -1
        if abs(moving_obstacle.pos.y) > space_size / 2:
            moving_obstacle.velocity.y *= -1
    for i in range(num_robots):
        robots[i].pos += velocities[i] * dt
        if abs(robots[i].pos.x) > space_size / 2:
            velocities[i].x *= -1
        if abs(robots[i].pos.y) > space_size / 2:
            velocities[i].y *= -1
        if robots[i].pos.x >= target_position.x:
            robots[i].pos.x = target_position.x
            robots[i].pos.y = target_line_y[i]
            velocities[i] = vector(0, 0, 0)
    
    # Record data
    time_data.append(t)
    for i in range(num_robots):
        positions_data[i].append(robots[i].pos.x)
        velocities_data[i].append(velocities[i].x)
        # Simulate depth (since we're in 2D, we'll use a random variation)
        depth = random.uniform(100, 200)  # Simulating depth between 100-200m
        depth_data[i].append(depth)
        pressure_data[i].append(calculate_pressure(depth))
        # Calculate distance to target
        distance = mag(target_position - robots[i].pos)
        distance_data[i].append(distance)
    
    t += dt
