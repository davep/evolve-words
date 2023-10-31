"""The main app class."""

##############################################################################
# Backward compatibility.
from __future__ import annotations
from dataclasses import dataclass

##############################################################################
# Python imports.
from collections import Counter, OrderedDict
from pathlib import Path
from random import choice, randint
from string import ascii_lowercase

##############################################################################
# Textual imports.
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Footer, Header, Input, Label, Log, Rule, Static
from textual.worker import get_current_worker

##############################################################################
# Textual Plotext imports.
from textual_plotext import PlotextPlot


##############################################################################
class IntInput(Input):
    """A simple integer input widget."""

    DEFAULT_CSS = """
    IntInput {
        border: none;
        width: 1fr;
        max-width: 10;
        padding: 0;
        margin-top: 1;
    }

    IntInput:focus {
        border: none;
    }
    """

    def _validate_value(self, value: str) -> str:
        """Validate the value and ensure it's an integer input.

        Args:
            value: The value to validated.

        Returns:
            The validated value.
        """
        if value.strip():
            try:
                _ = int(value)
            except ValueError:
                self.app.bell()
                value = self.value
        return value


##############################################################################
class Mutate:
    """Utility class for mutating words."""

    @staticmethod
    def random_char() -> str:
        """Get a random lowercase letter.

        Returns:
            A random lowercase ASCII character.
        """
        return choice(ascii_lowercase)

    @staticmethod
    def point(word: str) -> str:
        """Point mutate the given word.

        Args:
            word: The word to mutate.

        Returns:
            The word with a character mutated.
        """
        if not word:
            return word
        position = randint(0, len(word) - 1)
        return word[:position] + Mutate.random_char() + word[position + 1 :]

    @staticmethod
    def deletion(word: str) -> str:
        """Deletion mutate the given word.

        Args:
            word: The word to mutate.

        Returns:
            The word with a random character removed.
        """
        if not word:
            return word
        position = randint(0, len(word) - 1)
        return word[:position] + word[position + 1 :]

    @staticmethod
    def insertion(word: str) -> str:
        """Insertion mutate the given word.

        Args:
            word: The word to mutate.

        Returns:
            The word with a random character inserted.
        """
        if not word:
            return word
        position = randint(0, len(word) - 1)
        return word[:position] + Mutate.random_char() + word[position:]

    @staticmethod
    def randomly(word: str) -> str:
        """Randomly mutate the given word.

        Args:
            word: The word to mutate.

        Returns:
            The word, randomly mutated.
        """
        return choice((Mutate.point, Mutate.deletion, Mutate.insertion))(word)


##############################################################################
class AppLog(Log):
    """The log widget for the app."""

    BORDER_TITLE = "Log"


##############################################################################
class SizeCount(PlotextPlot):
    """Plot of the count of word sizes."""

    BORDER_TITLE = "Word Size Frequency"

    def on_mount(self) -> None:
        """Configure the plot once the DOM is ready."""
        self.plt.xlabel("Word Size")
        self.plt.ylabel("Frequency")

    def update(self, unique_words: set[str]) -> None:
        """Update the plot.

        Args:
            unique_words: The set of unique words found so far.
        """
        counts = OrderedDict(Counter([len(word) for word in unique_words]))
        self.plt.cld()
        self.plt.bar(list(counts.keys()), list(counts.values()))
        self.refresh()


##############################################################################
class SurvivalRate(PlotextPlot):
    """A plot of the survival rate."""

    BORDER_TITLE = "Survival Rate"

    def on_mount(self) -> None:
        self.plt.xlabel("Generation")
        self.plt.ylabel("%age")

    def update(self, survival_history: list[float]) -> None:
        self.plt.cld()
        self.plt.yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
        self.plt.ylim(0, 100)
        self.plt.plot(survival_history, marker="braille")
        self.refresh()


##############################################################################
class EvolveWordsApp(App[None]):
    """An application that demonstrates evolution through mutation."""

    TITLE = "Evolve Words"

    CSS = """
    Horizontal {
        height: auto;
        background: $panel;
    }

    #io-bar Label {
        height: 100%;
        content-align: left middle;
    }

    VerticalScroll {
        border-top: panel cornflowerblue 70%;
        height: 1fr;
        background: $panel;
    }

    VerticalScroll:focus {
        border-top: panel cornflowerblue;
    }

    #plots {
        height: 1fr;
    }

    PlotextPlot {
        border-top: panel cornflowerblue 70%;
        background: $panel;
    }

    Log {
        border-top: panel cornflowerblue 70%;
        height: 1fr;
        background: $panel;
    }

    Log:focus {
        border-top: panel cornflowerblue;
    }
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self._words: set[str] = set()

    def compose(self) -> ComposeResult:
        """Compose the DOM of the app."""
        yield Header()
        with Horizontal(id="io-bar", disabled=True):
            yield Button("Evolve!", id="evolve")
            yield Rule(orientation="vertical")
            yield Label("Loading...", id="fitness-landscape")
            yield Rule(orientation="vertical")
            yield Label("Target population size: ")
            yield IntInput("300")
            yield Rule(orientation="vertical")
            yield Label("Loading...", id="progenitor")
            yield Rule(orientation="vertical")
            yield Label("Generation: 0", id="generation")
        with VerticalScroll() as wrapper:
            wrapper.border_title = "Resulting words"
            yield Static(id="words")
        with Horizontal(id="plots"):
            yield SizeCount()
            yield SurvivalRate()
        yield AppLog()
        yield Footer()

    def find_words(self) -> Path | None:
        """Find a suitable source of words.

        Returns:
            A path to a word file if one is found, otherwise `None`.
        """
        for candidate in (Path("/usr/share/dict/words"), Path("/usr/dict/words")):
            if candidate.is_file():
                return candidate
        return None

    def progenitor(self) -> str:
        """Find a starting word.

        Returns:
            A random 3 letter word found in the full collection of words.
        """
        return choice([word for word in self._words if len(word) == 3])

    class Ready(Message):
        """Message to say that the app is ready to go."""

    @work(thread=True, exclusive=True)
    def load_words(self) -> None:
        """Load the words that will be used as the fitness test."""
        if words := self.find_words():
            self._words = set(
                word.lower() for word in words.read_text(encoding="utf-8").split()
            )
            self.post_message(self.Ready())
        else:
            self.bell()
            self.notify(
                "Could not find a source of words", severity="error", timeout=60
            )

    def on_mount(self) -> None:
        """Configure the application once the DOM is mounted."""
        self.load_words()

    @on(Ready)
    def okay_to_go(self) -> None:
        """Set the application as ready to go."""
        self.query_one("#io-bar").disabled = False
        self.query_one("#fitness-landscape", Label).update(
            f"Fitness landscape size: {len(self._words)} words"
        )
        self.query_one("#progenitor", Label).update("Progenitor: TBD")
        self.query_one("#evolve").disabled = False
        self.query_one("#evolve").focus()

    @on(Button.Pressed)
    @on(Input.Submitted)
    def start_world(self) -> None:
        """Kick off a new evolution."""
        try:
            target_population = int(self.query_one(IntInput).value)
        except ValueError:
            target_population = 0
        if target_population < 1:
            self.query_one(IntInput).value = "300"
            self.start_world()
            return
        self.query_one("#words", Static).update("")
        progenitor = self.progenitor()
        self.query_one(Log).clear().write_line(f"Progenitor selected: {progenitor}")
        self.query_one("#progenitor", Label).update(f"Progenitor: {progenitor}")
        self.run_world(progenitor, target_population)

    @dataclass
    class Progress(Message):
        """Message sent to report the progress."""

        population_size: int
        unique_words: set[str]
        generation: int
        last_cull: int
        survival_history: list[float]

    @on(Progress)
    def update_progress(self, event: Progress) -> None:
        """Update the display with our progress.

        Args:
            event: The message containing the progress information.
        """
        self.query_one(SizeCount).update(event.unique_words)
        self.query_one(SurvivalRate).update(event.survival_history)
        self.query_one("#words", Static).update(" ".join(sorted(event.unique_words)))
        self.query_one("#generation", Label).update(f"Generation: {event.generation}")
        self.query_one(Log).write_line(
            f"Generation #{event.generation}: {event.last_cull} mutations culled. "
            f"Population size is now {event.population_size}"
        )

    @work(thread=True, exclusive=True)
    def run_world(self, progenitor: str, target_population: int) -> None:
        """Run the world within a thread."""

        # Get set up.
        worker = get_current_worker()
        population = [progenitor]
        generation = 0
        survival: list[float] = []

        # While the population hasn't reached the target value....
        while len(population) < target_population:
            # Create an offspring from each word in the population, randomly
            # mutating as we do; then add them to the population. Note that
            # we do this long-handed because we want to frequently check if
            # the thread has been called on to cancel; we don't want a quit
            # of the application to be lagged.
            offspring: list[str] = []
            for word in population:
                if worker.is_cancelled:
                    return
                offspring.append(Mutate.randomly(word))
            population.extend(offspring)

            # Now cull all of the words that aren't "fit".
            before = len(population)
            population = [word for word in population if word in self._words]
            survival.append((100 / before) * len(population))

            # Update the UI with our progress.
            self.post_message(
                self.Progress(
                    len(population),
                    set(population),
                    generation,
                    before - len(population),
                    survival,
                )
            )

            # Next population.
            generation += 1

        # Get the user's attention to let them know we've completed the run.
        self.notify(
            f"Generated {len(set(population))} unique words in {generation} generations."
        )
        self.bell()


### app.py ends here
