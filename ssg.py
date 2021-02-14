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


@dataclass
class Config:
    title: str
    description: str
    twitter: str
    github: str
    build_dir: str = "out"
    static_dir: str = "static"
    posts_dir: str = "posts"
    images_dir: str = "images"


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


def create_site_skeleton(site_cfg: Config) -> None:
    build_dir = site_cfg.build_dir
    if isdir(build_dir):
        rmtree(build_dir)
    mkdir(site_cfg.build_dir)
    mkdir(path.join(build_dir, "posts"))
    mkdir(path.join(build_dir, "static"))


def copy_static_files(static_dir: str = "static", build_dir: str = "out") -> None:
    copytree(static_dir, path.join(build_dir, "static"), dirs_exist_ok=True)


def load_template(tmpl: str, template_dir: str = "templates") -> Template:
    # TODO A closure might a good solution so we don't always need to
    # instantiate the environment.
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template(tmpl)


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


def parse_post(post_file: str) -> Post:
    content = Path(post_file).read_text()
    html, meta = md_to_html(content)
    return Post(content, html, meta)


if __name__ == "__main__":
    site_cfg = load_config()
    build_dir = site_cfg.build_dir
    posts_dir = site_cfg.posts_dir
    static_dir = site_cfg.static_dir
    images_dir = site_cfg.images_dir

    create_site_skeleton(site_cfg)
    copy_static_files()

    copytree(
        path.join(posts_dir, images_dir), path.join(build_dir, posts_dir, images_dir)
    )

    post_tmpl = load_template("post.html.j2")
    posts = []
    for md_file in md_files(posts_dir):
        post = parse_post(path.join(posts_dir, md_file))
        render_page(
            post_tmpl,
            context={"post": post} | asdict(site_cfg),
            out_file=path.join(build_dir, posts_dir, post.file_name),
        )
        posts.append(post)

    render_page(
        load_template("posts.html.j2"),
        context={"posts": posts} | asdict(site_cfg),
        out_file=path.join(build_dir, "index.html"),
    )
