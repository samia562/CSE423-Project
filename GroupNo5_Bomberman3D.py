from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18

import math
import random
import time

Window_Width = 1000
Window_Height = 800

camera_pos = [0, 600, 600]
camera_angle = 0
camera_radius = 600
camera_height = 600
fovY = 50.0

Grid_SIZE = 15
Cell_SIZE = 40
ARENA_SIZE = Grid_SIZE * Cell_SIZE

Bomb_explode_time_S = 1.5
Flame_Range = 3
Flame_Duration_S = 0.5

enemy_step_delay_level1 = 0.45
enemy_step_delay_level2_start = 0.40
enemy_step_delay_level2_min = 0.18
enemy_L2_decrease_per_min = 0.05
enemy_speed_update_interval_sec = 60

Bomb_Carry_total = 5


freeze_mode = False                    
cheat_mode = False                     


invincibility_timer = 0.0              


final_time_value = None               


level = 1
lives = 2
bombs_available = 1
score = 0
golden_stones = 0
game_won = False
paused = False
first_person_mode = False
fp_horizontal_rotation_degree = 0.0
fp_vertical_rotation_degree = 0.0
player_orientation = 0.0  
start_time = 0.0
level_elapsed = 0.0
enemy_step_interval = enemy_step_delay_level1
next_speed_increase_t = enemy_speed_update_interval_sec
last_time = 0.0
total_paused_time = 0.0
pause_start_time = 0.0

player_x = 1
player_y = 1
player_size = Cell_SIZE * 0.3

enemies_x = []
enemies_y = []
enemies_move_accum = []

bombs_x = []
bombs_y = []
bombs_timer = []
bombs_pulse_scale = []
bombs_pulse_direction = []

Type_Life = 0
Type_Bomb = 1
Type_Golden_Stone = 2
Type_Diamond = 3  
collectibles_x = []
collectibles_y = []
collectibles_type = []
hidden_collectibles = []

grid = []  
exit_exists = False
exit_x = -1
exit_y = -1

flames_x = []
flames_y = []
flames_ttl = []

quadric = None


def world_to_screen_coords(x, y):
    sx = (x - Grid_SIZE // 2) * Cell_SIZE
    sz = (y - Grid_SIZE // 2) * Cell_SIZE
    return sx, sz

def draw_text(x, y, text, color=(1,1,1)):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def get_forward_dir():
    ang = player_orientation % 360.0
    idx = int((ang + 45) // 90) % 4  
    mapping = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    return mapping[idx]

def occupied_by_bomb(x, y):
    for i in range(len(bombs_x)):
        if bombs_x[i] == x and bombs_y[i] == y:
            return True
    return False

def is_inside_grid(x, y):
    return 0 <= x < Grid_SIZE and 0 <= y < Grid_SIZE

def tile_is_walkable(x, y):
    if not is_inside_grid(x, y):
        return False
    if grid[y][x] != 0:
        return False
    if occupied_by_bomb(x, y):
        return False
    return True

def is_game_active():
    if lives <= 0:
        return False 
    elif game_won:
        return False  
    else:
        return True 

def is_gameplay_active():
    if not is_game_active():
        return False 
    elif paused:
        return False  
    else:
        return True  

def draw_cube_halfextent(size_half):
    glutSolidCube(size_half * 2.0)

def draw_sphere(radius):
    gluSphere(quadric, radius, 20, 20)

def draw_cylinder_y(radius, height):
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, radius, radius, height, 20, 1)
    glPopMatrix()

def draw_capped_cylinder_y(radius, height):
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quadric, radius, radius, height, 20, 1)
    gluDisk(quadric, 0.0, radius, 20, 1)
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0.0, radius, 20, 1)
    glPopMatrix()
    glPopMatrix()


def init_level():
    global grid, enemies_x, enemies_y, enemies_move_accum
    global bombs_x, bombs_y, bombs_timer, bombs_pulse_scale, bombs_pulse_direction
    global flames_x, flames_y, flames_ttl
    global collectibles_x, collectibles_y, collectibles_type, hidden_collectibles
    global exit_exists, exit_x, exit_y
    global enemy_step_interval, next_speed_increase_t, level_elapsed
    global invincibility_timer, cheat_mode, freeze_mode

    
    cheat_mode = False          
    freeze_mode = False         
    invincibility_timer = 0.0

    g = []
    for y in range(Grid_SIZE):
        row = []
        for x in range(Grid_SIZE):
            row.append(0)
        g.append(row)

    
    for i in range(Grid_SIZE):
        g[0][i] = 3
        g[Grid_SIZE-1][i] = 3
        for j in (0, Grid_SIZE-1):
            g[i][j] = 3

    
    for y in range(2, Grid_SIZE - 2, 2):
        for x in range(2, Grid_SIZE - 2, 2):
            g[y][x] = 1

    
    coloumn_positions = []
    for y in range(1, Grid_SIZE-1):
        for x in range(1, Grid_SIZE-1):
            if g[y][x] == 0:
                if abs(x - 1) <= 1 and abs(y - 1) <= 1:
                    pass  
                else:
                    if random.random() < 0.4:
                        g[y][x] = 2
                        if random.random() < 0.3:
                            coloumn_positions.append((x, y))

    grid = g
    for i in range(len(coloumn_positions) - 1, 0, -1):
       j = int(random.random() * (i + 1))  
       coloumn_positions[i], coloumn_positions[j] = coloumn_positions[j], coloumn_positions[i]
    types_of_collectibles = [Type_Bomb]*4 + [Type_Life]*1 + [Type_Golden_Stone]*2 + [Type_Diamond]*1

    collectibles_x = []
    collectibles_y = []
    collectibles_type = []
    hidden_collectibles = []

    max_items = min(len(types_of_collectibles), len(coloumn_positions))
    for i in range(max_items):
        cx, cy = coloumn_positions[i]
        collectibles_x.append(cx)
        collectibles_y.append(cy)
        collectibles_type.append(types_of_collectibles[i])
        hidden_collectibles.append(True)

    enemies_x = []
    enemies_y = []
    enemies_move_accum = []

    desired_enemy_count = 4 + (level - 1) * 2
    enemy_count = 0
    attempts = 0
    while enemy_count < desired_enemy_count and attempts < 500:
        ex = random.randint(3, Grid_SIZE - 4)
        ey = random.randint(3, Grid_SIZE - 4)
        if grid[ey][ex] == 0 and not (ex == player_x and ey == player_y):
            enemies_x.append(ex)
            enemies_y.append(ey)
            enemies_move_accum.append(0.0)
            enemy_count += 1
        attempts += 1

  
    bombs_x = []
    bombs_y = []
    bombs_timer = []
    bombs_pulse_scale = []
    bombs_pulse_direction = []

    flames_x = []
    flames_y = []
    flames_ttl = []

    exit_exists = False
    exit_x = -1
    exit_y = -1


    if level == 1:
        enemy_step_interval = enemy_step_delay_level1
        next_speed_increase_t = enemy_speed_update_interval_sec
    else:
        enemy_step_interval = enemy_step_delay_level2_start
        next_speed_increase_t = enemy_speed_update_interval_sec

    globals()['enemy_step_interval'] = enemy_step_interval
    globals()['next_speed_increase_t'] = next_speed_increase_t

    level_elapsed = 0.0
    globals()['level_elapsed'] = level_elapsed

def reset_game():
    global level, lives, bombs_available, score, golden_stones
    global game_won, paused, start_time
    global player_x, player_y
    global first_person_mode, fp_horizontal_rotation_degree, fp_vertical_rotation_degree, player_orientation
    global last_time, total_paused_time, pause_start_time, level_elapsed
    global freeze_mode, cheat_mode, invincibility_timer, final_time_value

    level = 1
    lives = 2
    bombs_available = 1
    score = 0
    golden_stones = 0
    game_won = False
    paused = False
    first_person_mode = False
    fp_horizontal_rotation_degree = 0.0
    fp_vertical_rotation_degree = 0.0
    player_orientation = 0.0
    start_time = time.time()
    last_time = start_time
    total_paused_time = 0.0
    pause_start_time = 0.0
    level_elapsed = 0.0
    player_x = 1
    player_y = 1
    freeze_mode = False
    cheat_mode = False  
    invincibility_timer = 0.0
    final_time_value = None
    init_level()


def draw_player():

    blinking = False
    if invincibility_timer > 0:
        if paused==True:
            current = pause_start_time - start_time - total_paused_time
        else:
            current = time.time() - start_time - total_paused_time
        blinking = (int(current * 10) % 2 == 0)

   
    if blinking==True:
        body_col = (1.0, 0.0, 1.0)  
        head_col = (1.0, 0.0, 1.0)
        limb_col = (1.0, 0.0, 1.0)
    else:
        body_col = (0.0, 0.0, 1.0)  
        head_col = (1.0, 0.8, 0.6)
        limb_col = (0.0, 0.0, 1.0)

    sx, sz = world_to_screen_coords(player_x, player_y)
    glPushMatrix()
    glTranslatef(sx, 0, sz)
    glRotatef(player_orientation, 0, 1, 0)

    # Body
    glColor3f(*body_col)
    glPushMatrix()
    glTranslatef(0, 15, 0)
    draw_cylinder_y(8, 30)
    glPopMatrix()

    # Head
    glColor3f(*head_col)
    glPushMatrix()
    glTranslatef(0, 35, 0)
    draw_sphere(10)
    glPopMatrix()


    glColor3f(*limb_col)
    # Left arm
    glPushMatrix()
    glTranslatef(-6, 25, 0)
    glRotatef(90, 1, 0, 0)
    draw_cylinder_y(3, 16)
    glPopMatrix()
    # Right arm
    glPushMatrix()
    glTranslatef(6, 25, 0)
    glRotatef(90, 1, 0, 0)
    draw_cylinder_y(3, 16)
    glPopMatrix()

    # Legs
    glColor3f(*limb_col)
    glPushMatrix()
    glTranslatef(-5, -10, 0)
    draw_cylinder_y(3, 20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(5, -10, 0)
    draw_cylinder_y(3, 20)
    glPopMatrix()

    glPopMatrix()

def draw_enemy(ix):
    sx, sz = world_to_screen_coords(enemies_x[ix], enemies_y[ix])
    glPushMatrix()
    glTranslatef(sx, 15.0, sz)

    if freeze_mode and not cheat_mode:
        glColor3f(0.0, 1.0, 1.0)  
    else:
        glColor3f(1.0, 1.0, 0.0)  
    draw_sphere(20.0)

    
    eye_sep = 8.0
    eye_y   = 6.5
    eye_z   = 16.5
    eye_r   = 2.8
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-eye_sep * 0.5, eye_y, eye_z)
    draw_sphere(eye_r)
    glPopMatrix()
    glPushMatrix()
    glTranslatef( eye_sep * 0.5, eye_y, eye_z)
    draw_sphere(eye_r)
    glPopMatrix()

    glPopMatrix()

def draw_bomb(i):
    sx, sz = world_to_screen_coords(bombs_x[i], bombs_y[i])
    glPushMatrix()
    glTranslatef(sx, 10, sz)
    glScalef(bombs_pulse_scale[i], bombs_pulse_scale[i], bombs_pulse_scale[i])
    glColor3f(0.2, 0.2, 0.2)
    draw_sphere(15)
    glPopMatrix()

def draw_collectible(i):
    if hidden_collectibles[i]:
        return
    sx, sz = world_to_screen_coords(collectibles_x[i], collectibles_y[i])
    glPushMatrix()
    glTranslatef(sx, 10, sz)
    t = collectibles_type[i]
    if t == Type_Life:
        glColor3f(1.0, 0.0, 0.0)
        draw_sphere(6)
    elif t == Type_Bomb:
        glColor3f(0.2, 0.2, 0.2)
        draw_sphere(6)
    elif t == Type_Golden_Stone:
        glColor3f(1.0, 1.0, 0.0)
        draw_cube_halfextent(6)
    else:  
        glColor3f(1.0, 0.0, 1.0)
        glPushMatrix()
        glScalef(6.0, 6.0, 6.0)
        glutSolidOctahedron()
        glPopMatrix()
    glPopMatrix()

def draw_grid():
    
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    half_arena = ARENA_SIZE / 2
    glVertex3f(-half_arena, 0, -half_arena)
    glVertex3f(half_arena, 0, -half_arena)
    glVertex3f(half_arena, 0, half_arena)
    glVertex3f(-half_arena, 0, half_arena)
    glEnd()

    
    for y in range(Grid_SIZE):
        for x in range(Grid_SIZE):
            sx, sz = world_to_screen_coords(x, y)
            val = grid[y][x]
            if val == 1:  
                glPushMatrix()
                glTranslatef(sx, 20, sz)
                glColor3f(0.5, 0.5, 0.5)
                draw_cube_halfextent(15)
                glPopMatrix()
            elif val == 2:  
                glPushMatrix()
                glTranslatef(sx, 20, sz)
                if level == 1:
                    glColor3f(0.6, 0.3, 0.1)
                else:
                    colors = [
                        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                        (1.0, 1.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0)
                    ]
                    idx = (x + y) % len(colors)
                    glColor3f(*colors[idx])
                draw_capped_cylinder_y(15, 40)
                glPopMatrix()
            elif val == 3:  
                glPushMatrix()
                glTranslatef(sx, 25, sz)
                glColor3f(0.8, 0.8, 0.8)
                draw_cube_halfextent(20)
                glPopMatrix()

def draw_exit_door():
    if exit_exists:
        sx, sz = world_to_screen_coords(exit_x, exit_y)
        glPushMatrix()
        glTranslatef(sx, 30, sz)
        glColor3f(0.0, 1.0, 0.0)
        draw_cube_halfextent(18)
        glPopMatrix()

def draw_flames():
    if not flames_x:
        return
    glColor3f(1.0, 1.0, 0.0)
    for i in range(len(flames_x)):
        sx, sz = world_to_screen_coords(flames_x[i], flames_y[i])
        glPushMatrix()
        glTranslatef(sx, 15, sz)
        draw_cube_halfextent(10)
        glPopMatrix()


def draw_fp_hands():
    
    blinking = False
    if invincibility_timer > 0:
        if paused:
            current = pause_start_time - start_time - total_paused_time
        else:
            current = time.time() - start_time - total_paused_time
        blinking = (int(current * 10) % 2 == 0)
    limb_col = (1.0, 0.0, 1.0) if blinking else (0.0, 0.0, 1.0)

    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_DEPTH_TEST)

    arm_len = 18.0
    arm_radius = 2.8

    # Left hand
    glPushMatrix()
    glTranslatef(-12.0, -10.0, -55.0)
    glColor3f(*limb_col)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    draw_cylinder_y(arm_radius, arm_len)
    glPopMatrix()
    glTranslatef(0.0, 0.0, -arm_len)
    glutSolidSphere(5.0, 16, 16)
    glPopMatrix()

    # Right hand
    glPushMatrix()
    glTranslatef(12.0, -10.0, -55.0)
    glColor3f(*limb_col)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    draw_cylinder_y(arm_radius, arm_len)
    glPopMatrix()
    glTranslatef(0.0, 0.0, -arm_len)
    glutSolidSphere(5.0, 16, 16)
    glPopMatrix()

    glPopAttrib()


def place_bomb():
   
    global bombs_available
    if not is_gameplay_active():
        return
    if bombs_available <= 0:
        return

    fdx, fdy = get_forward_dir()
    tx = player_x + fdx
    ty = player_y + fdy

    if not is_inside_grid(tx, ty):
        return
    if grid[ty][tx] != 0:
        return
    if occupied_by_bomb(tx, ty):
        return

    bombs_x.append(tx)
    bombs_y.append(ty)
    bombs_timer.append(Bomb_explode_time_S)
    bombs_pulse_scale.append(1.0)
    bombs_pulse_direction.append(1.0)
    bombs_available -= 1

def finalize_time():
    
    global final_time_value
    if final_time_value is None:
        if paused:
            paused_offset = total_paused_time + (time.time() - pause_start_time)
        else:
            paused_offset = total_paused_time
        final_time_value = time.time() - start_time - paused_offset

def explode_bomb(bi):
    global score, lives, player_x, player_y
    hit_tiles = []

    cx = bombs_x[bi]
    cy = bombs_y[bi]
    if is_inside_grid(cx, cy):
        hit_tiles.append((cx, cy))

    for (dx, dy) in [(1,0), (-1,0), (0,1), (0,-1)]:
        for step in range(1, Flame_Range + 1):
            tx = cx + dx * step
            ty = cy + dy * step
            if not is_inside_grid(tx, ty):
                break
            val = grid[ty][tx]
            if val == 1 or val == 3:
                break
            hit_tiles.append((tx, ty))
            if val == 2:
                break

    # flames
    for (tx, ty) in hit_tiles:
        flames_x.append(tx)
        flames_y.append(ty)
        flames_ttl.append(Flame_Duration_S)

    for (tx, ty) in hit_tiles:
        if grid[ty][tx] == 2:
            grid[ty][tx] = 0
            score += 5
            for ci in range(len(collectibles_x)):
                if collectibles_x[ci] == tx and collectibles_y[ci] == ty and hidden_collectibles[ci]:
                    hidden_collectibles[ci] = False
                    break

    
    for (tx, ty) in hit_tiles:
        if tx == player_x and ty == player_y:
            if invincibility_timer <= 0:
                lives -= 1
                player_x, player_y = 1, 1
                if lives <= 0:
                    finalize_time()
            break

    
    killed = 0
    i = len(enemies_x) - 1
    while i >= 0:
        ex = enemies_x[i]
        ey = enemies_y[i]
        if (ex, ey) in hit_tiles:
            killed += 1
            enemies_x.pop(i)
            enemies_y.pop(i)
            enemies_move_accum.pop(i)
        i -= 1
    if killed > 0:
        score += 10 * killed

def check_collectibles():
    global score, lives, bombs_available, golden_stones
    global exit_exists, exit_x, exit_y, invincibility_timer
    i = len(collectibles_x) - 1
    while i >= 0:
        if not hidden_collectibles[i]:
            if collectibles_x[i] == player_x and collectibles_y[i] == player_y:
                t = collectibles_type[i]
                
                collectibles_x.pop(i)
                collectibles_y.pop(i)
                collectibles_type.pop(i)
                hidden_collectibles.pop(i)

                score += 20

                if t == Type_Life:
                    lives += 1
                elif t == Type_Bomb:
                    bombs_available = min(Bomb_Carry_total, bombs_available + 1)
                elif t == Type_Golden_Stone:
                    golden_stones += 1
                    if golden_stones >= 2 and not exit_exists:
                        attempts = 0
                        while attempts < 200:
                            rx = random.randint(1, Grid_SIZE-2)
                            ry = random.randint(1, Grid_SIZE-2)
                            if grid[ry][rx] == 0 and not occupied_by_bomb(rx, ry):
                                globals()['exit_exists'] = True
                                globals()['exit_x'] = rx
                                globals()['exit_y'] = ry
                                break
                            attempts += 1
                else:  
                    invincibility_timer = 30.0
        i -= 1

def check_exit_door():
    global score, level, golden_stones, game_won, player_x, player_y
    if exit_exists and player_x == exit_x and player_y == exit_y:
        score += 30
        if level < 2:
            level += 1
            golden_stones = 0
            player_x, player_y = 1, 1
            init_level()
        else:
            game_won = True
            score += 100
            finalize_time()

def check_player_enemy_collision():
    global lives, player_x, player_y
    for i in range(len(enemies_x)):
        if enemies_x[i] == player_x and enemies_y[i] == player_y:
            if freeze_mode and not cheat_mode:
                continue
            if invincibility_timer > 0:
                continue
            lives -= 1
            player_x, player_y = 1, 1
            if lives <= 0:
                finalize_time()
            break


def update_bombs(dt):
    global bombs_available
    i = len(bombs_x) - 1
    while i >= 0:
        bombs_timer[i] -= dt
        if bombs_pulse_direction[i] > 0:
            bombs_pulse_scale[i] += 1.1 * dt
        else:
            bombs_pulse_scale[i] -= 1.1 * dt
        if bombs_pulse_scale[i] > 1.40:
            bombs_pulse_direction[i] = -1.0
        elif bombs_pulse_scale[i] < 0.75:
            bombs_pulse_direction[i] = 1.0
        if bombs_timer[i] <= 0.0:
            explode_bomb(i)
            bombs_x.pop(i)
            bombs_y.pop(i)
            bombs_timer.pop(i)
            bombs_pulse_scale.pop(i)
            bombs_pulse_direction.pop(i)
            bombs_available = min(Bomb_Carry_total, bombs_available + 1)
        i -= 1

def update_flames(dt):
    i = len(flames_x) - 1
    while i >= 0:
        flames_ttl[i] -= dt
        if flames_ttl[i] <= 0.0:
            flames_x.pop(i)
            flames_y.pop(i)
            flames_ttl.pop(i)
        i -= 1

def update_invincibility(dt):
    global invincibility_timer
    if invincibility_timer > 0.0:
        invincibility_timer -= dt
        if invincibility_timer < 0.0:
            invincibility_timer = 0.0

def move_player(dx, dy):
    global player_x, player_y
    if not is_gameplay_active():
        return
    nx = player_x + dx
    ny = player_y + dy
    if is_inside_grid(nx, ny) and tile_is_walkable(nx, ny):
        player_x, player_y = nx, ny

def enemy_try_step(idx):
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    for i in range(len(directions) - 1, 0, -1):
      j = int(random.random() * (i + 1))
      directions[i], directions[j] = directions[j], directions[i]
    for dx, dy in directions:
        nx = enemies_x[idx] + dx
        ny = enemies_y[idx] + dy
        if tile_is_walkable(nx, ny):
            enemies_x[idx] = nx
            enemies_y[idx] = ny
            return True
    return False

def update_enemies(dt):

    if freeze_mode and not cheat_mode:
        return
    interval = enemy_step_interval
    for i in range(len(enemies_x)):
        enemies_move_accum[i] += dt
        while enemies_move_accum[i] >= interval:
            enemy_try_step(i)
            enemies_move_accum[i] -= interval

def increase_enemy_speed_level2(dt):
    global level_elapsed, enemy_step_interval, next_speed_increase_t
    if level != 2 or game_won:
        return
    level_elapsed += dt
    while level_elapsed >= next_speed_increase_t:
        new_interval = enemy_step_interval - enemy_L2_decrease_per_min
        if new_interval < enemy_step_delay_level2_min:
            new_interval = enemy_step_delay_level2_min
        enemy_step_interval = new_interval
        next_speed_increase_t += enemy_speed_update_interval_sec

def update_game(dt):
    if not is_gameplay_active():
        return
    update_enemies(dt)
    update_bombs(dt)
    update_flames(dt)
    update_invincibility(dt)
    check_collectibles()
    check_exit_door()
    check_player_enemy_collision()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, Window_Width / float(Window_Height), 1.0, 5000.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_mode:
        sx, sz = world_to_screen_coords(player_x, player_y)
        eye_y = 50
        yaw_rad = math.radians(fp_horizontal_rotation_degree)
        pitch_rad = math.radians(fp_vertical_rotation_degree)
        dir_x = math.cos(pitch_rad) * math.sin(yaw_rad)
        dir_y = math.sin(pitch_rad)
        dir_z = -math.cos(pitch_rad) * math.cos(yaw_rad)
        gluLookAt(sx, eye_y, sz,
                  sx + dir_x * 100, eye_y + dir_y * 100, sz + dir_z * 100,
                  0, 1, 0)
    else:
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0, 0, 0,
                  0, 1, 0)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    light_pos = [0, 500, 0, 1]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.35, 0.35, 0.35, 1.0))

    draw_grid()
    draw_player()
    for i in range(len(enemies_x)):
        draw_enemy(i)
    for i in range(len(bombs_x)):
        draw_bomb(i)
    draw_flames()
    for i in range(len(collectibles_x)):
        draw_collectible(i)
    draw_exit_door()

    if first_person_mode:
        draw_fp_hands()

 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, Window_Width, 0, Window_Height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if final_time_value is not None:
        time_display = int(final_time_value)
    else:
        if paused:
            paused_offset = total_paused_time + (time.time() - pause_start_time)
        else:
            paused_offset = total_paused_time
        current_time = time.time() - start_time - paused_offset
        time_display = int(current_time)

    glColor3f(1.0, 1.0, 1.0)
    draw_text(10, Window_Height - 30, f"Level: {level}")
    draw_text(10, Window_Height - 60, f"Lives: {lives}")
    draw_text(10, Window_Height - 90, f"Bombs: {bombs_available}/{Bomb_Carry_total}")
    draw_text(10, Window_Height - 120, f"Score: {score}")
    draw_text(10, Window_Height - 150, f"Stones: {golden_stones}/2")
    draw_text(10, Window_Height - 180, f"Time: {time_display}s")

    if game_won:
        blink_on = (int(time.time() * 2) % 2 == 0)
        cx = int(Window_Width * 0.40)
        cy = int(Window_Height * 0.60)
        if blink_on:
            draw_text(cx, cy, "WINNER!")
        draw_text(cx + 20, cy - 30, f"Score: {score}")
        if final_time_value is not None:
            draw_text(cx, cy - 55, f"Taken Time: {int(final_time_value)}s")
    elif lives <= 0:
        draw_text(Window_Width // 2 - 60, Window_Height // 2, "GAME OVER!")
    elif paused:
        draw_text(Window_Width // 2 - 40, Window_Height // 2, "PAUSED")

    if freeze_mode:
        draw_text(Window_Width - 160, Window_Height - 30, "FREEZE: ON")
    if cheat_mode:
        draw_text(Window_Width - 160, Window_Height - 60, "CHEAT: ON")
    if invincibility_timer > 0:
        draw_text(Window_Width - 240, Window_Height - 90, f"INVINCIBLE: {int(invincibility_timer)}s")

    glutSwapBuffers()

def idle():
    global last_time
    now = time.time()
    dt = now - last_time
    if dt < 0:
        dt = 0
    if paused:
        last_time = now
        glutPostRedisplay()
        return

    last_time = now
    increase_enemy_speed_level2(dt)
    update_game(dt)
    glutPostRedisplay()

def toggle_pause():
    global paused, pause_start_time, total_paused_time
    if is_game_active():
        if not paused:
            paused = True
            pause_start_time = time.time()
        else:
            paused = False
            total_paused_time += (time.time() - pause_start_time)

def apply_cheat_mode_changes():
    
    global enemies_x, enemies_y, enemies_move_accum
    enemies_x = []
    enemies_y = []
    enemies_move_accum = []
    
    for j in range(Grid_SIZE):
        for i in range(Grid_SIZE):
            if grid[j][i] == 2:
                grid[j][i] = 0
                for ci in range(len(collectibles_x)):
                    if collectibles_x[ci] == i and collectibles_y[ci] == j and hidden_collectibles[ci]:
                        hidden_collectibles[ci] = False
                        break

def activate_cheat_mode():

    global cheat_mode, freeze_mode
    if not cheat_mode:
        cheat_mode = True
        freeze_mode = False  
        apply_cheat_mode_changes()


def keyboardListener(key, x, y):
    global freeze_mode, player_orientation
    if key in (b'r', b'R'):
        reset_game()
        return
    if key in (b'p', b'P'):
        toggle_pause()
        return
    
    if key in (b'c', b'C'):
        if is_game_active():
            activate_cheat_mode()
        return
    
    if key in (b'f', b'F'):
        if is_game_active() and not cheat_mode:
            freeze_mode = not freeze_mode
        return

    if not is_gameplay_active():
        return

    
    fdx, fdy = get_forward_dir()
    
    ldx, ldy = (-fdy, fdx)   
    rdx, rdy = (fdy, -fdx)   

    if key in (b'w', b'W'):          
        move_player(fdx, fdy)
    elif key in (b's', b'S'):       
        move_player(-fdx, -fdy)
    elif key in (b'a', b'A'):        
        move_player(ldx, ldy)
    elif key in (b'd', b'D'):       
        move_player(rdx, rdy)
    elif key in (b'b', b'B'):        
        place_bomb()
    elif key in (b'z', b'Z'):
        player_orientation = (player_orientation - 10) % 360
    elif key in (b'x', b'X'):
        player_orientation = (player_orientation + 10) % 360

def specialKeyListener(key, x, y):
    global camera_pos, camera_angle, camera_height
    if not is_gameplay_active():
        return
    if not first_person_mode:
        if key == GLUT_KEY_UP:
            camera_height += 20
            camera_pos[1] = camera_height
        elif key == GLUT_KEY_DOWN:
            camera_height -= 20
            camera_pos[1] = camera_height
        elif key == GLUT_KEY_LEFT:
            camera_angle -= 5
            camera_pos[0] = camera_radius * math.sin(math.radians(camera_angle))
            camera_pos[2] = camera_radius * math.cos(math.radians(camera_angle))
        elif key == GLUT_KEY_RIGHT:
            camera_angle += 5
            camera_pos[0] = camera_radius * math.sin(math.radians(camera_angle))
            camera_pos[2] = camera_radius * math.cos(math.radians(camera_angle))

def mouseListener(button, state, x, y):
    global first_person_mode
    if not is_gameplay_active():
        return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode


def reshape(w, h):
    global Window_Width, Window_Height
    Window_Width = max(1, w)
    Window_Height = max(1, h)
    glViewport(0, 0, Window_Width, Window_Height)

def init_gl():
    global quadric
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glClearColor(0.1, 0.1, 0.2, 1.0)
    quadric = gluNewQuadric()

def init_game():
    global start_time, last_time, player_x, player_y
    global total_paused_time, pause_start_time, paused, level_elapsed
    global freeze_mode, cheat_mode, invincibility_timer, final_time_value
    global first_person_mode, fp_horizontal_rotation_degree, fp_vertical_rotation_degree, player_orientation

    start_time = time.time()
    last_time = start_time
    total_paused_time = 0.0
    pause_start_time = 0.0
    paused = False
    level_elapsed = 0.0
    first_person_mode = False
    fp_horizontal_rotation_degree = 0.0
    fp_vertical_rotation_degree = 0.0
    player_orientation = 0.0
    player_x = 1
    player_y = 1
    freeze_mode = False
    cheat_mode = False
    invincibility_timer = 0.0
    final_time_value = None
    init_level()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(Window_Width, Window_Height)
    glutCreateWindow(b"Bomberman 3D")

    init_gl()
    init_game()

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
