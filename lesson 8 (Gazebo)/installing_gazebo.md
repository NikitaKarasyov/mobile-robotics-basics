# Установка Gazebo Harmonic для ROS 2 Jazzy

**Цель:** установить и проверить Gazebo Harmonic в связке с ROS 2 Jazzy Jalisco на Ubuntu 24.04.

## Какие версии нам нужны

| Компонент | Версия |
|---|---|
| Ubuntu | 24.04 LTS (Noble Numbat) |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (LTS, поддерживается до 2028) |
| Мостовой пакет | `ros_gz` |

> На Jazzy "родной" симулятор - именно **Gazebo Harmonic** (новая архитектура, ранее `Ignition Gazebo`), не классический Gazebo 11. CLI команды называются `gz`, плагины - `gz-sim-*`, типы сообщений - `gz.msgs.*`.

## Установка

Базовый ROS 2 Jazzy уже должен быть установлен ([урок 1](<../lesson 1 (install ROS2 and testing)/ros2_jazzy_install.md>)). Добавляем сам симулятор и интеграцию:

```bash
sudo apt update
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    ros-jazzy-teleop-twist-keyboard
```

`ros-jazzy-ros-gz` - это метапакет, он подтянет сам Gazebo Harmonic (`gz-sim8`, `gz-tools2`, рендер `ogre2`).

### возможные проблемы
- **`gz: command not found`**. Метапакет не доустановил `gz-tools2`: `sudo apt install gz-tools2`.

## Проверка установки

В одном терминале запустим симулятор:

```bash
gz sim -v 4 empty.sdf
```

Откроется окно Gazebo с пустым миром и серой плоскостью. Флаг `-v 4` включает отладочный лог. По умолчанию симуляция запускается на паузе - нажмите **Play** в нижнем левом углу.

### возможные проблемы
- **Чёрное или мигающее окно Gazebo, рендер плохо работает**. На WSL2/виртуалке часто нет аппаратного ускорения. Запустите с программным рендером:
  ```bash
  LIBGL_ALWAYS_SOFTWARE=1 gz sim empty.sdf
  ```
  Этот флаг необходимо использовать и для всех последующих  запусков 

- **`/clock` пустой**. Симуляция стоит на паузе - нажмите Play.



В другом терминале посмотрим, какие топики транспорта Gazebo есть в системе:

```bash
gz topic -l
```

Должны увидеть `/clock`, `/stats`, `/world/empty/...` и другие служебные.

## Проверка интеграции с ROS 2

Запустим bridge на одном топике - часы симуляции:

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock
```

В отдельном терминале:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /clock
```

Если в Gazebo симуляция запущена (нажата кнопка Play), `/clock` будет публиковаться. Это значит, что мост работает - время уходит из Gazebo в ROS 2.

## Контрольные проверки

- [x] `gz sim --version` показывает Harmonic (8.x).
- [x] `gz topic -l` возвращает список топиков пустого мира.
- [x] `ros2 run ros_gz_bridge parameter_bridge` запускается без ошибок и `/clock` тикает в `ros2 topic echo`.

## Дальше

Переходите к статье [Первый мир и gz CLI](first_world.md).
