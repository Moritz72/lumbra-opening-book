# Lumbra Opening Book

This project provides functionality to create an opening book
using the data from [Lumbra's Gigabase](https://lumbrasgigabase.com).

It specifically fetches all OTB games in the database
and stores the number of white wins, draws, and black wins
for each move in each position.

## Installation

Install [uv](https://docs.astral.sh/uv) and run

```commandline
uv sync
```

## Build

For fast pgn parsing, [shakmaty](https://docs.rs/shakmaty) is used.

To build the database, run

````commandline
python -m lumbra_opening_book
````

For help, see

````commandline
python -m lumbra_opening_book --help
````

## Usage

The [scripts](./scripts) folder provides example
of the generated database with [sqlmodel](https://sqlmodel.tiangolo.com)
along with implementation to generate hashes and decode moves.
