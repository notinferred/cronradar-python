from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cronradar",
    version="0.0.5",
    author="Administrator",
    author_email="contact@cronradar.com",
    description="Dead-simple cron job monitoring with auto-registration. Two functions: ping() and sync_monitor(). Self-healing monitors.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cronradar/cronradar-python",
    project_urls={
        "Documentation": "https://cronradar.com/docs",
        "Source": "https://github.com/cronradar/cronradar-python",
        "Tracker": "https://github.com/cronradar/cronradar-python/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
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
    keywords="cron monitoring scheduler job task ping sync auto-register",
    license="Proprietary",
)
