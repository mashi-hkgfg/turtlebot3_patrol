# TurtleBot3 三目标点巡件导航（SRM27 算法组第五讲作业）

## 环境要求
- Ubuntu 22.04 LTS + ROS 2 Humble
- TurtleBot3 `waffle` + `turtlebot3_world`（Gazebo 仿真）
- 运行一键巡件所需（apt 安装）：
  ```bash
  sudo apt install \
    ros-humble-turtlebot3-simulations \
    ros-humble-turtlebot3-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-nav2-map-server \
    ros-humble-nav2-simple-commander
  ```
  （`nav2_simple_commander` 是 patrol_node 依赖；桌面版安装通常已含 rviz2。）
- 环境变量：`export TURTLEBOT3_MODEL=waffle`（已写入 ~/.bashrc）
- 如需自行重新建图（可选）：另装 `ros-humble-turtlebot3-cartographer` 与键盘遥控包

## 运行方法
一键自动巡件（Gazebo 世界 + Nav2 导航 + RViz + 巡件节点一起启动）：
```bash
cd ~/turtlebot3_patrol
colcon build --symlink-install --packages-select patrol   # 首次需编译
source install/setup.bash
ros2 launch patrol patrol.launch.py
```
机器人自动完成：精确初始定位 → 依次到达 3 个目标点（每个点打印剩余距离与到达结果）→ 巡件完成。

## 项目结构
```
turtlebot3_patrol/
├── README.md                  # 作业说明（本文件）
├── .gitignore                 # 忽略 build/ install/ log/ __pycache__/ *.webm
├── map/                       # 建图产物（Cartographer 保存，导航加载用）
│   ├── map.pgm                #   栅格地图图像
│   └── map.yaml               #   地图元数据（分辨率、原点等）
└── src/patrol/                # 巡件代码包（ament_python）
    ├── package.xml            #   包清单：包名 / 运行时依赖 / 构建类型
    ├── setup.py               #   安装脚本：登记可执行、拷贝 launch 与注册文件
    ├── setup.cfg              #   安装补充配置
    ├── resource/patrol        #   包注册空文件（ament index“名牌”，不可删）
    ├── patrol/                #   Python 源码模块（import 命名空间 = patrol）
    │   ├── __init__.py        #     包标记（空文件）
    │   ├── patrol_node.py     #     巡件主逻辑：发初始位姿→依次导航→判到达→失败重试
    │   └── waypoints.py       #     出生点与 3 个目标点坐标（map 系实测值）
    └── launch/
        └── patrol.launch.py   #   一键启动：世界 + 导航栈 + RViz + 巡件节点
```


## 实现思路
- 建图 / 定位 / 规划全部使用现成组件（Cartographer 建图；Nav2 的 AMCL 定位、NavFn/DWB 规划、costmap；Gazebo 仿真里程计），作业实现的部分是"巡件大脑"。
- `patrol_node` 流程：启动即向 AMCL 发布**精确初始位姿**（代码内置出生点实测坐标）→ 等待 Nav2 就绪 → 依序向 3 个目标点发送 `NavigateToPose` action → 用 **action result 判定到达**（位置 + 朝向容差内且停稳）→ 单点失败自动**清空代价地图重试**。
- 目标点选点：3 点覆盖场地不同区域、具有空间跨度，其中一点需绕开场地中部障碍。
- 仿真时钟统一：Nav2 全栈与 Gazebo 使用同一时间源（use_sim_time），保证贴点判定稳定。

## 已实现功能
- 三目标点顺序巡检，全程机器人自动运行、无人工干预
- 精确初始位姿发布，无需在 RViz 手动初始化
- 到达判定基于 Nav2 action result，终端实时打印剩余距离与每点结果
- 失败自动 Recovery：单点失败清空代价地图并自动重试

## 加分项
- 全程代码驱动：无需 RViz 手动初始位姿或发送目标
- 单条命令一键启动（Launch 同时拉起世界、导航栈、RViz 与巡件节点）
- 导航失败 Recovery（自动重试）

## 优化点 / 技术亮点
- 逻辑 / 坐标 / 启动三者分离（waypoints.py 单独配置，扩展巡检点不用改逻辑）
- 仿真时间源一致性处理，规避 Nav2 在 Gazebo 下的贴点抖动问题
- 路径由 Nav2 全局/局部规划器完成，机器人运动稳定、绕障合理