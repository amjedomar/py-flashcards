from dataclasses import dataclass, asdict
from random import choice
from json import loads, dumps
from io import StringIO
from collections import defaultdict
from argparse import ArgumentParser


class Logger:
    def __init__(self):
        self.log = StringIO()

    def print(self, *msgs):
        print(*msgs)
        self.log.write(f"{' '.join(msgs)}\n")

    def input(self):
        result = input()
        self.log.write(f'> {result}\n')
        return result


@dataclass
class FlashCard:
    term: str
    definition: str


class FlashCards(Logger):
    ACTIONS = (
        'add', 'remove', 'import', 'export', 'ask', 'exit', 'log',
        'hardest card',
        'reset stats')

    def __init__(self, import_from, export_to):
        super().__init__()
        self.flashcards = []
        self.answered_wrong = defaultdict(int)
        self.import_from = import_from
        self.export_to = export_to

    def prompt_action(self):
        if self.import_from:
            self.import_cards(self.import_from)

        self.print(f"Input the action ({', '.join(FlashCards.ACTIONS)}):")
        action = self.input().strip()
        if action == 'exit':
            if self.export_to:
                self.export_cards(self.export_to)
            self.print('Bye bye!')
        elif action in FlashCards.ACTIONS:
            prompt_method_name = f"prompt_{action.replace(' ', '_')}"
            getattr(self, prompt_method_name)()
            self.print()
            self.prompt_action()

    def prompt_add(self):
        self.print('The card:')
        while True:
            term = self.input()
            if self.find_index('term', term) is not None:
                self.print(f'The card "{term}" already exists. Try again:')
            else:
                break

        self.print('The definition of the card:')
        while True:
            definition = self.input()
            if self.find_index('definition', definition) is not None:
                self.print(f'The definition "{definition}"',
                           'already exists. Try again:')
            else:
                break

        self.flashcards.append(FlashCard(term, definition))
        self.print(f'The pair ("{term}":"{definition}") has been added.')

    def prompt_remove(self):
        self.print('Which Card?')
        target_term = self.input()
        for i, flashcard in enumerate(self.flashcards):
            if flashcard.term == target_term:
                del self.flashcards[i]
                return self.print('The card has been removed.')
        self.print(f'Can\'t remove "{target_term}": there is no such card.')

    def prompt_ask(self):
        self.print('How many times to ask?')
        count = int(self.input())

        for _ in range(count):
            flashcard = choice(self.flashcards)
            self.print(f'Print the definition of "{flashcard.term}":')
            answer = self.input().strip()
            if flashcard.definition != answer:
                other_flashcard_idx = self.find_index('definition', answer)
                if other_flashcard_idx is not None:
                    other_flashcard = self.flashcards[other_flashcard_idx]
                    self.print('Wrong. The right answer is',
                               f'"{flashcard.definition}",',
                               'but your definition is correct for',
                               f'"{other_flashcard.term}"')
                else:
                    self.print('Wrong. The right answer is',
                               f'"{flashcard.definition}".')
                self.answered_wrong[flashcard.term] += 1
            else:
                self.print('Correct!')

    def import_cards(self, filename):
        try:
            with open(filename, 'r') as f:
                loaded_cards = loads(f.read())
                for loaded_card in loaded_cards:
                    term = loaded_card['term']
                    definition = loaded_card['definition']
                    card_idx = self.find_index('term', term)
                    if card_idx is None:
                        self.flashcards.append(FlashCard(term, definition))
                    else:
                        self.flashcards[card_idx].definition = definition
                self.print(f'{len(loaded_cards)} cards have been loaded.')
        except FileNotFoundError:
            self.print('File not found.')

    def prompt_import(self):
        self.print('File name:')
        self.import_cards(self.input())

    def export_cards(self, filename):
        serializable_cards = list(map(lambda c: asdict(c), self.flashcards))
        with open(filename, 'w') as f:
            f.write(dumps(serializable_cards, indent=2))
        self.print(f'{len(self.flashcards)} cards have been saved.')

    def prompt_export(self):
        self.print('File name:')
        self.export_cards(self.input())

    def prompt_log(self):
        self.print('File name:')
        filename = self.input()
        with open(filename, 'a') as f:
            self.log.seek(0)
            f.write(self.log.read() + '\n')
        self.print(f'The log has been saved.')

    def prompt_hardest_card(self):
        most_wrong_times = max(
            self.answered_wrong.values()
        ) if self.answered_wrong else 0

        if most_wrong_times > 0:
            hardest_cards = []
            for card_term, wrong_times in self.answered_wrong.items():
                if wrong_times == most_wrong_times:
                    hardest_cards.append(f'"{card_term}"')
            if len(hardest_cards) == 1:
                self.print(f'The hardest card is {hardest_cards[0]}.',
                           f'You have {most_wrong_times} errors answering it')
            else:
                self.print(f"The hardest cards are {', '.join(hardest_cards)}")
        else:
            self.print('There are no cards with errors.')

    def prompt_reset_stats(self):
        self.answered_wrong = {}
        self.print('Card statistics have been reset.')

    def find_index(self, key, val):
        for i, flashcard in enumerate(self.flashcards):
            if getattr(flashcard, key) == val:
                return i
        return None


def main():
    parser = ArgumentParser()
    parser.add_argument('--import_from')
    parser.add_argument('--export_to')
    args = parser.parse_args()

    FlashCards(**vars(args)).prompt_action()


if __name__ == '__main__':
    main()
