#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D ИГРА НА PyQt6 + OpenGL
=========================
Простой 3D-шутер от первого лица: лабиринт из стен, враги (кубы),
которые нужно расстрелять, пока они не добрались до игрока.

Управление:
  W A S D   - движение
  мышь      - осмотр (зажми ЛКМ и таскай, либо включён захват курсора)
  ЛКМ       - выстрел
  ESC       - выход / освобождение курсора
  R         - рестарт после смерти/победы

Установка зависимостей:
  pip install PyQt6 PyOpenGL PyOpenGL_accelerate

Запуск:
  python game3d.py
"""

import sys
import math
import random
import time

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluNewQuadric, gluSphere, gluCylinder


# ------------------------------------------------------------------
#                         НАСТРОЙКИ ИГРЫ
# ------------------------------------------------------------------

WORLD_SIZE = 20.0          # половина размера квадратного мира
WALL_HEIGHT = 3.0
PLAYER_SPEED = 6.0
PLAYER_RADIUS = 0.4
MOUSE_SENS = 0.15
FOV = 70.0
NUM_ENEMIES = 8
ENEMY_SPEED = 1.6
ENEMY_SIZE = 0.5
BULLET_SPEED = 30.0
PLAYER_MAX_HP = 100
ENEMY_DAMAGE = 12          # урон, наносимый врагом за столкновение
FIRE_COOLDOWN = 0.25

# Список стен лабиринта: (x1, z1, x2, z2) — отрезки прямоугольных стен.
# Формируем простой лабиринт вручную.
MAZE_WALLS = [
    (-20, -20, 20, -20),
    (-20, 20, 20, 20),
    (-20, -20, -20, 20),
    (20, -20, 20, 20),

    (-12, -20, -12, -4),
    (-12, -4, -4, -4),
    (-4, -20, -4, -10),

    (4, -20, 4, -6),
    (4, -6, 12, -6),
    (12, -20, 12, -6),

    (-16, 0, -6, 0),
    (-6, 0, -6, 10),

    (0, 4, 0, 16),
    (0, 4, 10, 4),

    (6, 6, 6, 18),
    (6, 18, 16, 18),

    (-16, 8, -16, 18),
    (-16, 18, -8, 18),
]


# ------------------------------------------------------------------
#                     ВСПОМОГАТЕЛЬНАЯ ГЕОМЕТРИЯ
# ------------------------------------------------------------------

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


def closest_point_on_segment(px, pz, x1, z1, x2, z2):
    dx, dz = x2 - x1, z2 - z1
    length2 = dx * dx + dz * dz
    if length2 == 0:
        return x1, z1
    t = ((px - x1) * dx + (pz - z1) * dz) / length2
    t = max(0.0, min(1.0, t))
    return x1 + t * dx, z1 + t * dz


def circle_segment_collision(px, pz, radius, x1, z1, x2, z2):
    cx, cz = closest_point_on_segment(px, pz, x1, z1, x2, z2)
    d2 = dist2(px, pz, cx, cz)
    if d2 < radius * radius:
        d = math.sqrt(d2) if d2 > 1e-9 else 1e-9
        overlap = radius - d
        nx = (px - cx) / d
        nz = (pz - cz) / d
        return True, nx * overlap, nz * overlap
    return False, 0.0, 0.0


# ------------------------------------------------------------------
#                            СУЩНОСТИ
# ------------------------------------------------------------------

class Enemy:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.alive = True
        self.hit_flash = 0.0

    def update(self, dt, player_x, player_z):
        if not self.alive:
            return
        dx = player_x - self.x
        dz = player_z - self.z
        d = math.hypot(dx, dz)
        if d > 0.01:
            dx /= d
            dz /= d
        new_x = self.x + dx * ENEMY_SPEED * dt
        new_z = self.z + dz * ENEMY_SPEED * dt

        # столкновение со стенами - просто не пускаем сквозь них
        blocked = False
        for (x1, z1, x2, z2) in MAZE_WALLS:
            hit, px, pz = circle_segment_collision(new_x, new_z, ENEMY_SIZE, x1, z1, x2, z2)
            if hit:
                blocked = True
                break
        if not blocked:
            self.x, self.z = new_x, new_z

        if self.hit_flash > 0:
            self.hit_flash -= dt


class Bullet:
    def __init__(self, x, y, z, dx, dy, dz):
        self.x, self.y, self.z = x, y, z
        self.dx, self.dy, self.dz = dx, dy, dz
        self.life = 3.0

    def update(self, dt):
        self.x += self.dx * BULLET_SPEED * dt
        self.y += self.dy * BULLET_SPEED * dt
        self.z += self.dz * BULLET_SPEED * dt
        self.life -= dt


# ------------------------------------------------------------------
#                        ГЛАВНЫЙ WIDGET
# ------------------------------------------------------------------

class GameWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # состояние игрока
        self.px, self.py, self.pz = 0.0, 1.6, 0.0
        self.yaw = 0.0     # поворот вокруг Y (градусы)
        self.pitch = 0.0   # наклон вверх/вниз (градусы)
        self.hp = PLAYER_MAX_HP
        self.score = 0
        self.game_over = False
        self.win = False

        self.keys = set()
        self.mouse_captured = False
        self.last_shot_time = 0.0

        self.enemies = []
        self.bullets = []
        self.spawn_enemies()

        self.last_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)  # ~60 fps

        self.quadric = None

    # ---------------- инициализация сцены ----------------

    def spawn_enemies(self):
        self.enemies = []
        random.seed()
        placed = 0
        attempts = 0
        while placed < NUM_ENEMIES and attempts < 500:
            attempts += 1
            x = random.uniform(-WORLD_SIZE + 2, WORLD_SIZE - 2)
            z = random.uniform(-WORLD_SIZE + 2, WORLD_SIZE - 2)
            if dist2(x, z, 0, 0) < 25:
                continue
            collides = False
            for (x1, z1, x2, z2) in MAZE_WALLS:
                hit, _, _ = circle_segment_collision(x, z, ENEMY_SIZE + 0.3, x1, z1, x2, z2)
                if hit:
                    collides = True
                    break
            if collides:
                continue
            self.enemies.append(Enemy(x, z))
            placed += 1

    def restart(self):
        self.px, self.py, self.pz = 0.0, 1.6, 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.hp = PLAYER_MAX_HP
        self.score = 0
        self.game_over = False
        self.win = False
        self.bullets = []
        self.spawn_enemies()

    # ---------------- OpenGL setup ----------------

    def initializeGL(self):
        glClearColor(0.53, 0.7, 0.9, 1.0)  # цвет неба
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.3, 1.0, 0.3, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.35, 0.35, 0.35, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.9, 1.0])
        self.quadric = gluNewQuadric()

    def resizeGL(self, w, h):
        glViewport(0, 0, max(w, 1), max(h, 1))

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = max(self.width(), 1)
        h = max(self.height(), 1)
        aspect = w / h

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, aspect, 0.05, 200.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # камера от первого лица
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        look_x = self.px + math.sin(rad_yaw) * math.cos(rad_pitch)
        look_y = self.py + math.sin(rad_pitch)
        look_z = self.pz - math.cos(rad_yaw) * math.cos(rad_pitch)

        self._gl_look_at(self.px, self.py, self.pz, look_x, look_y, look_z, 0, 1, 0)

        self.draw_ground()
        self.draw_walls()
        self.draw_enemies()
        self.draw_bullets()

        # HUD рисуем поверх в 2D
        self.draw_hud(w, h)

    def _gl_look_at(self, ex, ey, ez, cx, cy, cz, ux, uy, uz):
        # ручная реализация gluLookAt через glLoadIdentity+вращения проще:
        fx, fy, fz = cx - ex, cy - ey, cz - ez
        flen = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
        fx, fy, fz = fx / flen, fy / flen, fz / flen

        # up x forward -> right? используем классическую формулу
        sx = fy * uz - fz * uy
        sy = fz * ux - fx * uz
        sz = fx * uy - fy * ux
        slen = math.sqrt(sx * sx + sy * sy + sz * sz) or 1.0
        sx, sy, sz = sx / slen, sy / slen, sz / slen

        ux2 = sy * fz - sz * fy
        uy2 = sz * fx - sx * fz
        uz2 = sx * fy - sy * fx

        m = [
            sx, ux2, -fx, 0.0,
            sy, uy2, -fy, 0.0,
            sz, uz2, -fz, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]
        glMultMatrixf(m)
        glTranslatef(-ex, -ey, -ez)

    # ---------------- отрисовка сцены ----------------

    def draw_ground(self):
        glColor3f(0.35, 0.55, 0.3)
        s = WORLD_SIZE
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-s, 0, -s)
        glVertex3f(-s, 0, s)
        glVertex3f(s, 0, s)
        glVertex3f(s, 0, -s)
        glEnd()

        # потолок (просто для атмосферы, тёмный)
        glColor3f(0.15, 0.15, 0.2)
        glBegin(GL_QUADS)
        glNormal3f(0, -1, 0)
        glVertex3f(-s, WALL_HEIGHT, -s)
        glVertex3f(s, WALL_HEIGHT, -s)
        glVertex3f(s, WALL_HEIGHT, s)
        glVertex3f(-s, WALL_HEIGHT, s)
        glEnd()

    def draw_walls(self):
        glColor3f(0.65, 0.6, 0.55)
        for (x1, z1, x2, z2) in MAZE_WALLS:
            dx, dz = x2 - x1, z2 - z1
            length = math.hypot(dx, dz)
            if length < 1e-6:
                continue
            nx, nz = -dz / length, dx / length  # нормаль к стене
            thickness = 0.15

            ax1 = x1 + nx * thickness
            az1 = z1 + nz * thickness
            ax2 = x1 - nx * thickness
            az2 = z1 - nz * thickness
            bx1 = x2 + nx * thickness
            bz1 = z2 + nz * thickness
            bx2 = x2 - nx * thickness
            bz2 = z2 - nz * thickness

            glBegin(GL_QUADS)
            # передняя грань
            glNormal3f(nx, 0, nz)
            glVertex3f(ax1, 0, az1)
            glVertex3f(ax1, WALL_HEIGHT, az1)
            glVertex3f(bx1, WALL_HEIGHT, bz1)
            glVertex3f(bx1, 0, bz1)
            # задняя грань
            glNormal3f(-nx, 0, -nz)
            glVertex3f(bx2, 0, bz2)
            glVertex3f(bx2, WALL_HEIGHT, bz2)
            glVertex3f(ax2, WALL_HEIGHT, az2)
            glVertex3f(ax2, 0, az2)
            # верх
            glNormal3f(0, 1, 0)
            glVertex3f(ax1, WALL_HEIGHT, az1)
            glVertex3f(ax2, WALL_HEIGHT, az2)
            glVertex3f(bx2, WALL_HEIGHT, bz2)
            glVertex3f(bx1, WALL_HEIGHT, bz1)
            glEnd()

    def draw_enemies(self):
        for e in self.enemies:
            if not e.alive:
                continue
            glPushMatrix()
            glTranslatef(e.x, ENEMY_SIZE, e.z)
            if e.hit_flash > 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.8, 0.15, 0.15)
            self.draw_cube(ENEMY_SIZE)
            glPopMatrix()

    def draw_cube(self, s):
        glBegin(GL_QUADS)
        # +x
        glNormal3f(1, 0, 0)
        glVertex3f(s, -s, -s); glVertex3f(s, s, -s); glVertex3f(s, s, s); glVertex3f(s, -s, s)
        # -x
        glNormal3f(-1, 0, 0)
        glVertex3f(-s, -s, s); glVertex3f(-s, s, s); glVertex3f(-s, s, -s); glVertex3f(-s, -s, -s)
        # +y
        glNormal3f(0, 1, 0)
        glVertex3f(-s, s, -s); glVertex3f(-s, s, s); glVertex3f(s, s, s); glVertex3f(s, s, -s)
        # -y
        glNormal3f(0, -1, 0)
        glVertex3f(-s, -s, s); glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s); glVertex3f(s, -s, s)
        # +z
        glNormal3f(0, 0, 1)
        glVertex3f(-s, -s, s); glVertex3f(s, -s, s); glVertex3f(s, s, s); glVertex3f(-s, s, s)
        # -z
        glNormal3f(0, 0, -1)
        glVertex3f(s, -s, -s); glVertex3f(-s, -s, -s); glVertex3f(-s, s, -s); glVertex3f(s, s, -s)
        glEnd()

    def draw_bullets(self):
        glColor3f(1.0, 0.9, 0.2)
        for b in self.bullets:
            glPushMatrix()
            glTranslatef(b.x, b.y, b.z)
            gluSphere(self.quadric, 0.06, 8, 8)
            glPopMatrix()

    def draw_hud(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        # прицел
        glColor3f(1, 1, 1)
        cx, cy = w / 2, h / 2
        glBegin(GL_LINES)
        glVertex2f(cx - 10, cy)
        glVertex2f(cx + 10, cy)
        glVertex2f(cx, cy - 10)
        glVertex2f(cx, cy + 10)
        glEnd()

        # полоска HP (простая рамка+заливка)
        hp_ratio = max(0.0, self.hp / PLAYER_MAX_HP)
        bar_w, bar_h = 200, 20
        bx, by = 20, h - 40
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(bx, by); glVertex2f(bx + bar_w, by)
        glVertex2f(bx + bar_w, by + bar_h); glVertex2f(bx, by + bar_h)
        glEnd()
        glColor3f(1.0 - hp_ratio, hp_ratio, 0.1)
        glBegin(GL_QUADS)
        glVertex2f(bx, by); glVertex2f(bx + bar_w * hp_ratio, by)
        glVertex2f(bx + bar_w * hp_ratio, by + bar_h); glVertex2f(bx, by + bar_h)
        glEnd()

        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # текстовый HUD через QPainter поверх (после релиза контекста paintGL это делает overlay-виджет)

    # ---------------- игровой цикл ----------------

    def game_loop(self):
        now = time.time()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now

        if not self.game_over:
            self.handle_movement(dt)
            self.update_bullets(dt)
            self.update_enemies(dt)
            self.check_player_hp()

        self.update()  # перерисовка

    def handle_movement(self, dt):
        rad_yaw = math.radians(self.yaw)
        forward_x, forward_z = math.sin(rad_yaw), -math.cos(rad_yaw)
        right_x, right_z = math.cos(rad_yaw), math.sin(rad_yaw)

        move_x, move_z = 0.0, 0.0
        if Qt.Key.Key_W in self.keys:
            move_x += forward_x; move_z += forward_z
        if Qt.Key.Key_S in self.keys:
            move_x -= forward_x; move_z -= forward_z
        if Qt.Key.Key_A in self.keys:
            move_x -= right_x; move_z -= right_z
        if Qt.Key.Key_D in self.keys:
            move_x += right_x; move_z += right_z

        mlen = math.hypot(move_x, move_z)
        if mlen > 1e-6:
            move_x, move_z = move_x / mlen, move_z / mlen
            new_x = self.px + move_x * PLAYER_SPEED * dt
            new_z = self.pz + move_z * PLAYER_SPEED * dt

            # коллизии со стенами (раздельно по осям для скольжения)
            test_x, test_z = new_x, self.pz
            blocked_x = self.collides_with_walls(test_x, test_z)
            if not blocked_x:
                self.px = new_x
            test_x, test_z = self.px, new_z
            blocked_z = self.collides_with_walls(test_x, test_z)
            if not blocked_z:
                self.pz = new_z

        # ограничение по границам мира
        limit = WORLD_SIZE - 0.3
        self.px = max(-limit, min(limit, self.px))
        self.pz = max(-limit, min(limit, self.pz))

    def collides_with_walls(self, x, z):
        for (x1, z1, x2, z2) in MAZE_WALLS:
            hit, _, _ = circle_segment_collision(x, z, PLAYER_RADIUS, x1, z1, x2, z2)
            if hit:
                return True
        return False

    def update_bullets(self, dt):
        alive_bullets = []
        for b in self.bullets:
            b.update(dt)
            if b.life <= 0:
                continue
            hit_something = False
            for e in self.enemies:
                if not e.alive:
                    continue
                if dist2(b.x, b.z, e.x, e.z) < (ENEMY_SIZE + 0.15) ** 2 and abs(b.y - ENEMY_SIZE) < ENEMY_SIZE + 0.3:
                    e.alive = False
                    self.score += 10
                    hit_something = True
                    break
            if hit_something:
                continue
            # столкновение со стенами
            wall_hit = False
            for (x1, z1, x2, z2) in MAZE_WALLS:
                hit, _, _ = circle_segment_collision(b.x, b.z, 0.05, x1, z1, x2, z2)
                if hit:
                    wall_hit = True
                    break
            if wall_hit:
                continue
            alive_bullets.append(b)
        self.bullets = alive_bullets

        if all(not e.alive for e in self.enemies):
            self.game_over = True
            self.win = True

    def update_enemies(self, dt):
        for e in self.enemies:
            e.update(dt, self.px, self.pz)
            if e.alive and dist2(e.x, e.z, self.px, self.pz) < (ENEMY_SIZE + PLAYER_RADIUS) ** 2:
                self.hp -= ENEMY_DAMAGE * dt
                # немного оттолкнуть врага, чтобы не наносил урон бесконечно за кадр
                e.hit_flash = 0.05

    def check_player_hp(self):
        if self.hp <= 0:
            self.hp = 0
            self.game_over = True
            self.win = False

    def shoot(self):
        now = time.time()
        if now - self.last_shot_time < FIRE_COOLDOWN:
            return
        self.last_shot_time = now
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        dx = math.sin(rad_yaw) * math.cos(rad_pitch)
        dy = math.sin(rad_pitch)
        dz = -math.cos(rad_yaw) * math.cos(rad_pitch)
        self.bullets.append(Bullet(self.px, self.py, self.pz, dx, dy, dz))

    # ---------------- ввод ----------------

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.release_mouse()
            return
        if key == Qt.Key.Key_R and self.game_over:
            self.restart()
            return
        self.keys.add(key)

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def mousePressEvent(self, event):
        if not self.mouse_captured:
            self.capture_mouse()
            return
        if event.button() == Qt.MouseButton.LeftButton and not self.game_over:
            self.shoot()

    def mouseMoveEvent(self, event):
        if not self.mouse_captured:
            return
        center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        current = event.globalPosition().toPoint()
        dx = current.x() - center.x()
        dy = current.y() - center.y()
        if dx == 0 and dy == 0:
            return
        self.yaw += dx * MOUSE_SENS
        self.pitch -= dy * MOUSE_SENS
        self.pitch = max(-89.0, min(89.0, self.pitch))
        QCursor.setPos(center)

    def capture_mouse(self):
        self.mouse_captured = True
        self.setCursor(Qt.CursorShape.BlankCursor)
        center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        QCursor.setPos(center)

    def release_mouse(self):
        self.mouse_captured = False
        self.unsetCursor()


# ------------------------------------------------------------------
#                    ОВЕРЛЕЙ С ТЕКСТОМ (QPainter)
# ------------------------------------------------------------------

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QFont, QColor


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Лабиринт-шутер — PyQt6 + OpenGL")
        self.resize(1000, 700)

        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)

        self.game = GameWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.game)

        self.overlay_timer = QTimer()
        self.overlay_timer.timeout.connect(self.update)
        self.overlay_timer.start(50)

    def paintEvent(self, event):
        # Рисуем текстовый HUD прямо на этом виджете НАД OpenGL виджетом невозможно
        # стандартным способом (разные слои). Поэтому текст выводим в title и
        # через простую надпись, встроенную в сам QOpenGLWidget не получится в Qt-way -
        # вместо этого обновляем заголовок окна с информацией о состоянии игры.
        g = self.game
        status = ""
        if g.game_over:
            status = "  |  ПОБЕДА! Нажми R для рестарта" if g.win else "  |  ВЫ ПОГИБЛИ. Нажми R для рестарта"
        alive = sum(1 for e in g.enemies if e.alive)
        self.setWindowTitle(
            f"3D Лабиринт-шутер — HP: {int(g.hp)}  Очки: {g.score}  Врагов осталось: {alive}{status}"
        )

    def keyPressEvent(self, event):
        self.game.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.game.keyReleaseEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
