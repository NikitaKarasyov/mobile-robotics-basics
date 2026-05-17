# Сенсоры: лидар и IMU

**Цель:** разобраться, как Gazebo Harmonic моделирует лидар (`gpu_lidar`) и IMU, как привязать сенсор к линку URDF, как сконфигурировать частоту/диапазон и проверить данные в RViz.

## Как устроены сенсоры в Gazebo Harmonic

Сенсор - это `<sensor>`-тег внутри блока `<gazebo reference="link_name">`. Сам линк должен существовать в URDF (`<link name="lidar_link">...`), сенсор просто "вешается" на него. Поза `<pose>` задаётся относительно линка.

Для работы сенсоров в мире обязательно должны быть включены системы:

- `gz-sim-sensors-system` - для лазеров и камер (использует рендер `ogre2`),
- `gz-sim-imu-system` - для IMU.

Если их нет, `gz topic -l` не покажет сенсорных топиков.

## 2D лидар

```xml
<gazebo reference="lidar_link">
  <sensor name="lidar" type="gpu_lidar">
    <pose>0 0 0 0 0 0</pose>
    <topic>scan</topic>
    <gz_frame_id>lidar_link</gz_frame_id>
    <update_rate>10</update_rate>
    <ray>
      <scan>
        <horizontal>
          <samples>360</samples>
          <resolution>1</resolution>
          <min_angle>-3.14159</min_angle>
          <max_angle> 3.14159</max_angle>
        </horizontal>
      </scan>
      <range>
        <min>0.12</min>
        <max>8.0</max>
        <resolution>0.01</resolution>
      </range>
    </ray>
    <always_on>1</always_on>
    <visualize>true</visualize>
  </sensor>
</gazebo>
```

Ключевые параметры:

| Параметр | Значение | Заметка |
|---|---|---|
| `type` | `gpu_lidar` | Аппаратный рендер (быстрый). `lidar` - CPU-версия |
| `samples` | 360 | Размер `LaserScan.ranges` |
| `min/max_angle` | ±π | Круговой обзор |
| `update_rate` | 10 Гц | Частота `/scan` |
| `range.max` | 8.0 м | Дальность |
| `visualize` | true | Жёлтые лучи в Gazebo GUI |
| `gz_frame_id` | `lidar_link` | Какой `frame_id` уйдёт в `sensor_msgs/LaserScan` |

> Важно: `gz_frame_id` должен **совпадать с именем линка** в URDF, иначе RViz не найдёт фрейм в TF и не нарисует точки.

## IMU

```xml
<gazebo reference="imu_link">
  <sensor name="imu" type="imu">
    <topic>imu</topic>
    <gz_frame_id>imu_link</gz_frame_id>
    <update_rate>100</update_rate>
    <always_on>1</always_on>
  </sensor>
</gazebo>
```

По умолчанию IMU без шума. Если нужен реалистичный шум (для тестирования EKF):

```xml
<imu>
  <angular_velocity>
    <x><noise type="gaussian"><mean>0</mean><stddev>0.001</stddev></noise></x>
    <!-- y, z аналогично -->
  </angular_velocity>
  <linear_acceleration>
    <x><noise type="gaussian"><mean>0</mean><stddev>0.01</stddev></noise></x>
  </linear_acceleration>
</imu>
```

## Проверяем сенсоры через ROS 2

После `parameter_bridge` (см. предыдущую статью):

```bash
ros2 topic hz /scan        # ожидаем ~10 Hz
ros2 topic hz /imu         # ожидаем ~100 Hz
ros2 topic echo /scan --once
```

Видим заполненный `sensor_msgs/LaserScan` (360 значений в `ranges`, `frame_id: lidar_link`).

## Визуализация в RViz

`rviz/my_robot.rviz` уже настроен: `LaserScan` подписан на `/scan`, fixed frame - `odom`.

```bash
rviz2 -d $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/rviz/my_robot.rviz
```

В мире `obstacles.sdf` вы увидите контур комнаты и препятствий, нарисованных жёлтыми точками вокруг робота.

## Чек: вращение по IMU

В `obstacles.sdf` запустите робота, командой:

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{angular: {z: 0.8}}"
```

И смотрите:

```bash
ros2 topic echo /imu --field angular_velocity.z
```

Должно сходиться к 0.8 рад/с (± шум).

## Частые ошибки

- **`/scan` пустой**. В мире нет `gz-sim-sensors-system` или сцена пустая - лидар видит только небо.
- **RViz пишет `For frame [lidar_link]: Fixed Frame [odom] does not exist`**. TF мост не запущен или его маппинг неправильный (см. `bridge.yaml`).
- **CPU зашкаливает**. `samples=360` + `update_rate=30` на CPU-рендере = плохо. Снижайте rate или используйте `gpu_lidar`.

## Контрольные проверки

- [x] `ros2 topic hz /scan` ≈ 10 Hz, `ros2 topic hz /imu` ≈ 100 Hz.
- [x] В RViz видны жёлтые точки лидара, образующие контур препятствий.
- [x] `angular_velocity.z` IMU соответствует команде `/cmd_vel`.

## Дальше

Финальная статья урока - [Свой мир и teleop](custom_world_teleop.md).
