from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="unipcb",
    version="0.1.0",
    author="Fuxiang Sun, Xi Jiang, et al.",
    author_email="sfx076@163.com",
    description="UniPCB: A Unified Vision-Language Benchmark for PCB Quality Inspection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fuxiangSun/UniPCB",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
        "train": [
            "accelerate>=0.24.0",
            "deepspeed>=0.12.0",
            "wandb>=0.16.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "unipcb-eval=unipcb.eval.main:main",
            "unipcb-train=unipcb.train.main:main",
        ],
    },
)
