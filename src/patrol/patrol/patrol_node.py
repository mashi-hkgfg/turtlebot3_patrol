"""
巡件大脑（SRM27 第五讲）

职责：
  1. 启动时向 AMCL 精确发布初始位姿（不再手点 RViz，坐标写在 waypoints.py 中）
  2. 等待 Nav2 就绪（AMCL 定位 + 代价地图）
  3. 依序向每个目标点发送 NavigateToPose，用 action 的 result 精确判定"是否到达"
  4. 单个点失败：清空代价地图自动重试（waypoints.RETRIES 次）

运行：
  ros2 launch patrol patrol.launch.py        # 一键：世界 + 导航 + 巡件
  ros2 run patrol patrol_node --init-only    # 只做初始定位，不巡件（标定坐标用）
"""
import argparse
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

from patrol import waypoints

MAP_FRAME = 'map'


def make_pose(navigator, x, y, yaw):
    """构造 map 坐标系下的目标位姿（yaw 弧度制）。"""
    pose = PoseStamped()
    pose.header.frame_id = MAP_FRAME
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z = math.sin(float(yaw) / 2.0)
    pose.pose.orientation.w = math.cos(float(yaw) / 2.0)
    return pose


def patrol(navigator, log):
    """依序访问 WAYPOINTS；返回 0 表示全部到达。"""
    total = len(waypoints.WAYPOINTS)
    for i, (x, y, yaw) in enumerate(waypoints.WAYPOINTS, start=1):
        reached = False
        for attempt in range(waypoints.RETRIES + 1):
            if attempt > 0:
                log.warning(f'目标 {i} 第 {attempt} 次未到达，清空代价地图后重试')
                navigator.clearAllCostmaps()
            log.info(f'>>> 目标 {i}/{total} ({x}, {y}) 第 {attempt + 1} 次尝试')
            navigator.goToPose(make_pose(navigator, x, y, yaw))

            # 轮询直到 Nav2 判定任务结束（isTaskComplete 内部自带 spin）
            while not navigator.isTaskComplete():
                feedback = navigator.getFeedback()
                if feedback and hasattr(feedback, 'distance_remaining'):
                    log.info(f'    剩余距离: {feedback.distance_remaining:.2f} m')
                time.sleep(0.1)

            result = navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                log.info(f'== 已到达目标 {i} ==')
                reached = True
                break
            log.warning(f'目标 {i} 结果: {result}')

        if not reached:
            log.error(f'目标 {i} 重试后仍失败，巡件中止')
            return 1

    log.info(f'巡件完成：{total} 个目标全部到达')
    return 0


def main():
    parser = argparse.ArgumentParser(description='三目标点巡件（SRM27 第五讲加分项）')
    parser.add_argument('--init-only', action='store_true',
                        help='只发布初始位姿并等待定位，不巡件（用于标定坐标）')
    args, _ = parser.parse_known_args()  # 兼容 --ros-args 等 ROS 参数

    rclpy.init()
    navigator = BasicNavigator()
    log = navigator.get_logger()

    ix, iy, iyaw = waypoints.INITIAL_POSE
    log.info(f'发布初始位姿 map({ix}, {iy}, yaw={iyaw})，AMCL 将据此收敛粒子')
    navigator.setInitialPose(make_pose(navigator, ix, iy, iyaw))

    log.info('等待 Nav2 就绪（AMCL 定位 + 代价地图）……')
    navigator.waitUntilNav2Active()
    log.info('Nav2 就绪，定位已建立')

    if args.init_only:
        log.info('--init-only 结束。请到 RViz 确认粒子收敛、扫描线与墙体对齐；')
        log.info('再用 `ros2 topic echo /amcl_pose --once` 标定坐标填入 waypoints.py')
        rc = 0
    else:
        rc = patrol(navigator, log)

    navigator.destroy_node()
    rclpy.shutdown()
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
