# Сенсоры: IMU и лидар

Цель: добавить роботу два сенсора, нужных для дальнейшей навигации: IMU (инерциальное измерительное устройство) и лазерный дальномер. Оба пробрасываются через мост в ROS 2 и визуализируются в RViz.

## Как сенсоры работают в Gazebo

Сенсор в Gazebo — это **тег `<sensor>` внутри линка**. Он привязан к определённому фрейму на роботе. Когда симуляция работает, Gazebo генерирует данные сенсора (с учётом физики и опционального шума) и публикует их в свой топик.

Чтобы данные попали в ROS 2 — добавляем сенсорный топик в мост.

В URDF сенсор оборачивается в тег `<gazebo reference="имя_линка">`.

## IMU

IMU измеряет линейные ускорения и угловые скорости. Используется для оценки ориентации робота, балансировки, навигации.

### Линк для IMU

Сначала добавим в URDF (`r2d2.urdf.xacro`) линк-крепление:

```xml
<link name="imu_link">
  <inertial>
    <mass value="0.01"/>
    <inertia ixx="1e-6" ixy="0" ixz="0"
             iyy="1e-6" iyz="0"
             izz="1e-6"/>
  </inertial>
</link>

<joint name="imu_joint" type="fixed">
  <parent link="base_link"/>
  <child link="imu_link"/>
  <origin xyz="0 0 0"/>
</joint>
```

Линк практически без массы — IMU физический объект малый. Крепится в центре `base_link`.

### Плагин сенсора

В `r2d2_gazebo.xacro`:

```xml
<gazebo reference="imu_link">
  <sensor name="imu_sensor" type="imu">
    <always_on>true</always_on>
    <update_rate>100</update_rate>
    <topic>imu</topic>
    <gz_frame_id>imu_link</gz_frame_id>
    <imu>
      <angular_velocity>
        <x><noise type="gaussian"><mean>0</mean><stddev>0.009</stddev></noise></x>
        <y><noise type="gaussian"><mean>0</mean><stddev>0.009</stddev></noise></y>
        <z><noise type="gaussian"><mean>0</mean><stddev>0.009</stddev></noise></z>
      </angular_velocity>
      <linear_acceleration>
        <x><noise type="gaussian"><mean>0</mean><stddev>0.021</stddev></noise></x>
        <y><noise type="gaussian"><mean>0</mean><stddev>0.021</stddev></noise></y>
        <z><noise type="gaussian"><mean>0</mean><stddev>0.021</stddev></noise></z>
      </linear_acceleration>
    </imu>
  </sensor>
</gazebo>
```

* `update_rate` — частота публикации в Гц.
* `topic` — имя топика в шине Gazebo.
* `gz_frame_id` — frame в котором даются данные.
* `noise` — гауссов шум, имитирует реальный сенсор. Без шума IMU будет давать идеальные значения, что нереалистично.

Stddev `0.009` для гироскопа и `0.021` для акселерометра — типичные значения для MPU-6050.

### Активация системного плагина IMU

В `worlds/blue.sdf` (или `empty.sdf`) должен быть подключён системный плагин:

```xml
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
```

Без него Gazebo не активирует сенсоры IMU.

### Мостим IMU

В `config/ros_gz_bridge.yaml` добавляем:

```yaml
- ros_topic_name: "imu"
  gz_topic_name: "imu"
  ros_type_name: "sensor_msgs/msg/Imu"
  gz_type_name: "gz.msgs.IMU"
  direction: GZ_TO_ROS
```

После пересборки и запуска:

```bash
ros2 topic echo /imu --once
```

Покажет ориентацию (`orientation`), угловые скорости (`angular_velocity`) и линейные ускорения (`linear_acceleration`).

## Лидар

Лидар сканирует окружение лучами и возвращает расстояния до препятствий — основа SLAM и obstacle avoidance.

### Линк для лидара

В `r2d2.urdf.xacro`:

```xml
<link name="lidar_link">
  <visual>
    <geometry>
      <cylinder length="0.05" radius="0.05"/>
    </geometry>
    <material name="black"/>
  </visual>
  <collision>
    <geometry>
      <cylinder length="0.05" radius="0.05"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="0.1"/>
    <inertia ixx="1e-4" ixy="0" ixz="0"
             iyy="1e-4" iyz="0"
             izz="1e-4"/>
  </inertial>
</link>

<joint name="lidar_joint" type="fixed">
  <parent link="base_link"/>
  <child link="lidar_link"/>
  <origin xyz="0 0 0.35"/>
</joint>
```

Крепится на верх корпуса, чтобы не цеплять собственные детали робота.

### Плагин лидара

В `r2d2_gazebo.xacro`:

```xml
<gazebo reference="lidar_link">
  <sensor name="lidar" type="gpu_lidar">
    <always_on>true</always_on>
    <update_rate>10</update_rate>
    <topic>scan</topic>
    <gz_frame_id>lidar_link</gz_frame_id>
    <lidar>
      <scan>
        <horizontal>
          <samples>360</samples>
          <min_angle>-3.14</min_angle>
          <max_angle>3.14</max_angle>
        </horizontal>
      </scan>
      <range>
        <min>0.1</min>
        <max>10.0</max>
        <resolution>0.01</resolution>
      </range>
      <noise>
        <type>gaussian</type>
        <mean>0.0</mean>
        <stddev>0.01</stddev>
      </noise>
    </lidar>
  </sensor>
</gazebo>
```

* `gpu_lidar` — версия использующая GPU, быстрее CPU варианта. Если GPU нет, поменяйте на `ray`.
* `samples=360` — точек на оборот, по одному на градус.
* `min_angle/max_angle` — 360° обзор (`-π` до `+π`).
* `range` — расстояние от 10 см до 10 м.

### Системный плагин лидара

Лидар требует рендеринг, поэтому работает через `gz-sim-sensors-system`. Он уже подключён в `blue.sdf`:

```xml
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
```

### Мостим лидар

В YAML:

```yaml
- ros_topic_name: "scan"
  gz_topic_name: "scan"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS
```

После пересборки и запуска:

```bash
ros2 topic hz /scan
```

Должно показать ~10 Гц.

```bash
ros2 topic echo /scan --once
```

Покажет массив дальностей в 360 точек.

## Визуализация в RViz

```bash
rviz2
```

Настройки:
* **Fixed Frame** — `odom`
* Добавить **LaserScan** — топик `/scan`, цвет точек по дальности
* Добавить **RobotModel** — описание из `/robot_description`
* Добавить **TF** — видны фреймы `imu_link` и `lidar_link`

Расставьте в `obstacles.sdf` коробки рядом с роботом и посмотрите как точки лидара повторяют контур препятствий.
![Лидар в RViz](./images/rviz_lidar.png)
## Проверка работы

После полного запуска `spawn_robot.launch.py`:

```bash
ros2 topic list | grep -E "imu|scan"
# /imu
# /scan

ros2 topic hz /imu
# average rate: 100.0

ros2 topic hz /scan
# average rate: 10.0
```

В RViz при движении робота:
* Точки лидара смещаются вместе с положением робота.
* Ориентация IMU обновляется при поворотах.
* TF фреймы `imu_link` и `lidar_link` движутся с базой.

## Контрольные проверки

* `ros2 topic hz /imu` показывает 100 Гц.
* `ros2 topic hz /scan` показывает 10 Гц.
* В RViz LaserScan повторяет контур препятствий в мире.
* TF дерево содержит `imu_link` и `lidar_link`.

## Дальше

В следующей статье — добавляем препятствия в кастомный мир `obstacles.sdf` и подключаем `teleop_twist_keyboard` для управления роботом с клавиатуры.
