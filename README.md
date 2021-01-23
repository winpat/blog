# Blog

My blog including the static site generator that powers it.


## Installation

The project dependencies are managed with [nix](https://nixos.org/).


To install site generator, run:

``` bash
nix -f default.nix -i ssg
```


## Configuration

The page can be configured through a config.yaml file. Look at the template for
examples.


## Usage

Run `ssg` in the same directory as your `config.yml`.


## Development

To get use a development shell with all dependencies, run:

```bash
nix-shell
```


## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

Please make sure to update tests as appropriate.


## License

[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
