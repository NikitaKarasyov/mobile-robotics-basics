# Свой мир и teleop: складываем всё вместе

**Цель:** запустить итоговый сценарий - робот в кастомном мире `obstacles.sdf`, мост на все нужные топики, RViz с лидаром и одометрией, управление с клавиатуры через `teleop_twist_keyboard`.

## Структура world.sdf

Файл [worlds/obstacles.sdf](<../ros2_ws/src/my_robot_gazebo/worlds/obstacles.sdf>) - комната 6×6 м, окружённая четырьмя стенами высотой 1 м, с двумя цилиндрическими столбами и двумя коробками внутри.

Идея структуры файла:

```
<sdf>
  <world name="obstacles">
    <physics>...</physics>
    <plugin ... gz-sim-physics-system .../>
    <plugin ... gz-sim-user-commands-system .../>
    <plugin ... gz-sim-scene-broadcaster-system .../>
    <plugin ... gz-sim-sensors-system .../>
    <plugin ... gz-sim-imu-system .../>

    <light ... sun .../>
    <model name="ground_plane">...</model>

    <model name="wall_n">...</model>  <!-- 4 стены -->
    <model name="pillar_1">...</model> <!-- препятствия -->
    ...
  </world>
</sdf>
```

Каждое препятствие - `static = true` модель с одним линком и двумя геометриями (`<collision>` для физики/лидара и `<visual>` для рендера).

> Лидар видит только `<collision>` геометрию. Если препятствие визуально есть, но `<collision>` отсутствует, лучи лидара пройдут сквозь него.

## Полный launch

`launch/spawn_robot.launch.py` объединяет всё:

1. Запускает `gz_sim` с миром `obstacles.sdf`.
2. Поднимает `robot_state_publisher`, который читает `my_robot.urdf.xacro` (через `xacro.process_file`).
3. Спавнит модель командой `ros_gz_sim create`.
4. Запускает `parameter_bridge` с конфигом `bridge.yaml`.
5. Запускает RViz с `my_robot.rviz`.

Запуск одной командой:

```bash
cd ~/projects/misis/mobile-robotics-basics/ros2_ws
source install/setup.bash
ros2 launch my_robot_gazebo spawn_robot.launch.py
```

Аргументы:

```bash
ros2 launch my_robot_gazebo spawn_robot.launch.py \
  world:=obstacles.sdf \
  x:=1.0 y:=1.0 yaw:=1.57 \
  use_rviz:=true
```

## Teleop

В отдельном терминале:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Управление:

- `i`/`,` - вперёд / назад,
- `j`/`l` - поворот влево / вправо,
- `u`/`o`, `m`/`.` - дуги,
- `q`/`z` - увеличить / уменьшить общую скорость,
- `k` - стоп.

> `teleop_twist_keyboard` публикует в `/cmd_vel` тип `geometry_msgs/Twist`. Наш bridge уже настроен на этот топик в направлении `ROS_TO_GZ`.

## Что мы наблюдаем

В RViz:

- `RobotModel` - синяя база с колёсами обновляется при движении,
- `TF` - дерево `odom → base_footprint → base_link → wheels/lidar/imu`,
- `LaserScan` - жёлтые точки очерчивают стены и препятствия,
- `Odometry` - пунктирная линия пройденного пути.

В Gazebo GUI:

- модель катится по комнате,
- столкновения со стенами физически останавливают робота.

## Запись данных (ros2 bag)

Полезный навык - записать заезд для последующего анализа или для Nav2:

```bash
ros2 bag record -o teleop_run /cmd_vel /odom /scan /imu /tf /tf_static /joint_states
```

И воспроизвести:

```bash
ros2 bag play teleop_run --clock
```

Флаг `--clock` публикует `/clock` из записи, так что подписчики с `use_sim_time:=true` будут жить во времени записи.

## Headless-режим

Если работаете по SSH или в CI:

```bash
ros2 launch my_robot_gazebo spawn_robot.launch.py use_rviz:=false
# и в gz_sim передайте -s (server only) - правится в launch если нужно
```

## Контрольные проверки

- [x] `ros2 launch my_robot_gazebo spawn_robot.launch.py` поднимает Gazebo + RViz + bridge.
- [x] В RViz отображается модель робота, TF, лидар.
- [x] `teleop_twist_keyboard` двигает робота в Gazebo.
- [x] Робот не проходит сквозь стены и столбы.

## Что дальше

Этот робот - **готовый стенд для Nav2**. В [уроке 9](<../lesson 9 (NAV2)/README.md>) мы возьмём те же `/scan`, `/odom`, `/cmd_vel` и подключим стек навигации.

Если хочется ещё практики на Gazebo - добавьте RGB-камеру:

1. Линк `camera_link` в URDF.
2. Сенсор `<sensor type="camera">` с `<topic>camera/image_raw</topic>`.
3. Маппинг в `bridge.yaml` или отдельный `ros_gz_image image_bridge`.
4. Display `Image` в RViz.
