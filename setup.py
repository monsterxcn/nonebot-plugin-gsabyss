import setuptools

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nonebot-plugin-gsabyss",
    version="0.1.0",
    author="monsterxcn",
    author_email="monsterxcn@gmail.com",
    description="Genshin spiral abyss plugin for NoneBot2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/monsterxcn/nonebot-plugin-gsabyss",
    project_urls={
        "Bug Tracker": "https://github.com/monsterxcn/nonebot-plugin-gsabyss/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=["nonebot-plugin-gsabyss"],
    python_requires=">=3.8,<4.0",
    install_requires=[
        "nonebot2>=2.0.0b3",
        "nonebot-adapter-onebot>=2.0.0b1",
        "nonebot-plugin-apscheduler>=0.2.0",
        "httpx>=0.20.0,<1.0.0",
        "Pillow>=9.1.0",
    ],
)
