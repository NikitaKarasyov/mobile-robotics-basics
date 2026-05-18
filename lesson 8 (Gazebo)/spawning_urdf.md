# Spawn URDF робота в Gazebo

**Цель:** взять Xacro/URDF модель diff-drive робота, дополнить её плагинами Gazebo Harmonic и поместить в симуляцию.

## Что нужно добавить к чистому URDF

URDF из [урока 5](<../lesson 5 (URDF and XACRO)/understanding_URDF.md>) описывает кинематику и инерцию. Чтобы Gazebo "видел" робота как управляемый, в URDF добавляются блоки `<gazebo>`:

| Блок | Что описывает |
|---|---|
| `<gazebo>` без `reference` | Системные плагины модели (diff_drive, joint_state_publisher, ...) |
| `<gazebo reference="link_name">` | Свойства конкретного линка (сенсоры, материалы, трение) |

> Все плагины Gazebo Harmonic, которые мы используем, ставятся вместе с `ros-jazzy-ros-gz`. Имена файлов плагинов короткие (`gz-sim-diff-drive-system`), а `name` - это C++ класс системы.

## Diff-drive плагин

Минимальный блок:

```xml
<gazebo>
  <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
    <left_joint>left_front_wheel_joint</left_joint>
    <right_joint>right_front_wheel_joint</right_joint>
    
    <wheel_separation>0.44</wheel_separation> 
    <wheel_radius>0.035</wheel_radius>
    
    <odom_publish_frequency>30</odom_publish_frequency>
    <topic>cmd_vel</topic>
    <odom_topic>odom</odom_topic>
    <tf_topic>tf</tf_topic>
    <frame_id>odom</frame_id>
    <child_frame_id>base_footprint</child_frame_id>
  </plugin>
</gazebo>
```

Что произойдёт после spawn:

1. На топик Gazebo `/cmd_vel` система ждёт `gz.msgs.Twist`. Скорость переводится в задание угловой скорости двум суставам.
2. Каждые 33 мс публикуется `/odom` (`gz.msgs.Odometry`) и `/tf` с парой `odom → base_footprint`.

## Joint state publisher

Чтобы `robot_state_publisher` в ROS 2 правильно показывал колёса, ему нужны `JointState` для двух суставов. Их даёт системный плагин:

```xml
<gazebo>
  <plugin filename="gz-sim-joint-state-publisher-system"
          name="gz::sim::systems::JointStatePublisher">
    <topic>joint_states</topic>
    <joint_name>left_wheel_joint</joint_name>
    <joint_name>right_wheel_joint</joint_name>
  </plugin>
</gazebo>
```

## Полный Xacro

См. [my_robot.urdf.xacro](<../ros2_ws/src/my_robot_gazebo/urdf/my_robot.urdf.xacro>). Ключевые особенности:

- `base_link` - параллелепипед, центр совпадает с центром масс;
- два `continuous` сустава для колёс с осью `0 1 0`;
- `caster_link` - сфера в задней части базы, обеспечивает третью точку опоры;
- `base_footprint` (фрейм с z=0) - стандартный root-фрейм для Nav2;
- инерции считаются макросами `box_inertia`, `cylinder_inertia`, `sphere_inertia` - **физика Gazebo не работает без них корректно**.

## Spawn в симуляцию

Spawn в Gazebo Harmonic делает утилита `ros_gz_sim create`. Она читает URDF из топика `robot_description`, поэтому нужен `robot_state_publisher`. Сценарий:

```bash
# Терминал 1: симулятор
ros2 launch my_robot_gazebo gazebo.launch.py

# Терминал 2: разворачивает Xacro и публикует robot_description
xacro $(ros2 pkg prefix my_robot_gazebo)/share/my_robot_gazebo/urdf/my_robot.urdf.xacro > /tmp/my_robot.urdf
ros2 run robot_state_publisher robot_state_publisher /tmp/my_robot.urdf

# Терминал 3: spawn
ros2 run ros_gz_sim create \
  -name my_robot \
  -topic robot_description \
  -x 0 -y 0 -z 0.1
```

В Gazebo появится синяя коробка с двумя чёрными колёсами, красным цилиндром лидара сверху и зелёным IMU.

## Тестируем drive в шине Gazebo

`/cmd_vel` пока живёт только в шине Gazebo (без bridge!). Опубликуем туда напрямую:

```bash
gz topic -t /cmd_vel \
  -m gz.msgs.Twist \
  -p 'linear: {x: 0.2}, angular: {z: 0.5}'
```

Робот поедет по дуге. Если этого не происходит:

- проверьте `gz topic -l | grep cmd_vel` (топик должен существовать);
- проверьте `gz topic -e -t /odom -n 1` - публикуется ли одометрия;
- убедитесь, что симуляция запущена (Play в GUI).

## Контрольные проверки

- [x] Модель spawn'ится без ошибок (`Requested entity spawn` в логах).
- [x] `gz topic -l` показывает `/cmd_vel`, `/odom`, `/joint_states`, `/tf`.
- [x] Команда `gz topic -p` заставляет робота двигаться.

## Дальше

Топики ещё не в ROS 2. Подключим [ros_gz_bridge](ros_gz_bridge.md).
