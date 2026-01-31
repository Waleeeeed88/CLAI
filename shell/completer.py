"""Tab completion for shell."""
from prompt_toolkit.completion import Completer, Completion
from .constants import MENTION_ALIASES, TEAM_MENTIONS, COMMANDS, WORKFLOWS


class MentionCompleter(Completer):
    def __init__(self):
        self.mentions = list(MENTION_ALIASES.keys()) + TEAM_MENTIONS
        self.commands = COMMANDS + WORKFLOWS
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        
        if "@" in text:
            at_pos = text.rfind("@")
            partial = text[at_pos:].lower()
            for mention in self.mentions:
                if mention.startswith(partial):
                    yield Completion(mention, start_position=-len(partial), style="fg:cyan bold")
        else:
            for cmd in self.commands:
                if cmd.startswith(word.lower()):
                    yield Completion(cmd, start_position=-len(word))
