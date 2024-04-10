# Evolve Words

## Introduction

Many moons ago, back in 2008, while in a debate on an atheist-oriented phpBB
site (as was the fashion back then), I ended up writing [a couple of
scripts](https://github.com/davep/selection), in ruby, to illustrate a point
about how mutation and selection can, given enough time, result in something
with the appearance of design.

The code was far from a mic-drop body of evidence (it wasn't meant to be), I
think it did an okay job of showing how nothing more than just mutating
something and selecting for the "fitter" options can get you somewhere
meaningful given enough time.

No matter, either you get the illustration or you don't. That's not
important.

Fast forward 15 years and I was thinking that a Textual version of the code
might be fun.

![Evolve Words](https://raw.githubusercontent.com/davep/evolve-words/main/evolve-words.png)

This is a version of
[`selection2`](https://github.com/davep/selection/blob/master/selection2).
Turns out it *is* fun!

## Installing

### pipx

The package can be installed using [`pipx`](https://pypa.github.io/pipx/):

```sh
$ pipx install evolve-words
```

### Homebrew

The package can be installed using Homebrew. Use the following commands to
install:

```sh
$ brew tap davep/homebrew
$ brew install evolve-words
```

## Running

Once installed run the `evolve-words` command.

## Requirements

While this code *should* work fine on any operating system, it's really
coded to work on a system that provides one of the two following files:

- `/usr/dict/words`
- `/usr/share/dict/words`

That does, of course, mean it's unlikely to work fine on Windows given
neither of them will be there. At some point in the very near future I'll
add support for loading words from a file whose name is passed on the
command line, or something similar.

[//]: # (README.md ends here)
