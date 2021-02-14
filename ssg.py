from typing import Union, NamedTuple, Iterable, Dict, List, Tuple
from pathlib import Path
from sys import exit
from os.path import isdir, exists
from os import path, mkdir, listdir
from shutil import copytree, rmtree
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from dataclasses import dataclass, asdict
from markdown import Markdown
from datetime import datetime
from functools import cached_property

import yaml

BUILD_DIR = Path("out")
STATIC_DIR = Path("static")
POSTS_DIR = Path("posts")
IMAGES_DIR = Path("images")
TEMPLATE_DIR = Path("templates")


@dataclass
class Config:
    title: str
    description: str
    twitter: str
    github: str


def load_config(config_file: str = "config.yml") -> Config:
    """Parse config file."""
    if not exists(config_file):
        print(f"Config file {config_file} does not exist.")
        exit(1)

    with open(config_file) as f:
        cfg_data = yaml.safe_load(f)

    return Config(**cfg_data)


def md_files(dir: str) -> Iterable[str]:
    return (Path(file) for file in listdir(dir) if file.endswith(".md"))


def create_site_skeleton() -> None:
    if isdir(BUILD_DIR):
        rmtree(BUILD_DIR)
    mkdir(BUILD_DIR)
    mkdir(BUILD_DIR / POSTS_DIR)
    mkdir(BUILD_DIR / STATIC_DIR)


def copy_static_files() -> None:
    copytree(STATIC_DIR, BUILD_DIR / STATIC_DIR, dirs_exist_ok=True)


def copy_images() -> None:
    copytree(POSTS_DIR / IMAGES_DIR, BUILD_DIR / POSTS_DIR / IMAGES_DIR)


def template_loader() -> Template:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.globals["STATIC_DIR"] = STATIC_DIR
    env.globals["POSTS_DIR"] = POSTS_DIR
    return env.get_template


def md_to_html(md_text: str) -> Tuple[str, Dict]:
    md = Markdown(extensions=["meta", "fenced_code", "codehilite"])
    html = md.convert(md_text)
    return html, md.Meta


def render_page(tmpl: Template, context: Dict, out_file: Path) -> None:
    html = tmpl.render(context)
    with open(out_file, "w+") as f:
        f.write(html)


@dataclass
class Post:
    raw: str
    html: str
    meta: Dict

    @property
    def title(self) -> str:
        return self.meta["title"][0]

    @property
    def file_name(self) -> str:
        return self.title.lower().replace(" ", "-") + ".html"

    @property
    def publish_date(self):
        published = self.meta.get("published")
        if published is None:
            return None
        return datetime.strptime(published[0], "%Y-%m-%d")


def parse_post(post_file: Path) -> Post:
    content = post_file.read_text()
    html, meta = md_to_html(content)
    return Post(content, html, meta)


if __name__ == "__main__":
    site_cfg = load_config()

    create_site_skeleton()
    copy_static_files()
    copy_images()

    load_template = template_loader()
    post_tmpl = load_template("post.html.j2")
    posts = []
    for md_file in md_files(POSTS_DIR):
        post = parse_post(POSTS_DIR / md_file)
        render_page(
            post_tmpl,
            context={"post": post} | asdict(site_cfg),
            out_file=BUILD_DIR / POSTS_DIR / post.file_name,
        )
        posts.append(post)

    render_page(
        load_template("posts.html.j2"),
        context={"posts": posts} | asdict(site_cfg),
        out_file=path.join(BUILD_DIR, "index.html"),
    )
