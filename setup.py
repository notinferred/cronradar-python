from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cronradar",
    version="0.1.1",
    author="CronRadar",
    author_email="support@cronradar.com",
    description="Non-blocking lifecycle and heartbeat monitoring for Python scheduled jobs, with missed-run, failure, and stuck-run detection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cronradar/cronradar-python",
    project_urls={
        "Documentation": "https://docs.cronradar.com/integrations/python",
        "Product": "https://cronradar.com/python",
        "Source": "https://github.com/cronradar/cronradar-python",
        "Tracker": "https://github.com/cronradar/cronradar-python/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    keywords="cron monitoring scheduled-jobs recurring-jobs missed-jobs failed-jobs stuck-jobs heartbeat",
    license="Proprietary",
)
