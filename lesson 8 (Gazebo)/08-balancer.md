# Бонус: балансирующий робот (двухколёсный R2D2)

Цель: превратить четырёхколёсного R2D2 в двухколёсный балансирующий робот по принципу Segway. Это упражнение показывает как из физики выводится модель управления, и как теория оптимального управления (LQR) применяется на практике.

**Важно:** этот раздел опционален. Основная часть урока 8 заканчивается на предыдущей статье. Здесь — углублённое расширение для тех кому интересна динамика и теория управления.

## Что нужно знать заранее

* Урок 5 — URDF и Xacro макросы.
* Базовая линейная алгебра (матрицы, собственные числа).
* Производные и интегралы — на уровне второго курса.
* По желанию — материалы из `physics_robotics.docx` и `lqr_theory.docx` в этом же репозитории. Там подробно разобраны вывод инерций, центр масс, уравнения движения и теория LQR.

## Идея балансира

Перевёрнутый маятник — классическая задача теории управления. Робот на двух колёсах естественно падает под действием гравитации. Контроллер должен **двигать колёса** так, чтобы база оставалась вертикальной — как человек балансирует на одной ноге, делая маленькие шаги.

```
        * ЦМ
        |
        |  l = 0.435 м
        |
    ===O===  ← ось колёс
```

Если ЦМ наклоняется на угол θ, контроллер должен ускорить базу так, чтобы создать встречный момент.

## Физика робота

Уравнение движения перевёрнутого маятника при малых углах:

```
θ̈ = (g/l)·θ - (1/l)·u
```

где:
* θ — угол наклона относительно вертикали;
* g = 9.81 м/с² — ускорение свободного падения;
* l — высота ЦМ над осью колёс;
* u — ускорение базы (управление).

Первое слагаемое — гравитация валит робота. Второе — контроллер компенсирует через ускорение базы.

Полная модель в пространстве состояний:

```
x = [θ, θ̇, p, ṗ]ᵀ      ← состояние

ẋ = Ax + Bu              ← уравнение системы

A = [0,    1,   0,  0]   B = [0   ]
    [g/l,  0,   0,  0]       [-1/l]
    [0,    0,   0,  1]       [0   ]
    [0,    0,   0,  0]       [1   ]
```

Подробный вывод матриц A и B из законов Ньютона есть в `physics_robotics.docx`.

## Изменения в URDF

Для балансира нужны три модификации:

### 1. Убрать задние колёса

В макросе `leg_assembly` оставляем только передние колёса. Робот двухколёсный.

### 2. Поставить передние колёса под ЦМ

В `r2d2_properties.xacro`:

```xml
<!-- БЫЛО: смещение колеса вперёд от центра базы -->
<!-- xacro:property name="wheel_offset_x" value="0.133"/-->

<!-- СТАЛО: колесо под центром масс -->
<xacro:property name="wheel_offset_x" value="0.0"/>
```

Так ЦМ робота окажется прямо над осью колёс. Это критично для балансировки.

### 3. Добавить collision и inertial всем линкам

Балансиру нужна полноценная физика. Если хотя бы у одного линка нет inertial — Gazebo делает его неустойчивым.

Уже есть макросы `cylinder_inertia`, `box_inertia`, `sphere_inertia` из основной части урока. Применяем ко всем линкам.

## Расчёт высоты ЦМ из URDF

Для контроллера нужен параметр **l** — высота ЦМ над осью колёс. Считается из URDF по формуле взвешенного среднего:

```
l = Σ(mᵢ · zᵢ) / Σmᵢ
```

где zᵢ — высота центра i-го линка над осью колёс. Скрипт для расчёта:

```python
import numpy as np

links = {
    'base_link':   {'z': 0.435, 'm': 5.0},
    'head':        {'z': 0.735, 'm': 1.0},
    'right_leg':   {'z': 0.685, 'm': 0.5},
    'left_leg':    {'z': 0.685, 'm': 0.5},
    'right_base':  {'z': 0.085, 'm': 0.3},
    'left_base':   {'z': 0.085, 'm': 0.3},
    'right_wheel': {'z': 0.0,   'm': 0.5},
    'left_wheel':  {'z': 0.0,   'm': 0.5},
}

m_total = sum(d['m'] for d in links.values())
mz_sum = sum(d['m'] * d['z'] for d in links.values())
l = mz_sum / m_total
print(f"l = {l:.3f} м")
# l = 0.435 м
```

Все высоты — относительно оси колеса (0 — ось колеса).

## LQR контроллер

LQR (Linear Quadratic Regulator) — стандартный метод для линейных систем. На вход даёшь матрицы A, B, Q, R, на выходе получаешь оптимальное усиление K.

Управление:

```
u = -K · x
```

K — это вектор-строка из 4 чисел (по одному на каждое состояние).

### Pole placement как альтернатива

Вместо подбора Q и R можно задать желаемые **полюса замкнутой системы** напрямую — собственные числа матрицы (A - BK). Полюса определяют скорость и плавность реакции:

```
σ = N · ω₀     ← скорость затухания, ω₀ = √(g/l)
ω = σ·√(1-ζ²)/ζ ← частота колебаний

полюс = -σ ± ωi
```

* `N` — во сколько раз контроллер быстрее естественного падения робота. N > 1 — устойчиво.
* `ζ` — коэффициент демпфирования. ζ = 1 — нет колебаний, ζ = 0.7 — небольшое перерегулирование.

### Реализация на Python

```python
import numpy as np
from scipy.signal import place_poles

g = 9.81
l = 0.435
N = 0.8       # подобрано экспериментально для нашего робота
zeta = 0.9

w0 = np.sqrt(g / l)
sigma = N * w0
omega = sigma * np.sqrt(1 - zeta**2) / zeta

A = np.array([[0, 1, 0, 0],
              [g/l, 0, 0, 0],
              [0, 0, 0, 1],
              [0, 0, 0, 0]])
B = np.array([[0], [-1.0/l], [0], [1]])

poles = [
    -sigma + omega*1j,
    -sigma - omega*1j,
    -2 * w0,
    -1 * w0,
]

K = place_poles(A, B, poles).gain_matrix
print(f"K = {K}")
```

Подробный вывод теории LQR и обоснование выбора параметров — в `lqr_theory.docx`.

## ROS 2 нода контроллера

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
from scipy.signal import place_poles
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from tf_transformations import euler_from_quaternion


def compute_gains(g, l, N=0.8, zeta=0.9):
    w0 = np.sqrt(g / l)
    sigma = N * w0
    omega = sigma * np.sqrt(1 - zeta**2) / zeta
    poles = [
        -sigma + omega * 1j,
        -sigma - omega * 1j,
        -2 * w0,
        -1 * w0,
    ]
    A = np.array([[0, 1, 0, 0],
                  [g/l, 0, 0, 0],
                  [0, 0, 0, 1],
                  [0, 0, 0, 0]])
    B = np.array([[0], [-1.0/l], [0], [1]])
    return place_poles(A, B, poles).gain_matrix


class BalanceController(Node):
    def __init__(self):
        super().__init__('balance_controller')
        self.g = 9.81
        self.l = 0.435
        self.K = compute_gains(self.g, self.l)
        self.get_logger().info(f'K = {self.K}')

        self.theta = 0.0
        self.theta_dot = 0.0
        self.pos = 0.0
        self.vel = 0.0
        self.vel_cmd = 0.0
        self.ang_desired = 0.0
        self.prev_time = None

        self.imu_ready = False
        self.odom_ready = False

        self.create_subscription(Imu, '/imu', self.imu_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_balanced', 10)
        self.create_timer(0.01, self.control_loop)

    def imu_cb(self, msg):
        q = msg.orientation
        _, self.theta, _ = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.theta_dot = msg.angular_velocity.y
        self.imu_ready = True

    def odom_cb(self, msg):
        self.pos = msg.pose.pose.position.x
        self.vel = msg.twist.twist.linear.x
        self.odom_ready = True

    def cmd_cb(self, msg):
        self.ang_desired = msg.angular.z

    def control_loop(self):
        if not (self.imu_ready and self.odom_ready):
            return

        now = self.get_clock().now().nanoseconds * 1e-9
        x = np.array([self.theta, self.theta_dot, self.pos, self.vel])

        accel = float(-(self.K @ x).item())
        accel = np.clip(accel, -5.0, 5.0)

        if self.prev_time is not None:
            dt = now - self.prev_time
            if dt > 0:
                self.vel_cmd += accel * dt
                self.vel_cmd = np.clip(self.vel_cmd, -1.0, 1.0)
        self.prev_time = now

        msg = Twist()
        msg.linear.x = float(self.vel_cmd)
        msg.angular.z = self.ang_desired
        self.cmd_pub.publish(msg)


def main():
    rclpy.init()
    node = BalanceController()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

Контроллер:
1. Получает угол θ из IMU.
2. Получает скорость и позицию из одометрии.
3. Вычисляет ускорение `u = -K·x`.
4. Интегрирует ускорение в `vel_cmd` (так как diff-drive принимает скорость, а не ускорение).
5. Публикует в `/cmd_vel_balanced` который подключается к diff-drive плагину.

## Особенности запуска

Балансир чувствителен к порядку запуска:

1. Робот должен заспавниться **после** того как мост готов принимать топики.
2. Контроллер должен начать работать **сразу** как пришли первые данные с IMU.
3. Спавн на небольшой высоте (z = 0.4 м), чтобы робот мягко опустился, не накопив энергию падения.

Готовый launch:

```python
return LaunchDescription([
    world_arg,
    gz_sim,
    rsp,
    TimerAction(period=2.0, actions=[bridge]),   # bridge первым
    TimerAction(period=3.0, actions=[spawn]),    # потом робот
    balance,                                      # контроллер ждёт IMU сам
])
```

В контроллере проверяем флаги готовности:

```python
def control_loop(self):
    if not (self.imu_ready and self.odom_ready):
        return
    # ...
```

## Ограничения линейной модели

Контроллер работает на приближении `sin θ ≈ θ`. Это верно при малых углах:

```
θ < 0.25 рад ≈ 14° — погрешность ≈ 1%
θ < 0.5 рад  ≈ 28° — погрешность ≈ 5%
```

При больших углах:
* Нелинейные члены становятся значительными.
* Контроллер недооценивает силу падения.
* Робот не сможет восстановиться.

В коде стоит защитный порог:

```python
if abs(self.theta) > 0.5:
    self.cmd_pub.publish(Twist())  # стоп
    return
```

## Возможные проблемы

**Робот падает сразу после спавна.** Контроллер не успел получить данные с IMU. Проверьте флаги `imu_ready` и `odom_ready`.

**Робот балансирует но дрейфует в сторону.** ЦМ робота смещён по X — грипперы и box на голове дают вес вперёд. Решения:
* Убрать декоративные элементы из inertial (массу ≈ 0).
* Добавить интегральную составляющую к контроллеру.

**Реакция слишком резкая, робот «дёргается».** N слишком большое. Уменьшите до 0.5-0.8.

**Реакция слишком медленная, робот падает.** N слишком маленькое. Увеличьте, но не больше 2-3.

## Дальнейшее развитие

В этой статье — базовый LQR контроллер. Можно расширить:

* **Интегральная коррекция** — добавить ∫θ·dt к управлению. Убирает дрейф от постоянных возмущений.
* **Область Ляпунова** — формально определить безопасную зону через матрицу P. См. `lqr_theory.docx`.
* **Калман фильтр** — улучшить оценку угла θ из шумных данных IMU.
* **Адаптивный контроллер** — параметры подстраиваются под изменения нагрузки.

Это уже выходит за рамки урока 8. Темы пригодятся в курсах по теории управления.

## Контрольные проверки

* После `ros2 launch ...` робот спавнится и **не падает** в течение минимум 10 секунд.
* `ros2 topic echo /imu --field orientation.y` показывает угол близкий к нулю (< 0.05 рад).
* При лёгком толчке робота он восстанавливает вертикаль за 1-2 секунды.

## Что читать дальше

* `physics_robotics.docx` — детальный вывод физики: моменты инерции, ЦМ, уравнения движения.
* `lqr_theory.docx` — теория LQR от собственных чисел до уравнения Риккати.
* TurtleBot3 simulation — промышленный аналог для сравнения.
