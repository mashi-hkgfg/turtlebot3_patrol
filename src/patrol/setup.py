import os
from glob import glob

from setuptools import setup

package_name = 'patrol'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mashi_hkgfg',
    maintainer_email='A1398900686@163.com',
    description='SRM27 第五讲作业：三目标点巡件',
    license='MIT',
    entry_points={
        'console_scripts': [
            'patrol_node = patrol.patrol_node:main',
        ],
    },
)
