from setuptools import setup

from schedule_manager import __version__ as VERSION

setup(
    name='schedule-manager',
    packages=['schedule_manager'],
    version=VERSION,
    license='MIT',
    url='https://github.com/e619003/ScheduleManager',
    description='Thread-based task scheduling management.',
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author='James Chiang',
    author_email='e619003@gmail.com',
    keywords=[
        'schedule',
        'periodic',
        'jobs',
        'daily',
        'weekly',
        'monthly',
        'scheduling',
        'scheduling management',
        'scheduling manager',
        'scheduler'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
)
